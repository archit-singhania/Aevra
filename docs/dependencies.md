# Dependency decisions

## Phase 0 runtime

- **Next.js + React + TypeScript:** responsive web workspace and server rendering.
- **Tailwind CSS:** token-led styling with a small reusable UI primitive layer.
- **Radix Slot + class-variance-authority:** composable shadcn-style primitives without inaccessible ad-hoc controls.
- **Lucide:** consistent interface iconography.
- **Biome:** fast formatting and static checks for the frontend.
- **FastAPI + Pydantic:** typed API boundary and generated OpenAPI contracts.
- **PostgreSQL/pgvector, Redis, MinIO:** local infrastructure declared now and integrated in later phases.

## Deferred intentionally

SQLAlchemy, Alembic, auth/password libraries, LangChain, LangGraph, Ollama clients, embedding models, Celery, Pillow, FFmpeg bindings, OpenTelemetry, and social SDKs are introduced in the first phase that uses them. This limits supply-chain surface and avoids decorative dependencies.

## Provider policy

Core AI capabilities target local, swappable providers. No commercial model API is required for the core workflow. Platform APIs can still impose their own access, review, quota, or billing constraints.

