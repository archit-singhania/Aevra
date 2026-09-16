import httpx

from aevra_api.ai.contracts import (
    GenerationRequest,
    GenerationResult,
    LLMProvider,
    ProviderStatus,
)
from aevra_api.config import Settings
from aevra_api.domain.errors import ProviderUnavailableError


class OllamaLLMProvider:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(
            base_url=settings.ollama_base_url.rstrip("/"),
            timeout=settings.ollama_timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self.settings.ollama_model

    def status(self) -> ProviderStatus:
        try:
            response = self.client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            installed = any(
                item.get("name") == self.model_name or item.get("model") == self.model_name
                for item in models
                if isinstance(item, dict)
            )
            detail = (
                "Model is installed and ready" if installed else "Ollama is ready; model not found"
            )
            return ProviderStatus(installed, "ollama", self.model_name, detail)
        except (httpx.HTTPError, ValueError, AttributeError):
            return ProviderStatus(False, "ollama", self.model_name, "Ollama is unavailable")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        payload: dict[str, object] = {
            "model": self.model_name,
            "stream": False,
            "messages": [
                {"role": message.role, "content": message.content} for message in request.messages
            ],
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.response_format == "json":
            payload["format"] = "json"
        try:
            response = self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()
            content = body["message"]["content"]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ProviderUnavailableError("Local language model is unavailable") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderUnavailableError("Local language model returned an empty response")
        return GenerationResult(
            content=content,
            model=body.get("model", self.model_name),
            provider="ollama",
            prompt_tokens=body.get("prompt_eval_count"),
            completion_tokens=body.get("eval_count"),
            metadata={"done": bool(body.get("done", True))},
        )


def build_llm_provider(settings: Settings) -> LLMProvider:
    return OllamaLLMProvider(settings)
