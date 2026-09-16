# Aevra

Aevra is a self-hostable agentic content intelligence and publishing platform. It grounds campaign work in a workspace-specific Brand Brain, creates platform-native variants, routes them through approval, and hands approved actions to deterministic publishing workers.

> Current milestone: **Phases 0–12 complete.** Aevra now includes authenticated tenant
> boundaries, a cited Brand Brain, local Qwen/Ollama providers, durable campaign state,
> LangGraph orchestration, platform-native content variants, quality validation, revision
> history, a human approval boundary, deterministic branded image variants, safe FFmpeg
> video compositions, idempotent publishing jobs, multi-platform connector boundaries,
> scheduling, metrics capture, audit logs, and a stable mobile API contract.

## Quick start

### Web workspace

```bash
pnpm install
pnpm dev:web
```

Open `http://localhost:3000`.

### Local infrastructure

```bash
cp .env.example .env
docker compose up --build
```

The web app runs on `http://localhost:3000`; the API health endpoint is `http://localhost:8000/health`.

Initialize the development data once the stack is healthy:

```bash
docker compose --profile tools run --rm seed
```

For an API-only local workflow:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e "./apps/api[dev]"
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m aevra_api.seed
.venv/Scripts/python -m uvicorn aevra_api.main:app --reload --app-dir apps/api
```

Install the local models before selecting the Ollama embedding provider:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

The development/test default uses deterministic hashing embeddings and needs no model
download. Docker reads Ollama on `host.docker.internal:11434` from `.env`.

## Phase 3–4 API

- `POST /api/v1/workspaces/{workspace_id}/knowledge/documents` ingests text, Markdown,
  or extracted website HTML.
- `POST /api/v1/workspaces/{workspace_id}/knowledge/documents/upload` accepts TXT,
  Markdown, HTML, and PDF files.
- `POST /api/v1/workspaces/{workspace_id}/knowledge/search` returns ranked excerpts with
  source and offset citations.
- `GET /api/v1/workspaces/{workspace_id}/models/local/status` checks the configured local
  model without exposing infrastructure details.
- `POST /api/v1/workspaces/{workspace_id}/models/local/generate` sends a constrained,
  workspace-authorized generation request through the provider abstraction.

## Phase 5–6 API

- `POST /api/v1/workspaces/{workspace_id}/campaigns` creates a tenant-scoped campaign brief.
- `POST /api/v1/workspaces/{workspace_id}/campaigns/{campaign_id}/generate` runs the
  retrieval, planning, generation, adaptation, validation, and approval-boundary graph.
- `POST /api/v1/workspaces/{workspace_id}/campaigns/{campaign_id}/decision` approves or
  rejects the current immutable revision.
- `GET /api/v1/workspaces/{workspace_id}/campaigns/{campaign_id}/variants` returns complete
  platform and revision history with citations and quality findings.

## Phase 7–8 media API

- `POST /api/v1/workspaces/{workspace_id}/media/images/generate` creates a deterministic,
  auditable source image plus tenant-scoped platform crops with optional brand treatment.
- `POST /api/v1/workspaces/{workspace_id}/media/videos/compose` renders 9:16, 1:1, and
  16:9 campaign videos from approved image assets. FFmpeg is used when available; the
  deterministic manifest mode keeps local previews and CI reproducible.
- `GET /api/v1/workspaces/{workspace_id}/media/assets` lists scoped media assets and
  `GET .../assets/{asset_id}/download` streams an authorized artifact.

## Phase 9–10 publishing API

- `POST /api/v1/workspaces/{workspace_id}/publishing/accounts` registers a connected
  platform account using a token reference; raw credentials are not returned to clients.
- `POST /api/v1/workspaces/{workspace_id}/publishing/jobs` creates an idempotent publish
  job. LinkedIn uses the REST adapter; other platforms use the deterministic mock until
  their connector phases are delivered.
- `POST /api/v1/workspaces/{workspace_id}/publishing/jobs/{job_id}/verify` verifies the
  external post and records the result.

## Phase 11–12 operations API

- The remaining platform adapters share the same safe REST publisher contract for Instagram,
  Facebook, Threads, X, and YouTube.
- `POST /api/v1/workspaces/{workspace_id}/operations/schedule` creates an idempotent,
  tenant-scoped scheduled post.
- `GET /api/v1/workspaces/{workspace_id}/operations/metrics` returns captured performance
  snapshots, while `POST .../metrics` records normalized impressions and engagement metrics.
- `GET /api/v1/workspaces/{workspace_id}/operations/audit` exposes a tenant-scoped audit trail.

## Remaining production foundations

The free/local foundations for OAuth vaulting, media uploads, Celery/Redis workers, normalized
analytics, request observability, Flutter, optional FLUX HTTP generation, advanced storyboard
subtitles, and MinIO/S3 storage are now included. See
[docs/remaining-9-areas-audit.md](docs/remaining-9-areas-audit.md) for the implementation and
the exact provider/deployment handoff still required.

## Quality checks

```bash
pnpm check
.venv/Scripts/python -m ruff check apps/api infrastructure/migrations
.venv/Scripts/python -m mypy apps/api/aevra_api
.venv/Scripts/python -m pytest apps/api/tests -q
```

## Repository map

```text
apps/
  web/                  Next.js product workspace
  api/                  FastAPI edge/API boundary
  mobile/               Flutter boundary (Phase 12)
services/
  agents/               LangGraph orchestration
  rag/                  Tenant-safe ingestion and retrieval
  generation/           Text, image, and video providers
  publishing/           Deterministic publisher adapters
  analytics/            Normalized metrics and insights
  workers/              Celery jobs and schedules
packages/
  shared/               Cross-runtime constants and contracts
  schemas/              Versioned API/event schemas
infrastructure/
  docker/               Application container definitions
  migrations/           Database migrations (Phase 1+)
tests/
  unit/ integration/ e2e/
docs/                   Architecture and delivery records
```

Read [docs/architecture.md](docs/architecture.md) for system boundaries,
[docs/roadmap.md](docs/roadmap.md) for the phased plan, and
[docs/phase-5-6-audit.md](docs/phase-5-6-audit.md) for the current delivery audit.
