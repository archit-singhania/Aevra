"""Contracts shared by local and remote image providers.

No provider receives a filesystem path or a database model.  That makes the
boundary easy to test and prevents accidental tenant-data writes from inside a
renderer.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

from aevra_api.ai.contracts import ProviderStatus

ImageFormat = Literal["png", "jpeg", "webp"]

MIN_IMAGE_DIMENSION = 64
MAX_IMAGE_DIMENSION = 4096
MAX_IMAGE_PIXELS = 12_000_000
MAX_PROMPT_CHARS = 4_000
MAX_NEGATIVE_PROMPT_CHARS = 2_000

_FORMATS: frozenset[str] = frozenset({"png", "jpeg", "webp"})
_STYLE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class ImagePipelineError(ValueError):
    """A safe, non-provider-specific image pipeline failure."""


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _validate_dimension(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ImagePipelineError(f"{name} must be an integer")
    if not MIN_IMAGE_DIMENSION <= value <= MAX_IMAGE_DIMENSION:
        raise ImagePipelineError(
            f"{name} must be between {MIN_IMAGE_DIMENSION} and {MAX_IMAGE_DIMENSION} pixels"
        )


@dataclass(frozen=True)
class ImageGenerationRequest:
    """Validated, deterministic input to an image provider.

    An omitted seed is derived from the stable request fingerprint. This is
    intentional: a retry of the same job produces the same bytes when using a
    deterministic provider, while callers can opt into variations with a seed.
    """

    prompt: str
    width: int = 1024
    height: int = 1024
    seed: int | None = None
    negative_prompt: str = ""
    style: str = "editorial"
    output_format: ImageFormat = "png"

    def __post_init__(self) -> None:
        prompt = _normalized_text(self.prompt)
        negative_prompt = _normalized_text(self.negative_prompt)
        style = self.style.strip().lower()
        if not prompt:
            raise ImagePipelineError("prompt must not be empty")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise ImagePipelineError(f"prompt must be at most {MAX_PROMPT_CHARS} characters")
        if len(negative_prompt) > MAX_NEGATIVE_PROMPT_CHARS:
            raise ImagePipelineError(
                f"negative_prompt must be at most {MAX_NEGATIVE_PROMPT_CHARS} characters"
            )
        _validate_dimension("width", self.width)
        _validate_dimension("height", self.height)
        if self.width * self.height > MAX_IMAGE_PIXELS:
            raise ImagePipelineError(f"image may not exceed {MAX_IMAGE_PIXELS:,} pixels")
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0
        ):
            raise ImagePipelineError("seed must be a non-negative integer when provided")
        if not _STYLE_PATTERN.fullmatch(style):
            raise ImagePipelineError("style must be a short lowercase identifier")
        if self.output_format not in _FORMATS:
            raise ImagePipelineError("output_format must be png, jpeg, or webp")
        object.__setattr__(self, "prompt", prompt)
        object.__setattr__(self, "negative_prompt", negative_prompt)
        object.__setattr__(self, "style", style)

    @property
    def fingerprint(self) -> str:
        """Stable digest for idempotency, cache keys, and implicit seed selection."""

        payload = {
            "height": self.height,
            "negative_prompt": self.negative_prompt,
            "output_format": self.output_format,
            "prompt": self.prompt,
            "seed": self.seed,
            "style": self.style,
            "width": self.width,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EncodedImage:
    """A serialized image ready for object storage or an HTTP response."""

    data: bytes
    content_type: str
    width: int
    height: int
    sha256: str
    file_extension: str

    def __post_init__(self) -> None:
        if not self.data:
            raise ImagePipelineError("encoded image must not be empty")
        _validate_dimension("width", self.width)
        _validate_dimension("height", self.height)
        if self.width * self.height > MAX_IMAGE_PIXELS:
            raise ImagePipelineError(f"image may not exceed {MAX_IMAGE_PIXELS:,} pixels")
        expected = hashlib.sha256(self.data).hexdigest()
        if self.sha256 != expected:
            raise ImagePipelineError("encoded image digest did not match its payload")


@dataclass(frozen=True)
class ImageGenerationResult:
    """Provider output plus immutable provenance metadata."""

    image: EncodedImage
    provider: str
    model: str
    seed: int
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider.strip() or not self.model.strip():
            raise ImagePipelineError("provider and model must be present")
        if self.seed < 0:
            raise ImagePipelineError("seed must be non-negative")


class ImageProvider(Protocol):
    """A provider boundary suitable for local, hosted, and test renderers."""

    @property
    def model_name(self) -> str: ...

    def status(self) -> ProviderStatus: ...

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult: ...
