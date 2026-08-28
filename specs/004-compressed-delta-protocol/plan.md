# Implementation Plan: Canonical Fixed-Point Delta and Shard Protocol

**Branch**: `004-compressed-delta-protocol` | **Date**: 2026-08-27 | **Spec**: `spec.md`

**Constitution**: 2.1.0

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Summary

Implement the mandatory `int16-fixed-v1` protocol as runtime-neutral schemas and fixtures, an
authoritative portable C++ encoder/shard/checked-bound implementation, an independently designed
Python fixture producer and Java opaque-byte conformance tests. Accepted q values remain integers
through the feature-003 native runtime. Transport, robust aggregation, Apply and residual runtime
semantics remain later-feature work.

No production source may be created until Phase 0 emits a passing content-addressed
`evidence/preflight.json` binding the exact feature-003 merge/source/evidence/report, accepted
Formal GO and PO-A1/PO-A2/PO-A3 artifacts, the current SpecKit source tree and a zero-finding
float-consensus/legacy-path scan.

## Exact predecessor boundary

- feature-003 merge commit: `53da4d3c0b236726566fb242fdcae84032b42679`;
- feature-003 final source: `189e5f155b787c2d1d391630fc599b67ea366bba`;
- feature-003 evidence overlay: `f4f2101969d14709834ab6b6d60e88755d710334`;
- feature-003 compatibility SHA-256:
  `2cd392aafaba1ab70cc0a6919cae9580955c742f9f92296f54a570af29dca769`;
- accepted formal source: `1e6e0f6f70056161d95933e71494ec390c7c1151`;
- accepted Formal GO report SHA-256:
  `b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab`.

Any mismatch is an unconditional STOP.

## Technical context

- C++20/23 is authoritative for profile validation, exact rational scale handling, signed
  ties-to-even quantization, little-endian INT16 bytes, shard coverage/envelopes, bounded parsing
  and checked INT64/INT128 proof-instance validation.
- Python consumes feature-002 normalized inputs and independently produces fixture expectations
  using exact integer/Fraction logic. It is an oracle, not consensus acceptance code.
- Java JDK 25/26 checks FFM/direct/copy bounds and preserves canonical envelopes byte-for-byte. It
  does not convert q values to float or aggregate them.
- The mandatory signed lattice and scale table are shared by all workers and fixed by RoundConfig.
- Residual/error-feedback runtime is unsupported and rejected in feature 004.
- Shards are immutable bounded bytes; no pickle, object dtype, executable payload or public network
  is required by tests.

## Constitution check

| Principle | Design response | Gate |
| --- | --- | --- |
| II — formal first | Exact GO/artifacts and theorem boundary are Phase 0 inputs | `evidence/preflight.json` |
| IV — fixed work | Manifest binds ticket, `A_j=H`, domain, parent, schema and config | contract fixtures |
| V — integer arithmetic | One q lattice; checked product/prefix/final bounds; no q→float | native and architecture tests |
| VI — lineage | Profile/proof/shards bind exact RoundConfig/ticket/schema parents | context mismatch corpus |
| VIII — plane separation | Worker q shards are reduce-plane-only artifacts | publisher denylist |
| IX — safe boundaries | Bounded parser before allocation; no pickle | fuzz/security corpus |
| XI — evidence | Deterministic metrics, mutants and content-addressed exit report | final gate |
| XII — replaceability | C++/Python/Java agree on canonical bytes | cross-language vectors |

**Pre-implementation result**: pending `evidence/preflight.json`. No source task may begin while
that file is missing, stale or `FAIL`.

## Formal proof-instance boundary

The accepted Lean artifact is `formal/proofs/DeltaReduce/FixedPoint.lean`.

- PO-A1: `signedProductBound` and `intermediateProductFits` bind `|a|≤A`, `|q|≤Q` and the selected
  multiplication width.
- PO-A2: `flatAccumulatorBound` and `everyCanonicalPrefixFits` bind `Nmax`, canonical incremental
  sums and the final accumulator width `M`.
- PO-A3: `ReducedRational`, denominator/coprime/common-denominator theorems,
  `commonDenominatorNumeratorSafe` and the formal canonical coefficient rounding theorems bind
  later rational coefficient arithmetic.

PO-A3 is not evidence for worker ties-to-even quantization. That rule is frozen in the feature-004
protocol and checked by independent exact-byte implementations. Each concrete proof instance
records theorem IDs, `Q`, `A`, `Nmax`, product/partial/final widths, denominator metadata and exact
profile/schema/config hashes. `maximum-safe` must pass and `first-unsafe` must reject.

## Architecture and data flow

```text
feature-002 normalized reference input
        │
        ├──────────────▶ independent Python fixture producer
        │                              │
        ▼                              ▼ exact-byte comparison
portable C++ FixedPointEncoder ──▶ canonical q stream ──▶ C++ ShardWriter
        ▲                                                   │
RoundConfig ─▶ profile + scale table + proof instance       ▼
                                              bounded shard envelopes
                                                          │
                                       C++ streaming verifier/reducer
                                                          │
                                       feature-003 state/effect/WAL path

Java FFM/direct/copy conformance ── preserves envelopes byte-for-byte
```

## Project structure

```text
delta-protocol/
  schemas/004/
    fixed-point-profile-v1.json
    scale-table-v1.json
    encoded-contribution-manifest-v1.json
    encoded-shard-v1.json
    shard-plan-v1.json
    accumulator-proof-instance-v1.json
  fixtures/004/{valid,invalid,cross-language}/

delta-core-cpp/
  include/delta/fixedpoint/{profile,scale,rounding,checked,encoder,bounds}.hpp
  include/delta/shards/{plan,envelope,reader}.hpp
  src/fixedpoint/
  src/shards/
  tests/
  fuzz/

delta-worker-python/
  src/deltatorrent/reference/{fixedpoint_encoder,accumulator_proof}.py
  tests/{contract,fixtures}/

delta-node-java/src/test/java/io/deltareduce/node/
  FixedPointEnvelopeConformance.java
  DirectCopyParity.java
  MalformedEnvelopeConformance.java
```

## Implementation sequence

1. Verify exact predecessor, Formal GO/theorems, formal impact and zero forbidden paths.
2. Freeze signed range, rational scale, per-segment/shard rule, signed ties-to-even, zero,
   little-endian layout, parser bounds and accumulator selection in runtime-neutral schemas.
3. Commit valid/invalid/cross-language vectors before optimized code.
4. Implement the portable C++ encoder and checked proof-instance validation.
5. Implement deterministic C++ shard planning, envelopes and bounded streaming parser.
6. Implement the independent Python fixture producer without translating C++ line-for-line.
7. Add Java direct/copy preservation and malformed-envelope conformance.
8. Stream q directly through the feature-003 runtime and compare state/effect/WAL behavior.
9. Run GCC/Clang, sanitizers, fuzz, refinement/mutant and final compatibility gates.

## Mandatory golden corpus

The corpus covers positive/negative zero, smallest nonzero, positive/negative half-way, both signed
limits, first out-of-range values, huge numerator, zero denominator, non-reduced fraction, wrong
profile/schema/ticket, truncated/oversized shard, duplicate/conflicting ordinal, overlap, gap and
trailing bytes. Each case records normalized source, profile bytes, q integers, little-endian
payload, envelope, leaf hashes, Merkle root, accept/reject code and proof-instance result.

## Test strategy

- independent C++ and Python exact-byte encoders;
- GCC/Clang C++20/23 plus x86_64/aarch64 where a pinned runner is available;
- endian, signed limit, zero and ties-to-even vectors;
- exact schema coverage and arbitrary shard arrival order;
- bounded malicious length/range/version/trailing-data parser corpus;
- INT64/INT128 maximum-safe/first-unsafe and proof invalidation cases;
- Java JDK 25/26 direct/copy preservation;
- ASan/UBSan, parser fuzz and allocation limits;
- feature-003 direct-q state/effect/WAL regression and formal refinement traces;
- architecture checks forbidding float contribution formats, per-worker scales and q→float reduce.

## Rollout and rollback

Roll out `int16-fixed-v1` as the only accepted profile. Protocol IDs and golden bytes are immutable.
Rollback disables the profile/config and aborts affected rounds; it never reinterprets committed
bytes, saturates a value or silently falls back to float. Feature 005 remains blocked until the
feature-004 exit report is `PASS`.

## Out of scope

- residual/error-feedback runtime;
- P2P, Netty/TLS, regional hierarchy or routing;
- robust clipping/APC weights and full certificate hierarchy;
- ApplyQC or outer optimizer;
- QLoRA tuning, Top-K, PowerSGD or low-rank compression;
- quality, WAN or memory achievement claims.

## Exit gate

All normative tasks and runtime obligations pass; independent encoders emit identical bytes;
shard/parser properties and maximum-safe/first-unsafe instances behave exactly; accepted q values
remain integer through feature 003; state/effect/WAL results are unchanged or explicitly versioned
with compatibility evidence; no accepted float/dynamic-scale/residual path exists; final
Constitution 2.1.0 and `REFINEMENT_ONLY` compatibility checks pass.
