# Tasks: Canonical Fixed-Point Delta and Shard Protocol

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `003-bft-round-state-machine`.

## Phase 0: Legacy codec STOP

- [ ] T000 Remove/block all authoritative `raw-fp32`, `fp16`, decode-to-FP32 and per-worker dynamic-scale aggregation contracts; record search evidence in `specs/004-compressed-delta-protocol/evidence/preflight.md`.

## Phase 1: Profiles and golden contracts

- [ ] T001 Define versioned `FixedPointProfile` and `int16-fixed-v1` config in `src/deltatorrent/fixedpoint/profile.py` and `configs/fixedpoint/int16-fixed-v1.json`.
- [ ] T002 Define canonical integer/rational scale table in `src/deltatorrent/fixedpoint/scales.py`.
- [ ] T003 Define exact ties-to-even signed rounding in `src/deltatorrent/fixedpoint/rounding.py`.
- [ ] T004 Define `EncodedContributionManifest`, `EncodedShard` and proof models in `src/deltatorrent/domain/encoded_contribution.py`.
- [ ] T005 Create mandatory source/q/envelope/root fixtures in `tests/fixtures/contracts/deltareduce_v1/004/`.
- [ ] T006 Implement an independent fixture encoder used only by contract tests in `tests/reference/fixedpoint_encoder.py`.
- [ ] T007 Add canonical-byte contract tests in `tests/contract/test_fixedpoint_protocol_bytes.py`.

## Phase 2: Reference encoding

- [ ] T008 Implement exact normalization input adapter and encoder in `src/deltatorrent/fixedpoint/encoder.py`.
- [ ] T009 Implement fail-closed source/range/finite validation in `src/deltatorrent/fixedpoint/validation.py`.
- [ ] T010 Add positive/negative half-way, zero and signed-limit tests in `tests/unit/test_fixedpoint_rounding.py`.
- [ ] T011 Add out-of-range/profile/schema/config mismatch tests in `tests/unit/test_fixedpoint_encoder.py`.
- [ ] T012 Verify optimized/portable encoder byte identity hook in `tests/contract/test_encoder_implementation_conformance.py`.

## Phase 3: Deterministic shards

- [ ] T013 Implement exact schema-covering shard planner in `src/deltatorrent/shards/plan.py`.
- [ ] T014 Implement canonical bounded envelope writer in `src/deltatorrent/shards/envelope.py` and `writer.py`.
- [ ] T015 Implement streaming reader and context verifier in `src/deltatorrent/shards/reader.py` and `verifier.py`.
- [ ] T016 Add gap/overlap/tensor-boundary property tests in `tests/unit/test_shard_plan.py`.
- [ ] T017 Add duplicate/reorder/corrupt/truncated/oversized tests in `tests/unit/test_shard_verifier.py`.
- [ ] T018 Add malicious parser corpus in `tests/security/test_shard_parser_corpus.py`.

## Phase 4: Accumulator safety proof

- [ ] T019 Extend checked intermediate multiply/add model in `src/deltatorrent/fixedpoint/checked.py`.
- [ ] T020 Implement content-addressed per-shard safety proof in `src/deltatorrent/fixedpoint/bounds.py`.
- [ ] T021 Bind proof hash and coefficient headroom into `RoundConfig` validation.
- [ ] T022 Add INT64/INT128 maximum-safe/first-unsafe fixtures in `tests/unit/test_accumulator_proof.py`.
- [ ] T023 Add proof invalidation tests for profile/count/coefficient/schema changes.

## Phase 5: Feature-003 integration

- [ ] T024 Implement bounded canonical q iterator for reducers in `src/deltatorrent/shards/reader.py`.
- [ ] T025 Remove any q→float conversion from `src/deltatorrent/reduce/`.
- [ ] T026 Add direct streaming q-reduce integration tests in `tests/integration/test_q_stream_reduce.py`.
- [ ] T027 Rerun and pin the four-aggregator/100-ticket hash regression in `tests/integration/test_100_ticket_bit_identity.py`.
- [ ] T028 Add architecture test `tests/architecture/test_no_float_consensus_codec.py`.
- [ ] T029 Add distribution denylist regression for worker encoded shards.

## Phase 6: Optional residual profile

- [ ] T030 Define disabled-by-default residual profile and exact inclusion-certificate rule in `src/deltatorrent/fixedpoint/residual.py`.
- [ ] T031 Implement candidate/prior/current atomic state and exact-byte retry.
- [ ] T032 Add rejected/late/aborted/unknown/restart tests in `tests/unit/test_residual_transaction.py`.
- [ ] T033 Add schema/profile/ticket lineage reset/migration hard-failure tests.

## Final Phase: Validation and documentation

- [ ] T034 Add profile/proof/shard metrics and CLI inspect/verify commands.
- [ ] T035 Document protocol and golden vectors in `docs/deltareduce/fixed-point-protocol.md`.
- [ ] T036 Publish exit evidence in `specs/004-compressed-delta-protocol/evidence/exit-gate.md`.
- [ ] T037 Run cross-artifact analysis, full quality gate and final Constitution Check.

## Dependencies

- T000 blocks all implementation.
- T001–T007 block encoder/shard work.
- T008–T012 block commitment integration.
- T013–T018 block availability and streaming reduce.
- T019–T023 block any accepted `RoundConfig` using the profile.
- T024–T029 are the mandatory integration gate.
- T030–T033 are optional functionality but mandatory if residual mode ships.
- T034–T037 are final.

## Exit Gate

All mandatory tasks pass; two encoders emit identical bytes; shard and parser properties hold; maximum-safe/first-unsafe accumulator cases behave exactly; q-values reach the feature-003 reducer without float conversion; 100-ticket hashes remain bit-identical.
