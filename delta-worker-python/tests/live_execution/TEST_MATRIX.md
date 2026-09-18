# Step 5C Worker Adapter Test Matrix

Branch: `feature/step5c-worker-adapter`
Base / contract freeze: `66e3e7e5bb07a48aadbee8d9c4683144b812d229`
Tasks: `step5c:T017-T022`
Status: preparation only; executable tests wait for canonical contract artifacts from
`feature/step5c-contracts`.

## Scope

The worker adapter belongs under `delta-worker-python/src/deltatorrent/live_execution/**`.
It may call the existing `ModelPluginRunner` only after `AuthorizedExecution` preflight passes.
It must not implement controller authentication or policy, browser transport, idempotency
ledger semantics, or Delta consensus behavior.

Contract branch dependencies:

- Draft 2020-12 schemas and fixtures for `ExecutionIntent`, `AdmissionRecord`,
  `AuthorizedExecution`, `ExecutionStatus`, and receipt lineage extension.
- RFC 8785/JCS canonical byte fixtures for intent and admission digest recomputation.
- Ed25519 valid and invalid signature fixtures, including pinned controller verification
  key metadata.
- Error taxonomy names that worker preflight should return or raise.

Do not replace these with worker-local schemas, worker-local `AuthorizedExecution`
serialization, or a worker-local canonicalization dialect.

## ModelPluginRunner Archaeology

- `ModelPluginRunner` resolves plugins and datasets only through static registries and fresh
  plugin/provider instances.
- `ModelPluginRunner.train_ticket()` and `ModelPluginRunner.evaluate_checkpoint()` set
  `_last_execution` and are receipt-eligible for Step 5C v1.
- `ModelPluginRunner.materialize_dataset()` does not set `_last_execution`, matching the frozen
  Step 5C status-only `MATERIALIZE_DATASET` contract.
- `emit_execution_receipt()` rejects local `STAGE_C_REAL_DRQ1` claims and rejects receipt
  emission before a runner instance has executed a receipt-eligible operation.
- Existing tests already cover static registry binding, provenance separation, no-prior-execution
  receipt rejection, checkpoint numeric bounds, unsafe deserializer bans, and worker-local
  cancellation/failure terminal behavior.
- The worker package does not currently expose an Ed25519 verifier dependency. Implementation
  should consume the dependency/helper and vectors supplied by contracts rather than introducing
  unreviewed crypto glue in the worker branch.

## Planned Executable Tests

| ID | Task | Test candidate | Required contract artifact | Expected result |
| --- | --- | --- | --- | --- |
| C-WA-001 | T017 | accepts valid `AuthorizedExecution` for `TRAIN_TICKET` | valid intent/admission/signature fixture | immutable preflight context; execution ID comes only from admission |
| C-WA-002 | T017 | rejects `intent.intent_id != admission.intent_id` | one-field tampered admission | fail closed before runner construction |
| C-WA-003 | T017 | recomputes intent digest and rejects tampered payload | tampered `ticket_id` fixture | fail closed before runner construction |
| C-WA-004 | T017 | rejects `admission.intent_digest != intent.intent_digest` | tampered admission digest fixture | fail closed before runner construction |
| C-WA-005 | T017 | verifies Ed25519 signature over admission without `authenticator.signature` | valid Ed25519 vector | passes only with pinned key metadata |
| C-WA-006 | T017 | rejects invalid Ed25519 signature | invalid signature vector | fail closed before runner construction |
| C-WA-007 | T017 | rejects valid signature under unknown `key_id` | unknown-key fixture | fail closed before runner construction |
| C-WA-008 | T017 | rejects expired `admission_expires_at` | expired admission fixture | fail closed before runner construction |
| C-WA-009 | T017 | rejects `admission_expires_at > intent.expires_at` | invalid TTL fixture | fail closed before runner construction |
| C-WA-010 | T017 | honors `admission.resource_grants.allow_downloads`, ignoring request flag | intent requests downloads; admission denies | materialization uses `allow_download=False` |
| C-WA-011 | T018 | dispatch table contains only approved operations | operation enum fixture | no dynamic lookup; unknown operation rejected |
| C-WA-012 | T018 | malicious callable/module/cmd/path fields cannot select code | hostile extra-field fixtures | fail closed before dispatch |
| C-WA-013 | T018 | source-level guard forbids `eval`, `exec`, dynamic import, subprocess, shell helpers | AST scan of live adapter package | no violations |
| C-WA-014 | T019 | `TRAIN_TICKET` calls only `runner.train_ticket(ticket_id, partition_id)` | valid train fixture | receipt-eligible result with `TRAIN_TICKET` execution type |
| C-WA-015 | T019 | `TRAIN_TICKET` rejects non-`PLUGIN_BOUNDARY` scope | invalid scope fixture | fail closed before runner construction |
| C-WA-016 | T019 | `EVALUATE_CHECKPOINT` calls only `runner.evaluate_checkpoint(coordinates)` | valid checkpoint fixture | receipt-eligible result, no split/model object input |
| C-WA-017 | T019 | checkpoint coordinate length matches plugin parameter schema before runner call | short, long, and over-max fixtures | fail closed; no runner call |
| C-WA-018 | T019 | `MATERIALIZE_DATASET` calls `runner.materialize_dataset(..., allow_download=grant)` | valid materialize fixture | typed status only; no receipt |
| C-WA-019 | T019 | materialize `cache_key` cannot become unmanaged filesystem path | traversal and absolute path fixtures | managed cache path or fail closed |
| C-WA-020 | T020 | timeout before receipt-eligible operation completes | injected slow runner/fault | terminal timeout/failure status; no success receipt |
| C-WA-021 | T020 | cancellation before completion | injected cancellation token | terminal cancelled status; no success receipt |
| C-WA-022 | T020 | runner exception during operation | injected runner error | failure status; no success receipt; no consensus claim |
| C-WA-023 | T021 | train receipt includes intent/admission/execution lineage | valid train fixture | provenance includes `intent_id`, `intent_digest`, `admission_id`, `admission_digest`, `execution_id` |
| C-WA-024 | T021 | checkpoint receipt includes lineage and preserves catalog/producer provenance | valid checkpoint fixture | lineage present; no consensus fields |
| C-WA-025 | T021 | materialization cannot emit receipt | valid materialize fixture | status only; no `ExecutionReceipt` |
| C-WA-026 | T021 | receipt workload binding must match intent workload | cross-workload tamper fixture | fail closed or receipt validation rejects |
| C-WA-027 | T022 | forged admission with matching shape but no trusted signature | forged admission fixture | fail closed before runner construction |
| C-WA-028 | T022 | wrong execution ID supplied by caller/result path is ignored or rejected | execution ID tamper fixture | admission execution ID remains sole authority |
| C-WA-029 | T022 | unknown plugin/dataset IDs fail through registries | unknown ID fixtures | fail closed; no dynamic import |
| C-WA-030 | T022 | local `STAGE_C_REAL_DRQ1` claim remains forbidden | false Stage C fixture | fail closed; no consensus evidence |
| C-WA-031 | T022 | receipt replay from another runner/execution is rejected by lineage check | cross-runner receipt fixture | validation rejects |
| C-WA-032 | T022 | public network remains denied except loopback in worker tests | existing autouse network fixture | no accidental network egress |

## Suggested Test Layout After Contracts Merge

- `delta-worker-python/tests/live_execution/test_authorized_execution_preflight.py`
- `delta-worker-python/tests/live_execution/test_dispatch.py`
- `delta-worker-python/tests/live_execution/test_receipt_lineage.py`
- `delta-worker-python/tests/live_execution/test_timeout_cancel.py`
- `delta-worker-python/tests/live_execution/test_live_execution_architecture.py`

The first implementation PR must cite the contract artifact commit and replace or supplement this
matrix with executable pytest cases. Narrative completion is not enough to close any
`step5c:T017-T022` task.
