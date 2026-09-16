# GCP free-tier staging

This profile is intentionally small: one Compute Engine VM, SQLite, local media storage, Docker
Compose, and Caddy-managed HTTPS. It is suitable for a private staging/demo environment, not
production. GCP billing must still be enabled even when usage remains inside the free allowance.

## VM shape

Use an always-free eligible `e2-micro` in an eligible US region. It is resource constrained, so
the profile does not start PostgreSQL, Redis, MinIO, Ollama, or Celery. Those services remain
available through the main Compose stack for a larger staging or production VM.

## First boot

1. Create `/opt/aevra/.env.staging` from `.env.example`.
2. Set `AEVRA_ENV=staging`, a new `AEVRA_SECRET_KEY`, and
   `AEVRA_DATABASE_URL=sqlite:////app/data/aevra.db`.
3. Set `AEVRA_MEDIA_ROOT=/app/data/media` and `NEXT_PUBLIC_API_URL=https://stage.aevra.com`.
4. Copy this repository to `/opt/aevra`.
5. Run `bash infrastructure/gcp/startup.sh`.
6. Run `docker compose --env-file .env.staging -f infrastructure/gcp/staging-compose.yml run --rm api python -m aevra_api.seed`.

## DNS and firewall

Reserve a static external IP, create an A record for `stage.aevra.com`, and allow TCP 80/443 in
the VM firewall. Caddy obtains and renews the certificate after DNS resolves.
