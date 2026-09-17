# Step 5C Security Checklist

A checked item requires test/evidence, not assertion.

## Authority / Identity
- [ ] Browser-declared identity cannot grant a role.
- [ ] Trusted authentication result is bound into `AdmissionRecord`.
- [ ] `AdmissionRecord` Ed25519 signature verifies with pinned controller key over `admission \ {"authenticator.signature"}` (binding issuer/key/algorithm metadata); unsigned or tampered admissions are rejected fail-closed.
- [ ] `admission_expires_at` is enforced by worker; expired admission fails before worker start.
- [ ] Wrong/expired credential, role, audience/peer, policy version, or catalog ref fails before worker start.

## Input / RCE Boundary
- [ ] No intent field can select shell commands, Python source, callable/module paths, interpreter flags, native handles, or unmanaged filesystem paths.
- [ ] Unknown operation and unknown payload fields fail closed.
- [ ] Bounded parse/size/depth/string limits exist at controller ingress (`checkpoint_coordinates` bounded to 4096 items, int32 range).
- [ ] Fuzz/property tests cover JSON/JCS/schema/dispatch boundary.

## Replay / Idempotency
- [ ] Same intent submitted concurrently starts at most one execution.
- [ ] Duplicate active submission returns existing execution identity/status.
- [ ] Duplicate completed submission returns existing terminal result/receipt from cache.
- [ ] Re-submission of existing `intent_id` with different digest fails with `ERR_INTENT_ID_DIGEST_CONFLICT`.
- [ ] Re-submission or status lookup by different caller fails with `ERR_UNAUTHORIZED_CALLER`.
- [ ] Anomalous duplicate digest under different intent ID fails fail-closed with `ERR_INTENT_COLLISION_DETECTED`.
- [ ] Retry requires a fresh `intent_id` (optional `retry_of_intent_id`).
- [ ] Controller restart preserves the duplicate-execution invariant.
- [ ] Expired intents cannot be newly admitted.

## Resource Safety
- [ ] Quota/concurrency/time limits are enforced before/while running as specified.
- [ ] Worker honors strictly `resource_grants.allow_downloads` (default `false`); intent requested flag cannot grant network authority.
- [ ] Rejected quota requests start no worker.
- [ ] Timeout/cancel/failure cannot emit SUCCESS/COMPLETED receipt.
- [ ] Transport/profile has hard request/response size and backpressure limits.

## Lineage / Provenance
- [ ] One-field tamper of intent invalidates `intent_digest`.
- [ ] One-field tamper of admission invalidates `admission_digest` and Ed25519 signature.
- [ ] Cross-workload/cross-execution receipt reuse is rejected.
- [ ] Catalog ref, producer commit, controller commit, intent_id, intent_digest, admission_id, admission_digest, execution_id are bound and verified with correct semantics.
- [ ] `PLUGIN_BOUNDARY` remains unattested; UI does not use signature/consensus wording without evidence.

## Secrets / Data
- [ ] Browser storage contains no private keys or long-lived service credentials.
- [ ] Audit logs redact credentials and private payloads.
- [ ] Repository secret/license scan is green.
- [ ] No protected Delta spine path changed.
