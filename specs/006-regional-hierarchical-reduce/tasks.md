# Tasks: Региональная и шардированная иерархическая редукция

**Input**: `spec.md`, `plan.md`, constitution и завершённые `001–005`.

## Phase 1: Contracts and topology

- [ ] T001 Определить topology/accepted-set/partial/global-set models в `src/deltatorrent/domain/hierarchy.py`.
- [ ] T002 Реализовать topology validation/hash в `src/deltatorrent/reduce/topology.py`.
- [ ] T003 Реализовать canonical parameter shard planner в `src/deltatorrent/reduce/shard_plan.py`.
- [ ] T004 Создать reduce protobuf contract в `proto/deltatorrent/reduce/v1/reduce.proto`.
- [ ] T005 [P] Добавить canonical topology/partial fixtures в `tests/fixtures/contracts/reduce/`.
- [ ] T006 Добавить contract tests в `tests/contract/test_reduce_protocol.py`.

## Phase 2: Foundational regional state

- [ ] T007 Реализовать regional/global CAS repositories в `src/deltatorrent/reduce/repository.py`.
- [ ] T008 Реализовать `RegionalAcceptedSet` sealing в `src/deltatorrent/reduce/regional_sealing.py`.
- [ ] T009 Реализовать local shard intake/idempotent receipts в `src/deltatorrent/reduce/intake.py`.
- [ ] T010 [P] Добавить shard coverage property tests в `tests/unit/test_shard_plan.py`.
- [ ] T011 Добавить accepted-set/token consistency tests в `tests/unit/test_regional_sealing.py`.

## Phase 3: US1 — Regional reduce

- [ ] T012 [US1] Реализовать decoded FP32 weighted-numerator reducer в `src/deltatorrent/reduce/regional_reducer.py`.
- [ ] T013 [US1] Реализовать immutable regional partial writer в `src/deltatorrent/reduce/partials.py`.
- [ ] T014 [US1] Добавить numerator/token/codecs reference tests в `tests/unit/test_regional_numerator.py`.
- [ ] T015 [US1] Добавить multi-region vertical slice в `tests/integration/test_hierarchical_equivalence.py`.

## Phase 4: US2 — Global sharded assembly

- [ ] T016 [US2] Реализовать required region×shard matrix intake в `src/deltatorrent/reduce/global_intake.py`.
- [ ] T017 [US2] Реализовать global numerator sum/denominator contract в `src/deltatorrent/reduce/global_reducer.py`.
- [ ] T018 [US2] Реализовать exact-schema delta assembler в `src/deltatorrent/reduce/assembler.py`.
- [ ] T019 [US2] Интегрировать outer optimizer/atomic publisher в `src/deltatorrent/coordinator/service.py`.
- [ ] T020 [P] [US2] Добавить mismatched/incomplete/duplicate matrix tests в `tests/integration/test_hierarchical_consistency.py`.
- [ ] T021 [US2] Добавить arrival permutation/flat-equivalence cases в `tests/integration/test_hierarchical_equivalence.py`.

## Phase 5: US3 — Retry, deadlines and recovery

- [ ] T022 [US3] Реализовать idempotent partial/global command receipts в `src/deltatorrent/reduce/repository.py`.
- [ ] T023 [US3] Реализовать hard deadline/abort propagation в `src/deltatorrent/reduce/service.py`.
- [ ] T024 [US3] Реализовать restart reconciliation в `src/deltatorrent/reduce/recovery.py`.
- [ ] T025 [US3] Добавить retry/conflict/crash/deadline matrix в `tests/integration/test_hierarchical_faults.py`.

## Phase 6: Transport, CLI and fallback

- [ ] T026 Реализовать transport-neutral hierarchical service в `src/deltatorrent/reduce/application.py`.
- [ ] T027 [P] Реализовать gRPC adapter в `src/deltatorrent/adapters/grpc/hierarchical_reduce.py`.
- [ ] T028 Реализовать topology/round CLI в `src/deltatorrent/cli/reduce.py`.
- [ ] T029 Добавить sample 3-region topology в `configs/topology/smoke.json`.
- [ ] T030 Реализовать runtime `flat|hierarchical` selection без изменения lineage contracts.
- [ ] T031 Добавить netem link-loss/retry tests в `tests/integration/test_hierarchical_wan.py`.

## Final Phase: Validation and documentation

- [ ] T032 Добавить fan-in measurement fixture в `benchmarks/reduce/fan_in.py`.
- [ ] T033 Документировать hierarchy math/topology/rollback в `docs/hierarchical-reduce.md`.
- [ ] T034 Добавить P2P denial/architecture tests в `tests/architecture/test_regional_partial_boundary.py`.
- [ ] T035 Записать equivalence/fan-in evidence в `specs/006-regional-hierarchical-reduce/evidence.md`.
- [ ] T036 Выполнить cross-artifact analysis, full quality gate и final Constitution Check.

## Dependencies

- T001–T006 блокируют persisted partials.
- T007–T011 блокируют regional execution.
- T012–T015 блокируют global assembly.
- T016–T021 блокируют publication.
- T022–T025 должны пройти до transport rollout.
- T032–T036 выполняются последними.

## Implementation Strategy

Сначала topology и flat-equivalent in-process math. Затем persistence/recovery, после — gRPC/WAN tests. Flat path остаётся oracle и fallback. Не вводить adaptive membership, staleness или signatures.

## Exit Gate

Все T001–T036 выполнены; flat-equivalence, coverage, consistency, recovery/WAN fault suites зелёные; fan-in evidence и P2P boundary подтверждены; quality gate/Constitution Check завершены.
