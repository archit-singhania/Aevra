"""A deterministic local renderer used for offline development and tests.

It intentionally does not claim to be a diffusion model.  It creates refined,
abstract campaign artwork from a prompt-derived seed so the rest of the asset
pipeline is fully usable before a GPU-backed provider is configured.
"""

from __future__ import annotations

import hashlib
import random

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from aevra_api.ai.contracts import ProviderStatus
from aevra_api.media.image_contracts import (
    ImageGenerationRequest,
    ImageGenerationResult,
)
from aevra_api.media.image_transforms import BrandVisualStyle, apply_brand_overlay, encode_image


class DeterministicImageProvider:
    """Generate stable abstract artwork without a network, GPU, or file write."""

    provider_name = "deterministic-local"
    _model_name = "aevra-deterministic-canvas-v1"

    @property
    def model_name(self) -> str:
        return self._model_name

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            available=True,
            provider=self.provider_name,
            model=self.model_name,
            detail="Offline deterministic image renderer is ready.",
        )

    @staticmethod
    def _effective_seed(request: ImageGenerationRequest) -> int:
        if request.seed is not None:
            return request.seed
        return int(request.fingerprint[:16], 16)

    @staticmethod
    def _colour(digest: bytes, offset: int, *, floor: int = 32) -> tuple[int, int, int]:
        return tuple(
            floor + (digest[(offset + index) % len(digest)] % (256 - floor)) for index in range(3)
        )  # type: ignore[return-value]

    def _render_canvas(self, request: ImageGenerationRequest, seed: int) -> Image.Image:
        material = f"{request.fingerprint}:{seed}".encode()
        digest = hashlib.sha256(material).digest()
        randomizer = random.Random(seed)
        left = self._colour(digest, 0, floor=12)
        right = self._colour(digest, 8, floor=28)
        gradient = Image.linear_gradient("L").resize(
            (request.width, request.height), Image.Resampling.BICUBIC
        )
        canvas = ImageOps.colorize(gradient, black=left, white=right).convert("RGBA")

        shapes = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(shapes)
        count = 5 + (seed % 4)
        for index in range(count):
            colour = (
                *self._colour(digest, 15 + (index * 3), floor=70),
                randomizer.randint(40, 130),
            )
            diameter = randomizer.randint(max(80, request.width // 8), max(140, request.width // 2))
            x = randomizer.randint(-diameter // 3, request.width - (diameter * 2 // 3))
            y = randomizer.randint(-diameter // 3, request.height - (diameter * 2 // 3))
            draw.ellipse((x, y, x + diameter, y + diameter), fill=colour)
        for index in range(3):
            inset = max(12, (index + 1) * min(request.width, request.height) // 13)
            colour = (*self._colour(digest, 25 + (index * 2), floor=90), 55)
            draw.rounded_rectangle(
                (inset, inset, request.width - inset, request.height - inset),
                radius=max(16, inset // 2),
                outline=colour,
                width=max(1, min(request.width, request.height) // 280),
            )
        blurred = shapes.filter(ImageFilter.GaussianBlur(radius=max(4, request.width // 100)))
        return Image.alpha_composite(canvas, blurred)

    def generate(
        self,
        request: ImageGenerationRequest,
        *,
        brand_style: BrandVisualStyle | None = None,
    ) -> ImageGenerationResult:
        """Create in-memory artwork; an optional brand treatment is deterministic too."""

        seed = self._effective_seed(request)
        image = self._render_canvas(request, seed)
        if brand_style is not None:
            image = apply_brand_overlay(image, brand_style)
        encoded = encode_image(image, request.output_format)
        return ImageGenerationResult(
            image=encoded,
            provider=self.provider_name,
            model=self.model_name,
            seed=seed,
            metadata={
                "offline": True,
                "fingerprint": request.fingerprint,
                "style": request.style,
                "brand_treatment": brand_style is not None,
            },
        )
