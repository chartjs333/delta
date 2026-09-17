# Supplemental Runtime Tasks: Step 5C

These runtime obligations are mandatory refinements of `tasks.md`; they do not introduce separate commit IDs.

## Contract Runtime Obligations (T005–T009)

- Canonicalization must use RFC 8785-compatible semantics with cross-language golden bytes, not ad-hoc key sorting.
- Unknown fields fail closed for authoritative intent/admission/status contracts (`additionalProperties: false`).
- No JSON-Schema defaults in digest-bound schemas; all digest-bound fields are strictly required or omitted.
- Bounded coordinates: `checkpoint_coordinates` capped at `maxItems: 4096` with signed 32-bit integer limits (`[-2147483648, 2147483647]`).
- Numeric bounds and Unicode handling must be explicit in fixtures.
- Schema/version mismatch must be a typed rejection, never best-effort coercion.
- Ed25519 verification fixtures and golden vectors included in T008.

## Controller Runtime Obligations (T010–T016)

- Ingress is bounded before full parse/validation.
- Authenticated subject is derived from the trusted mechanism, never copied from `declared_operator`.
- Admission and idempotency allocation are atomic with respect to duplicate intent submission.
- Idempotency ledger keyed by `intent_id` (storing first-seen `intent_digest` and `authenticated_subject`).
- Duplicate lookup: same id + same digest + same subject returns existing status/receipt; same id + different digest rejects with `ERR_INTENT_ID_DIGEST_CONFLICT`; same id + different subject rejects with `ERR_UNAUTHORIZED_CALLER`.
- Retrying a failed/cancelled run requires a new `intent_id` (optional `retry_of_intent_id` lineage).
- `admission_expires_at` is assigned as the dispatch deadline and MUST NOT exceed `intent.expires_at`.
- Signs `AdmissionRecord` using private Ed25519 controller key.
- No denied/expired/quota-rejected request may start a worker.
- Controller audit output excludes raw secrets and private workload payloads.

## Worker Runtime Obligations (T017–T022)

- Operation dispatch is a closed enum switch/table over approved handlers (`TRAIN_TICKET`, `EVALUATE_CHECKPOINT`, `MATERIALIZE_DATASET`).
- No `eval`, `exec`, dynamic import, user module name, shell/process string, or unmanaged path can be reached from intent fields.
- Worker validates `AuthorizedExecution` preflight fail-closed: Ed25519 controller signature, digest parity, execution ID parity, and `now() <= admission_expires_at`.
- Worker strictly honors `resource_grants.allow_downloads` (default `false`); client-requested flags are ignored.
- `MATERIALIZE_DATASET` returns typed status only; emits no `ExecutionReceipt` in Step 5C v1.
- Success receipt is emitted only after receipt-eligible operation (`TRAIN_TICKET`, `EVALUATE_CHECKPOINT`) succeeds on the same execution identity.
- Terminal receipt lineage includes `intent_id`, `intent_digest`, `admission_id`, `admission_digest`, and `execution_id`.
- Timeout/cancel/error paths produce no success receipt and no consensus claim.

## Admin UI Runtime Obligations (T023–T028)

- Existing browser-local mode and `DataSourcePort` remain usable without a controller.
- Live mode is developed strictly behind a new `LiveExecutionPort` abstraction (mocked in Phase 4).
- Offline CSP (`connect-src 'none'`) and zero-egress boundaries remain intact in Phase 4; network transport is deferred to T035.
- UI never labels locally computed digest checks as authentication/authorization.
- UI renders gate/worker status but does not infer policy or protocol verdicts.
- Browser persistence must not contain private keys or long-lived service credentials; recovery occurs via re-submitting exact intent.

## Integration Runtime Obligations (T035–T039)

- Transport selection must preserve all authority boundaries from ADR 0002.
- Requests/responses have hard size limits and bounded timeout/backpressure behavior.
- Duplicate/reordered/replayed messages must not duplicate execution.
- Controller restart and browser reconnect must recover status by execution identity.
- End-to-end receipt lineage must verify from canonical fixtures and reject one-field tampering.
