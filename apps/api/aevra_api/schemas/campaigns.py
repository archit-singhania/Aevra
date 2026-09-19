import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Platform = Literal["linkedin", "instagram", "threads", "x", "facebook", "youtube"]
PublishingMode = Literal["manual", "assisted", "autonomous"]
CampaignStatus = Literal[
    "draft",
    "context_retrieval",
    "planning",
    "content_generation",
    "platform_adaptation",
    "validation",
    "awaiting_approval",
    "approved",
    "failed",
    "cancelled",
]


def default_media_types() -> list[Literal["text", "image", "video"]]:
    return ["text"]


class CampaignCreateRequest(BaseModel):
    brand_id: uuid.UUID | None = None
    name: str = Field(min_length=2, max_length=200)
    goal: str = Field(min_length=5, max_length=5000)
    product_service: str = Field(min_length=2, max_length=300)
    audience: str = Field(min_length=2, max_length=3000)
    instructions: str = Field(default="", max_length=8000)
    platforms: list[Platform] = Field(min_length=1, max_length=6)
    media_types: list[Literal["text", "image", "video"]] = Field(
        default_factory=default_media_types, min_length=1, max_length=3
    )
    start_at: datetime | None = None
    publishing_mode: PublishingMode = "manual"

    @field_validator("platforms", "media_types")
    @classmethod
    def unique_values(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))


class CampaignGenerateRequest(BaseModel):
    feedback: str | None = Field(default=None, max_length=4000)


class CampaignDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    feedback: str | None = Field(default=None, max_length=4000)


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID
    created_by_user_id: uuid.UUID
    name: str
    goal: str
    product_service: str
    audience: str
    instructions: str
    platforms: list[Platform]
    media_types: list[str]
    start_at: datetime | None
    publishing_mode: PublishingMode
    status: CampaignStatus
    current_revision: int
    latest_feedback: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ContentVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    campaign_id: uuid.UUID
    revision: int
    platform: Platform
    title: str | None
    caption: str
    hashtags: list[str]
    call_to_action: str | None
    status: Literal["draft", "approved", "rejected", "superseded"]
    quality_score: float
    validation_issues: list[str]
    citations: list[dict[str, object]]
    generated_by_model: str
    generation_metadata: dict[str, object]
    created_at: datetime


class CampaignStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence: int
    node_name: str
    status: Literal["completed", "failed"]
    duration_ms: int
    citations: list[dict[str, object]]
    provider_metadata: dict[str, object]
    error_message: str | None


class CampaignRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    run_number: int
    revision: int
    status: Literal["running", "waiting_approval", "completed", "failed", "cancelled"]
    current_node: str | None
    provider_metadata: dict[str, object]
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None


class CampaignGenerationResponse(BaseModel):
    campaign: CampaignResponse
    run: CampaignRunResponse
    plan: dict[str, object]
    variants: list[ContentVariantResponse]
    steps: list[CampaignStepResponse]
