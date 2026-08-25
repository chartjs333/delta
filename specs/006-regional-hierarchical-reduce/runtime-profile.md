# Runtime Profile: 006 Regional Hierarchical Reduce

**Primary runtime**: C++ regional/global integer committees  
**Transport runtime**: Java regional routing and bounded streams  
**Formal impact**: `REFINEMENT_ONLY` with PO-H1/PO-H2 concrete instantiation

## Responsibility split

C++ validates topology, exact ticket/domain/shard coverage, coefficients, profile/proof roots and committee QCs. It computes regional integer partials and global sums.

Java routes canonical worker/regional/global frames, applies transport backpressure and collects telemetry. Java cannot:

- average regional outputs;
- exclude a region or ticket after freeze;
- substitute a committee;
- choose coefficients;
- mark a partial finalized;
- publish a partial through P2P.

## Exact topology proof

For every round, concrete evidence must establish:

- each frozen ticket belongs to exactly one regional set;
- regional sets are disjoint and their union is exact per domain;
- parameter shards cover the required schema exactly once;
- regional/global coefficient, denominator and accumulator bounds match one APC/profile view.

Only then may PO-H2 justify hierarchy-flat equality.

## Runtime flow

```text
Java route → native command → verify lineage/topology
→ checked regional/global sum → native WAL/QC commit
→ canonical effect → Java route
```

Every committee mutating path follows the feature-003 single-writer and persist-before-expose contract.

## Failure behavior

Missing regional/global quorum triggers native view/deadline handling and eventual certified abort. Java transport cannot fall back to “available regions only.” Post-ISC artifact loss uses exact-ID repair or abort; membership and weights remain immutable.

## Exit additions

- C++ hierarchical bytes match flat C++ oracle exactly;
- theorem preconditions are materialized for the actual topology;
- Java message arrival/parallelism changes no output;
- committee crash/restart/quorum traces refine formal behavior;
- partial media types cannot enter Java P2P publisher;
- cross-region byte/message evidence is measured without changing mathematics.
