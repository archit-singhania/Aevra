import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from aevra_api.ai.contracts import EmbeddingProvider, LLMProvider
from aevra_api.ai.embeddings import build_embedding_provider
from aevra_api.ai.llm import build_llm_provider
from aevra_api.config import Settings, get_settings
from aevra_api.db.models import User
from aevra_api.db.session import get_session
from aevra_api.security import decode_access_token
from aevra_api.services.tenancy import TenancyService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    user_id: uuid.UUID = decode_access_token(token, settings)
    return TenancyService(session).require_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_embedding_provider(settings: SettingsDep) -> EmbeddingProvider:
    return build_embedding_provider(settings)


def get_llm_provider(settings: SettingsDep) -> LLMProvider:
    return build_llm_provider(settings)


EmbeddingProviderDep = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
LLMProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
