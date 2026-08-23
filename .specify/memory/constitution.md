# DeltaTorrent / DeltaReduce Constitution

**Version**: 2.0.0  
**Ratified**: 2026-08-21  
**Last amended**: 2026-08-23

Version 2.0.0 is a breaking architectural amendment. It replaces the central coordinator, adaptive local-step scheduling and FP32 global accumulation contracts with DeltaReduce v1.

## I. Scientific correctness before throughput

Every distributed result MUST be comparable with a token- and domain-matched reference baseline. Data assignment, domain mixture, ticket budget, model version, optimizer configuration, arithmetic profile, random seeds and evaluation inputs MUST be persisted in immutable manifests. Training loss alone is insufficient; validation loss, downstream quality and post-training behavior are required at the applicable milestone.

## II. Replicated deterministic state, never central authority

Round lifecycle and global application MUST execute as a deterministic BFT replicated state machine over a configured validator set of `3f+1`. A finalized transition or quorum certificate MUST contain at least `2f+1` valid votes. No service, operator or arrival-order winner MAY unilaterally decide membership, aggregate bytes or the current checkpoint.

## III. Domain-pure fixed work

Every `WorkTicket` MUST bind exactly one data domain, one immutable data range, fixed batch/token budget `B`, fixed optimizer-step count `H`, parent checkpoint, parameter schema and arithmetic profile. Adaptive `H_i`, stale update acceptance, device-speed weighting and mutation after ticket issuance are forbidden. Heterogeneous capacity MAY influence admission and the number of tickets assigned before input freeze, but MUST NOT alter the declared domain mixture `π_d`.

## IV. Integer fixed-point consensus arithmetic

Workers MUST normalize their local accumulation by effective optimizer-step count `A_j` before quantization. All certified clipping, scalar weighting and parameter summation MUST use a canonical integer/fixed-point representation with exact rounding and ordering rules. Floating-point addition is forbidden in the BFT reduce phase. Every round MUST prove that the worst-case integer sum fits the selected INT64/INT128 accumulator; saturation and wraparound are protocol failures.

## V. Input freeze, unbiased randomness and certificate lineage

The exact ordered input set `{T_j, C_j, AC_j}` MUST be finalized before seed `ρ_t` is generated or revealed. Every later decision MUST reference its explicit parent certificate. A valid model lineage proceeds through input-set, eligibility/aggregation-plan, parameter-shard, aggregate-root and apply certificates. Mixed views, missing parents and context-reused signatures MUST fail closed.

## VI. Atomic certified model application

Domain mixture, outer momentum, weight decay and Nesterov application MUST execute under a deterministic `ApplyArithmeticProfile` inside the consensus layer. A checkpoint becomes current only after `2f+1` apply validators sign one tuple containing the new model hash, new optimizer-state hash and parent `AggregateRootQC`. For one aggregate root, at most one `ApplyQC` may finalize.

## VII. Reduce plane and distribution plane are separate

Different worker updates MUST be reduced and certified before distribution. Only identical immutable datasets, base models, certified global aggregates, checkpoints and certificate bundles MAY enter the P2P distribution plane. Worker-local vectors, commitments, availability fragments and regional partials MUST NOT be swarm objects.

## VIII. Permissioned identity and safe boundaries

The MVP MUST use enrolled workers, storage peers and validators, authenticated transport, role-bound signing keys, replay protection and safe tensor/manifest formats. Untrusted bytes MUST never be deserialized through pickle or executed. Permissionless participation, Sybil resistance and economic incentives require a separate constitutional amendment.

## IX. WAN realism, observability and reversibility

Networking behavior MUST be validated under controlled RTT, bandwidth, loss, jitter, reordering, partition and Byzantine-message profiles before a real WAN pilot. Every feature branch MUST expose structured metrics, deterministic tests, an independent exit gate, immutable evidence and a rollback/abort path. Later features MUST NOT excuse a failing earlier gate.

## X. Reproducible interfaces, replaceable implementations

Domain, arithmetic and certificate contracts MUST be independent of transport, storage, accelerator and BFT-engine adapters. Implementations may be replaced only when they pass the same canonical bytes, state roots, accumulator proofs and quorum fixtures.

## Engineering quality gates

- Typed Python code passes formatting, linting, static checks and configured test suites.
- Protocol changes include golden canonical-serialization and backward-read fixtures.
- Integer arithmetic tests include maximum/minimum, overflow, sign, rounding and accumulator-headroom boundaries.
- At least four independent aggregator instances (`f=1`) produce byte-identical state and aggregate hashes on the feature-003 gate.
- Randomness-order tests prove that no seed exists before the input-set certificate.
- Certificate tests cover quorum intersection, duplicate votes, equivocation, wrong validator set, replay and mixed-view rejection.
- GPU-specific local training has a CPU or mocked smoke path; consensus arithmetic has a portable reference implementation.
- Secrets, private data and licensed model weights are never committed.
- Performance targets remain labelled as targets until measured evidence exists.

## Governance

This constitution governs all specifications, plans, tasks and implementation changes. Breaking invariants increment the major version; new mandatory principles increment the minor version; clarifications increment the patch version. Amendments require a dedicated commit explaining the reason, migration impact, superseded branches and affected artifacts.

Every feature plan MUST record a pre-implementation Constitution Check and repeat it against the final diff before merge.
