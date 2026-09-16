import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from aevra_api.db.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    OrganizationMember,
    Workspace,
)


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_document(self, document: KnowledgeDocument) -> None:
        self.session.add(document)

    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        self.session.add_all(chunks)

    def find_duplicate_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, checksum: str
    ) -> KnowledgeDocument | None:
        statement = (
            select(KnowledgeDocument)
            .join(Workspace, Workspace.id == KnowledgeDocument.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                KnowledgeDocument.workspace_id == workspace_id,
                KnowledgeDocument.checksum == checksum,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def list_documents_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[KnowledgeDocument]:
        statement = (
            select(KnowledgeDocument)
            .join(Workspace, Workspace.id == KnowledgeDocument.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                KnowledgeDocument.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
            .order_by(KnowledgeDocument.created_at.desc(), KnowledgeDocument.id)
        )
        return list(self.session.scalars(statement).all())

    def candidate_chunks_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        *,
        brand_id: uuid.UUID | None = None,
        source_type: str | None = None,
        product: str | None = None,
        campaign: str | None = None,
    ) -> list[tuple[KnowledgeChunk, KnowledgeDocument]]:
        statement = (
            select(KnowledgeChunk, KnowledgeDocument)
            .join(
                KnowledgeDocument,
                and_(
                    KnowledgeDocument.id == KnowledgeChunk.document_id,
                    KnowledgeDocument.workspace_id == KnowledgeChunk.workspace_id,
                ),
            )
            .join(Workspace, Workspace.id == KnowledgeDocument.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                KnowledgeChunk.workspace_id == workspace_id,
                KnowledgeDocument.status == "ready",
                OrganizationMember.user_id == user_id,
            )
        )
        if brand_id is not None:
            statement = statement.where(KnowledgeDocument.brand_id == brand_id)
        if source_type is not None:
            statement = statement.where(KnowledgeDocument.source_type == source_type)

        rows = list(self.session.execute(statement).all())
        return [
            (row[0], row[1])
            for row in rows
            if (product is None or row[1].document_metadata.get("product") == product)
            and (campaign is None or row[1].document_metadata.get("campaign") == campaign)
        ]

    def ranked_chunks_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        query_embedding: list[float],
        *,
        limit: int,
        min_score: float,
        brand_id: uuid.UUID | None = None,
        source_type: str | None = None,
        product: str | None = None,
        campaign: str | None = None,
    ) -> list[tuple[float, KnowledgeChunk, KnowledgeDocument]]:
        """Use pgvector/HNSW in production; SQLite keeps a deterministic test fallback."""
        if self.session.get_bind().dialect.name != "postgresql":
            return []

        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)  # type: ignore[attr-defined]
        statement = (
            select(KnowledgeChunk, KnowledgeDocument, (1 - distance).label("score"))
            .join(
                KnowledgeDocument,
                and_(
                    KnowledgeDocument.id == KnowledgeChunk.document_id,
                    KnowledgeDocument.workspace_id == KnowledgeChunk.workspace_id,
                ),
            )
            .join(Workspace, Workspace.id == KnowledgeDocument.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                KnowledgeChunk.workspace_id == workspace_id,
                KnowledgeDocument.status == "ready",
                OrganizationMember.user_id == user_id,
                distance <= 1 - min_score,
            )
        )
        if brand_id is not None:
            statement = statement.where(KnowledgeDocument.brand_id == brand_id)
        if source_type is not None:
            statement = statement.where(KnowledgeDocument.source_type == source_type)
        if product is not None:
            statement = statement.where(
                KnowledgeDocument.document_metadata["product"].as_string() == product
            )
        if campaign is not None:
            statement = statement.where(
                KnowledgeDocument.document_metadata["campaign"].as_string() == campaign
            )
        rows = self.session.execute(statement.order_by(distance, KnowledgeChunk.id).limit(limit))
        return [(float(row[2]), row[0], row[1]) for row in rows]

    def count_chunks_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, document_id: uuid.UUID
    ) -> int:
        return sum(
            1
            for _ in self.session.scalars(
                select(KnowledgeChunk.id)
                .join(Workspace, Workspace.id == KnowledgeChunk.workspace_id)
                .join(
                    OrganizationMember,
                    OrganizationMember.organization_id == Workspace.organization_id,
                )
                .where(
                    KnowledgeChunk.document_id == document_id,
                    KnowledgeChunk.workspace_id == workspace_id,
                    OrganizationMember.user_id == user_id,
                )
            )
        )
