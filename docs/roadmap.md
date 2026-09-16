# Delivery roadmap

| Phase | Scope | Exit gate |
| --- | --- | --- |
| 0 ✅ | Monorepo, product shell, quality tooling, Docker, architecture docs | Passed |
| 1 ✅ | PostgreSQL, migrations, users, organizations, workspaces | Passed: auth and tenant lifecycle tests |
| 2 ✅ | Brand profiles, rules, role permissions, and tenant isolation | Passed: cross-tenant API, repository, and database denial tests |
| 3 ✅ | Ingestion, embeddings, pgvector, cited RAG | Passed: format, citation, filter, isolation, and vector DDL tests |
| 4 ✅ | Local model provider and Qwen/Ollama | Passed: provider contract, mock transport, failure, and authorization tests |
| 5 ✅ | Campaign models and LangGraph orchestration | Passed: lifecycle, checkpoint, approval, failure, revision, and tenant tests |
| 6 ✅ | Platform-native text variants | Passed: citation grounding, JSON contract, quality, and platform adaptation tests |
| 7 | Local image generation | Asset pipeline and resize/crop tests pass |
| 8 | FFmpeg video composer | 9:16, 1:1, and 16:9 render tests pass |
| 9 | SocialPublisher abstraction and mocks | Failure matrix and idempotency tests pass |
| 10 | First real connector | Sandbox end-to-end publish/verify succeeds |
| 11 | Remaining approved connectors | Per-platform contract and smoke tests pass |
| 12 | Scheduling, analytics, observability, hardening, mobile | Production and recovery checklist passes |

Phase 7 is the next implementation boundary. No later phase starts until its exit gate is green.
