# DeltaReduce v1 formal-first Spec Kit roadmap

## Branch topology

Branches are stacked. Each authoritative branch adds only its own specification directory and uses the previous authoritative feature head as parent.

| Order | Branch | Base | Primary exit gate |
| ---: | --- | --- | --- |
| 0 | `000-formal-tla-spec` | `main` | TLC safety/liveness models, parametric proofs, counterexample mutants and Formal GO |
| 1 | `001-reproducible-training-baseline` | `000-formal-tla-spec` | Formal GO verified; deterministic local reference and offline WAN tests |
| 2 | `002-local-round-engine` | `001-reproducible-training-baseline` | Parent minus final local delta reconstructs worker state |
| 3 | `003-bft-round-state-machine` | `002-local-round-engine` | Implementation traces refine TLA+; four aggregators produce identical hashes for 100 tickets |
| 4 | `004-compressed-delta-protocol` | `003-bft-round-state-machine` | Canonical fixed-point shards and machine-checked accumulator proof pass boundary corpus |
| 5 | `005-content-addressed-p2p-distribution` | `004-compressed-delta-protocol` | Certified object download survives initial-seed loss without violating formal availability semantics |
| 6 | `006-regional-hierarchical-reduce` | `005-content-addressed-p2p-distribution` | Hierarchical integer result is formally and empirically equal to flat reference |
| 7 | `007-domain-pure-ticket-scheduling` | `006-regional-hierarchical-reduce` | Deterministic fixed-ticket plan preserves configured domain quotas and lease safety |
| 8 | `008-certificates-and-consensus` | `007-domain-pure-ticket-scheduling` | Certificate implementation refines parent graph; Frankenstein shard rejected; ApplyQC unique |
| 9 | `009-qlora-8gb-mode` | `008-certificates-and-consensus` | Frozen base and certified adapter-only 8 GB reference run |
| 10 | `010-wan-benchmark-and-quality` | `009-qlora-8gb-mode` | Preregistered quality, BFT, WAN, determinism and formal-regression gates pass |
| 11 | `011-multiregion-pilot` | `010-wan-benchmark-and-quality` | Compatible Formal GO and Benchmark GO; 20–50-worker pilot yields signed decision evidence |

## Superseded branches

These refs are historical only and MUST NOT be used as bases:

| Legacy ref | Replaced by | Reason |
| --- | --- | --- |
| `003-central-round-coordinator` | `003-bft-round-state-machine` | Central authority is incompatible with BFT replicated state. |
| `007-adaptive-heterogeneous-scheduling` | `007-domain-pure-ticket-scheduling` | Adaptive `H_i` and stale weighting are forbidden. |
| `008-permissioned-trust-and-resilience` | `008-certificates-and-consensus` | Identity-only resilience is insufficient; explicit certificate/QC lineage is mandatory. |

## Execution protocol

1. Implement and validate `000-formal-tla-spec` first.
2. Do not begin any code-bearing branch without exact compatible `FormalVerificationReport(decision=GO)`.
3. Implement and validate one subsequent authoritative branch at a time.
4. Run Spec Kit cross-artifact and formal-impact analysis before code and after any amendment.
5. Use task IDs in commits and keep `tasks.md`, traceability and formal evidence current.
6. Merge/promote only after feature and affected formal gates pass.
7. Stop on any model, theorem, refinement, certificate, arithmetic, determinism or quality failure; never bypass it with a later feature.

## Formal baseline obligations

- **F-SAFETY**: no conflicting finalized config, ISC, EC, APC, shard QC, aggregate root or ApplyQC under `n=3f+1`, quorum `2f+1`, honest no-double-vote.
- **F-FREEZE**: inputs and ticket/domain parameters cannot change after their certified freeze points; no valid seed exists before ISC.
- **F-AVAIL**: only AC-covered inputs enter ISC; post-ISC loss triggers repair or safe abort, never membership rewrite.
- **F-ATOMIC**: AggregateRootQC covers every required domain×shard once and cannot mix parent views.
- **F-APPLY**: only one ApplyQC/current checkpoint per aggregate/height; abort/recovery preserves the parent.
- **F-RECOVERY**: journal replay, duplicate messages and crash/restart are idempotent and cannot create a second vote/transition.
- **F-LIVENESS**: progress is conditional on eventual synchrony, honest quorum, artifact availability and fairness; outside assumptions only safety is required.
- **F-ARITH**: accumulator bounds, hierarchical-flat equality and exact rational/fixed-point composition are parametrically proved.
- **F-PLANES**: local/partial artifacts never become distribution objects.

## Cross-feature invariants

- A ticket names one domain, immutable data range, fixed `B`, fixed `H`, parent checkpoint and arithmetic profile.
- Worker speed can affect admission or ticket count before freeze, never the domain mixture or certified scalar weight.
- One `ticket_id` maps to at most one commitment root.
- Shards become eligible only after availability certification.
- Exact inputs are frozen before `ρ_t` exists.
- Consensus clipping, weighting and summation use canonical integer/rational arithmetic; floating addition is prohibited.
- Fixed-point headroom is proven for the worst-case eligible set before aggregation and revalidated for actual APC coefficients.
- Every parameter shard QC references one ISC/EC/APC view; `AggregateRootQC` atomically binds the complete shard set.
- One aggregate root can finalize at most one `ApplyQC`.
- Only certified global immutable objects enter P2P distribution.
- Network operations are idempotent, timeout-bounded and replay-protected.
- Permissioned identity is mandatory through the pilot.

## Deferred research

- permissionless participation, Sybil resistance and economic incentives;
- privacy-preserving secure aggregation and zero-knowledge proof of training;
- adaptive/local-staleness policies, unless a future constitutional amendment reintroduces them;
- advanced sparse/low-rank codecs that cannot satisfy canonical fixed-point proofs;
- WAN tensor/sequence parallelism, distributed MoE and block-local objectives;
- full dense multi-billion pretraining on isolated 8 GB GPUs.
