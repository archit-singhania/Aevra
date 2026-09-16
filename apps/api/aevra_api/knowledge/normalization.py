import re
import unicodedata
from dataclasses import dataclass
from io import BytesIO

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from pypdf import PdfReader

from aevra_api.domain.errors import UnsupportedContentError

BLANK_LINES = re.compile(r"\n{3,}")
INLINE_SPACE = re.compile(r"[ \t\f\v]+")


@dataclass(frozen=True)
class TextChunk:
    content: str
    index: int
    start_offset: int
    end_offset: int
    token_count: int


def normalize_text(content: str, source_type: str) -> str:
    if source_type == "markdown":
        rendered = MarkdownIt("commonmark").render(content)
        content = BeautifulSoup(rendered, "html.parser").get_text("\n")
    elif source_type == "website":
        soup = BeautifulSoup(content, "html.parser")
        for node in soup(["script", "style", "noscript", "template"]):
            node.decompose()
        content = soup.get_text("\n")
    elif source_type != "text":
        raise UnsupportedContentError(f"Unsupported text source type: {source_type}")

    content = unicodedata.normalize("NFKC", content).replace("\r\n", "\n").replace("\r", "\n")
    lines = [INLINE_SPACE.sub(" ", line).strip() for line in content.split("\n")]
    normalized = BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()
    if not normalized:
        raise UnsupportedContentError("Document contains no extractable text")
    return normalized


def extract_pdf_text(content: bytes, max_pages: int = 250) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise UnsupportedContentError("Encrypted PDFs require removal of the password")
        if len(reader.pages) > max_pages:
            raise UnsupportedContentError(f"PDF exceeds the {max_pages}-page ingestion limit")
        extracted = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except UnsupportedContentError:
        raise
    except Exception as exc:
        raise UnsupportedContentError("PDF could not be parsed safely") from exc
    return normalize_text(extracted, "text")


def chunk_text(content: str, chunk_chars: int, overlap: int) -> list[TextChunk]:
    if overlap >= chunk_chars:
        raise ValueError("Chunk overlap must be smaller than chunk size")
    chunks: list[TextChunk] = []
    start = 0
    while start < len(content):
        proposed_end = min(len(content), start + chunk_chars)
        end = proposed_end
        if proposed_end < len(content):
            floor = start + int(chunk_chars * 0.6)
            candidates = [
                content.rfind("\n\n", floor, proposed_end),
                content.rfind(". ", floor, proposed_end),
                content.rfind(" ", floor, proposed_end),
            ]
            boundary = max(candidates)
            if boundary > floor:
                end = boundary + (1 if content[boundary] == " " else 2)

        raw = content[start:end]
        left_trim = len(raw) - len(raw.lstrip())
        right_trimmed = raw.rstrip()
        actual_start = start + left_trim
        actual_end = start + len(right_trimmed)
        text = content[actual_start:actual_end]
        if text:
            chunks.append(
                TextChunk(
                    content=text,
                    index=len(chunks),
                    start_offset=actual_start,
                    end_offset=actual_end,
                    token_count=max(1, (len(text) + 3) // 4),
                )
            )
        if end >= len(content):
            break
        start = max(end - overlap, start + 1)
    return chunks
