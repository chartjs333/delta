# Tasks: Step 5C Controlled Live Execution

**Input**: ADR 0002, Step 5C `spec.md`, `plan.md`, Constitution 2.1.0, `AGENTS.md`, `main@4992d9e`, design baseline `f26c863`.

Task IDs are local to this SpecKit. Commit references MUST use the qualified form `[step5c:T###]`.

## Phase 0 — Governance and mandatory STOP checks

- [ ] **T000** Verify exact product baseline `4992d9e`, ADR design baseline `f26c863`, accepted formal semantics ID, and protected-path zero-diff requirement; record preflight evidence.
- [ ] **T001** Complete independent review of ADR 0002; resolve findings; confirm formal impact `NONE` relative to consensus semantics or STOP/reclassify.
- [ ] **T002** Review and approve this SpecKit, including task dependencies, branch ownership, threat scope, and exit gate.
- [ ] **T003** Merge governance PR with ADR 0002 status `Accepted`; no live-control implementation code in that PR.
- [ ] **T004** Record `CONTRACT_FREEZE_SHA`, create only the branches authorized by `branch-matrix.md`, and publish branch/base/task assignments.

## Phase 1 — Canonical contract artifacts

- [ ] **T005** Materialize strict Draft 2020-12 `ExecutionIntent` schema with operation-specific payloads and forbidden extra properties.
- [ ] **T006** Materialize strict `AdmissionRecord` / `AuthorizedExecution` schemas with authenticated subject, policy context, resource grants, execution ID, and admission digest.
- [ ] **T007** Define `ExecutionStatus`, preflight error taxonomy, and terminal `ExecutionReceipt` lineage extension schemas without consensus fields.
- [ ] **T008** Add RFC 8785 JCS golden vectors and SHA-256 fixtures covering every semantic field, Unicode/number edge cases, tampering, and cross-language parity.
- [ ] **T009** Add contract validation tests and valid/invalid fixtures; publish exact artifact hashes. Contracts branch exit gate blocks final review of controller/worker/UI branches.

## Phase 2 — Trusted Authorization Gate / Controller

- [ ] **T010** Create the separate controller package/process boundary and startup descriptor; it must not import browser state or native consensus APIs.
- [ ] **T011** Implement bounded input parsing, schema validation, JCS recomputation, intent TTL validation, and fail-closed digest mismatch handling.
- [ ] **T012** Implement authentication port and policy evaluation; treat `declared_operator` only as untrusted claimed metadata.
- [ ] **T013** Implement frozen catalog/ref/capability-matrix validation and operation/scope allowlist checks.
- [ ] **T014** Implement durable append-only idempotency ledger with one-intent/one-execution semantics, duplicate-in-progress lookup, completed receipt lookup, and restart recovery.
- [ ] **T015** Implement resource grants, concurrency/quota/timeout admission checks, and typed preflight rejection without worker start.
- [ ] **T016** Implement `AdmissionRecord`, execution ID allocation, dispatch port, status read model, and audit metadata with secret-redaction tests.

## Phase 3 — Constrained Worker Adapter

- [ ] **T017** Implement `AuthorizedExecution` validation: intent/admission IDs/digests, catalog ref, operation, scope, TTL/admission validity, and execution ID parity.
- [ ] **T018** Implement closed enum dispatch to existing registered `ModelPluginRunner` operations; no dynamic imports, callable names, shell, or arbitrary paths.
- [ ] **T019** Implement operation adapters for `TRAIN_TICKET`, `MATERIALIZE_DATASET`, `EVALUATE_SPLIT`, and `EVALUATE_CHECKPOINT` with operation-specific payload validation.
- [ ] **T020** Implement bounded timeout/cancellation behavior that cannot publish a success receipt after timeout/cancel/failure.
- [ ] **T021** Extend terminal receipt emission with `intent_id`, `intent_digest`, `admission_id`, `admission_digest`, and `execution_id`; preserve existing catalog/producer provenance and unattested semantics.
- [ ] **T022** Add worker negative/regression tests for forged admission, cross-workload binding, stale/expired bundles, wrong scope, wrong execution ID, arbitrary path/module injection, and false Stage C claims.

## Phase 4 — Admin UI Live Intent and Status Surface

- [ ] **T023** Add a live-execution `DataSourcePort`/adapter boundary isolated from existing offline adapters; no network behavior in local adapters.
- [ ] **T024** Implement form-first `ExecutionIntent` builder from the frozen catalog; expose only allowed operation-specific fields and constraints.
- [ ] **T025** Implement browser RFC 8785 canonicalization/digest verification against T008 golden vectors; UI digest remains informational, gate recomputation remains authority.
- [ ] **T026** Implement explicit UI states for draft, rejected, admitted, queued, running, completed, failed, timed out, cancelled, stale/unavailable.
- [ ] **T027** Implement lineage/provenance display linking intent/admission/execution/receipt without trust inflation; retain `UNATTESTED_*` semantics.
- [ ] **T028** Preserve offline mode, bounded untrusted JSON parsing, CSP, and zero-egress local-adapter tests; live transport must be isolated behind explicit configuration/capability.

## Phase 5 — Security and Reliability Hardening

- [ ] **T029** Build threat-test matrix for RCE/path/module injection, malicious JSON/JCS, stale catalog, forged lineage, role spoofing, and confused deputy.
- [ ] **T030** Prove replay/idempotency behavior under concurrent duplicate submission and controller restart; no duplicate worker start.
- [ ] **T031** Add authentication/policy negative tests: claimed-role escalation, credential mix-up, expired authorization, wrong audience/peer, and policy-version mismatch.
- [ ] **T032** Add quota/resource-exhaustion/timeout/backpressure tests and prove rejection does not start a worker.
- [ ] **T033** Add fuzz/property tests for contract parsers and operation payload dispatch boundaries; no arbitrary code/path escape.
- [ ] **T034** Add audit/secret scanning, sensitive-field redaction, and immutable evidence checks; no keys/tokens/private data committed.

## Phase 6 — End-to-End Integration

- [ ] **T035** Select and document the first transport implementation profile with explicit auth handoff, origin/CSRF or peer-credential controls, message limits, backpressure, timeout, and secret handling; amend ADR if trust semantics change.
- [ ] **T036** Integrate controller -> worker AuthorizedExecution dispatch and status propagation with restart-safe execution identity.
- [ ] **T037** Integrate Admin UI -> controller submit/status/result flow while retaining offline adapter independence.
- [ ] **T038** Prove complete `intent -> admission -> execution -> receipt` lineage with tamper rejection at every boundary and exact digest fixtures.
- [ ] **T039** Prove crash/restart/idempotent recovery, duplicate submit behavior, timeout/cancel terminal semantics, and cached terminal receipt retrieval.

## Final Phase — Qualification and merge gate

- [ ] **T040** Run Python/controller/worker/Admin UI quality gates plus repository diff checks and transport-specific integration tests.
- [ ] **T041** Run Step 5C security checklist, threat regression suite, dependency/secret scan, and protected-spine zero-diff verification.
- [ ] **T042** Publish machine-readable end-to-end evidence mapping T000–T041 to commits/tests/artifact hashes and one successful controlled workload proof.
- [ ] **T043** Perform final Constitution Check and formal-impact review against the actual implementation diff; any protected semantic change is STOP.
- [ ] **T044** Final independent review: all required tasks/evidence green, no unresolved review threads, mergeable/CLEAN; issue release/merge decision.

## Dependency Summary

- T000–T004 block all implementation branches.
- T005–T009 block final review/merge of T010–T028 implementation branches.
- T010–T016, T017–T022, T023–T028, and T029–T034 are parallel workstreams after contract freeze; each must rebase onto merged contract artifacts before final review.
- T035–T039 depend on controller + worker + UI contracts/implementations reaching review-clean state.
- T040–T044 are sequential exit gates.

## Exit Gate

Step 5C is complete only when a registered workload can be intentionally submitted from the Admin UI, independently admitted by the trusted gate, executed through the constrained worker, and returned as an unattested but structurally valid receipt whose intent/admission/execution lineage verifies exactly; replay does not duplicate execution; hostile input cannot reach arbitrary execution; offline UI remains functional; protected consensus paths remain unchanged.
