# Supplemental Runtime-Boundary Tasks

- [ ] HR001 Classify the final code-bearing diff as `NONE`, `REFINEMENT_ONLY`, or `SEMANTIC`.
- [ ] HR002 Prove no build/runtime dependency points from Delta components to the UI.
- [ ] HR003 Prove the UI does not call C ABI/FFM transition entry points.
- [ ] HR004 Prove contribution/aggregate payloads remain opaque unless a public presentation contract exists.
- [ ] HR005 Verify adapter failures cannot affect node, worker, or native-runtime liveness.
- [ ] HR006 Verify canonical schema IDs/versions are displayed and not forked by UI-owned copies.
- [ ] HR007 Verify client-visible payloads exclude secrets and restricted evidence.
- [ ] HR008 Re-run formal-impact review before adding any live command or state-changing endpoint.

Completion requires machine-readable evidence in the implementation branch. These
tasks are intentionally open in the specification branch.
