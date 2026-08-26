# Tasks: Воспроизводимый training baseline и WAN-эмулятор

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, `000-formal-tla-spec` artifacts and exact Formal GO.

## Format

`- [ ] T### [P?] [US#?] Action with exact path`

`[P]` означает, что задача может выполняться параллельно после завершения prerequisites. Task ID должен присутствовать в implementation commit message.

## Phase 0: Mandatory Formal GO prerequisite

- [x] T000 [US0] Implement/execute offline verifier for the exact `FormalVerificationReport(decision=GO)`; validate source/spec/Constitution/ADR/tool/evidence/formal-semantics compatibility and record hashes in `specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json`. STOP all T001+ on any failure.

## Phase 1: Setup

- [x] T001 Создать Python 3.12 package, dependency groups и CLI entry point в `pyproject.toml`.
- [x] T002 Зафиксировать dependency resolution в `uv.lock` и документировать update policy в `docs/dependencies.md`.
- [x] T003 [P] Настроить ruff, mypy и pytest defaults в `pyproject.toml`.
- [x] T004 [P] Добавить CI workflow с offline CPU gate в `.github/workflows/ci.yml`.
- [x] T005 [P] Добавить статический запрет unsafe pickle/deserialization в `tests/architecture/test_safe_serialization.py`.
- [x] T006 [P] Add formal semantics compatibility loader/action-ID registry in `src/deltatorrent/domain/formal_compat.py` without importing TLA/tooling at runtime.

## Phase 2: Foundational domain and artifact contracts

- [x] T007 Реализовать typed errors и stable error codes в `src/deltatorrent/domain/errors.py`.
- [x] T008 Реализовать `ArtifactRef`, `RunManifest` и `CheckpointManifest` в `src/deltatorrent/domain/manifests.py`.
- [x] T009 Реализовать canonical JSON и SHA-256 helpers в `src/deltatorrent/artifacts/canonical_json.py`.
- [x] T010 Реализовать atomic filesystem artifact store в `src/deltatorrent/artifacts/filesystem.py`.
- [x] T011 [P] Добавить schema/canonicalization contract tests в `tests/contract/test_manifest_contracts.py`.
- [x] T012 [P] Добавить atomic publish/crash-cleanup tests в `tests/unit/test_filesystem_artifact_store.py`.
- [x] T013 [P] Add legal/illegal artifact lifecycle projection fixtures in `tests/fixtures/formal/001/` and contract tests.

## Phase 3: US1 — Reproducible baseline

- [ ] T014 [US1] Определить строгую `BaselineConfig` и version migration boundary в `src/deltatorrent/training/config.py`.
- [ ] T015 [P] [US1] Добавить synthetic corpus и tokenizer fixtures в `tests/fixtures/corpus/` и `tests/fixtures/tokenizer/`.
- [ ] T016 [US1] Реализовать deterministic sampler, batching и non-padding token accounting в `src/deltatorrent/training/data.py`.
- [ ] T017 [P] [US1] Реализовать tiny causal LM factory и parameter-schema fingerprint в `src/deltatorrent/training/model.py`.
- [ ] T018 [US1] Реализовать baseline AdamW/gradient-accumulation loop и finite guards в `src/deltatorrent/training/baseline.py`.
- [ ] T019 [US1] Реализовать safe checkpoint snapshot/restore всех RNG, optimizer и cursor states в `src/deltatorrent/training/checkpoint.py`.
- [ ] T020 [US1] Реализовать `baseline run/resume` commands в `src/deltatorrent/cli/baseline.py`.
- [ ] T021 [P] [US1] Добавить one-step numerical reference и token-count tests в `tests/unit/test_baseline_math.py`.
- [ ] T022 [US1] Добавить repeated-run determinism и continuous-vs-resume tests в `tests/integration/test_baseline_reproducibility.py`.

## Phase 4: US2 — WAN emulation

- [ ] T023 [US2] Определить `NetworkProfile`, fault events и validation rules в `src/deltatorrent/domain/network.py`.
- [ ] T024 [US2] Реализовать seeded unprivileged faulty stream/proxy в `src/deltatorrent/adapters/netem/simulated.py`.
- [ ] T025 [P] [US2] Реализовать cleanup-safe optional Linux `tc/netem` adapter в `src/deltatorrent/adapters/netem/linux_tc.py`.
- [ ] T026 [US2] Реализовать `netem smoke` command и sample profiles в `src/deltatorrent/cli/netem.py` и `configs/netem/`.
- [ ] T027 [US2] Добавить deterministic loss/jitter/disconnect/deadline tests в `tests/integration/test_network_profiles.py`.

## Phase 5: US3 — Artifact verification

- [ ] T028 [US3] Реализовать recursive bundle verifier в `src/deltatorrent/artifacts/verifier.py`.
- [ ] T029 [US3] Реализовать `artifacts verify` command в `src/deltatorrent/cli/artifacts.py`.
- [ ] T030 [P] [US3] Добавить corruption fixtures и verifier tests в `tests/integration/test_artifact_verification.py`.

## Final Phase: Validation and documentation

- [ ] T031 Записать baseline и reproducibility guide в `docs/reproducibility.md`.
- [ ] T032 Добавить committed smoke configs в `configs/baseline/`.
- [ ] T033 Run formal-impact/cross-artifact analysis and verify no semantic drift from the bound `formal_semantics_id`.
- [ ] T034 Выполнить полный offline quality gate и приложить команды/результаты в `specs/001-reproducible-training-baseline/evidence/exit-gate.md`.
- [ ] T035 Повторить Constitution Check по final diff в `plan.md` and reverify Formal GO compatibility.

## Dependencies

- T000 is a hard prerequisite for every other task.
- T001–T006 block production code.
- T007–T013 block training and verifier publication.
- T014–T022 block US1 integration test.
- T023 blocks T024–T027.
- T028 depends on artifact producers.
- T033–T035 are final.

## Implementation Strategy

First establish immutable formal prerequisite evidence, then obtain a green artifact/domain foundation and US1 vertical slice. US2 may proceed after foundation. US3 completes after a full bundle exists. Do not add distributed coordinator/BFT API here; protocol semantic changes return to 000.

## Exit Gate

T000–T035 complete; Formal GO remains compatible; repeated run, resume, corruption, WAN fault and projection tests pass offline; AGENTS quality commands are green; evidence and final Constitution Check are committed.
