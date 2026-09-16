"""Contracts and validation primitives for Aevra's deterministic video composer.

The contracts deliberately accept only image slides for the first video-composer
release.  That keeps the FFmpeg filter graph free from user-controlled filter
expressions and gives callers predictable platform-ready canvases.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Literal


class VideoCompositionError(RuntimeError):
    """Base error raised when a requested composition cannot be rendered."""


class VideoValidationError(VideoCompositionError):
    """Raised when a composition request violates an explicit safety limit."""


class FFmpegUnavailableError(VideoCompositionError):
    """Raised when a caller explicitly requests FFmpeg but it is unavailable."""


class FFmpegExecutionError(VideoCompositionError):
    """Raised when FFmpeg returns a non-zero result or no video artifact."""


class VideoAspectRatio(StrEnum):
    """The social-media canvases supported by Phase 8."""

    VERTICAL = "9:16"
    SQUARE = "1:1"
    LANDSCAPE = "16:9"


@dataclass(frozen=True)
class VideoCanvas:
    width: int
    height: int

    @property
    def label(self) -> str:
        return f"{self.width}x{self.height}"


VIDEO_CANVASES: Final[dict[VideoAspectRatio, VideoCanvas]] = {
    VideoAspectRatio.VERTICAL: VideoCanvas(width=1080, height=1920),
    VideoAspectRatio.SQUARE: VideoCanvas(width=1080, height=1080),
    VideoAspectRatio.LANDSCAPE: VideoCanvas(width=1920, height=1080),
}

SUPPORTED_IMAGE_SUFFIXES: Final[frozenset[str]] = frozenset({".jpeg", ".jpg", ".png", ".webp"})
MAX_SLIDES: Final[int] = 24
MAX_SOURCE_BYTES: Final[int] = 50 * 1024 * 1024
MIN_SLIDE_DURATION_SECONDS: Final[float] = 0.5
MAX_SLIDE_DURATION_SECONDS: Final[float] = 30.0
MAX_TOTAL_DURATION_SECONDS: Final[float] = 180.0
MIN_FPS: Final[int] = 1
MAX_FPS: Final[int] = 60

_OUTPUT_STEM_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_HEX_COLOR_PATTERN: Final[re.Pattern[str]] = re.compile(r"^#[0-9A-Fa-f]{6}$")


@dataclass(frozen=True)
class VideoSlide:
    """One still image held on-screen for a bounded amount of time."""

    source_path: Path | str
    duration_seconds: float = 3.0


@dataclass(frozen=True)
class VideoCompositionRequest:
    """A bounded, image-only composition request.

    ``output_stem`` is intentionally a file stem rather than a path.  The
    composer decides the final path inside its configured output directory.
    """

    slides: tuple[VideoSlide, ...]
    aspect_ratio: VideoAspectRatio = VideoAspectRatio.VERTICAL
    fps: int = 30
    background_color: str = "#090B12"
    output_stem: str = "aevra-video"


@dataclass(frozen=True)
class ValidatedVideoSlide:
    """An immutable, safe-to-pass-to-FFmpeg image input."""

    source_path: Path
    duration_seconds: float
    source_sha256: str
    byte_size: int


@dataclass(frozen=True)
class ValidatedVideoComposition:
    request: VideoCompositionRequest
    canvas: VideoCanvas
    slides: tuple[ValidatedVideoSlide, ...]
    background_color: str
    total_duration_seconds: float


RenderMode = Literal["auto", "ffmpeg", "mock"]
CompositionMode = Literal["ffmpeg", "deterministic_mock"]


@dataclass(frozen=True)
class VideoCompositionResult:
    """The render outcome, including a deterministic manifest for auditability."""

    output_path: Path
    mode: CompositionMode
    render_key: str
    canvas: VideoCanvas
    fps: int
    duration_seconds: float
    frame_count: int
    manifest: dict[str, object]
    ffmpeg_command: tuple[str, ...] | None = None


def normalize_aspect_ratio(value: VideoAspectRatio | str) -> VideoAspectRatio:
    try:
        return VideoAspectRatio(value)
    except ValueError as error:
        supported = ", ".join(item.value for item in VideoAspectRatio)
        raise VideoValidationError(f"Unsupported aspect ratio; use one of: {supported}") from error


def validate_output_stem(value: str) -> str:
    if not _OUTPUT_STEM_PATTERN.fullmatch(value):
        raise VideoValidationError(
            "output_stem must be 1-64 characters using only letters, numbers, "
            "hyphens, or underscores"
        )
    return value


def validate_background_color(value: str) -> str:
    if not _HEX_COLOR_PATTERN.fullmatch(value):
        raise VideoValidationError("background_color must use the #RRGGBB form")
    return value.upper()


def validate_fps(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_FPS <= value <= MAX_FPS:
        raise VideoValidationError(f"fps must be an integer between {MIN_FPS} and {MAX_FPS}")
    return value


def validate_duration(value: float) -> float:
    if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value):
        raise VideoValidationError("slide duration must be a finite number")
    normalized = float(value)
    if not MIN_SLIDE_DURATION_SECONDS <= normalized <= MAX_SLIDE_DURATION_SECONDS:
        raise VideoValidationError(
            "slide duration must be between "
            f"{MIN_SLIDE_DURATION_SECONDS:g} and {MAX_SLIDE_DURATION_SECONDS:g} seconds"
        )
    return normalized
