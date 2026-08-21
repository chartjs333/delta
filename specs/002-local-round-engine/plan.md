# Implementation Plan: Локальный worker round и псевдоградиент

**Branch**: `002-local-round-engine` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Расширить baseline training primitives отдельным application service `LocalRoundEngine`. Domain layer определяет assignment, schema, lifecycle и update manifest; training layer выполняет детерминированный local AdamW; delta layer вычисляет/проверяет `parent - final`; filesystem adapter публикует result атомарно. Первый adapter — in-process/CLI, чтобы математический contract был доказан до появления coordinator transport.

## Technical Context

- Наследует Python/PyTorch/artifact contracts feature `001`.
- Canonical delta payload: safetensors с FP32 tensors в parameter-schema order.
- State persistence: assignment journal и immutable result refs в filesystem store.
- Cancellation: injected monotonic clock и cancellation token.
- Validation: exact schema/tensor-set checks, finite scan, global/per-tensor norm summaries.
- Concurrency: один active execution на assignment ID; repository lock/compare-and-set semantics.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Local math сравнивается с direct reference; tokens считаются на committed optimizer boundaries | Numerical/reference suite |
| Reduce/distribution separation | Артефакт явно типизирован как worker-local и запрещён в distribution interfaces | Architecture test |
| Versioned state | Assignment, parameter schema, parent и update content-addressed | Contract tests |
| Heterogeneity bounded | Step/token/deadline limits explicit; adaptive policy ещё не вводится | Boundary tests |
| Permissioned security | Identity пока logical; unsafe payloads и non-finite data отвергаются | Validation suite |
| Reversible increments | In-process adapter, atomic result, cancellation и rollback path | Integration gate |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
RoundAssignment + parent ref + data refs
                 │
                 ▼
        AssignmentValidator
                 │
                 ▼
         LocalRoundEngine
      ┌──────────┴──────────┐
      ▼                     ▼
Baseline training core   Token ledger
      │                     │
      └──── final state ─────┘
                 │
                 ▼
       DeltaBuilder(parent - final)
                 │
      schema/finite/norm validation
                 │
                 ▼
 atomic tensor publish → LocalUpdateManifest
```

`LocalRoundEngine` работает через ports `ModelLoader`, `DatasetResolver`, `UpdateRepository`, `Clock`, `CancellationToken` и metrics sink. Никакой coordinator-specific логики внутри engine нет.

## Project Structure

```text
src/deltatorrent/
  domain/
    assignments.py
    parameters.py
    updates.py
    worker_state.py
  training/
    local_round.py
    token_accounting.py
  delta/
    builder.py
    reconstruction.py
    validation.py
  worker/
    engine.py
    repository.py
  cli/
    worker.py
tests/
  unit/test_parameter_schema.py
  unit/test_token_accounting.py
  unit/test_delta_math.py
  contract/test_local_update_contract.py
  integration/test_local_round_engine.py
  integration/test_worker_idempotency.py
configs/worker/
docs/local-round-contract.md
```

## Implementation Sequence

1. Зафиксировать assignment/update/schema domain contracts и stable serialization fixtures.
2. Реализовать parameter schema fingerprint и exact tensor mapping.
3. Выделить reusable local-training loop из baseline без изменения baseline semantics.
4. Ввести committed token ledger и stop-policy state machine.
5. Реализовать delta builder/reconstructor и numerical validators.
6. Реализовать idempotent update repository и atomic publication.
7. Собрать engine, cancellation и CLI vertical slice.
8. Закрыть direct-reference, reconstruction, retry/conflict и cancellation-race tests.

## Test Strategy

- **Unit**: schema aliasing/order, stop policy, token ledger, delta sign, finite/norm guards.
- **Property**: произвольные малые tensor sets удовлетворяют `parent - delta ≈ final`.
- **Contract**: canonical JSON fixture для assignment/update; backward read текущей schema version.
- **Integration**: direct loop parity, deadline/cancel, data exhaustion, atomic crash points.
- **Architecture**: domain import boundaries и невозможность публикации local update в distribution plane.
- **Resource**: CPU mandatory; optional CUDA verifies mixed-precision-to-FP32 delta path.

## Observability

Events: assignment accepted/rejected, model/data resolved, local step committed, cancellation observed, delta validated, result published. Metrics: micro/optimizer steps, non-padding tokens, loss, step time, peak memory, delta L2/max norm, data exhaustion и completion reason.

## Rollout and Rollback

Новый worker API experimental и вызывается только локально. Feature flag не нужен, поскольку существующий baseline command остаётся неизменным. Rollback удаляет worker composition/API, но сохраняет schema fixtures для предотвращения случайного повторного использования version IDs.

## Risks and Mitigations

- **Sign confusion**: константа/документированный contract и reconstruction tests во всех слоях.
- **Token overcount after partial accumulation**: commit ledger обновляется только вместе с optimizer step.
- **Tied parameters duplicated**: alias table в schema и один canonical tensor owner.
- **Race duplicate execution**: compare-and-set assignment claim и immutable result.
- **Большой FP32 peak**: явно измерять; streaming delta отложен до необходимости.

## Exit Gate

- Direct reference parity и reconstruction tests зелёные.
- Все malformed/wrong-parent/non-finite inputs отвергаются.
- Retry/cancellation/crash-point suite не оставляет partial published updates.
- Local update media type изолирован от distribution plane.
- Полный quality gate и final Constitution Check проходят.
