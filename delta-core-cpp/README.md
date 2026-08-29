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

Feature 004 adds the authoritative `int16-fixed-v1` encoder, reduced rational scales, portable
ties-to-even rounding, concrete INT64/INT128 proof validation, deterministic DRQ1 shard planning,
bounded parsing and direct-q adaptation. Verified q values are widened directly into the existing
checked integer accumulator; they are never converted to float for consensus reduction.

The core owns no I/O. It is standard-library-only and has no socket, filesystem, wall-clock,
thread, JVM, Python or floating-point-reduce dependency. `delta-runtime-cpp` owns serialization of
commands and durability; later features own certificate-hierarchy completion and transport.

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

Feature-004 profile, proof, cross-language shard and direct-q fixtures live under
`delta-protocol/fixtures/004/`. `make fixedpoint-refinement` reproduces their contract,
architecture, proof-instance and formal-refinement gates.

Feature 005 adds the standard-library-only distribution certification boundary. It accepts only
bounded canonical manifest/certificate bytes under the exact frozen policy registry and rejects
unknown/inactive/weaker policy, forbidden media, wrong lineage/root and aggregate-as-current use.
Piece layout is exact, contiguous and bounded. Production mutants weaken policy downgrade,
forbidden-media and canonical parsing checks; all are required to fail the real test suite.

Feature 008 adds the native certificate, robust-reduce and deterministic-apply authority. Every
ISC/EC/APC/ParameterShardQC/AggregateRootQC/ApplyQC body is canonically serialized, context-bound,
signer-bound and checked against the immutable parent graph. Aggregate coverage is derived from
the frozen RoundConfig domain-by-shard matrix and committed by a domain-separated Merkle tree;
observed leaves can never redefine the requirement set. Robust filtering and Apply use checked
integer/rational arithmetic only. `delta-runtime-cpp` supplies the shared persist-before-expose
vote journal and the ApplyQC-authorized, crash-recoverable current-pointer compare-and-set.
