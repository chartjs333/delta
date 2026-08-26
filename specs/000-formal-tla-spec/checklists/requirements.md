# Specification Quality Checklist: 000 Formal TLA+ Baseline

**Reviewed**: 2026-08-23  
**Status**: Ready for formal implementation; Formal GO not yet established

## Architectural scope

- [x] Formal verification is a mandatory predecessor, not a later test task.
- [x] TLA+/TLC and theorem-prover responsibilities are separated correctly.
- [x] State/action vocabulary spans ticketing through ApplyQC/current publication.
- [x] Permissioned/cryptographic abstractions and non-claims are explicit.
- [x] Later implementation refinement boundary is defined.

## Safety completeness

- [x] Quorum, vote persistence, commitment uniqueness and certificate parentage are covered.
- [x] AC-before-ISC, immutable freeze and seed ordering are covered.
- [x] Fixed-point/overflow, shard atomicity and aggregate completeness are covered.
- [x] Apply uniqueness/current certification and plane separation are covered.
- [x] Abort/current preservation and crash/replay idempotence are covered.

## Failure and recovery completeness

- [x] Soft timeout/view change and hard abort are distinct.
- [x] Proposer/validator crashes at durability boundaries are specified.
- [x] Network partition/quorum loss safety and liveness boundaries are explicit.
- [x] Pre/post-ISC storage loss, exact repair and irrecoverable abort are specified.
- [x] Seed, parameter, aggregate and apply failures have deterministic outcomes.
- [x] Epoch/key compromise and finalized-history behavior are specified.

## Mathematical proof completeness

- [x] Quorum intersection and conflicting-QC theorem are explicit.
- [x] Signed product, flat accumulator and rational denominator bounds are explicit.
- [x] Exact regional partition and hierarchy-flat equality are explicit.
- [x] Aggregate coverage and Apply/current uniqueness are explicit.
- [x] Runtime theorem precondition validation is mandatory.

## Model-checking quality

- [x] Mandatory f=1 scope and fault families are measurable.
- [x] Safety does not rely on synchrony.
- [x] Liveness assumptions/fairness are explicit and scoped.
- [x] State-explosion reductions require rationale/coverage.
- [x] Deliberately broken mutants and expected counterexamples prevent vacuity.

## Evidence and governance

- [x] Toolchains, configs, modules, proofs, traces and reports are pinned/content-addressed.
- [x] FormalVerificationReport has deterministic GO/NO_GO semantics.
- [x] Independent clean reproduction and two reviews are mandatory.
- [x] Formal semantic changes invalidate compatibility until a new GO.
- [x] No implementation task in 001–011 can begin without GO.

## Readiness decision

- [x] No unresolved `[NEEDS CLARIFICATION]` remains in the specification.
- [x] The tasks are executable without inventing failure or proof semantics.
- [x] The branch is ready for `/speckit.tasks` execution.
- [x] This checklist does not claim that the formal model/proofs have already been implemented or passed.
