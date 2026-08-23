# DeltaTorrent system context — DeltaReduce v1

## Authority and provenance

The original DeltaTorrent concept memo defines the low-communication training and content-addressed distribution direction. The DeltaReduce v1 amendment supersedes its central-coordination, adaptive-`H_i`, stale-weighting and FP32-accumulation proposals. The distribution-plane boundary, WAN experimentation and 8 GB/QLoRA goals remain applicable.

## Authoritative architecture

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

## State-machine lifecycle

| State | Required trigger | Deterministic effect |
| --- | --- | --- |
| `TICKETING_OPEN` | `RoundConfigQC` | Emit immutable domain-pure tickets with fixed `B/H`. |
| `COMMITTED` | unique worker Merkle root `C_j` | Bind one ticket to one quantized vector commitment. |
| `AVAILABLE` | availability certificate `AC_j` | Prove all committed shard bytes are retrievable. |
| `ELIGIBLE` | input set frozen, then `ρ_t` generated | Derive canonical eligible set and aggregation plan without post-seed inclusion changes. |
| `AGGREGATED` | all required parameter-shard QCs | Bind bit-exact fixed-point shard sums into one aggregate root. |
| `APPLIED` | `ApplyQC` | Atomically certify one next checkpoint and optimizer state. |
| `ABORTED` | deterministic terminal failure rule | Preserve parent checkpoint and publish failure evidence only. |

Transitions are monotonic and content-addressed. A finalized certificate cannot be replaced by arrival order or operator preference.

## Arithmetic boundary

- Worker-local training may use configured floating-point kernels because it occurs before consensus.
- The worker divides its local accumulation by exact effective step count `A_j` and deterministically quantizes under the `RoundConfig` profile.
- Norm evidence, clipping coefficients, bucket weights and parameter sums used by consensus are represented in canonical integer/rational form.
- Accumulator bounds are proven before ticketing opens. Any overflow risk aborts configuration validation; runtime saturation is forbidden.
- Outer apply uses a versioned deterministic arithmetic profile and must produce byte-identical model/optimizer hashes across apply validators.

## Component boundaries

- `domain`: tickets, configs, state roots, certificates and immutable manifests.
- `training`: worker-local optimizer execution and normalized pseudo-gradient construction.
- `fixedpoint`: quantization, exact norms, rational weights, accumulator proofs and canonical shards.
- `consensus`: deterministic transition function, votes, QCs and validator-set rules.
- `availability`: shard storage, attestations and retrievability checks.
- `reduce`: regional/parameter committee integer aggregation.
- `certificates`: ISC, EC, APC, ParameterShardQC, AggregateRootQC and ApplyQC verification.
- `apply`: deterministic domain mixture and outer optimizer state transition.
- `distribution`: CAS/P2P for certified immutable global objects only.
- `adapters`: BFT engine, gRPC, filesystem/object storage, accelerator and deployment integrations.

Architecture tests MUST reject imports or API routes that:

- make one coordinator an authoritative writer;
- perform floating-point addition in consensus reduce;
- mutate `B/H/domain` after ticket issuance;
- generate `ρ_t` before input freeze;
- publish local/partial reduce artifacts into the P2P swarm;
- advance a checkpoint without the required parent certificates and `ApplyQC`.
