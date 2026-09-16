# Agent graph contract

The campaign graph coordinates work; it is not the scheduler and it does not directly publish.

Each node receives a typed state projection containing identifiers, authorized workspace scope, artifact references, policy flags, and citations. It never receives OAuth tokens. Deterministic nodes handle validation, state transitions, scheduling requests, and adapter calls. Model-backed nodes are reserved for tasks requiring synthesis or judgment.

Every node emits a structured result, evidence references, timing, provider metadata, and safe error information. Human approval creates an immutable boundary: later regeneration produces a new revision rather than mutating an approved artifact.

## Implemented Phase 5 graph

```text
START
  -> context_retrieval
  -> planning
  -> content_generation
  -> platform_adaptation
  -> validation
  -> approval_boundary
  -> END
```

The graph is synchronous in Phase 5, while every node records a durable `campaign_steps`
checkpoint containing an input digest, safe output projection, citations, duration, provider
metadata, and failure state. `campaign_runs.state_snapshot` stores the latest resumable
application state. Celery execution and native PostgreSQL LangGraph checkpoint adapters are
deferred until background workers are introduced.

The model is called only by `content_generation`. Retrieval, lifecycle transitions,
platform limits, quality checks, approval decisions, and revision handling remain
deterministic application code.
