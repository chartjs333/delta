# DeltaReduce v1 Spec Kit roadmap

## Branch topology

Branches are stacked. Each authoritative branch adds only its own specification directory and uses the previous authoritative feature head as parent.

| Order | Branch | Base | Primary exit gate |
| ---: | --- | --- | --- |
| 1 | `001-reproducible-training-baseline` | `main` | Deterministic local reference and offline WAN tests |
| 2 | `002-local-round-engine` | `001-reproducible-training-baseline` | Parent minus final local delta reconstructs worker state |
| 3 | `003-bft-round-state-machine` | `002-local-round-engine` | Four independent aggregators produce bit-identical hashes for 100 tickets |
| 4 | `004-compressed-delta-protocol` | `003-bft-round-state-machine` | Canonical fixed-point shards and accumulator proof pass boundary corpus |
| 5 | `005-content-addressed-p2p-distribution` | `004-compressed-delta-protocol` | Certified object download survives initial-seed loss |
| 6 | `006-regional-hierarchical-reduce` | `005-content-addressed-p2p-distribution` | Hierarchical integer result equals flat integer reference bit-for-bit |
| 7 | `007-domain-pure-ticket-scheduling` | `006-regional-hierarchical-reduce` | Deterministic fixed-ticket plan preserves configured domain quotas |
| 8 | `008-certificates-and-consensus` | `007-domain-pure-ticket-scheduling` | Frankenstein shard rejected; full certificate chain and ApplyQC finalize once |
| 9 | `009-qlora-8gb-mode` | `008-certificates-and-consensus` | Frozen base and certified adapter-only 8 GB reference run |
| 10 | `010-wan-benchmark-and-quality` | `009-qlora-8gb-mode` | Preregistered quality, BFT, WAN and determinism gates pass |
| 11 | `011-multiregion-pilot` | `010-wan-benchmark-and-quality` | 20–50-worker pilot yields signed go/no-go evidence |

## Superseded branches

These refs are historical only and MUST NOT be used as bases:

| Legacy ref | Replaced by | Reason |
| --- | --- | --- |
| `003-central-round-coordinator` | `003-bft-round-state-machine` | Central authority is incompatible with BFT replicated state. |
| `007-adaptive-heterogeneous-scheduling` | `007-domain-pure-ticket-scheduling` | Adaptive `H_i` and stale weighting are forbidden. |
| `008-permissioned-trust-and-resilience` | `008-certificates-and-consensus` | Identity-only resilience is insufficient; explicit certificate/QC lineage is mandatory. |

## Execution protocol

1. Implement and validate one authoritative branch at a time.
2. Run Spec Kit cross-artifact analysis before code and after any amendment.
3. Use task IDs in commits and keep `tasks.md` current.
4. Merge/promote the current branch only after its exit gate passes.
5. Stop on any certificate, arithmetic, determinism or quality gate failure; never bypass it with a later feature.

## Cross-feature invariants

- A ticket names one domain, immutable data range, fixed `B`, fixed `H`, parent checkpoint and arithmetic profile.
- Worker speed can affect admission or ticket count before freeze, never the domain mixture or certified scalar weight.
- One `ticket_id` maps to at most one commitment root.
- Shards become eligible only after availability certification.
- Exact inputs are frozen before `ρ_t` exists.
- Consensus clipping, weighting and summation use canonical integer/rational arithmetic; floating addition is prohibited.
- Fixed-point headroom is proven for the worst-case eligible set before aggregation.
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
