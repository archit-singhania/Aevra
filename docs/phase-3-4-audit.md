# Phase 3–4 delivery audit

Date: 2026-09-16

## Outcome

Phase 3 and Phase 4 exit gates are green. Aevra can ingest an authorized workspace's
initial knowledge formats, normalize and deduplicate them, create cited chunks and
embeddings, persist production vectors in pgvector, retrieve tenant-filtered evidence,
and call a replaceable local Ollama/Qwen provider through a constrained API boundary.

## Phase 3 — built

- Text, Markdown, website HTML, TXT, HTML, Markdown, and PDF ingestion.
- Unicode/whitespace normalization, unsafe HTML-node removal, text-bearing PDF extraction,
  boundary-aware overlapping chunks, content hashes, and atomic document/chunk writes.
- Workspace and optional brand scoping, product/campaign metadata, source URI attribution,
  excerpt and character-offset citations, metadata filters, configurable score/limit, and
  tenant-local deduplication.
- PostgreSQL `vector(384)` storage and HNSW cosine index with native pgvector ranking.
  SQLite retains a deterministic hashing/vector fallback for tests and lightweight local
  development.
- Role policy: owner/admin/member may ingest; viewers may read and retrieve; outsiders see
  `404`. Composite document/workspace and brand/workspace foreign keys provide a second
  database-level isolation barrier.
- Upload size, supported-extension, UTF-8, empty-document, encrypted-PDF, and PDF page
  protections with safe `415` responses.

## Phase 3 — left for later

- OCR/scanned PDFs, authenticated crawling, sitemap crawling, Office documents, and image
  or audio knowledge are later ingestion enhancements.
- Object-storage originals, asynchronous Celery ingestion, re-index/version jobs, deletion
  APIs, hybrid lexical/vector retrieval, reranking, and retrieval evaluation datasets remain
  production-hardening work.
- The premium knowledge-management UI is not connected yet; current Phase 3 delivery is the
  secured backend/API foundation.

## Phase 4 — built

- Provider-neutral chat, embedding, generation-result, and health contracts.
- Ollama `/api/chat`, `/api/embed`, and `/api/tags` adapters with timeouts, JSON mode,
  usage metadata, model shape validation, and stable failure mapping.
- Configurable Qwen model, embedding model, endpoint, timeout, and deterministic hashing
  provider for repeatable tests.
- Workspace-authorized local-model status and generation endpoints. Authorization is checked
  before generation, preventing a foreign tenant request from reaching the provider.
- Dependency injection allows later llama.cpp, hosted, or specialized local providers without
  rewriting routes or services.

## Phase 4 — left for later

- On this machine Ollama is reachable, but `qwen3:8b` and `nomic-embed-text` are not installed;
  the detected runtime currently exposes `qwen2.5-coder:14b`. Pull the configured models for
  a live Qwen3 smoke test.
- RAG prompt assembly, factual-claim citation retention, structured campaign output,
  streaming, cancellation, token budgets, model warm-up/queueing, and generation telemetry
  belong to Phases 5–6 and production hardening.
- LangChain/LangGraph remain intentionally absent until Phase 5, where they will orchestrate
  persisted campaign state instead of decorating the provider layer.

## Verification evidence

- Ruff: passed.
- mypy: passed for the API package.
- Pytest: 24 passed, including document normalization, PDF ingestion, deduplication,
  metadata-filtered citations, API isolation, database isolation, model authorization,
  mocked Ollama status/chat/embed, and malformed-provider handling.
- Alembic: full SQLite upgrade → downgrade → upgrade passed.
- PostgreSQL offline DDL compilation confirmed the vector extension, `vector(384)`, and HNSW
  cosine index.
- Frontend/type quality remains part of the final repository-wide check.

## Next gate

Phase 5 should add campaign persistence, explicit lifecycle transitions, durable LangGraph
checkpoints, Brand Brain retrieval nodes, deterministic approval boundaries, and graph tests
for success, regeneration, rejection, retry, cancellation, and resume behavior.
