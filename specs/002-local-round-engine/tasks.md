# Tasks: Локальный worker round и псевдоградиент

**Input**: `spec.md`, `plan.md`, constitution и реализованный exit gate feature `001`.

## Phase 1: Domain contracts

- [ ] T001 Определить `RoundAssignment` и stop-policy schema в `src/deltatorrent/domain/assignments.py`.
- [ ] T002 Определить `ParameterSchema`, aliases и fingerprint contract в `src/deltatorrent/domain/parameters.py`.
- [ ] T003 Определить `LocalDelta` и `LocalUpdateManifest` в `src/deltatorrent/domain/updates.py`.
- [ ] T004 [P] Определить worker lifecycle/state transitions в `src/deltatorrent/domain/worker_state.py`.
- [ ] T005 [P] Добавить canonical assignment/update fixtures в `tests/fixtures/contracts/local_round/`.
- [ ] T006 Добавить schema and state-machine tests в `tests/contract/test_local_update_contract.py`.

## Phase 2: Foundational math and accounting

- [ ] T007 Реализовать parameter traversal/fingerprint и tied-parameter handling в `src/deltatorrent/delta/schema.py`.
- [ ] T008 Реализовать committed optimizer-boundary token ledger в `src/deltatorrent/training/token_accounting.py`.
- [ ] T009 Рефакторить reusable local AdamW step loop без изменения baseline в `src/deltatorrent/training/local_round.py`.
- [ ] T010 Реализовать FP32 delta builder с соглашением `parent - final` в `src/deltatorrent/delta/builder.py`.
- [ ] T011 [P] Реализовать reconstruction helper в `src/deltatorrent/delta/reconstruction.py`.
- [ ] T012 Реализовать tensor-set, finite и norm validation в `src/deltatorrent/delta/validation.py`.
- [ ] T013 [P] Добавить property/reference tests delta math в `tests/unit/test_delta_math.py`.
- [ ] T014 [P] Добавить parameter schema и token-ledger tests в `tests/unit/test_parameter_schema.py` и `tests/unit/test_token_accounting.py`.

## Phase 3: US1 — Execute local round

- [ ] T015 [US1] Реализовать assignment validator/resolvers в `src/deltatorrent/worker/validation.py`.
- [ ] T016 [US1] Реализовать `LocalRoundEngine` orchestration в `src/deltatorrent/worker/engine.py`.
- [ ] T017 [US1] Подключить lifecycle и structured metrics в `src/deltatorrent/worker/telemetry.py`.
- [ ] T018 [US1] Добавить `worker run-assignment` CLI в `src/deltatorrent/cli/worker.py`.
- [ ] T019 [US1] Добавить direct-reference parity/data-exhaustion tests в `tests/integration/test_local_round_engine.py`.

## Phase 4: US2 — Reconstruct and validate update

- [ ] T020 [US2] Интегрировать safe FP32 update artifact writer в `src/deltatorrent/worker/update_writer.py`.
- [ ] T021 [US2] Добавить reconstruction/wrong-schema/malformed update tests в `tests/integration/test_local_update_reconstruction.py`.
- [ ] T022 [P] [US2] Добавить mixed-precision optional CUDA test в `tests/integration/test_local_round_cuda.py`.

## Phase 5: US3 — Idempotency and cancellation

- [ ] T023 [US3] Реализовать atomic assignment claim/result repository в `src/deltatorrent/worker/repository.py`.
- [ ] T024 [US3] Реализовать injected cancellation/deadline checks в `src/deltatorrent/worker/engine.py`.
- [ ] T025 [US3] Добавить retry/conflict/cancel/crash-point suite в `tests/integration/test_worker_idempotency.py`.
- [ ] T026 [P] [US3] Добавить concurrency test для одного assignment ID в `tests/integration/test_worker_concurrency.py`.

## Final Phase: Validation and documentation

- [ ] T027 Добавить local-round contract и sign convention в `docs/local-round-contract.md`.
- [ ] T028 Добавить deterministic sample assignment в `configs/worker/smoke-assignment.json`.
- [ ] T029 Добавить architecture test запрета local update в distribution plane в `tests/architecture/test_reduce_distribution_boundary.py`.
- [ ] T030 Выполнить cross-artifact analysis и зафиксировать evidence в `specs/002-local-round-engine/evidence.md`.
- [ ] T031 Выполнить полный quality gate и final Constitution Check.

## Dependencies

- T001–T006 блокируют persisted implementation.
- T007–T014 блокируют engine publication.
- T015–T019 формируют первый вертикальный slice.
- T020 зависит от delta math и artifact store feature `001`.
- T023 должен быть завершён до retry/concurrency tests.
- T029–T031 выполняются после всех user stories.

## Implementation Strategy

Сначала доказать math/schema без transport, затем выполнить один детерминированный local round end-to-end. Идемпотентность и cancellation добавляются до объявления API готовым. Не вводить multi-worker coordinator, compression или networking в этой ветке.

## Exit Gate

Все T001–T031 выполнены; local engine совпадает с reference; reconstruction, malformed input, retry/conflict и cancellation tests зелёные; architecture boundary и quality commands проходят.
