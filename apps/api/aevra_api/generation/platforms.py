import re
from dataclasses import dataclass

from aevra_api.domain.errors import GenerationError

HASHTAG_CLEANER = re.compile(r"[^a-zA-Z0-9_]")


@dataclass(frozen=True)
class PlatformSpec:
    caption_limit: int
    hashtag_limit: int
    title_limit: int | None = None
    requires_title: bool = False


PLATFORM_SPECS = {
    "linkedin": PlatformSpec(3000, 5),
    "instagram": PlatformSpec(2200, 15),
    "threads": PlatformSpec(500, 5),
    "x": PlatformSpec(280, 3),
    "facebook": PlatformSpec(5000, 5),
    "youtube": PlatformSpec(5000, 15, title_limit=100, requires_title=True),
}


def truncate_at_word(value: str, limit: int) -> str:
    value = value.strip()
    if len(value) <= limit:
        return value
    shortened = value[: max(1, limit - 1)].rsplit(" ", 1)[0].rstrip()
    return f"{shortened or value[: limit - 1]}…"


def normalize_hashtags(values: object, limit: int) -> list[str]:
    if not isinstance(values, list):
        return []
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = HASHTAG_CLEANER.sub("", value.strip().lstrip("#"))
        if cleaned:
            normalized.append(f"#{cleaned}")
    return list(dict.fromkeys(normalized))[:limit]


def adapt_variant(raw: dict[str, object], platform: str) -> dict[str, object]:
    spec = PLATFORM_SPECS[platform]
    caption = raw.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        raise GenerationError(f"The model returned no caption for {platform}")
    title_value = raw.get("title")
    title = title_value.strip() if isinstance(title_value, str) and title_value.strip() else None
    if spec.requires_title and title is None:
        raise GenerationError(f"The model returned no title for {platform}")
    if title and spec.title_limit:
        title = truncate_at_word(title, spec.title_limit)
    cta_value = raw.get("call_to_action")
    cta = cta_value.strip() if isinstance(cta_value, str) and cta_value.strip() else None
    return {
        "platform": platform,
        "title": title,
        "caption": truncate_at_word(caption, spec.caption_limit),
        "hashtags": normalize_hashtags(raw.get("hashtags"), spec.hashtag_limit),
        "call_to_action": truncate_at_word(cta, 500) if cta else None,
    }


def validate_variant(
    variant: dict[str, object], prohibited_directives: list[str], has_citations: bool
) -> tuple[list[str], float]:
    platform = str(variant["platform"])
    caption = str(variant["caption"])
    issues: list[str] = []
    if not has_citations:
        issues.append("No Brand Brain citations were available for factual grounding.")
    if not variant.get("call_to_action"):
        issues.append("No call to action was provided.")
    if platform == "instagram" and not variant.get("hashtags"):
        issues.append("Instagram content should include relevant hashtags.")
    for directive in prohibited_directives:
        quoted = re.findall(r'["“](.*?)["”]', directive)
        for phrase in quoted:
            if phrase.lower() in caption.lower():
                issues.append(f'Prohibited phrase detected: "{phrase}".')
    score = max(0.0, 100.0 - (15.0 * len(issues)))
    return issues, score
