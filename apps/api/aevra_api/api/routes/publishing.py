import uuid

from fastapi import APIRouter, status

from aevra_api.api.dependencies import CurrentUser, SessionDep, SettingsDep
from aevra_api.schemas.publishing import (
    PublishJobResponse,
    PublishRequest,
    SocialAccountCreateRequest,
    SocialAccountResponse,
)
from aevra_api.services.publishing import PublishingService

router = APIRouter(prefix="/workspaces/{workspace_id}/publishing", tags=["publishing"])


@router.get("/accounts", response_model=list[SocialAccountResponse])
def list_accounts(
    workspace_id: uuid.UUID, current_user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> list[SocialAccountResponse]:
    items = PublishingService(session, settings).list_accounts(current_user.id, workspace_id)
    return [SocialAccountResponse.model_validate(item) for item in items]


@router.post("/accounts", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
def connect_account(
    workspace_id: uuid.UUID,
    request: SocialAccountCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> SocialAccountResponse:
    item = PublishingService(session, settings).connect_account(
        current_user.id, workspace_id, request
    )
    return SocialAccountResponse.model_validate(item)


@router.post("/jobs", response_model=PublishJobResponse, status_code=status.HTTP_201_CREATED)
def publish(
    workspace_id: uuid.UUID,
    request: PublishRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> PublishJobResponse:
    item = PublishingService(session, settings).publish(current_user.id, workspace_id, request)
    return PublishJobResponse.model_validate(item)


@router.post("/jobs/{job_id}/verify", response_model=PublishJobResponse)
def verify(
    workspace_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> PublishJobResponse:
    item = PublishingService(session, settings).verify(current_user.id, workspace_id, job_id)
    return PublishJobResponse.model_validate(item)
