"""Copy local Aevra media keys to an S3-compatible bucket.

The script is deliberately idempotent: it uses the local relative path as the
object key and skips an object when its size and SHA-256 metadata already
match. Run it once while the API is paused, then switch
``AEVRA_STORAGE_BACKEND`` to ``s3``/``minio`` and keep the same media root
layout. It never deletes local files.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.getenv("AEVRA_MEDIA_ROOT", "./media"))
    parser.add_argument("--endpoint", default=os.getenv("AEVRA_MINIO_ENDPOINT", "localhost:9000"))
    parser.add_argument("--access-key", default=os.getenv("AEVRA_MINIO_ACCESS_KEY"))
    parser.add_argument("--secret-key", default=os.getenv("AEVRA_MINIO_SECRET_KEY"))
    parser.add_argument("--bucket", default=os.getenv("AEVRA_MINIO_BUCKET", "aevra-assets"))
    parser.add_argument("--secure", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.access_key or not args.secret_key:
        parser.error("set --access-key/--secret-key or the corresponding AEVRA_MINIO_* variables")
    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError as error:  # pragma: no cover - operational script
        raise SystemExit("Install the API dependencies first: pip install minio") from error

    client = Minio(args.endpoint, access_key=args.access_key, secret_key=args.secret_key, secure=args.secure)
    if not args.dry_run and not client.bucket_exists(args.bucket):
        client.make_bucket(args.bucket)
    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"media root does not exist: {root}")
    copied = skipped = failed = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        key = path.relative_to(root).as_posix()
        digest = sha256(path)
        try:
            existing = client.stat_object(args.bucket, key)
            metadata = {str(k).lower(): str(v) for k, v in (existing.metadata or {}).items()}
            if existing.size == path.stat().st_size and metadata.get("x-amz-meta-sha256") == digest:
                skipped += 1
                continue
        except S3Error:
            pass
        if args.dry_run:
            print(f"would upload {key} ({path.stat().st_size} bytes)")
            copied += 1
            continue
        try:
            import mimetypes

            with path.open("rb") as handle:
                client.put_object(
                    args.bucket,
                    key,
                    handle,
                    length=path.stat().st_size,
                    content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    metadata={"X-Amz-Meta-Sha256": digest},
                )
            copied += 1
            print(f"uploaded {key}")
        except Exception as error:  # pragma: no cover - operational script
            failed += 1
            print(f"failed {key}: {error}")
    print(f"completed copied={copied} skipped={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
