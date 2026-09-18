"""Provider OAuth handshakes.

The callback is deliberately small and provider-neutral: it validates a signed,
workspace-bound state, exchanges the one-time code server-side, encrypts the
provider token through the existing vault, and stores only the account metadata.
Provider app review and credentials are still required before these routes can
be used against live accounts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal, cast
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from aevra_api.api.dependencies import CurrentUser, SessionDep, SettingsDep
from aevra_api.config import Settings
from aevra_api.domain.errors import ProviderUnavailableError
from aevra_api.schemas.publishing import Platform, SocialAccountCreateRequest
from aevra_api.security import create_oauth_state, decode_oauth_state
from aevra_api.services.publishing import PublishingService
from aevra_api.services.tenancy import TenancyService

router = APIRouter(prefix="/workspaces/{workspace_id}/publishing/oauth", tags=["oauth"])
callback_router = APIRouter(prefix="/oauth", tags=["oauth"])


@dataclass(frozen=True)
class ProviderConfig:
    client_id: str | None
    client_secret: str | None
    authorize_url: str
    token_url: str
    profile_url: str
    scopes: tuple[str, ...]


class OAuthAuthorizeResponse(BaseModel):
    provider: Platform
    authorization_url: str
    expires_in: int


def provider_config(provider: str, settings: Settings) -> ProviderConfig:
    if provider in {"facebook", "instagram"}:
        return ProviderConfig(
            settings.meta_oauth_client_id,
            settings.meta_oauth_client_secret,
            "https://www.facebook.com/v23.0/dialog/oauth",
            "https://graph.facebook.com/v23.0/oauth/access_token",
            "https://graph.facebook.com/v23.0/me?fields=id,name,username",
            (
                "public_profile",
                "pages_show_list",
                "pages_read_engagement",
                "pages_manage_posts",
                "instagram_basic",
                "instagram_content_publish",
            ),
        )
    if provider == "threads":
        return ProviderConfig(
            settings.threads_oauth_client_id or settings.meta_oauth_client_id,
            settings.threads_oauth_client_secret or settings.meta_oauth_client_secret,
            "https://threads.net/oauth/authorize",
            "https://graph.threads.net/oauth/access_token",
            "https://graph.threads.net/v1.0/me?fields=id,name,username",
            ("threads_basic", "threads_content_publish"),
        )
    if provider == "linkedin":
        return ProviderConfig(
            settings.linkedin_oauth_client_id,
            settings.linkedin_oauth_client_secret,
            "https://www.linkedin.com/oauth/v2/authorization",
            "https://www.linkedin.com/oauth/v2/accessToken",
            "https://api.linkedin.com/v2/userinfo",
            ("openid", "profile", "email", "w_member_social"),
        )
    if provider == "youtube":
        return ProviderConfig(
            settings.youtube_oauth_client_id,
            settings.youtube_oauth_client_secret,
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://www.googleapis.com/youtube/v3/channels",
            ("openid", "email", "profile", "https://www.googleapis.com/auth/youtube.upload"),
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported OAuth provider")


def redirect_uri(provider: str, settings: Settings) -> str:
    """Return one stable callback URL per provider for app-review allowlists."""
    return f"{settings.oauth_redirect_base_url.rstrip('/')}/api/v1/oauth/{provider}/callback"


def frontend_redirect(settings: Settings, **params: str) -> RedirectResponse:
    query = urlencode(params)
    return RedirectResponse(f"{settings.oauth_frontend_url.rstrip('/')}/?{query}", status_code=303)


@router.get("/{provider}/authorize", response_model=OAuthAuthorizeResponse)
def authorize(
    workspace_id: uuid.UUID,
    provider: Literal["facebook", "instagram", "threads", "linkedin", "youtube"],
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> OAuthAuthorizeResponse:
    TenancyService(session).get_workspace(current_user.id, workspace_id)
    config = provider_config(provider, settings)
    if not config.client_id or not config.client_secret:
        raise ProviderUnavailableError(
            f"{provider.title()} OAuth credentials are not configured on this environment"
        )
    state = create_oauth_state(current_user.id, workspace_id, provider, settings)
    uri = redirect_uri(provider, settings)
    query = {
        "client_id": config.client_id,
        "redirect_uri": uri,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
    }
    if provider == "youtube":
        query.update({"access_type": "offline", "prompt": "consent"})
    return OAuthAuthorizeResponse(
        provider=provider,
        authorization_url=f"{config.authorize_url}?{urlencode(query)}",
        expires_in=settings.oauth_state_minutes * 60,
    )


@callback_router.get("/{provider}/callback")
async def callback(
    provider: Literal["facebook", "instagram", "threads", "linkedin", "youtube"],
    settings: SettingsDep,
    session: SessionDep,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    if error:
        return frontend_redirect(
            settings, oauth="error", provider=provider, message="Provider denied access"
        )
    if not code or not state:
        return frontend_redirect(
            settings, oauth="error", provider=provider, message="Missing OAuth code"
        )
    try:
        state_data = decode_oauth_state(state, settings)
        if state_data["provider"] != provider:
            raise ProviderUnavailableError("OAuth state does not match this workspace")
        user_id = uuid.UUID(state_data["user_id"])
        workspace_id = uuid.UUID(state_data["workspace_id"])
        TenancyService(session).require_user(user_id)
        config = provider_config(provider, settings)
        if not config.client_id or not config.client_secret:
            raise ProviderUnavailableError("OAuth credentials are not configured")
        uri = redirect_uri(provider, settings)
        async with httpx.AsyncClient(timeout=20) as client:
            token_response = await client.post(
                config.token_url,
                data={
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "redirect_uri": uri,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            token_payload = token_response.json()
            access_token = str(token_payload.get("access_token", ""))
            if not access_token:
                raise ProviderUnavailableError("Provider returned no access token")
            profile_params = {"part": "snippet", "mine": "true"} if provider == "youtube" else None
            profile_response = await client.get(
                config.profile_url,
                params=profile_params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
        external_id, display_name = profile_identity(provider, profile)
        account = PublishingService(session, settings).connect_account(
            user_id,
            workspace_id,
            SocialAccountCreateRequest(
                platform=provider,
                external_account_id=external_id,
                display_name=display_name,
                access_token_ref=access_token,
                capabilities=["publish", "analytics"],
            ),
        )
        return frontend_redirect(
            settings, oauth="connected", provider=provider, account=str(account.id)
        )
    except (httpx.HTTPError, KeyError, ValueError, ProviderUnavailableError):
        # Provider responses can echo request details; keep those out of the
        # browser redirect and rely on request-id/server logs for diagnosis.
        return frontend_redirect(
            settings, oauth="error", provider=provider, message="OAuth connection failed"
        )


def profile_identity(provider: str, profile: dict[str, object]) -> tuple[str, str]:
    if provider == "youtube":
        items = profile.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            item = items[0]
            snippet_raw = item.get("snippet")
            snippet = cast(dict[str, object], snippet_raw) if isinstance(snippet_raw, dict) else {}
            return str(item.get("id", "youtube-channel")), str(
                snippet.get("title", "YouTube channel")
            )
    external_id = str(profile.get("id", ""))
    display_name = str(
        profile.get("name") or profile.get("username") or f"{provider.title()} account"
    )
    if not external_id:
        raise ProviderUnavailableError("Provider profile did not include an account id")
    return external_id, display_name
