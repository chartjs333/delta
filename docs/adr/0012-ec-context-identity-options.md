# ADR-0012 — EC context / QC identity: варианты и достижимость

**Статус:** ANALYSIS COMPLETE / DECISION NOT SELECTED / IMPLEMENTATION STOP.
**Дата:** 29 сентября 2026. **Тип работы:** чтение исходников и документация;
код, TLA, Lean, schemas, fixtures и результаты прежних запусков не изменены.
**База formal candidate:** `957323cd18b18e6b7dd29fcc6d08b14ea8b44b21`.
**Native revision прежнего опыта:** `60c692f6e391f839829dfc64e93380db54cd507b`.

R1, R2.1 и R2.2 остаются CLOSED. R2.3/R2 OPEN; R3 не начат. Замороженные
DoD R1–R7 и три области residual R2.3 не меняются. Этот ADR не разрешает
реализацию, не выбирает исправление и не является Formal GO.

## 1. Вывод reachability analysis

**Прежняя цепочка `ISC@1 → EC@2 → EC@3` воспроизведена на отдельных admission
вызовах и одном in-memory VoteJournal. Она не является достижимой цепочкой
одного production Runtime/WAL на проверенном native revision.** Для неё
использованы разные исходные состояния/policies ISC и EC. Существующий Runtime
не предоставляет соответствующего переключения authority с сохранением WAL.

Это уточнение существенно: опыт доказывает несовместимость *всего принимаемого
API snapshot/journal domain* с нынешней public projection, но **не доказывает
нарушение safety в достижимой production protocol history**. Необходимость
изменения production semantics из этого опыта пока не следует.

| Уровень утверждения | Результат и граница |
|---|---|
| Исходные admission-функции + `VoteJournal::record` | **Воспроизведено ранее:** обе EC записи принимаются. Проверены bytes/IDs и original sequences; физический WAL не исполнялся. |
| Та же полная цепочка через один `Runtime`, тот же WAL, обычные production actions | **Исключена проверенным control flow:** фазовые guards, immutable policy, invalidation после transition и проверка policy identity при replay. Ниже приведены конкретные predicates. Это анализ исходников, не новая Lean/TLC теорема. |
| Две EC записи из извне переданного готового `ELIGIBLE` snapshot | **Отдельный API-путь не исключён:** OPEN принимает supplied state/policy, а `record_vote` использует те же admission/journal checks. Но для пустого WAL потребовались бы sequences 1/2, другие vote bytes/IDs; это не исходная цепочка 1/2/3. Такой Runtime-запуск здесь не выполнялся. |
| Получение спорного snapshot из genesis через protocol finalization/network actions | **Не установлено.** В production TLA второй signer-вариант не добавляется повторным `FinalizeISC`; native OPEN получает snapshot извне. Доказанного producer-пути для спорной пары QCs нет. Само наличие API OPEN не доказывает её protocol reachability. |

Указанный native pin не является предком ни formal candidate, ни замороженного
demo baseline `c8aea64972f741060d1e527ebbb6f9a5a168a075` (`git merge-base
--is-ancestor` вернул 1 в обоих случаях). Здесь исследован production-path код
**на revision опыта**, а не заявлена проверка развернутого demo binary или
слитая formal authority. Демонстрация не запускалась и не менялась.

### Проверенная цепочка вызовов и места, где она обрывается

Все native ссылки ниже закреплены на `60c692f6e391f839829dfc64e93380db54cd507b`.

1. [C ABI `delta_runtime_open_with_vote_policy_v1`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-ffi/src/delta_abi.cpp#L399)
   получает `initial_state` и encoded policy от вызывающего кода. Аналогично
   [sidecar `handle_open`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/sidecar_server.cpp#L661)
   передаёт их в `Runtime::Config`. Это загрузка authority, не действие
   получения ISC/EC из доставленных votes. `CertificateVoteRuntime` также
   только принимает initial state/policy и делегирует `record_vote`.
2. [`Runtime::Impl` и `vote_policy_identity`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/runtime.cpp#L113)
   проверяют policy против initial state и фиксируют hash её полного encoding.
   Интерфейс Runtime содержит submit/record_vote/snapshot/close; операции
   refresh/replace policy нет.
3. [`phase_allows`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-core-cpp/src/certificates/vote_admission.cpp#L198)
   допускает ISC (`input_set`) только при `available`, EC (`eligibility`)
   только при `eligible`. Запись vote сама фазу не меняет. Один immutable
   initial state не разрешает обе части опыта последовательно.
4. [`FINALIZE_INPUT_FREEZE`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-core-cpp/src/transition.cpp#L84)
   переводит available в eligible. Но любой успешно committed submit в
   [`process_submit`](https://github.com/chartjs333/delta/blob/60c692f6e391f839829dfc64e93380db54cd507b/delta-runtime-cpp/src/runtime.cpp#L421)
   устанавливает `vote_authority_invalidated_ = true`. Последующий
   `validate_vote_admission` требует `!admission_state.authority_invalidated`.
   Кроме того, transition занимает собственную WAL sequence: сохранить
   исходные физические 1/2/3 вставкой этого перехода нельзя.
5. Перезапуск с прежней policy повторяет invalidation при replay transition
   (`runtime.cpp:274–277`). Подмена policy на EC policy отвергается на прежней
   vote-записи: `entry.wal_record_bytes == vote_policy_identity_`
   (`runtime.cpp:289–292`). Admission при recovery снова проверяет фазу и
   invalidation (`runtime.cpp:301–308`). Snapshot сверяется с полным replay,
   не заменяет его (`runtime.cpp:325–334`). Новый пустой WAL не сохраняет
   исходную историю/identity и не является обходом этих ограничений.
6. В [production TLA](../../formal/tla/DeltaReduceCertificates.tla)
   `CertificateInit` начинает с пустого `inputSetCertificates`;
   `FinalizeISC` (187) требует `FinalizedISCBodiesFor(body.round) = {}`.
   Повторный вызов не добавляет новый signer subset для того же body.
   `ReplayMessage` (635) изменяет receipts и сохраняет certificates.
   `GenerateSeed` (233) допускает один seed на ISC body; `VoteEC` (337)
   отдельно запрещает конфликтующий body и повтор уже существующей записи.
   Загрузка произвольного состояния в diagnostic harness не входит в
   production `DeltaReduce.Init/Next` и не даёт недостающей достижимости.

Исходники и raw hashes для этого чтения перечислены в
[source audit](evidence/0012-ec-context-source-audit.json). Новые native runs,
TLC, Lean builds или доказательства recovery здесь **не выполнялись**.

## 2. Что именно различается и что требует исходный контракт

Пусть `B` — одно исходное ISC vote body, `Q1=(B,{1,2,3})`,
`Q2=(B,{1,2,4})`, threshold 3. Все четыре прежних ISC vote голосуют за `B`.
Native canonical ISC encoding включает `signer_ids`, поэтому `id(Q1) ≠ id(Q2)`.
EC `vote_context_id` использует исходный parent QC ID. Связанные seed/norm/EC
artifacts в опыте переподчинены каждому точному QC, не изменяя их числовые
значения. Получаются два разных native EC context и два fresh vote одного actor.
Опыт использует synthetic fixture/signature assumptions существующей formal
границы; он не выполняет криптографическое подписание или network finalization.

Public `EcBody.vote` использует `IscBody.value` как context. Эта value
вычисляется по ISC **body**, без QC signer discriminator. Два разных projected
EC body нарушают `CertificateVoteUniqueness`; два равных body сливаются в
public set, теряя multiplicity и `DurableSequenceExact`. Смена aliases,
удаление записи или присвоение новой sequence не являются исправлением.

Исходный контракт содержит **обе** стороны, и их нельзя подменить друг другом:

- [ADR-0001](0001-deltareduce-v1.md), пункт 6, и
  [EC wire schema](../../delta-protocol/schemas/008/eligibility-certificate-v1.json)
  требуют explicit parent certificate, включая `input_set_certificate_id`.
  Сертификат с другим набором signers не имеет прежнего content ID.
- [PO-Q1/PO-Q2](../../specs/000-formal-tla-spec/proof-obligations.md) и
  `CertificateVoteUniqueness`/`CertificateQCUniqueness` требуют уникальность
  решения в его логическом контексте. В текущей public модели EC-контекст —
  ISC body, а не произвольно выбранный signer-вариант QC.
- [Refinement contract, §§3–5](../../specs/000-formal-tla-spec/refinement-contract.md)
  запрещает скрывать protocol-visible parents/votes и invariant violation,
  требует исходные durable records и допускает retry только без второго события.
- [Принятый candidate contract](../../specs/000-formal-tla-spec/candidate-contract.md)
  уже требует для initial snapshot существующий `Init` либо проверенную
  reachable-history relation. Отсечение произвольного injected snapshot
  **выведенным** source predicate не расширяет DoD. Просто предположить его
  эквивалентность полному public state запрещено. Этот predicate для всей
  требуемой области здесь не построен, поэтому R2.3 не закрывается.

Следовательно, после анализа **не доказано**, что все три варианта обязательно
нужны или что один из них уже необходимо реализовать. Сначала решение должно
явно определить: сохраняем ли нынешний протокольный domain, или намеренно
расширяем его на дополнительные admission-accepted snapshots. Сам ADR не
меняет domain и не вводит новую обязанность.

## 3. Сравнение вариантов

Под identity ниже различаются (а) исходные canonical bytes/content IDs и
физические WAL sequences, (б) логический ключ запрета повторного решения.
Инъективность требуется для сохраняемых исходных protocol objects и records
в **совместной** relation; необязательно для одной scalar `πₖ` в отрыве от
общего source witness. Signer не умножается на число координат.

| Критерий | A — обогатить public EC context | B — ужесточить native admission | C — изменить public uniqueness/context semantics |
|---|---|---|---|
| Минимальный смысл | Хранить исходные parent QC ID, native context, body ID и source/signers binding рядом с логическим ISC body. Не превращать QC ID в новое право голосовать. | Проверять fresh EC по исходному логическому ISC-body context, даже когда parent QC IDs различны; exact retry остаётся retry. | Сделать parent QC ID самостоятельным логическим EC-контекстом и разрешить отдельное голосование для Q1/Q2. |
| Исходный протокольный контракт | **Совместим условно:** дополнительные identity-поля сохраняют wire parent и прежний запрет разных решений. Обогащение само по себе не разрешает исходный API witness. | **Совместим с нынешней public safety-семантикой.** Нужно показать, что ограничение не исключает допустимую protocol history; этого не доказывает один контрпример. | **Не сохраняет нынешнее EC body-scoped safety-утверждение.** Требует явного изменения формального контракта; сейчас это не разрешено замороженным DoD. |
| Допустимые native histories | Production native acceptance не меняется. Полная relation остаётся только для source-qualified domain; произвольный API domain A в консервативной форме не покрывает. | API-accepted histories с повторным fresh EC для одного логического контекста сужаются. Сохранение всех ранее protocol-legal histories подлежит проверке. | Native API acceptance может остаться прежним; множество **public legal histories** расширяется. Для генерации двух QCs в модели нужны также согласованные finalization actions. |
| Certificate/QC/WAL identity | Native bytes, QC IDs, vote IDs, WAL identity и sequences сохраняются. Public witness/state encoding меняется. | Можно сохранить все wire encodings и IDs принятого подмножества: добавить admission guard/index, не менять `vote_context_id`. Меняется разрешённость нового append. Замена hashed context вместо дополнительного guard — уже другой, более дорогой вариант. | Wire bytes/IDs могут сохраниться, но **семантика context и certificate acceptance меняется**. Перенос новых полей в native wire дополнительно изменил бы IDs и здесь не предлагается. |
| Sequences / journal multiplicity | Сохраняются в общем original record carrier. Нельзя считать каждый tag новой протокольной записью или разрешением продублировать vote. Весь прежний спорный журнал с неизменными public guards всё ещё не представим. | У принятой истории ничего не удаляется и не перенумеровывается. Старый спорный журнал нельзя «починить» выкидыванием второй записи: он потребует явного reject/legacy handling. Тождественное восстановление всех старых API-журналов не обещается. | Для расширенной модели можно сохранить обе исходные записи и sequences, если tag присутствует и в vote record, и в durable envelope, и в certificate lineage. Изменение только одного invariant не сохраняет multiplicity. |
| Инъективная refinement relation | **Можно сформулировать** на допустимых histories через original object tags + checked decoding; отдельно нужен прежний logical uniqueness predicate. Нельзя получить total relation для спорного API witness простым добавлением поля. | **Можно сформулировать** на суженном domain с сохранёнными original IDs/artifacts в shared source. Один прежний public body без shared QC witness по-прежнему не инъективен по signer-вариантам. | **Можно сформулировать** identity-preserving relation к новой tagged модели. Это не доказывает прежний safety contract: корректность новой uniqueness/lineage ещё потребуется установить. |
| Production `Init/Next` | Native actions можно сохранить. Если tags только в refinement carrier, production TLA `Init/Next` тоже прежние; включение tags в public protocol state требует переноса shapes/actions и доказательства консервативного забывания tags. | Production TLA `Init/Next` прежние. Native admission predicate меняется; это возврат в feature000/formal gate, а не разрешение менять runtime сейчас. | Изменяются public TLA guards/actions, а значит отношение `Next`, даже если текст верхнего `Next` остаётся тем же. Native Init/Next может не измениться. |

**Граница A/C:** если в A заменить `HasConflictingECVote` и
`CertificateVoteUniqueness` так, чтобы Q1/Q2 позволяли разные решения за один
ISC body, это вариант C, а не «только более точное представление».
Добавить QC ID лишь в `VoteEnvelope` недостаточно: `ECVoteRecord` пока содержит
только `[validator,body]`, и `vote ∉ ecVotes` продолжит схлопывать повтор.

Почему C затрагивает safety: если honest validators 1 и 2 вправе подписать
EC1 под Q1 и другой EC2 под Q2, то EC quorums {1,2,3} и {1,2,4} могут иметь
honest intersection, не нарушая новой *QC-scoped* дисциплины. Из неё уже нельзя
вывести прежний запрет двух EC bodies на один ISC body. Чтобы оба сертификата
финализировались, пришлось бы ослабить и нынешний `FinalizeEC`; если сохранить
его guard, одно изменение vote uniqueness всё ещё не даёт заявленной полной
relation. Это условный логический пример для оценки C, не новый native run.

**Граница B:** проверять только один текущий snapshot недостаточно для обещания
о прежнем журнале. Guard должен опираться на исходные body/context и уже
сохранённые записи; как получать их из существующих bytes/artifacts, должно
быть определено до реализации. Это следствие уже существующего persist/replay
контракта, не новый слой R2 и не начало R3. Выбор одного QC по порядку прихода
или удаление его альтернатив не предполагаются допустимыми.

## 4. Точные точки воздействия и повторная квалификация

`PROOF REUSE` означает прежнюю теорему при прежних premises; `INVALIDATED`
ниже означает невозможность использовать прежний результат **для изменённого
утверждения/source revision**, а не ошибку Lean kernel или отмену исторического
отчёта. **Сейчас, от одного ADR, ничего не инвалидировано.**

### TLA actions / invariants

| Существующий контракт | A | B | C |
|---|---|---|---|
| `DeltaReduceTypes`: `ECVoteRecords`, `VoteEnvelope`, `EligibilityBodies`; `DeltaReduceCertificates`: `ECVoteRecord`, `VoteEC`; `DeltaReducePublicState`: public state encoding | `MODIFICATION`, если tag входит в модель; `UNCHANGED`, если он лишь в refinement carrier | `UNCHANGED` | `MODIFICATION`: context tag должен проходить через полные records/lineage |
| `HasConflictingECVote`, `CertificateVoteUniqueness`, `FinalizedECBodiesFor`, `FinalizeEC`, `CertificateQCUniqueness` | Логическое утверждение `UNCHANGED`; перенос на tagged shape и old-state projection требует квалификации | `UNCHANGED`; новый native guard должен его обеспечивать | Старое body-scoped применение `INVALIDATED`; predicates/actions `MODIFICATION` |
| `FinalizeISC`, `GenerateSeed`, `ValidECParent`, `ValidEligibilityBody`, `VoteAPC`, `FinalizeAPC`, `ReplayMessage` | `PROOF REUSE` для logical layer; source/tag correspondence `MODIFICATION` | TLA `UNCHANGED`; повторный source/refinement check | `MODIFICATION` там, где QC variants должны стать отдельными parents/событиями. Одной замены `CertificateVoteUniqueness` недостаточно |
| `DeltaReduceQuorums`: `CanPersistVoteEnvelope`, `PersistVoteEnvelopeChanges`, send/delivery keys; `DeltaReduceFailures`: `DurableSequenceExact`, `AllQCVotesPersisted`; `DeltaReduceCertificates`: `ValidCertificateQuorums`, `ISCImmutability`, `SeedAfterInputFreeze`, `CertificateReplayIdempotence` | Definitions/instantiations с tagged records адаптируются; multiplicity и erasure требуют повторной проверки | Формальные утверждения `UNCHANGED`; native correspondence по admission/replay повторно квалифицируется | Старое применение к прежним contexts `INVALIDATED`; нужно заново проверить полноту counts, delivered signer sets, uniqueness и replay |
| `DeltaReduceReduceApply` и `DeltaReduceFailures`: downstream APC→PARAMETER→ROOT→APPLY/current/ABORT ancestry; верхние `DeltaReduce.Init/Next` | Численные guards прежние; affected parent/tag bindings переносимы | `UNCHANGED` как модель, новые source bindings | Перепроверить следствия изменённых parent contexts для прежних safety obligations; current/ABORT lineage нельзя стереть |

В A/C повторная квалификация затрагивает зарегистрированные certificate,
vote-lifecycle, public-state, persistence/recovery и downstream конфигурации
из `formal/tla/cfg/config-manifest.json`, а также относящиеся к ним production
mutants. Старые finite TLC результаты не становятся доказательством новой
модели. В B неизменные TLC semantics/results сохраняются; native-source и
refinement qualification обновляются, согласно существующему gate.

### Lean definitions / proofs

| Существующий артефакт | Что меняется или сохраняется |
|---|---|
| `Quorum.lean`: `quorumIntersection`, `quorumIntersectionContainsHonest`, `conflictingQCImpossible` | A/B/C: **PROOF REUSE** самих теорем. В C прежняя EC-instantiation последней не переносится: её premise «один honest durable vote в одном context» больше не относится к общему ISC-body context. |
| `PublicAuthority.lean`: `iscValue`, `ecValue`; `PublicPlanningBody.lean`: `IscBody.value`, `EcBody.value`, `EcBody.vote`, `loadEcBody`, `ecParentShape`, `nativeParentsRetained`, `checkedWholeVote` | A/C: **MODIFICATION** identity/context boundary либо отдельного carrier join. B: body constructors **PROOF REUSE**; общая relation должна связать дополнительный native logical-context guard. |
| `PublicPlanningHistory.lean`: `check`, `exactNativeSource`, `exactOriginalBytes`, `completePublicVote`; `PublicJournal.lean`: `Envelope.key`, `Envelope.encode`, `Slot`, `Environment` | Original-byte assertions сохраняют смысл. A/C меняют public-image/context join; B требует повторной source qualification admission, без переписывания исходных bytes/keys. |
| `NativeCandidateAuthority.lean`: `Ec`, `check`, `ecWitness`, `ecOriginalBody`, `bindPolicy`; `NativeSnapshotBase.lean`: `checkBase`, `bindSnapshot`, `preparedSource`; `NativeVoteCache.lean`: `capture`, `ordinaryOriginalAuthority` | A/C native source predicates прежние, новые projected-context joins. B: новые admission/source assumptions нельзя считать уже доказанными этими helpers; affected bindings — **MODIFICATION**, прежние decoding/parent lemmas — **PROOF REUSE**. |
| `PublicVoteEffects`, `PublicStateValues/Loads/Documents`; `PublicRecovery`: `otherVote`, `restore`, `recover`; `PublicReachability`: `otherVotePreservesInvariant`, `reachableJournalHistory`, `reachableSlotProvenance` | A/C: affected structured-public instantiations/serialization перепроверяются; generic ordered-slot/persistence lemmas **PROOF REUSE** при прежних premises. B: pure lemmas прежние, changed native admission/replay instantiation не квалифицирована автоматически. Это перечень зависимости; работы R3 здесь не ведутся. |
| `formal/proposals/b-family-transfer/FamilyRelation.lean`: `loadCertificateParents`, `CertificateParents.isc/ec/apc`, `loadObservedState`, `loadCertificateBasis`, `loadSufficientAbort`, `loadAbortStateLink` | A/B/C: affected full-state/context/source join — **MODIFICATION**. Сохранение original PARAMETER/ROOT lists и nonempty ABORT lineage остаётся обязательным; не вводится новый full-ABORT gate. |
| Арифметика, native widths, family πₖ, ordered reconstruction, `FixedPoint`, `Hierarchy`, `ParameterKernel`, `ApplyKernel`, численные части constructors | **PROOF REUSE** во всех вариантах. Ни одного численного контрпримера не найдено. R2.1/R2.2 не открываются заново; изменение типов parent bindings не отменяет их численные результаты. |

### Schemas, checkers и existing evidence

- **A/C:** пересмотреть public shapes/keys в `formal/scripts/public_state_projection.py`,
  `public_native_projection.py`, `check_public_state_replay.py` и генераторах
  `generate_public_state_lean.py`, `generate_public_state_vectors.py`,
  `generate_public_vote_effects.py`, `generate_public_journal_vectors.py`,
  `generate_public_recovery_vectors.py`. Их соответствующие full-state/snapshot,
  journal, planning-body и recovery fixture families — **MODIFICATION + RE-RUN**.
  Внешняя обёртка `formal/schemas/formal-trace.schema.json` может остаться
  прежней, если новое поле находится только внутри existing witness value;
  это не освобождает semantic checker от проверки поля.
- **B:** native `validate_typed_snapshot` / `validate_policy_impl` /
  `validate_vote_admission` и его journal-facing guard должны быть согласованы;
  точное размещение guard пока не выбрано. `native_admission_snapshot.py`,
  `generate_native_admission_vectors.py` и затронутые native admission/replay
  fixtures — **MODIFICATION + RE-RUN**. Wire schema, vote codec и hash
  constructors могут быть **UNCHANGED** при дополнительном guard, а их
  source qualification — **RE-RUN ONLY**. Старые positive cases, если новый
  guard их запрещает, будут **INVALIDATED как положительные для новой версии**.
- При сохранении wire format schemas
  `delta-protocol/schemas/008/input-set-certificate-v1.json` и
  `eligibility-certificate-v1.json` не нужно менять ради нового logical index.
  Изменить их semantic acceptance или `formal_semantics_id` — отдельное
  compatibility последствие выбранного решения; ничего не обновляется сейчас.
- Точные затронутые evidence roots: `formal/proposals/evidence/`
  `public-planning-body.json`, `public-authority.json`, `public-state.json`,
  `public-state-lean.json`, `public-snapshot.json`, `public-journal.json`,
  `public-recovery.json`, `public-reachability.json`, `native-candidate-authority.json`,
  `native-snapshot-base.json`, `native-admission-snapshot.json`,
  `native-eligibility.json`, `native-isc-admission.json`,
  `native-config-replay.json`, `native-mixed-replay.json`, `native-whole-replay.json`
  и `b-family-constructors.json`. Переносить их PASS на изменённые source hashes
  нельзя. Самые общие прежние теоремы сохраняются; affected instantiations
  обновляются после выбора, без автоматического запуска R3.
- `r2-qc-context/counterexample.json` остаётся неизменным историческим
  **admission/in-memory** результатом на старом pin. B изменит ожидаемый outcome
  нового опыта; A/C изменят его public interpretation. В этом ADR уточняется
  только reachability-вывод, не переписываются прежние raw результаты.
- Нынешний NO_GO report не превращается в GO ни при одном выборе. Любой
  semantic/source-impact требует прежней exact-source gate qualification;
  математическая истинность старой теоремы и совместимость отчёта с новым
  исходником — разные утверждения.

## 5. Оценка стоимости и решение, которое пока не принято

Это грубая оценка **активных инженерных часов на данный EC mismatch и его
затронутую локальную qualification**, после выбора точного варианта. Доверие
низкое: реализации не было. Не включены полное закрытие остальных частей
R2.3, общий R3, R4–R7, независимое ревью, ожидание внешнего решения или полный
Formal GO. Перенос прежних часов на эти оценки не даёт обещания срока.

| Вариант | Representation / guard и source binding | Затронутые proofs / fixtures / qualification | Всего и ограничение |
|---|---:|---:|---|
| A, консервативное identity enrichment | 6–12 ч | 10–20 ч | **16–32 ч**. Не включает превращение спорного API witness в допустимую history: без прежнего logical predicate это уже C. |
| B, дополнительный logical-context guard без rehash | 8–16 ч | 16–32 ч | **24–48 ч**. При условии восстановления нужного original body из имеющихся artifacts и явно определённой обработки старого журнала. Если это не так, оценка пересматривается до реализации. |
| C, новые QC-scoped public semantics | 16–32 ч | 32–64 ч | **48–96 ч**, предварительно. Не обещает существования безопасной новой semantics: потеря body-scoped uniqueness может потребовать отказа от C, а не ещё одного локального патча. |

**Рекомендация:** не выбирать C только ради прохождения контрпримера.
Если сохраняем нынешний safety contract и хотим ограничить именно весь
native API domain, B — наиболее прямой вариант; identity carrier из A может
сохранять provenance, но не заменяет logical guard. При этом анализ не доказал,
что production fix вообще обязателен для исходного source-qualified R2:
проверяемая допустимость initial snapshot уже входит в замороженный residual.
Её нельзя ни предположить целиком, ни заменять новым требованием.

**Контрольная точка:** R2.3 OPEN; прежняя API/domain obstruction сохранена,
но production-reachable safety counterexample **не установлен**, а точная
составная цепочка 1/2/3 исключена проверенным Runtime control flow. R2.1/R2.2
CLOSED. Решение A/B/C не выбрано; исправление и новые proof layers не начаты.
STOP сохраняется. Для дальнейшей реализации требуется отдельная прямая команда.
