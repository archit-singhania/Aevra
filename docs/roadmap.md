# Delivery roadmap

| Phase | Scope | Exit gate |
| --- | --- | --- |
| 0 | Monorepo, product shell, quality tooling, Docker, architecture docs | Web build and static checks pass; API imports; Compose validates |
| 1 | PostgreSQL, migrations, users, organizations, workspaces | Tenant lifecycle integration tests pass |
| 2 | Brand profiles and tenant isolation | Cross-tenant denial tests pass |
| 3 | Ingestion, embeddings, pgvector, cited RAG | Retrieval isolation and citation tests pass |
| 4 | Local model provider and Qwen/Ollama | Provider contract and offline smoke tests pass |
| 5 | Campaign models and LangGraph orchestration | State transition and checkpoint tests pass |
| 6 | Platform-native text variants | Grounding, quality, and adaptation evals pass |
| 7 | Local image generation | Asset pipeline and resize/crop tests pass |
| 8 | FFmpeg video composer | 9:16, 1:1, and 16:9 render tests pass |
| 9 | SocialPublisher abstraction and mocks | Failure matrix and idempotency tests pass |
| 10 | First real connector | Sandbox end-to-end publish/verify succeeds |
| 11 | Remaining approved connectors | Per-platform contract and smoke tests pass |
| 12 | Scheduling, analytics, observability, hardening, mobile | Production and recovery checklist passes |

No later phase starts until the current phase's exit gate is green.

