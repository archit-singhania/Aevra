import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import (
    Campaign,
    OrganizationMember,
    PublishJob,
    SocialAccount,
    Workspace,
)


class PublishingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _scoped(
        self,
        model: type[SocialAccount] | type[PublishJob],
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

    def accounts(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[SocialAccount]:
        return list(
            self.session.scalars(
                self._scoped(SocialAccount, user_id, workspace_id).order_by(SocialAccount.platform)
            ).all()
        )

    def account(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, account_id: uuid.UUID
    ) -> SocialAccount | None:
        return self.session.scalar(
            self._scoped(SocialAccount, user_id, workspace_id).where(SocialAccount.id == account_id)
        )

    def account_by_identity(
        self, workspace_id: uuid.UUID, platform: str, external_id: str
    ) -> SocialAccount | None:
        return self.session.scalar(
            select(SocialAccount).where(
                SocialAccount.workspace_id == workspace_id,
                SocialAccount.platform == platform,
                SocialAccount.external_account_id == external_id,
            )
        )

    def campaign(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, campaign_id: uuid.UUID
    ) -> Campaign | None:
        return self.session.scalar(
            select(Campaign)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember, OrganizationMember.organization_id == Workspace.organization_id
            )
            .where(
                Campaign.id == campaign_id,
                Campaign.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
        )

    def job(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, job_id: uuid.UUID
    ) -> PublishJob | None:
        return self.session.scalar(
            self._scoped(PublishJob, user_id, workspace_id).where(PublishJob.id == job_id)
        )

    def job_by_key(self, workspace_id: uuid.UUID, key: str) -> PublishJob | None:
        return self.session.scalar(
            select(PublishJob).where(
                PublishJob.workspace_id == workspace_id, PublishJob.idempotency_key == key
            )
        )
