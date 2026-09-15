# Aevra architecture

## Product boundary

Aevra is a multi-tenant content operating system. A workspace supplies its own brand knowledge; an agent graph produces recommendations and creative artifacts; a human or explicit policy approves them; trusted workers execute schedules and platform calls.

```text
Web / future mobile
        |
        v
FastAPI authorization + policy boundary
        |
        +---------------- Brand/RAG service ---------------- pgvector
        |
        +---------------- LangGraph campaign orchestration -- local model providers
        |
        +---------------- Approval service
        |
        v
Durable job queue -> deterministic publisher adapters -> social platforms
        |
        +---------------- audit log + normalized analytics
```

## Architectural boundaries

| Boundary | Owns | Must not own |
| --- | --- | --- |
| Web | Accessible workflows, server-rendered views, safe public state | OAuth tokens, direct model or social API access |
| API | Authentication, authorization, tenant context, validation, transactions | Long-running generation and publish execution |
| Agents | Typed campaign state, reasoning, tool selection, quality recommendations | Credentials, arbitrary HTTP/database/filesystem access |
| RAG | Ingestion, chunking, embeddings, citations, workspace-filtered retrieval | Cross-workspace queries or unscoped vector search |
| Generation | Replaceable text/image/video providers and media transforms | Publication decisions or credential handling |
| Publishing | Adapter contracts, validation, idempotent execution, verification | Creative reasoning or prompt construction |
| Workers | Durable schedules, retries, backoff, cancellation, attempt history | User authorization policy decisions |
| Analytics | Normalized metrics and evidence-backed insights | Silent modification of brand policy |

## Security invariants

1. The authenticated server derives organization and workspace scope; client-supplied tenant IDs are never trusted alone.
2. Every tenant-owned row carries organization and workspace ownership. Repository methods require tenant context.
3. Vector retrieval filters by workspace before ranking or returning content.
4. OAuth credentials are envelope-encrypted at rest and decrypted only inside the publishing service.
5. Credentials never enter prompts, browser state, logs, analytics, LangGraph checkpoints, or error payloads.
6. Publication uses an idempotency key and a unique destination/content constraint.
7. Security-sensitive state changes and all publication attempts create append-only audit events.

## Campaign control flow

`DRAFT → CONTEXT_RETRIEVAL → PLANNING → CONTENT_GENERATION → MEDIA_GENERATION → PLATFORM_ADAPTATION → VALIDATION → AWAITING_APPROVAL → APPROVED → SCHEDULED → PUBLISHING → PUBLISHED → ANALYZING → COMPLETED`

Exceptional states are `FAILED`, `RETRYING`, and `CANCELLED`. Manual approval is the default. A model may recommend a transition; application policy validates and persists it.

## Deployment shape

The local stack uses PostgreSQL with pgvector, Redis, MinIO, the Next.js web app, and FastAPI. Celery workers, Beat, Ollama, and media services are added only in the phases that exercise them so Phase 0 remains reliable on ordinary developer hardware.

