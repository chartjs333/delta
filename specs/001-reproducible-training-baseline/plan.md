# Implementation Plan: Воспроизводимый training baseline и WAN-эмулятор

**Branch**: `001-reproducible-training-baseline` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Создать минимальный typed Python codebase, в котором training core отделён от artifact storage, CLI и network emulation adapters. Реализация сначала фиксирует канонические схемы и deterministic fixtures, затем строит single-node trainer, безопасный checkpoint/resume, verifier и два netem adapters: обязательный unprivileged simulator и опциональный Linux `tc` integration.

## Technical Context

- **Language/runtime**: Python 3.12.
- **Dependency/build**: `uv`, `pyproject.toml`, committed lockfile.
- **ML runtime**: PyTorch; `safetensors` для tensor payload.
- **Schema/validation**: typed domain dataclasses/Pydantic boundary models; canonical JSON UTF-8 с sorted keys.
- **CLI**: тонкий composition layer; бизнес-логика вызывается как Python API.
- **Tests**: pytest, property tests там, где они дают ценность; ruff и mypy.
- **Storage**: filesystem artifact store с atomic publish; интерфейс допускает замену на CAS позднее.
- **Network emulation**: deterministic in-process proxy/stream adapter; `tc/netem` только как marked integration test.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Token count, seeds, data order и manifests являются частью domain contract | Determinism и resume-equivalence tests |
| Reduce/distribution separation | Эти planes отсутствуют в функции; interfaces не вводят обходных путей | Architecture import test |
| Content-addressed state | Каждый persisted input/output получает SHA-256 и schema/media type | Bundle corruption tests |
| WAN realism | Есть offline fault profiles и optional real netem adapter | Deterministic profile suite |
| Permissioned security | Network trust ещё не вводится; unsafe deserialization запрещена сразу | Pickle-ban/static test |
| Observable increments | JSONL metrics, typed failures, independent exit gate | Full branch gate |

**Pre-implementation result**: PASS. Повторить проверку против final diff.

## Architecture and Data Flow

```text
BaselineConfig ──validate──▶ BaselineService
      │                         │
DatasetManifest ────────────────┤
                                ▼
                    deterministic data/model/trainer
                                │
                metrics + checkpoint candidate
                                │
                                ▼
                     atomic ArtifactStore publish
                                │
                                ▼
                         immutable RunManifest

NetworkProfile ──▶ FaultyStream/Proxy ──▶ local loopback scenario
```

Training code зависит от ports `ArtifactWriter`, `MetricsSink`, `Clock` и `DeviceRuntime`; filesystem, real clock и CLI остаются adapters. Reproducibility class фиксирует platform/device/dtype contract.

## Project Structure

```text
pyproject.toml
uv.lock
src/deltatorrent/
  domain/
    artifacts.py
    manifests.py
    network.py
    errors.py
  training/
    config.py
    data.py
    model.py
    baseline.py
    checkpoint.py
  artifacts/
    canonical_json.py
    filesystem.py
    verifier.py
  adapters/netem/
    simulated.py
    linux_tc.py
  cli/
    main.py
    baseline.py
    artifacts.py
    netem.py
tests/
  unit/
  contract/
  integration/
  fixtures/
configs/baseline/
configs/netem/
docs/reproducibility.md
```

## Implementation Sequence

1. Зафиксировать packaging, quality tooling и запрет unsafe serialization.
2. Реализовать canonical JSON, hashes, manifests и atomic artifact-store port.
3. Добавить deterministic corpus/tokenizer/model fixtures и token accounting.
4. Реализовать baseline loop, checkpoint boundary и exact resume state.
5. Добавить CLI и bundle verifier.
6. Реализовать seeded unprivileged WAN simulator; затем optional `tc` adapter.
7. Закрыть determinism, corruption, timeout и offline integration tests.
8. Снять final Constitution Check и обновить evidence в tasks/checklist.

## Test Strategy

- **Unit**: schema validation, canonicalization, hashing, token counting, sampler cursor, timeout math.
- **Numerical**: one-step direct reference; finite-value guards; dtype-aware tolerances.
- **Contract**: run/checkpoint/network schemas и stable error codes.
- **Integration**: continuous-vs-resume, repeated deterministic runs, artifact corruption, local loopback with faults.
- **Platform**: CPU path обязателен; CUDA smoke marked; `tc` test marked `requires_net_admin`.
- **Offline gate**: test process запускается с заблокированным DNS/outbound и использует только repo fixtures.

## Observability

- `metrics.jsonl`: step/token/loss/lr/throughput/memory.
- `events.jsonl`: lifecycle, checkpoint, retry, timeout и fault injection events.
- `run-manifest.json`: итоговый status и artifact graph.
- Логи структурированы, но manifest/metrics считаются authoritative evidence.

## Rollout and Rollback

Функция не меняет внешнюю систему. Rollout — публикация CLI/API как `0.x` experimental. Rollback выполняется возвратом к предыдущему commit; schema versions не переиспользуются. Незавершённые temporary files игнорируются и очищаются отдельной командой/на старте после проверки ownership.

## Risks and Mitigations

- **Недетерминированные kernels**: deterministic algorithms, platform fingerprint, отдельный tolerance class.
- **Checkpoint не полностью воспроизводит sampler/RNG**: explicit state inventory и resume-equivalence test.
- **Слишком тяжёлый CI fixture**: маленькая модель/corpus и отдельный full benchmark profile.
- **Утечка `tc` rules**: context manager/finalizer плюс cleanup verification.
- **Manifest опубликован раньше данных**: двухфазный atomic publish; manifest коммитится последним.

## Exit Gate

- Все T-задачи отмечены выполненными с test evidence.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run pytest` проходят offline.
- Deterministic repeat, resume-equivalence, corruption и WAN timeout suites зелёные.
- Нет pickle на cross-process/artifact boundaries.
- Final Constitution Check = PASS и README содержит воспроизводимую команду smoke run.
