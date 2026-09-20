# Runtime Profile: Multi-Region Hybrid Pilot

**Hybrid validator/reducer/apply/P2P node**: Java/Netty shell plus C++ native
core/runtime.
**Training worker**: Python/PyTorch.
**Deployment profile**: selected by the compatible Feature 010 ResultQC.
**Current status**: blocked before remote provisioning.

## Hybrid validator node

- pinned signed Java image/runtime and native library or sidecar image;
- startup handshake for ABI, schema, protocol, build, and formal semantics IDs;
- native-owned WAL/snapshot and single-writer recovery;
- Java-owned TLS sessions, connections, framing, routing, backpressure, and
  content-addressed-storage (CAS) I/O; native C++ retains current-pointer
  compare-and-set authority;
- externally injected TLS/signing credentials;
- separate Java/native health, incident, resource, and evidence identities.

## Python worker

- pinned Python/PyTorch/accelerator image and immutable model/data/profile IDs;
- local fixed-ticket training and evaluation only;
- no validator key, QC construction, aggregation, or current-state authority;
- canonical normalized/quantized bytes are the only consensus-visible output.

## Embedded profile

Java loads native in-process; a native crash terminates the node. Recovery restarts
the whole node and replays native WAL before network admission. No crash-isolation
claim is allowed.

## Sidecar profile

Java and native runtime use the benchmark-approved bounded local IPC contract.
Native restart/replay completes before Java forwards new commands. IPC queues,
memory ownership, timeouts, health, and backpressure are versioned and tested.

## Pilot-specific fault gates

- Java/native crash and restart around persist-before-expose;
- ABI/formal/schema/image mismatch during rolling deployment;
- WAL/snapshot loss/corruption and replay;
- Netty leak, event-loop stall, FFM/IPC saturation, stale timers, duplicates;
- Python OOM/partial ticket and GPU/profile drift;
- TLS expiry/revocation, clock skew, endpoint/route drift, and secret rotation;
- rollback only between waves/rounds without reinterpreting certified history.
