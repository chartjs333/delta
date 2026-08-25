# Implementation Plan: Certificates, Robust Aggregation and Apply Consensus

**Branch**: `008-certificates-and-consensus` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Implement the complete parent-certificate chain, exact post-ISC randomness/bucketing, canonical norm/trimming/centered-clipping plan, parameter-shard QCs, atomic AggregateRootQC and deterministic outer-model ApplyQC. Extend feature-005 certification policies so only ApplyQC-certified checkpoints become current/distributable as applied models.

## Technical Context

- Reuse BFT vote guards/QC verification from feature 003.
- Canonical certificate bodies and Merkle tables use existing hash/serialization rules.
- Norm and robust-policy reference implementation uses arbitrary-precision integers/rationals with explicit fixed-width output coefficients.
- Seed source is an adapter behind a transcript-verification port; mandatory tests use deterministic threshold-share/beacon fixtures.
- Parameter committees consume only q shards plus finalized APC.
- Apply reference path uses checked integer/fixed-point arithmetic and canonical checkpoint serialization; optimized kernels must match exact bytes.
- Durable publication uses content-addressed artifacts and current-pointer CAS keyed by parent/ApplyQC.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Input freeze | ISC required structurally before seed/EC/APC | Property/model tests |
| Certificate lineage | Explicit parent roots in every body | Mutation/mixed-view corpus |
| Integer arithmetic | Exact norms, weights, reduce and apply | No-float architecture gate |
| BFT uniqueness | Persist-before-sign and `2f+1` QCs | Double-vote/apply tests |
| Domain mixture | Separate domain shards until exact apply | Speed-independent fixture |
| Atomic model | Current pointer requires ApplyQC | Crash/CAS matrix |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Available tuple set
      │
      ▼
ISCBuilder/QC ──▶ SeedTranscript
      │                 │
      ▼                 ▼
ExactNormEngine ──▶ EligibilityEngine ──▶ EC
                                      │
                 Bucket/CenteredClipPlanner ──▶ APC
                                      │
                         Parameter committees
                                      │
                            ParameterShardQCs
                                      │
                           AggregateRootAssembler/QC
                                      │
                         DeterministicApplyEngine
                                      │
                              ApplyQC + current CAS
```

## Project Structure

```text
src/deltatorrent/domain/certificates.py
src/deltatorrent/certificates/
  isc.py
  seed.py
  ec.py
  apc.py
  parameter_qc.py
  aggregate_root.py
  verifier.py
  replay.py
src/deltatorrent/robust/
  norms.py
  trimming.py
  bucketing.py
  centered_clipping.py
  coefficients.py
  transcript.py
src/deltatorrent/apply/
  profile.py
  domain_mix.py
  momentum.py
  nesterov.py
  engine.py
  qc.py
  publisher.py
proto/deltareduce/certificates/v1/certificates.proto
tests/contract/test_certificate_bytes.py
tests/unit/test_exact_norms.py
tests/unit/test_robust_plan.py
tests/integration/test_certificate_chain.py
tests/integration/test_frankenstein_rejection.py
tests/integration/test_apply_qc_uniqueness.py
tests/architecture/test_certificate_parentage_and_no_float_apply.py
```

## Implementation Sequence

1. Freeze all certificate/vote/body canonical schemas and parent graph.
2. Implement ISC builder/verifier and structural seed gate.
3. Implement seed transcript adapter/fixtures and post-ISC derivation.
4. Implement exact norm evidence, trimming and EC.
5. Implement bucketing, fixed-iteration centered clipping, coefficient quantization and APC-specific bound proof.
6. Integrate parameter committees with APC and form ParameterShardQCs.
7. Implement aggregate completeness/Merkle root and AggregateRootQC.
8. Implement deterministic domain mix/outer optimizer, ApplyQC and current-pointer transaction.
9. Register distribution certification policies and run malicious/recovery suites.
10. Publish full chain evidence and final Constitution Check.

## Test Strategy

- Golden certificate/vote/transcript bytes and signature sets.
- State/property tests forbidding seed or descendants before ISC.
- Exact integer/rational norm and robust-policy boundary/tie fixtures.
- Bucket permutation and fixed-iteration transcript equality.
- APC coefficient/accumulator unsafe cases.
- Parameter QC wrong parent/view/domain/shard/epoch corpus.
- Complete/incomplete/duplicate/overlap aggregate table tests.
- Explicit Frankenstein mixed-view test.
- Apply arithmetic golden vectors, four-validator hash equality, double-apply/crash/replay matrix.
- Distribution policy strength/downgrade tests.

## Observability

Expose certificate roots/parents, signer counts/epochs, seed transcript status, norm/eligibility/bucket summaries, robust iteration/weight/headroom summaries, shard-QC completeness, mixed-view rejects, apply validator hash agreement and current-pointer outcome. Do not log worker vector bytes or private keys.

## Rollout and Rollback

Run certificate/robust/apply pipeline in deterministic shadow mode against existing aggregate fixtures before enabling current-pointer publication. Rollback disables future protocol version/rounds and preserves parent checkpoint. It never accepts a weaker certificate or reinterprets a finalized chain.

## Risks and Mitigations

- **Robust algorithm ambiguity**: exact versioned formulas, iteration count, tie order and golden vectors.
- **Norm overflow**: arbitrary-precision reference evidence plus bounded coefficient output.
- **Seed manipulation**: structural ISC parent and transcript verification.
- **Frankenstein assembly**: full parent tuple in every shard QC plus ordered Merkle table.
- **Apply nondeterminism**: portable checked reference and byte conformance for optimized paths.
- **Double current pointer**: persist-before-sign plus parent/height/ApplyQC compare-and-set.

## Exit Gate

Full ISC→EC→APC→ParameterShardQC→AggregateRootQC→ApplyQC chain is byte-deterministic; malicious mixed-view shard is rejected; four apply validators agree exactly; conflicting apply cannot finalize; distribution policy requires appropriate QC; full quality and Constitution gates pass.
