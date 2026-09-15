import uuid

from fastapi import APIRouter, status

from aevra_api.api.dependencies import CurrentUser, SessionDep
from aevra_api.schemas.tenancy import WorkspaceCreateRequest, WorkspaceResponse
from aevra_api.services.tenancy import TenancyService

router = APIRouter(tags=["workspaces"])


@router.get("/workspaces", response_model=list[WorkspaceResponse])
def list_workspaces(current_user: CurrentUser, session: SessionDep) -> list[WorkspaceResponse]:
    workspaces = TenancyService(session).list_workspaces(current_user.id)
    return [WorkspaceResponse.model_validate(workspace) for workspace in workspaces]


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> WorkspaceResponse:
    workspace = TenancyService(session).get_workspace(current_user.id, workspace_id)
    return WorkspaceResponse.model_validate(workspace)


@router.post(
    "/organizations/{organization_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    organization_id: uuid.UUID,
    request: WorkspaceCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> WorkspaceResponse:
    workspace = TenancyService(session).create_workspace(
        current_user.id,
        organization_id,
        request,
    )
    return WorkspaceResponse.model_validate(workspace)
