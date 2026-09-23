# PR 50 body draft — provisional until the one-shot diagnostic is sealed

## Scope

This PR continues the existing isolated-sidecar source line. It does not open a
second implementation line and does not run or claim an official profile-selection
campaign.

Current source remediation covers the reviewed native-authoritative RECORD_VOTE
refinement, POSIX durable-directory identity/rebind hardening, the mandatory SHM
publication path and crash qualification, and qualification-only diagnostic
instrumentation. The exact closure commit/tree and completed gate list must be
inserted only after all source changes and tests are final.

## Historical captures

The three prior comparison attempts remain immutable `INCOMPLETE` history. They
are neither deleted nor promoted. Their scheduler/allocation failure is not
relabelled as a runtime or Feature 010 failure.

## One-shot diagnostic

After source commit S is frozen, a later manifest commit M will preregister one
`DIAGNOSTIC_ONLY` campaign bound to S/tree(S), an exact pinned allocation, 100
offers/s, one fixed duration, and exactly one `EMBEDDED_FFM` lane followed by one
`ISOLATED_SIDECAR` lane. The diagnostic is assembler-ineligible.

Diagnostic status: **NOT RUN in this source draft**.

Root-cause classification: **PENDING SEALED EVIDENCE**. Replace this line only
with `ENVIRONMENT_INVALID`, `HARNESS_OR_TIMER_DEFECT`,
`GENUINE_RUNTIME_DEMAND_INDICATOR`, or `NO_MISSED_SLOTS_OBSERVED`. An
`INCONCLUSIVE` result blocks the source node and must not be guessed away.

## Authority and claims

- Official comparison: not run here; it requires source merge and fresh
  exact-source authority.
- Frozen offered rate: unchanged at 100/s.
- `selected_profile`: `null`.
- Gate A/B/C/D qualification: none claimed.
- `BenchmarkResultQC`: absent.
- Feature 010 GO: false.
- Feature 011 authority: false.

The PR body must be updated with the sealed diagnostic identity/classification and
exact source/evidence commits before final handoff. Diagnostic evidence cannot be
used as input to the official comparison assembler.
