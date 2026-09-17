# Supplemental Runtime Tasks: Step 5C

These runtime obligations are mandatory refinements of `tasks.md`; they do not introduce separate commit IDs.

## Contract Runtime Obligations (T005–T009)

- Canonicalization must use RFC 8785-compatible semantics with cross-language golden bytes, not ad-hoc key sorting.
- Unknown fields fail closed for authoritative intent/admission/status contracts.
- Numeric bounds and Unicode handling must be explicit in fixtures.
- Schema/version mismatch must be a typed rejection, never best-effort coercion.

## Controller Runtime Obligations (T010–T016)

- Ingress is bounded before full parse/validation.
- Authenticated subject is derived from the trusted mechanism, never copied from `declared_operator`.
- Admission and idempotency allocation are atomic with respect to duplicate intent submission.
- No denied/expired/quota-rejected request may start a worker.
- Controller audit output excludes raw secrets and private workload payloads.

## Worker Runtime Obligations (T017–T022)

- Operation dispatch is a closed enum switch/table over approved handlers.
- No `eval`, `exec`, dynamic import, user module name, shell/process string, or unmanaged path can be reached from intent fields.
- Worker recomputes/verifies lineage fields supplied by the gate before executing.
- Success receipt is emitted only after the operation succeeds on the same execution identity.
- Timeout/cancel/error paths produce no success receipt and no consensus claim.

## Admin UI Runtime Obligations (T023–T028)

- Existing browser-local mode remains usable without a controller.
- Live mode is explicit; network capability is not silently added to `LocalJsonAdapter`.
- UI never labels locally computed digest checks as authentication/authorization.
- UI renders gate/worker status but does not infer policy or protocol verdicts.
- Browser persistence must not contain private keys or long-lived service credentials.

## Integration Runtime Obligations (T035–T039)

- Transport selection must preserve all authority boundaries from ADR 0002.
- Requests/responses have hard size limits and bounded timeout/backpressure behavior.
- Duplicate/reordered/replayed messages must not duplicate execution.
- Controller restart and browser reconnect must recover status by execution identity.
- End-to-end receipt lineage must verify from canonical fixtures and reject one-field tampering.
