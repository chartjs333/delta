# delta-core-cpp

Pure deterministic DeltaReduce feature-003 protocol core. It implements the bounded
`delta-canonical-binary-v1` parser/encoder, domain-separated content IDs, checked INT64 and
portable two-limb INT128 arithmetic, conservative accumulator-headroom validation and the pure
`prior-state bytes + command bytes -> next-state/effect/WAL bytes` transition.

Explicit `Command`, `RoundState`, `QuorumCertificate` and `PreparedIntegerShard` types reject
unknown fields, non-canonical integers, malformed identifiers and signer sets, incompatible
profiles and unsafe bounds. Consensus guards enforce validator membership and `2f+1` quorum,
durable vote uniqueness, commitment idempotency/equivocation, complete availability coverage,
input freeze before seed and deterministic abort/view-change behavior.

The core owns no I/O. It is standard-library-only and has no socket, filesystem, wall-clock,
thread, JVM, Python or floating-point-reduce dependency. `delta-runtime-cpp` owns serialization of
commands and durability; later features own production quantization, certificate-hierarchy
completion and transport.

Configure and run the isolated targets with:

```text
cmake --preset cpp20
cmake --build --preset cpp20 --parallel
ctest --preset cpp20
```

The `cpp23` preset exercises the compatibility language mode.

The cross-language golden, endian, accumulator and 100-ticket prepared-integer inputs live under
`delta-protocol/fixtures/003/`. `make bft-check` verifies their registered hashes and the
content-addressed feature-003 evidence.
