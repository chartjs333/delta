# Implementation Plan: Сжатый и шардированный delta protocol

**Branch**: `004-compressed-delta-protocol` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Ввести отдельный `compression` subsystem с pure codec contracts и committed golden fixtures. Encoding формирует bounded immutable shards; decoding восстанавливает FP32 stream/tensors. Worker получает transactional residual repository, coordinator — codec registry и validating decode stage перед существующим reducer. Raw profile обеспечивает backward-compatible path.

## Technical Context

- Tensor math: PyTorch CPU reference; optional accelerator implementation behind same port.
- Payload: custom canonical binary envelope или safetensors-compatible bounded files с отдельным canonical JSON manifest; формат утверждается до implementation.
- INT8: symmetric blockwise scale, deterministic rounding, no `-128`.
- Hashing: SHA-256 manifest/shards; content IDs независимы от transport.
- Residual persistence: safe FP32 tensors, compare-and-set version, candidate journal.
- Limits: max manifest/shard/tensor/total bytes и max element counts from trusted config.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Codec error contract и decode-before-FP32-reduce | Reference/conformance tests |
| Plane separation | Compression меняет representation, не destination; local updates остаются reduce-only | Architecture test |
| Content-addressed state | Manifest, shards, profile и residual versions hashed | Corruption tests |
| WAN efficiency | Payload ratio и timings измеряются, не предполагаются | Size benchmark fixture |
| Bounded/reversible | Limits, versioned profiles, raw fallback, transactional residual | Fault matrix |
| Safe trust boundary | Bounded parser, no pickle/object dtype | Adversarial corpus |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
LocalDelta + committed residual
          │
          ▼
  CandidateBuilder: u = Δ + r
          │
          ▼
 CodecRegistry.encode(profile)
          │
          ├── EncodedUpdateManifest
          ├── shard[0..N]
          └── candidate next residual
                    │
           accepted receipt CAS
                    ▼
          committed ResidualState

Coordinator intake → bounded shard verify → decode FP32 → existing reducer
```

## Project Structure

```text
src/deltatorrent/
  compression/
    codec.py
    registry.py
    raw_fp32.py
    fp16.py
    int8_blockwise.py
    sharding.py
    envelope.py
    limits.py
    residual.py
  coordinator/decoding.py
  worker/compression.py
  domain/compression.py
proto/deltatorrent/coordinator/v1/coordinator.proto
tests/
  unit/test_int8_codec.py
  unit/test_sharding.py
  unit/test_residual_state.py
  contract/test_codec_conformance.py
  security/test_encoded_payload_parser.py
  integration/test_compressed_round.py
  integration/test_residual_transactions.py
benchmarks/compression/
docs/compression-protocol.md
```

## Implementation Sequence

1. Утвердить profile/envelope schemas, limits и golden fixtures.
2. Реализовать raw и FP16 profiles; подтвердить compatibility path.
3. Реализовать deterministic INT8 reference codec и numerical tests.
4. Реализовать schema-driven segmentation/sharding и bounded parser.
5. Реализовать residual candidate/CAS repository и crash-safe protocol.
6. Интегрировать worker encoder и coordinator decoder registry.
7. Прогнать mixed-codec rounds, payload-size fixture и adversarial corpus.
8. Повторить constitution/compatibility analysis.

## Test Strategy

- **Golden**: exact bytes/metadata для известных tensors каждого profile.
- **Property/numerical**: random finite tensors, zero blocks, extrema, error bound, residual recurrence.
- **Parser security**: truncated/duplicate/oversized counts, hash mismatch, NaN scale, illegal dtype/name/path.
- **Transactional**: crashes before/after candidate, upload, receipt и residual CAS.
- **Integration**: mixed-codec round against decode-then-reduce reference; reordered shards.
- **Regression**: все feature `003` tests через raw profile.
- **Microbenchmark**: encoded bytes и encode/decode time записываются как evidence, без CI performance flakiness.

## Observability

Per update/profile: raw/encoded bytes, ratio, block/shard count, encode/decode duration, L2/max error, residual L2, parser rejection reason. Round result перечисляет profiles и decoded content hashes.

## Rollout and Rollback

Default сначала `raw-fp32-v1`; FP16/INT8 включаются round allowlist. Rollback исключает lossy profile из новых rounds, сохраняя decoder для чтения старых artifacts. Residual profile нельзя silently переиспользовать; rollback выполняет documented reset/migration decision.

## Risks and Mitigations

- **Residual double advance**: candidate journal + exact accepted receipt CAS.
- **Platform-dependent rounding**: CPU reference/golden bytes и kernel conformance.
- **Decompression bomb**: declared hard limits checked before allocation.
- **Small-tensor overhead**: deterministic packing и ratio gate на representative fixture.
- **Numerical regression**: raw control, error metrics и later token-matched benchmark.

## Exit Gate

Conformance, adversarial parser, residual crash/retry и mixed-codec reference suites проходят; INT8 payload ratio gate достигнут на committed fixture; raw compatibility зелёная; quality gates и final Constitution Check завершены.
