# DeltaTorrent Constitution

**Version**: 1.0.0  
**Ratified**: 2026-08-21  
**Last amended**: 2026-08-21

## I. Scientific correctness before throughput

Every distributed result MUST be comparable with a token-matched reference baseline. Token accounting, data assignment, model version, optimizer configuration, random seeds and evaluation inputs MUST be persisted in an immutable run manifest. Throughput optimizations MUST NOT be accepted solely because training loss appears normal; validation loss, downstream quality and post-training behavior are required at the applicable milestone.

## II. Reduce plane and distribution plane are separate

Different worker updates MUST first be mathematically reduced into one canonical global update. Only identical immutable objects MAY enter the P2P distribution plane. Worker-local deltas MUST NOT be broadcast to the whole swarm. Tests MUST enforce this boundary at module and protocol level.

## III. Deterministic, versioned and content-addressed state

Every dataset shard, base model, checkpoint, parameter schema, compressed delta shard and round manifest MUST have a stable identifier and cryptographic content hash. Every update MUST name its parent model version. Duplicate, replayed, corrupted or wrong-parent artifacts MUST be rejected idempotently.

## IV. WAN realism is a test requirement

Networking behavior MUST be validated under controlled RTT, bandwidth, loss, jitter, reordering and disconnect profiles before a real WAN pilot. Tests MUST avoid public network dependencies and MUST provide an unprivileged deterministic simulation path when Linux traffic control is unavailable. Timeouts, retries and cancellation are part of the contract.

## V. Heterogeneity and asynchrony are bounded

No algorithm MAY wait indefinitely for the slowest node or accept updates with unbounded staleness. Work allocation MUST use measured capability, verified processed tokens and explicit deadlines. Adaptive local-step counts MUST be clamped by communication-efficiency and optimization-drift guards. Experimental staleness weighting MUST be feature-flagged against a strict synchronous default.

## VI. Permissioned security by default

The MVP MUST use enrolled node identities, authenticated transport, signed metadata and safe tensor formats. Untrusted network input MUST never be deserialized through pickle or executed. Norm limits, finite-value checks, replay protection, audit records and manifest verification are mandatory before the multi-region pilot. Permissionless participation requires a separate approved specification.

## VII. Observable, reversible increments

Each feature branch MUST expose structured metrics, deterministic tests, an independent exit gate and a rollback path. New protocol behavior MUST be versioned. A feature MAY be merged only when its tasks, tests, documentation and evidence are complete; later features MUST NOT excuse a failing earlier gate.

## VIII. Reproducible interfaces, replaceable implementations

Domain contracts MUST be separated from transport, storage, accelerator and orchestration adapters. Tests MUST target stable interfaces so implementations can be replaced without changing the mathematical contract.

## Engineering quality gates

- Typed Python code passes formatting, linting, static checks and the configured test suites.
- Numerical tests define dtype-aware tolerances and compare with a direct reference implementation.
- Protocol changes include compatibility and canonical serialization fixtures.
- GPU-specific behavior has a CPU or mocked smoke path.
- Secrets, private data and licensed model weights are never committed.
- Performance targets remain labelled as targets until benchmark evidence exists.

## Governance

This constitution governs all specifications, plans, tasks and implementation changes. Amendments require a dedicated commit explaining reason, migration impact and affected features. A breaking invariant increments the major version; a new mandatory principle increments the minor version; clarification increments the patch version.

Every feature plan MUST record a Constitution Check before implementation and repeat it against the final diff before merge.
