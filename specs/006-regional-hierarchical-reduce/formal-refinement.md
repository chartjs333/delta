# Formal Proof/Refinement Obligations: 006 Hierarchical BFT Integer Reduce

This file is normative for `006-regional-hierarchical-reduce`.

## Theorem dependency

Every accepted `ReduceTopology` MUST instantiate PO-H1 and PO-H2 from the 000 theorem baseline:

- regional ticket sets are pairwise disjoint;
- their union equals the exact frozen ticket set for each domain;
- parameter shards form exact non-overlapping schema coverage;
- regional and global coefficients/scales/denominators match the APC/profile context;
- every regional product satisfies PO-A1 product bounds;
- every flat-or-composed accumulator satisfies PO-A2 accumulator bounds;
- every common-denominator numerator, reduced fraction and final rounding step satisfies every
  normative conjunct of PO-A3.

Only after these concrete preconditions verify may hierarchical result equality be inferred.

## Runtime precondition binding

The content-addressed topology proof instance MUST bind every theorem used by the runtime as a
separate checked obligation:

- **PO-A1** binds the declared input coefficient and q-value bounds to the multiplication width;
- **PO-A2** binds the maximum regional/global term counts, canonical accumulation order and
  intermediate accumulator width;
- **PO-A3** binds positive canonical denominators, common-denominator divisibility, numerator
  headroom and the exact deterministic rounding profile;
- **PO-H1** binds the exact disjoint ticket partition and complete domain/shard coverage;
- **PO-H2** may be invoked only after the PO-H1 partition and PO-A bounds above pass for the same
  topology, input, profile, proof and coefficient context.

A parent proof ID, theorem build or test vector alone is insufficient. The runtime validator must
check the concrete values, emit one PASS record per normative conjunct and content-address the full
precondition instance before any regional committee starts.

## Failure/refinement semantics

- Missing regional/global quorum follows soft view change and hard abort; no central or average-of-available-regions fallback.
- Post-ISC region/storage loss cannot remove/reweight tickets; repair exact bytes or abort.
- Regional/global partials bind one topology/input/profile/APC view and never enter P2P publication.
- Duplicate/replayed partials are idempotent; conflicts are rejected/evidence.
- Hierarchical execution traces must project regional/global parameter actions and terminal outcomes to the formal model.

## Exit evidence

1. machine-checked theorem build and exact topology proof instance;
2. bit-for-bit hierarchy/flat equality for the integration corpus;
3. overlap, gap, mixed-view, overflow and insufficient-quorum negative traces rejected;
4. partition/crash/restart traces accepted only under formal semantics;
5. hierarchy, overflow and partial-publication mutants remain detectable.

Any change to partition/composition or failure fallback semantics returns to branch 000 first.

## Feature-008 boundary

Feature 006 may materialize committee-local regional/global result vote bodies and quorum envelopes
needed for hierarchy execution tests. It MUST NOT claim completion of ISC, EC, APC,
ParameterShardQC, AggregateRootQC, ApplyQC or current-pointer transitions. Those certificate graph
and apply responsibilities remain in feature 008. A newly observable certificate terminal or
fallback not projected by the accepted formal vocabulary is `SEMANTIC` and stops this branch.
