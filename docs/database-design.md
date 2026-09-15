# Database design principles

The logical data model begins in Phase 1. It will separate identity, tenancy, knowledge, campaign, publishing, and analytics concerns while preserving transactional boundaries.

Every tenant-owned table will include `organization_id` and `workspace_id` where applicable. Authorization is enforced in both services and repositories, backed by database constraints and row-level security where practical. OAuth material is stored separately from ordinary social account metadata. Vector chunks retain source document identity and tenant keys. Publish attempts retain idempotency keys, external IDs, retry state, and audit references.

