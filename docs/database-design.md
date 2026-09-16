# Database design principles

The Phase 1–4 data model separates identity, tenancy, brand policy, and knowledge while
preserving transactional boundaries. Later migrations add campaign, publishing, and
analytics domains without weakening these ownership keys.

Every tenant-owned table will include `organization_id` and `workspace_id` where applicable. Authorization is enforced in both services and repositories, backed by database constraints and row-level security where practical. OAuth material is stored separately from ordinary social account metadata. Vector chunks retain source document identity and tenant keys. Publish attempts retain idempotency keys, external IDs, retry state, and audit references.

## Current tables

- `users`: normalized unique identity, Argon2 password hash, active state, login time.
- `organizations`: top-level tenant with globally unique slug.
- `organization_members`: unique user/organization membership and constrained role.
- `workspaces`: organization-owned boundary with tenant-local slug uniqueness.
- `brand_profiles`: workspace-owned voice, audience, CTA, hashtag, and positioning data.
- `brand_rules`: prioritized policy records with a composite foreign key to both brand and workspace, preventing cross-workspace attachment at the database layer.
- `knowledge_documents`: normalized workspace sources with brand association, metadata,
  state, content checksum, attribution URI, and tenant-local deduplication.
- `knowledge_chunks`: cited text ranges and 384-dimensional vectors with a composite
  document/workspace foreign key. PostgreSQL adds an HNSW cosine index; SQLite uses JSON
  only as a deterministic test/development fallback.
- `campaigns`: workspace and brand-scoped campaign briefs, publishing mode, lifecycle state,
  feedback, and monotonically increasing current revision.
- `campaign_runs`: durable graph executions with run/revision identity, current node, safe
  state checkpoint, model metadata, timing, and terminal failure state.
- `campaign_steps`: ordered node-level checkpoints with digests, citations, safe outputs,
  durations, and provider metadata.
- `content_variants`: immutable campaign revisions for each platform, including copy,
  hashtags, CTA, quality score, validation issues, model identity, and evidence citations.

All workspace, brand, document, chunk-count, and retrieval reads require a user identifier
and join through organization membership. Direct unscoped tenant reads are not exposed by
the repositories.
