# Formal Proof/Refinement Obligations: 006 Hierarchical BFT Integer Reduce

This file is normative for `006-regional-hierarchical-reduce`.

## Theorem dependency

Every accepted `ReduceTopology` MUST instantiate PO-H1 and PO-H2 from the 000 theorem baseline:

- regional ticket sets are pairwise disjoint;
- their union equals the exact frozen ticket set for each domain;
- parameter shards form exact non-overlapping schema coverage;
- regional and global coefficients/scales/denominators match the APC/profile context;
- composed intermediate/final accumulator bounds satisfy PO-A1–PO-A3.

Only after these concrete preconditions verify may hierarchical result equality be inferred.

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
