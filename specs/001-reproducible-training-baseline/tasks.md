# Tasks: Воспроизводимый training baseline и WAN-эмулятор

**Input**: `spec.md`, `plan.md`, project constitution and `main` foundation.

## Format

`- [ ] T### [P?] [US#?] Action with exact path`

`[P]` означает, что задача может выполняться параллельно после завершения её prerequisites. Task ID должен присутствовать в implementation commit message.

## Phase 1: Setup

- [ ] T001 Создать Python 3.12 package, dependency groups и CLI entry point в `pyproject.toml`.
- [ ] T002 Зафиксировать dependency resolution в `uv.lock` и документировать update policy в `docs/dependencies.md`.
- [ ] T003 [P] Настроить ruff, mypy и pytest defaults в `pyproject.toml`.
- [ ] T004 [P] Добавить CI workflow с offline CPU gate в `.github/workflows/ci.yml`.
- [ ] T005 [P] Добавить статический запрет unsafe pickle/deserialization в `tests/architecture/test_safe_serialization.py`.

## Phase 2: Foundational domain and artifact contracts

- [ ] T006 Реализовать typed errors и stable error codes в `src/deltatorrent/domain/errors.py`.
- [ ] T007 Реализовать `ArtifactRef`, `RunManifest` и `CheckpointManifest` в `src/deltatorrent/domain/manifests.py`.
- [ ] T008 Реализовать canonical JSON и SHA-256 helpers в `src/deltatorrent/artifacts/canonical_json.py`.
- [ ] T009 Реализовать atomic filesystem artifact store в `src/deltatorrent/artifacts/filesystem.py`.
- [ ] T010 [P] Добавить schema/canonicalization contract tests в `tests/contract/test_manifest_contracts.py`.
- [ ] T011 [P] Добавить atomic publish/crash-cleanup tests в `tests/unit/test_filesystem_artifact_store.py`.

## Phase 3: US1 — Reproducible baseline

- [ ] T012 [US1] Определить строгую `BaselineConfig` и version migration boundary в `src/deltatorrent/training/config.py`.
- [ ] T013 [P] [US1] Добавить synthetic corpus и tokenizer fixtures в `tests/fixtures/corpus/` и `tests/fixtures/tokenizer/`.
- [ ] T014 [US1] Реализовать deterministic sampler, batching и non-padding token accounting в `src/deltatorrent/training/data.py`.
- [ ] T015 [P] [US1] Реализовать tiny causal LM factory и parameter-schema fingerprint в `src/deltatorrent/training/model.py`.
- [ ] T016 [US1] Реализовать baseline AdamW/gradient-accumulation loop и finite guards в `src/deltatorrent/training/baseline.py`.
- [ ] T017 [US1] Реализовать safe checkpoint snapshot/restore всех RNG, optimizer и cursor states в `src/deltatorrent/training/checkpoint.py`.
- [ ] T018 [US1] Реализовать `baseline run/resume` commands в `src/deltatorrent/cli/baseline.py`.
- [ ] T019 [P] [US1] Добавить one-step numerical reference и token-count tests в `tests/unit/test_baseline_math.py`.
- [ ] T020 [US1] Добавить repeated-run determinism и continuous-vs-resume tests в `tests/integration/test_baseline_reproducibility.py`.

## Phase 4: US2 — WAN emulation

- [ ] T021 [US2] Определить `NetworkProfile`, fault events и validation rules в `src/deltatorrent/domain/network.py`.
- [ ] T022 [US2] Реализовать seeded unprivileged faulty stream/proxy в `src/deltatorrent/adapters/netem/simulated.py`.
- [ ] T023 [P] [US2] Реализовать cleanup-safe optional Linux `tc/netem` adapter в `src/deltatorrent/adapters/netem/linux_tc.py`.
- [ ] T024 [US2] Реализовать `netem smoke` command и sample profiles в `src/deltatorrent/cli/netem.py` и `configs/netem/`.
- [ ] T025 [US2] Добавить deterministic loss/jitter/disconnect/deadline tests в `tests/integration/test_network_profiles.py`.

## Phase 5: US3 — Artifact verification

- [ ] T026 [US3] Реализовать recursive bundle verifier в `src/deltatorrent/artifacts/verifier.py`.
- [ ] T027 [US3] Реализовать `artifacts verify` command в `src/deltatorrent/cli/artifacts.py`.
- [ ] T028 [P] [US3] Добавить corruption fixtures и verifier tests в `tests/integration/test_artifact_verification.py`.

## Final Phase: Validation and documentation

- [ ] T029 Записать baseline и reproducibility guide в `docs/reproducibility.md`.
- [ ] T030 Добавить committed smoke configs в `configs/baseline/`.
- [ ] T031 Запустить cross-artifact Spec Kit analysis и устранить противоречия в `specs/001-reproducible-training-baseline/`.
- [ ] T032 Выполнить полный offline quality gate и приложить команды/результаты в `specs/001-reproducible-training-baseline/evidence.md`.
- [ ] T033 Повторить Constitution Check по final diff в `specs/001-reproducible-training-baseline/plan.md`.

## Dependencies

- T001–T005 блокируют production code.
- T006–T011 блокируют training и verifier publication.
- T012–T17 блокируют US1 integration test.
- T021 блокирует T022–T025.
- T026 зависит от T007–T009 и завершённых artifact producers.
- T031–T033 выполняются последними.

## Implementation Strategy

Сначала получить зелёный artifact/domain foundation, затем vertical slice US1. US2 может выполняться параллельно после foundational phase. US3 завершается после появления полного run bundle. Не добавлять distributed coordinator API в эту ветку.

## Exit Gate

Все задачи T001–T033 завершены; повторный run, resume, corruption и WAN fault tests проходят offline; quality commands из `AGENTS.md` зелёные; evidence и final Constitution Check закоммичены.
