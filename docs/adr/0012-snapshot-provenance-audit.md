# ADR-0012 — audit существующего snapshot provenance contract

29 сентября 2026. Tasks T053/T054/T056. Только чтение источников и документация.
База: `894a82850262ad74dfeec5ef0be760311b3959ce`.
Native source прежнего опыта: `60c692f6e391f839829dfc64e93380db54cd507b`.

**Ответ: нет. STOP — `MISSING SNAPSHOT PROVENANCE CONTRACT`.**

В замороженном контракте есть требования к authenticated recovery, проверенные
частные continuity checks и именованные trust premises. Но не зафиксирован
независимый authority/provenance predicate с достаточным смыслом и evidence
binding для **полного непустого initial/recovered snapshot**, который позволил
бы ограничить domain R2 без использования самой R2 relation.

Это не утверждение, что в проекте вообще нет authentication или recovery.
Не требуется доказывать физическую криптографию или создавать production
exporter ради этого аудита. Пробел относится к контракту: существующие
предпосылки не задают проверяемую связь полного supplied snapshot с допустимым
исходным protocol prefix. Дополнить их таким смыслом молча означало бы принять
новое решение о границе доверия.

Новый predicate, proof layer, код или исправление A/B/C **не создавались**.
R1/R2.1/R2.2 CLOSED, R2.3/R2 OPEN; R3 не начат. DoD R1–R7 не изменён.

## 1. Какие объекты нельзя смешивать

- **`runtime.snapshot` / DRS1:** `journal_sequence` и canonical `RoundState`
  bytes с контрольными хэшами. Это не сериализация всех certificate collections.
- **`VoteAdmissionSnapshot` внутри DVPOL001 policy:** отдельно переданный
  prepared graph, включая proposed/finalized IDs, typed bodies, certificates,
  candidates и failure data. `snapshot.state_id` связывает его с RoundState;
  hash полной policy сохраняется в vote WAL. Он связывает байты, а не источник.
- **`nativeSnapshot` diagnostic witness:** JSON header/anchor, prior root,
  authority reference, sequence и certificate/projection references. Его
  producer authentication — отдельная предпосылка.
- **Current model/optimizer checkpoint:** сертифицированные tensor/artifact
  bytes и current pointer; это также не полный consensus snapshot.

Замороженная R2.3 требует совместную связь нужных полных collections. Успех
проверки одного из этих объектов не переносится автоматически на остальные.

## 2. Матрица существующих путей

В таблице «должна существовать» описывает уже действующие requirements,
а не утверждает наличие такого evidence у любого supplied snapshot.

| Путь появления непустого состояния | Кто создаёт | Чем аутентифицирован | Какая WAL/certificate lineage требуется | Кто проверяет continuity сейчас | Исходное requirement |
|---|---|---|---|---|---|
| **Prepared initial state/policy при `OPEN`** | Вызывающий код передаёт `Runtime::Config.initial_state_bytes` и policy; C ABI/sidecar копируют и декодируют их. `CertificateVoteRuntime` также получает их извне. Авторитетный producer полного graph в этом интерфейсе не определён. | `state_id`, полный policy hash, canonical decoding и typed checks; роли/epoch/committees проверяются по supplied policy. Это не удостоверение происхождения prepared snapshot. Комментарий «already-prepared formal state» не является attestation. | Immutable config/parent; точные сертификаты и их finalized status; исходный durable prefix, если initial cut непустой. | `validate_vote_admission_policy` / typed snapshot checks проверяют структуру и parents; Runtime связывает policy с WAL. Они не проверяют весь producing prefix initial collections. | Frozen candidate contract: independently anchored source и Init/verified history; PO-AB1; failure semantics §7, шаги 1–4. |
| **Локальный snapshot действующего Runtime** | Single-writer reactor: `process_snapshot` сохраняет текущее `state_bytes_` и WAL tip. | Хэш state bytes и checksum snapshot; local durable storage binding. На POSIX в проверенном pin есть descriptor/inode/path checks; это не remote producer attestation и не свойство, автоматически переносимое на Windows. | Существующий WAL до исходного tip, original initial state/policy, прежние votes/commands; certificate graph policy остаётся отдельным input. | `Wal::read_snapshot`, `Runtime::recover`: sequence, replay outputs, policy identity и совпадение snapshot с replay на его положительной sequence. Snapshot не заменяет prefix и не удостоверяет initial producer. | ADR-0010: владелец WAL/snapshots; 003 runtime profile; 003 FR-027; 000 FR-014 и PO-R2. |
| **Состояние после restart/replay, в том числе без snapshot-файла** | `Runtime::recover` восстанавливает state и vote caches из WAL, начиная с supplied initial state. | Integrity/canonical checks и original policy identity; authenticity исходного initial state и полноты наблюдения не выводится из checksum. | Полный сохраняемый vote/transition prefix, original bytes/sequence, matching policy, referenced certificates/artifacts; UNKNOWN/отсутствие ответа не означает пустой журнал. | Runtime replay; в candidate — `NativeConfigReplay`, `NativeArithmeticHistory`, scan/snapshot checks. Они устанавливают исполненный суффикс от исходной machine, не origin этой machine. | Failure semantics §7; FR-014; PO-R2; frozen contract о unknown/incomplete и сохранении исходных записей. |
| **Восстановление verified backup / переданный непустой recovery cut** | Failure contract допускает «recover verified backup» после потери journal; конкретный producer полного backup и отдельный bootstrap authority в этом контракте не определены. Наличие файла или его передачи не назначает отправителя authority. | Требуется verified backup, runtime identity и historical/active epoch. Но отдельный определённый predicate/attestation для полномочий полного backup и его origin не указан. | Исходные durable votes/transitions, finalized certificate history и current; finalized history нельзя удалить или переинтерпретировать. | Обычные replay/ID checks применимы к восстановленным bytes. Полная проверка допустимости imported initial cut **не закреплена отдельным достаточным contract/evidence path**. | Failure matrix «Validator loses durable journal», §7; spec §6 «Finalized history»; PO-R2; candidate Init/verified history clause. |
| **Сертифицированный current checkpoint, в том числе загруженный через P2P/CAS** | Apply validators создают ApplyQC; `CurrentPointerStore` меняет pointer; publisher/downloader переносит разрешённые global artifacts. Это частичное состояние, не producer полного admission snapshot. | Требуются scoped signatures/epoch/quorum и trusted certificate root из replicated state. `ChainVerifier` проверяет configured signer set/context/parents; сам набор signer IDs не доказывает подписи. Peer authentication и content hash не делают peer authority для consensus snapshot. | `ISC → seed → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC`; точные parent/model/optimizer IDs; pointer WAL с прежним parent и возрастающим height. | Certificate verifier и publication policy; current CAS/replay. `NativeCurrentHistory.checkRow` дополнительно связывает pointer record с supplied finalized APPLY snapshot и values. Источник начального pointer и полного certificate snapshot остаётся предпосылкой. | 008 FR-001/002/006/012–015/028/032–040 и formal-refinement graph; 005 FR-004/015 и trusted-root assumption; PO-R1/R2. |
| **Экспорт native witness для formal trace checker** | Контракт требует independently authenticated exporter вне candidate command, но не задаёт producer полного initial snapshot. Реестр witness передаётся отдельно от trace. | Внешний pinned SHA, per-snapshot hash; `ExportTrust.authentic` и anchor/recovery/certificate premises. Hash не является attestation. Конкретная достаточная semantics full-snapshot provenance не определена. | Original prior root, actor/context/contract, exact durable sequence/current, finalized parent, original recovery observations и требуемый prefix. | `NativeEvidence.check`, `PublicSnapshot.load/bindFirst`, native resolver и public journal checks. Они связывают отдельное событие/anchor/bytes; не доказывают source origin всех initial collections. | Refinement contract «Candidate native witness boundary», trust premise и §§4–5; schema `nativeSnapshot`; PO-AB1; FR-037/038. |
| **Synthetic fixtures и loaded formal examples** | `native_trace_fixture.py`, native fixture exporter/`full(action)`, generated full-state/vector fixtures. | Git/hash pin подтверждает версию примера; `syntheticTrust`/пример `exportTrust` используют `True`. Это явно не runtime attestation. | Только явно сконструированный fixture prefix/graph. Удалённые или отсутствующие producer steps не восстанавливаются из hashes. | Fixture/checker/kernel проверяет заявленную конечную область примера; не назначает его production provenance authority. | Candidate contract: synthetic pin не authentication; FR-033; refinement contract прямо отличает fixture registry от exporter. |

Неполный/corrupt/ambiguous scan не является ещё одним разрешённым способом
создать «пустой» или «valid» snapshot. Это existing blocked/incomplete case;
такой ввод не становится authority через повторное хэширование.

Отдельного общего authenticated state-transfer/foreign-snapshot bootstrap
contract в проверенных нормативных источниках нет. 005 разрешает перенос
сертифицированных artifacts; его trusted root **уже** должен приходить из
replicated state. Это не решение начальной authority этой replicated state.

## 3. Проверенные существующие predicates и их точные пределы

Ниже перечислены существующие definitions, не предложения новых predicates.

| Existing source | Что уже есть | Почему недостаточно для полного domain R2 |
|---|---|---|
| `ArithmeticBinding.lean:319`, `NativeBinding.Trust` | `anchorAuthenticated : Anchor → Prop`; `recoveryAuthenticated : Anchor → Prop`; `certificateAuthenticated : Ref → Prop` | Входные abstract premises. В frozen contract не зафиксирована их интерпретация как authority/provenance **всего** initial graph и его permitted prefix. `Binding` дополнительно вычисляет graph/field связи; premises не доказывают origin остальных collections. |
| `PublicSnapshot.lean:74`, `ExportTrust` | `authentic : Anchor → VoteMetadata → Header → Bytes → Prop`; `Exported.provenance` | Удостоверение export задаётся извне. Модуль прямо оставляет full root preimage/full transition открытыми. Добавить сюда условие «весь snapshot production-reachable» было бы новым смыслом, не прочитанным существующим контрактом. |
| `NativeBindingConstruction.lean:17`, `Premises` | Требует `nativeAnchor`, `nativeRecovery`, ISC/EC/APC authentication; `fromRun` получает `auth` отдельно | Computed source/graph closure не порождает эти premises. `noAuthenticationFromClosure` прямо отделяет отсутствие authentication от наличия graph. |
| `NativeAggregateBinding.lean:20`, `CertificateAuthority` | Внешняя relation между original certificate bytes/value и projected artifact | Требует отдельного обоснования certificate/projection authority; не является уже определённым full-snapshot initial/history predicate. |
| `NativeReplay.lean`, `Environment` | `applyAuthenticated`, `scanAuthenticated`, independently resolved inputs | Предпосылки для APPLY и scan. Нет вывода origin всех supplied initial certificate collections; это не full initial-snapshot validator. |
| `NativeReplayAdmission.prepareWhole`; `NativeConfigReplay.recoveryComputed`; `NativeArithmeticHistory.recoveryComputed` | Decode/bind policy/state и исполненная native history от initial machine | Независимость от public representation есть, но начальная policy/state supplied. Успех суффикса не аутентифицирует и не устанавливает protocol origin базы. |
| `formal-trace.schema.json` / `NativeEvidence` | Exact witness fields, independently supplied file digest, canonical IDs и event/context checks | Schema требует authenticated native recovery в description; не определяет issuer/authority semantics и проверку producing prefix полного snapshot. Пин файла не заменяет этот контракт. |

Именованная предпосылка допустима как abstraction. **Отсутствие реализации
криптографии само по себе не было бы основанием этого STOP.** Основание —
отсутствие уже закреплённого достаточного утверждения о полном snapshot и
связи с его исходным prefix. Нельзя домыслить его из названия
`recoveryAuthenticated`, сигнатуры `Prop` или комментария `already-prepared`.

## 4. Evidence paths и область их утверждений

- [Frozen candidate contract](../../specs/000-formal-tla-spec/candidate-contract.md),
  [accepted residual](../../specs/000-formal-tla-spec/accepted-residual-20260928.md),
  [registered baseline inputs](../../formal/reports/baseline-inputs.json):
  именованные assumptions и Init/verified-history requirement присутствуют;
  готового sufficient full-snapshot provenance contract из них не следует.
- [Recovery ordering](../../specs/000-formal-tla-spec/failure-semantics.md),
  [PO-AB1/PO-R2](../../specs/000-formal-tla-spec/proof-obligations.md),
  [refinement boundary](../../specs/000-formal-tla-spec/refinement-contract.md):
  задают уже существующее обязательство, но не полномочия конкретного backup/
  prepared-snapshot producer и не его полную origin-verification relation.
- [Native policy/WAL scope](../../formal/proposals/native-policy-wal.md) и
  [existing evidence](../../formal/proposals/evidence/native-policy-wal.json):
  `PASS_NATIVE_POLICY_WAL_LOCAL_RECOVERY_NOT_FULL_PUBLIC_REFINEMENT`.
  Проверено сохранение full policy identity и local replay в прежних опытах;
  документ явно оставляет trusted initial policy producer открытым.
- [Public snapshot scope](../../formal/proposals/public-snapshot-proof.md) и
  [existing evidence](../../formal/proposals/evidence/public-snapshot.json):
  first-event binding; synthetic exporter/hash adapters, не attestation полного
  initial/recovered state. [Пример](../../formal/proofs/DeltaReduce/PublicSnapshotVectors.lean)
  явно помечает `exportTrust` как synthetic.
- [Computed binding evidence](../../formal/proposals/evidence/native-binding-construction.json):
  conditional binding, `native_export_authenticated: false`.
  [Конструктор](../../formal/proofs/DeltaReduce/NativeBindingConstruction.lean)
  принимает authentication premises отдельно от source computation.
- Native pinned source:
  [startup/recovery](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/runtime.cpp#L113),
  [snapshot writer](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/runtime.cpp#L549),
  [prepared snapshot fields](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-core-cpp/include/delta/core/consensus.hpp#L233),
  [current pointer recovery](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/certificate_runtime.cpp#L111).
  Этот pin относится к прежнему diagnostic, не выдаётся за merged candidate
  или за проверку развернутого demo binary.

Полный перечень прочитанных contract/source/evidence blobs и hashes:
[documentary audit](evidence/0012-snapshot-provenance-source-audit.json).
Это provenance данного **анализа**, не новая attestation snapshot.

## 5. Решение этой контрольной точки

**Существующего независимого predicate, уже достаточного для ограничения
domain R2 по полному initial/recovered snapshot, в проверенном замороженном
контракте нет. `MISSING SNAPSHOT PROVENANCE CONTRACT`.**

Это не доказательство необходимости A/B/C и не новая производственная
уязвимость. Исходный API-контрпример по-прежнему не объявляется допустимой
production history. Нужное решение относится к смыслу исходной authority и
границе доверия; этот аудит его не принимает и не формулирует вместо пользователя.

Никакие requirements, predicates, schemas, proofs, fixtures, protocol semantics
или runtime/guard не изменены. Новых native/TLC/Lean прогонов нет. R2.3 не
продолжается автоматически; R3 не начинается. STOP сохраняется до отдельного
решения пользователя о контракте/архитектуре.
