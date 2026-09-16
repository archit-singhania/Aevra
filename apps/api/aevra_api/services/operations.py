from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from aevra_api.db.models import AuditLog, PostMetric, ScheduledPost
from aevra_api.domain.errors import ConflictError, ForbiddenError, NotFoundError
from aevra_api.repositories.operations import OperationsRepository
from aevra_api.repositories.publishing import PublishingRepository
from aevra_api.repositories.tenancy import TenancyRepository
from aevra_api.schemas.operations import MetricsCreateRequest, ScheduleCreateRequest

EDIT_ROLES = {"owner", "admin", "member"}


class OperationsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = OperationsRepository(session)
        self.publishing = PublishingRepository(session)
        self.tenancy = TenancyRepository(session)

    def _access(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> str:
        access = self.tenancy.get_workspace_access(user_id, workspace_id)
        if access is None:
            raise NotFoundError("Workspace not found")
        return access[1]

    def _editor(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        if self._access(user_id, workspace_id) not in EDIT_ROLES:
            raise ForbiddenError("Operations editor access is required")

    def schedule(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, request: ScheduleCreateRequest
    ) -> ScheduledPost:
        self._editor(user_id, workspace_id)
        if request.scheduled_for <= datetime.now(UTC):
            raise ConflictError("scheduled_for must be in the future")
        if self.publishing.campaign(user_id, workspace_id, request.campaign_id) is None:
            raise NotFoundError("Campaign not found")
        account = self.publishing.account(user_id, workspace_id, request.social_account_id)
        if account is None or account.status != "connected":
            raise NotFoundError("Connected social account not found")
        existing = (
            self.session.query(ScheduledPost)
            .filter_by(workspace_id=workspace_id, idempotency_key=request.idempotency_key)
            .first()
        )
        if existing is not None:
            return existing
        item = ScheduledPost(
            workspace_id=workspace_id,
            campaign_id=request.campaign_id,
            social_account_id=request.social_account_id,
            created_by_user_id=user_id,
            idempotency_key=request.idempotency_key,
            scheduled_for=request.scheduled_for,
            status="scheduled",
            payload={"text": request.text, "media_urls": request.media_urls},
        )
        self.session.add(item)
        self.session.add(
            AuditLog(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                action="schedule.created",
                resource_type="scheduled_post",
                resource_id=str(item.id),
                details={"scheduled_for": request.scheduled_for.isoformat()},
            )
        )
        self.session.commit()
        return item

    def scheduled(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[ScheduledPost]:
        self._access(user_id, workspace_id)
        return self.repo.scheduled(user_id, workspace_id)

    def record_metrics(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, request: MetricsCreateRequest
    ) -> PostMetric:
        self._editor(user_id, workspace_id)
        if self.publishing.account(user_id, workspace_id, request.social_account_id) is None:
            raise NotFoundError("Connected social account not found")
        item = PostMetric(
            workspace_id=workspace_id,
            social_account_id=request.social_account_id,
            external_post_id=request.external_post_id,
            collected_at=request.collected_at,
            impressions=request.impressions,
            engagements=request.engagements,
            clicks=request.clicks,
            likes=request.likes,
            comments=request.comments,
            shares=request.shares,
            metric_metadata=request.metric_metadata,
        )
        self.session.add(item)
        self.session.add(
            AuditLog(
                workspace_id=workspace_id,
                actor_user_id=user_id,
                action="analytics.metrics_recorded",
                resource_type="post_metric",
                resource_id=request.external_post_id,
                details={"impressions": request.impressions, "engagements": request.engagements},
            )
        )
        self.session.commit()
        return item

    def metrics(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[PostMetric]:
        self._access(user_id, workspace_id)
        return self.repo.metrics(user_id, workspace_id)

    def audit(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[AuditLog]:
        self._access(user_id, workspace_id)
        return self.repo.audit(user_id, workspace_id)
