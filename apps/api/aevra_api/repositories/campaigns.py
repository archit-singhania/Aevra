import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from aevra_api.db.models import (
    Campaign,
    CampaignRun,
    CampaignStep,
    ContentVariant,
    OrganizationMember,
    Workspace,
)


class CampaignRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_campaign(self, campaign: Campaign) -> None:
        self.session.add(campaign)

    def get_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, campaign_id: uuid.UUID
    ) -> Campaign | None:
        statement = (
            select(Campaign)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                Campaign.id == campaign_id,
                Campaign.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def list_for_user(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[Campaign]:
        statement = (
            select(Campaign)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                Campaign.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
            .order_by(Campaign.created_at.desc(), Campaign.id)
        )
        return list(self.session.scalars(statement).all())

    def next_run_number(self, campaign_id: uuid.UUID) -> int:
        current = self.session.scalar(
            select(func.max(CampaignRun.run_number)).where(CampaignRun.campaign_id == campaign_id)
        )
        return int(current or 0) + 1

    def add_run(self, run: CampaignRun) -> None:
        self.session.add(run)

    def latest_run_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, campaign_id: uuid.UUID
    ) -> CampaignRun | None:
        statement = (
            select(CampaignRun)
            .join(Campaign, Campaign.id == CampaignRun.campaign_id)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                CampaignRun.workspace_id == workspace_id,
                CampaignRun.campaign_id == campaign_id,
                OrganizationMember.user_id == user_id,
            )
            .order_by(CampaignRun.run_number.desc())
        )
        return self.session.scalar(statement)

    def add_step(self, step: CampaignStep) -> None:
        self.session.add(step)

    def add_variants(self, variants: list[ContentVariant]) -> None:
        self.session.add_all(variants)

    def list_variants_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        campaign_id: uuid.UUID,
        revision: int | None = None,
    ) -> list[ContentVariant]:
        statement = (
            select(ContentVariant)
            .join(Campaign, Campaign.id == ContentVariant.campaign_id)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                ContentVariant.workspace_id == workspace_id,
                ContentVariant.campaign_id == campaign_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if revision is not None:
            statement = statement.where(ContentVariant.revision == revision)
        return list(
            self.session.scalars(
                statement.order_by(ContentVariant.revision.desc(), ContentVariant.platform)
            ).all()
        )

    def list_steps_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[CampaignStep]:
        statement = (
            select(CampaignStep)
            .join(CampaignRun, CampaignRun.id == CampaignStep.run_id)
            .join(Campaign, Campaign.id == CampaignRun.campaign_id)
            .join(Workspace, Workspace.id == Campaign.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                CampaignStep.workspace_id == workspace_id,
                CampaignStep.run_id == run_id,
                OrganizationMember.user_id == user_id,
            )
            .order_by(CampaignStep.sequence)
        )
        return list(self.session.scalars(statement).all())

    def supersede_variants(self, campaign_id: uuid.UUID) -> None:
        self.session.execute(
            update(ContentVariant)
            .where(
                ContentVariant.campaign_id == campaign_id,
                ContentVariant.status.in_(["draft", "rejected"]),
            )
            .values(status="superseded")
        )
