import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import (
    Campaign,
    MediaAsset,
    OrganizationMember,
    Workspace,
)


class MediaRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, asset: MediaAsset) -> None:
        self.session.add(asset)

    def add_many(self, assets: list[MediaAsset]) -> None:
        self.session.add_all(assets)

    def get_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, asset_id: uuid.UUID
    ) -> MediaAsset | None:
        statement = (
            select(MediaAsset)
            .join(Workspace, Workspace.id == MediaAsset.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                MediaAsset.id == asset_id,
                MediaAsset.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def list_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        campaign_id: uuid.UUID | None = None,
        media_type: str | None = None,
    ) -> list[MediaAsset]:
        statement = (
            select(MediaAsset)
            .join(Workspace, Workspace.id == MediaAsset.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                MediaAsset.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
        )
        if campaign_id is not None:
            statement = statement.where(MediaAsset.campaign_id == campaign_id)
        if media_type is not None:
            statement = statement.where(MediaAsset.media_type == media_type)
        statement = statement.order_by(MediaAsset.created_at.desc(), MediaAsset.id)
        return list(self.session.scalars(statement).all())

    def get_campaign_for_user(
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
