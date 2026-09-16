from dataclasses import dataclass

import httpx
from conftest import bearer, register_account
from fastapi.testclient import TestClient

from aevra_api.ai.contracts import (
    GenerationRequest,
    GenerationResult,
    ProviderStatus,
)
from aevra_api.ai.embeddings import OllamaEmbeddingProvider
from aevra_api.ai.llm import OllamaLLMProvider
from aevra_api.api.dependencies import get_llm_provider
from aevra_api.config import Settings
from aevra_api.domain.errors import ProviderUnavailableError
from aevra_api.main import app


@dataclass
class FakeLLMProvider:
    calls: int = 0

    @property
    def model_name(self) -> str:
        return "qwen-test"

    def status(self) -> ProviderStatus:
        return ProviderStatus(True, "fake-local", self.model_name, "Ready")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        return GenerationResult(
            content=f"Grounded: {request.messages[-1].content}",
            model=self.model_name,
            provider="fake-local",
            prompt_tokens=8,
            completion_tokens=4,
            metadata={"offline": True},
        )


class FailingLLMProvider(FakeLLMProvider):
    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderUnavailableError("Local language model is unavailable")


def test_local_model_gateway_and_workspace_boundary(client: TestClient) -> None:
    owner = register_account(
        client,
        email="model-owner@example.com",
        organization_name="Model Labs",
        workspace_name="Core",
    )
    outsider = register_account(
        client,
        email="model-outsider@example.com",
        organization_name="Other Labs",
        workspace_name="Other",
    )
    provider = FakeLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    endpoint = f"/api/v1/workspaces/{workspace_id}/models/local"

    status = client.get(f"{endpoint}/status", headers=bearer(owner))
    generated = client.post(
        f"{endpoint}/generate",
        headers=bearer(owner),
        json={
            "prompt": "Write a verified launch line",
            "system_prompt": "Be concise",
            "response_format": "json",
        },
    )
    denied = client.post(
        f"{endpoint}/generate",
        headers=bearer(outsider),
        json={"prompt": "Leak another tenant's context"},
    )
    assert status.status_code == 200 and status.json()["available"] is True
    assert generated.status_code == 200, generated.text
    assert generated.json()["provider"] == "fake-local"
    assert generated.json()["metadata"]["offline"] is True
    assert denied.status_code == 404
    assert provider.calls == 1


def test_local_model_failure_has_stable_api_error(client: TestClient) -> None:
    owner = register_account(
        client,
        email="model-failure@example.com",
        organization_name="Failure Lab",
        workspace_name="Core",
    )
    app.dependency_overrides[get_llm_provider] = lambda: FailingLLMProvider()
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/models/local/generate",
        headers=bearer(owner),
        json={"prompt": "Try a local generation"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"


def test_ollama_adapters_validate_status_generation_and_vectors() -> None:
    settings = Settings(
        _env_file=None,
        secret_key="test-secret-key-that-is-at-least-thirty-two-characters",
        embedding_dimensions=64,
        ollama_model="qwen3:8b",
    )
    first = [1, *([0] * 63)]
    second = [0, 1, *([0] * 62)]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
        if request.url.path == "/api/chat":
            return httpx.Response(
                200,
                json={
                    "model": "qwen3:8b",
                    "message": {"content": "Local answer"},
                    "prompt_eval_count": 5,
                    "eval_count": 2,
                    "done": True,
                },
            )
        return httpx.Response(200, json={"embeddings": [first, second]})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama")
    llm = OllamaLLMProvider(settings, client)
    embedding = OllamaEmbeddingProvider(settings, client)
    assert llm.status().available is True
    result = llm.generate(GenerationRequest(messages=[]))
    assert result.content == "Local answer" and result.completion_tokens == 2
    assert embedding.embed(["one", "two"]) == [
        [float(value) for value in first],
        [float(value) for value in second],
    ]


def test_ollama_generation_wraps_malformed_responses() -> None:
    settings = Settings(
        _env_file=None,
        secret_key="test-secret-key-that-is-at-least-thirty-two-characters",
    )
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={})),
        base_url="http://ollama",
    )
    provider = OllamaLLMProvider(settings, client)
    try:
        provider.generate(GenerationRequest(messages=[]))
        raise AssertionError("Malformed provider response was accepted")
    except ProviderUnavailableError:
        pass
