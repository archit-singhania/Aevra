import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aevra_api.db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)

    memberships: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationMember(TimestampMixin, Base):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id"),
        CheckConstraint(
            "role IN ('owner', 'admin', 'member', 'viewer')",
            name="valid_organization_role",
        ),
        Index("ix_organization_members_user_org", "user_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16), default="member")

    organization: Mapped[Organization] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug"),
        Index("ix_workspaces_organization_created", "organization_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_active: Mapped[bool] = mapped_column(default=True)

    organization: Mapped[Organization] = relationship(back_populates="workspaces")
    brands: Mapped[list["BrandProfile"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class BrandProfile(TimestampMixin, Base):
    __tablename__ = "brand_profiles"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug"),
        UniqueConstraint("id", "workspace_id", name="uq_brand_profiles_id_workspace"),
        CheckConstraint("status IN ('draft', 'active', 'archived')", name="valid_brand_status"),
        Index("ix_brand_profiles_workspace_created", "workspace_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tone_attributes: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_audiences: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_ctas: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="draft")

    workspace: Mapped[Workspace] = relationship(back_populates="brands")
    rules: Mapped[list["BrandRule"]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )


class BrandRule(TimestampMixin, Base):
    __tablename__ = "brand_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brand_profiles.id", "brand_profiles.workspace_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "category IN ('voice', 'claim', 'cta', 'terminology', 'compliance')",
            name="valid_brand_rule_category",
        ),
        CheckConstraint(
            "enforcement IN ('required', 'preferred', 'prohibited')",
            name="valid_brand_rule_enforcement",
        ),
        CheckConstraint("priority BETWEEN 1 AND 100", name="valid_brand_rule_priority"),
        Index("ix_brand_rules_workspace_brand", "workspace_id", "brand_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    category: Mapped[str] = mapped_column(String(24))
    enforcement: Mapped[str] = mapped_column(String(16))
    directive: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(default=True)

    brand: Mapped[BrandProfile] = relationship(back_populates="rules")
