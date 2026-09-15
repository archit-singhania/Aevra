import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

BrandStatus = Literal["draft", "active", "archived"]
RuleCategory = Literal["voice", "claim", "cta", "terminology", "compliance"]
RuleEnforcement = Literal["required", "preferred", "prohibited"]


def normalize_list(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class BrandCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=5000)
    website_url: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=120)
    tone_attributes: list[str] = Field(default_factory=list, max_length=20)
    target_audiences: list[str] = Field(default_factory=list, max_length=20)
    preferred_ctas: list[str] = Field(default_factory=list, max_length=20)
    preferred_hashtags: list[str] = Field(default_factory=list, max_length=40)
    status: BrandStatus = "draft"

    @field_validator("tone_attributes", "target_audiences", "preferred_ctas", "preferred_hashtags")
    @classmethod
    def normalize_values(cls, values: list[str]) -> list[str]:
        return normalize_list(values)

    @field_validator("website_url")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not normalized.startswith(("https://", "http://")):
            raise ValueError("Website URL must start with http:// or https://")
        return normalized


class BrandUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    website_url: str | None = Field(default=None, max_length=2048)
    industry: str | None = Field(default=None, max_length=120)
    tone_attributes: list[str] | None = Field(default=None, max_length=20)
    target_audiences: list[str] | None = Field(default=None, max_length=20)
    preferred_ctas: list[str] | None = Field(default=None, max_length=20)
    preferred_hashtags: list[str] | None = Field(default=None, max_length=40)
    status: BrandStatus | None = None

    @field_validator("tone_attributes", "target_audiences", "preferred_ctas", "preferred_hashtags")
    @classmethod
    def normalize_optional_values(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else normalize_list(values)

    @field_validator("website_url")
    @classmethod
    def validate_optional_website(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        if not normalized.startswith(("https://", "http://")):
            raise ValueError("Website URL must start with http:// or https://")
        return normalized


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    slug: str
    description: str
    website_url: str | None
    industry: str | None
    tone_attributes: list[str]
    target_audiences: list[str]
    preferred_ctas: list[str]
    preferred_hashtags: list[str]
    status: BrandStatus
    created_at: datetime
    updated_at: datetime


class BrandRuleCreateRequest(BaseModel):
    category: RuleCategory
    enforcement: RuleEnforcement
    directive: str = Field(min_length=3, max_length=4000)
    rationale: str | None = Field(default=None, max_length=4000)
    priority: int = Field(default=50, ge=1, le=100)


class BrandRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    brand_id: uuid.UUID
    created_by_user_id: uuid.UUID
    category: RuleCategory
    enforcement: RuleEnforcement
    directive: str
    rationale: str | None
    priority: int
    is_active: bool
    created_at: datetime
