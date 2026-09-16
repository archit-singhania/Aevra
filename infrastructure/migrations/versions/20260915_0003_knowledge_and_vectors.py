"""Create workspace-scoped knowledge documents and vector chunks.

Revision ID: 20260915_0003
Revises: 20260915_0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "20260915_0003"
down_revision: str | None = "20260915_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("brand_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_uri", sa.String(length=2048), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("normalized_content", sa.Text(), nullable=False),
        sa.Column("content_length", sa.Integer(), nullable=False),
        sa.Column("document_metadata", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_type IN ('text', 'markdown', 'website', 'pdf')",
            name=op.f("ck_knowledge_documents_valid_knowledge_source_type"),
        ),
        sa.CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name=op.f("ck_knowledge_documents_valid_knowledge_status"),
        ),
        sa.ForeignKeyConstraint(
            ["brand_id", "workspace_id"],
            ["brand_profiles.id", "brand_profiles.workspace_id"],
            name=op.f("fk_knowledge_documents_brand_id_brand_profiles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name=op.f("fk_knowledge_documents_created_by_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_knowledge_documents_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_documents")),
        sa.UniqueConstraint(
            "id", "workspace_id", name="uq_knowledge_documents_id_workspace"
        ),
        sa.UniqueConstraint(
            "workspace_id", "checksum", name="uq_knowledge_documents_checksum"
        ),
    )
    op.create_index(
        op.f("ix_knowledge_documents_brand_id"),
        "knowledge_documents",
        ["brand_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_created_by_user_id"),
        "knowledge_documents",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_workspace_id"),
        "knowledge_documents",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_documents_workspace_created",
        "knowledge_documents",
        ["workspace_id", "created_at"],
        unique=False,
    )

    embedding_type: sa.TypeEngine[object] = (
        Vector(384) if dialect_name == "postgresql" else sa.JSON()
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("embedding", embedding_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name=op.f("ck_knowledge_chunks_valid_knowledge_chunk_index"),
        ),
        sa.CheckConstraint(
            "start_offset >= 0",
            name=op.f("ck_knowledge_chunks_valid_knowledge_start_offset"),
        ),
        sa.CheckConstraint(
            "end_offset > start_offset",
            name=op.f("ck_knowledge_chunks_valid_knowledge_end_offset"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id", "workspace_id"],
            ["knowledge_documents.id", "knowledge_documents.workspace_id"],
            name=op.f("fk_knowledge_chunks_document_id_knowledge_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_chunks")),
        sa.UniqueConstraint(
            "document_id", "chunk_index", name=op.f("uq_knowledge_chunks_document_id")
        ),
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_workspace_id"),
        "knowledge_chunks",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_workspace_document",
        "knowledge_chunks",
        ["workspace_id", "document_id"],
        unique=False,
    )
    if dialect_name == "postgresql":
        op.create_index(
            "ix_knowledge_chunks_embedding_hnsw",
            "knowledge_chunks",
            ["embedding"],
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
