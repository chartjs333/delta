# Step 5C Security Checklist

A checked item requires test/evidence, not assertion.

## Authority / Identity
- [ ] Browser-declared identity cannot grant a role.
- [ ] Trusted authentication result is bound into `AdmissionRecord`.
- [ ] Wrong/expired credential, role, audience/peer, policy version, or catalog ref fails before worker start.

## Input / RCE Boundary
- [ ] No intent field can select shell commands, Python source, callable/module paths, interpreter flags, native handles, or unmanaged filesystem paths.
- [ ] Unknown operation and unknown payload fields fail closed.
- [ ] Bounded parse/size/depth/string limits exist at controller ingress.
- [ ] Fuzz/property tests cover JSON/JCS/schema/dispatch boundary.

## Replay / Idempotency
- [ ] Same intent submitted concurrently starts at most one execution.
- [ ] Duplicate active submission returns existing execution identity/status.
- [ ] Duplicate completed submission returns existing terminal result/receipt.
- [ ] Controller restart preserves the duplicate-execution invariant.
- [ ] Expired intents cannot be newly admitted.

## Resource Safety
- [ ] Quota/concurrency/time limits are enforced before/while running as specified.
- [ ] Rejected quota requests start no worker.
- [ ] Timeout/cancel/failure cannot emit SUCCESS/COMPLETED receipt.
- [ ] Transport/profile has hard request/response size and backpressure limits.

## Lineage / Provenance
- [ ] One-field tamper of intent invalidates `intent_digest`.
- [ ] One-field tamper of admission invalidates `admission_digest`.
- [ ] Cross-workload/cross-execution receipt reuse is rejected.
- [ ] Catalog ref, producer commit, controller commit, intent/admission/execution IDs are displayed/validated with correct semantics.
- [ ] `PLUGIN_BOUNDARY` remains unattested; UI does not use signature/consensus wording without evidence.

## Secrets / Data
- [ ] Browser storage contains no private keys or long-lived service credentials.
- [ ] Audit logs redact credentials and private payloads.
- [ ] Repository secret/license scan is green.
- [ ] No protected Delta spine path changed.
