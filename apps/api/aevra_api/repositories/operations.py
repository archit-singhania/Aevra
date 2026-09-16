import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import AuditLog, OrganizationMember, PostMetric, ScheduledPost, Workspace


class OperationsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _scoped(
        self,
        model: type[ScheduledPost] | type[PostMetric] | type[AuditLog],
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ):
        return (
            select(model)
            .join(Workspace, Workspace.id == model.workspace_id)
            .join(
                OrganizationMember, OrganizationMember.organization_id == Workspace.organization_id
            )
            .where(model.workspace_id == workspace_id, OrganizationMember.user_id == user_id)
        )

    def scheduled(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[ScheduledPost]:
        return list(
            self.session.scalars(
                self._scoped(ScheduledPost, user_id, workspace_id).order_by(
                    ScheduledPost.scheduled_for
                )
            ).all()
        )

    def due(self, workspace_id: uuid.UUID, now):
        return list(
            self.session.scalars(
                select(ScheduledPost)
                .where(
                    ScheduledPost.workspace_id == workspace_id,
                    ScheduledPost.status == "scheduled",
                    ScheduledPost.scheduled_for <= now,
                )
                .order_by(ScheduledPost.scheduled_for)
            ).all()
        )

    def metrics(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[PostMetric]:
        return list(
            self.session.scalars(
                self._scoped(PostMetric, user_id, workspace_id).order_by(
                    PostMetric.collected_at.desc()
                )
            ).all()
        )

    def audit(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[AuditLog]:
        return list(
            self.session.scalars(
                self._scoped(AuditLog, user_id, workspace_id).order_by(AuditLog.created_at.desc())
            ).all()
        )
