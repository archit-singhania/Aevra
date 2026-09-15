import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import Organization, OrganizationMember, User, Workspace


class TenancyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email.strip().lower()))

    def get_user(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def organization_slug_exists(self, slug: str) -> bool:
        organization_id = self.session.scalar(
            select(Organization.id).where(Organization.slug == slug)
        )
        return organization_id is not None

    def add_user(self, user: User) -> None:
        self.session.add(user)

    def add_organization(self, organization: Organization) -> None:
        self.session.add(organization)

    def add_membership(self, membership: OrganizationMember) -> None:
        self.session.add(membership)

    def add_workspace(self, workspace: Workspace) -> None:
        self.session.add(workspace)

    def get_membership(
        self, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> OrganizationMember | None:
        statement = select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == organization_id,
        )
        return self.session.scalar(statement)

    def get_organization_for_user(
        self, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Organization | None:
        statement = (
            select(Organization)
            .join(OrganizationMember)
            .where(
                Organization.id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def get_workspace_for_user(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Workspace | None:
        statement = (
            select(Workspace)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                Workspace.id == workspace_id,
                Workspace.is_active.is_(True),
                OrganizationMember.user_id == user_id,
            )
        )
        return self.session.scalar(statement)

    def get_workspace_access(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> tuple[Workspace, str] | None:
        statement = (
            select(Workspace, OrganizationMember.role)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                Workspace.id == workspace_id,
                Workspace.is_active.is_(True),
                OrganizationMember.user_id == user_id,
            )
        )
        row = self.session.execute(statement).one_or_none()
        return None if row is None else (row[0], row[1])

    def list_workspaces_for_user(self, user_id: uuid.UUID) -> list[Workspace]:
        statement = (
            select(Workspace)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Workspace.organization_id,
            )
            .where(
                OrganizationMember.user_id == user_id,
                Workspace.is_active.is_(True),
            )
            .order_by(Workspace.created_at, Workspace.id)
        )
        return list(self.session.scalars(statement).all())

    def workspace_slug_exists(self, organization_id: uuid.UUID, slug: str) -> bool:
        statement = select(Workspace.id).where(
            Workspace.organization_id == organization_id,
            Workspace.slug == slug,
        )
        return self.session.scalar(statement) is not None
