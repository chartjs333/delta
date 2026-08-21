# DeltaTorrent Spec Kit roadmap

## Branch topology

Branches are stacked. Each adds only its own specification directory and uses the previous feature head as parent.

| Order | Branch | Base | Primary exit gate |
| ---: | --- | --- | --- |
| 1 | `001-reproducible-training-baseline` | `main` | Deterministic reference run and offline WAN tests |
| 2 | `002-local-round-engine` | `001-reproducible-training-baseline` | Local delta reconstructs trained weights |
| 3 | `003-central-round-coordinator` | `002-local-round-engine` | Token-weighted rounds match reference math |
| 4 | `004-compressed-delta-protocol` | `003-central-round-coordinator` | INT8 reduction and bounded error feedback |
| 5 | `005-content-addressed-p2p-distribution` | `004-compressed-delta-protocol` | Verified multi-peer download survives seed loss |
| 6 | `006-regional-hierarchical-reduce` | `005-content-addressed-p2p-distribution` | Hierarchical result equals flat weighted reduce |
| 7 | `007-adaptive-heterogeneous-scheduling` | `006-regional-hierarchical-reduce` | Bounded stragglers and adaptive communication share |
| 8 | `008-permissioned-trust-and-resilience` | `007-adaptive-heterogeneous-scheduling` | Signed/replay-safe updates and 10% churn tolerance |
| 9 | `009-qlora-8gb-mode` | `008-permissioned-trust-and-resilience` | Frozen base and adapter-only 8 GB reference |
| 10 | `010-wan-benchmark-and-quality` | `009-qlora-8gb-mode` | Token-matched benchmark and quality/efficiency gates |
| 11 | `011-multiregion-pilot` | `010-wan-benchmark-and-quality` | 20–50-node pilot evidence and go/no-go decision |

## Execution protocol

1. Implement and validate one branch at a time.
2. Run Spec Kit analysis before code and after any spec amendment.
3. Use task IDs in commits and keep `tasks.md` current.
4. Merge the current branch before promoting the next.
5. Stop when an exit gate fails; revise the current spec rather than bypassing it.

## Cross-feature invariants

- A worker delta names exactly one parent model and parameter schema.
- Contribution weight uses verified processed tokens.
- Regional aggregation transports weighted sums and token counts.
- Compression precedes transport and aggregation accumulates decoded FP32.
- Error feedback is worker-local and keyed by worker/schema/codec.
- Only globally aggregated immutable objects enter P2P distribution.
- Network operations are idempotent, timeout-bounded and resumable where needed.
- Permissioned identity is mandatory for the pilot.

## Deferred research

- permissionless participation, Sybil resistance and incentives;
- streaming/overlapped transfer and advanced sparse/low-rank codecs;
- WAN pipeline parallelism, distributed MoE and block-local objectives;
- full dense multi-billion pretraining on isolated 8 GB GPUs;
- independent cryptographic verification of arbitrary participant compute.
