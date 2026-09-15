import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import BrandProfile, BrandRule, OrganizationMember, Workspace


class BrandRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def slug_exists(self, workspace_id: uuid.UUID, slug: str) -> bool:
        statement = select(BrandProfile.id).where(
            BrandProfile.workspace_id == workspace_id,
            BrandProfile.slug == slug,
        )
        return self.session.scalar(statement) is not None

    def add_brand(self, brand: BrandProfile) -> None:
        self.session.add(brand)

    def add_rule(self, rule: BrandRule) -> None:
        self.session.add(rule)

    def get_brand_by_slug_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, slug: str
    ) -> BrandProfile | None:
        statement = (
            select(BrandProfile)
            .join(Workspace, Workspace.id == BrandProfile.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                BrandProfile.workspace_id == workspace_id,
                BrandProfile.slug == slug,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def list_brands_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[BrandProfile]:
        statement = (
            select(BrandProfile)
            .join(Workspace, Workspace.id == BrandProfile.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                BrandProfile.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
            .order_by(BrandProfile.created_at, BrandProfile.id)
        )
        return list(self.session.scalars(statement).all())

    def get_brand_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        brand_id: uuid.UUID,
    ) -> BrandProfile | None:
        statement = (
            select(BrandProfile)
            .join(Workspace, Workspace.id == BrandProfile.workspace_id)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                BrandProfile.id == brand_id,
                BrandProfile.workspace_id == workspace_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def list_rules_for_user(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        brand_id: uuid.UUID,
    ) -> list[BrandRule] | None:
        brand = self.get_brand_for_user(user_id, workspace_id, brand_id)
        if brand is None:
            return None
        statement = (
            select(BrandRule)
            .where(
                BrandRule.workspace_id == workspace_id,
                BrandRule.brand_id == brand_id,
                BrandRule.is_active.is_(True),
            )
            .order_by(BrandRule.priority.desc(), BrandRule.created_at, BrandRule.id)
        )
        return list(self.session.scalars(statement).all())
