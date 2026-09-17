from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1] / "assets" / "vae-social-pack"
LIME = (185, 255, 75, 255)
VIOLET = (151, 132, 255, 255)
MINT = (97, 229, 211, 255)
INK = (8, 11, 17, 255)
WHITE = (245, 247, 241, 255)
MUTED = (157, 166, 180, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))  # type: ignore[return-value]


def gradient(size: tuple[int, int]) -> Image.Image:
    width, height = size
    stops = ((10, 13, 20), (16, 19, 32), (10, 16, 22))
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        p = y / max(1, height - 1)
        if p < 0.56:
            color = lerp(stops[0], stops[1], p / 0.56)
        else:
            color = lerp(stops[1], stops[2], (p - 0.56) / 0.44)
        pixels[0, y] = color
    return strip.resize((width, height), Image.Resampling.BICUBIC).convert("RGBA")


def glow(image: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=max(10, radius // 2)))
    image.alpha_composite(layer)


def background(size: tuple[int, int]) -> Image.Image:
    image = gradient(size)
    width, height = size
    glow(image, (round(width * 0.16), round(height * 0.22)), round(min(size) * 0.42), (142, 117, 255), 64)
    glow(image, (round(width * 0.83), round(height * 0.22)), round(min(size) * 0.38), (125, 255, 115), 50)
    glow(image, (round(width * 0.55), round(height * 0.86)), round(min(size) * 0.35), (48, 191, 183), 24)
    grid = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid)
    spacing = max(44, round(min(size) / 16))
    for x in range(-height, width + height, spacing):
        draw.line((x, 0, x + height, height), fill=(255, 255, 255, 13), width=1)
    for y in range(0, height, spacing):
        draw.line((0, y, width, y), fill=(255, 255, 255, 8), width=1)
    image.alpha_composite(grid)
    return image


def mark(size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    pad = size * 0.34
    box = (pad, pad, size * 2 - pad, size * 2 - pad)
    width = max(4, round(size * 0.075))
    draw.rounded_rectangle(box, radius=size * 0.19, outline=LIME, width=width)
    stroke = max(3, round(size * 0.06))
    left = size * 0.70
    right = size * 1.30
    top = size * 0.69
    bottom = size * 1.36
    draw.line((size, top, left, bottom), fill=WHITE, width=stroke, joint="curve")
    draw.line((size, top, right, bottom), fill=WHITE, width=stroke, joint="curve")
    draw.line((size * 0.84, size * 1.15, size * 1.16, size * 1.15), fill=LIME, width=max(2, round(size * 0.045)))
    glow_layer = canvas.copy().filter(ImageFilter.GaussianBlur(max(5, round(size * 0.08))))
    alpha = glow_layer.getchannel("A").point(lambda value: round(value * 0.33))
    glow_layer.putalpha(alpha)
    canvas.alpha_composite(glow_layer)
    canvas.alpha_composite(canvas.copy())
    return canvas.rotate(-32, resample=Image.Resampling.BICUBIC, expand=False)


def place_mark(image: Image.Image, center: tuple[int, int], size: int) -> None:
    artwork = mark(size)
    image.alpha_composite(artwork, (center[0] - artwork.width // 2, center[1] - artwork.height // 2))


def lockup(image: Image.Image, origin: tuple[int, int], scale: int, *, compact: bool = False) -> None:
    x, y = origin
    place_mark(image, (x + scale, y + scale), scale)
    draw = ImageDraw.Draw(image)
    draw.text((x + scale * 2.05, y + scale * 0.58), "VAE", font=font(round(scale * 0.62), True), fill=WHITE)
    if not compact:
        draw.text(
            (x + scale * 2.10, y + scale * 1.30),
            "CAMPAIGN INTELLIGENCE",
            font=font(max(12, round(scale * 0.17)), True),
            fill=LIME,
            spacing=4,
        )


def save_avatar(path: Path, size: int) -> None:
    image = background((size, size))
    place_mark(image, (size // 2, size // 2), round(size * 0.33))
    image.save(path, "PNG", optimize=True)


def save_cover(path: Path, size: tuple[int, int], *, mode: str) -> None:
    image = background(size)
    width, height = size
    if mode == "facebook":
        lockup(image, (round(width * 0.08), round(height * 0.22)), round(height * 0.23))
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.60), round(height * 0.38)), "VAE", font=font(round(height * 0.20), True), fill=WHITE)
        draw.text((round(width * 0.605), round(height * 0.63)), "Campaign intelligence", font=font(round(height * 0.045)), fill=MUTED)
    elif mode == "x":
        lockup(image, (round(width * 0.06), round(height * 0.17)), round(height * 0.30))
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.61), round(height * 0.31)), "VAE", font=font(round(height * 0.21), True), fill=WHITE)
        draw.text((round(width * 0.615), round(height * 0.64)), "Campaign intelligence", font=font(round(height * 0.055)), fill=MUTED)
    elif mode == "reddit":
        lockup(image, (round(width * 0.06), round(height * 0.05)), round(height * 0.33), compact=True)
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.60), round(height * 0.25)), "VAE", font=font(round(height * 0.27), True), fill=WHITE)
        draw.text((round(width * 0.605), round(height * 0.67)), "AI • CONTENT • INSIGHT", font=font(round(height * 0.10), True), fill=LIME)
    elif mode == "linkedin":
        lockup(image, (round(width * 0.06), round(height * 0.02)), round(height * 0.55), compact=True)
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.62), round(height * 0.29)), "CAMPAIGN INTELLIGENCE", font=font(round(height * 0.15), True), fill=LIME)
    elif mode == "youtube":
        lockup(image, (round(width * 0.16), round(height * 0.38)), round(height * 0.19))
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.57), round(height * 0.40)), "VAE", font=font(round(height * 0.12), True), fill=WHITE)
        draw.text((round(width * 0.573), round(height * 0.57)), "CAMPAIGN INTELLIGENCE", font=font(round(height * 0.033), True), fill=LIME)
    elif mode == "instagram-story":
        lockup(image, (round(width * 0.11), round(height * 0.42)), round(width * 0.13))
        draw = ImageDraw.Draw(image)
        draw.text((round(width * 0.11), round(height * 0.61)), "CAMPAIGN INTELLIGENCE", font=font(round(width * 0.042), True), fill=LIME)
    image.save(path, "PNG", optimize=True)


def svg_mark(path: Path) -> None:
    path.write_text(
        """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 256 256\">
  <defs><linearGradient id=\"lime\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop stop-color=\"#d4ff72\"/><stop offset=\"1\" stop-color=\"#8eea34\"/></linearGradient></defs>
  <rect width=\"256\" height=\"256\" rx=\"64\" fill=\"#0a0d14\"/>
  <g transform=\"translate(128 128) rotate(-32) translate(-128 -128)\" fill=\"none\" stroke=\"url(#lime)\" stroke-linecap=\"round\">
    <rect x=\"55\" y=\"55\" width=\"146\" height=\"146\" rx=\"38\" stroke-width=\"13\"/>
    <path d=\"M128 80 88 176M128 80 168 176M108 139h40\" stroke=\"#f5f7f1\" stroke-width=\"10\"/>
  </g>
</svg>\n""",
        encoding="utf-8",
    )


def svg_wordmark(path: Path) -> None:
    path.write_text(
        """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 760 220\">
  <rect width=\"760\" height=\"220\" rx=\"32\" fill=\"#0a0d14\"/>
  <g transform=\"translate(18 4) scale(.82)\"><rect x=\"55\" y=\"55\" width=\"146\" height=\"146\" rx=\"38\" fill=\"none\" stroke=\"#b9ff4b\" stroke-width=\"13\" transform=\"rotate(-32 128 128)\"/><path d=\"M128 80 88 176M128 80 168 176M108 139h40\" fill=\"none\" stroke=\"#f5f7f1\" stroke-width=\"10\" stroke-linecap=\"round\"/></g>
  <text x=\"235\" y=\"130\" fill=\"#f5f7f1\" font-family=\"Arial, sans-serif\" font-size=\"96\" font-weight=\"700\" letter-spacing=\"8\">VAE</text>
  <text x=\"242\" y=\"172\" fill=\"#b9ff4b\" font-family=\"Arial, sans-serif\" font-size=\"20\" font-weight=\"700\" letter-spacing=\"6\">CAMPAIGN INTELLIGENCE</text>
</svg>\n""",
        encoding="utf-8",
    )


def png_mark(path: Path) -> None:
    """Export the editable mark as a transparent PNG for upload forms."""
    artwork = mark(512)
    artwork.save(path, "PNG", optimize=True)


def png_wordmark(path: Path) -> None:
    """Export a transparent horizontal lockup for decks, bios, and overlays."""
    canvas = Image.new("RGBA", (1800, 520), (0, 0, 0, 0))
    place_mark(canvas, (220, 260), 190)
    draw = ImageDraw.Draw(canvas)
    draw.text((480, 165), "VAE", font=font(170, True), fill=WHITE)
    draw.text((488, 340), "CAMPAIGN INTELLIGENCE", font=font(36, True), fill=LIME)
    canvas.save(path, "PNG", optimize=True)


def main() -> None:
    for folder in ("logo", "avatars", "covers"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    svg_mark(ROOT / "logo" / "vae-mark.svg")
    svg_wordmark(ROOT / "logo" / "vae-wordmark.svg")
    png_mark(ROOT / "logo" / "vae-mark-transparent.png")
    png_wordmark(ROOT / "logo" / "vae-wordmark-transparent.png")

    avatar_specs = {
        "facebook-page-profile.png": 2048,
        "instagram-profile.png": 1080,
        "x-profile.png": 800,
        "reddit-avatar.png": 512,
        "linkedin-company-logo.png": 800,
        "youtube-channel-icon.png": 800,
    }
    for filename, size in avatar_specs.items():
        save_avatar(ROOT / "avatars" / filename, size)

    cover_specs = {
        "facebook-page-cover.png": ((1640, 856), "facebook"),
        "instagram-story-highlight-cover.png": ((1080, 1920), "instagram-story"),
        "x-header.png": ((1500, 500), "x"),
        "reddit-community-banner.png": ((1920, 384), "reddit"),
        "linkedin-company-cover.png": ((1128, 191), "linkedin"),
        "youtube-channel-banner.png": ((2560, 1440), "youtube"),
    }
    for filename, (size, mode) in cover_specs.items():
        save_cover(ROOT / "covers" / filename, size, mode=mode)

    (ROOT / "README.md").write_text(
        """# VAE social brand pack\n\nA cohesive dark-luxe campaign-intelligence identity with acid-lime signal accents and a violet-to-mint atmospheric field. PNGs are platform-ready; SVGs in `logo/` are the editable source marks.\n\n## Included\n\n- `avatars/facebook-page-profile.png` — 2048×2048\n- `avatars/instagram-profile.png` — 1080×1080\n- `avatars/x-profile.png` — 800×800\n- `avatars/reddit-avatar.png` — 512×512\n- `avatars/linkedin-company-logo.png` — 800×800\n- `avatars/youtube-channel-icon.png` — 800×800\n- `covers/facebook-page-cover.png` — 1640×856\n- `covers/instagram-story-highlight-cover.png` — 1080×1920 (Instagram has no page-cover slot)\n- `covers/x-header.png` — 1500×500\n- `covers/reddit-community-banner.png` — 1920×384\n- `covers/linkedin-company-cover.png` — 1128×191\n- `covers/youtube-channel-banner.png` — 2560×1440 (center safe area preserved)\n\nThe artwork is original and contains no stock-photo or third-party trademark elements.\n""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
