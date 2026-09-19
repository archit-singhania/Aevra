import uuid
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from aevra_api.config import Settings
from aevra_api.domain.errors import AuthenticationError

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(user_id: uuid.UUID, settings: Settings) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires,
        "iss": "aevra-api",
        "aud": "aevra-web",
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, settings.access_token_minutes * 60


def decode_access_token(token: str, settings: Settings) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            audience="aevra-web",
            issuer="aevra-api",
        )
        return uuid.UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid or expired access token") from exc


def create_onboarding_token(user_id: uuid.UUID, settings: Settings) -> tuple[str, int]:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id), "iat": now,
        "exp": now + timedelta(days=settings.payment_expiry_days),
        "iss": "aevra-api", "aud": "aevra-onboarding",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), settings.payment_expiry_days * 86400


def decode_onboarding_token(token: str, settings: Settings) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM], audience="aevra-onboarding", issuer="aevra-api")
        return uuid.UUID(str(payload["sub"]))
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid or expired onboarding token") from exc


def create_oauth_state(
    user_id: uuid.UUID, workspace_id: uuid.UUID, provider: str, settings: Settings
) -> str:
    """Create a short-lived, signed OAuth state bound to the current workspace."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "wid": str(workspace_id),
        "provider": provider,
        "nonce": token_urlsafe(24),
        "iat": now,
        "exp": now + timedelta(minutes=settings.oauth_state_minutes),
        "iss": "aevra-api",
        "aud": "aevra-oauth",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_oauth_state(state: str, settings: Settings) -> dict[str, str]:
    """Validate OAuth state and return only the identifiers needed by a callback."""
    try:
        payload = jwt.decode(
            state,
            settings.secret_key,
            algorithms=[ALGORITHM],
            audience="aevra-oauth",
            issuer="aevra-api",
        )
        user_id = uuid.UUID(str(payload["sub"]))
        workspace_id = uuid.UUID(str(payload["wid"]))
        provider = str(payload["provider"])
        nonce = str(payload["nonce"])
        if not provider or not nonce:
            raise ValueError("OAuth state is incomplete")
        return {
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
            "provider": provider,
            "nonce": nonce,
        }
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise AuthenticationError("Invalid or expired OAuth state") from exc
