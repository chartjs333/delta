# Supplemental Runtime-Boundary Tasks

- [x] HR001 Classify the final code-bearing diff as `NONE`, `REFINEMENT_ONLY`, or `SEMANTIC`. Evidence: `evidence/final-formal-impact.json`.
- [x] HR002 Prove no build/runtime dependency points from Delta components to the UI. Evidence: `evidence/final-formal-impact.json`.
- [x] HR003 Prove the UI does not call C ABI/FFM transition entry points. Evidence: `evidence/final-formal-impact.json`.
- [x] HR004 Prove contribution/aggregate payloads remain opaque unless a public presentation contract exists. Evidence: `evidence/final-formal-impact.json`.
- [x] HR005 Verify adapter failures cannot affect node, worker, or native-runtime liveness. Evidence: `evidence/final-formal-impact.json`.
- [x] HR006 Verify schema ID/version/authority/document type/source are displayed and governance schemas are never substituted for Delta-canonical schemas. Evidence: `evidence/final-formal-impact.json`.
- [x] HR007 Verify client-visible payloads exclude secrets and restricted evidence. Evidence: `evidence/final-formal-impact.json`.
- [x] HR008 Re-run formal-impact review before adding any live command or state-changing endpoint. Evidence: `evidence/final-formal-impact.json`.
- [x] HR009 Verify the MVP performs no automatic network requests and has no backend or login dependency. Evidence: `evidence/final-formal-impact.json`.
- [x] HR010 Verify hostile local input limits and inert string/URL rendering from `threat-model.md`. Evidence: `evidence/final-formal-impact.json`.
- [x] HR011 Verify T032–T040 change presentation only and preserve `DataSourcePort`, offline, validation, and export boundaries. Evidence: `evidence/final-formal-impact.json`.
- [x] HR012 Verify no pairwise answer, evidence reference, completion count, or historical fixture is presented as an independence verdict. Evidence: `evidence/final-formal-impact.json`, `evidence/web-qa.json`.
- [x] HR013 STOP if dynamic-pair implementation requires a canonical schema, protocol validator, or runtime change. Evidence: `evidence/final-formal-impact.json` (`stop_rule_triggered=false`).

Completed MVP tasks retain their existing evidence. HR011–HR013 require new
machine-readable evidence in the later UX implementation branch.
