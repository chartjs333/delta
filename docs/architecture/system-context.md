# DeltaTorrent system context — DeltaReduce v1 formal-first architecture

## Authority and provenance

The original DeltaTorrent concept memo defines the low-communication training and content-addressed distribution direction. The DeltaReduce v1 amendment supersedes its central-coordination, adaptive-`H_i`, stale-weighting and FP32-accumulation proposals. Constitution 2.1.0 and ADR-0000 add an obligatory formal baseline before implementation.

## Authority layers

```text
Constitution 2.1.0 + ADR-0000/0001
                 │
                 ▼
TLA+ executable protocol/failure/recovery model
+ machine-checked parametric proofs
                 │ FormalVerificationReport(GO)
                 ▼
Spec Kit feature contracts 001–011
                 │ refinement/trace obligations
                 ▼
Python/PyTorch/BFT/storage/P2P implementations
                 │ evidence and conformance traces
                 ▼
BenchmarkResultQC → PilotResultQC
```

A production implementation is authoritative only insofar as its externally visible trace refines the accepted formal action/state vocabulary and satisfies canonical byte/arithmetic contracts. An implementation test cannot redefine the formal semantics.

## Authoritative runtime architecture

```text
                       RoundConfig / ValidatorSet
                                  │
                                  ▼
                    BFT replicated state machine
                                  │
                      domain-pure fixed tickets
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
          Worker j            Worker k             Worker n
       local AdamW         local AdamW          local AdamW
       fixed B, H, d       fixed B, H, d        fixed B, H, d
             │                    │                    │
        q-shards + Cj        q-shards + Ck       q-shards + Cn
             └──────────── storage availability peers ───────────┘
                                  │
                            ACj / ACk / ACn
                                  │
                   InputSetCertificate (input frozen)
                                  │
                    bias-resistant seed ρt generated
                                  │
                 EC + AggregationPlanCertificate
                                  │
          regional/parameter committees: integer fixed-point sum
                                  │
                       ParameterShardQC for each shard
                                  │
                         AggregateRootQC
                                  │
              deterministic domain mix + outer optimizer
                                  │
                              ApplyQC
                                  │
                  certified checkpoint / global object
                                  │
                     content-addressed P2P swarm
```

## State-machine lifecycle and failure terminals

| State | Required trigger | Deterministic effect/failure rule |
| --- | --- | --- |
| `TICKETING_OPEN` | `RoundConfigQC` | Emit fixed tickets; unsafe arithmetic/config aborts before open. |
| `COMMITTED` | unique `C_j` | Bind ticket once; conflict is equivocation evidence. |
| `AVAILABLE` | valid `AC_j` | Only AC-covered inputs can be frozen. Missing pre-freeze AC follows close policy. |
| `ELIGIBLE` | ISC finalized, then `ρ_t`, EC/APC | Late input cannot mutate ISC; unavailable required post-ISC bytes trigger repair then abort. |
| `AGGREGATED` | complete parameter-shard QCs | Missing quorum triggers view change/retry until hard deadline, then abort. Mixed views never assemble. |
| `APPLIED` | unique `ApplyQC` and pointer CAS | Current state advances exactly once; replay repairs pointer idempotently. |
| `ABORTED` | deterministic hard failure/deadline | Parent checkpoint remains current; evidence is immutable. |

## Formal fault model

The formal baseline explicitly models asynchronous reorder/duplication/drop, proposer equivocation, up to `f` Byzantine validators, validator crash/restart, durable vote journal, quorum loss, network partition, storage loss/corruption, repair, soft timeout/view change, hard deadline/abort, certificate replay and current-pointer crash recovery.

Safety is unconditional within the declared Byzantine/cryptographic abstraction. Liveness is conditional on eventual synchrony, at least `2f+1` responsive validators, required artifact availability and fairness. Permissionless Sybil resistance and cryptographic primitive correctness are outside this model.

## Arithmetic boundary

- Worker-local training may use configured floating-point kernels because it occurs before consensus.
- The worker divides its local accumulation by exact effective step count `A_j` and deterministically quantizes under the `RoundConfig` profile.
- Norm evidence, clipping coefficients, bucket weights and parameter sums used by consensus are represented in canonical integer/rational form.
- Accumulator bounds are parametrically proved and validated before ticketing; actual APC coefficients must remain inside the proved envelope.
- Hierarchical integer reduction is proved equal to flat reduction when region partitions are exact and non-overlapping.
- Outer apply uses a versioned deterministic arithmetic profile and produces byte-identical model/optimizer hashes.

## Component boundaries

- `formal`: TLA+ modules/configs, theorem proofs, mutants, traces and verification reports.
- `domain`: tickets, configs, state roots, certificates and immutable manifests.
- `training`: worker-local optimizer execution and normalized pseudo-gradient construction.
- `fixedpoint`: quantization, exact norms, rational weights, accumulator proofs and canonical shards.
- `consensus`: deterministic transition function, votes, QCs and validator-set rules.
- `availability`: shard storage, attestations, repair and retrievability checks.
- `reduce`: regional/parameter committee integer aggregation.
- `certificates`: ISC, EC, APC, ParameterShardQC, AggregateRootQC and ApplyQC verification.
- `apply`: deterministic domain mixture and outer optimizer state transition.
- `distribution`: CAS/P2P for certified immutable global objects only.
- `adapters`: BFT engine, gRPC, filesystem/object storage, accelerator and deployment integrations.

Architecture/formal-refinement tests MUST reject routes that make one coordinator authoritative, perform floating consensus addition, mutate fixed tickets/ISC, produce seed before ISC, mix certificate views, publish local/partial artifacts, advance current without ApplyQC, or handle quorum/storage loss through unspecified fallback.
