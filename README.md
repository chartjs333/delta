# DeltaTorrent / DeltaReduce v1

DeltaTorrent — исследовательская система для обучения и дообучения языковых моделей на географически распределённой сети GPU с ограниченной памятью и нестабильными WAN-соединениями. **DeltaReduce v1** является authoritative архитектурой её reduce/apply plane.

Репозиторий находится на стадии **formal-first, specification-first**. До реализации Python/PyTorch-веток протокол обязан пройти нулевой этап: executable TLA+ model checking для BFT lifecycle/failure/recovery и параметрические theorem-prover proofs для quorum/fixed-point/hierarchical/apply утверждений.

## Архитектурный мандат DeltaReduce v1

1. **Нет единственного authoritative coordinator.** Раунд исполняется детерминированной BFT state machine с validator set размером `3f+1`; quorum certificate требует не менее `2f+1` подписей.
2. **Только Domain-Pure Work Tickets.** Каждый ticket связан ровно с одним data domain `d`, фиксированным batch/token budget `B` и фиксированным числом local optimizer steps `H`.
3. **Нет adaptive `H_i`.** Неоднородность устройств влияет на admission, число назначаемых tickets и deadlines, но не меняет `B`, `H`, domain mixture `π_d` или математический вес ticket после фиксации `RoundConfig`.
4. **Нет FP32 accumulation в consensus reduce.** Worker нормализует local accumulation по effective step count `A_j`, затем квантует её по зафиксированному fixed-point profile. Parameter shards суммируются только в INT64/INT128-compatible integer space с доказанной границей переполнения.
5. **Input freeze предшествует randomness.** Exact set `{T_j, C_j, AC_j}` фиксируется до генерации seed `ρ_t`; seed не может влиять на включение commitments задним числом.
6. **Каждый переход сертифицирован.** Certificate chain развивается от input set через eligibility/aggregation plan и parameter QCs к `AggregateRootQC` и `ApplyQC`.
7. **Reduce и distribution разделены.** P2P swarm распространяет только одинаковые immutable datasets, checkpoints, certified global aggregates и applied checkpoints. Worker commitments, local shards и regional partials не являются distributable objects.
8. **Формальная модель предшествует коду.** Safety/failure/recovery semantics и parametric proof obligations фиксируются в `000-formal-tla-spec`; изменение протокольной семантики без обновления модели и повторного formal gate запрещено.

## Порядок реализации

| Шаг | Feature-ветка | Результат |
| ---: | --- | --- |
| 0 | `000-formal-tla-spec` | TLA+ BFT/failure/recovery model, theorem-prover proofs и обязательный Formal GO |
| 1 | `001-reproducible-training-baseline` | Воспроизводимый single-node baseline и WAN-эмулятор, заблокированные до Formal GO |
| 2 | `002-local-round-engine` | Локальный optimizer engine и canonical pseudo-gradient |
| 3 | `003-bft-round-state-machine` | Реализация, refinement и bit-exact conformance BFT lifecycle |
| 4 | `004-compressed-delta-protocol` | Canonical fixed-point quantization, shard envelopes и machine-checked overflow proofs |
| 5 | `005-content-addressed-p2p-distribution` | Проверяемая P2P-раздача только certified global objects |
| 6 | `006-regional-hierarchical-reduce` | Региональные/parameter-shard BFT committees и formal flat-equivalence obligation |
| 7 | `007-domain-pure-ticket-scheduling` | Детерминированное планирование fixed `B/H` tickets по domains |
| 8 | `008-certificates-and-consensus` | ISC/EC/APC, shard QCs, AggregateRootQC, ApplyQC и refinement gate |
| 9 | `009-qlora-8gb-mode` | Adapter-only fixed-ticket QLoRA для квалифицированных 8 GB GPU |
| 10 | `010-wan-benchmark-and-quality` | Token/domain-matched WAN, BFT, safety и quality gates |
| 11 | `011-multiregion-pilot` | Permissioned pilot на 20–50 workers и 3–5 регионах |

Полный authoritative набор спецификаций находится в последней стековой ветке `011-multiregion-pilot`. Карта зависимостей, formal obligations и exit gates находится в `specs/ROADMAP.md`.

## Formal gate

Ветка `000-formal-tla-spec` должна завершиться content-addressed `FormalVerificationReport(decision=GO)`. Минимальный gate включает:

- TLC safety checking для `f=1`, четырёх validators, message reorder/duplicate/drop, crash/restart, partition, equivocation и storage loss;
- liveness checking только под явно заданными fairness/eventual-synchrony/quorum/availability assumptions;
- machine-checked parametric proofs для quorum intersection, accumulator safety, hierarchical-flat equality и Apply uniqueness;
- зафиксированные counterexample traces для намеренно сломанных вариантов;
- refinement/trace contract, обязательный для реализационных веток `003`, `004`, `006` и `008`.

`001` и все последующие code-bearing branches не могут начинать implementation tasks при отсутствии exact compatible Formal GO.

## Superseded legacy refs

Следующие исторические ветки больше не входят в execution path и не должны использоваться как base:

- `003-central-round-coordinator`;
- `007-adaptive-heterogeneous-scheduling`;
- `008-permissioned-trust-and-resilience`.

Они сохранены только для audit/history. Их контракты central authority, adaptive `H_i`, stale weighting и FP32 reduce заменены DeltaReduce v1.

## Как выполнять очередной шаг

1. Начать с `000-formal-tla-spec` и получить Formal GO.
2. Переключиться на очередную authoritative feature-ветку из таблицы.
3. Прочитать `.specify/memory/constitution.md`, `docs/adr/0000-formal-verification-gate.md`, `specs/ROADMAP.md`, formal failure/proof artifacts, затем `spec.md`, `plan.md` и `tasks.md` текущей функции.
4. Запустить cross-artifact и formal-impact analysis; central coordinator, adaptive local steps, FP consensus accumulation и несогласованная с TLA+ transition semantics считаются blocking defects.
5. Реализовывать задачи по порядку, связывая commits с task IDs и formal trace obligations.
6. Пройти feature exit gate, regression formal gate и final Constitution Check до перехода к следующей ветке.

## Целевой MVP

Первый убедительный WAN-прототип должен поддерживать 20–50 remote workers класса 8 GB, 3–5 регионов, permissioned BFT validator set, full-training workload порядка 100–300 млн параметров либо QLoRA, fixed domain-pure tickets, canonical INT16-style worker vectors, INT64/INT128 accumulation, certificate hierarchy и P2P-раздачу certified global checkpoints.

## Источники и supersession

Исходная концепция DeltaTorrent сохранена в `docs/source/deltatorrent-concept.ru.md`. Архитектурная поправка DeltaReduce v1 сохранена в `docs/source/deltareduce-v1-amendment.md` и имеет приоритет в вопросах central coordination, local-step adaptivity, reduce arithmetic и consensus certification. ADR-0000 и Constitution 2.1.0 дополнительно требуют formal verification до production implementation.
