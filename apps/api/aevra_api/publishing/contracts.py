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


class PlatformRestPublisher:
    """Common REST boundary used by the remaining platform adapters."""

    platform = "platform"

    def __init__(self, *, base_url: str, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        try:
            response = self.client.post(
                f"{self.base_url}/v1/{self.platform}/publish",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "account_id": request.account_id,
                    "text": request.text,
                    "media_urls": list(request.media_urls),
                    "idempotency_key": request.idempotency_key,
                },
            )
        except httpx.HTTPError as error:
            raise PublisherError(f"{self.platform} transport failed", retryable=True) from error
        if response.status_code in {401, 403}:
            raise PublisherError(f"{self.platform} authorization was rejected")
        if response.status_code == 429 or response.status_code >= 500:
            raise PublisherError(f"{self.platform} is temporarily unavailable", retryable=True)
        if response.status_code >= 400:
            raise PublisherError(f"{self.platform} rejected the post")
        body = response.json()
        external_id = response.headers.get("x-post-id") or body.get("id")
        if not external_id:
            raise PublisherError(f"{self.platform} returned no post identifier", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            str(external_id),
            body.get("url"),
            datetime.now(UTC),
            self.platform,
            {"http_status": response.status_code},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        try:
            response = self.client.get(
                f"{self.base_url}/v1/{self.platform}/posts/{external_post_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError(
                f"{self.platform} verification transport failed", retryable=True
            ) from error
        if response.status_code == 404:
            raise PublisherError(f"{self.platform} post was not found")
        if response.status_code >= 500:
            raise PublisherError(
                f"{self.platform} verification is temporarily unavailable", retryable=True
            )
        if response.status_code >= 400:
            raise PublisherError(f"{self.platform} verification was rejected")
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            response.json().get("url"),
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )


class InstagramPublisher(PlatformRestPublisher):
    platform = "instagram"


class FacebookPublisher(PlatformRestPublisher):
    platform = "facebook"


class ThreadsPublisher(PlatformRestPublisher):
    platform = "threads"


class XPublisher(PlatformRestPublisher):
    platform = "x"


class YouTubePublisher(PlatformRestPublisher):
    platform = "youtube"


class MetaFacebookPublisher:
    """Facebook Page feed publisher using the Graph API."""

    platform = "facebook"

    def __init__(
        self,
        *,
        base_url: str = "https://graph.facebook.com/v23.0",
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        data: dict[str, str] = {"message": request.text}
        if request.media_urls:
            data["link"] = request.media_urls[0]
        try:
            response = self.client.post(
                f"{self.base_url}/{request.account_id}/feed",
                data=data,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError("Facebook transport failed", retryable=True) from error
        _raise_graph_error(response, "Facebook")
        body = response.json()
        external_id = body.get("id")
        if not external_id:
            raise PublisherError("Facebook returned no post identifier", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            str(external_id),
            f"https://www.facebook.com/{external_id}",
            datetime.now(UTC),
            self.platform,
            {"http_status": response.status_code},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        try:
            response = self.client.get(
                f"{self.base_url}/{external_post_id}",
                params={"fields": "id"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError(
                "Facebook verification transport failed", retryable=True
            ) from error
        _raise_graph_error(response, "Facebook verification")
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            f"https://www.facebook.com/{external_post_id}",
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )


class InstagramGraphPublisher:
    """Instagram Graph API container-create/container-publish workflow."""

    platform = "instagram"

    def __init__(
        self,
        *,
        base_url: str = "https://graph.facebook.com/v23.0",
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        if not request.media_urls:
            raise PublisherError("Instagram requires an image or video URL", retryable=False)
        media_url = request.media_urls[0]
        is_video = media_url.lower().split("?", 1)[0].endswith((".mp4", ".mov", ".m4v"))
        data: dict[str, str] = {
            "caption": request.text,
            "media_type": "REELS" if is_video else "IMAGE",
            ("video_url" if is_video else "image_url"): media_url,
        }
        try:
            container = self.client.post(
                f"{self.base_url}/{request.account_id}/media",
                data=data,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            _raise_graph_error(container, "Instagram media container")
            creation_id = str(container.json().get("id", ""))
            if not creation_id:
                raise PublisherError("Instagram returned no media container id", retryable=True)
            published = self.client.post(
                f"{self.base_url}/{request.account_id}/media_publish",
                data={"creation_id": creation_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError("Instagram transport failed", retryable=True) from error
        _raise_graph_error(published, "Instagram publish")
        external_id = str(published.json().get("id", ""))
        if not external_id:
            raise PublisherError("Instagram returned no media id", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_id,
            f"https://www.instagram.com/p/{external_id}/",
            datetime.now(UTC),
            self.platform,
            {"http_status": published.status_code, "container_id": creation_id},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        try:
            response = self.client.get(
                f"{self.base_url}/{external_post_id}",
                params={"fields": "id"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError(
                "Instagram verification transport failed", retryable=True
            ) from error
        _raise_graph_error(response, "Instagram verification")
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            f"https://www.instagram.com/p/{external_post_id}/",
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )


class ThreadsGraphPublisher:
    """Threads API two-step container creation and publishing."""

    platform = "threads"

    def __init__(
        self,
        *,
        base_url: str = "https://graph.threads.net/v1.0",
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=30.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        data: dict[str, str] = {"media_type": "TEXT", "text": request.text}
        if request.media_urls:
            media_url = request.media_urls[0]
            data["media_type"] = (
                "VIDEO"
                if media_url.lower().split("?", 1)[0].endswith((".mp4", ".mov"))
                else "IMAGE"
            )
            data["video_url" if data["media_type"] == "VIDEO" else "image_url"] = media_url
        try:
            container = self.client.post(
                f"{self.base_url}/{request.account_id}/threads",
                data=data,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            _raise_graph_error(container, "Threads container")
            creation_id = str(container.json().get("id", ""))
            published = self.client.post(
                f"{self.base_url}/{request.account_id}/threads_publish",
                data={"creation_id": creation_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError("Threads transport failed", retryable=True) from error
        _raise_graph_error(published, "Threads publish")
        external_id = str(published.json().get("id", ""))
        if not external_id:
            raise PublisherError("Threads returned no post identifier", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_id,
            f"https://www.threads.net/post/{external_id}",
            datetime.now(UTC),
            self.platform,
            {"http_status": published.status_code, "container_id": creation_id},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        try:
            response = self.client.get(
                f"{self.base_url}/{external_post_id}",
                params={"fields": "id"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError("Threads verification transport failed", retryable=True) from error
        _raise_graph_error(response, "Threads verification")
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            f"https://www.threads.net/post/{external_post_id}",
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )


class YouTubeDataPublisher:
    """YouTube Data API resumable upload publisher."""

    platform = "youtube"

    def __init__(
        self, *, base_url: str = "https://www.googleapis.com", client: httpx.Client | None = None
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=120.0)

    def publish(self, request: PublishRequest, *, access_token: str) -> PublishResult:
        if not request.media_urls:
            raise PublisherError("YouTube requires a video URL", retryable=False)
        try:
            media = self.client.get(request.media_urls[0])
            if media.status_code >= 400:
                raise PublisherError("YouTube source media could not be downloaded", retryable=True)
            content_type = media.headers.get("content-type", "video/mp4")
            metadata = {
                "snippet": {"title": request.text[:100], "description": request.text},
                "status": {"privacyStatus": "private"},
            }
            start = self.client.post(
                f"{self.base_url}/upload/youtube/v3/videos",
                params={"part": "snippet,status"},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Upload-Content-Type": content_type,
                    "X-Upload-Content-Length": str(len(media.content)),
                },
                json=metadata,
            )
            if start.status_code >= 400 or not start.headers.get("location"):
                raise PublisherError(
                    "YouTube upload session could not be created",
                    retryable=start.status_code >= 500,
                )
            uploaded = self.client.put(
                start.headers["location"],
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": content_type},
                content=media.content,
            )
        except httpx.HTTPError as error:
            raise PublisherError("YouTube transport failed", retryable=True) from error
        if uploaded.status_code >= 400:
            raise PublisherError(
                "YouTube rejected the video", retryable=uploaded.status_code >= 500
            )
        external_id = str(uploaded.json().get("id", ""))
        if not external_id:
            raise PublisherError("YouTube returned no video identifier", retryable=True)
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_id,
            f"https://www.youtube.com/watch?v={external_id}",
            datetime.now(UTC),
            self.platform,
            {"http_status": uploaded.status_code},
        )

    def verify(self, external_post_id: str, *, access_token: str) -> PublishResult:
        try:
            response = self.client.get(
                f"{self.base_url}/youtube/v3/videos",
                params={"part": "id", "id": external_post_id},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.HTTPError as error:
            raise PublisherError("YouTube verification transport failed", retryable=True) from error
        if response.status_code >= 400:
            raise PublisherError(
                "YouTube verification was rejected", retryable=response.status_code >= 500
            )
        items = response.json().get("items", [])
        if not items:
            raise PublisherError("YouTube video was not found during verification")
        return PublishResult(
            PublishStatus.PUBLISHED,
            external_post_id,
            f"https://www.youtube.com/watch?v={external_post_id}",
            datetime.now(UTC),
            self.platform,
            {"verified": True, "http_status": response.status_code},
        )


def _raise_graph_error(response: httpx.Response, provider: str) -> None:
    if response.status_code in {401, 403}:
        raise PublisherError(f"{provider} authorization was rejected", retryable=False)
    if response.status_code == 429 or response.status_code >= 500:
        raise PublisherError(f"{provider} is temporarily unavailable", retryable=True)
    if response.status_code >= 400:
        raise PublisherError(f"{provider} rejected the request", retryable=False)
