# Aevra

Aevra is a self-hostable agentic content intelligence and publishing platform. It grounds campaign work in a workspace-specific Brand Brain, creates platform-native variants, routes them through approval, and hands approved actions to deterministic publishing workers.

> Current milestone: **Phases 0–8 complete.** Aevra now includes authenticated tenant
> boundaries, a cited Brand Brain, local Qwen/Ollama providers, durable campaign state,
> LangGraph orchestration, platform-native content variants, quality validation, revision
> history, a human approval boundary, deterministic branded image variants, and safe
> FFmpeg video compositions.

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
