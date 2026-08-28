# Feature 004: canonical fixed-point shards

Feature 004 implements the mandatory `int16-fixed-v1` contribution format on top of the merged
feature-003 native runtime. The authoritative encoder, bounded shard parser, proof validator and
direct-q accumulator adapter are C++20/C++23 code. Python independently generates frozen fixtures;
Java preserves opaque bytes and exercises the production parser through the C FFM boundary.

The profile uses the symmetric q range `[-32767, 32767]`, reduced positive-denominator rational
scales fixed per canonical segment, signed round-to-nearest-ties-to-even, little-endian INT16
payloads and fail-closed range handling. The fixed-point config binds the base RoundConfig,
parameter schema, profile, scale table, shard plan, term/coefficient bounds and selected INT64 or
portable INT128 accumulator width. Its content ID is therefore part of every concrete proof
instance rather than mutable runtime state.

DRQ1 parsing validates prefix/version, header and payload limits, exact total length, canonical
context, payload SHA-256 and the forbidden `-32768` encoding before values are exposed. Shard
collection accepts byte-identical retries idempotently, rejects conflicting ordinals and emits only
the frozen schema order. Merkle leaves bind the complete envelope.

Verified q values are widened directly to feature-003 `PreparedIntegerShard` values. No q-to-float
conversion occurs. The 100-ticket compatibility fixture versions the resulting prepared, frozen,
effect, WAL and state hashes. The accepted refinement trace reaches `APPLIED`; an unchecked-bound
production mutant is rejected by the frozen formal checker.

Run the local deterministic gates with:

```text
make fixedpoint-refinement
cmake --preset cpp20
cmake --build --preset cpp20 --parallel
ctest --preset cpp20
cmake --preset cpp23
cmake --build --preset cpp23 --parallel
ctest --preset cpp23
```

Pinned CI additionally runs GCC 14.2 and Clang 20.1.8 in both language modes, JDK 25/26 FFM
conformance, ASan/UBSan and bounded libFuzzer. An aarch64 result is reported only when an exact
pinned runner is available.

This phase does not claim model-quality bounds, WAN/transport behavior, residual/error-feedback
semantics, hierarchy, robust aggregation certificates, AggregateRootQC or ApplyQC completion.
