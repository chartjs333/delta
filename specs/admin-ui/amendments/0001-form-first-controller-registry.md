# Amendment 001: Form-first Controller Registry

- **Status**: Reviewed
- **Date**: 2026-09-14
- **Base implementation**: `feature/admin-ui-mvp` at Web-QA-fixed commit
  `ed47c7d600655513a3e7ebcda3cebf37c71d7aca`
- **Formal impact**: `NONE`

## Decision

The default controller-register experience is a guided form for non-technical users.
JSON remains the internal, import, advanced-preview, validation, and export format;
manual JSON editing is not required. Advanced JSON is hidden by default and read-only.

The workflow is:

`Guided form → Presentation model → DocumentDraft → JSON Schema validation → Export JSON`

T032–T039 change presentation and interaction design only. They preserve the current
`DataSourcePort`, offline execution, structural-validation authority boundary,
threat controls, and explicit download of a new file.

## Pairwise clarification

The guided pairwise step records three tri-state answers and evidence references.
It never produces an independence verdict. The summary reports structural completion,
for example "6 of 6 pairwise records filled". "Verified", "confirmed", "approved",
"pass", "fail", and equivalent claims require an external `SourcedResult` with
matching subject binding and provenance.

The structural draft contract and stale/orphaned lifecycle are defined in
`../contracts/pairwise-review-draft.md`. The frozen PR #29 worksheet is historical
test input and does not define this dynamic presentation model.

## STOP rule

Stop implementation and re-enter formal-first review if this UX requires a canonical
schema, canonical validator, protocol transition/result, runtime change, or semantic
independence rule. A UI-owned `LOCAL_FIXTURE` structural mapping may be reviewed
separately, but it cannot claim governance or Delta authority.

## Verification gate

- production-browser checks at supported desktop and mobile widths;
- strict CSP execution without `unsafe-eval`;
- keyboard and assistive-technology navigation;
- non-technical form-to-export usability;
- unknown-field preservation;
- dynamic pair cardinality and identity-mutation lifecycle tests;
- search/assertion proving no local verdict language or promotion.
