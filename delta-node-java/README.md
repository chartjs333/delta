# delta-node-java

Java conformance boundary for feature 003. `RuntimeDescriptorCompatibility` validates the frozen
descriptor on pinned JDK 25 and JDK 26 toolchains. `NativeRuntimeFfmConformance` uses the standard
Foreign Function & Memory API to load the real C ABI, negotiate output capacity, exercise both
borrowed and copied submission paths, snapshot state and release the opaque handle.

The harness owns no validator state, transition rule, vote journal or native pointer beyond its
declared arena/call lifetime. ABI/schema/protocol/formal/build mismatch cases fail before command
admission. Feature-003 and feature-004 harnesses introduce no transport dependency.

Feature 004 adds opaque DRQ1 heap/direct copy tests and `NativeFixedPointFfmConformance`. The latter
calls both production C ABI shard-validation entry points on JDK 25 and JDK 26 and requires exact
bytes for valid envelopes and stable rejection for truncated, trailing, corrupt and oversized
inputs. Java does not decode q values, choose scales or aggregate contributions.

Feature 005 adds the production Java 25 distribution data plane under
`io.deltareduce.node.distribution`. Netty owns bounded buffer/peer mechanics, while the native C++
policy remains the sole certification authority through FFM. The direct buffer path is retained
only for a synchronous borrowed call; heap/composite/non-contiguous input uses the same bounded
owned-copy ABI. Both paths must return identical status, effect and manifest identity.

`CasStore`, `Publisher`, `PeerPlane`, `DownloadJournal` and `Downloader` implement atomic immutable
storage, verified-piece-only advertisements, deterministic multi-peer repair and restart. Java
cannot construct an `ACCEPT`, reinterpret an aggregate as current or distribute worker-local
partials. Dependencies and JDK 25/26 lanes are frozen in `distribution-dependencies.lock.json` and
`toolchains.toml`; CI provisions them by size/SHA-256 and runs offline afterward.

Feature 006 adds `NativeHierarchy` and `HierarchyRouter`. Native C++ validates the canonical
topology/theorem instance and remains the sole owner of partition, arithmetic and committee-QC
semantics. Java binds its routing projection to the returned topology ID and moves only bounded
opaque bytes through permissioned regional queues with deadline, cancellation, retry,
backpressure and telemetry controls. It exposes no sum, averaging, signer-selection or QC-building
API.

Feature 007 adds `NativeScheduling`, `CapabilityCollector`, `AdmissionTransport` and
`LeaseTimerRouter`. Java submits authenticated canonical capability bytes through the bounded
borrowed-direct or owned-copy C ABI and receives a byte-exact native eligibility decision. Plan,
lease and timer-token artifacts remain defensive-copy opaque payloads in bounded queues. Java may
apply backpressure, cancel delivery and publish operational counters; it cannot calculate
eligibility, change a ticket, advance a lease epoch/deadline, select a commitment winner or use
device metrics as aggregation weights. Native C++ remains the only scheduling and lease-state
authority, including stale/reordered timer handling and restart recovery.

Feature 008 adds `NativeCertificateVerifier`, `AuthenticatedCertificateTransport`,
`CertificateTimerService`, `ArtifactEffectAdapter` and `CurrentCheckpointPublisher`. The FFM
adapter routes canonical bytes to the bounded native certificate inspector and requires borrowed
direct/copy parity. Java authenticates, delays, reorders, duplicates or drops opaque frames and
executes only bounded native-authored artifact/current effects. It has no quorum, robust-plan,
root-coverage, apply arithmetic or current-state decision API.
