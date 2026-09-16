import hashlib
import math
import re

import httpx

from aevra_api.ai.contracts import EmbeddingProvider
from aevra_api.config import Settings
from aevra_api.domain.errors import ProviderUnavailableError

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class HashingEmbeddingProvider:
    """Deterministic, dependency-light fallback for development and tests."""

    def __init__(self, dimensions: int = 384) -> None:
        self._dimensions = dimensions

    @property
    def model_name(self) -> str:
        return "aevra-hashing-v1"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimensions
            sign = 1.0 if (value >> 8) % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class OllamaEmbeddingProvider:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(
            base_url=settings.ollama_base_url.rstrip("/"),
            timeout=settings.ollama_timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self.settings.embedding_model

    @property
    def dimensions(self) -> int:
        return self.settings.embedding_dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.post(
                "/api/embed",
                json={
                    "model": self.model_name,
                    "input": texts,
                    "dimensions": self.dimensions,
                    "truncate": True,
                },
            )
            response.raise_for_status()
            embeddings = response.json().get("embeddings")
        except (httpx.HTTPError, ValueError, AttributeError) as exc:
            raise ProviderUnavailableError("Local embedding service is unavailable") from exc
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise ProviderUnavailableError("Local embedding service returned an invalid response")
        vectors = [[float(value) for value in vector] for vector in embeddings]
        if any(len(vector) != self.dimensions for vector in vectors):
            raise ProviderUnavailableError(
                f"Embedding model must return exactly {self.dimensions} dimensions"
            )
        return vectors


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider.lower() == "ollama":
        return OllamaEmbeddingProvider(settings)
    if settings.embedding_provider.lower() == "hashing":
        return HashingEmbeddingProvider(settings.embedding_dimensions)
    raise ProviderUnavailableError("Configured embedding provider is not supported")
