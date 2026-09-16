from __future__ import annotations

import uuid
from pathlib import Path

from aevra_api.domain.errors import GenerationError


class LocalMediaStorage:
    """Filesystem storage with UUID-based keys and traversal protection."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def key_for(self, workspace_id: uuid.UUID, asset_id: uuid.UUID, extension: str) -> str:
        clean_extension = extension.removeprefix(".").lower()
        if clean_extension not in {"png", "jpg", "jpeg", "mp4", "json"}:
            raise GenerationError("Unsupported media extension")
        return f"workspaces/{workspace_id}/{asset_id}.{clean_extension}"

    def path_for(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if self.root != candidate and self.root not in candidate.parents:
            raise GenerationError("Unsafe media storage path")
        return candidate

    def write(self, storage_key: str, content: bytes) -> Path:
        path = self.path_for(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def read(self, storage_key: str) -> bytes:
        return self.path_for(storage_key).read_bytes()
