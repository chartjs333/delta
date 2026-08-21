# Feature Specification: Адаптивное планирование неоднородных workers

**Feature Branch**: `007-adaptive-heterogeneous-scheduling`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `006-regional-hierarchical-reduce`

## Summary

Workers различаются по GPU, памяти, скорости обучения, upload/download, RTT и стабильности. Одинаковый workload заставляет быстрых ждать медленных, а произвольно длинные local rounds увеличивают optimization drift. Функция вводит измеренные capability profiles, per-round workload/region planning, адаптивное число локальных optimizer steps `H_i`, deadlines и feedback controller.

Strict synchronous sealed-set режим остаётся default и reference. Опциональный bounded-asynchronous mode принимает только updates с ограниченной staleness и явно versioned weighting policy; он выключен по умолчанию и не может обходить drift/quality guards.

## User Scenarios & Testing

### US1 — Составить план для неоднородных workers (Priority: P1)

Scheduler получает свежие benchmark/network profiles и формирует immutable round topology, assignments, token budgets и deadlines, чтобы workers завершали близко к общей целевой длительности.

**Independent Test**: deterministic simulator с быстрыми/медленными GPU и разными WAN links выдаёт один и тот же plan; workloads пропорциональны измеренной capacity в пределах caps, а ни одна операция не ждёт бесконечно.

**Acceptance Scenarios**:

1. **Given** валидные capability profiles, **When** scheduler создаёт round plan, **Then** каждый включённый worker получает region, local-step/token budget, expected duration и soft/hard deadline.
2. **Given** profile истёк или несовместим с model mode/memory requirement, **When** planning выполняется, **Then** worker benchmark-ится повторно либо исключается с явной причиной.
3. **Given** fast и slow workers, **When** token budgets распределены, **Then** fast worker получает больший budget при соблюдении minimum/fairness и max-contribution caps.
4. **Given** недостижимый quorum при доступных capacities/deadline, **When** plan валидируется, **Then** round не открывается и возвращает infeasibility report.

### US2 — Адаптировать длительность local round к сети и drift (Priority: P1)

Controller выбирает `H_i`, чтобы амортизировать коммуникацию, но уменьшает его при признаках расхождения локальных updates.

**Independent Test**: при росте expected communication time scheduler увеличивает `H_i` до configured cap; при превышении drift thresholds следующий план уменьшает cap/`H_i`; одинаковая telemetry history даёт одинаковое решение.

**Acceptance Scenarios**:

1. **Given** `T_step`, `T_comm` и target communication share `ρ`, **When** вычисляется lower bound, **Then** используется `ceil(T_comm·(1−ρ)/(ρ·T_step))` при валидных положительных входах.
2. **Given** communication-derived value ниже/выше policy bounds, **When** plan строится, **Then** `H_i` clamp-ится к `[H_min,H_max_effective]`.
3. **Given** drift norm/cosine/validation guard превышен, **When** controller обновляет policy, **Then** `H_max_effective` уменьшается или worker/codec mode quarantined; рост `H` запрещён до recovery condition.
4. **Given** network target невозможно выполнить без нарушения drift cap, **When** plan публикуется, **Then** он явно отмечает `COMM_TARGET_UNMET`, а не скрывает конфликт.

### US3 — Не ждать stragglers бесконечно и экспериментировать с bounded staleness (Priority: P2)

Coordinator завершает synchronous round по seal policy, а отдельный feature-flagged path может оценить немного устаревшие updates.

**Independent Test**: straggler/disconnect suite завершает round к hard deadline; async mode принимает только `0≤τ≤τ_max`, вычисляет documented weight и никогда не меняет synchronous default results.

**Acceptance Scenarios**:

1. **Given** worker не успел к hard deadline, **When** minimum workers/tokens достигнуты до seal, **Then** он исключается как late и round продолжается без него; иначе round abort-ится.
2. **Given** update от parent version с staleness `τ>τ_max`, **When** async intake включён, **Then** update отвергается.
3. **Given** допустимый stale update, **When** policy применена, **Then** effective weight равен `n_i·exp(−λτ_i)·a_i`, где `a_i=max(0,cos(Δ_i,m_t))^p` или documented neutral value при нулевом momentum.
4. **Given** async flag выключен, **When** wrong-parent update поступает, **Then** поведение полностью совпадает со strict synchronous feature `003`.
5. **Given** quality/drift guard сработал, **When** следующий round планируется, **Then** async mode автоматически отключается до explicit recovery gate.

## Edge Cases

- Нулевой/отрицательный `T_step`, bandwidth или target `ρ` вне `(0,1)`.
- Профиль измерен на другой model/schema/sequence length/dtype.
- Worker сообщает высокую скорость, но систематически не выполняет assignments.
- Fast worker мог бы доминировать по token contribution.
- Очень медленный worker получает меньше одного optimizer step.
- `H_comm > H_max_drift` и communication target недостижим.
- Momentum нулевой, delta нулевой или cosine numerically unstable.
- Stale update создан до topology/schema/codec change.
- Clock skew в worker timestamps; coordinator использует monotonic receipt/deadline time.
- Worker disconnect/reconnect с тем же identity и новым profile.
- Region reassignment между rounds, но не внутри open round.
- Telemetry window недостаточен либо содержит outliers.

## Requirements

### Functional Requirements

- **FR-001**: `CapabilityProfile` MUST быть versioned и включать worker/hardware/software/model-mode fingerprint, memory limit, measured step/tokens rate, peak memory, upload/download, RTT/jitter/loss to candidate regions, reliability observations, sample size и expiry.
- **FR-002**: Profiles MUST создаваться standard benchmark probe и MUST быть привязаны к конкретным model/schema/sequence/dtype settings; произвольные self-claims не являются authoritative measurements.
- **FR-003**: Scheduler MUST отбрасывать expired/incompatible profiles либо использовать explicit conservative fallback policy.
- **FR-004**: `SchedulingPolicy` MUST задавать round duration target, `H_min/H_max`, token min/max, target communication share `ρ`, contribution cap, deadlines, quorum и fairness/aging parameters.
- **FR-005**: Для положительных estimates communication lower bound MUST вычисляться как `H_comm=ceil(T_comm(1−ρ)/(ρT_step))` с documented composition upload+download+protocol time.
- **FR-006**: Planned local steps MUST быть `clamp(max(H_min,H_comm,policy_floor), H_min,H_max_effective)` и дополнительно ограничиваться data/token/deadline/memory feasibility.
- **FR-007**: Если communication lower bound конфликтует с drift/memory/deadline cap, scheduler MUST сохранить cap и emit infeasibility/target-unmet reason; нельзя бесконтрольно увеличивать `H`.
- **FR-008**: Token/work allocation MUST учитывать measured throughput и target duration, но MUST применять per-worker contribution cap и configurable minimum/aging, чтобы один worker не доминировал и совместимые slow workers не голодали бесконечно.
- **FR-009**: Scheduler MUST генерировать immutable `RoundSchedule`/`ReduceTopology` before round open; membership/assignments не мутируют после open.
- **FR-010**: Region placement MAY использовать measured latency/bandwidth и configured locality constraints, но MUST быть deterministic для одного input snapshot/seed.
- **FR-011**: Planner MUST проверять model memory compatibility и не назначать mode, превышающий measured/specified device budget.
- **FR-012**: Expected duration/deadlines MUST включать local compute, update encode/upload, regional/global wait и global download estimates с safety margin.
- **FR-013**: Feedback controller MUST ingest only committed historical evidence and compute versioned drift signals: update norm ratio/outliers, pairwise/centroid cosine dispersion, deadline misses и optional held-out validation probe.
- **FR-014**: Drift policy MUST иметь thresholds, hysteresis, minimum evidence window и actions `DECREASE_H`, `HOLD`, `RECOVER_GRADUALLY`, `QUARANTINE`, `DISABLE_ASYNC`.
- **FR-015**: Изменение scheduling policy/state MUST быть persisted и связано с evidence window/hash; decision должна быть воспроизводима offline.
- **FR-016**: Strict synchronous mode MUST оставаться default и принимать только exact-parent updates согласно feature `003`.
- **FR-017**: Bounded-asynchronous mode MUST быть отдельным feature flag с `τ_max`, `λ`, `p`, neutral-momentum rule, norm/schema/topology gates и independent metrics.
- **FR-018**: Async intake MUST вычислять staleness по model lineage, отвергать `τ<0`, `τ>τ_max` и updates через incompatible schema/codec/topology transitions.
- **FR-019**: Effective async weight MUST быть `n_i exp(−λτ_i) a_i`; zero/non-finite/negative result отвергается, а exact formula/version записывается в result lineage.
- **FR-020**: Async mode MUST автоматически отключаться при drift/quality guard, недостаточном evidence или operator kill switch.
- **FR-021**: Hard deadlines MUST гарантировать terminal round outcome; heartbeat/progress messages не могут продлевать hard deadline бесконечно.
- **FR-022**: Scheduler MUST emit machine-readable plan/infeasibility explanation и metrics planned-vs-actual duration/tokens/network share/deadline misses.
- **FR-023**: Simulation API MUST позволять replay capability/network/churn traces с deterministic clock/seed.

### Non-Functional Requirements

- **NFR-001**: Одинаковый profile/evidence snapshot, policy и seed MUST давать byte-identical schedule decision.
- **NFR-002**: Planning for 50 workers and representative shard topology SHOULD завершаться менее чем за 5 seconds на CI-class CPU; измерение фиксируется как target evidence.
- **NFR-003**: Ни один test/production round не должен оставаться non-terminal после configured hard deadline plus bounded cleanup allowance.
- **NFR-004**: При feasible profiles predicted communication share SHOULD быть ≤ configured `ρ`; infeasible cases должны быть явно классифицированы.
- **NFR-005**: Adaptive decisions MUST быть observable, reversible и сравнимы с fixed-H synchronous control.
- **NFR-006**: Async quality improvement не предполагается; он считается experimental до benchmark feature `010`.

### Key Entities

- **CapabilityProfile**: измеренный worker/network/model-mode snapshot.
- **SchedulingPolicy**: versioned constraints/objective и safety caps.
- **RoundSchedule**: immutable topology, assignments, budgets, deadlines и estimates.
- **SchedulingDecision**: inputs/evidence hash, chosen values и reasons.
- **DriftEvidenceWindow**: committed update/quality/deadline summaries.
- **AdaptiveControllerState**: current effective caps, hysteresis и quarantine state.
- **StalenessPolicy**: async formula/version/limits/kill state.

## Success Criteria

- **SC-001**: Heterogeneous simulator строит deterministic feasible schedules и не назначает incompatible/expired workers.
- **SC-002**: Для feasible network cases `H_i` удовлетворяет communication formula/caps; infeasible cases имеют точный reason code.
- **SC-003**: Drift-threshold fixture уменьшает `H_max_effective`, hysteresis предотвращает oscillation, recovery повышает cap только постепенно.
- **SC-004**: Planned-vs-actual simulation показывает bounded round completion и отсутствие indefinite straggler wait.
- **SC-005**: Async acceptance/weight fixtures точно реализуют staleness/alignment formula и reject all out-of-bound lineage cases.
- **SC-006**: При выключенном async все existing synchronous hashes/results остаются неизменными.
- **SC-007**: 50-worker planning target и replayable decision evidence задокументированы.

## Assumptions

- Capability measurements честны в permissioned development network; anti-tamper identity появится в `008`.
- Estimates могут ошибаться; controller сравнивает plan с actual и использует safety margins.
- Quality/drift thresholds сначала задаются conservative defaults и калибруются benchmark-ом.
- Region membership меняется только между rounds.

## Out of Scope

- Permissionless reputation/economic scheduling.
- Learned/RL scheduler и глобально оптимальный combinatorial placement.
- Unbounded async, gossip-only training или acceptance без authoritative lineage.
- Гарантия convergence для предложенной staleness formula.
- Production autoscaling/cloud procurement.
