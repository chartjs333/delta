# Implementation Plan: Certificates, Robust Aggregation and Apply Consensus

**Branch**: `008-certificates-and-consensus` | **Date**: 2026-08-23 | **Spec**: `spec.md`

**Constitution**: 2.1.0

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

**Exact predecessor**: feature-007 merge `2054f31ef0f6750645b924ef337a35d1737c619d`,
verified source `781cdbd76d812bf66323a3d1d11ca93f4b9d8333`, evidence overlay
`08a118c5d52a0a4f6658249cb65ea15e538904c2` and final-report SHA-256
`2b45bf2dba25b15db624a02ee11e530a967961220e414ab04054428d44f59ef3`.

## Summary

Implement the complete parent-certificate chain, exact post-ISC randomness/bucketing, canonical norm/trimming/centered-clipping plan, parameter-shard QCs, atomic AggregateRootQC and deterministic outer-model ApplyQC. Extend feature-005 certification policies so only ApplyQC-certified checkpoints become current/distributable as applied models.

## Technical Context

- Reuse native BFT vote guards/QC verification from feature 003 and the durable native runtime.
- Runtime-neutral JSON schemas and canonical binary bodies replace protobuf/Python authority.
- C++ norm and robust-policy authority uses checked integers/canonical rationals with explicit fixed-width output coefficients.
- Seed source is an adapter behind a transcript-verification port; mandatory tests use deterministic threshold-share/beacon fixtures.
- Parameter committees consume only q shards plus finalized APC through bounded native APIs.
- C++ apply uses checked integer/fixed-point arithmetic and canonical checkpoint serialization; optimized kernels must match exact bytes.
- The native runtime owns vote/apply WAL recovery and current-pointer CAS keyed by parent/ApplyQC.
- Java 25/26 owns authenticated opaque delivery, opaque timers and bounded artifact effects only.
- Python remains worker-local and has no validator, certificate, robust, root or apply authority.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Input freeze | ISC required structurally before seed/EC/APC | Property/model tests |
| Certificate lineage | Explicit parent roots in every body | Mutation/mixed-view corpus |
| Integer arithmetic | Exact norms, weights, reduce and apply | No-float architecture gate |
| BFT uniqueness | Persist-before-sign and `2f+1` QCs | Double-vote/apply tests |
| Domain mixture | Separate domain shards until exact apply | Speed-independent fixture |
| Atomic model | Current pointer requires ApplyQC | Crash/CAS matrix |

**SpecKit reconciliation result**: PASS. Production implementation remains blocked until the exact
predecessor/Formal GO/forbidden-authority preflight and canonical schema gate pass.

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

## Mandatory preflight

No production source may be added until content-addressed evidence rederives the exact feature-007
merge/source/evidence/report chain, revalidates Formal GO and the feature-004/005/006 identities used
by certificate arithmetic, distribution and hierarchy, proves zero formal source diff, classifies the
work `REFINEMENT_ONLY`, and finds zero pre-ISC randomness, floating robust/apply arithmetic,
single-signer current path or Java/Python certificate authority.

## Project Structure

```text
delta-protocol/
  schemas/008/{input-set-certificate,seed-transcript,norm-evidence,
               eligibility-certificate,aggregation-plan-certificate,
               parameter-shard-qc,aggregate-root-qc,apply-arithmetic-profile,
               apply-candidate,apply-qc,current-pointer-command}-v1.json
  fixtures/008/{valid,invalid,cross-language}/
delta-core-cpp/
  include/delta/{certificates,robust,apply}/
  src/{certificates,robust,apply}/
  tests/certificates_*.cpp
  fuzz/certificate_contract_fuzz.cpp
delta-runtime-cpp/
  src/certificates/{vote_wal,certificate_recovery}.cpp
  src/apply/{apply_wal,artifact_transaction,current_pointer}.cpp
delta-ffi/
  src/{certificates_abi,apply_abi}.cpp
  tests/certificates_abi_test.cpp
delta-node-java/src/main/java/io/deltareduce/node/
  certificates/{AuthenticatedCertificateTransport,NativeCertificateVerifier,
                SeedShareTransport,CertificateTimerService}.java
  apply/{ArtifactEffectAdapter,CurrentCheckpointPublisher,ApplyTelemetry}.java
specs/008-certificates-and-consensus/
  scripts/ evidence/ tests/
```

## Implementation Sequence

1. Pass exact feature-007 predecessor, Formal GO and forbidden-authority preflight.
2. Freeze runtime-neutral certificate/vote/effect schemas, bytes, IDs and exact parent graph.
3. Generalize native persist-before-send vote lifecycle to every certificate/QC class.
4. Implement ISC builder/verifier and structurally unavailable pre-ISC seed path.
5. Implement exact norm evidence, EC, bucketing, centered clipping and APC proof revalidation.
6. Integrate parameter committees and exact required matrix into ShardQC/AggregateRootQC.
7. Implement deterministic apply, ApplyQC, artifact transaction and current-pointer CAS/replay.
8. Expose bounded C ABI and Java opaque transport/timer/artifact adapters without authority.
9. Export legal/illegal/crash traces, kill production mutants and pass exact formal refinement.
10. Publish exact-source compiler/JDK/sanitizer/fuzz evidence and final Constitution Check.

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
