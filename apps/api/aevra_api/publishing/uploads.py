from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class UploadStatus(StrEnum):
    READY = "ready"
    PROCESSING = "processing"
    FAILED = "failed"


@dataclass(frozen=True)
class MediaUploadRequest:
    idempotency_key: str
    account_id: str
    content: bytes
    mime_type: str
    filename: str

    def __post_init__(self) -> None:
        if not self.idempotency_key.strip() or len(self.idempotency_key) > 160:
            raise ValueError("upload idempotency key is invalid")
        if not self.account_id.strip() or not self.content:
            raise ValueError("account_id and content are required")
        if self.mime_type not in {"image/png", "image/jpeg", "image/webp", "video/mp4"}:
            raise ValueError("unsupported media MIME type")


@dataclass(frozen=True)
class MediaUploadResult:
    status: UploadStatus
    external_media_id: str
    provider: str
    sha256: str
    metadata: dict[str, object]


class MediaUploader(Protocol):
    platform: str

    def upload(self, request: MediaUploadRequest, *, access_token: str) -> MediaUploadResult: ...


class DeterministicMediaUploader:
    """Free/local uploader used by tests and offline previews."""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def upload(self, request: MediaUploadRequest, *, access_token: str) -> MediaUploadResult:
        del access_token
        digest = hashlib.sha256(request.content).hexdigest()
        return MediaUploadResult(
            UploadStatus.READY,
            f"{self.platform}_media_{digest[:24]}",
            f"{self.platform}-deterministic",
            digest,
            {"filename": request.filename, "mime_type": request.mime_type},
        )


class LinkedInMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("linkedin")


class InstagramMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("instagram")


class FacebookMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("facebook")


class ThreadsMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("threads")


class XMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("x")


class YouTubeMediaUploader(DeterministicMediaUploader):
    def __init__(self) -> None:
        super().__init__("youtube")
