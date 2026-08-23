# DeltaReduce formal verification workspace

This directory is reserved for implementation of `specs/000-formal-tla-spec`.

No Formal GO has been established merely by creating the specification branch. The formal stage is complete only when the checked-in TLA+/TLC models, Lean proofs, mutants, trace fixtures and content-addressed `FormalVerificationReport(decision=GO)` satisfy the feature exit gate.

Planned layout:

```text
formal/
  tla/          # executable protocol, failure/recovery and refinement modules
  proofs/       # machine-checked parametric theorems
  schemas/      # canonical trace and report contracts
  fixtures/     # legal/illegal traces and expected counterexamples
  scripts/      # reproducible invocation, normalization and verification
  reports/      # generated evidence manifests and final decision
  toolchain/    # pinned/checksummed formal dependencies
```

Implementation branches `001–011` remain blocked until the exact compatible GO report exists.
