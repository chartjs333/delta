# Tasks: Certificates, Robust Aggregation and Apply Consensus

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `007`.

## Phase 0: Mandatory certificate/arithmetic STOP

- [ ] T000 Verify no single-signer current model, pre-ISC seed, tolerance-based shard assembly, floating robust/apply arithmetic or device-speed domain weighting exists; record evidence before implementation.

## Phase 1: Certificate graph and canonical contracts

- [ ] T001 Define ISC, seed transcript, EC, APC, ParameterShardQC, AggregateRootQC and ApplyQC models in `src/deltatorrent/domain/certificates.py`.
- [ ] T002 Define exact parent graph, vote contexts, stable errors and validator-role scopes.
- [ ] T003 Define canonical ordered leaf tables/Merkle bodies for ISC and AggregateRootQC.
- [ ] T004 Create full-chain golden fixtures in `tests/fixtures/contracts/deltareduce_v1/008/`.
- [ ] T005 Add canonical byte/signature contract tests in `tests/contract/test_certificate_bytes.py`.
- [ ] T006 Implement standalone chain verifier in `src/deltatorrent/certificates/verifier.py`.
- [ ] T007 Implement persistent vote/replay guards for every certificate type.

## Phase 2: ISC and post-freeze randomness

- [ ] T008 Implement exact tuple validation/order/root and ISC QC in `src/deltatorrent/certificates/isc.py`.
- [ ] T009 Implement seed transcript port/fixture verifier bound to ISC in `src/deltatorrent/certificates/seed.py`.
- [ ] T010 Add duplicate/wrong-context/late tuple ISC tests.
- [ ] T011 Add seed-before-ISC state/property tests covering every command/message order.
- [ ] T012 Add conflicting ISC/double-vote/quorum-intersection tests.

## Phase 3: Exact norms and EligibilityCertificate

- [ ] T013 Define canonical norm profile, scale unification and overflow rules in `src/deltatorrent/robust/norms.py`.
- [ ] T014 Implement exact squared norm/integer-root or comparison primitives.
- [ ] T015 Implement deterministic trimming/tie order and clipping-limit calculation in `src/deltatorrent/robust/trimming.py`.
- [ ] T016 Implement EC builder/QC in `src/deltatorrent/certificates/ec.py`.
- [ ] T017 Add zero/equal/boundary/large norm golden tests in `tests/unit/test_exact_norms.py`.
- [ ] T018 Add EC ISC-subset, reason, gamma and parent-mutation tests.

## Phase 4: Bucketing, centered clipping and APC

- [ ] T019 Implement post-ISC seed-based canonical bucketing in `src/deltatorrent/robust/bucketing.py`.
- [ ] T020 Implement fixed-iteration exact centered clipping in `src/deltatorrent/robust/centered_clipping.py`.
- [ ] T021 Implement canonical coefficient quantization/common denominator in `src/deltatorrent/robust/coefficients.py`.
- [ ] T022 Implement robust transcript root in `src/deltatorrent/robust/transcript.py`.
- [ ] T023 Recompute/validate APC-specific accumulator safety proof.
- [ ] T024 Implement APC builder/QC in `src/deltatorrent/certificates/apc.py`.
- [ ] T025 Add bucket/iteration/tie/empty-bucket/zero-distance tests in `tests/unit/test_robust_plan.py`.
- [ ] T026 Add unsafe coefficient, wrong seed/EC/ISC and non-canonical weight tests.

## Phase 5: ParameterShardQC and AggregateRootQC

- [ ] T027 Integrate APC exact weights with integer shard reducers.
- [ ] T028 Implement ParameterShardQC vote/body verifier in `src/deltatorrent/certificates/parameter_qc.py`.
- [ ] T029 Implement complete ordered domain×shard coverage validator.
- [ ] T030 Implement AggregateRoot Merkle body/QC in `src/deltatorrent/certificates/aggregate_root.py`.
- [ ] T031 Add correct complete chain integration test in `tests/integration/test_certificate_chain.py`.
- [ ] T032 Add missing/duplicate/overlap/wrong-domain/wrong-epoch shard tests.
- [ ] T033 Add mandatory malicious mixed-view Frankenstein test in `tests/integration/test_frankenstein_rejection.py`.

## Phase 6: Deterministic outer apply

- [ ] T034 Define `ApplyArithmeticProfile`, exact coefficient/scales/rounding/weight-decay/Nesterov contract in `src/deltatorrent/apply/profile.py`.
- [ ] T035 Implement exact domain mixture in `src/deltatorrent/apply/domain_mix.py`.
- [ ] T036 Implement checked momentum and Nesterov state in `src/deltatorrent/apply/momentum.py` and `nesterov.py`.
- [ ] T037 Implement deterministic apply engine and canonical checkpoint serialization in `src/deltatorrent/apply/engine.py`.
- [ ] T038 Implement Apply vote/QC and persist-before-sign guard in `src/deltatorrent/apply/qc.py`.
- [ ] T039 Implement ApplyQC-bound artifact/current-pointer transaction in `src/deltatorrent/apply/publisher.py`.
- [ ] T040 Add apply golden vectors and four-validator byte/hash equality tests.
- [ ] T041 Add `DomainMixturePreservation` speed/ownership independence tests.
- [ ] T042 Add conflicting ApplyQC, wrong parent/profile/state and arithmetic overflow tests in `tests/integration/test_apply_qc_uniqueness.py`.
- [ ] T043 Add crash before/after sign/artifact/pointer matrix.

## Phase 7: Distribution, APIs and security boundaries

- [ ] T044 Register `aggregate-root-qc-v1` and `apply-qc-v1` in feature-005 policy registry.
- [ ] T045 Require ApplyQC for current-checkpoint distribution/use.
- [ ] T046 Define protobuf certificate/verify APIs in `proto/deltareduce/certificates/v1/certificates.proto`.
- [ ] T047 Implement standalone certificate/robust/apply CLI commands.
- [ ] T048 Add wrong-role/revoked/duplicate signer and replay corpus.
- [ ] T049 Add architecture test `tests/architecture/test_certificate_parentage_and_no_float_apply.py`.

## Final Phase

- [ ] T050 Add certificate/robust/apply telemetry and audit records.
- [ ] T051 Document full protocol in `docs/deltareduce/certificates-and-apply.md`.
- [ ] T052 Publish complete chain, Frankenstein rejection and ApplyQC evidence.
- [ ] T053 Run cross-artifact analysis, full quality gate and final Constitution Check.

## Dependencies

T000 blocks everything. T001–T007 block every certificate. T008–T012 block seed and descendants. T013–T018 block APC. T019–T026 block parameter committees. T027–T033 are the AggregateRootQC/Frankenstein gate. T034–T043 are the ApplyQC gate. T044–T049 complete policy/security integration. T050–T053 are final.

## Exit Gate

All tasks pass; full certificate chain is byte-deterministic; seed cannot precede ISC; robust plan is exact; mixed-view shard is rejected due to AggregateRootQC mismatch; four validators produce one identical ApplyQC; conflicting apply/current pointer cannot finalize.
