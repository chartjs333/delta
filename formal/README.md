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

## Implemented verification baseline

The executable model covers replicated quorum state, durable vote recovery,
immutable tickets and commitments, availability and exact-ID repair, the
ISC→seed→EC/APC certificate graph, checked integer parameter reduction,
complete aggregate roots, ApplyQC/current-pointer recovery, certified
publication, partitions, view change and certified abort. `DeltaReduce.tla`
composes the complete transition system; focused harnesses keep mandatory TLC
scopes finite and auditable.

The mandatory model matrix contains ten safety configs and one liveness config.
It includes the required `f=1` scope with four validators, at least three
tickets, two domains and two shards. Required action coverage is fail-closed,
and the retained evidence explicitly reports states, distinct states, diameter
and observed terminal outcome classes. No safety config relies on synchrony,
symmetry reduction or a state constraint.

Lean 4.32.1/mathlib 4.32.1 discharges PO-Q1 through PO-R2, with concrete f=1,
INT64, INT128 and topology instantiations. The proof gate rejects `sorry`,
`admit`, user-declared axioms, unpinned dependencies and unexpected kernel
axioms. TLC finite-state results and Lean parametric results remain separate
evidence classes.

Ten weakening mutants must produce their intended counterexamples. Seven legal
and sixteen illegal action-labelled trace fixtures are checked against the
published `formal_semantics_id`. The final report generator is deterministic
and fail-closed: until a clean offline Linux reproduction and two genuine
independent reviews bound to the exact source commit and semantics ID are
present, it records `decision=NO_GO` and keeps branches `001–011` blocked.

## Reproduction

```text
python formal/toolchain/verify_locks.py --require-cache
make formal-parse formal-safety formal-liveness formal-proofs
make formal-mutants formal-refinement
python formal/scripts/collect_tlc_evidence.py
python formal/scripts/analyze_formal_consistency.py
python formal/scripts/generate_formal_report.py
python formal/scripts/verify_formal_report.py formal/reports/formal-verification-report.json
```

`make formal-report` additionally requires a deterministic `GO`; it is expected
to fail closed while either mandatory independent review is absent.
