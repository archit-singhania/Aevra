# API contract policy

- Public HTTP APIs are versioned under `/api/v1` beginning in Phase 1.
- Pydantic models define request/response boundaries and publish OpenAPI.
- Domain models do not accept authorization scope from request bodies.
- Mutating endpoints accept idempotency keys where retries could duplicate work.
- Errors use stable machine codes plus safe human-readable messages; secrets and internal prompts are redacted.
- Events are versioned separately from HTTP schemas and remain backward-readable by workers during rolling upgrades.

The Phase 0 `/health` endpoint is intentionally unversioned and contains no dependency or secret details.

## Implemented endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Atomically create a user, organization, owner membership, workspace, and access token |
| POST | `/api/v1/auth/login` | Verify the Argon2 password hash and issue a short-lived bearer token |
| GET | `/api/v1/auth/me` | Read the authenticated user |
| GET | `/api/v1/workspaces` | List only workspaces visible through organization membership |
| GET | `/api/v1/workspaces/{workspace_id}` | Read one authorized workspace without leaking foreign resource existence |
| POST | `/api/v1/organizations/{organization_id}/workspaces` | Create a workspace as an owner or administrator |
| GET/POST | `/api/v1/workspaces/{workspace_id}/brands` | List or create tenant-scoped brand profiles |
| GET/PATCH | `/api/v1/workspaces/{workspace_id}/brands/{brand_id}` | Read or update an authorized brand |
| GET/POST | `/api/v1/workspaces/{workspace_id}/brands/{brand_id}/rules` | List or create prioritized brand rules |
| POST | `/api/v1/workspaces/{workspace_id}/knowledge/documents` | Normalize, chunk, embed, and store text, Markdown, or website text |
| POST | `/api/v1/workspaces/{workspace_id}/knowledge/documents/upload` | Ingest validated TXT, Markdown, HTML, or PDF content |
| GET | `/api/v1/workspaces/{workspace_id}/knowledge/documents` | List authorized knowledge sources without returning full source content |
| POST | `/api/v1/workspaces/{workspace_id}/knowledge/search` | Retrieve workspace-filtered excerpts with document, URI, score, and offset citations |
| GET | `/api/v1/workspaces/{workspace_id}/models/local/status` | Report availability of the configured local model |
| POST | `/api/v1/workspaces/{workspace_id}/models/local/generate` | Run a bounded, authorized local generation request |

Knowledge mutations require owner, administrator, or member access. Viewers may list and
retrieve. Foreign workspace access returns `404`, so resource existence is not disclosed.
Provider transport errors use the stable `provider_unavailable` code and HTTP `503`.
