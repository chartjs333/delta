# Branch Matrix: Step 5C Controlled Live Execution

## STOP

Do not create implementation branches until `tasks.md` T000–T004 are complete and `CONTRACT_FREEZE_SHA` is recorded from the merged governance commit.

## Planned Branches

### `feature/step5c-contracts`
- Tasks: T005–T009
- Base: `CONTRACT_FREEZE_SHA`
- Owns: canonical Step 5C schemas, JCS vectors, contract fixtures/tests/evidence.
- Must merge before final review of controller/worker/UI implementations.

### `feature/step5c-controller`
- Tasks: T010–T016
- Base: `CONTRACT_FREEZE_SHA`; rebase onto contracts merge before final review.
- Owns: new trusted controller package/process and tests.
- Forbidden: worker model/plugin behavior, Admin UI product code, protected spine.

### `feature/step5c-worker-adapter`
- Tasks: T017–T022
- Base: `CONTRACT_FREEZE_SHA`; rebase onto contracts merge before final review.
- Owns: narrow live-execution worker adapter and directly related worker tests/receipt-lineage integration.
- Forbidden: authentication/policy controller logic, browser networking, protected spine.

### `feature/step5c-admin-ui-live`
- Tasks: T023–T028
- Base: `CONTRACT_FREEZE_SHA`; rebase onto contracts merge before final review.
- Owns: live intent/status UI module and explicit adapter/composition tests.
- Forbidden: trusted policy, direct worker invocation, shell/process/native runtime calls.

### `feature/step5c-security`
- Tasks: T029–T034
- Base: `CONTRACT_FREEZE_SHA`; consume/rebase onto contract artifacts as needed.
- Owns: threat fixtures, adversarial/fuzz/property tests, evidence/checklists.
- Production fixes discovered here go back to the owning branch.

### `feature/step5c-e2e`
- Tasks: T035–T039
- Base: review-clean merged controller + worker + UI + security dependencies.
- Owns: transport adapter/profile, cross-component integration and recovery/idempotency E2E tests.

### `release/step5c-qualification`
- Tasks: T040–T044
- Base: integrated candidate.
- Owns: qualification evidence/checklists/docs/CI adjustments only. Defect fixes are split back to the owning implementation branch.

## Assignment Policy

A developer receives one branch and one task range. They may not self-assign tasks from another range. Findings that require new work are returned to the SpecKit owner for task creation/reprioritization before code changes.

## Required PR Header

Every Step 5C PR must state:

```text
Contract freeze: <SHA>
Tasks: step5c:Txxx–Tyyy
Allowed paths: ...
Protected paths modified: NONE
Formal impact: NONE / STOP if changed
Evidence: ...
```
