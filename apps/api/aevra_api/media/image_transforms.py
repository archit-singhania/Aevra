"""Safe, deterministic raster transforms used by Aevra's asset pipeline."""

from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

from aevra_api.media.image_contracts import (
    MAX_IMAGE_DIMENSION,
    MAX_IMAGE_PIXELS,
    MIN_IMAGE_DIMENSION,
    EncodedImage,
    ImageFormat,
    ImagePipelineError,
)

MAX_SOURCE_BYTES = 20 * 1024 * 1024
MAX_LOGO_BYTES = 5 * 1024 * 1024
LogoPosition = Literal["bottom_left", "bottom_right", "top_left", "top_right"]

_FORMAT_DETAILS: dict[ImageFormat, tuple[str, str, str]] = {
    "png": ("PNG", "image/png", "png"),
    "jpeg": ("JPEG", "image/jpeg", "jpg"),
    "webp": ("WEBP", "image/webp", "webp"),
}


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _assert_target_size(width: int, height: int) -> None:
    if isinstance(width, bool) or isinstance(height, bool):
        raise ImagePipelineError("target dimensions must be integers")
    if not isinstance(width, int) or not isinstance(height, int):
        raise ImagePipelineError("target dimensions must be integers")
    if not MIN_IMAGE_DIMENSION <= width <= MAX_IMAGE_DIMENSION:
        raise ImagePipelineError(
            f"target width must be between {MIN_IMAGE_DIMENSION} and {MAX_IMAGE_DIMENSION} pixels"
        )
    if not MIN_IMAGE_DIMENSION <= height <= MAX_IMAGE_DIMENSION:
        raise ImagePipelineError(
            f"target height must be between {MIN_IMAGE_DIMENSION} and {MAX_IMAGE_DIMENSION} pixels"
        )
    if width * height > MAX_IMAGE_PIXELS:
        raise ImagePipelineError(f"image may not exceed {MAX_IMAGE_PIXELS:,} pixels")


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """Parse a CSS-style six-digit hex colour without accepting ambiguous input."""

    normalized = value.strip()
    if len(normalized) != 7 or not normalized.startswith("#"):
        raise ImagePipelineError("colour must be a #RRGGBB value")
    try:
        red = int(normalized[1:3], 16)
        green = int(normalized[3:5], 16)
        blue = int(normalized[5:7], 16)
    except ValueError as error:
        raise ImagePipelineError("colour must be a #RRGGBB value") from error
    return red, green, blue


@dataclass(frozen=True)
class BrandVisualStyle:
    """Non-sensitive visual inputs used after image generation.

    ``logo_png`` remains in memory; persistence and object storage are owned by
    callers. The byte-size cap avoids passing unexpectedly large payloads into
    Pillow.
    """

    primary_color: str = "#6D5EF7"
    secondary_color: str = "#0B1020"
    accent_color: str = "#F7C95C"
    overlay_opacity: float = 0.38
    logo_png: bytes | None = None
    logo_position: LogoPosition = "bottom_left"
    safe_margin: int = 48
    label: str | None = None

    def __post_init__(self) -> None:
        hex_to_rgb(self.primary_color)
        hex_to_rgb(self.secondary_color)
        hex_to_rgb(self.accent_color)
        if not 0.0 <= self.overlay_opacity <= 1.0:
            raise ImagePipelineError("overlay_opacity must be between 0 and 1")
        if self.logo_png is not None and len(self.logo_png) > MAX_LOGO_BYTES:
            raise ImagePipelineError(f"logo_png may not exceed {MAX_LOGO_BYTES:,} bytes")
        if self.logo_position not in {"bottom_left", "bottom_right", "top_left", "top_right"}:
            raise ImagePipelineError("logo_position was not recognized")
        if isinstance(self.safe_margin, bool) or not isinstance(self.safe_margin, int):
            raise ImagePipelineError("safe_margin must be an integer")
        if not 0 <= self.safe_margin <= 512:
            raise ImagePipelineError("safe_margin must be between 0 and 512")
        if self.label is not None:
            label = _normalized_text(self.label)
            if not label or len(label) > 80:
                raise ImagePipelineError("label must contain between 1 and 80 characters")
            object.__setattr__(self, "label", label)


def _safe_open(data: bytes, *, max_bytes: int = MAX_SOURCE_BYTES) -> Image.Image:
    if not data:
        raise ImagePipelineError("image payload must not be empty")
    if len(data) > max_bytes:
        raise ImagePipelineError(f"image payload may not exceed {max_bytes:,} bytes")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                source.verify()
            with Image.open(io.BytesIO(data)) as source:
                source.load()
                image = source.copy()
    except (Image.DecompressionBombError, OSError, ValueError) as error:
        raise ImagePipelineError("image payload could not be safely decoded") from error
    _assert_target_size(image.width, image.height)
    return image


def _coerce_source(image: Image.Image) -> Image.Image:
    _assert_target_size(image.width, image.height)
    return image.copy()


def _resampling_lanczos() -> Image.Resampling:
    return Image.Resampling.LANCZOS


def resize_cover(
    image: Image.Image,
    width: int,
    height: int,
    *,
    focus: tuple[float, float] = (0.5, 0.5),
) -> Image.Image:
    """Crop to fill a target canvas, with a normalized focal point."""

    _assert_target_size(width, height)
    focus_x, focus_y = focus
    if not 0.0 <= focus_x <= 1.0 or not 0.0 <= focus_y <= 1.0:
        raise ImagePipelineError("focus values must be between 0 and 1")
    source = _coerce_source(image)
    source_ratio = source.width / source.height
    target_ratio = width / height
    if source_ratio > target_ratio:
        crop_width = max(1, round(source.height * target_ratio))
        left = round((source.width - crop_width) * focus_x)
        left = min(max(left, 0), source.width - crop_width)
        box = (left, 0, left + crop_width, source.height)
    else:
        crop_height = max(1, round(source.width / target_ratio))
        top = round((source.height - crop_height) * focus_y)
        top = min(max(top, 0), source.height - crop_height)
        box = (0, top, source.width, top + crop_height)
    return source.crop(box).resize((width, height), _resampling_lanczos())


def resize_contain(
    image: Image.Image,
    width: int,
    height: int,
    *,
    background_color: str = "#0B1020",
) -> Image.Image:
    """Letterbox an image inside a target canvas without changing its aspect ratio."""

    _assert_target_size(width, height)
    background = hex_to_rgb(background_color)
    source = _coerce_source(image)
    source.thumbnail((width, height), _resampling_lanczos())
    has_alpha = "A" in source.getbands()
    mode = "RGBA" if has_alpha else "RGB"
    canvas_color: tuple[int, int, int] | tuple[int, int, int, int]
    canvas_color = (*background, 255) if has_alpha else background
    canvas = Image.new(mode, (width, height), canvas_color)
    position = ((width - source.width) // 2, (height - source.height) // 2)
    if has_alpha:
        canvas.alpha_composite(source.convert("RGBA"), position)
    else:
        canvas.paste(source, position)
    return canvas


def _paste_logo(canvas: Image.Image, style: BrandVisualStyle) -> None:
    if style.logo_png is None:
        return
    logo = _safe_open(style.logo_png, max_bytes=MAX_LOGO_BYTES).convert("RGBA")
    max_width = max(1, canvas.width // 4)
    max_height = max(1, canvas.height // 7)
    logo.thumbnail((max_width, max_height), _resampling_lanczos())
    margin = min(style.safe_margin, canvas.width // 4, canvas.height // 4)
    horizontal = (
        margin if style.logo_position.endswith("left") else canvas.width - logo.width - margin
    )
    vertical = (
        margin if style.logo_position.startswith("top") else canvas.height - logo.height - margin
    )
    canvas.alpha_composite(logo, (max(0, horizontal), max(0, vertical)))


def _draw_label(canvas: Image.Image, style: BrandVisualStyle) -> None:
    if style.label is None:
        return
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    margin = min(style.safe_margin, canvas.width // 4, canvas.height // 4)
    bounds = draw.textbbox((0, 0), style.label, font=font)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    padding_x, padding_y = 10, 7
    left = margin
    top = canvas.height - margin - text_height - (padding_y * 2)
    draw.rounded_rectangle(
        (
            left,
            max(0, top),
            min(canvas.width - margin, left + text_width + (padding_x * 2)),
            canvas.height - margin,
        ),
        radius=8,
        fill=(*hex_to_rgb(style.secondary_color), 210),
        outline=(*hex_to_rgb(style.accent_color), 230),
        width=1,
    )
    draw.text(
        (left + padding_x, max(0, top) + padding_y),
        style.label,
        fill=(255, 255, 255, 255),
        font=font,
    )


def apply_brand_overlay(image: Image.Image, style: BrandVisualStyle) -> Image.Image:
    """Apply a reproducible, non-destructive visual treatment to a generated image."""

    source = _coerce_source(image).convert("RGBA")
    overlay = Image.new("RGBA", source.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    primary = hex_to_rgb(style.primary_color)
    secondary = hex_to_rgb(style.secondary_color)
    maximum_alpha = round(style.overlay_opacity * 255)
    height_denominator = max(1, source.height - 1)
    for y in range(source.height):
        progress = y / height_denominator
        # Keep the artwork open near the top and reserve contrast for captions.
        alpha = round(maximum_alpha * (0.15 + (0.85 * progress * progress)))
        colour = primary if y < source.height // 2 else secondary
        draw.line((0, y, source.width, y), fill=(*colour, alpha))
    accent = hex_to_rgb(style.accent_color)
    accent_width = max(2, min(12, source.width // 160))
    draw.rectangle((0, 0, accent_width, source.height), fill=(*accent, 235))
    composed = Image.alpha_composite(source, overlay)
    _paste_logo(composed, style)
    _draw_label(composed, style)
    return composed


def encode_image(image: Image.Image, output_format: ImageFormat = "png") -> EncodedImage:
    """Serialize a bounded Pillow image with an immutable content digest."""

    if output_format not in _FORMAT_DETAILS:
        raise ImagePipelineError("output_format must be png, jpeg, or webp")
    source = _coerce_source(image)
    pillow_format, content_type, extension = _FORMAT_DETAILS[output_format]
    if output_format == "jpeg" and "A" in source.getbands():
        flattened = Image.new("RGB", source.size, (255, 255, 255))
        flattened.paste(source.convert("RGBA"), mask=source.convert("RGBA").getchannel("A"))
        source = flattened
    elif output_format == "jpeg":
        source = source.convert("RGB")
    buffer = io.BytesIO()
    if output_format == "png":
        source.save(buffer, format=pillow_format, compress_level=9, optimize=False)
    elif output_format == "jpeg":
        source.save(
            buffer,
            format=pillow_format,
            quality=92,
            optimize=False,
            progressive=False,
        )
    elif output_format == "webp":
        source.save(buffer, format=pillow_format, lossless=True, method=6)
    data = buffer.getvalue()
    return EncodedImage(
        data=data,
        content_type=content_type,
        width=source.width,
        height=source.height,
        sha256=hashlib.sha256(data).hexdigest(),
        file_extension=extension,
    )
