# Runtime Profile: Step 5C Controlled Live Execution

**Formal impact**: `NONE` relative to consensus semantics, subject to STOP rules below.

## Runtime Ownership

### Browser / Admin UI (Zone 1, untrusted)

Owns presentation, intent drafting, local structural validation, informational JCS digest display, status rendering, and offline receipt inspection. It owns no secret keys, trusted role decisions, process handles, scheduler authority, worker authority, or native consensus handles.

### Authorization Gate / Controller (Zone 2, trusted policy authority)

A separate process. Owns bounded ingress, authenticated caller identity, policy evaluation, catalog/ref/capability checks, intent TTL, resource quotas, durable idempotency ledger, Ed25519 signing key for `AdmissionRecord`, dispatch deadline (`admission_expires_at`), execution IDs, status projection, dispatch authorization, and audit metadata. It does not compute ML results or consensus decisions.

### Python Worker (Zone 3, constrained execution)

Owns local dataset materialization (status-only), ticket training (receipt-eligible), and checkpoint evaluation (receipt-eligible) through canonical `DatasetProvider`, `ModelPlugin`, and `ModelPluginRunner` paths. It accepts only an `AuthorizedExecution` bundle and verifies intent/admission parity, Ed25519 signature, dispatch deadline, and effective download grants before operation dispatch.

### Delta Consensus Spine (Zone 4, protected)

Unchanged. No local Step 5C operation can claim consensus, mutate WAL/current checkpoint, or bypass Feature 008/010 governance.

## Boundary Rules

- Browser -> controller: declarative schema-bounded data only via `LiveExecutionPort` abstraction.
- Controller -> worker: immutable `AuthorizedExecution` bundle packaging `ExecutionIntent` and signed `AdmissionRecord`.
- Worker -> controller/UI: bounded status/result artifacts and terminal receipt; no internal Python objects as wire authority.
- Contracts are transport-neutral and canonicalized independently at each trust boundary.
- Failure to canonicalize/verify any required digest or Ed25519 signature is terminal fail-closed for that request.

## Threading / Concurrency

- Controller may process concurrent intents, but durable idempotency allocation occurs atomically per intent identity.
- One admitted intent maps to at most one execution ID.
- Worker concurrency is bounded by resource grants; no implicit unbounded task spawning.
- Cancellation/timeout cannot convert a failed/aborted operation into a success receipt.

## Persistence

The idempotency ledger and terminal result reference must survive controller restart for the supported deployment profile. Persistence format is controller-owned and must not be confused with Delta consensus WAL.

## Formal STOP Conditions

Immediately stop implementation and return to formal/governance review if any proposed change:

- adds or changes a consensus state transition, vote/QC context, durability ordering, current-checkpoint rule, certificate edge, or BFT failure terminal;
- requires direct UI/controller mutation of native runtime state;
- exposes local controlled execution as `STAGE_C_REAL_DRQ1` without the native harness;
- modifies protected Zone 4 paths to satisfy Step 5C product behavior.

## Quality Gates

- controller: lint/type/unit/security tests defined by its package;
- worker: existing `ruff`, `mypy`, worker tests plus Step 5C adapter tests;
- Admin UI: `npm run check`, offline audit regression, live-adapter tests;
- repository: `git diff --check`, secret scan, protected-path zero diff;
- integration: duplicate/replay/restart/timeout/tamper E2E suite.
