# Implementation Plan: Canonical Fixed-Point Delta and Shard Protocol

**Branch**: `004-compressed-delta-protocol` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Replace the legacy decode-to-FP32 codec design with a canonical integer protocol. Implement `int16-fixed-v1`, deterministic scale tables and shard envelopes, bounded streaming parsing, exact accumulator proofs and portable golden vectors. Preserve feature-003 hashes through direct q-value streaming.

## Technical Context

- Python reference encoder uses exact `Fraction`/integer operations for scale and rounding fixtures; production worker adapter may use optimized kernels only after byte conformance.
- Mandatory q storage is signed INT16 with explicit little-endian layout.
- Accumulator proof and reference reduce use checked Python integers emulating INT64/INT128 limits.
- Shards are immutable safe bytes; no pickle, object dtype or executable payload.
- Merkle/hash rules reuse feature 003.
- Residual mode is an optional disabled profile and cannot affect mandatory exit gates.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Integer consensus | q-values stream directly to checked accumulators | Float-path architecture test |
| Fixed work | Manifest binds ticket, `A_j=H`, domain and config | Contract fixtures |
| Determinism | Exact scale/rounding/layout and golden bytes | Independent encoder test |
| FixedPointSafety | Content-addressed per-config bound proof | Boundary corpus |
| Plane separation | Encoded worker shards denied by swarm | Media-type test |
| Replaceable adapters | Reference/optimized encoder share fixtures | Conformance suite |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
NormalizedPseudoGradient
        │
        ▼
FixedPointEncoder ──▶ q-vector ──▶ DeterministicShardWriter
        │                              │
        ▼                              ▼
Conformance metrics             shard envelopes + Merkle root
                                       │
                        storage/availability from feature 003
                                       │
                                       ▼
                         BoundedShardReader ──▶ checked integer reducer

RoundConfig ──▶ ScaleTable + AccumulatorSafetyProof
```

## Project Structure

```text
src/deltatorrent/fixedpoint/
  profile.py
  scales.py
  rounding.py
  encoder.py
  checked.py
  bounds.py
  residual.py
src/deltatorrent/shards/
  plan.py
  envelope.py
  writer.py
  reader.py
  verifier.py
src/deltatorrent/domain/encoded_contribution.py
tests/contract/test_fixedpoint_protocol_bytes.py
tests/unit/test_fixedpoint_rounding.py
tests/unit/test_shard_plan.py
tests/unit/test_accumulator_proof.py
tests/integration/test_q_stream_reduce.py
tests/security/test_shard_parser_corpus.py
tests/architecture/test_no_float_consensus_codec.py
configs/fixedpoint/int16-fixed-v1.json
docs/deltareduce/fixed-point-protocol.md
```

## Implementation Sequence

1. Freeze exact profile, scale-table, rounding and source canonicalization rules.
2. Commit independent golden vectors before optimized implementation.
3. Implement reference encoder and fail-closed range behavior.
4. Implement deterministic shard plan/envelopes and bounded reader/verifier.
5. Implement content-addressed accumulator safety proof and validation.
6. Integrate direct q streaming with feature-003 reducer and rerun bit-identity gate.
7. Add optional residual state only after mandatory profile gates pass.
8. Add metrics, CLI inspection and documentation.

## Test Strategy

- Golden bytes across two independent encoder implementations.
- Positive/negative half-way rounding and signed-range boundaries.
- Property tests for exact schema coverage and arbitrary shard arrival order.
- Malicious length/range/version/trailing-data parser corpus.
- INT64/INT128 maximum-safe/first-unsafe proof corpus.
- Architecture test forbidding accepted float codecs or q→float reduce conversion.
- Feature-003 100-ticket hash regression.
- Optional residual exact-retry and inclusion-certificate transaction tests.

## Observability

Record profile/scale/proof hashes, source and encoded sizes, range failures, zero counts, encoding/verifying duration, per-shard sizes, accumulator headroom and parser rejection reason. Quantization error diagnostics remain worker-local evidence and do not enter consensus arithmetic.

## Rollout and Rollback

Roll out `int16-fixed-v1` as the only accepted profile. Protocol IDs and golden bytes are immutable. Rollback disables an entire profile/config and aborts affected rounds; it never reinterprets committed shard bytes or silently falls back to float.

## Risks and Mitigations

- **Scale ambiguity**: integer/rational representation and committed table.
- **Optimized kernel drift**: mandatory byte conformance against portable reference.
- **Overflow under later APC weights**: reserve declared coefficient headroom and revalidate proof in feature 008.
- **Parser resource attack**: limits before allocation and streaming verification.
- **Residual double advance**: disabled by default; two-phase exact-certificate commit if enabled.

## Exit Gate

Golden encoders, shard parser/coverage, accumulator-bound and direct-q integration suites pass; feature-003 100-ticket hashes remain unchanged; no accepted float/dynamic-scale path exists; quality and Constitution checks pass.
