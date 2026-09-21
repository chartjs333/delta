# Implementation Plan: Reconciled Feature 010 Qualification

**Historical reconciliation**: `ac0e54ffbab4b9a5c20945b17ede2930b78ff080`
**Foundation implementation**: `6054e35ed627392172f94c2a90dfb7d799d5251e`
**Foundation tree**: `0640a117aba6772b7c0b22ec9cdaa047e507e1d5`
**Formal impact**: `NO_SEMANTIC_CHANGE` / `REFINEMENT_ONLY`
**Current result**: `FOUNDATION_COMPLETE`; `STOPPED_BEFORE_PRIMARY_EXECUTION`

## Constitution checks

**Pre-implementation check — PASS for foundation scope.** The exact accepted
Formal GO/report and merged Feature 009 predecessor verify. The foundation is
bound to one immutable implementation commit and adds benchmark-only contracts,
fixtures, plans and offline verification with no runtime/protocol semantic change.

**Foundation candidate check — PASS/STOP.** Protected formal/native/FFI/Java
paths are zero, Formal GO still verifies, historical NO_GO/STOP states remain
unchanged, and the candidate deliberately produces no GO, observation, execution
authorization or runtime authority. The exact-head foundation verifier is
mandatory after the evidence overlay is committed.

## Summary

Publish the current-lineage foundation and immutable zero-authority evidence.
Resume qualifying execution only when T028/HR010-004 and later gates plus the
missing independent governance, physical scientific environment, and approved
real-WAN resources are satisfied. Historical drafts supply audit facts and design
lessons, never authority or a merge base.

## Sequence

1. **Reconcile authority** — inventory the named historical refs, confirm the exact
   working-version base/formal report, retain current-main code only, and propose
   this SpecKit plus machine-readable status for review and merge.
2. **Close governance externally** — adopt an exact custody policy; appoint four
   independent controllers; verify all owner/key bindings and pair reviews; freeze
   the validator set; collect and verify both three-signature bootstrap quorums.
3. **Implement the current-lineage benchmark foundation — complete for
   T001–T027 and HR010-001–003 only** — schemas, benchmark-governance QCs,
   fixture-only planners/adapters, polyglot stage-receipt contracts, deterministic
   fault/attack fixtures, immutable evidence graph and negative tests. Historical
   implementations are design input only and are not copied wholesale.
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

Steps 2 and 4–9 cannot complete in the present assignment. Step 3's bounded
foundation slice is complete; T028/HR010-004 are the next qualifying STOP. The
host has a physical
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
- verify `evidence/foundation-status.json`, its task/formal companions and the
  immutable implementation tree with `scripts/verify_foundation_status.py`;
- run the foundation-status mutation tests and exact preflight;
- run `git diff --check` and JSON parsing;
- run the canonical formal gate because these are numbered-feature artifacts;
- prove the diff is empty for `formal/**`, `delta-core-cpp/**`,
  `delta-runtime-cpp/**`, `delta-ffi/**`, and `delta-node-java/**`;
- require two independent exact-head/governance reviews before merge or any later
  implementation/execution node.

## Exit gate

The foundation evidence overlay may merge as an authoritative foundation-only
checkpoint. It is not Feature 010 GO and cannot authorize execution. Scientific
work resumes only from a separately reviewed current-lineage candidate satisfying
every prerequisite in `spec.md`, beginning with T028/HR010-004.
