import hashlib
import math
import uuid
from dataclasses import dataclass
from typing import cast

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aevra_api.ai.contracts import EmbeddingProvider
from aevra_api.config import Settings
from aevra_api.db.models import KnowledgeChunk, KnowledgeDocument
from aevra_api.domain.errors import ForbiddenError, NotFoundError, UnsupportedContentError
from aevra_api.knowledge.normalization import chunk_text, extract_pdf_text, normalize_text
from aevra_api.repositories.knowledge import KnowledgeRepository
from aevra_api.repositories.tenancy import TenancyRepository
from aevra_api.schemas.knowledge import CitationResponse, RetrievalRequest, SourceType
from aevra_api.services.brands import BrandService

KNOWLEDGE_EDIT_ROLES = {"owner", "admin", "member"}
SUPPORTED_UPLOADS = {
    ".txt": ("text", "text/plain"),
    ".md": ("markdown", "text/markdown"),
    ".markdown": ("markdown", "text/markdown"),
    ".html": ("website", "text/html"),
    ".htm": ("website", "text/html"),
    ".pdf": ("pdf", "application/pdf"),
}


@dataclass(frozen=True)
class IngestionResult:
    document: KnowledgeDocument
    chunks_created: int
    deduplicated: bool


@dataclass(frozen=True)
class RetrievalResult:
    citations: list[CitationResponse]
    embedding_model: str


class KnowledgeService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.session = session
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.repository = KnowledgeRepository(session)
        self.tenancy_repository = TenancyRepository(session)

    def _require_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> str:
        access = self.tenancy_repository.get_workspace_access(user_id, workspace_id)
        if access is None:
            raise NotFoundError("Workspace not found")
        return access[1]

    def _require_editor(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        if self._require_workspace(user_id, workspace_id) not in KNOWLEDGE_EDIT_ROLES:
            raise ForbiddenError("Knowledge editor access is required")

    def ingest_text(
        self,
        *,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str,
        source_type: str,
        content: str,
        source_uri: str | None = None,
        mime_type: str | None = None,
        brand_id: uuid.UUID | None = None,
        metadata: dict[str, str] | None = None,
    ) -> IngestionResult:
        self._require_editor(user_id, workspace_id)
        if len(content.encode("utf-8")) > self.settings.max_document_bytes:
            raise UnsupportedContentError("Document exceeds the configured ingestion limit")
        if brand_id is not None:
            BrandService(self.session).get_brand(user_id, workspace_id, brand_id)

        normalized = normalize_text(content, source_type)
        return self._store_document(
            user_id=user_id,
            workspace_id=workspace_id,
            title=title.strip(),
            source_type=source_type,
            normalized=normalized,
            source_uri=source_uri,
            mime_type=mime_type,
            brand_id=brand_id,
            metadata=metadata or {},
        )

    def ingest_upload(
        self,
        *,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        filename: str,
        content: bytes,
        title: str | None = None,
        source_uri: str | None = None,
        brand_id: uuid.UUID | None = None,
        metadata: dict[str, str] | None = None,
    ) -> IngestionResult:
        self._require_editor(user_id, workspace_id)
        if len(content) > self.settings.max_document_bytes:
            raise UnsupportedContentError("Document exceeds the configured ingestion limit")
        suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if suffix not in SUPPORTED_UPLOADS:
            raise UnsupportedContentError("Supported uploads are TXT, Markdown, HTML, and PDF")
        source_type, mime_type = SUPPORTED_UPLOADS[suffix]
        if source_type == "pdf":
            normalized = extract_pdf_text(content)
        else:
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise UnsupportedContentError("Text uploads must use UTF-8 encoding") from exc
            normalized = normalize_text(decoded, source_type)
        if brand_id is not None:
            BrandService(self.session).get_brand(user_id, workspace_id, brand_id)
        return self._store_document(
            user_id=user_id,
            workspace_id=workspace_id,
            title=(title or filename).strip(),
            source_type=source_type,
            normalized=normalized,
            source_uri=source_uri,
            mime_type=mime_type,
            brand_id=brand_id,
            metadata=metadata or {},
        )

    def _store_document(
        self,
        *,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        title: str,
        source_type: str,
        normalized: str,
        source_uri: str | None,
        mime_type: str | None,
        brand_id: uuid.UUID | None,
        metadata: dict[str, str],
    ) -> IngestionResult:
        checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        duplicate = self.repository.find_duplicate_for_user(user_id, workspace_id, checksum)
        if duplicate is not None:
            return IngestionResult(
                document=duplicate,
                chunks_created=self.repository.count_chunks_for_user(
                    user_id, workspace_id, duplicate.id
                ),
                deduplicated=True,
            )

        text_chunks = chunk_text(
            normalized,
            self.settings.knowledge_chunk_chars,
            self.settings.knowledge_chunk_overlap,
        )
        embeddings = self.embedding_provider.embed([chunk.content for chunk in text_chunks])
        if len(embeddings) != len(text_chunks) or any(
            len(vector) != self.settings.embedding_dimensions for vector in embeddings
        ):
            raise UnsupportedContentError("Embedding provider returned an incompatible shape")

        document = KnowledgeDocument(
            workspace_id=workspace_id,
            brand_id=brand_id,
            created_by_user_id=user_id,
            title=title,
            source_type=source_type,
            source_uri=source_uri,
            mime_type=mime_type,
            checksum=checksum,
            normalized_content=normalized,
            content_length=len(normalized),
            document_metadata={key: value for key, value in metadata.items() if value},
            status="processing",
        )
        self.repository.add_document(document)
        self.session.flush()
        chunks = [
            KnowledgeChunk(
                workspace_id=workspace_id,
                document_id=document.id,
                chunk_index=chunk.index,
                content=chunk.content,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                token_count=chunk.token_count,
                embedding_model=self.embedding_provider.model_name,
                embedding=embedding,
            )
            for chunk, embedding in zip(text_chunks, embeddings, strict=True)
        ]
        self.repository.add_chunks(chunks)
        document.status = "ready"
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            duplicate = self.repository.find_duplicate_for_user(user_id, workspace_id, checksum)
            if duplicate is None:
                raise
            return IngestionResult(
                document=duplicate,
                chunks_created=self.repository.count_chunks_for_user(
                    user_id, workspace_id, duplicate.id
                ),
                deduplicated=True,
            )
        return IngestionResult(document=document, chunks_created=len(chunks), deduplicated=False)

    def list_documents(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[KnowledgeDocument]:
        self._require_workspace(user_id, workspace_id)
        return self.repository.list_documents_for_user(user_id, workspace_id)

    def retrieve(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, request: RetrievalRequest
    ) -> RetrievalResult:
        self._require_workspace(user_id, workspace_id)
        query_embedding = self.embedding_provider.embed([request.query])[0]
        if self.session.get_bind().dialect.name == "postgresql":
            database_ranked = self.repository.ranked_chunks_for_user(
                user_id,
                workspace_id,
                query_embedding,
                limit=request.limit,
                min_score=request.min_score,
                brand_id=request.brand_id,
                source_type=request.source_type,
                product=request.product,
                campaign=request.campaign,
            )
            return RetrievalResult(
                self._citations(database_ranked, request.limit),
                self.embedding_provider.model_name,
            )
        candidates = self.repository.candidate_chunks_for_user(
            user_id,
            workspace_id,
            brand_id=request.brand_id,
            source_type=request.source_type,
            product=request.product,
            campaign=request.campaign,
        )
        ranked: list[tuple[float, KnowledgeChunk, KnowledgeDocument]] = []
        for chunk, document in candidates:
            score = cosine_similarity(query_embedding, list(chunk.embedding))
            if score >= request.min_score:
                ranked.append((score, chunk, document))
        ranked.sort(key=lambda item: (-item[0], item[1].chunk_index, str(item[1].id)))
        return RetrievalResult(
            self._citations(ranked, request.limit), self.embedding_provider.model_name
        )

    def _citations(
        self,
        ranked: list[tuple[float, KnowledgeChunk, KnowledgeDocument]],
        limit: int,
    ) -> list[CitationResponse]:
        citations = [
            CitationResponse(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                source_uri=document.source_uri,
                source_type=cast(SourceType, document.source_type),
                score=round(score, 6),
                excerpt=chunk.content[:480],
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                metadata=document.document_metadata,
            )
            for score, chunk, document in ranked[:limit]
        ]
        return citations


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return -1.0
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
