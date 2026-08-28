# Feature 005: Certified Content-Addressed P2P Distribution

Feature 005 distributes one immutable global object identified by canonical manifest bytes and a
native-verified certification policy. It refines `ACT-PUBLISH` and `ACT-ARTIFACT-REPAIR`; it does
not add a consensus transition or allow discovery to define trusted identity.

## Authority boundary

The C++ `delta::distribution::evaluate_certified_manifest` implementation is the only publication
authority. It parses bounded canonical manifest/certificate JSON, binds formal semantics, source
state/root, certificate root, policy registry, media type and exact piece layout, and returns a
canonical `ACCEPT` or typed `REJECT` effect. The additive C ABI exposes synchronous borrowed and
owned-copy commands with identical results. Java cannot instantiate an allow decision; it may
only consume the native effect through FFM.

The active `aggregated-transition-qc-v1` policy permits an immutable aggregate bundle and cannot
make it current. The future ApplyQC policy remains registered but inactive and belongs to feature
008. Unknown/weaker policy, wrong roots and every worker-local/partial media class fail closed.

## Data plane

Java 25 owns deterministic 1 MiB chunking, piece-tree verification, CAS/journal I/O, permissioned
discovery and bounded peer mechanics using Netty buffers. The CAS derives every path from a
validated digest, rejects symlink/path escape, writes through forced same-directory temporaries and
uses atomic rename for visibility. Existing corrupt piece bytes may be atomically repaired only by
bytes that reproduce the frozen piece ID.

Peer advertisements are leased hints containing only locally reverified ordinals. They cannot
replace the trusted manifest. Fetch uses deterministic peer ordering, deadlines, retry bounds,
cancellation, stream semaphores and explicit buffer ownership. Wrong-length/hash responses are
released and journaled; restart rechecks local bytes. Final materialization repeats native policy,
piece and whole-payload verification before atomic visibility. An incomplete peer union returns
`PIECE_UNAVAILABLE` without deleting its journal or changing current checkpoint state.

## Reproduction

The contract verifier is offline and runtime-neutral:

```text
python specs/005-content-addressed-p2p-distribution/scripts/verify_protocol_contracts.py
```

Native C++20/C++23 tests, production mutants and parser smoke corpus are part of the root CMake
presets. `.github/workflows/distribution.yml` provisions content-addressed GCC/Clang, Temurin
25/26 and Netty artifacts, then disables network access for compilation/execution. The Java
conformance harness covers direct/copy/composite FFM parity, idempotent publication, quota and
filesystem guards, corrupt/slow/truncated peers, restart, bit rot, registry outage, seed loss,
incomplete union, cancellation and event-loop blocking detection.

No WAN performance, anonymous DHT, erasure coding, model quality, hierarchy, certificate transport
or Apply/current completion claim is made by this phase.
