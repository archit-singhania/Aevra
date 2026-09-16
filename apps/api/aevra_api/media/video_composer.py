"""Safe, deterministic FFmpeg composition for Aevra Phase 8.

The public composer has two deliberately separate execution paths:

* FFmpeg receives a list of arguments with ``shell=False`` and a filter graph
  made exclusively from validated numeric values.  User-provided paths never
  appear in filter expressions.
* The deterministic mock path writes a canonical JSON render manifest.  It is
  useful in local development, CI, and product previews when FFmpeg is absent.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Final

from aevra_api.media.video_contracts import (
    MAX_SLIDES,
    MAX_SOURCE_BYTES,
    MAX_TOTAL_DURATION_SECONDS,
    SUPPORTED_IMAGE_SUFFIXES,
    VIDEO_CANVASES,
    CompositionMode,
    FFmpegExecutionError,
    FFmpegUnavailableError,
    RenderMode,
    ValidatedVideoComposition,
    ValidatedVideoSlide,
    VideoCanvas,
    VideoCompositionRequest,
    VideoCompositionResult,
    VideoSlide,
    VideoValidationError,
    normalize_aspect_ratio,
    validate_background_color,
    validate_duration,
    validate_fps,
    validate_output_stem,
)

MANIFEST_SCHEMA_VERSION: Final[int] = 1
DEFAULT_TIMEOUT_SECONDS: Final[float] = 240.0


class VideoComposer:
    """Compose validated still-image slides into a social-media video artifact.

    ``output_directory`` is the composition boundary: output names are derived
    from a content hash and cannot escape this directory.  Source files may be
    read from a managed asset store outside it, but must be regular supported
    image files.
    """

    def __init__(
        self,
        output_directory: Path | str,
        *,
        execution_mode: RenderMode = "auto",
        ffmpeg_binary: str = "ffmpeg",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if execution_mode not in {"auto", "ffmpeg", "mock"}:
            raise VideoValidationError("execution_mode must be auto, ffmpeg, or mock")
        if not ffmpeg_binary.strip():
            raise VideoValidationError("ffmpeg_binary cannot be blank")
        if timeout_seconds <= 0:
            raise VideoValidationError("timeout_seconds must be positive")
        self.output_directory = Path(output_directory).expanduser().resolve()
        self.execution_mode = execution_mode
        self.ffmpeg_binary = ffmpeg_binary
        self.timeout_seconds = timeout_seconds

    def compose(self, request: VideoCompositionRequest) -> VideoCompositionResult:
        """Render a request with FFmpeg where available, otherwise emit a manifest."""

        composition = validate_composition(request)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        render_key = composition_render_key(composition)
        if self.execution_mode == "mock":
            return self._compose_mock(composition, render_key)
        if self._ffmpeg_is_available():
            return self._compose_ffmpeg(composition, render_key)
        if self.execution_mode == "ffmpeg":
            raise FFmpegUnavailableError(
                f"FFmpeg executable '{self.ffmpeg_binary}' was not found on PATH"
            )
        return self._compose_mock(composition, render_key)

    def _ffmpeg_is_available(self) -> bool:
        return shutil.which(self.ffmpeg_binary) is not None

    def _compose_mock(
        self, composition: ValidatedVideoComposition, render_key: str
    ) -> VideoCompositionResult:
        output_path = self._safe_output_path(
            f"{composition.request.output_stem}-{render_key[:16]}.render.json"
        )
        manifest = build_render_manifest(composition, render_key, "deterministic_mock")
        encoded = json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        output_path.write_text(encoded, encoding="utf-8")
        return VideoCompositionResult(
            output_path=output_path,
            mode="deterministic_mock",
            render_key=render_key,
            canvas=composition.canvas,
            fps=composition.request.fps,
            duration_seconds=composition.total_duration_seconds,
            frame_count=_frame_count(composition.total_duration_seconds, composition.request.fps),
            manifest=manifest,
        )

    def _compose_ffmpeg(
        self, composition: ValidatedVideoComposition, render_key: str
    ) -> VideoCompositionResult:
        output_path = self._safe_output_path(
            f"{composition.request.output_stem}-{render_key[:16]}.mp4"
        )
        partial_path = self._safe_output_path(
            f"{composition.request.output_stem}-{render_key[:16]}.partial.mp4"
        )
        command = build_ffmpeg_command(
            composition,
            output_path=partial_path,
            ffmpeg_binary=self.ffmpeg_binary,
        )
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                shell=False,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as error:
            raise FFmpegUnavailableError(
                f"FFmpeg executable '{self.ffmpeg_binary}' was not found on PATH"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise FFmpegExecutionError("FFmpeg composition timed out") from error
        except subprocess.CalledProcessError as error:
            stderr = (error.stderr or "").strip()
            detail = stderr[-1200:] if stderr else "FFmpeg did not report an error"
            raise FFmpegExecutionError(f"FFmpeg composition failed: {detail}") from error
        if not partial_path.is_file() or partial_path.stat().st_size == 0:
            raise FFmpegExecutionError("FFmpeg completed without producing a video artifact")
        partial_path.replace(output_path)
        manifest = build_render_manifest(composition, render_key, "ffmpeg")
        return VideoCompositionResult(
            output_path=output_path,
            mode="ffmpeg",
            render_key=render_key,
            canvas=composition.canvas,
            fps=composition.request.fps,
            duration_seconds=composition.total_duration_seconds,
            frame_count=_frame_count(composition.total_duration_seconds, composition.request.fps),
            manifest=manifest,
            ffmpeg_command=tuple(command),
        )

    def _safe_output_path(self, file_name: str) -> Path:
        candidate = (self.output_directory / file_name).resolve()
        try:
            candidate.relative_to(self.output_directory)
        except ValueError as error:
            raise VideoValidationError(
                "Video output path escaped the configured output directory"
            ) from error
        return candidate


def validate_composition(request: VideoCompositionRequest) -> ValidatedVideoComposition:
    """Resolve files and validate every value before command construction."""

    if not isinstance(request, VideoCompositionRequest):
        raise VideoValidationError("request must be a VideoCompositionRequest")
    if not request.slides:
        raise VideoValidationError("A composition needs at least one image slide")
    if len(request.slides) > MAX_SLIDES:
        raise VideoValidationError(f"A composition supports at most {MAX_SLIDES} slides")
    aspect_ratio = normalize_aspect_ratio(request.aspect_ratio)
    canvas = VIDEO_CANVASES[aspect_ratio]
    fps = validate_fps(request.fps)
    background_color = validate_background_color(request.background_color)
    output_stem = validate_output_stem(request.output_stem)

    validated_slides: list[ValidatedVideoSlide] = []
    total_duration = 0.0
    for slide in request.slides:
        if not isinstance(slide, VideoSlide):
            raise VideoValidationError("Every composition slide must be a VideoSlide")
        duration = validate_duration(slide.duration_seconds)
        total_duration += duration
        source_path = Path(slide.source_path).expanduser().resolve()
        if source_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            supported = ", ".join(sorted(SUPPORTED_IMAGE_SUFFIXES))
            raise VideoValidationError(
                f"Unsupported video slide type; supported types are: {supported}"
            )
        if not source_path.is_file():
            raise VideoValidationError("Video slide source must be an existing regular file")
        byte_size = source_path.stat().st_size
        if byte_size > MAX_SOURCE_BYTES:
            raise VideoValidationError(
                f"Video slide source exceeds the {MAX_SOURCE_BYTES // (1024 * 1024)} MiB limit"
            )
        validated_slides.append(
            ValidatedVideoSlide(
                source_path=source_path,
                duration_seconds=duration,
                source_sha256=_sha256_file(source_path),
                byte_size=byte_size,
            )
        )
    if total_duration > MAX_TOTAL_DURATION_SECONDS:
        raise VideoValidationError(
            f"Composition duration exceeds the {MAX_TOTAL_DURATION_SECONDS:g}-second limit"
        )
    normalized_request = VideoCompositionRequest(
        slides=request.slides,
        aspect_ratio=aspect_ratio,
        fps=fps,
        background_color=background_color,
        output_stem=output_stem,
    )
    return ValidatedVideoComposition(
        request=normalized_request,
        canvas=canvas,
        slides=tuple(validated_slides),
        background_color=background_color,
        total_duration_seconds=total_duration,
    )


def composition_render_key(composition: ValidatedVideoComposition) -> str:
    """Create a stable key from only render-relevant, non-secret data."""

    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "aspect_ratio": composition.request.aspect_ratio.value,
        "background_color": composition.background_color,
        "canvas": asdict(composition.canvas),
        "fps": composition.request.fps,
        "slides": [
            {
                "duration_seconds": _canonical_number(slide.duration_seconds),
                "sha256": slide.source_sha256,
            }
            for slide in composition.slides
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def build_render_manifest(
    composition: ValidatedVideoComposition,
    render_key: str,
    mode: CompositionMode,
) -> dict[str, object]:
    """Return a stable, non-sensitive render record for storage or review."""

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "mode": mode,
        "render_key": render_key,
        "aspect_ratio": composition.request.aspect_ratio.value,
        "canvas": {"width": composition.canvas.width, "height": composition.canvas.height},
        "fps": composition.request.fps,
        "frame_count": _frame_count(composition.total_duration_seconds, composition.request.fps),
        "duration_seconds": _canonical_number(composition.total_duration_seconds),
        "background_color": composition.background_color,
        "slides": [
            {
                "duration_seconds": _canonical_number(slide.duration_seconds),
                "source_sha256": slide.source_sha256,
                "byte_size": slide.byte_size,
            }
            for slide in composition.slides
        ],
    }


def build_ffmpeg_command(
    composition: ValidatedVideoComposition,
    *,
    output_path: Path | str,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    """Build a shell-free FFmpeg command for a composition.

    Input names are individual arguments and never interpolated into the filter
    graph.  The graph contains only indices and values validated by this module.
    """

    safe_output_path = Path(output_path).expanduser().resolve()
    if safe_output_path.suffix.lower() != ".mp4":
        raise VideoValidationError("FFmpeg output must use an .mp4 extension")
    if not ffmpeg_binary.strip():
        raise VideoValidationError("ffmpeg_binary cannot be blank")
    command = [ffmpeg_binary, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    for slide in composition.slides:
        command.extend(
            [
                "-loop",
                "1",
                "-framerate",
                str(composition.request.fps),
                "-t",
                _ffmpeg_number(slide.duration_seconds),
                "-i",
                str(slide.source_path),
            ]
        )
    command.extend(
        [
            "-filter_complex",
            _filter_complex(
                composition.canvas,
                composition.request.fps,
                composition.background_color,
                len(composition.slides),
            ),
            "-map",
            "[outv]",
            "-an",
            "-r",
            str(composition.request.fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-map_metadata",
            "-1",
            str(safe_output_path),
        ]
    )
    return command


def _filter_complex(canvas: VideoCanvas, fps: int, background_color: str, slide_count: int) -> str:
    color = f"0x{background_color.removeprefix('#')}"
    nodes = [
        (
            f"[{index}:v]scale={canvas.width}:{canvas.height}:"
            "force_original_aspect_ratio=decrease,"
            f"pad={canvas.width}:{canvas.height}:(ow-iw)/2:(oh-ih)/2:color={color},"
            f"setsar=1,fps={fps},format=yuv420p[v{index}]"
        )
        for index in range(slide_count)
    ]
    inputs = "".join(f"[v{index}]" for index in range(slide_count))
    nodes.append(f"{inputs}concat=n={slide_count}:v=1:a=0,format=yuv420p[outv]")
    return ";".join(nodes)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_number(value: float) -> float:
    return float(f"{value:.6f}")


def _ffmpeg_number(value: float) -> str:
    return f"{_canonical_number(value):.6f}".rstrip("0").rstrip(".")


def _frame_count(duration_seconds: float, fps: int) -> int:
    return round(duration_seconds * fps)
