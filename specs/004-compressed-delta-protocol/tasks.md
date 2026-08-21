# Tasks: Сжатый и шардированный delta protocol

**Input**: `spec.md`, `plan.md`, constitution и завершённые `001–003`.

## Phase 1: Contracts and limits

- [ ] T001 Определить codec/profile/envelope/residual domain models в `src/deltatorrent/domain/compression.py`.
- [ ] T002 Определить hard parsing/resource limits в `src/deltatorrent/compression/limits.py`.
- [ ] T003 Создать codec interface/registry в `src/deltatorrent/compression/codec.py` и `registry.py`.
- [ ] T004 [P] Добавить canonical golden vectors в `tests/fixtures/contracts/compression/`.
- [ ] T005 Обновить compressed update fields в `proto/deltatorrent/coordinator/v1/coordinator.proto`.
- [ ] T006 Добавить schema/proto/golden contract tests в `tests/contract/test_codec_conformance.py`.

## Phase 2: Core codecs and sharding

- [ ] T007 Реализовать `raw-fp32-v1` в `src/deltatorrent/compression/raw_fp32.py`.
- [ ] T008 [P] Реализовать `fp16-v1` в `src/deltatorrent/compression/fp16.py`.
- [ ] T009 Реализовать deterministic `int8-blockwise-v1` в `src/deltatorrent/compression/int8_blockwise.py`.
- [ ] T010 Реализовать parameter-schema segmentation и bounded sharding в `src/deltatorrent/compression/sharding.py`.
- [ ] T011 Реализовать canonical envelope writer/parser в `src/deltatorrent/compression/envelope.py`.
- [ ] T012 [P] Добавить codec numerical/property tests в `tests/unit/test_int8_codec.py`.
- [ ] T013 [P] Добавить shard order/boundary tests в `tests/unit/test_sharding.py`.
- [ ] T014 Добавить malicious/truncated/oversized corpus tests в `tests/security/test_encoded_payload_parser.py`.

## Phase 3: US1 — Encode/decode update

- [ ] T015 [US1] Реализовать worker compression facade в `src/deltatorrent/worker/compression.py`.
- [ ] T016 [US1] Реализовать coordinator bounded decoder stage в `src/deltatorrent/coordinator/decoding.py`.
- [ ] T017 [US1] Добавить exact/hash/reordered-shard integration tests в `tests/integration/test_compressed_update_roundtrip.py`.

## Phase 4: US2 — Transactional error feedback

- [ ] T018 [US2] Реализовать residual repository и key/version rules в `src/deltatorrent/compression/residual.py`.
- [ ] T019 [US2] Реализовать compression candidate journal/CAS в `src/deltatorrent/compression/candidate.py`.
- [ ] T020 [US2] Связать accepted receipt с residual commit в `src/deltatorrent/worker/compression.py`.
- [ ] T021 [P] [US2] Добавить residual recurrence/reset tests в `tests/unit/test_residual_state.py`.
- [ ] T022 [US2] Добавить retry/reject/unknown/crash matrix в `tests/integration/test_residual_transactions.py`.

## Phase 5: US3 — Compressed coordinator round

- [ ] T023 [US3] Добавить codec allowlist/intake validation в `src/deltatorrent/coordinator/intake.py`.
- [ ] T024 [US3] Подключить decode-before-FP32-reduce в `src/deltatorrent/coordinator/service.py`.
- [ ] T025 [US3] Расширить round result evidence profile/decoded hashes в `src/deltatorrent/coordinator/manifests.py`.
- [ ] T026 [US3] Добавить mixed-codec/reference/permutation tests в `tests/integration/test_compressed_round.py`.
- [ ] T027 [P] [US3] Запустить весь uncompressed suite через raw profile и устранить regressions.

## Final Phase: Measurement and documentation

- [ ] T028 Создать representative payload fixture/runner в `benchmarks/compression/measure.py`.
- [ ] T029 Зафиксировать ratio/error/timing evidence в `specs/004-compressed-delta-protocol/evidence.md`.
- [ ] T030 Документировать byte/numerical/residual contracts в `docs/compression-protocol.md`.
- [ ] T031 Добавить architecture test сохранения reduce/distribution boundary в `tests/architecture/test_compression_boundary.py`.
- [ ] T032 Выполнить cross-artifact analysis, full quality gate и final Constitution Check.

## Dependencies

- T001–T006 блокируют persisted payloads.
- T007–T014 блокируют network/application integration.
- T018–T022 требуют стабильных codec bytes и receipt semantics feature `003`.
- T023–T027 выполняются после decoder stage.
- T028–T032 завершают branch gate.

## Implementation Strategy

Начать с raw compatibility, затем FP16 и reference INT8. Sharding/parser должны быть безопасны до подключения coordinator. Error feedback вводится только с two-phase commit; нельзя временно продвигать residual «по факту отправки».

## Exit Gate

Все T001–T032 выполнены; golden/numerical/parser/residual/mixed-round suites зелёные; large fixture даёт требуемый ratio; raw path не регрессировал; evidence и Constitution Check закоммичены.
