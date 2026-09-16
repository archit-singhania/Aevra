from typing import Literal

from pydantic import BaseModel, Field


class LocalModelStatusResponse(BaseModel):
    available: bool
    provider: str
    model: str
    detail: str


class LocalGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=32_000)
    system_prompt: str | None = Field(default=None, max_length=12_000)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1200, ge=1, le=16_384)
    response_format: Literal["text", "json"] = "text"


class LocalGenerateResponse(BaseModel):
    content: str
    model: str
    provider: str
    prompt_tokens: int | None
    completion_tokens: int | None
    metadata: dict[str, str | int | float | bool]
