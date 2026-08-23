# DeltaTorrent / DeltaReduce v1

DeltaTorrent — исследовательская система для обучения и дообучения языковых моделей на географически распределённой сети GPU с ограниченной памятью и нестабильными WAN-соединениями. **DeltaReduce v1** является authoritative архитектурой её reduce/apply plane.

Репозиторий находится на стадии **specification-first**. Реализационный стек разбит на последовательные Spec Kit feature-ветки; каждая следующая ветка основана на предыдущей и добавляет одну независимо проверяемую возможность.

## Архитектурный мандат DeltaReduce v1

1. **Нет единственного authoritative coordinator.** Раунд исполняется детерминированной BFT state machine с validator set размером `3f+1`; quorum certificate требует не менее `2f+1` подписей.
2. **Только Domain-Pure Work Tickets.** Каждый ticket связан ровно с одним data domain `d`, фиксированным batch/token budget `B` и фиксированным числом local optimizer steps `H`.
3. **Нет adaptive `H_i`.** Неоднородность устройств влияет на admission, число назначаемых tickets и deadlines, но не меняет `B`, `H`, domain mixture `π_d` или математический вес ticket после фиксации `RoundConfig`.
4. **Нет FP32 accumulation в consensus reduce.** Worker нормализует local accumulation по effective step count `A_j`, затем квантует её по зафиксированному fixed-point profile. Parameter shards суммируются только в INT64/INT128-compatible integer space с доказанной границей переполнения.
5. **Input freeze предшествует randomness.** Exact set `{T_j, C_j, AC_j}` фиксируется до генерации seed `ρ_t`; seed не может влиять на включение commitments задним числом.
6. **Каждый переход сертифицирован.** Certificate chain развивается от input set через eligibility/aggregation plan и parameter QCs к `AggregateRootQC` и `ApplyQC`.
7. **Reduce и distribution разделены.** P2P swarm распространяет только одинаковые immutable datasets, checkpoints, certified global aggregates и applied checkpoints. Worker commitments, local shards и regional partials не являются distributable objects.

## Порядок реализации

| Шаг | Feature-ветка | Результат |
| ---: | --- | --- |
| 1 | `001-reproducible-training-baseline` | Воспроизводимый single-node baseline и WAN-эмулятор |
| 2 | `002-local-round-engine` | Локальный optimizer engine и canonical pseudo-gradient |
| 3 | `003-bft-round-state-machine` | Реплицированная BFT lifecycle, fixed tickets и bit-exact integer reduce |
| 4 | `004-compressed-delta-protocol` | Canonical fixed-point quantization, shard envelopes и overflow proofs |
| 5 | `005-content-addressed-p2p-distribution` | Проверяемая P2P-раздача только certified global objects |
| 6 | `006-regional-hierarchical-reduce` | Региональные/parameter-shard BFT committees без FP arithmetic |
| 7 | `007-domain-pure-ticket-scheduling` | Детерминированное планирование fixed `B/H` tickets по domains |
| 8 | `008-certificates-and-consensus` | ISC/EC/APC, shard QCs, AggregateRootQC и ApplyQC |
| 9 | `009-qlora-8gb-mode` | Adapter-only fixed-ticket QLoRA для квалифицированных 8 GB GPU |
| 10 | `010-wan-benchmark-and-quality` | Token/domain-matched WAN, BFT, safety и quality gates |
| 11 | `011-multiregion-pilot` | Permissioned pilot на 20–50 workers и 3–5 регионах |

Полный authoritative набор спецификаций находится в последней стековой ветке `011-multiregion-pilot`. Карта зависимостей и exit gates находится в `specs/ROADMAP.md`.

## Superseded legacy refs

Следующие исторические ветки больше не входят в execution path и не должны использоваться как base:

- `003-central-round-coordinator`;
- `007-adaptive-heterogeneous-scheduling`;
- `008-permissioned-trust-and-resilience`.

Они сохранены только для audit/history. Их контракты central authority, adaptive `H_i`, stale weighting и FP32 reduce заменены DeltaReduce v1.

## Как выполнять очередной шаг

1. Переключиться на нужную authoritative feature-ветку из таблицы.
2. Прочитать `.specify/memory/constitution.md`, `specs/ROADMAP.md`, затем `spec.md`, `plan.md` и `tasks.md` текущей функции.
3. Запустить cross-artifact analysis; любые упоминания central coordinator, adaptive local steps или FP32 consensus accumulation считаются blocking defects.
4. Реализовывать задачи по порядку, связывая commits с task IDs.
5. Пройти exit gate функции и final Constitution Check до перехода к следующей ветке.

## Целевой MVP

Первый убедительный WAN-прототип должен поддерживать 20–50 remote workers класса 8 GB, 3–5 регионов, permissioned BFT validator set, full-training workload порядка 100–300 млн параметров либо QLoRA, fixed domain-pure tickets, canonical INT16-style worker vectors, INT64/INT128 accumulation, certificate hierarchy и P2P-раздачу certified global checkpoints.

## Источники и supersession

Исходная концепция DeltaTorrent сохранена в `docs/source/deltatorrent-concept.ru.md`. Архитектурная поправка DeltaReduce v1 сохранена в `docs/source/deltareduce-v1-amendment.md` и имеет приоритет в вопросах central coordination, local-step adaptivity, reduce arithmetic и consensus certification.
