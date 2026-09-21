# Implementation Plan: Reconciled Feature 010 Qualification

**Base**: `7a9faf852e0ccae4d25fdc363fbf39ecf1719341`
**Formal impact**: `NONE`
**Current result**: `STOPPED_BEFORE_PRIMARY_EXECUTION`

## Constitution checks

**Pre-implementation check — PASS for reconciliation scope.** The exact accepted
Formal GO/report and merged Feature 009 predecessor verify; the planned diff is
documentation plus a fail-closed status verifier, with no runtime/protocol change.
Feature 010 implementation and execution remain closed at T001.

**Final candidate check — PASS/STOP.** The actual diff is limited to Feature
010/011 SpecKit and `HYBRID-RUNTIME-MAP.md`; protected formal/native/FFI/Java
paths are zero, Formal GO still verifies, all historical NO_GO/STOP states remain
unchanged, and the candidate deliberately produces no GO, observation or runtime
authority. A sealed verifier run after commit is mandatory before handoff.

## Summary

First publish the current-lineage SpecKit and immutable STOP evidence. Resume only
when the missing independent governance, physical scientific environment, and
approved real-WAN resources exist. Historical drafts supply audit facts and design
lessons, never authority or a merge base.

## Sequence

1. **Reconcile authority** — inventory the named historical refs, confirm the exact
   working-version base/formal report, retain current-main code only, and propose
   this SpecKit plus machine-readable status for review and merge.
2. **Close governance externally** — adopt an exact custody policy; appoint four
   independent controllers; verify all owner/key bindings and pair reviews; freeze
   the validator set; collect and verify both three-signature bootstrap quorums.
3. **Implement the current-lineage benchmark foundation** — implement T001–T034
   and HR010-001–014: schemas, QCs, current-lineage runner, analyzers, polyglot
   stage receipts, fault harness, immutable evidence graph and negative tests.
   Historical implementations are design input only and are not copied wholesale.
4. **Freeze current-lineage execution identity** — produce a reviewed Benchmark
   Definition, model/data/evaluator/ticket/runtime identities, missing-run policy,
   stage plans, and separate Definition/execution authorizations.
5. **Qualify exact source** — run canonical cross-language, compiler, sanitizer,
   TSan, fuzz, WAL/replay, Netty, and deployment-profile gates on that exact tree.
6. **Execute scientific gates** — run every preregistered seed and token/domain-
   matched arm through the bound Python → Java/Netty → native/WAL path using the
   pinned physical CUDA environment. No ad-hoc dependency, threshold, or
   observation substitution is permitted.
7. **Execute simulated network gates** — label every local/netem output `SIMULATED`;
   complete P2P, churn, fault, recovery, and accounting gates.
8. **Execute approved real-WAN gates** — only after the earlier gates pass and the
   independent endpoint/TLS/credential inventory is approved.
9. **Seal the result** — verify the full evidence graph offline, obtain evaluator
   quorum, publish `BenchmarkResultQC`, and create
   `FEATURE010_GO_CHECKPOINT_SHA` only for genuine GO.

## Current STOP

Steps 2–9 cannot complete in the present assignment. Step 3 additionally requires
reviewed implementation work absent from the current base. The host has a physical
8 GiB NVIDIA GPU, while the current worktree resolves the pinned Worker environment
to CPU-only PyTorch. A separate local CUDA environment and model cache exist, but
they are untracked, not bound to this current-lineage definition, and the required
WikiText/LAMBADA/HellaSwag datasets are absent. There is no authoritative controller
set with available matching custodial private keys, bootstrap quorum, execution
authority, repository secret/variable inventory for remote resources, or approved
real-WAN topology.

No scientific or network benchmark was started. This is a required fail-closed
outcome, not a test failure.

## Validation strategy

- verify `evidence/reconciliation-status.json` with
  `scripts/verify_reconciliation_status.py`;
- run its pytest contract;
- run `git diff --check` and JSON parsing;
- run the canonical formal gate because these are numbered-feature artifacts;
- prove the diff is empty for `formal/**`, `delta-core-cpp/**`,
  `delta-runtime-cpp/**`, `delta-ffi/**`, and `delta-node-java/**`;
- require two independent exact-head/governance reviews before merge or any later
  implementation/execution node.

## Exit gate

The reconciliation PR may merge as an authoritative STOP/requirements package. It
is not a Feature 010 GO. Scientific work resumes only from a separately reviewed
current-lineage candidate satisfying every prerequisite in `spec.md`.
