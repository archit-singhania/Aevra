import uuid

from sqlalchemy.orm import Session

from aevra_api.ai.contracts import (
    ChatMessage,
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderStatus,
)
from aevra_api.domain.errors import NotFoundError
from aevra_api.repositories.tenancy import TenancyRepository
from aevra_api.schemas.models import LocalGenerateRequest


class LocalModelService:
    def __init__(self, session: Session, provider: LLMProvider) -> None:
        self.repository = TenancyRepository(session)
        self.provider = provider

    def _require_workspace(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        if self.repository.get_workspace_access(user_id, workspace_id) is None:
            raise NotFoundError("Workspace not found")

    def status(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> ProviderStatus:
        self._require_workspace(user_id, workspace_id)
        return self.provider.status()

    def generate(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request: LocalGenerateRequest,
    ) -> GenerationResult:
        self._require_workspace(user_id, workspace_id)
        messages = []
        if request.system_prompt:
            messages.append(ChatMessage(role="system", content=request.system_prompt))
        messages.append(ChatMessage(role="user", content=request.prompt))
        return self.provider.generate(
            GenerationRequest(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format=request.response_format,
            )
        )
