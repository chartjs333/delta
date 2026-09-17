# Step 5C Task / Workstream Map

## Governance Rule

The SpecKit is the task authority. Developers may report findings, but may not self-assign new task IDs, expand scope, or reuse task IDs from Feature 009/010. New work is first added here/`tasks.md` by reviewed SpecKit amendment.

## Parallel Workstreams

| Workstream | Tasks | Planned branch | Primary owner paths | Hard dependencies |
| --- | --- | --- | --- | --- |
| Governance/contracts | T000–T009 | `feature/step5c-contracts` after T004 | `specs/admin-ui/step5c-controlled-live-execution/contracts/**`, fixtures/evidence | ADR + SpecKit accepted/frozen |
| Controller | T010–T016 | `feature/step5c-controller` | new `delta-controller-python/**`; controller tests | T004; final review depends T009 |
| Worker adapter | T017–T022 | `feature/step5c-worker-adapter` | `delta-worker-python/src/deltatorrent/live_execution/**`, narrowly required runner/receipt tests | T004; final review depends T009 |
| Admin UI | T023–T028 | `feature/step5c-admin-ui-live` | `tools/admin-ui/src/modules/live-execution/**`, `tools/admin-ui/src/data/live-execution-port.ts`, explicit adapter/composition/test files (offline `data-source-port.ts` forbidden) | T004; final review depends T009 |
| Security | T029–T034 | `feature/step5c-security` | Step 5C threat fixtures/tests/evidence; no production semantics | T004; consumes frozen contracts |
| Integration | T035–T039 | `feature/step5c-e2e` | transport adapter + cross-component E2E/evidence only | review-clean controller/worker/UI/security |
| Qualification | T040–T044 | `release/step5c-qualification` | CI/evidence/checklists/docs only unless a reviewed defect fix is split to owner branch | integrated Step 5C candidate |

## Protected / Forbidden Paths for All Step 5C Branches

Unless formal-impact is reclassified and Feature 000 is reopened, no Step 5C branch may modify:

- `delta-core-cpp/**`
- `delta-runtime-cpp/**`
- `delta-ffi/**`
- `delta-node-java/**`
- `formal/**`
- `specs/000-formal-tla-spec/**`

No branch may add `STAGE_C_REAL_DRQ1` authority to local controlled execution.

## Cross-branch Ownership Rules

1. Shared contract changes originate only on `feature/step5c-contracts` or an RFC/SpecKit amendment branch.
2. Controller does not modify worker plugin/model semantics.
3. Worker adapter does not implement authentication, authorization policy, or browser transport.
4. Admin UI does not implement policy decisions, trusted identity, worker process invocation, shell commands, or receipt authority.
5. Security branch adds adversarial fixtures/tests and findings; production fixes return to the owning branch.
6. Integration branch may connect already-reviewed ports but may not redesign contracts silently.
7. A change touching another workstream's owned path requires a cross-owner review and task-map amendment before merge.

## Developer Handoff Template

Every developer assignment must include:

```text
Branch: <planned branch>
Base: <CONTRACT_FREEZE_SHA or required merged dependency SHA>
Tasks: step5c:Txxx–Tyyy
Allowed paths: <explicit list>
Forbidden paths: protected spine + other workstream owners
Required evidence: <tests/fixtures/CI artifacts>
Exit condition: PR review-clean; tasks remain unchecked until evidence independently verified
```

## Merge Discipline

- No direct merge from a developer branch without independent diff review.
- No task is marked `[x]` from narrative claims alone.
- PR description must enumerate exact Step 5C task IDs and evidence.
- If a dependency branch changes a frozen contract, affected branches stop, rebase only after the contract amendment is reviewed, and rerun all impacted gates.
