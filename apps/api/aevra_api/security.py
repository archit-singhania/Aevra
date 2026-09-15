import uuid
from datetime import UTC, datetime, timedelta
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
