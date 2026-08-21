# Tasks: Центральный синхронный round coordinator

**Input**: `spec.md`, `plan.md`, constitution и завершённые features `001–002`.

## Phase 1: Domain and protocol contracts

- [ ] T001 Определить `RoundDefinition`, `RoundRecord`, transitions и sealing policy в `src/deltatorrent/domain/rounds.py`.
- [ ] T002 [P] Определить `UpdateReceipt` taxonomy и stable reason codes в `src/deltatorrent/domain/receipts.py`.
- [ ] T003 [P] Определить outer optimizer config/state/result contracts в `src/deltatorrent/domain/optimizer.py`.
- [ ] T004 Создать protobuf API в `proto/deltatorrent/coordinator/v1/coordinator.proto`.
- [ ] T005 Добавить canonical round/receipt/result fixtures в `tests/fixtures/contracts/coordinator/`.
- [ ] T006 Добавить domain/protobuf contract tests в `tests/contract/test_coordinator_proto.py`.

## Phase 2: Durable coordinator foundation

- [ ] T007 Реализовать CAS/journal `RoundRepository` port и filesystem adapter в `src/deltatorrent/coordinator/repository.py`.
- [ ] T008 Реализовать exhaustive transition guard в `src/deltatorrent/coordinator/state_machine.py`.
- [ ] T009 [P] Реализовать deterministic assignment allocator в `src/deltatorrent/coordinator/assignments.py`.
- [ ] T010 Реализовать update intake validation/idempotent receipts в `src/deltatorrent/coordinator/intake.py`.
- [ ] T011 [P] Добавить state/CAS tests в `tests/unit/test_round_state_machine.py`.
- [ ] T012 Добавить duplicate/conflict/wrong-parent validation tests в `tests/unit/test_update_intake.py`.

## Phase 3: US1 — Synchronous round lifecycle

- [ ] T013 [US1] Реализовать soft/hard/manual sealing policy в `src/deltatorrent/coordinator/sealing.py`.
- [ ] T014 [US1] Реализовать `RoundService` create/open/assign/submit/seal/cancel/status commands в `src/deltatorrent/coordinator/service.py`.
- [ ] T015 [US1] Реализовать structured lifecycle telemetry в `src/deltatorrent/coordinator/telemetry.py`.
- [ ] T016 [US1] Добавить multi-worker lifecycle/quorum/deadline integration tests в `tests/integration/test_central_round.py`.

## Phase 4: US2 — Reduce and outer optimization

- [ ] T017 [US2] Реализовать canonical token-weighted FP32 reducer в `src/deltatorrent/coordinator/reducer.py`.
- [ ] T018 [US2] Реализовать Nesterov/SGD outer optimizer contract в `src/deltatorrent/coordinator/outer_optimizer.py`.
- [ ] T019 [US2] Реализовать immutable accepted-set/global-delta/result manifests в `src/deltatorrent/coordinator/manifests.py`.
- [ ] T020 [P] [US2] Добавить scalar/tensor weighted-reference tests в `tests/unit/test_weighted_reduce.py`.
- [ ] T021 [P] [US2] Добавить Nesterov state/reference tests в `tests/unit/test_outer_optimizer.py`.
- [ ] T022 [US2] Добавить arrival-permutation determinism tests в `tests/integration/test_reduce_determinism.py`.

## Phase 5: US3 — Atomic publication and recovery

- [ ] T023 [US3] Реализовать two-phase artifact/current-pointer publisher в `src/deltatorrent/coordinator/publisher.py`.
- [ ] T024 [US3] Реализовать restart/recovery reconciliation в `src/deltatorrent/coordinator/recovery.py`.
- [ ] T025 [US3] Добавить injected crash hooks только для tests в `src/deltatorrent/coordinator/faults.py`.
- [ ] T026 [US3] Добавить crash-point/double-apply matrix в `tests/integration/test_coordinator_recovery.py`.

## Phase 6: Reference adapters

- [ ] T027 Реализовать transport-neutral application facade в `src/deltatorrent/coordinator/application.py`.
- [ ] T028 [P] Реализовать gRPC server/client adapters в `src/deltatorrent/adapters/grpc/coordinator_server.py` и `coordinator_client.py`.
- [ ] T029 Реализовать loopback-default bind guard и deadlines в `src/deltatorrent/adapters/grpc/security_mode.py`.
- [ ] T030 Реализовать coordinator CLI в `src/deltatorrent/cli/coordinator.py` и sample config в `configs/coordinator/smoke.json`.
- [ ] T031 Добавить gRPC retry/deadline/bind tests в `tests/integration/test_grpc_retry_semantics.py`.

## Final Phase: Validation and documentation

- [ ] T032 Документировать state machine, reduce math и recovery в `docs/round-protocol.md`.
- [ ] T033 Добавить architecture boundary tests в `tests/architecture/test_coordinator_boundaries.py`.
- [ ] T034 Выполнить cross-artifact analysis и записать evidence в `specs/003-central-round-coordinator/evidence.md`.
- [ ] T035 Выполнить full quality gate и final Constitution Check.

## Dependencies

- T001–T006 блокируют persisted/API contracts.
- T007–T012 блокируют user-story orchestration.
- T013–T016 должны завершиться до reduce/publish end-to-end.
- T017–T022 блокируют T023–T026.
- T027 зависит от стабильного application service; gRPC не должен определять domain behavior.
- T032–T035 выполняются последними.

## Implementation Strategy

Сначала доказать deterministic synchronous semantics in-process. Только после зелёного math/recovery gate подключать gRPC adapter. Не вводить compression, P2P или regional abstractions в текущую ветку.

## Exit Gate

Все T001–T035 завершены; multi-worker round, token-weighted/Nesterov reference, permutation, retry, abort и crash-recovery suites зелёные; coordinator остаётся loopback-only по умолчанию; quality gate и Constitution Check проходят.
