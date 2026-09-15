import uuid

from fastapi import APIRouter, status

from aevra_api.api.dependencies import CurrentUser, SessionDep
from aevra_api.schemas.brands import (
    BrandCreateRequest,
    BrandResponse,
    BrandRuleCreateRequest,
    BrandRuleResponse,
    BrandUpdateRequest,
)
from aevra_api.services.brands import BrandService

router = APIRouter(prefix="/workspaces/{workspace_id}/brands", tags=["brands"])


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
def create_brand(
    workspace_id: uuid.UUID,
    request: BrandCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> BrandResponse:
    brand = BrandService(session).create_brand(current_user.id, workspace_id, request)
    return BrandResponse.model_validate(brand)


@router.get("", response_model=list[BrandResponse])
def list_brands(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> list[BrandResponse]:
    brands = BrandService(session).list_brands(current_user.id, workspace_id)
    return [BrandResponse.model_validate(brand) for brand in brands]


@router.get("/{brand_id}", response_model=BrandResponse)
def get_brand(
    workspace_id: uuid.UUID,
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> BrandResponse:
    brand = BrandService(session).get_brand(current_user.id, workspace_id, brand_id)
    return BrandResponse.model_validate(brand)


@router.patch("/{brand_id}", response_model=BrandResponse)
def update_brand(
    workspace_id: uuid.UUID,
    brand_id: uuid.UUID,
    request: BrandUpdateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> BrandResponse:
    brand = BrandService(session).update_brand(current_user.id, workspace_id, brand_id, request)
    return BrandResponse.model_validate(brand)


@router.post(
    "/{brand_id}/rules",
    response_model=BrandRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(
    workspace_id: uuid.UUID,
    brand_id: uuid.UUID,
    request: BrandRuleCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> BrandRuleResponse:
    rule = BrandService(session).create_rule(current_user.id, workspace_id, brand_id, request)
    return BrandRuleResponse.model_validate(rule)


@router.get("/{brand_id}/rules", response_model=list[BrandRuleResponse])
def list_rules(
    workspace_id: uuid.UUID,
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> list[BrandRuleResponse]:
    rules = BrandService(session).list_rules(current_user.id, workspace_id, brand_id)
    return [BrandRuleResponse.model_validate(rule) for rule in rules]
