# Step 5C Integration Checklist

## Contract Freeze
- [ ] ADR 0002 Accepted.
- [ ] `CONTRACT_FREEZE_SHA` recorded.
- [ ] Canonical contracts/JCS vectors merged and all implementation branches rebased.

## Component Gates
- [ ] Controller T010–T016 review-clean with auth/policy/idempotency evidence.
- [ ] Worker T017–T022 review-clean with closed operation dispatch and lineage evidence.
- [ ] Admin UI T023–T028 review-clean with offline regression and no trust inflation.
- [ ] Security T029–T034 review-clean with adversarial evidence.

## E2E
- [ ] Transport implementation note reviewed and does not change ADR trust semantics.
- [ ] Valid intent produces admission, one execution, terminal receipt.
- [ ] Intent/admission/execution/receipt IDs and digests match exactly across all boundaries.
- [ ] Duplicate submission during RUNNING does not start another worker.
- [ ] Duplicate submission after COMPLETED returns the same terminal result.
- [ ] Restart/reconnect recovers existing status and idempotency state.
- [ ] Timeout/cancel/failure paths never produce success receipt.
- [ ] Invalid/expired/unauthorized/incompatible intents start no worker.
- [ ] Existing offline Admin UI flow works with controller absent.

## Final Gate
- [ ] Full quality suites green.
- [ ] Threat/security checklist green.
- [ ] Machine-readable evidence published.
- [ ] Protected-path diff empty.
- [ ] Final Constitution/formal-impact check complete.
- [ ] Independent reviewers report no blocking findings.
