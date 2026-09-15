# Agent graph contract

The campaign graph coordinates work; it is not the scheduler and it does not directly publish.

Each node receives a typed state projection containing identifiers, authorized workspace scope, artifact references, policy flags, and citations. It never receives OAuth tokens. Deterministic nodes handle validation, state transitions, scheduling requests, and adapter calls. Model-backed nodes are reserved for tasks requiring synthesis or judgment.

Every node emits a structured result, evidence references, timing, provider metadata, and safe error information. Human approval creates an immutable boundary: later regeneration produces a new revision rather than mutating an approved artifact.

