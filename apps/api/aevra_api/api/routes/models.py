import uuid

from fastapi import APIRouter

from aevra_api.api.dependencies import CurrentUser, LLMProviderDep, SessionDep
from aevra_api.schemas.models import (
    LocalGenerateRequest,
    LocalGenerateResponse,
    LocalModelStatusResponse,
)
from aevra_api.services.models import LocalModelService

router = APIRouter(prefix="/workspaces/{workspace_id}/models/local", tags=["models"])


@router.get("/status", response_model=LocalModelStatusResponse)
def local_model_status(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    provider: LLMProviderDep,
) -> LocalModelStatusResponse:
    result = LocalModelService(session, provider).status(current_user.id, workspace_id)
    return LocalModelStatusResponse(
        available=result.available,
        provider=result.provider,
        model=result.model,
        detail=result.detail,
    )


@router.post("/generate", response_model=LocalGenerateResponse)
def generate_locally(
    workspace_id: uuid.UUID,
    request: LocalGenerateRequest,
    current_user: CurrentUser,
    session: SessionDep,
    provider: LLMProviderDep,
) -> LocalGenerateResponse:
    result = LocalModelService(session, provider).generate(current_user.id, workspace_id, request)
    return LocalGenerateResponse(
        content=result.content,
        model=result.model,
        provider=result.provider,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        metadata=result.metadata,
    )
