import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SourceType = Literal["text", "markdown", "website", "pdf"]


class KnowledgeIngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    source_type: Literal["text", "markdown", "website"]
    content: str = Field(min_length=1)
    source_uri: str | None = Field(default=None, max_length=2048)
    brand_id: uuid.UUID | None = None
    product: str | None = Field(default=None, max_length=160)
    campaign: str | None = Field(default=None, max_length=160)

    @field_validator("source_uri")
    @classmethod
    def validate_source_uri(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not normalized.startswith(("https://", "http://")):
            raise ValueError("Source URI must start with http:// or https://")
        return normalized


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID | None
    created_by_user_id: uuid.UUID
    title: str
    source_type: SourceType
    source_uri: str | None
    mime_type: str | None
    checksum: str
    content_length: int
    document_metadata: dict[str, str]
    status: Literal["processing", "ready", "failed"]
    created_at: datetime


class IngestionResponse(BaseModel):
    document: KnowledgeDocumentResponse
    chunks_created: int
    deduplicated: bool


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    limit: int = Field(default=6, ge=1, le=20)
    min_score: float = Field(default=0.05, ge=-1, le=1)
    brand_id: uuid.UUID | None = None
    source_type: SourceType | None = None
    product: str | None = Field(default=None, max_length=160)
    campaign: str | None = Field(default=None, max_length=160)


class CitationResponse(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    source_uri: str | None
    source_type: SourceType
    score: float
    excerpt: str
    start_offset: int
    end_offset: int
    metadata: dict[str, str]


class RetrievalResponse(BaseModel):
    query: str
    citations: list[CitationResponse]
    embedding_model: str
