from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol


class ObjectStorage(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def signed_url(self, key: str, expires_seconds: int = 900) -> str: ...


@dataclass
class InMemoryObjectStorage:
    objects: dict[str, tuple[bytes, str]]

    def __init__(self) -> None:
        self.objects = {}

    def put(self, key: str, content: bytes, content_type: str) -> None:
        self.objects[key] = (content, content_type)

    def get(self, key: str) -> bytes:
        return self.objects[key][0]

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)

    def signed_url(self, key: str, expires_seconds: int = 900) -> str:
        del expires_seconds
        return f"memory://{key}"


class MinioObjectStorage:
    """S3-compatible adapter with lazy SDK import for the free local profile."""

    def __init__(
        self, endpoint: str, access_key: str, secret_key: str, bucket: str, secure: bool = False
    ) -> None:
        try:
            from minio import Minio  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("Install the minio package to enable object storage") from error
        self.bucket = bucket
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        from minio.error import S3Error  # type: ignore[import-not-found]

        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except S3Error as error:
            raise RuntimeError(f"Unable to initialise object-storage bucket '{bucket}'") from error

    def put(self, key: str, content: bytes, content_type: str) -> None:
        from io import BytesIO

        self.client.put_object(
            self.bucket, key, BytesIO(content), len(content), content_type=content_type
        )

    def get(self, key: str) -> bytes:
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def signed_url(self, key: str, expires_seconds: int = 900) -> str:
        return self.client.presigned_get_object(
            self.bucket, key, expires=timedelta(seconds=expires_seconds)
        )


def build_object_storage(settings) -> ObjectStorage:
    if str(settings.storage_backend).lower() in {"minio", "s3", "s3-compatible"}:
        return MinioObjectStorage(
            settings.minio_endpoint,
            settings.minio_access_key,
            settings.minio_secret_key,
            settings.minio_bucket,
            settings.minio_secure,
        )
    return InMemoryObjectStorage()
