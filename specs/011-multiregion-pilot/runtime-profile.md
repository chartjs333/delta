# Runtime Profile: 011 Multi-Region Hybrid Pilot

**Validator/reducer/apply/P2P node**: Java node shell + C++ native runtime/core  
**Training worker**: Python/PyTorch  
**Deployment profile**: selected by feature-010 BenchmarkResultQC  
**Formal impact**: no semantic change permitted during pilot

## Prerequisite extension

Remote deployment requires both:

- exact compatible Formal GO;
- exact compatible BenchmarkResultQC(GO) selecting a concrete runtime/deployment profile.

The pilot cannot choose embedded FFM when the benchmark approved only sidecar, or vice versa.

## Deployable units

### Hybrid validator node

- signed/pinned Java image/runtime;
- signed/pinned native library or sidecar image;
- ABI/schema/formal-semantics startup handshake;
- native durable volumes for WAL/snapshot;
- Java volumes/CAS for distribution and operational state;
- external TLS/signing/model credentials;
- separate Java/native health and resource telemetry.

### Python worker

- pinned Python/PyTorch/accelerator image;
- fixed-ticket local training only;
- immutable model/data/profile identities;
- no validator key or current-state authority.

## Embedded profile

Java loads native runtime in-process. A native crash terminates the node process. Recovery restarts the node, verifies identity, replays native WAL before network admission and resumes idempotently.

## Sidecar profile

Java and native runtime are separate processes using the benchmark-approved local IPC contract. Native restart/replay completes before Java forwards new protocol commands. IPC queue, shared memory and lifetime limits are versioned and bounded.

## Operations boundary

Operator APIs may start/stop/quarantine services and revoke identities, but cannot inject unsigned state, skip native durability, reinterpret certificate bytes or advance current state manually.

## Pilot fault campaign additions

- Java process crash with native embedded runtime;
- native sidecar crash while Java remains alive;
- ABI/formal-semantics mismatch during rolling deployment;
- WAL/snapshot volume loss/corruption;
- Netty buffer pressure/leak alarm and event-loop stall;
- FFM/IPC queue saturation;
- stale timer storm and duplicate transport delivery;
- Python worker OOM/partial ticket;
- native/Java image rollback between rounds only.

## Exit additions

- target inventory records Java/native/Python image and build identities separately;
- every finalized trace binds ABI and formal semantics IDs;
- restart/rollback preserves certified history and current checkpoint;
- pilot report distinguishes Java, native and Python resource/incident metrics;
- GO is impossible with an unapproved deployment profile or unresolved native-runtime discrepancy.
