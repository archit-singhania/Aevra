# Aevra

Aevra is a self-hostable agentic content intelligence and publishing platform. It grounds campaign work in a workspace-specific Brand Brain, creates platform-native variants, routes them through approval, and hands approved actions to deterministic publishing workers.

> Current milestone: **Phases 0–2 complete.** Authentication, tenant persistence, workspaces, brand profiles, and brand rules are implemented. The dashboard still uses representative content until later campaign phases connect it to generated assets.

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

Read [docs/architecture.md](docs/architecture.md) for system boundaries, [docs/roadmap.md](docs/roadmap.md) for the phased plan, and [docs/phase-1-2-audit.md](docs/phase-1-2-audit.md) for the current delivery audit.
