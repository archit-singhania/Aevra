from fastapi import APIRouter, status

from aevra_api.api.dependencies import CurrentUser, SessionDep, SettingsDep
from aevra_api.schemas.tenancy import (
    LoginRequest,
    OrganizationResponse,
    RegisterRequest,
    RegistrationResponse,
    TokenResponse,
    UserResponse,
    WorkspaceResponse,
)
from aevra_api.security import create_access_token
from aevra_api.services.tenancy import TenancyService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> RegistrationResponse:
    result = TenancyService(session).register(request)
    token, expires_in = create_access_token(result.user.id, settings)
    return RegistrationResponse(
        user=UserResponse.model_validate(result.user),
        organization=OrganizationResponse.model_validate(result.organization),
        workspace=WorkspaceResponse.model_validate(result.workspace),
        token=TokenResponse(access_token=token, expires_in=expires_in),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> TokenResponse:
    user = TenancyService(session).authenticate(request.email, request.password)
    token, expires_in = create_access_token(user.id, settings)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
