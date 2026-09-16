import uuid

from fastapi import APIRouter, status

from aevra_api.api.dependencies import CurrentUser, SessionDep
from aevra_api.schemas.operations import (
    AuditLogResponse,
    MetricsCreateRequest,
    MetricsResponse,
    ScheduleCreateRequest,
    ScheduledPostResponse,
)
from aevra_api.services.operations import OperationsService

router = APIRouter(prefix="/workspaces/{workspace_id}/operations", tags=["operations"])


@router.post("/schedule", response_model=ScheduledPostResponse, status_code=status.HTTP_201_CREATED)
def schedule(
    workspace_id: uuid.UUID,
    request: ScheduleCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> ScheduledPostResponse:
    item = OperationsService(session).schedule(current_user.id, workspace_id, request)
    return ScheduledPostResponse.model_validate(item)


@router.get("/schedule", response_model=list[ScheduledPostResponse])
def scheduled(
    workspace_id: uuid.UUID, current_user: CurrentUser, session: SessionDep
) -> list[ScheduledPostResponse]:
    items = OperationsService(session).scheduled(current_user.id, workspace_id)
    return [ScheduledPostResponse.model_validate(item) for item in items]


@router.post("/metrics", response_model=MetricsResponse, status_code=status.HTTP_201_CREATED)
def record_metrics(
    workspace_id: uuid.UUID,
    request: MetricsCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> MetricsResponse:
    item = OperationsService(session).record_metrics(current_user.id, workspace_id, request)
    return MetricsResponse.model_validate(item)


@router.get("/metrics", response_model=list[MetricsResponse])
def metrics(
    workspace_id: uuid.UUID, current_user: CurrentUser, session: SessionDep
) -> list[MetricsResponse]:
    items = OperationsService(session).metrics(current_user.id, workspace_id)
    return [MetricsResponse.model_validate(item) for item in items]


@router.get("/audit", response_model=list[AuditLogResponse])
def audit(
    workspace_id: uuid.UUID, current_user: CurrentUser, session: SessionDep
) -> list[AuditLogResponse]:
    items = OperationsService(session).audit(current_user.id, workspace_id)
    return [AuditLogResponse.model_validate(item) for item in items]
