# Publishing

The API now exposes the Phase 9 `SocialPublisher` contract, a replay-safe mock, and the
Phase 10 LinkedIn REST adapter under `apps/api/aevra_api/publishing`. This service boundary
remains the only place allowed to resolve token references; credentials never enter prompts,
browser state, agent state, job payloads, or provider metadata.

The next production increment is the worker-backed OAuth/token-vault flow. Until then,
`social_accounts.access_token_ref` is intentionally opaque and the mock publisher is the
safe default for non-LinkedIn platforms.
