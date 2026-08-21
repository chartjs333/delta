# Feature Specification: Региональная и шардированная иерархическая редукция

**Feature Branch**: `006-regional-hierarchical-reduce`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `005-content-addressed-p2p-distribution`

## Summary

Центральный coordinator не должен принимать отдельный полный update от каждого worker через межрегиональные каналы. Функция вводит статически заданные регионы и parameter-shard reducers: coordinator сначала запечатывает accepted worker set внутри каждого региона, региональные reducers вычисляют FP32 weighted numerators, затем global reducers суммируют региональные numerators и token denominators.

Ключевой математический инвариант: иерархия должна совпадать с flat token-weighted reduce. Региональный уровень передаёт не безусловное среднее, а `Σ n_i·Δ_i` и `Σ n_i`. Все shards одного региона обязаны ссылаться на один accepted-set hash. Только финальная global delta допускается в P2P distribution; regional partials остаются reduce-plane artifacts.

## User Scenarios & Testing

### US1 — Провести раунд через региональные reducers (Priority: P1)

Оператор задаёт topology с несколькими регионами; workers отправляют encoded shards только назначенным региональным reducers, после чего global level получает по одному partial на регион/shard.

**Independent Test**: минимум 3 региона с неодинаковым количеством workers/tokens дают global delta, совпадающую с flat decode-and-token-weighted reference.

**Acceptance Scenarios**:

1. **Given** immutable round topology и worker assignments, **When** regional intake открыт, **Then** каждый worker/shard имеет ровно один authoritative destination и bounded retry route.
2. **Given** region seal с accepted workers, **When** regional reduce выполняется, **Then** каждый shard result содержит weighted numerator, общий regional token denominator и accepted-set hash.
3. **Given** все обязательные regional partials, **When** global reduce выполняется, **Then** результат равен `Σ_r numerator_r / Σ_r tokens_r`.
4. **Given** regions с 10% и 90% токенов, **When** они объединяются, **Then** их вклад пропорционален токенам, а не числу regions.

### US2 — Выполнить parameter-sharded reduce параллельно и согласованно (Priority: P1)

Большая parameter schema делится на logical shards, которые обрабатываются отдельными reducer assignments.

**Independent Test**: shuffled completion order всех shard reducers собирается в одну global delta; missing/duplicate/inconsistent shard не допускает publication.

**Acceptance Scenarios**:

1. **Given** canonical `ReduceShardPlan`, **When** schema разбивается, **Then** каждый trainable parameter segment покрыт ровно один раз, без пробелов и overlap.
2. **Given** несколько shard reducers одного региона, **When** они публикуют partials, **Then** все partials ссылаются на один region/round/accepted-set/token-total tuple.
3. **Given** один shard использует иной accepted-set hash или denominator, **When** assembly начинается, **Then** весь regional/global result отвергается как inconsistent.
4. **Given** все shards валидны, **When** global delta assembled, **Then** parameter schema/order/hash полностью совпадают с parent.

### US3 — Диагностировать неполную иерархию и безопасно повторить работу (Priority: P2)

Reducer или сеть падает, partial отправляется повторно, либо region не достигает quorum.

**Independent Test**: retry/crash/deadline matrix не удваивает numerator, не смешивает topology versions и либо публикует один exact global result, либо abort-ит round без изменения модели.

**Acceptance Scenarios**:

1. **Given** повтор exact regional partial ID/hash, **When** global intake уже принял его, **Then** возвращается существующий receipt без повторного сложения.
2. **Given** тот же partial ID с другим bytes/hash, **When** он подан, **Then** conflict отвергается.
3. **Given** один region/shard не завершился к hard deadline, **When** policy не разрешает исключить регион до seal, **Then** round abort-ится и current model не меняется.
4. **Given** topology version изменилась для следующего round, **When** приходит partial старой topology, **Then** он не может попасть в новый accepted set.

## Edge Cases

- Region с одним worker или нулём accepted workers.
- Worker обработал разное число токенов, но все shards должны иметь один token count.
- Один local encoded shard повреждён, остальные валидны.
- Parameter segment на tensor boundary и очень большой tensor, разделённый на несколько shards.
- Regional reducers завершились с разным arrival order.
- Duplicate worker update попал на два reducer endpoints.
- Region seal и late worker update происходят одновременно.
- Partial numerator non-finite/overflow или denominator mismatch.
- Global reducer restart после записи части shard outputs.
- Topology содержит неизвестный worker, duplicate region или неполное schema coverage.
- Regional partial ошибочно направлен в swarm publisher.
- Region потерян полностью после seal.

## Requirements

### Functional Requirements

- **FR-001**: Каждый hierarchical round MUST иметь immutable `ReduceTopology` с topology version/hash, regions, worker membership, shard plan, reducer assignments, endpoints и deadline policy.
- **FR-002**: `ReduceShardPlan` MUST детерминированно покрывать canonical parameter schema ровно один раз; overlap/gap запрещены.
- **FR-003**: Coordinator MUST seal отдельный `RegionalAcceptedSet` до вычисления partials; set содержит exact local update refs, worker IDs и token counts.
- **FR-004**: Все shard reducers одного региона MUST использовать один и тот же `RegionalAcceptedSet` hash и regional token denominator.
- **FR-005**: Worker contribution token count MUST быть одинаковым для всех его shards и проверяться против accepted local update manifest.
- **FR-006**: Regional reducer MUST validate/decode каждый local encoded shard и аккумулировать FP32 weighted numerator `N_{r,j}=Σ_i n_i·Δ_{i,j}` в canonical worker order.
- **FR-007**: `RegionalPartialManifest` MUST включать round/topology/region/shard/schema/accepted-set hashes, weighted-numerator artifact, token denominator, worker count и validation evidence.
- **FR-008**: Regional partial MUST быть safe, immutable, content-addressed reduce-plane artifact и MUST быть запрещён distribution publisher-ом.
- **FR-009**: Global intake MUST принимать ровно один authoritative partial на required region/shard tuple; duplicate same hash идемпотентен, conflict отвергается.
- **FR-010**: Global reducer MUST вычислять `N_j=Σ_r N_{r,j}` и `T=Σ_r T_r`, затем `Δ̄_j=N_j/T` в FP32.
- **FR-011**: Global denominator MUST считаться один раз по consistent region token totals; нельзя суммировать denominator отдельно по каждому parameter shard.
- **FR-012**: Assembly MUST требовать полный required region×shard set либо explicit pre-seal exclusion policy; post-hoc silent exclusion запрещено.
- **FR-013**: Все assembled shards MUST иметь exact parent parameter schema coverage/order и один global accepted-topology hash.
- **FR-014**: Outer optimizer и atomic publication MUST повторно использовать contract feature `003`; только fully assembled global delta меняет current model.
- **FR-015**: Regional/global reducer operations MUST быть идемпотентными по command/partial ID и content hash и restart-safe.
- **FR-016**: Coordinator MUST сохранять lineage local update→regional accepted set→regional partial→global set→global delta→model.
- **FR-017**: Reference transport MUST поддерживать bounded streaming upload/download per shard и retry receipts; domain math не зависит от transport.
- **FR-018**: Reducer MAY обрабатывать shards параллельно, но output identity MUST не зависеть от completion order.
- **FR-019**: Topology validation MUST отклонять duplicate membership, unknown IDs/endpoints, missing schema coverage и incompatible codec allowlists до round open.
- **FR-020**: Metrics MUST включать intra/inter-region bytes, local/partial counts, per-region tokens, decode/reduce/assembly timing, shard skew, retries и abort reason.
- **FR-021**: Flat central reducer feature `003` MUST оставаться selectable reference/fallback для тех же sealed local updates.

### Non-Functional Requirements

- **NFR-001**: На deterministic fixtures hierarchical result MUST совпадать с flat FP32 reference в явно заданном tolerance.
- **NFR-002**: Global cross-region fan-in count SHOULD быть proportional `regions × shards`, а не `workers × shards`; test/evidence фиксирует фактические message/object counts.
- **NFR-003**: Reducers MUST применять memory/resource limits per shard и не требовать full-model numerator в каждом shard process.
- **NFR-004**: Все deadlines/cancellation/retries MUST быть bounded и тестироваться через WAN simulator.
- **NFR-005**: Hierarchy correctness MUST не зависеть от region size, token imbalance или arrival order.
- **NFR-006**: Текущая feature не обещает Byzantine robustness или automatic reducer failover; failure приводит к retry/abort по явной policy.

### Key Entities

- **ReduceTopology**: immutable regions, membership, shard/reducer plan и policy.
- **RegionalAcceptedSet**: sealed workers/updates/tokens одного региона.
- **WeightedNumeratorShard**: FP32 `Σ n_i·Δ_i` для schema segment.
- **RegionalPartialManifest**: lineage numerator/denominator/accepted set.
- **GlobalPartialSet**: required region×shard refs и consistency hash.
- **HierarchicalRoundResult**: assembled global delta и topology evidence.

## Success Criteria

- **SC-001**: 3-region/heterogeneous-token test совпадает с flat reference для каждого tensor.
- **SC-002**: Shard plan property tests доказывают exact non-overlapping schema coverage.
- **SC-003**: Arrival permutation, parallel completion и retry не меняют partial/global hashes.
- **SC-004**: Mismatched accepted-set/token/schema/topology, missing/duplicate shard и non-finite numerator блокируют publication.
- **SC-005**: Fault matrix либо восстанавливает тот же result, либо abort-ит без model/outer-state change.
- **SC-006**: Evidence показывает сокращение global fan-in с worker-level до region-level object count на committed topology fixture.
- **SC-007**: Flat fallback и P2P boundary regression suites остаются зелёными.

## Assumptions

- Region membership и reducer assignments статичны в пределах round.
- Logical trusted reducers используются до identity/resilience feature `008`.
- Региональный уровень может находиться ближе к workers, но network placement в этом шаге задаётся config, а не автоматически.
- Regional partial transport использует FP32 correctness-first representation; дополнительное сжатие partials отложено.

## Out of Scope

- Automatic topology discovery, capability benchmarking и adaptive placement.
- Bounded asynchrony/staleness acceptance.
- Byzantine-robust aggregation, signatures и redundant committee consensus.
- P2P-раздача regional partials.
- Advanced streaming overlap и compressed-domain reduce.
