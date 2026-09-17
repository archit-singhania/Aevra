from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Literal, Protocol

MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class GenerationRequest:
    messages: list[ChatMessage]
    temperature: float = 0.2
    max_tokens: int = 1200
    response_format: Literal["text", "json"] = "text"


@dataclass(frozen=True)
class GenerationResult:
    content: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderStatus:
    available: bool
    provider: str
    model: str
    detail: str


class EmbeddingProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LLMProvider(Protocol):
    @property
    def model_name(self) -> str: ...

    def status(self) -> ProviderStatus: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...

    def stream(self, request: GenerationRequest) -> Iterator[str]: ...
