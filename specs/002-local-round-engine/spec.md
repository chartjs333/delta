# Feature Specification: Локальный worker round и псевдоградиент

**Feature Branch**: `002-local-round-engine`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `001-reproducible-training-baseline`

## Summary

Каждый worker должен уметь получить неизменяемую родительскую модель и детерминированное назначение данных, выполнить много локальных optimizer steps без межмашинной синхронизации и опубликовать одно uncompressed изменение модели. Этот артефакт является псевдоградиентом следующего уровня, а не checkpoint и не объектом P2P-раздачи.

Функция определяет математический знак, parameter schema, token accounting, lifecycle локального раунда и идемпотентную публикацию результата. Сетевой transport и глобальная агрегация остаются за следующими features.

## User Scenarios & Testing

### US1 — Выполнить назначенный локальный раунд (Priority: P1)

Worker получает `RoundAssignment`, проверяет родительскую модель и выполняет локальный AdamW до указанной границы.

**Independent Test**: на fixture model/data assignment локальный engine выдаёт тот же final state и processed-token count, что прямой однопроцессный reference loop.

**Acceptance Scenarios**:

1. **Given** валидные parent model, dataset assignment и parameter schema, **When** worker запускает раунд, **Then** он проходит состояния `ACCEPTED → RUNNING → COMPLETED` и публикует один `LocalUpdateManifest`.
2. **Given** `max_optimizer_steps=H`, **When** данные достаточны, **Then** выполняется ровно H optimizer steps, а gradient-accumulation microsteps не считаются отдельными local steps.
3. **Given** token cap или deadline достигнут на разрешённой batch boundary, **When** раунд завершается досрочно, **Then** manifest содержит фактические steps/tokens и типизированную completion reason.

### US2 — Проверить математическую обратимость локального update (Priority: P1)

Ревьюер восстанавливает локальные финальные веса только из parent model и опубликованного псевдоградиента.

**Independent Test**: для каждого tensor выполняется `local_final = parent - local_delta` в FP32 и результат совпадает с сохранённым direct final state в dtype-aware tolerance.

**Acceptance Scenarios**:

1. **Given** parent model `θ_t` и local final model `θ_i,H`, **When** update вычисляется, **Then** он строго использует соглашение `Δ_i = θ_t - θ_i,H`.
2. **Given** update с другим parameter-schema hash, **When** выполняется reconstruction, **Then** операция отвергается до tensor arithmetic.
3. **Given** non-finite tensor или несовпадающая shape, **When** update публикуется, **Then** manifest не получает статус `COMPLETED`.

### US3 — Безопасно повторить или отменить работу (Priority: P2)

Оператор повторно отправляет то же назначение либо отменяет worker до публикации.

**Independent Test**: повтор того же assignment ID и тех же входных хешей возвращает тот же immutable result; conflicting reuse ID отвергается; cancellation не оставляет видимого update.

**Acceptance Scenarios**:

1. **Given** уже завершённый assignment, **When** он отправлен повторно без изменений, **Then** worker возвращает существующий result ref без повторной публикации.
2. **Given** тот же assignment ID с другим parent/data/config hash, **When** worker принимает его, **Then** он отвергается как idempotency conflict.
3. **Given** cancellation до commit point, **When** engine останавливается, **Then** temporary artifacts удаляются/карантинируются и update не считается доступным.

## Edge Cases

- Dataset заканчивается до step/token budget.
- Один batch состоит только из padding tokens.
- Gradient accumulation прерывается до optimizer boundary.
- Parent checkpoint содержит buffers или tied parameters.
- Параметр заморожен либо не получил gradient.
- Mixed-precision local training при FP32 canonical delta.
- Worker перезапускается после вычисления tensor file, но до manifest commit.
- Повторное назначение с тем же ID и отличающимся deadline.
- Cancellation одновременно с final atomic publish.
- Слишком большой delta norm либо NaN/Inf после optimizer step.

## Requirements

### Functional Requirements

- **FR-001**: Система MUST определить версионированный `RoundAssignment` с `assignment_id`, `round_id`, `worker_id`, parent artifact/hash, parameter-schema hash, dataset assignment, local optimizer config, deterministic seeds, step/token limits и deadline.
- **FR-002**: Worker MUST проверить все referenced artifact hashes, schema versions и parent parameter schema до выделения training resources.
- **FR-003**: Один local step MUST означать один успешный optimizer update; microbatch/backward operations учитываются отдельно.
- **FR-004**: Worker MUST выполнять локальный AdamW, используя reproducibility и checkpoint primitives feature `001`.
- **FR-005**: Фактический contribution weight MUST основываться на non-padding tokens, прошедших успешный optimizer boundary; aborted partial accumulation не засчитывается.
- **FR-006**: Stop policy MUST однозначно задавать maximum optimizer steps, optional maximum tokens, deadline и поведение при исчерпании данных.
- **FR-007**: Worker MUST вычислять псевдоградиент как `Δ_i = θ_parent - θ_local_final` в каноническом ordered FP32 representation.
- **FR-008**: Parameter schema MUST включать ordered names, shapes, logical dtypes, trainable flags и tied-parameter aliases; schema fingerprint MUST быть stable.
- **FR-009**: Frozen parameters MAY отсутствовать в update payload только если omission policy является частью schema; неявное отсутствие запрещено.
- **FR-010**: `LocalUpdateManifest` MUST включать assignment/round/worker IDs, parent hash, parameter-schema hash, delta artifact ref, actual optimizer/micro steps, processed tokens, data cursor range, completion reason, numerical summaries и producer version.
- **FR-011**: Update payload MUST использовать safe tensor format и MUST NOT использовать pickle.
- **FR-012**: Worker MUST проверить finite values, exact tensor set/shapes и configurable norm ceiling до atomic publication.
- **FR-013**: Assignment execution MUST быть идемпотентным по `assignment_id` и canonical input fingerprint.
- **FR-014**: Conflicting reuse assignment ID MUST завершаться стабильной ошибкой без изменения существующего результата.
- **FR-015**: Cancellation/deadline MUST проверяться не реже каждой microbatch boundary и MUST завершать работу без публикации partial update.
- **FR-016**: Engine MUST публиковать update manifest последним, после durable tensor artifact, используя atomic commit semantics feature `001`.
- **FR-017**: Local round API MUST быть transport-independent; CLI/in-process adapter MAY вызывать его, но transport не входит в domain layer.
- **FR-018**: Worker MUST emit structured lifecycle/step/resource metrics, связанные с assignment и round IDs.
- **FR-019**: Worker-local update MUST иметь media type, который P2P publisher не сможет принять как distributable global object.

### Non-Functional Requirements

- **NFR-001**: Reference CPU local-round fixture MUST завершаться не более чем за 10 минут в CI.
- **NFR-002**: Delta creation SHOULD иметь не более одной дополнительной полной FP32 model copy сверх явно документированного memory budget; streaming optimization MAY быть позднее.
- **NFR-003**: Все cancellation paths MUST быть timeout-bounded и testable с injected clock/cancellation token.
- **NFR-004**: Domain contracts MUST не зависеть от gRPC, HTTP или конкретного artifact backend.
- **NFR-005**: Numerical comparisons MUST использовать per-dtype/per-operation tolerances, определённые в test contract.
- **NFR-006**: Worker не должен заявлять remote-compute honesty; manifest фиксирует вычисленный результат и observed counters, а не криптографическое доказательство работы.

### Key Entities

- **RoundAssignment**: неизменяемое задание worker и fingerprint всех входов.
- **ParameterSchema**: канонический порядок и структура параметров модели.
- **LocalRoundState**: lifecycle и timestamps `RECEIVED/ACCEPTED/RUNNING/COMPLETED/FAILED/CANCELLED`.
- **LocalDelta**: ordered FP32 pseudo-gradient с соглашением `parent - final`.
- **LocalUpdateManifest**: подписываемая в будущем метаинформация локального результата.
- **TokenAccountingRecord**: committed optimizer boundaries, non-padding tokens и data cursor.

## Success Criteria

- **SC-001**: Local engine совпадает с direct reference loop по final weights, steps и tokens на deterministic fixture.
- **SC-002**: Reconstruction test восстанавливает final local model из parent и delta в заявленном tolerance для каждого tensor.
- **SC-003**: Wrong-parent, wrong-schema, missing tensor, non-finite и norm-limit cases отвергаются до publication.
- **SC-004**: Idempotent retry возвращает тот же artifact hash; conflicting retry не меняет durable state.
- **SC-005**: Cancellation race suite не обнаруживает опубликованных partial updates или незавершённых mutable manifests.
- **SC-006**: Architecture test подтверждает, что `LocalUpdateManifest` нельзя передать в distribution/P2P interface.

## Assumptions

- В этой функции один worker process владеет полной trainable model state, помещающейся на выбранном device.
- Dataset assignment уже локально доступен через artifact refs feature `001`.
- Глобальный coordinator ещё не существует; assignments создаются fixture/CLI adapter.
- Compression, sharding и residual error feedback появятся в feature `004`.

## Out of Scope

- Сбор updates от нескольких workers и outer optimizer.
- RPC service discovery, enrollment и authentication.
- Compression, P2P, региональная редукция и staleness weighting.
- Mid-round migration между workers.
- Доказательство честности processed-token claim в permissionless сети.
