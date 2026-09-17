# Implementation Plan: Step 5C Controlled Live Execution

**Status**: Draft / STOP before implementation branches  
**Authority**: ADR 0002 + this SpecKit  
**Design baseline**: `f26c863d8dc2c5c019b77308b9ca0d0754bc3ff9`

## Constitution Check

- Formal-first rule: PASS for planning only. Planned scope does not alter consensus actions, certificates, arithmetic, durability, or current-state behavior.
- Permissioned identity/safe boundary principle: directly applicable; authentication, role policy, replay protection, and safe data contracts are mandatory.
- Runtime ownership: browser drafts/displays; trusted controller admits/dispatches; Python worker executes local ML; consensus spine remains isolated.
- Persist-before-expose: not modified. Step 5C does not create or expose native consensus transitions.
- Any task that requires protected spine changes, new consensus transitions, or new `STAGE_C_REAL_DRQ1` behavior is STOP and must return to Feature 000/formal review.

## Contract Freeze Gate

No implementation feature branch may be created or assigned until all of the following are true:

1. ADR 0002 is reviewed and marked `Accepted`.
2. `spec.md`, `plan.md`, `tasks.md`, `task-map.md`, `runtime-profile.md`, `runtime-tasks.md`, and checklists are reviewed.
3. `ExecutionIntent`, `AdmissionRecord`, `ExecutionStatus`, error taxonomy, lineage fields, idempotency semantics, and allowed operations are frozen at the design level.
4. A merge commit containing the accepted ADR + SpecKit is recorded as `CONTRACT_FREEZE_SHA`.

`CONTRACT_FREEZE_SHA` is the common base for Step 5C implementation branches. No developer may invent or reuse unrelated task IDs after this point.

## Work Waves

### Wave A — Contract artifacts and adversarial design

- Contracts branch materializes frozen schemas and golden JCS/digest fixtures.
- Security branch prepares attack/replay/confused-deputy matrices against those contracts.
- UI work may prepare presentation-state mocks but may not add a live network adapter before canonical contract artifacts exist.

### Wave B — Parallel implementation

After canonical contract artifacts are merged/rebased, three implementation branches proceed in parallel:

- trusted Authorization Gate / controller;
- worker execution adapter;
- Admin UI live intent/status adapter.

Each branch has exclusive path ownership described in `branch-matrix.md`. Contract changes require returning to the RFC branch and a reviewed SpecKit amendment.

### Wave C — Integration

Integration selects the first transport profile, joins controller/worker/UI, proves end-to-end lineage/idempotency/recovery, and adds transport-specific security controls without changing the authority model.

### Wave D — Qualification

Run full quality/security gates, publish machine-readable evidence, perform final Constitution/formal-impact check, and decide merge/release readiness.

## Architecture Ownership

### Zone 1 — Admin UI

- remains untrusted;
- drafts intents from frozen catalog descriptors;
- computes/displays canonical digests for user visibility but is never authority;
- submits only through the live adapter;
- retains existing offline local adapters unchanged.

### Zone 2 — Authorization Gate

Planned as a separate process/package (`delta-controller-python/` unless amended before T010). It owns authentication, policy, catalog parity, TTL, idempotency ledger, quotas, admission records, execution IDs, status, and audit metadata. It must not share mutable in-process authority with the worker.

### Zone 3 — Worker

Adds a narrow live-execution adapter around existing `ModelPluginRunner`; it does not become an authentication/policy service. It accepts only validated `AuthorizedExecution` bundles and performs operation-enum dispatch to existing registered functionality.

### Zone 4 — Consensus Spine

Out of scope and protected. No Step 5C implementation branch owns protected C++/Java/formal paths.

## First Transport Profile

Transport remains intentionally undecided until integration task T035. T035 must record a reviewed implementation note covering endpoint binding, authentication handoff, origin/CSRF protections where applicable, message size limits, timeout/backpressure, and secret handling. A transport choice that changes trust or protocol semantics requires an ADR/SpecKit amendment before code.

## Merge Order

1. RFC/SpecKit governance merge (contract freeze).
2. Contracts PR.
3. Controller, worker, Admin UI, and security PRs may proceed in parallel but must rebase onto the merged contracts commit before final review.
4. Integration PR.
5. Qualification/release PR.

## Evidence Policy

Every task completion requires at least one of: exact test name/result, generated fixture hash, schema/vector artifact, audit record, CI job URL/run ID, or reviewed diff/commit SHA. Narrative walkthroughs alone do not close tasks.

## Commit/Task Reference Rule

Step 5C uses local task IDs `T000`–`T044`. To avoid ambiguity with numbered roadmap features, commit messages MUST qualify them, e.g. `[step5c:T017]`, never unqualified `[T017]`. Existing Feature 009/010 task IDs must not be reused as Step 5C authority.
