# Runtime Profile: 004 Canonical Fixed-Point Delta Protocol

**Primary runtime**: C++ fixed-point/shard library  
**Supporting runtimes**: Python fixture producer, Java opaque transport/conformance  
**Formal impact**: `REFINEMENT_ONLY` with concrete Lean proof instantiation

## Allocation

- C++ implements canonical scale tables, signed ties-to-even rounding, INT16 q encoding, bounded shard envelopes, streaming verification and checked INT64/INT128 accumulation helpers.
- Python supplies normalized pseudo-gradient reference inputs and an independent fixture encoder where feasible; it is not authoritative for consensus acceptance.
- Java validates outer buffer/ABI bounds and passes canonical shard bytes unchanged. It must not decode q-values to floating point for aggregation.

## Shared-lattice requirement

All accepted workers in a round use the exact `FixedPointProfile` and scale table committed by RoundConfig. Per-worker dynamic scale, FP16/FP32 fallback and implicit saturation are forbidden.

## Proof-instance boundary

Every concrete profile/config produces content-addressed evidence for:

- q range `Q`;
- coefficient envelope `A`;
- maximum terms `Nmax`;
- multiplication and accumulator widths;
- common denominator and rounding contract;
- exact theorem IDs and precondition values;
- schema/profile/config hashes.

C++ validates these preconditions before ticketing and again for actual APC coefficients in feature 008.

## Cross-language conformance

Golden vectors contain source representation, expected q integers, exact little-endian bytes, shard envelopes, hashes, Merkle root, accepted/rejected status and accumulator proof result. C++, Python reference and Java parser/transport views must agree exactly.

## Memory and streaming

Reducers consume bounded verified q streams. A full floating model-sized decode buffer is prohibited. Parser allocation is bounded before payload access and fuzzed against length/range/version attacks.

## Exit additions

- GCC and Clang emit identical bytes/hashes;
- Java direct/copy ingress preserves bytes;
- first unsafe profile/config is rejected;
- no q-to-float reduce symbol/path exists;
- parser fuzz and sanitizer corpus pass;
- feature-003 100-ticket hashes remain stable or are versioned with formal compatibility evidence.
