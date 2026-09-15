# Database design principles

The Phase 1–2 data model separates identity, tenancy, and brand policy while preserving transactional boundaries. Later migrations add knowledge, campaign, publishing, and analytics domains without weakening these ownership keys.

Every tenant-owned table will include `organization_id` and `workspace_id` where applicable. Authorization is enforced in both services and repositories, backed by database constraints and row-level security where practical. OAuth material is stored separately from ordinary social account metadata. Vector chunks retain source document identity and tenant keys. Publish attempts retain idempotency keys, external IDs, retry state, and audit references.

## Current tables

- `users`: normalized unique identity, Argon2 password hash, active state, login time.
- `organizations`: top-level tenant with globally unique slug.
- `organization_members`: unique user/organization membership and constrained role.
- `workspaces`: organization-owned boundary with tenant-local slug uniqueness.
- `brand_profiles`: workspace-owned voice, audience, CTA, hashtag, and positioning data.
- `brand_rules`: prioritized policy records with a composite foreign key to both brand and workspace, preventing cross-workspace attachment at the database layer.

All application workspace and brand reads require a user identifier and join through membership. Direct unscoped `get(id)` access is not exposed by tenant repositories.
