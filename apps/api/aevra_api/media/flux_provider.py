from __future__ import annotations

import base64
import hashlib
from io import BytesIO
from typing import Any

import httpx
from PIL import Image

from aevra_api.domain.errors import GenerationError, ProviderUnavailableError
from aevra_api.media.image_contracts import ImageGenerationRequest, ImageGenerationResult
from aevra_api.media.image_transforms import encode_image


class FluxHTTPProvider:
    """Optional FLUX-compatible HTTP provider; deterministic local fallback remains default."""

    provider_name = "flux-http"

    def __init__(self, base_url: str, *, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=120.0)

    def generate(
        self, request: ImageGenerationRequest, *, brand_style=None
    ) -> ImageGenerationResult:
        del brand_style
        try:
            response = self.client.post(
                f"{self.base_url}/generate",
                json={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "width": request.width,
                    "height": request.height,
                    "seed": request.seed,
                    "output_format": request.output_format,
                },
            )
        except httpx.HTTPError as error:
            raise ProviderUnavailableError("FLUX service is unavailable") from error
        if response.status_code >= 500:
            raise ProviderUnavailableError("FLUX service is unavailable")
        if response.status_code >= 400:
            raise GenerationError("FLUX rejected the image request")
        try:
            body: dict[str, Any] = response.json()
            raw = base64.b64decode(body["image_base64"])
            with Image.open(BytesIO(raw)) as image:
                image.load()
                encoded = encode_image(image.convert("RGB"), request.output_format)
        except (KeyError, ValueError, OSError) as error:
            raise GenerationError("FLUX returned an invalid image payload") from error
        return ImageGenerationResult(
            image=encoded,
            provider=self.provider_name,
            model=str(body.get("model", "flux")),
            seed=int(body.get("seed", request.seed or 0)),
            metadata={"remote": True, "response_sha256": hashlib.sha256(raw).hexdigest()},
        )
