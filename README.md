# DeltaTorrent / DeltaReduce v1

DeltaTorrent — formal-first система распределённого обучения и дообучения языковых моделей на географически распределённых GPU. **DeltaReduce v1** является authoritative архитектурой reduce/apply plane.

Формальный predecessor `000-formal-tla-spec` получил `FormalVerificationReport(decision=GO)` для formal semantics:

```text
sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6
```

Implementation branches всё равно начинают работу только после merge PR #1 и независимой проверки merged evidence.

## Неподвижные протокольные инварианты

1. Нет единственного authoritative coordinator: state machine реплицирована на `3f+1` validators, QC требует `2f+1` подписей.
2. Каждый `WorkTicket` domain-pure и фиксирует data range, `B`, `H`, parent, schema и arithmetic profile.
3. Adaptive `H_i`, stale weighting и device-speed mathematical weights запрещены.
4. Consensus reduce/apply выполняется в canonical integer/rational fixed-point space; FP accumulation запрещена.
5. `{T_j,C_j,AC_j}` фиксируется до seed `ρ_t`.
6. Certificate lineage: `ISC → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC`.
7. Только ApplyQC может продвинуть current checkpoint.
8. Reduce и distribution planes разделены: local/partial artifacts не входят в P2P swarm.
9. Protocol-semantic change сначала меняет formal baseline, а затем код.

## Hybrid Runtime v1

Reference implementation использует три runtime, разделённые по fault domain и workload:

| Runtime | Ответственность | Не имеет права делать |
| --- | --- | --- |
| **C++20/23 pure core** | canonical parsing, legality, fixed-point math, certificates, deterministic next state | sockets, wall-clock decisions, JVM/Python object access |
| **C++ native runtime** | single-writer reactor, WAL, snapshots, durable vote guard, recovery ordering | выбирать peers/маршруты, интерпретировать transport topology |
| **Java reference node** | JDK 25 reference runtime, Netty, TLS, peer sessions, backpressure, opaque timers, observability, FFM | выбирать transition, quorum, bucket membership, coefficient или current checkpoint |
| **Python/PyTorch worker** | local training, data/token accounting, QLoRA, normalized pseudo-gradient, evaluation | consensus reduce/apply, current-state authority |

Главный boundary principle:

> C++ не знает о соединениях; Java не принимает протокольных решений; Python не является validator state machine.

Подробности: `docs/adr/0010-hybrid-runtime-boundary.md`, `docs/architecture/hybrid-runtime.md`, `specs/HYBRID-RUNTIME-MAP.md`.

## FFI contract

- Java вызывает только маленький versioned **C ABI** через FFM; C++ ABI никогда не пересекает границу.
- Command/effect API передаёт canonical bytes, а не набор fine-grained setters.
- Все mutating calls выполняются одним consensus reactor thread.
- Native runtime делает durable commit до возврата outbound effects (`persist-before-expose`).
- C++ exceptions не пересекают ABI; возвращаются versioned numeric status codes.
- Java-owned direct memory заимствуется только на время синхронного downcall; native pointer не сохраняется.
- Zero-copy ingress является fast path. Heap/composite/non-contiguous input использует bounded direct-copy fallback с идентичным результатом.
- Java доставляет opaque `timer_token`; только C++ решает, разрешён ли timeout transition.
- Startup handshake проверяет ABI, protocol/schema versions, build ID и `formal_semantics_id`.

## Репозиторий

```text
formal/                 TLA+, Lean, mutants, refinement, evidence
delta-protocol/         canonical schemas, IDs and cross-language fixtures
delta-worker-python/    Python/PyTorch baseline, local engine, QLoRA
delta-core-cpp/         pure deterministic protocol core
delta-runtime-cpp/      single-writer reactor, WAL, snapshot, recovery
delta-ffi/              C ABI and generated/handwritten Java bindings
delta-node-java/        Netty/TLS/P2P/timers/operations shell
integration/            polyglot traces, crash matrix, E2E and benchmark fixtures
```

## Последовательность веток

| Шаг | Ветка | Runtime focus |
| ---: | --- | --- |
| 0 | `000-formal-tla-spec` | executable semantics and parametric proofs — GO established |
| 1 | `001-reproducible-training-baseline` | Python scientific baseline + runtime-neutral protocol foundation |
| 2 | `002-local-round-engine` | Python fixed-ticket worker engine |
| 3 | `003-bft-round-state-machine` | C++ pure core/runtime/WAL + C ABI + minimal Java FFM harness |
| 4 | `004-compressed-delta-protocol` | C++ fixed-point/shard implementation and cross-language byte conformance |
| 5 | `005-content-addressed-p2p-distribution` | Java Netty P2P and zero-copy fast path with safe fallback |
| 6 | `006-regional-hierarchical-reduce` | C++ integer hierarchy + Java regional routing |
| 7 | `007-domain-pure-ticket-scheduling` | C++ deterministic plan/lease state + Java admission telemetry |
| 8 | `008-certificates-and-consensus` | C++ full certificate/apply chain + Java TLS/message/timer shell |
| 9 | `009-qlora-8gb-mode` | Python QLoRA worker + C++ adapter aggregate/apply + Java node |
| 10 | `010-wan-benchmark-and-quality` | Python+C+++Java E2E, sanitizer/fuzz/crash and quality benchmark |
| 11 | `011-multiregion-pilot` | packaged validator/node/worker deployment and fault campaign |

Каждая feature directory содержит исходные `spec.md`, `plan.md`, `tasks.md` и обязательные hybrid addenda `runtime-profile.md`/`runtime-tasks.md`.

## С чего начинается реализация

1. Merge PR #1 (`000-formal-tla-spec`).
2. Перестроить/проверить `001-reproducible-training-baseline` поверх merged main.
3. Выполнить `T000` и `HR001-001`: offline verify Formal GO and semantics ID.
4. Зафиксировать polyglot directory boundaries и `delta-protocol` canonical fixtures.
5. Реализовать Python baseline; C++/Java production code до feature 003 не добавлять.

## Целевой MVP

20–50 permissioned workers класса 8 GB, 3–5 регионов, fixed domain-pure tickets, canonical INT16-style vectors, checked INT64/INT128 accumulation, BFT certificate chain, ApplyQC current state и P2P-раздача certified global checkpoints.

## Источники и supersession

Исходная концепция сохранена в `docs/source/deltatorrent-concept.ru.md`. Она остаётся основанием для длительного local training, WAN realism и разделения reduce/distribution. DeltaReduce v1 и formal baseline supersede central coordination, adaptive `H_i`, stale weighting и FP32 consensus accumulation. Hybrid Runtime v1 — implementation decision, а не утверждение исходного концептуального документа.
