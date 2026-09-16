# Phase 5–6 delivery audit

Date: 2026-09-16

## Outcome

Phase 5 and Phase 6 exit gates are green. Aevra now turns a tenant-authorized campaign brief
and Brand Brain evidence into a persisted campaign plan and distinct, reviewable social
variants through a real LangGraph workflow. Every run stops at an explicit human approval
boundary and regeneration creates a new revision without mutating previously approved work.

## Phase 5 — built

- Workspace/brand-scoped campaigns with goal, product, audience, instructions, platforms,
  media types, start time, and manual/assisted/autonomous policy metadata.
- Typed LangGraph nodes for context retrieval, planning, content generation, platform
  adaptation, quality validation, and approval.
- Durable campaign runs and ordered node checkpoints with safe state snapshots, input digests,
  citations, duration, provider/model metadata, and failure records.
- Explicit lifecycle guards, `404` tenant non-disclosure, editor role enforcement, immutable
  revision history, rejection feedback, and manual approval as the default.
- Cross-workspace composite foreign keys for campaigns, runs, steps, and content variants.

## Phase 5 — left

- Celery/background graph execution, cancellation during an active node, retry/backoff,
  websocket progress, and native PostgreSQL LangGraph checkpoint adapters are deferred to the
  worker and hardening phases.
- Assisted/autonomous modes are stored but still stop at human approval until a workspace
  policy engine and audit controls are implemented.
- Scheduling, publishing, media generation, and social credentials remain outside the graph.

## Phase 6 — built

- One strict grounded JSON generation contract for a master campaign plan and every requested
  platform variant.
- LinkedIn, Instagram, Threads, X, Facebook, and YouTube rules with distinct caption/title and
  hashtag constraints; overlong copy is safely truncated at word boundaries.
- Brand profile, prioritized rules, revision feedback, and cited Brand Brain excerpts are
  assembled into the model request without exposing credentials or unrestricted tools.
- Variants retain document/chunk citations, model and token metadata, quality scores, and
  actionable validation issues.
- Deterministic checks cover missing evidence, CTA presence, Instagram hashtag suitability,
  prohibited quoted phrases, missing/duplicate platforms, malformed JSON, and required
  YouTube titles.
- Premium variant-review UI with platform switching, quality indicators, evidence visibility,
  responsive layout, revision approval, and regeneration affordance. It remains representative
  until frontend authentication/session wiring is implemented.

## Phase 6 — left

- Live frontend API binding, per-claim inline citation spans, language/localization variants,
  A/B experiments, richer compliance classifiers, and offline evaluation datasets.
- Image and video prompts are intentionally deferred to Phases 7–8.
- A live Qwen3 campaign smoke test still requires the configured `qwen3:8b` and embedding model
  to be installed in the available Ollama runtime.

## Verification evidence

- Ruff and mypy passed across the expanded API.
- Pytest: 30 passed, including graph topology/order, durable snapshots, cited variants,
  platform limits, approval, rejection, regeneration, immutable approved revisions, malformed
  model failure, cross-tenant API denial, and database constraint denial.
- Alembic: complete SQLite upgrade → downgrade → upgrade passed through migration `0004`.
- PostgreSQL offline DDL compilation confirmed campaign, run, step, and variant tables.
- Frontend lint, TypeScript, and production build are included in the final repository check.

## Next gate

Phase 7 should introduce a local image-generation abstraction, job and asset persistence,
prompt provenance, deterministic branding transforms, safe overlays, storage integration,
platform aspect-ratio variants, and mock-provider tests before requiring a large FLUX model.
