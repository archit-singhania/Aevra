# Remaining nine areas — implementation audit

> Status refreshed 18 September 2026. The integrated hardening pass is tracked in
> [production-readiness.md](production-readiness.md); this file preserves the original phase-by-phase notes.

The nine production extensions now have free/self-hosted foundations. External platform
approval, credentials, hosted GPU time, and electricity are not software features and remain
deployment responsibilities.

## 1. OAuth and token vault

Implemented `LocalTokenVault` with authenticated encrypted envelopes and tamper detection.
Implemented the signed, workspace-bound authorize/callback foundation for Meta, Threads,
LinkedIn, and YouTube. Production handoff: replace the master-key provider with Vault/KMS transit,
add one-time state replay protection, and implement provider-specific refresh/revoke rotation.

## 2. Media upload workflows

Implemented bounded upload contracts and deterministic local uploaders for all six platforms.
Production handoff: replace each uploader with that provider's container/resumable-upload API,
persist upload jobs, and poll processing states before post creation.

## 3. Redis/Celery workers

Implemented lazy Celery factory, Redis configuration, beat schedules, and retry/backoff/jitter
task declarations. The API remains runnable without Celery installed. Production handoff: wire
task bodies to the database claim/lock service and run dedicated worker/beat containers.

## 4. Analytics pipeline

Implemented normalized metric snapshots and engagement-rate calculation. Production handoff:
add platform analytics adapters, polling tasks, retention rules, and dashboard aggregation.

## 5. OpenTelemetry and alerting

Implemented request IDs, server timing, and in-process request/failure counters. Production
handoff: export OTLP traces/metrics to a self-hosted Collector, Grafana, Prometheus, and Jaeger,
then add redaction and alert rules.

## 6. Flutter mobile

Implemented a dependency-light Flutter shell with overview, campaigns, schedule, and analytics
surfaces. It consumes the existing API contract and keeps credentials server-side. Production
handoff: typed API client, auth/session storage, push notifications, offline cache, and approval
workflows.

## 7. FLUX provider

Implemented an optional HTTP FLUX-compatible provider selected by `AEVRA_IMAGE_PROVIDER=flux`;
the deterministic renderer remains the free default. Production handoff: run a local GPU model
server, add queueing, model caching, moderation, and GPU capacity limits.

## 8. Advanced video

Implemented bounded storyboards, motion presets, WebVTT subtitle generation, and explicit music
license validation. Production handoff: connect these assets to FFmpeg scene graphs, local TTS,
licensed music, and asynchronous render jobs.

## 9. MinIO/S3 storage

Implemented an `ObjectStorage` protocol, in-memory free test backend, and lazy MinIO S3-compatible
adapter with signed URLs. Production handoff: migrate existing local assets by checksum, enable
versioning/lifecycle rules, and switch media services to the object-storage backend.

## Verification

- API suite: **62 passed**.
- Ruff: clean.
- Mypy: clean across 79 API source files.
- Web typecheck, Biome, and production build pass; Flutter remains unverified when the SDK is not installed on the host.
