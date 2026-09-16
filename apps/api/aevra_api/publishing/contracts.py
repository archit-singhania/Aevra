from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

import httpx


class PublishStatus(StrEnum):
    PUBLISHED = "published"
    FAILED = "failed"
    ALREADY_PUBLISHED = "already_published"


class PublisherError(RuntimeError):
    """Safe publishing error with a retry classification."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class PublishRequest:
    idempotency_key: str
    account_id: str
    text: str
    media_urls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.idempotency_key or len(self.idempotency_key) > 160:
            raise ValueError("idempotency_key is required and must be <= 160 characters")
        if not self.account_id.strip():
            raise ValueError("account_id is required")
        if not self.text.strip() or len(self.text) > 30_000:
            raise ValueError("publish text must contain 1-30,000 characters")


@dataclass(frozen=True)
class PublishResult:
    status: PublishStatus
    external_post_id: str | None
    external_url: str | None
    published_at: datetime | None
    provider: str
    raw_metadata: dict[str, Any]


class SocialPublisher(Protocol):
    platform: str

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult: ...

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult: ...


class MockSocialPublisher:
    platform = "mock"

    def __init__(self) -> None:
        self._posts: dict[str, PublishResult] = {}

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        del access_token
        existing = self._posts.get(request.idempotency_key)
        if existing is not None:
            return PublishResult(
                PublishStatus.ALREADY_PUBLISHED,
                existing.external_post_id,
                existing.external_url,
                existing.published_at,
                self.platform,
                {"idempotent": True},
            )
        digest = hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:20]
        result = PublishResult(
            PublishStatus.PUBLISHED,
            f"mock_{digest}",
            f"https://mock.aevra.local/posts/{digest}",
            datetime.now(UTC),
            self.platform,
            {"text_sha256": hashlib.sha256(request.text.encode()).hexdigest()},
        )
        self._posts[request.idempotency_key] = result
        return result

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        del access_token
        found = next(
            (item for item in self._posts.values() if item.external_post_id == external_post_id),
            None,
        )
        if found is None:
            raise PublisherError("Mock post was not found", retryable=False)
        return found


class LinkedInPublisher:
    """LinkedIn REST adapter using the organization authoring API.

    HTTP is injected in tests and callers can provide a configured httpx client.
    Tokens never enter request metadata or error messages.
    """

    platform = "linkedin"

    def __init__(
        self, *, base_url: str = "https://api.linkedin.com", client: httpx.Client | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        headers = {"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"}
        payload: dict[str, Any] = {
            "author": request.account_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": request.text},
                    "shareMediaCategory": "NONE" if not request.media_urls else "ARTICLE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        try:
            response = self.client.post(
                f"{self.base_url}/v2/ugcPosts", headers=headers, json=payload
            )
        except httpx.HTTPError as error:
            raise PublisherError("LinkedIn transport failed", retryable=True) from error
        if response.status_code in {401, 403}:
            raise PublisherError("LinkedIn authorization was rejected", retryable=False)
        if response.status_code == 429 or response.status_code >= 500:
            raise PublisherError("LinkedIn is temporarily unavailable", retryable=True)
        if response.status_code >= 400:
            raise PublisherError("LinkedIn rejected the post", retryable=False)
        external_id = response.headers.get("x-restli-id") or response.json().get("id")
        if not external_id:
            raise PublisherError("LinkedIn returned no post identifier", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            str(external_id),
            f"https://www.linkedin.com/feed/update/{external_id}",
            datetime.now(UTC),
            self.platform,
            {"http_status": response.status_code},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        headers = {"Authorization": f"Bearer {access_token}", "X-Restli-Protocol-Version": "2.0.0"}
        try:
            response = self.client.get(
                f"{self.base_url}/v2/ugcPosts/{external_post_id}", headers=headers
            )
        except httpx.HTTPError as error:
            raise PublisherError(
                "LinkedIn verification transport failed", retryable=True
            ) from error
        if response.status_code == 404:
            raise PublisherError("LinkedIn post was not found during verification", retryable=False)
        if response.status_code >= 500:
            raise PublisherError("LinkedIn verification is temporarily unavailable", retryable=True)
        if response.status_code >= 400:
            raise PublisherError("LinkedIn verification was rejected", retryable=False)
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            f"https://www.linkedin.com/feed/update/{external_post_id}",
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )
