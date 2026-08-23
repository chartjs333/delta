# ADR-0001: Adopt DeltaReduce v1 deterministic BFT aggregation

**Status**: Accepted  
**Date**: 2026-08-23  
**Decision owners**: project specification authority

## Context

The initial specification stack used one authoritative coordinator, token-weighted FP32 accumulation, adaptive worker-local step counts and an optional stale-update path. Those choices conflict with the new requirement that all honest aggregators verify exactly the same state transition and produce bit-for-bit identical aggregate hashes.

Floating-point reduction order, platform kernels, mutable membership and post-hoc worker weighting create consensus ambiguity. A central writer also prevents Byzantine fault tolerance and makes certificate lineage advisory rather than authoritative.

## Decision

Adopt DeltaReduce v1 as the authoritative reduce/apply architecture:

1. Run each round as a deterministic BFT state machine over `3f+1` validators with `2f+1`-vote quorum certificates.
2. Issue only domain-pure work tickets bound to one domain, fixed `B`, fixed `H`, parent model and arithmetic profile.
3. Normalize worker pseudo-gradients by effective step count before deterministic quantization.
4. Perform certified clipping, scalar weighting and parameter summation in canonical fixed-point integer space using INT64 or INT128 accumulators with precomputed overflow bounds.
5. Freeze the exact `{ticket, commitment, availability certificate}` input set before generating seed `ρ_t`.
6. Require explicit parent certificates: ISC, EC/APC, per-parameter-shard QC, AggregateRootQC and ApplyQC.
7. Execute domain mixture and the outer optimizer through a deterministic apply profile inside consensus; publish a new checkpoint only after ApplyQC.
8. Retain content-addressed P2P only for identical certified global objects.

## Consequences

### Positive

- Honest validators can compare exact state roots and aggregate hashes.
- Quorum intersection prevents two conflicting finalized transitions for the same height under the stated fault threshold.
- Input-freeze-before-seed removes a major source of inclusion/bucketing manipulation.
- AggregateRootQC prevents shard sets from different views/configurations being assembled into a Frankenstein update.
- Fixed domain mixture is independent of device speed.

### Costs

- Fixed-point profile design, norm computation and overflow analysis become protocol-critical.
- Adaptive local-step and stale-update efficiency experiments are removed from v1.
- BFT replication, availability attestations and certificate verification add latency, bandwidth and operational complexity.
- Outer-optimizer implementations must provide a portable deterministic reference path rather than relying on unconstrained accelerator kernels.

## Migration

- Constitution is amended from `1.0.0` to `2.0.0`.
- `003-central-round-coordinator` is replaced by `003-bft-round-state-machine`.
- `007-adaptive-heterogeneous-scheduling` is replaced by `007-domain-pure-ticket-scheduling`.
- `008-permissioned-trust-and-resilience` is replaced by `008-certificates-and-consensus`.
- Features `004–006` and `009–011` are rewritten against fixed-point and certificate contracts.
- Historical refs remain audit-only and are excluded from `specs/ROADMAP.md` execution topology.

## Reversal criteria

Reintroducing central authority, adaptive `H_i`, stale weighting or floating-point consensus reduction requires a new major constitutional amendment and a safety proof explaining how bit-identical BFT verification and certificate uniqueness remain guaranteed.
