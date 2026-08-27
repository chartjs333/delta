# Feature 003 operator and verification guide

Feature 003 is the native BFT round-state-machine slice. The pure C++ core consumes canonical
prior-state and command bytes. The C++ runtime serializes those transitions through a bounded
single-writer reactor and persists canonical WAL records before exposing effects. The versioned C
ABI is the only language boundary; the JDK 25/26 code is a conformance harness, not a second
consensus implementation.

## Runtime and recovery contract

The observable order is `transition -> WAL append -> durability barrier -> state commit -> effect
return`. Startup validates a snapshot and its state root, replays checksummed monotonic WAL records
and recovers the durable vote journal before command admission. Exact retries are idempotent;
conflicting request or vote reuse, torn/corrupt WAL records and divergent recovery fail closed.

Borrowed ABI inputs remain caller-owned and are valid only for the synchronous call. Output uses
caller buffers with exact size negotiation and retry without double execution. Handles are opaque
and explicitly released. Descriptor mismatches are rejected before a runtime is opened.

## Fixtures and checks

- `delta-protocol/fixtures/003/valid/` and `invalid/` exercise runtime-neutral parsing contracts.
- `cross-language/golden-v1.json` binds canonical bytes and content IDs.
- `cross-language/core-portability-v1.json` binds compiler/language-mode/endian results.
- `cross-language/prepared-100-v1.json` supplies already prepared integer inputs for the native
  four-runtime exit test; it is not a production quantizer.
- `evidence/traces/` contains native legal traces accepted by the exact feature-000 refinement
  checker; `evidence/mutants/` contains real production-path mutants that it rejects.

Run the content-addressed gate with `make bft-check`. Native build/test targets remain available as
`make bft-native`; the pinned CI matrix supplies GCC/Clang C++20/23, JDK 25/26, ASan/UBSan and a
separate TSan lane.

## Scope boundary

The phase proves implementation conformance to the already accepted formal semantics ID
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
Its artifact analyzer is a deterministic compatibility and traceability gate and does not claim a
new proof of semantic completeness.

Feature 003 does not implement production quantization/rounding/clipping or delta codecs (feature
004), protobuf/gRPC/Netty/TLS transport (feature 005), the full certificate hierarchy and robust
aggregation (feature 008), P2P distribution or WAN performance claims.
