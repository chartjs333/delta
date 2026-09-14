# Tasks: Extensible Delta Admin UI

**Input**: `spec.md`, `plan.md`, project constitution, formal baseline, runtime map,
and PR #29 as a non-normative MVP input.

## Format

`- [ ] T### [P?] [US#?] Action with exact path`

## Phase 1: Specification setup

- [x] T001 Add the reviewed Spec Kit under `specs/admin-ui/` only. Evidence: `evidence/spec-kit-manifest.json`.
- [x] T002 Record the exact main commit and accepted formal semantics ID reviewed. Evidence: `evidence/spec-baseline.json`.
- [x] T003 Link the exact PR #29 revision used as the non-normative controller fixture. Evidence: `evidence/spec-baseline.json`.
- [ ] T004 Resolve the canonical schema ID/version used for MVP structural validation.

## Phase 2: Foundational decisions

- [ ] T005 Write a technology ADR without weakening `spec.md` requirements.
- [ ] T006 Define the extension composition root inside the future `tools/admin-ui/`.
- [ ] T007 Define the implementation-level `DataSourcePort` from `contracts/data-source-port.md`.
- [ ] T008 Define typed errors, authority classes, source descriptors, and sourced-result envelopes.
- [ ] T009 Decide whether local save overwrites a selected file or always creates an export.

## Phase 3: Local document workflow

- [ ] T010 [US1] Implement local JSON open/create under `tools/admin-ui/`.
- [ ] T011 [US1] Implement canonical schema selection and structural validation.
- [ ] T012 [US1] Implement lossless editing/export for allowed unknown fields.
- [ ] T013 [US1] Add dynamic controller list/detail views with no slot-count assumption.
- [ ] T014 [US1] Test 0, 1, 4, 100+, invalid, and forward-compatible controller documents.

## Phase 4: Capabilities and provenance

- [ ] T015 [US2] Implement source capability discovery and unavailable states.
- [ ] T016 [US2] Implement authority/provenance presentation for sourced results.
- [ ] T017 [US2] Reject promotion of arbitrary local result-looking fields to trusted verdicts.
- [ ] T018 [US2] Test unavailable, unsupported, stale, malformed, and subject-mismatch results.

## Phase 5: Extension points and adapter substitution

- [ ] T019 [US3] Register a placeholder domain module through the composition root.
- [ ] T020 [US3] Register an alternate entity view without controller-module changes.
- [ ] T021 [US4] Add a second test adapter implementing the same contract.
- [ ] T022 [US4] Run the shared adapter contract suite against both adapters.

## Final Phase: Validation and documentation

- [ ] T023 Prove Delta core/runtime builds and tests do not require the UI.
- [ ] T024 Verify no reverse dependency from Delta core/runtime to `tools/admin-ui/`.
- [ ] T025 Complete accessibility and primary-state checks.
- [ ] T026 Record final formal-impact review and machine-readable evidence.
- [ ] T027 Document opt-in startup, disablement, and rollback.

## Dependencies

- T001–T004 precede implementation.
- T005–T009 precede T010–T022.
- T010–T014 precede controller-specific MVP acceptance.
- T015–T018 precede display of any sourced assessment/result.
- T023–T027 precede promotion.

## Implementation Strategy

Deliver the local/offline workflow first. Do not mock a future Delta API into the
product contract and do not implement protocol/governance verdicts in the UI.

## Exit Gate

Every completed task requires machine-readable evidence. A code-bearing branch
must remain `NONE` under final formal-impact review; otherwise work stops and follows
the project's formal-first process.
