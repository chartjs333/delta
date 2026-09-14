# Tasks: Extensible Delta Admin UI

**Input**: `spec.md`, `plan.md`, project constitution, formal baseline, runtime map,
and PR #29 as a non-normative MVP input.

## Format

`- [ ] T### [P?] [US#?] Action with exact path`

## Phase 1: Specification setup

- [x] T001 Add the reviewed Spec Kit under `specs/admin-ui/` only. Evidence: `evidence/spec-kit-manifest.json`.
- [x] T002 Record the exact main commit and accepted formal semantics ID reviewed. Evidence: `evidence/spec-baseline.json`.
- [x] T003 Link the exact PR #29 revision used as the non-normative controller fixture. Evidence: `evidence/spec-baseline.json`.
- [x] T004 Replace the invalid single-canonical-schema assumption with authority-classed `SchemaDescriptor` and distinct governance/protocol document types. Evidence: `evidence/spec-decisions.json`.

## Phase 2: Foundational decisions

- [x] T005 Write and accept the browser-local TypeScript/React/Vite MVP ADR without weakening `spec.md`. Evidence: `adr/0001-browser-local-react-vite.md`, `evidence/spec-decisions.json`.
- [x] T006 Define the extension composition root inside the future `tools/admin-ui/`. Evidence: `evidence/implementation-tasks.json`.
- [x] T007 Define the implementation-level `DataSourcePort` from `contracts/data-source-port.md`. Evidence: `evidence/implementation-tasks.json`.
- [x] T008 Define typed errors, authority classes, source descriptors, and sourced-result envelopes. Evidence: `evidence/implementation-tasks.json`.
- [x] T009 Require explicit export/download of a new file and prohibit automatic source overwrite. Evidence: `evidence/spec-decisions.json`.
- [x] T028 Freeze the exact PR #29 worksheet bytes under future `tools/admin-ui/` test data with source commit, path, Git blob SHA, and SHA-256 metadata; never read the live PR at runtime. Evidence: `evidence/implementation-tasks.json`.
- [x] T029 Add hostile-input guards and tests for every mandatory limit in `threat-model.md`. Evidence: `evidence/implementation-tasks.json`.
- [x] T030 Prove the browser-local MVP has no backend, login, credential flow, analytics payload, or automatic network request. Evidence: `evidence/implementation-tasks.json`.
- [x] T031 Add contract tests that reject schema authority/document-type mismatch and external `$ref` resolution. Evidence: `evidence/implementation-tasks.json`.

## Phase 3: Local document workflow

- [x] T010 [US1] Implement local JSON open/create under `tools/admin-ui/`. Evidence: `evidence/implementation-tasks.json`.
- [x] T011 [US1] Implement authority-classed schema selection and structural validation. Evidence: `evidence/implementation-tasks.json`.
- [x] T012 [US1] Implement lossless editing/export for allowed unknown fields. Evidence: `evidence/implementation-tasks.json`.
- [x] T013 [US1] Add dynamic controller list/detail views with no slot-count assumption. Evidence: `evidence/implementation-tasks.json`.
- [x] T014 [US1] Test 0, 1, 4, 100+, invalid, and forward-compatible controller documents. Evidence: `evidence/implementation-tasks.json`.

## Phase 4: Capabilities and provenance

- [x] T015 [US2] Implement source capability discovery and unavailable states. Evidence: `evidence/implementation-tasks.json`.
- [x] T016 [US2] Implement authority/provenance presentation for sourced results. Evidence: `evidence/implementation-tasks.json`.
- [x] T017 [US2] Reject promotion of arbitrary local result-looking fields to trusted verdicts. Evidence: `evidence/implementation-tasks.json`.
- [x] T018 [US2] Test unavailable, unsupported, stale, malformed, and subject-mismatch results. Evidence: `evidence/implementation-tasks.json`.

## Phase 5: Extension points and adapter substitution

- [x] T019 [US3] Register a placeholder domain module through the composition root. Evidence: `evidence/implementation-tasks.json`.
- [x] T020 [US3] Register an alternate entity view without controller-module changes. Evidence: `evidence/implementation-tasks.json`.
- [x] T021 [US4] Add a second test adapter implementing the same contract. Evidence: `evidence/implementation-tasks.json`.
- [x] T022 [US4] Run the shared adapter contract suite against both adapters. Evidence: `evidence/implementation-tasks.json`.

## Final Phase: Validation and documentation

- [x] T023 Prove Delta core/runtime builds and tests do not require the UI. Evidence: `evidence/implementation-tasks.json`.
- [x] T024 Verify no reverse dependency from Delta core/runtime to `tools/admin-ui/`. Evidence: `evidence/implementation-tasks.json`.
- [x] T025 Complete accessibility and primary-state checks. Evidence: `evidence/implementation-tasks.json`.
- [x] T026 Record final formal-impact review and machine-readable evidence. Evidence: `evidence/final-formal-impact.json`, `evidence/implementation-tasks.json`.
- [x] T027 Document opt-in startup, disablement, and rollback. Evidence: `evidence/implementation-tasks.json`, `../../tools/admin-ui/README.md`.

## UX Amendment 001: Form-first controller registry

- [x] T032 [US1] Add the guided editor in `tools/admin-ui/src/modules/controllers/ControllerRegistryForm.tsx` and patch helpers in `tools/admin-ui/src/editor/document-draft.ts`; do not change `DataSourcePort`. Evidence: `evidence/implementation-tasks.json`.
- [x] T033 [US5] Implement non-verdict answer/evidence entry in `tools/admin-ui/src/modules/controllers/PairwiseReviewStep.tsx` and `tools/admin-ui/src/modules/controllers/pairwise-review-draft.ts` from `contracts/pairwise-review-draft.md`. Evidence: `evidence/implementation-tasks.json`.
- [x] T034 [US5] Add `tools/admin-ui/src/modules/controllers/ReadinessSummary.tsx` using wording such as "6 of 6 pairwise records filled"; reserve verified/confirmed/approved/pass/fail for matching sourced results. Evidence: `evidence/implementation-tasks.json`.
- [x] T035 [US1] Add friendly field mapping in `tools/admin-ui/src/components/FriendlyValidationPanel.tsx` while retaining machine JSON path, schema path, and constraint in accessible details. Evidence: `evidence/implementation-tasks.json`.
- [x] T036 [US1] Add a hidden-by-default, read-only projection at `tools/admin-ui/src/components/AdvancedJsonView.tsx` over the same `DocumentDraft`. Evidence: `evidence/implementation-tasks.json`.
- [x] T037 [US1] Add production-browser coverage under `tools/admin-ui/tests/browser/` and non-technical form-to-export coverage in `tools/admin-ui/src/app/form-first-usability.test.tsx`. Evidence: `evidence/implementation-tasks.json`.
- [x] T038 [US1] Prove unknown-field preservation and explicit-new-file behavior in `tools/admin-ui/src/editor/document-draft.form-roundtrip.test.ts`. Evidence: `evidence/implementation-tasks.json`.
- [x] T039 [US5] Test stable pair keys and `STALE`/`ORPHANED` lifecycle in `tools/admin-ui/src/modules/controllers/pairwise-review-draft.test.ts` without evidence retargeting. Evidence: `evidence/implementation-tasks.json`.

## Dependencies

- T001–T004 precede implementation.
- T005–T009 and T028–T031 precede T010–T022 acceptance.
- T010–T014 precede controller-specific MVP acceptance.
- T015–T018 precede display of any sourced assessment/result.
- T023–T027 precede promotion.
- The Web QA CSP/AJV and mobile-navigation fix precedes T032–T039 implementation.
- T032–T036 and the pairwise draft contract precede T037–T039 acceptance.
- Any required canonical schema, validator, protocol, or runtime change triggers STOP.

## Implementation Strategy

Deliver the local/offline workflow first. Do not mock a future Delta API into the
product contract and do not implement protocol/governance verdicts in the UI.
Implement T032–T039 only in the presentation layer over `DocumentDraft`; preserve
`DataSourcePort`, offline mode, structural validation, and explicit export.

## Exit Gate

Every completed task requires machine-readable evidence. A code-bearing branch
must remain `NONE` under final formal-impact review; otherwise work stops and follows
the project's formal-first process.
