# Feature Specification: Воспроизводимый training baseline и WAN-эмулятор

**Feature Branch**: `001-reproducible-training-baseline`  
**Created**: 2026-08-21  
**Last amended**: 2026-08-23  
**Status**: In progress — merged compatible `000` Formal GO verified by T000/HR001-001
**Depends on**: `000-formal-tla-spec`

## Formal Prerequisite

Before any implementation task begins, this branch MUST verify the exact content-addressed `FormalVerificationReport(decision=GO)` produced by `000-formal-tla-spec`, including its `formal_semantics_id`, Constitution/ADR hashes, mandatory model/proof/mutant status and offline verification result.

The baseline itself does not implement BFT consensus, but it defines artifact, failure, checkpoint and event abstractions that later implementations project into the formal trace vocabulary. Starting it before the formal lifecycle/recovery model is frozen risks introducing incompatible persistence and recovery boundaries.

## Summary

Нужен научно корректный single-node эталон, относительно которого будут сравниваться все последующие распределённые алгоритмы. Функция создаёт воспроизводимый учебный запуск, канонические run/artifact manifests, безопасные checkpoint и детерминированный WAN-эмулятор, не требующий публичного интернета или привилегий root для обязательного тестового пути.

Результат этого шага — не распределённое обучение, а измерительный фундамент: одна команда воспроизводит token-matched baseline, другая запускает сетевой профиль, а все артефакты можно проверить по схеме и хешам. Lifecycle/error/artifact events используют совместимые с `000` action/outcome/durability identifiers там, где формальная модель определяет соответствующую абстракцию.

## User Scenarios & Testing

### US0 — Проверить формальное основание до создания codebase (Priority: P1)

Инженер запускает prerequisite verifier до создания package/runtime файлов.

**Independent Test**: valid compatible Formal GO принимается; missing, `NO_GO`, altered, incompatible или unverifiable report блокирует T001+ и возвращает стабильную причину.

**Acceptance Scenarios**:

1. **Given** exact compatible `FormalVerificationReport(GO)`, **When** prerequisite check runs offline, **Then** it records verified report/evidence/semantics hashes and permits branch work.
2. **Given** no report, `NO_GO`, changed formal semantics, failed theorem/model/mutant or corrupted evidence, **When** check runs, **Then** implementation remains blocked.
3. **Given** a protocol-semantic amendment after GO, **When** compatibility is re-evaluated, **Then** prior GO is invalid until the affected formal gate is rerun.

### US1 — Воспроизвести эталонное обучение (Priority: P1)

Исследователь запускает маленькую causal-language-model задачу из декларативного конфига и получает checkpoint, метрики и manifest, достаточные для точного повторения запуска.

**Independent Test**: два запуска на одной поддерживаемой платформе с одинаковыми входами и seed дают одинаковые назначения данных, число non-padding tokens и checkpoint hash; floating-point метрики совпадают в документированном допуске.

**Acceptance Scenarios**:

1. **Given** валидный локальный dataset manifest и baseline config, **When** выполнен `delta baseline run`, **Then** создаются checkpoint, `metrics.jsonl` и `run-manifest.json` со статусом `COMPLETED`.
2. **Given** те же входные хеши, версии и seed, **When** запуск повторён, **Then** порядок batch, processed-token count и итоговый checkpoint воспроизводимы.
3. **Given** checkpoint незавершённого запуска на разрешённой границе, **When** выполнен resume, **Then** итог эквивалентен непрерывному запуску.

### US2 — Проверить поведение под WAN-профилем без реальной глобальной сети (Priority: P1)

Инженер задаёт RTT, bandwidth, jitter, loss и disconnect schedule и прогоняет timeout/retry-сценарий полностью локально.

**Independent Test**: один и тот же профиль и seed воспроизводят одинаковую последовательность задержек, потерь и отключений; тест завершается в ограниченное время без доступа к интернету.

**Acceptance Scenarios**:

1. **Given** валидный unprivileged network profile, **When** запускается smoke scenario, **Then** измеренные события соответствуют профилю и записываются в JSONL.
2. **Given** 100% loss или принудительный disconnect, **When** истекает deadline, **Then** операция отменяется с типизированной ошибкой, не зависает и освобождает ресурсы.
3. **Given** Linux host с явно разрешённым `tc`, **When** выбран privileged adapter, **Then** профиль применяется и гарантированно очищается даже после ошибки; этот путь не обязателен для CI.

### US3 — Проверить происхождение и целостность артефактов (Priority: P2)

Ревьюер проверяет run manifest и связанные артефакты без повторного обучения.

**Independent Test**: verifier принимает неизменённый bundle и отвергает подменённый config, dataset manifest, checkpoint или metrics file.

**Acceptance Scenarios**:

1. **Given** завершённый run bundle, **When** выполнен `delta artifacts verify`, **Then** все ссылки разрешаются локально и SHA-256 совпадают.
2. **Given** изменённый байт в checkpoint, **When** bundle проверяется, **Then** verifier возвращает ненулевой exit code и точный идентификатор повреждённого объекта.

## Edge Cases

- Formal report существует, но его source/spec/Constitution или semantics ID несовместимы.
- Formal report подписан/хеширован корректно, но mandatory mutant unexpectedly passed.
- Пустой dataset или dataset без единого non-padding token.
- Последний batch короче заданного размера.
- NaN/Inf loss, градиенты или параметры.
- Прерывание между записью checkpoint и публикацией manifest.
- Повторный запуск в уже существующий output directory.
- Различия CPU/GPU kernels и невозможность bitwise-идентичности между платформами.
- Недоступность `tc`, отсутствие root/capabilities, Windows/macOS runner.
- Нулевой bandwidth, jitter больше base latency, некорректная вероятность loss.

## Requirements

### Functional Requirements

- **FR-000**: Before T001 or any production code, the branch MUST independently verify a compatible `FormalVerificationReport(decision=GO)` and persist its report/evidence/formal-semantics hashes in branch evidence.
- **FR-001**: Проект MUST предоставлять устанавливаемый пакет `deltatorrent` и CLI `delta` для Python 3.12.
- **FR-002**: Baseline config MUST иметь версионированную строгую схему и запрещать неизвестные поля по умолчанию.
- **FR-003**: Репозиторий MUST содержать маленький лицензированно-безопасный синтетический corpus fixture и детерминированный tokenizer fixture для offline-тестов.
- **FR-004**: Baseline runner MUST выполнять обучение маленькой causal language model с gradient accumulation, AdamW и явно заданными dtype/device параметрами.
- **FR-005**: Система MUST считать вклад по фактически обработанным non-padding tokens; padding, пропущенные и повторно обработанные после rollback токены не учитываются дважды.
- **FR-006**: Каждый запуск MUST публиковать канонический `run-manifest.json` с config hash, code revision, dependency lock hash, platform fingerprint, seeds, dataset/model/tokenizer hashes, token counts, checkpoint links и статусом.
- **FR-007**: Checkpoint и tensor artifacts MUST использовать безопасный формат без pickle; запись MUST быть atomic publish через временный файл и rename/commit marker.
- **FR-008**: Metrics MUST писаться как append-safe JSONL и включать step, optimizer step, processed tokens, loss, learning rate, throughput, wall time и peak memory при наличии.
- **FR-009**: Resume MUST восстанавливать model, optimizer, scheduler, scaler при наличии, RNG states, sampler cursor и token counters с разрешённой checkpoint boundary.
- **FR-010**: CLI MUST предоставлять как минимум `baseline run`, `baseline resume`, `artifacts verify` и `netem smoke` с машинно-читаемым exit status.
- **FR-011**: Network profile MUST описывать latency, jitter, bandwidth, loss, reordering, disconnect windows, operation deadline и deterministic seed.
- **FR-012**: Обязательный WAN test adapter MUST работать без root и публичного интернета; Linux `tc/netem` MAY быть дополнительным интеграционным adapter.
- **FR-013**: Все persisted files, на которые ссылается manifest, MUST иметь SHA-256 и media/schema version.
- **FR-014**: Baseline и обязательные тесты MUST завершаться при запрещённом outbound network access.
- **FR-015**: Любая невалидная числовая величина MUST останавливать запуск до публикации `COMPLETED` и фиксироваться как структурированная причина `FAILED`.
- **FR-016**: Нельзя перезаписывать завершённый immutable run; повторное использование `run_id` допускается только как идемпотентное чтение того же manifest.
- **FR-017**: Lifecycle, failure, durability and artifact-publication events that correspond to `000` abstractions MUST use the canonical trace/action/outcome identifiers or an explicitly versioned projection map.
- **FR-018**: Checkpoint/artifact recovery semantics MUST not contradict formal identity-preserving repair, immutable finalized history or idempotent replay assumptions.

### Non-Functional Requirements

- **NFR-000**: Formal prerequisite verification MUST run offline and fail closed on any missing, altered or incompatible artifact.
- **NFR-001**: CPU smoke run SHOULD завершаться не более чем за 10 минут на типичном 4-core CI runner.
- **NFR-002**: Все unit и contract tests MUST быть детерминированы, timeout-bounded и не зависеть от порядка выполнения.
- **NFR-003**: Платформенные различия MUST быть отражены в manifest; bitwise equality требуется только внутри объявленного reproducibility class.
- **NFR-004**: Ошибки CLI MUST иметь стабильный код, краткое сообщение и структурированные детали без секретов.
- **NFR-005**: Domain-модели MUST не импортировать PyTorch, CLI, transport или filesystem adapters.
- **NFR-006**: Пиковая память, время и throughput являются измерениями, а не hard-coded заявлениями.

### Key Entities

- **FormalPrerequisiteRecord**: verified Formal GO/report/evidence/semantics identifiers and compatibility decision.
- **BaselineConfig**: версия схемы, model/data/optimizer/scheduler/runtime/reproducibility параметры.
- **DatasetManifest**: dataset ID, tokenizer hash, ordered shard hashes, split и token-count policy.
- **RunManifest**: неизменяемое описание запуска и связей между входами, кодом, метриками и выходами.
- **CheckpointManifest**: безопасные tensor/state files, training cursor и хеши.
- **NetworkProfile**: детерминированные WAN-ограничения и fault schedule.
- **ArtifactRef**: media type, schema version, byte length, SHA-256 и локатор.

## Success Criteria

- **SC-000**: Exact compatible Formal GO verifies from a clean offline environment before any package/production file is introduced.
- **SC-001**: Два одинаковых CPU smoke run проходят заявленный reproducibility contract и имеют одинаковый processed-token count и checkpoint hash.
- **SC-002**: Resume equivalence test достигает того же итогового checkpoint, что и непрерывный run.
- **SC-003**: Corruption test обнаруживает изменение каждого типа связанного артефакта до его использования.
- **SC-004**: WAN simulation suite воспроизводит loss/disconnect schedule и завершает каждый сценарий в заданный deadline.
- **SC-005**: Полный обязательный test suite проходит при полностью отключённом публичном интернете и без root.
- **SC-006**: Один run bundle содержит достаточно данных, чтобы другой инженер однозначно определить model/data/config/code/dependency inputs.
- **SC-007**: Baseline lifecycle/artifact traces validate against the declared formal projection boundary for the abstractions they use.

## Assumptions

- `000-formal-tla-spec` is implemented and has a compatible Formal GO before this branch begins.
- Референсная реализация использует Python 3.12 и PyTorch; версии фиксируются lockfile.
- Для CI используется маленькая модель и synthetic corpus; реальные веса и датасеты не коммитятся.
- Bitwise reproducibility между разными accelerator architectures не обещается; задаётся tolerance-based cross-platform contract for worker-local computation only.
- Git commit SHA доступен при обычном запуске, но source archive допускает явный `source_revision`.

## Out of Scope

- Реализация или изменение TLA+/theorem proofs; formal semantic changes возвращаются в 000 first.
- Любое межмашинное обучение или координация раундов.
- Локальные псевдоградиенты, outer optimizer и distributed reduce.
- P2P-протокол, identity/security plane и QLoRA.
- Публикация фактических performance/quality claims DeltaTorrent.
