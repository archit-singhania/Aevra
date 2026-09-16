import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
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


class KnowledgeDocument(TimestampMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        UniqueConstraint("id", "workspace_id", name="uq_knowledge_documents_id_workspace"),
        UniqueConstraint("workspace_id", "checksum", name="uq_knowledge_documents_checksum"),
        ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brand_profiles.id", "brand_profiles.workspace_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "source_type IN ('text', 'markdown', 'website', 'pdf')",
            name="valid_knowledge_source_type",
        ),
        CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name="valid_knowledge_status",
        ),
        Index("ix_knowledge_documents_workspace_created", "workspace_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(16))
    source_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64))
    normalized_content: Mapped[str] = mapped_column(Text)
    content_length: Mapped[int] = mapped_column(Integer)
    document_metadata: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="processing")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class KnowledgeChunk(TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id", "workspace_id"],
            ["knowledge_documents.id", "knowledge_documents.workspace_id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint("document_id", "chunk_index"),
        CheckConstraint("chunk_index >= 0", name="valid_knowledge_chunk_index"),
        CheckConstraint("start_offset >= 0", name="valid_knowledge_start_offset"),
        CheckConstraint("end_offset > start_offset", name="valid_knowledge_end_offset"),
        Index("ix_knowledge_chunks_workspace_document", "workspace_id", "document_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int] = mapped_column(Integer)
    end_offset: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[int] = mapped_column(Integer)
    embedding_model: Mapped[str] = mapped_column(String(120))
    embedding: Mapped[list[float]] = mapped_column(Vector(384).with_variant(JSON(), "sqlite"))
