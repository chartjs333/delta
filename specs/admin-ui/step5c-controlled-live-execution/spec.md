# Feature Specification: Step 5C Controlled Live Execution

**Track**: Admin UI product track (not roadmap Feature 010)  
**Status**: Draft / implementation blocked until contract freeze  
**Design authority**: `specs/admin-ui/adr/0002-controlled-live-execution-boundary.md`  
**Design baseline**: `f26c863d8dc2c5c019b77308b9ca0d0754bc3ff9`  
**Product baseline**: `main@4992d9eca319da21b5a2c7b94593f3668b92329c`  
**Formal impact**: `NONE` relative to Delta consensus semantics; any protocol-visible consensus change is an unconditional STOP and returns to Feature 000.

## Summary

Step 5C turns the existing browser-local Admin UI and canonical Python worker stack into a controlled product execution flow without giving the browser execution authority and without extending the Delta consensus spine. The product flow is:

`ExecutionIntent -> AdmissionRecord -> AuthorizedExecution -> constrained worker operation -> ExecutionReceipt`

The browser drafts intents and displays status/receipts. A separate trusted Authorization Gate authenticates the caller, validates policy/catalog/quota/idempotency, and emits an `AdmissionRecord`. A headless worker executes only allowlisted operations through registered `DatasetProvider` / `ModelPlugin` bindings. The receipt is a structurally validated, unattested record bound to intent/admission/execution lineage.

## User Scenarios

### US1 — Authorize and execute a registered training operation (P1)

An operator selects an approved model/dataset pair, drafts a `TRAIN_TICKET` intent, submits it to the trusted gate, receives admission/execution status, and obtains a receipt bound to the exact intent and admission.

**Acceptance**:
1. Browser input cannot contain shell commands, Python source, arbitrary module names, arbitrary filesystem paths, or native runtime handles.
2. The gate independently authenticates the caller; `declared_operator` is never authority.
3. Unknown model/dataset IDs, incompatible scope, catalog-ref mismatch, expired intent, quota failure, or policy denial produce a typed preflight rejection and start no worker.
4. Successful execution produces exactly one `execution_id` for one admitted `intent_id`.
5. The terminal receipt binds `intent_digest`, `admission_digest`, `execution_id`, catalog ref, producer commit, plugin ID, dataset ID, and executed scope.

### US2 — Safe replay and status recovery (P1)

An operator retries submission because the browser lost connectivity or the page was refreshed.

**Acceptance**:
1. A duplicate active intent returns the existing `execution_id` and current status without starting another worker.
2. A duplicate completed intent returns the existing terminal result/receipt.
3. A failed execution is not silently restarted; retry requires a new intent identity under explicit retry policy.
4. Controller restart preserves idempotency state required to prevent duplicate execution.

### US3 — Evaluate or materialize without training authority escalation (P1)

An operator requests `MATERIALIZE_DATASET`, `EVALUATE_SPLIT`, or `EVALUATE_CHECKPOINT` using only the operation-specific payload allowed by the frozen contract.

**Acceptance**:
1. Each operation has a closed payload schema and an explicit scope allowlist.
2. `emit_execution_receipt` is never an operator-requestable operation; receipt creation is terminal behavior of an executed operation.
3. Operation dispatch is by enum, never by user-supplied function/module/path name.

### US4 — Preserve offline Admin UI workflows (P1)

An auditor can continue to use the existing local-file catalog/receipt workflows with no controller, credentials, network service, or runtime present.

**Acceptance**:
1. Offline mode remains available and retains current bounded untrusted-JSON parsing and receipt semantics.
2. Live-mode code does not silently introduce network egress into offline adapters.
3. Removing/disableing the live adapter leaves existing browser-local workflows operational.

## Functional Requirements

- **FR-S5C-001**: `ExecutionIntent` MUST be strict, versioned, operation-specific, and canonically hashed with RFC 8785 JCS over all semantic fields except `intent_digest` itself.
- **FR-S5C-002**: Allowed intent operations are exactly `TRAIN_TICKET`, `EVALUATE_SPLIT`, `EVALUATE_CHECKPOINT`, and `MATERIALIZE_DATASET` for this increment.
- **FR-S5C-003**: `emit_execution_receipt` MUST NOT be an intent operation.
- **FR-S5C-004**: Zone 2 MUST authenticate the caller independently of `declared_operator` and emit a distinct `AdmissionRecord` for accepted work.
- **FR-S5C-005**: `AdmissionRecord` MUST bind intent identity/digest, authenticated subject/roles, policy version, controller commit, resource grants, execution ID, admission time/expiry, and its own canonical digest.
- **FR-S5C-006**: The gate MUST enforce catalog allowlist, compatibility matrix, catalog ref parity, intent TTL, authorization policy, resource quota, and replay/idempotency checks before worker dispatch.
- **FR-S5C-007**: One admitted intent MUST map to at most one execution ID. Duplicate submissions MUST be idempotent.
- **FR-S5C-008**: Worker dispatch MUST resolve plugins and datasets exclusively through canonical in-tree registries.
- **FR-S5C-009**: Worker dispatch MUST reject arbitrary code, module paths, shell arguments, unmanaged filesystem paths, and unregistered workloads.
- **FR-S5C-010**: Worker execution MUST verify intent/admission parity before invoking a workload operation.
- **FR-S5C-011**: Terminal receipt lineage MUST include `intent_id`, `intent_digest`, `admission_id`, `admission_digest`, and `execution_id` in addition to existing provenance/workload fields.
- **FR-S5C-012**: `PLUGIN_BOUNDARY` and `MODEL_DATASET_BINDING_ONLY` remain the only local live scopes; local live execution MUST NOT claim `STAGE_C_REAL_DRQ1`.
- **FR-S5C-013**: Admin UI MUST distinguish draft, rejected, admitted, queued/running, completed, failed, timed out, and cancelled product states without upgrading them into consensus claims.
- **FR-S5C-014**: Existing offline receipt inspection MUST remain available and must not depend on controller availability.
- **FR-S5C-015**: Transport is an implementation profile selected after authority/contract freeze; changing transport MUST NOT change intent/admission/lineage semantics.

## Security Requirements

- **SR-S5C-001**: No private signing key, long-lived service credential, worker handle, or native consensus handle may enter browser storage/DOM state.
- **SR-S5C-002**: Intents MUST expire; the initial maximum TTL is 900 seconds unless a reviewed contract change narrows it further.
- **SR-S5C-003**: Replay, confused-deputy, cross-workload, cross-runner, path-injection, plugin-injection, quota-exhaustion, stale-catalog, and forged-lineage tests are mandatory.
- **SR-S5C-004**: Controller audit records MUST not contain secrets or private dataset/model payloads.
- **SR-S5C-005**: The implementation MUST fail closed if canonicalization, digest verification, catalog parity, policy evaluation, idempotency state, or lineage verification is unavailable or ambiguous.

## Non-goals

- No change to `delta-core-cpp`, `delta-runtime-cpp`, `delta-ffi`, `delta-node-java`, or formal TLA+ semantics.
- No browser-driven shell/Python execution or dynamic plugin loading.
- No local fabrication of consensus/QC/WAL fields.
- No permissionless identity, economic incentives, or scheduler replacement.
- No new model workload is required to complete Step 5C.

## Key Entities

- **ExecutionIntent**: untrusted declarative request drafted by the client.
- **AdmissionRecord**: trusted gate decision binding authenticated authority and resource grants to an exact intent.
- **AuthorizedExecution**: runtime bundle `(ExecutionIntent, AdmissionRecord)` accepted for constrained execution.
- **ExecutionStatus**: read model for preflight/execution terminal state keyed by `execution_id`.
- **ExecutionReceipt**: terminal structurally validated, unattested record bound to intent/admission/execution lineage.
- **IdempotencyLedger**: durable gate-owned mapping preventing duplicate execution for the same admitted intent.

## Success Criteria

- **SC-S5C-001**: One registered workload completes end-to-end `intent -> admission -> execution -> receipt` with exact lineage verification and no manual receipt fabrication.
- **SC-S5C-002**: Duplicate submission tests prove one-intent/one-execution under concurrency and controller restart.
- **SC-S5C-003**: Hostile input tests cannot reach shell, dynamic import, arbitrary filesystem navigation, or native consensus mutation.
- **SC-S5C-004**: Existing Admin UI offline checks remain green and offline mode works with controller absent.
- **SC-S5C-005**: Protected Delta spine paths have zero Step 5C modifications.
- **SC-S5C-006**: Full Step 5C exit evidence is machine-readable and maps every completed task to tests/artifacts/commit SHAs.
