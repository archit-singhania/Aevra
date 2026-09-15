import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aevra_api.db.models import BrandProfile, BrandRule
from aevra_api.domain.errors import ConflictError, ForbiddenError, NotFoundError
from aevra_api.repositories.brands import BrandRepository
from aevra_api.repositories.tenancy import TenancyRepository
from aevra_api.schemas.brands import (
    BrandCreateRequest,
    BrandRuleCreateRequest,
    BrandUpdateRequest,
)
from aevra_api.services.tenancy import slugify

BRAND_EDIT_ROLES = {"owner", "admin", "member"}


class BrandService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = BrandRepository(session)
        self.tenancy_repository = TenancyRepository(session)

    def _require_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> str:
        access = self.tenancy_repository.get_workspace_access(user_id, workspace_id)
        if access is None:
            raise NotFoundError("Workspace not found")
        return access[1]

    def _require_editor(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        role = self._require_workspace(user_id, workspace_id)
        if role not in BRAND_EDIT_ROLES:
            raise ForbiddenError("Brand editor access is required")

    def _available_slug(self, workspace_id: uuid.UUID, name: str) -> str:
        base = slugify(name)
        candidate = base
        suffix = 2
        while self.repository.slug_exists(workspace_id, candidate):
            candidate = f"{base[:70]}-{suffix}"
            suffix += 1
        return candidate

    def create_brand(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: BrandCreateRequest,
    ) -> BrandProfile:
        self._require_editor(user_id, workspace_id)
        brand = BrandProfile(
            workspace_id=workspace_id,
            slug=self._available_slug(workspace_id, request.name),
            **request.model_dump(),
        )
        self.repository.add_brand(brand)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("A brand with this identity already exists") from exc
        return brand

    def list_brands(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[BrandProfile]:
        self._require_workspace(user_id, workspace_id)
        return self.repository.list_brands_for_user(user_id, workspace_id)

    def get_brand(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, brand_id: uuid.UUID
    ) -> BrandProfile:
        brand = self.repository.get_brand_for_user(user_id, workspace_id, brand_id)
        if brand is None:
            raise NotFoundError("Brand not found")
        return brand

    def update_brand(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        brand_id: uuid.UUID,
        request: BrandUpdateRequest,
    ) -> BrandProfile:
        self._require_editor(user_id, workspace_id)
        brand = self.get_brand(user_id, workspace_id, brand_id)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(brand, field, value)
        self.session.commit()
        return brand

    def create_rule(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        brand_id: uuid.UUID,
        request: BrandRuleCreateRequest,
    ) -> BrandRule:
        self._require_editor(user_id, workspace_id)
        self.get_brand(user_id, workspace_id, brand_id)
        rule = BrandRule(
            workspace_id=workspace_id,
            brand_id=brand_id,
            created_by_user_id=user_id,
            **request.model_dump(),
        )
        self.repository.add_rule(rule)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("The brand rule could not be stored") from exc
        return rule

    def list_rules(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, brand_id: uuid.UUID
    ) -> list[BrandRule]:
        rules = self.repository.list_rules_for_user(user_id, workspace_id, brand_id)
        if rules is None:
            raise NotFoundError("Brand not found")
        return rules
