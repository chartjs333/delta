# Formal Regression Obligations: 010 WAN/BFT/Quality Benchmark

This file is normative for `010-wan-benchmark-and-quality`.

## Benchmark identity

`BenchmarkDefinition` MUST bind the exact compatible `FormalVerificationReport`, `formal_semantics_id`, theorem/proof build IDs, formal trace schema and implementation refinement evidence from features 003–009.

## Mandatory formal regression gate

Before scientific/performance GO can be evaluated:

1. rerun every mandatory TLA+ safety config affected by the implementation/source/profile identity;
2. rerun liveness configs under the benchmark's exact quorum/availability/eventual-synchrony assumptions;
3. rebuild all mandatory theorem artifacts and validate the concrete fixed-point/hierarchy/apply proof instances;
4. rerun expected mutants and confirm their counterexamples remain detected;
5. project representative/full protocol attack, crash/recovery and successful-run traces and validate refinement;
6. verify no benchmark configuration enables adaptive H, stale acceptance, float consensus fallback, weaker certificate policy or manual current-state override.

## Decision rule

Any failed/missing/incompatible formal artifact or refinement result is a mandatory benchmark gate failure and forces `BenchmarkResultQC(decision=NO_GO)`. Quality or efficiency success cannot override it.

## Attack mapping

The conflicting-vote, seed-before-ISC, mutable availability/input, Frankenstein shard, incomplete aggregate, unchecked overflow, conflicting ApplyQC, current-without-ApplyQC and certificate-downgrade scenarios MUST map to their named 000 invariants/mutants and produce the expected rejection/abort traces.

## Evidence

The evidence graph records formal source/tool/config/proof/report IDs, explored property results, theorem concrete instances, mutant outcomes, projected trace hashes and compatibility decision. Mutable dashboards or prose summaries are not authoritative.
