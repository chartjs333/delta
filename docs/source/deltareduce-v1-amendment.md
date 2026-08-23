# DeltaReduce v1 architectural amendment — source provenance

**Supplied**: 2026-08-23  
**Authority**: user-provided project specification update  
**Supersedes**: central coordinator, adaptive `H_i`, stale weighting and FP32 global accumulation portions of the original DeltaTorrent concept/specification stack.

This amendment is authoritative for the reduce and apply planes. The original concept remains the source for low-frequency local training, WAN experimentation, content-addressed distribution and 8 GB/QLoRA objectives where those ideas do not conflict with this document.

## 003 — BFT Round State Machine mandate

The single central coordinator is replaced by a replicated Byzantine Fault Tolerant state machine. The system is a deterministic aggregation engine for `Domain-Pure Work Tickets`.

- A ticket is bound to exactly one data domain `d`, fixed batch/token budget `B` and fixed local optimizer steps `H`.
- Adaptive local steps are forbidden.
- A worker divides its local accumulation by effective step count `A_j` to produce normalized pseudo-gradient `hat(Delta)_{j,d}` before quantization.
- Parameter shards are quantized to a specified fixed-point format, such as INT16.
- Aggregators sum in INT64/INT128-compatible integer space. Floating-point addition is forbidden during BFT reduce.
- Validator-set size is `3f+1`; final certificates require quorum intersection.

Lifecycle:

| State | Trigger | Effect |
| --- | --- | --- |
| `TICKETING_OPEN` | `RoundConfig` published | Emit locked domain-pure tickets. |
| `COMMITTED` | Merkle root `C_j` received | Bind ticket to quantized shard vectors. |
| `AVAILABLE` | `AC_j` received | Storage peers attest shard retrievability. |
| `ELIGIBLE` | seed `rho_t` generated after input freeze | Compute canonical input set/bucketing without post-seed manipulation. |
| `AGGREGATED` | parameter QCs formed | Sum fixed-point shards and certify results. |

Mandatory invariants include `CommitUniqueness` and `FixedPointSafety`. The feature-003 exit gate requires at least four independent aggregators (`f=1`) to produce bit-identical hashes while summing 100 simulated worker tickets.

## 008 — Certificates and Consensus mandate

No update may advance without its explicit parent certificate.

1. `InputSetCertificate (ISC)` freezes the exact array `{T_j, C_j, AC_j}` before randomness exists.
2. `EligibilityCertificate (EC)` defines accepted workers and clipping limits `gamma_j` after global norm evaluation.
3. `AggregationPlanCertificate (APC)` binds randomized buckets, centered-clipping iterations and fixed-point scalar weights.
4. `ParameterShardQC` certifies each exact parameter-shard result.
5. `AggregateRootQC` binds every required shard QC under one Merkle root, preventing mixed-view or Frankenstein updates.
6. `ApplyQC` binds the new checkpoint, outer-optimizer state and parent AggregateRootQC after `2f+1` apply signatures.

Randomized bucketing uses a bias-resistant seed `rho_t` generated strictly after ISC finalization. Robust filtering computes canonical vector norms and iterative centered clipping before scalar accumulator weights are finalized.

The domain mixture `pi_d`, outer momentum, weight decay and Nesterov application execute inside consensus. Apply validators sign one tuple containing the next model, next momentum and parent aggregate certificate.

Mandatory invariants include:

- `SeedAfterInputFreeze`;
- `ApplyUniqueness`;
- `DomainMixturePreservation`.

The feature-008 exit gate must automatically reject a malicious mixed-view parameter shard because its AggregateRootQC lineage does not match.
