# Tasks: Адаптивное планирование неоднородных workers

**Input**: `spec.md`, `plan.md`, constitution и завершённые `001–006`.

## Phase 1: Contracts and measurement

- [ ] T001 Определить profile/policy/schedule/decision/controller models в `src/deltatorrent/domain/scheduling.py`.
- [ ] T002 Определить stable explanation/infeasibility codes в `src/deltatorrent/scheduling/explanations.py`.
- [ ] T003 Создать scheduling protobuf contract в `proto/deltatorrent/scheduling/v1/scheduling.proto`.
- [ ] T004 Реализовать content-addressed profile/decision repository в `src/deltatorrent/scheduling/repository.py`.
- [ ] T005 [P] Реализовать compute/memory benchmark probe в `src/deltatorrent/scheduling/probes.py`.
- [ ] T006 [P] Реализовать network probe/profile aggregation в `src/deltatorrent/scheduling/profiles.py`.
- [ ] T007 Добавить contract/profile compatibility tests в `tests/contract/test_scheduling_contract.py`.

## Phase 2: Foundational planner

- [ ] T008 Реализовать communication-derived H formula/validation в `src/deltatorrent/scheduling/workload.py`.
- [ ] T009 Реализовать memory/quorum feasibility analysis в `src/deltatorrent/scheduling/planner.py`.
- [ ] T010 Реализовать deterministic region placement в `src/deltatorrent/scheduling/regions.py`.
- [ ] T011 Реализовать workload/fairness/contribution allocation в `src/deltatorrent/scheduling/workload.py`.
- [ ] T012 Реализовать expected duration/deadline model в `src/deltatorrent/scheduling/deadlines.py`.
- [ ] T013 [P] Добавить H formula/property tests в `tests/unit/test_h_formula.py`.
- [ ] T014 [P] Добавить workload/feasibility/fairness tests в `tests/unit/test_workload_planner.py`.

## Phase 3: US1 — Heterogeneous schedules

- [ ] T015 [US1] Реализовать immutable `RoundSchedule` builder в `src/deltatorrent/scheduling/planner.py`.
- [ ] T016 [US1] Интегрировать schedule с `ReduceTopology`/assignments в `src/deltatorrent/coordinator/service.py`.
- [ ] T017 [US1] Реализовать `schedule probe/plan/explain` CLI в `src/deltatorrent/cli/schedule.py`.
- [ ] T018 [US1] Добавить heterogeneous/expired/incompatible/infeasible integration tests в `tests/integration/test_heterogeneous_schedule.py`.

## Phase 4: US2 — Adaptive feedback

- [ ] T019 [US2] Реализовать committed drift evidence extraction в `src/deltatorrent/scheduling/drift.py`.
- [ ] T020 [US2] Реализовать hysteretic/rate-limited controller в `src/deltatorrent/scheduling/controller.py`.
- [ ] T021 [US2] Связать controller state с planning snapshot/CAS в `src/deltatorrent/scheduling/repository.py`.
- [ ] T022 [P] [US2] Добавить threshold/hysteresis/recovery tests в `tests/unit/test_drift_controller.py`.
- [ ] T023 [US2] Добавить network-vs-drift conflict integration test в `tests/integration/test_adaptive_h.py`.

## Phase 5: Simulation and straggler handling

- [ ] T024 Реализовать deterministic discrete-event scheduler simulator в `src/deltatorrent/scheduling/simulator.py`.
- [ ] T025 Интегрировать hard deadline terminal policy в `src/deltatorrent/coordinator/sealing.py`.
- [ ] T026 Добавить 50-worker trace fixtures в `tests/fixtures/scheduling/`.
- [ ] T027 Добавить planned-vs-actual/straggler/disconnect suite в `tests/integration/test_straggler_deadlines.py`.

## Phase 6: US3 — Bounded asynchronous experiment

- [ ] T028 [US3] Определить versioned staleness policy/formula в `src/deltatorrent/scheduling/staleness.py`.
- [ ] T029 [US3] Реализовать lineage/norm/cosine async guard в `src/deltatorrent/coordinator/async_intake.py`.
- [ ] T030 [US3] Реализовать isolated weighted async aggregation path в `src/deltatorrent/coordinator/async_reducer.py`.
- [ ] T031 [US3] Реализовать feature flag/operator/automatic kill switches.
- [ ] T032 [P] [US3] Добавить exact staleness formula tests в `tests/unit/test_staleness_policy.py`.
- [ ] T033 [US3] Добавить async accept/reject/disable и sync-regression tests в `tests/integration/test_async_guard.py`.

## Final Phase: Validation and documentation

- [ ] T034 Добавить planner/controller telemetry в `src/deltatorrent/scheduling/telemetry.py`.
- [ ] T035 Добавить sample fixed/adaptive/async-off configs в `configs/scheduling/`.
- [ ] T036 Документировать formulas, evidence и rollback в `docs/adaptive-scheduling.md`.
- [ ] T037 Записать 50-worker/replay evidence в `specs/007-adaptive-heterogeneous-scheduling/evidence.md`.
- [ ] T038 Выполнить architecture/cross-artifact/full quality/final Constitution gates.

## Dependencies

- T001–T007 блокируют persisted decisions.
- T008–T014 блокируют schedule publication.
- T019–T023 требуют actual round telemetry.
- T024–T027 блокируют terminality evidence.
- T028–T033 выполняются только после stable synchronous adaptive path.
- T034–T038 завершают branch.

## Implementation Strategy

Сначала report-only deterministic planner, затем assignment integration, затем feedback controller. Async mode реализуется последним, остаётся off-by-default и не может считаться готовым при любой sync regression.

## Exit Gate

Все T001–T038 выполнены; deterministic planning/replay, drift/hysteresis, hard-deadline и async guard suites зелёные; strict sync results unchanged; evidence/quality/Constitution gates завершены.
