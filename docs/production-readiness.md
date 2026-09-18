# VAE production-readiness audit

Updated 18 September 2026 after the UI, OAuth-boundary, and quality-gate pass.

## Implemented in the codebase

- Browser authentication now uses an HTTP-only, SameSite session cookie. Legacy browser tokens are removed on hydration; native mobile clients can continue to use bearer tokens.
- Provider credentials are encrypted with the vault envelope before they are persisted. The `AEVRA_TOKEN_VAULT_KEY` setting supports a separate 32-byte-plus master key.
- Auth burst protection, request IDs, server timing, security headers, and a dependency-free Prometheus `/metrics` endpoint are active in staging/production.
- Celery/Redis worker and beat services are defined in Compose. Due scheduled posts are claimed idempotently, published through the existing provider contract, and retried by Celery.
- Media generation now selects local storage or an S3-compatible MinIO adapter from `AEVRA_STORAGE_BACKEND`; buckets are created on first connection and downloads remain tenant-scoped.
- Ollama has a real `/models/local/generate/stream` Server-Sent Events endpoint. The web brief also supports browser-native voice capture without uploading audio to VAE.
- Mobile now has an accessible light/dark theme switch with matching contrast tokens.
- Privacy, terms, and account-deletion pages are available in the web app. The API records a confirmed account-deletion request with a 30-day grace period and migration.
- Signed, workspace-bound OAuth authorize/callback routes now cover Facebook, Instagram, Threads, LinkedIn, and YouTube. Returned provider tokens are exchanged server-side and encrypted by the existing vault boundary; no provider token is returned to the browser. Callback allowlists use the stable `/api/v1/oauth/{provider}/callback` path.
- The overview now renders a useful first-run state when collections are empty, secondary API failures degrade per-panel, and the dashboard scrolls in its own content region. Dark/light tokens, motion preferences, chart accessibility labels, and the codec-free hero visual are applied consistently.
- CI-local gates are green: web typecheck, web Biome, Ruff, mypy, and **62 API tests**.

## Still requires your deployment or provider decisions

- Create/register LinkedIn, Instagram, Threads, X, Facebook, and YouTube apps; provide client IDs/secrets, redirect URLs, scopes, and complete each platform's review. The provider adapters and encrypted storage boundary are ready, but approval cannot be automated in this repository.
- Set `AEVRA_TOKEN_VAULT_KEY`, `AEVRA_SECRET_KEY`, database/Redis URLs, and S3-compatible endpoint credentials in Render/Vercel. Use `AEVRA_STORAGE_BACKEND=minio` or `s3` only after persistent object storage is available.
- Run a persistent Celery worker and beat process. Render free web services can host the API but are not a durable worker/queue SLA.
- Select a paid/persistent PostgreSQL and object-storage plan for real production, then configure retention, versioning, backup, restore drills, and billing alerts.
- Point the custom domain/DNS at Vercel, configure the API origin/rewrite, and verify HTTPS cookie behavior on the final domain.
- Have counsel replace the staging privacy/terms copy, publish a monitored support address, and document retention, subprocessors, data export, and deletion policy.

## Remaining engineering before a production launch

- Add provider-specific token refresh/revoke flows and one-time state replay protection, then add automated contract tests against each approved sandbox. The authorization/callback foundation is now in the codebase.
- Add real platform analytics adapters and polling tasks; the normalized metric model and dashboard endpoints are ready, but live metrics require platform credentials and permissions.
- Export traces/metrics to an OpenTelemetry Collector/Grafana/alert destination. `/metrics` and request instrumentation are the local boundary; an external exporter is still needed.
- Connect the web campaign generation UI to the SSE endpoint (the backend stream is ready); keep the existing visual typewriter as the fallback for deterministic staging.
- Complete server-side speech/TTS workflows, GPU FLUX capacity controls, advanced motion/caption/voiceover/music providers, and moderation policies.
- Finish persistent-media migration tooling, account-deletion execution/restore jobs, rate limiting backed by Redis, CSRF/origin policy for custom cross-site deployments, and signed iOS/Android release assets.

## Your remaining checklist

1. Add the production secrets and persistent service URLs in Render/Vercel.
2. Deploy the API, web app, and dedicated worker/beat processes; run `alembic upgrade head` once against the production database.
3. Configure the custom domain and validate login, logout, asset download, SSE generation, scheduling, and deletion-request flows over HTTPS.
4. Register the platform apps, set the exact callback URLs, and add the client IDs/secrets to Render; app review and provider approval remain external.
5. Turn on backups, restore testing, monitoring/alerts, billing limits, and reviewed legal pages.
