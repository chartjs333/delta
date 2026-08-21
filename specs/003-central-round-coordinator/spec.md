# Feature Specification: Центральный синхронный round coordinator

**Feature Branch**: `003-central-round-coordinator`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `002-local-round-engine`

## Summary

Нужен первый end-to-end distributed-training control loop с одним authoritative coordinator: создать раунд, детерминированно назначить workers, принять локальные псевдоградиенты, закрыть набор участников, вычислить token-weighted average и применить внешний optimizer к общей модели.

Этот шаг намеренно синхронный и централизованный. Он служит математическим и протокольным эталоном для последующих compression, hierarchy и bounded-asynchronous вариантов. Coordinator хранит canonical state machine и результаты в durable store; arrival order не влияет на published model.

## User Scenarios & Testing

### US1 — Провести синхронный раунд с несколькими workers (Priority: P1)

Оператор открывает раунд для известной parent model, workers получают задания и отправляют завершённые local updates до deadline.

**Independent Test**: три in-process workers с разным числом токенов завершают один раунд; coordinator принимает допустимые updates, запечатывает round и публикует ровно одну новую model version.

**Acceptance Scenarios**:

1. **Given** parent model, dataset allocation policy и зарегистрированные workers, **When** создаётся round, **Then** он получает immutable `round_id`, parent/schema hashes и набор deterministic assignments.
2. **Given** round в состоянии `OPEN`, **When** приходит валидный update для выданного assignment, **Then** он сохраняется один раз и увеличивает accepted worker/token counters.
3. **Given** выполнены minimum workers/tokens и наступила configured seal condition, **When** coordinator закрывает приём, **Then** состояние становится `SEALED`, а новые updates отвергаются как late.
4. **Given** quorum не достигнут до hard deadline, **When** deadline обработан, **Then** round становится `ABORTED`, parent model остаётся current, а partial updates не применяются.

### US2 — Получить правильный token-weighted global update (Priority: P1)

Исследователь сравнивает результат coordinator с прямым FP32 reference calculation.

**Independent Test**: для updates `Δ_i` и подтверждённых токенов `n_i` coordinator вычисляет `Δ̄ = Σ(n_i·Δ_i)/Σn_i` независимо от arrival order, затем применяет формально определённый outer optimizer.

**Acceptance Scenarios**:

1. **Given** workers с 100, 200 и 700 токенами, **When** reduce выполнен, **Then** их веса равны 0.1, 0.2 и 0.7, а не `1/3`.
2. **Given** default outer Nesterov state, **When** публикуется round, **Then** используется contract `v'=μv+Δ̄`, `u=Δ̄+μv'`, `θ'=θ−ηu`.
3. **Given** одинаковый sealed update set в разном arrival order, **When** reduce повторён, **Then** output hashes совпадают внутри declared reproducibility class.
4. **Given** update с нулём committed tokens, **When** он подан, **Then** update отвергается и не входит в denominator.

### US3 — Восстановиться после retry или coordinator restart (Priority: P2)

Оператор перезапускает coordinator либо worker повторяет запрос после потерянного ответа.

**Independent Test**: crash/restart на каждой durable transition не создаёт второй round result, не применяет update дважды и продолжает из последнего committed state.

**Acceptance Scenarios**:

1. **Given** повторная отправка того же update ID и payload hash, **When** coordinator уже принял его, **Then** возвращается исходный receipt.
2. **Given** тот же update ID с другим hash, **When** запрос повторён, **Then** он отвергается как conflict и записывается audit event.
3. **Given** crash после global checkpoint write, но до `PUBLISHED`, **When** coordinator восстановлен, **Then** transaction либо завершается тем же result hash, либо безопасно откатывается без смены current model.
4. **Given** повторная команда seal/publish, **When** round уже опубликован, **Then** ответ идемпотентен и не изменяет outer optimizer state второй раз.

## Edge Cases

- Два updates от одного worker для одного assignment.
- Update с правильным round ID, но чужим worker/assignment ID.
- Wrong parent model или parameter schema.
- Accepted token count выше assignment limit либо несовместим с local manifest.
- Один tensor отсутствует, имеет неверную shape или non-finite value.
- Round удовлетворил minimum tokens, но не minimum workers, и наоборот.
- Deadline и последний update происходят одновременно.
- Coordinator crash в каждой state transition.
- Outer optimizer state отсутствует, повреждён или относится к другому parent.
- Нулевой denominator либо переполнение weighted sum.
- Поздний update после `SEALED`, `ABORTED` или `PUBLISHED`.
- Worker получает assignment, но не возвращает update.

## Requirements

### Functional Requirements

- **FR-001**: Coordinator MUST реализовать durable state machine `CREATED → OPEN → SEALED → AGGREGATING → PUBLISHED`, с переходом в `ABORTED` из любого непublished terminal path.
- **FR-002**: Каждый round MUST ссылаться на ровно одну immutable parent model, parameter schema, dataset manifest, coordinator config и outer-optimizer state.
- **FR-003**: Round creation MUST детерминированно генерировать непересекающиеся dataset assignments либо явно помечать разрешённое повторение данных.
- **FR-004**: Assignment MUST быть связан с одним enrolled logical worker ID; реальная authentication появится в feature `008`.
- **FR-005**: Coordinator MUST принимать updates только в `OPEN`, только для выданного assignment и только при совпадении round/parent/schema/input fingerprints.
- **FR-006**: Validation MUST повторить safe-format, exact tensor set, finite, norm и token-bound checks до включения update в accepted set.
- **FR-007**: Update submission MUST быть идемпотентной по update ID и payload hash; conflicting reuse MUST отвергаться.
- **FR-008**: Sealing policy MUST включать minimum accepted workers, minimum committed tokens, soft deadline, hard deadline и optional manual seal; каждое условие имеет явный приоритет.
- **FR-009**: Sealed accepted set MUST быть immutable и content-hashed; late updates сохраняются только как rejected receipts, не меняя set.
- **FR-010**: Reduce MUST использовать verified-at-this-stage manifest token counts как веса и MUST аккумулировать decoded tensors в FP32.
- **FR-011**: Reduce order MUST быть canonical (например, sorted assignment/update ID) и не зависеть от network arrival order.
- **FR-012**: Global pseudo-gradient MUST вычисляться как `Δ̄ = Σ(n_i·Δ_i)/Σn_i`; zero/negative token updates запрещены.
- **FR-013**: Default outer optimizer MUST реализовать Nesterov contract `v'=μv+Δ̄`, `u=Δ̄+μv'`, `θ'=θ−ηu`; `μ=0` даёт outer SGD.
- **FR-014**: Outer optimizer config/state MUST быть versioned, content-addressed и опубликован вместе с новой model version.
- **FR-015**: Publication MUST atomically связать sealed-set hash, global-delta artifact, new model checkpoint, outer state и `RoundResultManifest`; current-model pointer меняется последним compare-and-set.
- **FR-016**: Failed/aborted round MUST NOT менять parent model или outer state.
- **FR-017**: Coordinator MUST поддерживать restart/recovery из durable journal без повторного применения outer update.
- **FR-018**: API MUST предоставлять операции create/open/get assignment/submit update/get receipt/seal/get status/get result/cancel.
- **FR-019**: Reference transport adapter MUST иметь версионированный protobuf/gRPC contract; domain/application services MUST оставаться transport-independent.
- **FR-020**: Insecure reference server MUST bind только loopback по умолчанию и предупреждать/отказываться от non-loopback без explicit development override до feature `008`.
- **FR-021**: Coordinator MUST emit round/update lifecycle events и metrics, включая accepted/rejected/late counts, tokens, wait/reduce/publish timings и failure reason.
- **FR-022**: Worker-local updates MUST передаваться только в reduce intake; никакой API этого feature не должен объявлять их глобально distributable.

### Non-Functional Requirements

- **NFR-001**: Reference integration test с минимум четырьмя simulated workers MUST завершаться в bounded CI timeout.
- **NFR-002**: Все mutating operations MUST быть idempotent и safe under client retry.
- **NFR-003**: Durable transition и artifact publication MUST выдерживать injected crash points.
- **NFR-004**: Aggregation MUST иметь dtype-aware numerical contract и диагностировать overflow/non-finite intermediate.
- **NFR-005**: Coordinator correctness MUST не зависеть от wall-clock ordering; deadlines используют monotonic clock, persisted timestamps — UTC.
- **NFR-006**: Storage, transport и clock adapters MUST быть replaceable ports.
- **NFR-007**: Этот baseline не обещает availability при coordinator failure во время downtime; он обещает корректное recovery после restart.

### Key Entities

- **RoundDefinition**: immutable parent/config/data/schema и sealing policy.
- **RoundRecord**: durable state, version/CAS token и counters.
- **AcceptedUpdateSet**: canonical ordered refs и set hash.
- **UpdateReceipt**: accepted/rejected/duplicate/late result с stable reason.
- **GlobalDelta**: token-weighted FP32 aggregate.
- **OuterOptimizerState**: momentum и config, привязанные к parent version.
- **RoundResultManifest**: lineage parent→round→delta→new model, token totals и evidence refs.

## Success Criteria

- **SC-001**: Multi-worker integration round публикует одну новую model version и правильные assignments/receipts.
- **SC-002**: Token-weighted reduce и Nesterov output совпадают с direct FP32 reference в заданном tolerance.
- **SC-003**: Шесть случайных permutations arrival order дают один и тот же sealed-set и result hash внутри reproducibility class.
- **SC-004**: Duplicate, conflict, wrong-parent/schema, zero-token, malformed и late submissions имеют ожидаемые stable receipts.
- **SC-005**: Crash-point matrix на seal/aggregate/artifact/current-pointer transitions не приводит к double apply или split-brain current model.
- **SC-006**: Hard-deadline failure оставляет parent current и публикует диагностируемый `ABORTED` record.
- **SC-007**: gRPC loopback contract проходит compatibility fixtures и не содержит unsafe tensor deserialization.

## Assumptions

- Logical workers и coordinator доверяют друг другу до security feature `008`.
- Один coordinator является authoritative writer; HA leader election не входит в этот шаг.
- Update payload uncompressed и доступен через artifact store/stream adapter.
- Strict synchronous sealed-set baseline является default для сравнения с будущей asynchrony.

## Out of Scope

- Compression, sharded transfer, P2P distribution и regional hierarchy.
- Adaptive scheduling, stale update acceptance и elastic membership.
- mTLS, cryptographic signatures, revocation и Byzantine-robust aggregation.
- Высокодоступный multi-leader coordinator.
- Реальный WAN performance benchmark.
