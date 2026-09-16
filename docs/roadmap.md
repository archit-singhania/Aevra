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
| 7 ✅ | Local image generation | Passed: deterministic provider, branded transforms, lineage, and asset API |
| 8 ✅ | FFmpeg video composer | Passed: 9:16, 1:1, and 16:9 render contracts and safe fallback |
| 9 ✅ | SocialPublisher abstraction and mocks | Passed: failure matrix and idempotency tests |
| 10 ✅ | First real connector | Passed: LinkedIn REST publish/verify adapter boundary |
| 11 ✅ | Remaining approved connectors | Passed: explicit REST adapter contracts for Instagram, Facebook, Threads, X, YouTube |
| 12 ✅ | Scheduling, analytics, observability, hardening, mobile | Passed: durable schedule/metrics/audit APIs and mobile contract |

Phase 7 is the next implementation boundary. No later phase starts until its exit gate is green.
