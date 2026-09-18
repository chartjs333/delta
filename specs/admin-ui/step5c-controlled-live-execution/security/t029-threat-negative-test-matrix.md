# T029 Threat / Negative-Test Matrix

**Task**: `step5c:T029`
**Branch**: `feature/step5c-security`
**Base / contract freeze**: `66e3e7e5bb07a48aadbee8d9c4683144b812d229`
**Scope**: Security-owned threat fixtures, adversarial test design, and owner handoff routing only.

This matrix is the Wave A security design artifact. It does not implement controller,
worker, UI, or transport production behavior. Executable tests that need canonical
schemas, RFC 8785 vectors, Ed25519 vectors, or typed error fixtures are intentionally
blocked on the contracts branch completing `step5c:T005-T009`.

## Execution Binding Status

| Area | Status | Unblocks When |
| --- | --- | --- |
| Schema-backed negative fixtures | `BLOCKED_ON_T009` | Frozen `ExecutionIntent`, `AdmissionRecord`, `AuthorizedExecution`, `ExecutionStatus`, and receipt lineage schemas exist. |
| JCS/digest tamper tests | `BLOCKED_ON_T008` | RFC 8785 golden bytes and SHA-256 fixtures exist. |
| Ed25519 forged admission tests | `BLOCKED_ON_T008` | Pinned public-key, valid signature, invalid signature, wrong-key, and tamper vectors exist. |
| Controller/worker executable tests | `BLOCKED_ON_OWNER_BRANCHES` | Controller `T010-T016` and worker adapter `T017-T022` expose review-clean test surfaces. |

## Matrix

| ID | Category | Attack Vector | Expected Fail-Closed Result | Owner For Production Fixes | First Executable Gate |
| --- | --- | --- | --- | --- | --- |
| `S5C-T029-RCE-001` | RCE | Put shell metacharacters or Python source in string fields such as `ticket_id`, `partition_id`, `cache_key`, or `declared_operator.subject_id`. | Schema rejects or dispatch rejects before worker start; no shell/process/callable path reachable. | Contracts for schema gaps; Worker for dispatch gaps; UI for form exposure gaps. | `T009`, then `T018/T022` |
| `S5C-T029-RCE-002` | RCE | Smuggle command-like values through unknown fields in `operation_payload` or root objects. | Unknown fields rejected by `additionalProperties: false`; no worker start. | Contracts if accepted by schema; Controller if accepted at ingress; Worker if accepted at adapter. | `T009`, then `T011/T022` |
| `S5C-T029-PATH-001` | Path injection | Use `../`, absolute paths, Windows drive paths, UNC paths, URL-like paths, or symlink-looking values in payload identifiers. | Schema rejects non-identifier values or worker dispatch refuses unmanaged paths; no filesystem selection from intent. | Contracts for identifier regex/bounds; Worker for filesystem adapter gaps. | `T009`, then `T018/T022` |
| `S5C-T029-MODULE-001` | Module/plugin injection | Use `model_plugin_id` values resembling module paths, import paths, package URLs, mixed case, or dotted names. | Catalog allowlist rejects; registry lookup is by ID only; no dynamic import. | Contracts for ID bounds; Controller for catalog parity; Worker for registry dispatch. | `T009`, then `T013/T018/T022` |
| `S5C-T029-JSON-001` | Malicious JSON | Oversized body, excessive depth, huge strings, duplicate keys, invalid UTF-8, malformed dates, or number edge cases. | Bounded parse/schema/JCS failure returns typed rejection; no ledger allocation or worker start. | Controller for ingress bounds; Contracts for vectors. | `T008/T009`, then `T011/T033` |
| `S5C-T029-JCS-001` | Malicious JCS | Reorder keys, alter Unicode normalization-sensitive text, use negative zero, float, exponent, or integer boundary values to produce digest ambiguity. | Canonicalization mismatch or schema rejection; typed digest/canonicalization failure. | Contracts for vectors; Controller/Worker for recomputation parity. | `T008/T009`, then `T011/T017/T033` |
| `S5C-T029-REPLAY-001` | Replay | Concurrently submit the exact same `intent_id + intent_digest + authenticated_subject`. | One ledger allocation, one `execution_id`, one worker start; duplicates return in-progress status. | Controller. | `T014/T030` |
| `S5C-T029-REPLAY-002` | Replay mutation | Re-submit same `intent_id` with changed payload/digest. | `ERR_INTENT_ID_DIGEST_CONFLICT`; no worker start. | Controller. | `T014/T030` |
| `S5C-T029-REPLAY-003` | Cross-subject replay | Different authenticated subject queries or replays an existing `intent_id`. | `ERR_UNAUTHORIZED_CALLER`; no status/receipt disclosure and no worker start. | Controller. | `T014/T031` |
| `S5C-T029-REPLAY-004` | Digest anomaly | Different `intent_id` with same `intent_digest`. | `ERR_INTENT_COLLISION_DETECTED`; fail closed. | Controller. | `T014/T030` |
| `S5C-T029-ADMISSION-001` | Forged admission | Unsigned, self-digested, or random-signature `AdmissionRecord`. | Worker/controller rejects Ed25519 verification before operation dispatch. | Contracts for signature vectors; Worker for preflight; Controller for signing. | `T008/T009`, then `T016/T017/T022` |
| `S5C-T029-ADMISSION-002` | Admission tamper | Modify `resource_grants`, `execution_id`, `admission_expires_at`, `policy_context`, issuer/key metadata, or `intent_digest` after signing. | `admission_digest` and/or Ed25519 verification fails; no worker start. | Worker for verification; Contracts for tamper vectors. | `T008/T009`, then `T017/T022` |
| `S5C-T029-ADMISSION-003` | Expired admission | Dispatch after `admission_expires_at` or with `admission_expires_at > intent.expires_at`. | Worker rejects stale bundle before operation dispatch. | Controller for issuance; Worker for freshness. | `T016/T017/T022` |
| `S5C-T029-DEPUTY-001` | Confused deputy | Intent requests downloads but `AdmissionRecord.resource_grants.allow_downloads=false`. | Worker honors only admission grant; no network/data materialization authority from intent request. | Worker; Controller for grant issuance. | `T015/T017/T022/T032` |
| `S5C-T029-DEPUTY-002` | Confused deputy | UI digest or declared operator role is treated as authentication/authorization. | Gate derives authenticated subject independently; UI text remains informational. | Controller for auth; Admin UI for wording/state. | `T012/T023/T027/T031` |
| `S5C-T029-ROLE-001` | Role spoofing | `declared_operator.role=OPERATOR` with caller credential lacking operator role. | Policy rejects before ledger allocation/worker dispatch. | Controller. | `T012/T031` |
| `S5C-T029-ROLE-002` | Credential confusion | Wrong audience, wrong peer, expired token/cert, or mismatched authenticated principal. | Auth/policy rejects before worker dispatch and redacts sensitive details. | Controller. | `T012/T031/T034` |
| `S5C-T029-QUOTA-001` | Resource exhaustion | `checkpoint_coordinates` at 4097 items, int outside signed 32-bit range, huge timeout, or large strings. | Schema/ingress rejects before worker start. | Contracts; Controller; Worker for adapter parity. | `T009/T011/T017/T032/T033` |
| `S5C-T029-QUOTA-002` | Resource exhaustion | Valid schema but quota/concurrency/memory would exceed policy. | Typed quota rejection; no worker start. | Controller. | `T015/T032` |
| `S5C-T029-TIMEOUT-001` | Reliability timeout | Operation times out, is cancelled, or fails after partial work. | Terminal status is failed/timed out/cancelled; no `SUCCESS`/`COMPLETED` receipt. | Worker; Controller status read model. | `T020/T032/T039` |
| `S5C-T029-CATALOG-001` | Stale catalog | Intent `catalog_backend_ref` differs from frozen catalog `source.backend_ref` or catalog no longer contains plugin/dataset pair. | Catalog parity/capability matrix rejects before worker start. | Controller; Contracts for catalog fixtures. | `T013/T029/T031` |
| `S5C-T029-CATALOG-002` | Stale compatibility | Valid IDs but operation/scope unsupported by capability matrix, e.g. `TRAIN_TICKET` outside `PLUGIN_BOUNDARY`. | Typed policy/capability rejection before worker start. | Controller; UI form constraints; Worker adapter parity. | `T013/T017/T024` |
| `S5C-T029-LINEAGE-001` | Forged lineage | Receipt reuses another intent/admission/execution or omits `admission_id`, `admission_digest`, `execution_id`, `producer_commit`, or catalog ref. | Receipt lineage validation rejects; UI does not display as bound receipt. | Worker for emission; Admin UI for display validation; Contracts for receipt schema. | `T007/T021/T027/T038` |
| `S5C-T029-LINEAGE-002` | Consensus claim forgery | Local `PLUGIN_BOUNDARY` execution includes `STAGE_C_REAL_DRQ1`, `round_id`, `state_root`, `wal_sequence`, or QC-looking fields. | Worker/UI reject or mark invalid; no consensus wording or authority. | Worker; Admin UI. | `T022/T027/T041` |
| `S5C-T029-AUDIT-001` | Secret/data leakage | Audit/status errors include bearer tokens, private dataset payloads, Ed25519 private key material, or raw model data. | Redaction tests reject unsafe audit output; no secrets committed. | Controller for audit; Security for scans. | `T016/T034` |

## Owner Handoff Rule

Security branch findings must be filed against the owning stream instead of changing
production code directly:

- Contract/schema/vector defect: `feature/step5c-contracts` (`T005-T009`).
- Controller auth, policy, ledger, quota, status, audit defect: `feature/step5c-controller` (`T010-T016`).
- Worker preflight, closed dispatch, timeout, receipt lineage defect: `feature/step5c-worker-adapter` (`T017-T022`).
- Admin UI trust wording, offline boundary, mock/live state defect: `feature/step5c-admin-ui-live` (`T023-T028`).
- Cross-component transport/backpressure defect: wait for `feature/step5c-e2e` (`T035-T039`) unless it invalidates ADR trust semantics.

## Acceptance Notes

- This matrix satisfies the T029 design inventory only.
- It does not mark the broader security checklist complete.
- Executable negative tests must bind to the exact schemas/vectors produced by A before final review of `feature/step5c-security`.
