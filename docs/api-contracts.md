# API contract policy

- Public HTTP APIs are versioned under `/api/v1` beginning in Phase 1.
- Pydantic models define request/response boundaries and publish OpenAPI.
- Domain models do not accept authorization scope from request bodies.
- Mutating endpoints accept idempotency keys where retries could duplicate work.
- Errors use stable machine codes plus safe human-readable messages; secrets and internal prompts are redacted.
- Events are versioned separately from HTTP schemas and remain backward-readable by workers during rolling upgrades.

The Phase 0 `/health` endpoint is intentionally unversioned and contains no dependency or secret details.

