# Dependency decisions

## Phase 0 runtime

- **Next.js + React + TypeScript:** responsive web workspace and server rendering.
- **Tailwind CSS:** token-led styling with a small reusable UI primitive layer.
- **Radix Slot + class-variance-authority:** composable shadcn-style primitives without inaccessible ad-hoc controls.
- **Lucide:** consistent interface iconography.
- **Biome:** fast formatting and static checks for the frontend.
- **FastAPI + Pydantic:** typed API boundary and generated OpenAPI contracts.
- **PostgreSQL/pgvector, Redis, MinIO:** local infrastructure declared now and integrated in later phases.

## Phase 1–4 runtime additions

- **SQLAlchemy + Alembic + psycopg:** typed persistence and reversible schema evolution.
- **pgvector:** vector columns, cosine operations, and a PostgreSQL HNSW index.
- **Beautiful Soup + markdown-it-py + pypdf:** safe initial normalization for website
  HTML, Markdown, and text-bearing PDFs.
- **HTTPX:** replaceable Ollama embedding and chat transports with bounded timeouts.
- **python-multipart:** streamed FastAPI file-upload parsing.
- **LangGraph:** typed campaign graph execution. Aevra persists application checkpoints in
  its own tenant-scoped run/step tables so authorization and audit history remain explicit.

## Deferred intentionally

Celery, FFmpeg bindings, image-generation runtimes,
OpenTelemetry, and social SDKs are introduced in the first phase that uses them. The Phase
4 Ollama integration uses its stable HTTP boundary instead of coupling core code to a
vendor SDK.

## Provider policy

Core AI capabilities target local, swappable providers. No commercial model API is required for the core workflow. Platform APIs can still impose their own access, review, quota, or billing constraints.
