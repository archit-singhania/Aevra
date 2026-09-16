# Phases 11–12 audit

Status: complete for the connector and operations foundation.

## Phase 11 — remaining connectors

Built:

- Explicit REST adapters for Instagram, Facebook, Threads, X, and YouTube.
- Shared bounded payloads, authorization handling, retry classification, idempotency keys,
  external IDs, verification, and safe provider metadata.
- Per-platform contract tests using injected HTTP transports, without real credentials or
  network-dependent CI.

Still required for production:

- Platform-specific OAuth scopes and callback/token-refresh flows.
- Platform-specific media upload protocols (for example Instagram containers and YouTube
  resumable uploads).
- App review, rate-limit policy, and live sandbox credentials per provider.

## Phase 12 — scheduling, analytics, observability, hardening, mobile

Built:

- Durable `scheduled_posts` table with future-time validation, idempotency, status, attempts,
  and audit records.
- Normalized `post_metrics` snapshots for impressions, engagements, clicks, likes, comments,
  and shares.
- Tenant-scoped `audit_logs` API for schedule and analytics events.
- Operations API endpoints for schedule, metrics, audit, and mobile read access.
- Mobile contract documentation that keeps credentials and AI providers server-side.
- Migration `20260916_0007_operations.py`.

Still required for production:

- Redis/Celery worker execution for due schedules, exponential backoff, and crash recovery.
- Provider-specific analytics polling and aggregation dashboards.
- OpenTelemetry exporters, structured request IDs, alerting, and retention policies.
- Real OAuth/token-vault implementation and mobile Flutter UI.

## Verification

- API suite: **56 passed**.
- Ruff: clean.
- Mypy: clean across 69 API source files.
- Alembic head: `20260916_0007`.
