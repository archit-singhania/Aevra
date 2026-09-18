# VAE production runbook

This runbook separates deployable code from approvals and infrastructure that
cannot be completed from the repository.

## API deployment

Apply migrations before starting the API:

```sh
alembic upgrade head
uvicorn aevra_api.main:app --host 0.0.0.0 --port 10000
```

For Render, use the API Docker image and set `AEVRA_DATABASE_URL` to the
internal PostgreSQL URL. Keep `AEVRA_ENABLE_CELERY=0` when no worker service is
available. The API still supports manual publishing and all request paths.

## OAuth secrets

Set provider client IDs and secrets only on the API service. Set
`AEVRA_OAUTH_REDIRECT_BASE_URL` to the public API origin and
`AEVRA_OAUTH_FRONTEND_URL` to the public web origin. The callback path is
`/api/v1/oauth/{provider}/callback`. Never expose provider secrets or vault
keys to Vercel/browser variables.

## Workers

When a persistent worker host is available, set `AEVRA_ENABLE_CELERY=1` and
run:

```sh
celery -A services.workers.celery_app:celery_app worker --loglevel=INFO --concurrency=1
celery -A services.workers.celery_app:celery_app beat --loglevel=INFO
```

The schedule dispatches due posts, polls provider analytics, and executes
account deletions after the grace period. Failed network requests are retried
with bounded exponential backoff.

## Persistent media

Pause writes, preview the migration, then copy local media to the S3-compatible
bucket without deleting the source:

```sh
python infrastructure/scripts/migrate-media-to-s3.py --dry-run
python infrastructure/scripts/migrate-media-to-s3.py
```

Set `AEVRA_STORAGE_BACKEND=minio` (or `s3`), the endpoint, credentials, and
bucket on the API. Verify an asset download after restarting the container.

## Backups and restore checks

Run `backup-postgres.ps1`/`.sh` on a schedule outside the web container. Test
each backup against a disposable PostgreSQL database with
`restore-postgres.ps1`/`.sh`; do not point the restore command at production.

## Monitoring

The API exposes `/health` (liveness), `/ready` (database/Redis readiness), and
Prometheus text at `/metrics`. Configure external uptime checks for `/health`
and `/ready`, scrape `/metrics` from a protected network, and alert on HTTP
5xx, Redis failures, failed worker tasks, and backup age. The repository does
not contain credentials for a hosted monitoring vendor, so exporter URLs and
alert destinations remain deployment settings.

## Launch gate

Before enabling public publishing, complete provider App Review, run one real
test post per approved provider, verify token refresh/revoke, test a worker
restart, restore a backup, and replace the staging legal copy with reviewed
privacy, terms, cookie, retention, export, and deletion policies.
