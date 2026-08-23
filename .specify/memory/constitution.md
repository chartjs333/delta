# DeltaTorrent / DeltaReduce Constitution

**Version**: 2.1.0  
**Ratified**: 2026-08-21  
**Last amended**: 2026-08-23

Version 2.0.0 replaced the central coordinator, adaptive local-step scheduling and FP32 global accumulation contracts with DeltaReduce v1. Version 2.1.0 introduces a new mandatory principle: formal verification of protocol safety, failure/recovery semantics and parametric arithmetic obligations before implementation.

## I. Scientific correctness before throughput

Every distributed result MUST be comparable with a token- and domain-matched reference baseline. Data assignment, domain mixture, ticket budget, model version, optimizer configuration, arithmetic profile, random seeds and evaluation inputs MUST be persisted in immutable manifests. Training loss alone is insufficient; validation loss, downstream quality and post-training behavior are required at the applicable milestone.

## II. Formal verification precedes implementation

The authoritative BFT lifecycle, certificate graph, failure/recovery behavior, liveness assumptions and arithmetic proof obligations MUST be specified and pass the `000-formal-tla-spec` exit gate before implementation tasks in branches `001–011` begin. Finite interleavings and fault schedules MUST be checked by executable TLA+/TLC models. Parametric claims not established by finite model checking—including quorum intersection, fixed-point bounds, hierarchical-flat equality and Apply uniqueness—MUST have machine-checked theorem-prover proofs or an explicitly approved equivalent formal method.

A protocol-semantic change MUST update the formal model/proofs before code and MUST rerun all affected invariant, liveness, counterexample and refinement checks. A formal failure is an unconditional STOP and cannot be waived by tests, benchmarks or operator approval.

## III. Replicated deterministic state, never central authority

Round lifecycle and global application MUST execute as a deterministic BFT replicated state machine over a configured validator set of `3f+1`. A finalized transition or quorum certificate MUST contain at least `2f+1` valid votes. No service, operator or arrival-order winner MAY unilaterally decide membership, aggregate bytes or the current checkpoint.

## IV. Domain-pure fixed work

Every `WorkTicket` MUST bind exactly one data domain, one immutable data range, fixed batch/token budget `B`, fixed optimizer-step count `H`, parent checkpoint, parameter schema and arithmetic profile. Adaptive `H_i`, stale update acceptance, device-speed weighting and mutation after ticket issuance are forbidden. Heterogeneous capacity MAY influence admission and the number of tickets assigned before input freeze, but MUST NOT alter the declared domain mixture `π_d`.

## V. Integer fixed-point consensus arithmetic

Workers MUST normalize their local accumulation by effective optimizer-step count `A_j` before quantization. All certified clipping, scalar weighting and parameter summation MUST use a canonical integer/fixed-point representation with exact rounding and ordering rules. Floating-point addition is forbidden in the BFT reduce phase. Every round MUST prove that the worst-case integer sum fits the selected INT64/INT128 accumulator; saturation and wraparound are protocol failures.

## VI. Input freeze, unbiased randomness and certificate lineage

The exact ordered input set `{T_j, C_j, AC_j}` MUST be finalized before seed `ρ_t` is generated or revealed. Every later decision MUST reference its explicit parent certificate. A valid model lineage proceeds through input-set, eligibility/aggregation-plan, parameter-shard, aggregate-root and apply certificates. Mixed views, missing parents and context-reused signatures MUST fail closed.

## VII. Atomic certified model application

Domain mixture, outer momentum, weight decay and Nesterov application MUST execute under a deterministic `ApplyArithmeticProfile` inside the consensus layer. A checkpoint becomes current only after `2f+1` apply validators sign one tuple containing the new model hash, new optimizer-state hash and parent `AggregateRootQC`. For one aggregate root, at most one `ApplyQC` may finalize.

## VIII. Reduce plane and distribution plane are separate

Different worker updates MUST be reduced and certified before distribution. Only identical immutable datasets, base models, certified global aggregates, checkpoints and certificate bundles MAY enter the P2P distribution plane. Worker-local vectors, commitments, availability fragments and regional partials MUST NOT be swarm objects.

## IX. Permissioned identity and safe boundaries

The MVP MUST use enrolled workers, storage peers and validators, authenticated transport, role-bound signing keys, replay protection and safe tensor/manifest formats. Untrusted bytes MUST never be deserialized through pickle or executed. Permissionless participation, Sybil resistance and economic incentives require a separate constitutional amendment.

## X. Explicit failure, recovery and liveness semantics

Every state-changing protocol MUST specify soft and hard deadlines, view/leader change, quorum loss, partition, crash/restart, durable vote recovery, artifact corruption, storage unavailability, repair, abort and current-state recovery behavior. Safety MUST hold without synchrony assumptions under the declared Byzantine threshold. Liveness MAY be claimed only under explicit eventual-synchrony, honest-quorum, storage-availability and fairness assumptions. When assumptions fail, the system MUST remain safe and either block or reach a deterministic certified abort without changing the current checkpoint.

## XI. WAN realism, observability and reversibility

Networking behavior MUST be validated under controlled RTT, bandwidth, loss, jitter, reordering, partition and Byzantine-message profiles before a real WAN pilot. Every feature branch MUST expose structured metrics, deterministic tests, an independent exit gate, immutable evidence and a rollback/abort path. Later features MUST NOT excuse a failing earlier gate.

## XII. Reproducible interfaces, replaceable implementations

Domain, arithmetic and certificate contracts MUST be independent of transport, storage, accelerator and BFT-engine adapters. Implementations may be replaced only when they pass the same canonical bytes, state roots, formal traces, accumulator proofs and quorum fixtures.

## Engineering quality gates

- `000-formal-tla-spec` produces an executable TLA+ model, model-check configurations, theorem-prover project, expected-counterexample mutants, formal trace schema and content-addressed `FormalVerificationReport`.
- TLC checks safety under finite `f=1` fault/interleaving models and liveness under the exact declared fairness/synchrony assumptions.
- Parametric proofs cover quorum intersection, accumulator safety, hierarchical-flat integer equality and Apply uniqueness.
- Code-bearing protocol branches project implementation traces into the formal action vocabulary and pass refinement/conformance checks.
- Typed Python code passes formatting, linting, static checks and configured test suites.
- Protocol changes include golden canonical-serialization and backward-read fixtures.
- Integer arithmetic tests include maximum/minimum, overflow, sign, rounding and accumulator-headroom boundaries.
- At least four independent aggregator instances (`f=1`) produce byte-identical state and aggregate hashes on the feature-003 gate.
- Randomness-order tests prove that no seed exists before the input-set certificate.
- Certificate tests cover quorum intersection, duplicate votes, equivocation, wrong validator set, replay and mixed-view rejection.
- GPU-specific local training has a CPU or mocked smoke path; consensus arithmetic has a portable reference implementation.
- Secrets, private data and licensed model weights are never committed.
- Performance targets and unexecuted formal obligations remain labelled as targets until evidence exists.

## Governance

This constitution governs all specifications, formal models, proofs, plans, tasks and implementation changes. Breaking invariants increment the major version; new mandatory principles increment the minor version; clarifications increment the patch version. Amendments require a dedicated commit explaining the reason, migration impact, superseded branches and affected artifacts.

Every feature plan MUST record a pre-implementation Constitution Check, a formal-impact classification and a final check against both the implementation diff and authoritative formal baseline.
