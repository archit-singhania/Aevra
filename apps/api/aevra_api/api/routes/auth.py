from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from aevra_api.api.dependencies import CurrentUser, SessionDep, SettingsDep
from aevra_api.db.models import AccountDeletionRequest
from aevra_api.domain.errors import ConflictError
from aevra_api.schemas.tenancy import (
    AccountDeletionCreateRequest,
    AccountDeletionResponse,
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


def set_session_cookie(
    response: Response, token: str, expires_in: int, settings: SettingsDep
) -> None:
    """Set the web session without exposing the token to browser JavaScript."""
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=settings.use_secure_session_cookie,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: SessionDep,
    settings: SettingsDep,
    response: Response,
) -> RegistrationResponse:
    result = TenancyService(session).register(request)
    token, expires_in = create_access_token(result.user.id, settings)
    set_session_cookie(response, token, expires_in, settings)
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
    response: Response,
) -> TokenResponse:
    user = TenancyService(session).authenticate(request.email, request.password)
    token, expires_in = create_access_token(user.id, settings)
    set_session_cookie(response, token, expires_in, settings)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, settings: SettingsDep) -> Response:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.use_secure_session_cookie,
        samesite=settings.session_cookie_samesite,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post(
    "/account-deletion",
    response_model=AccountDeletionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_account_deletion(
    request: AccountDeletionCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> AccountDeletionResponse:
    if request.confirmation_email.strip().lower() != current_user.email.lower():
        raise ConflictError("Confirmation email does not match the signed-in account")
    existing = session.scalar(
        select(AccountDeletionRequest).where(
            AccountDeletionRequest.user_id == current_user.id,
            AccountDeletionRequest.status == "requested",
        )
    )
    if existing is not None:
        return AccountDeletionResponse(
            request_id=existing.id,
            status=existing.status,
            requested_at=existing.requested_at,
            scheduled_for=existing.scheduled_for,
        )
    now = datetime.now(UTC)
    item = AccountDeletionRequest(
        user_id=current_user.id,
        status="requested",
        requested_at=now,
        scheduled_for=now + timedelta(days=30),
    )
    session.add(item)
    session.commit()
    return AccountDeletionResponse(
        request_id=item.id,
        status=item.status,
        requested_at=item.requested_at,
        scheduled_for=item.scheduled_for,
    )
