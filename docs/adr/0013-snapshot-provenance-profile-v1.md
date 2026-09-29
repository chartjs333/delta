# Snapshot Provenance Profile v1 — Linux, один epoch, один native owner

29 сентября 2026. T000/T047/T053. **PROFILE_PROPOSED — documentation only.**

[ADR-0013](0013-snapshot-provenance-contract-v1.md) концептуально принят как
production trust model. Этот документ выбирает одну конкретную конфигурацию,
а не набор альтернатив. Утверждение production implementation отсутствует.
Source base: `6faf85d1fa4855e7b4331b9460f3817db4affeca`; PR50 policy/WAL source
по-прежнему отдельно pinned на `60c692f6e391f839829dfc64e93380db54cd507b`.

## 1. Единственная выбранная конфигурация

- Linux, local ext4, native sidecar и один consensus reactor. Storage обязан
  честно исполнять durability barriers; NFS, shared writers и VM disk snapshots
  для trusted storage не входят в этот профиль.
- Один заранее enrolled validator в фиксированном epoch из четырёх validators:
  `3f+1=4`, `f=1`, `quorum_threshold=3`. Exact IDs/keys/roles берутся из
  independently provisioned epoch file. Cross-epoch import, membership changes
  и автоматический key rotation отсутствуют: другой epoch даёт отказ.
- **Fresh node здесь — новый runtime/host с пустым рабочим диском, который
  восстанавливает уже enrolled identity.** Независимый trust носитель приходит
  извне и сохраняет её собственную историю. Это не создание нового protocol
  validator и не разрешение начать старую identity с пустым vote journal.
- Два отдельных физических тома: `D=/srv/delta-data` для snapshot/staging и
  `T=/srv/delta-trust` для independent bootstrap, trusted floor и **исходных
  собственных consensus WAL, pointer WAL и vote journal**. T не восстанавливается
  из snapshot/backup D. Runtime остаётся единственным владельцем этих journals.
- Cold handover: предыдущий процесс этой identity остановлен; T и signing key
  переданы единственному новому owner. Параллельный старый signer не допускается.
  Physical custody и trusted host/root — assumptions deployment, не вывод из QC.
- Bootstrap восстанавливает **exact independently known checkpoint F**, не
  любой checkpoint с большим height. Snapshot current должен равняться F;
  WAL continuation заканчивается в известном собственном durable tip L,
  чей current также равен F. Newer checkpoint требует отдельно обновлённого
  independent anchor; импортёр не выбирает freshness по пакету.
- Нет chain of imported snapshots. Для full-state binding используется один
  конечный source bundle от закреплённого genesis до cut/tip, с исходными
  native events, body/config/artifact preimages и certificate lineage.

Таким образом, после provisioning не требуется ещё один trust server, новый QC
или interactive ответ peer. Подлинные keys, checkpoint F, source bundle и
approved verifier/build/formal pins являются конкретными deployment inputs;
фальшивые production значения в этом draft не подставляются.

**Threat boundary:** недоверенный пакет/peer может подменять и откатывать D;
возможны crashes, incomplete/corrupt bytes и до f Byzantine validators.
Он не может переписать/откатить T, trusted bootstrap media, исполняемый verifier
или signing key custody. Отдельный том сам по себе не защищает от root/firmware
attacker или отката обоих томов; такие события вне гарантии этого профиля.
Потеря T означает BLOCKED, не переинициализацию старой identity.

## 2. Пять выбранных механизмов

| Механизм | Threat | Authority | Persisted object | Verification | Fail closed |
|---|---|---|---|---|---|
| Bootstrap validator/epoch | Self-issued epoch, чужой signer, старый bootstrap под видом свежего | Offline provisioning от владельца permissioned deployment; независимо известный digest bootstrap file и custody T | Read-only `bootstrap.json` на T: origin/genesis/config pins, epoch registry, approved code/codec/formal pins, enrolled local identity, первоначальный F | До открытия candidate проверить provisioned digest, exact epoch/4 members/threshold3/roles/key refs и сохранённый trusted log; imported registry только сравнивается | Missing/mismatched root, unsupported epoch, неизвестный key/role или потерянный T: ни voting, ни READY |
| Full snapshot/history binding | Consistent hashes с fabricated initial collections, лишний EC/QC, уничтоженная lineage | Valid existing ApplyQC + independently observed raw source/journal bytes + проверка native producing rules от pinned genesis | Original source bundle/index на T; untrusted import manifest и referenced complete snapshot на D; immutable artifact refs | Вывести state/collections из конечного original prefix, сравнить все bytes/fields с candidate; отдельно проверить exact original cert/signature graph | Unsupported producer event, gap, wrong inventory или missing origin: отказ; не очистка collections и не предположение R2 |
| Trusted rollback floor | Старый валидный QC и snapshot после восстановления D | Последний durable independently retained anchor в T | Append-only `trust.log`, latest verified F и собственные исходные journals; начало связано с bootstrap digest | Проверить непрерывный trusted log, exact F tuple/QC, then candidate equality с F и authoritative local tips | Older/newer-unpinned/fork/unknown floor: отказ; нет fallback к bootstrap F0 при существующем более новом F |
| Atomic activation | Crash между записью snapshot, floor и публикацией current; stale generation | Single native writer + T commit record после durability D | Immutable generation на D, затем один `ACTIVATE` record на T, связывающий F, generation/manifest hashes и journal cuts | Сначала durable generation, затем durable T commit; на restart выбрать только последний complete consistent T commit и заново проверить referenced bytes | Missing generation после T commit, повреждённый T tail или несовпадение cuts: RECOVERING/BLOCKED; не предыдущий current |
| Canonical provenance encoding | Разные parser interpretations, числа с потерей точности, неоднозначный hash | Fixed profile/schema и existing hash/canonical primitives, pinned до пакета | Одна schema family: bootstrap, manifest, source-index, trusted-log record; original protocol objects хранятся byte-for-byte | Exact ASCII JSON subset, closed fields, ordered arrays, exact decimal strings, domain-separated IDs, decode/re-encode equality | Duplicate/unknown fields, noncanonical bytes, unsupported version, bounds overflow или trailing bytes: отказ |

Offline provisioning здесь удостоверяет **ключи, primitive origin/config pins и
faithful observation конкретных исходных bytes**. Оно не удостоверяет public
projection или законность произвольного prepared snapshot. Последнее проверяет
native producing-history verifier. Operator не может заменить ApplyQC подписью
bootstrap file или выставить current без трёх действительных apply signatures.

T содержит own journal continuity, в том числе unpublished/durable-but-unexposed
vote intent. Remote signed messages/certificates остаются исходными objects;
импорт не копирует чужие private vote journals под local signer. Участники не
обязаны отвечать во время bootstrap или раскрывать remote private WAL:
проверяется уже предоставленный complete **required source bundle**, а hidden
remote votes не объявляются отсутствующими. All-actor scope frozen R3 этим
одним deployment instance не уменьшается.

## 3. Concrete objects и encoding

Это field specification, **не созданные schemas или structures**. Existing
ApplyQC, ApplyCandidate, generic Vote/QC, certificate bodies, `RoundState`,
`PointerState`, `JournalEntry`, `WalRecord`, policy bytes и effect IDs берутся
в исходном encoding; полный inventory существующих полей есть в ADR-0013 §2.

Все новые control documents содержат `type_name`, `schema_version="1"`,
`profile_id="snapshot-provenance-linux-single-epoch-v1"`.

| Document | Обязательные содержательные поля |
|---|---|
| `bootstrap.json` | `origin_id`, `genesis_ref`, `initial_config_ref`, `validator_epoch_id`, `validators` (ordered `{validator_id,key_ref,roles}`), `quorum_threshold`, `local_validator_id`, `runtime_build_id`, `formal_semantics_id`, `schema_set_id`, `signature_codec_id`, `producer_rules_id`, `initial_anchor` |
| Import manifest | `origin_id`, `validator_epoch_id`, `local_validator_id`, `bootstrap_id`, `formal_semantics_id`, `schema_set_id`, `anchor`, `apply_qc_ref`, `apply_candidate_ref`, `snapshot_ref`, `source_index_ref`, `cut_event_index`, `target_event_index`, `journals`, `artifacts` |
| Source index | `origin_id`, `validator_epoch_id`, `local_validator_id`, `genesis_ref`, `events`, `artifacts`, `original_journal_refs` |
| Trusted-log record | `ordinal`, `previous_record_id`, `bootstrap_id`, `kind`, `anchor`, `journal_cuts`; для `ACTIVATE`/`ANCHOR` также `generation_id`, `manifest_id` |

`INIT` — только первый trusted record, ordinal `"0"`, previous_record_id
`"GENESIS"`, anchor равен independently provisioned initial anchor. Он не
активирует generation. Последующие `ACTIVATE`/`ANCHOR` ссылаются на exact ID
предыдущего record; `ANCHOR` сохраняет текущую generation и меняет только
проверенный anchor/cuts. У каждого kind закрытый набор полей; неизвестный kind
или повторный INIT отвергается. Initial anchor также требует valid ApplyQC,
его наличие в provisioning не освобождает шаг 3 от certificate verification.

`anchor` переиспользует exact `PointerState`
`{height,checkpoint_id,optimizer_id,apply_qc_id}` и фиксированный epoch/origin
из envelope. `journal_cuts`/`journals` содержат existing actor/journal identity,
byte count/hash и original first/last sequence для cut и target tip. Пустой
журнал имеет явный `entry_count="0"` и length/hash пустых bytes; отсутствующий
или неизвестный журнал не кодируется пустым. Native WAL sequence, vote sequence,
pointer-record position и `trust.log.ordinal` — разные пространства.

Artifact refs используют existing content/schema/media/length concepts. В новых
control documents `byte_length` — decimal string; это **profile descriptor**,
не молчаливое изменение старой artifact-ref schema. Source index — referenced
document в том же closed encoding: ordered events и table original
artifact refs. Event имеет original actor/action label, original event/record
ref, exact input refs и backward dependency indices. Это индекс исходных
objects, не создание новых protocol identities или public trace как authority.

Выбранное encoding:

- UTF-8 bytes, но строки ограничены existing certificate ASCII subset
  (`0x20..0x7e`, без quote/backslash); keys — фиксированные schema names,
  строго возрастают по ASCII. No BOM, whitespace или trailing newline.
- Allowed values: strings, booleans, arrays, objects. JSON numbers и `null`
  отсутствуют. U64/length/height/count поля — строки `0` либо `[1-9][0-9]*`
  в границах существующего типа; не float и не scientific notation.
- Arrays сохраняют заданный смысл: validator/artifact tables sorted unique,
  events и journal records строго в исходном порядке. Signer lists/certificate
  bytes не пересортировываются для изменения оригинального QC ID.
- Unknown/duplicate/missing field — ошибка. Прочитанные bytes должны совпасть
  с canonical re-encoding. Version/schema не выбираются imported content.
- New document ID: `sha256:` плюс lowercase SHA-256 от
  `ASCII(domain) || 0x00 || canonical_document_bytes`, как existing certificate
  `id_for`. Domains: `deltareduce.snapshot-provenance.bootstrap.v1`,
  `deltareduce.snapshot-provenance.manifest.v1`,
  `deltareduce.snapshot-provenance.source-index.v1`,
  `deltareduce.snapshot-provenance.trust-record.v1`.
  IDs не включаются рекурсивно в собственный preimage.
- New `trust.log` framing: u32 big-endian payload length, exact canonical record
  bytes, 32 raw digest bytes. Это local metadata log, не изменение формата или
  identities существующего consensus WAL. Любой incomplete/corrupt trusted-log
  frame блокирует automatic startup; он не обрезается до более старого floor.

Signature evidence сохраняет **исходные signed payload bytes, signature bytes,
key identity и original vote/signature IDs**. На deployment допускается ровно
один approved `signature_codec_id`/verifier, pinned в bootstrap, без plugin
negotiation от snapshot. Проверяются authentic signatures над original signed
context/body, semantic decoding этого payload и связь с typed certificate.
Не вводится новый signing preimage или algorithm вместо существующего protocol.

`producer_rules_id`, codec/build/schema/formal pins обязаны также совпасть с
единственным approved набором, встроенным в установленный verifier. Даже
provisioning operator не может подставить произвольный callback «accept», новый
producer rule или фильтр по успеху R2. Artifact locator не выбирает executable
code или путь вне выделенного content-addressed store; проверяются bytes
конкретного opened object, а затем именно они используются при activation.

В исследованных `ApplyQc`/`ValidatorPolicy` нет готового полного key/signature
binding; `signature_id` и `validate_signers` его не заменяют. Поэтому actual
approved codec/key artifacts — **необходимые inputs до запуска профиля**.
Если исходный protocol signing codec не определён/недоступен, шаг 3 ниже
детерминированно отказывает. Не заимствовать governance/worker signature
protocol и не выдумывать signatures ради прохода bootstrap.

## 4. Full-state binding: один finite prefix, без доверенной arbitrary базы

Source bundle начинается exact pinned genesis/configuration. Он содержит
конечный ordered native producing prefix с input/body preimages и original
certificate messages, плюс retained local journal evidence. Snapshot — только
ускоряющий materialized cut внутри этого prefix; в данном минимальном профиле
origin всё равно проверяется от genesis, без recursive snapshot shortcuts.

Для каждого event verifier обязан:

1. разрешить только уже известный native producer action соответствующей
   pinned версии; сверить actor/context/config и backward dependencies;
2. получить required fields из verified prior native state и original inputs,
   выполнить существующие body/certificate/arithmetic rules и проверить result;
3. сохранить exact identities, aliases/units, full collection membership,
   finalized/candidate различия и journal multiplicity; certificate existence
   не подменяет producing/finalization event;
4. сравнить recomputed native state/cut с complete snapshot inventory, включая
   все 33 policy fields ADR-0013 и вынесенные source/configuration artifacts.

Missing event/field, unsupported producer action или недостаточный source input
означает rejection. Нельзя заменить обработчик action проверкой публичного
`Next`, успешным R2 constructor либо given whole-state equality: это сделало бы
origin circular. Нельзя удалить исходный ISC/EC variant, чтобы получить equality.

**Текущее ограничение:** полного независимого native producer/checker пока нет.
Existing `prepareWhole` начинает с supplied state/policy; это не шаги 1–4 от
genesis. Профиль задаёт finite validation task, а не заявляет готовый verifier
или установленную невозможность EC mismatch. Этот gap остаётся R2.3; если
законный producer prefix воспроизводит mismatch, снова архитектурный STOP.

## 5. Буквально конечная процедура до READY

```text
fresh node -> bootstrap anchor -> verify checkpoint authority
 -> verify snapshot provenance -> check trusted floor
 -> reconstruct/verify WAL -> atomic activation -> READY
```

Перед началом имеется закрытый local bundle; verification не запускает fetch,
peer discovery, ожидание quorum или retry до «самого нового» checkpoint.
Для этой deployment configuration выбраны admission limits: control document
не более 4 MiB; до 65 536 artifact refs; суммарно до 64 GiB прочитанных bytes;
до 1 000 000 source events и до 1 000 000 WAL/pointer records суммарно.
Existing более строгие per-object/parser/arithmetic bounds сохраняются.
Это proposed production import resource caps, не новые universal formal bounds
и не измеренная пропускная способность. Слишком большой пакет отвергается.

| Шаг | Конечная работа и необходимый output | Отказ |
|---|---|---|
| **1. fresh node** | Пустой D. Подключить independently retained T по provisioned identity, получить exclusive owner lock и fenced signing-key custody. Закрыть voting/commands/effects. Один bounded scan inventory | T отсутствует/подменён, unknown custody, foreign local identity или другой writer: BLOCKED |
| **2. bootstrap anchor** | Проверить trusted bootstrap digest, fixed epoch registry, pinned build/semantics/codecs. Просканировать конечный T `trust.log` от INIT record; выбрать последний durable F и собственный tip L. Cold handover требует, чтобы pointer tip уже был связан с этим F; pending anchor — отказ. Даже на пустом D не сбрасывать T до initial F0 | Bad log/tail, pending pointer/anchor mismatch, unknown key/epoch/version, отсутствующий approved input, reset старой identity: BLOCKED |
| **3. verify checkpoint authority** | Один bounded traversal original ApplyQC/candidate/root/shard/APC/EC/ISC graph и votes. Проверить canonical IDs, contexts/roles/keys, threshold3/unique signers, signed payload association, model/optimizer artifacts. Output — authenticated exact F tuple и verified original graph | Signature/key/body/parent mismatch; cyclic/missing graph; self-authenticated epoch: BLOCKED |
| **4. verify snapshot provenance** | Один indexed topological pass native source events от pinned genesis до target, с сохранённым computed cut. Проверить complete snapshot/config/source/aliases/units/collections и checkpoint transitions. Output — derived original cut и target, а не accepted public state | Нет independent producer rule/inputs, extra or omitted collection, bad origin либо mismatch: BLOCKED |
| **5. check trusted floor** | Candidate snapshot current и derived target current должны **exactly equal F**; exact QC ID, height, model и optimizer, не просто model hash. Проверить original current lineage и snapshot cut ≤ authoritative own tip L. Floor reread под lock | Старый valid checkpoint, fork, новый self-selected checkpoint, changed F или unproven ancestry: BLOCKED |
| **6. reconstruct/verify WAL** | Один ordered scan own original journals на T. Сопоставить prefix/cut и suffix до L с source-derived states, policy IDs, exact commands/votes/receipts/effects и pointer CAS. Rebuild volatile caches. Original files/bytes/sequences не переписывать. Output — exact recovered state и полный own durable vote cache | Gap, missing intact record, ambiguous/torn required scan, lost unpublished intent, altered policy или target mismatch: BLOCKED |
| **7. atomic activation** | Выполнить конечный durability protocol §6: immutable D generation, then one T activation commit. F/L recheck перед commit. Output — durable association generation ↔ manifest ↔ F ↔ own cuts | Любая I/O/durability/identity ошибка: BLOCKED, ни replacement journal, ни fallback current |
| **8. READY** | Последняя identity/hash/cut проверка непосредственно загруженных immutable bytes; state/current равны шагам 4/6, last T commit соответствует F/L. Только теперь открыть existing runtime command/effect boundary | Несовпадение или unavailable proof/compatibility authority: остаётся RECOVERING/BLOCKED |

READY здесь имеет existing native смысл: разрешены commands/votes для той же
enrolled identity с восстановленным собственным no-double-vote cache и
сертифицированным current F. Это не observer-only READY и не утверждение,
что F является последним checkpoint глобальной сети. Bootstrap freshness
ограничена independently provisioned/retained anchor, как требует ADR-0013.

Конечность структурная: все refs перечислены до запуска; dependency indices
строго меньше текущего event index; cycle/missing ref не вызывает рекурсию/fetch.
Counters byte/event/record budgets монотонно убывают. Каждый документ, history
event и WAL record обрабатывается конечным checked алгоритмом. Invalid input
также заканчивается отказом; не существует ветви «дождаться ещё одного ресурса».

Host supervisor завершает startup worker после **60 минут** или I/O failure;
это operational timeout с закрытым READY, не consensus deadline/ABORT и не
обещание обработать 64 GiB за час. OS/storage hang не превращается в proof
termination: доступность supervisor/OS остаётся физическим deployment assumption.
Никакое истечение времени не считается успешной verification.

Процедура конечна по спецификации, но **не является сейчас исполняемой командой**:
нет implementation полного producer/verifier и activation integration. При
отсутствии любого обязательного checker/input результат BLOCKED, не READY.

## 6. Atomic activation и ongoing rollback floor

Выбрана одна техника: **immutable data generation + single authoritative commit
на независимом T**. Нет попытки atomically rename между двумя filesystems.

1. Под owner lock создать `D/staging/<manifest-id>`; materialize snapshot и
   referenced immutable artifacts. Own journals на T остаются на месте.
2. Записать и проверить exact bytes, `fsync` файлов и нужных directories.
   Переименовать staging в `D/generations/<manifest-id>` внутри D и `fsync`
   родительской directory. До этого candidate не active.
3. Повторно сверить F, own tip L и preceding trusted-log record ID. В один
   `ACTIVATE` record записать exact F, generation/manifest IDs и journal cuts.
   Append на T, `fsync` trust log (и directory при создании). **Это commit point.**
4. Только затем выбрать эту generation в памяти и выставить READY. Отдельный
   mutable `D/CURRENT` не authority и для этого профиля вообще не нужен.

`fsync(file)` не гарантирует durability directory entry; поэтому directory
sync задан отдельно. Atomic visibility rename также не заменяет barriers.
Основание: [Linux fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html)
и [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html).

| Crash point | Recovery rule |
|---|---|
| До durable D generation | Candidate не active; прежний T floor остаётся. Новый узел остаётся RECOVERING |
| D durable, T commit ещё отсутствует | Orphan generation не authority. Новый явный startup повторяет ограниченную проверку |
| T record partial/corrupt или durability outcome неоднозначен | BLOCKED. Нельзя отрезать trusted tail и выбрать более старый floor |
| T commit complete, response/READY ещё не опубликованы | Повторно проверить exact referenced generation/cuts; завершить тот же activation без новых vote/effect identities |
| T commit complete, но D откатан или generation потеряна | BLOCKED; восстановить требуемые bytes с теми же hashes через новый полный startup attempt, не выбрать старую generation |

После READY trusted floor должен обновляться для каждого нового accepted
checkpoint. Existing current-pointer WAL сначала durable на T; затем append
`ANCHOR` record с новым exact tuple и existing current/WAL references, `fsync`;
только после этого новый trusted current может быть exposed. `ANCHOR` не QC и
не меняет original pointer-WAL record. Предшествующая snapshot generation
сохраняется как immutable local base, а новый anchor ссылается на её verified
WAL continuation. При restart replay обязан дойти до последнего F.

Crash после durable pointer WAL, но до `ANCHOR`, не разрешает пропустить этот
current record: scan полного retained T WAL выявляет его. **Этот cold-import
profile завершает такой attempt как BLOCKED**; он не открывает внутри шага 2
второй неопределённый recovery workflow. Exact pending current/anchor completion
должен быть отдельно квалифицирован как existing native recovery edge до
допуска такого T к cold handover. Нельзя служить старым current потому, что
anchor append не успел, или восстановить на его место прежний T backup.
Это явная availability limitation минимального профиля, не закрытие general
R3 recovery/liveness. Autonomous pending-anchor repair здесь не проектируется.

Новый node с пустым D после утраты старой generation импортирует cut current=F;
восстановление прежнего own journal до L обязательно. Если такой complete пакет
не предоставлен, этот минимальный профиль заканчивается BLOCKED и не имеет
автоматического fallback к более старому snapshot.

## 7. Минимальные изменения после отдельного разрешения

| Область | Минимальный blast radius | Что сохраняется / что ещё не квалифицировано |
|---|---|---|
| Schemas/encoding | Одна profile specification/schema family с closed definitions bootstrap/manifest/source-index/trust-record; bindings original signature evidence refs; strict canonical control decoder/encoder | Existing 003/008 certificate/vote/QC/WAL encodings и IDs не меняются. Новые control fields не добавляются в `additionalProperties:false` старых types |
| `delta-core-cpp` | Pure verification exact bootstrap/manifest metadata, existing certificate graph и native producing-history composition; explicit signature/key evidence association | Нет sockets/filesystem/clock. `ChainVerifier::verify_apply` и arithmetic routines переиспользуются; full producer and typed signature binding сегодня не готовы |
| `delta-runtime-cpp` | Staging/import orchestration, independent trust-store reader/log, owner/cut checks, activation, READY gate, retained journal placement, floor ordering around `CurrentPointerStore::advance` | Existing consensus WAL/vote bytes, sequences, replay identities неизменны. Новый persist-before-expose порядок для local anchor требует qualification; это существенная runtime change, не простой config flag |
| Java/sidecar launch | Передать два pinned directories/authority descriptor, запретить обычные commands до verified readiness, ограничить startup worker operational budget | Transport остаётся opaque; Java не определяет current. Новых consensus commands по phase names нет |
| Production TLA | **Ожидаемый минимум: без изменения `DeltaReduce.Init/Next`**. Bootstrap проверяет source-reachable prestate; local staging/log operations должны отображаться в stutter/recovery, не новый protocol action | `CertificateVoteUniqueness`, `FinalizeApplyQC`, `AdvanceCurrentCheckpoint` сохраняются. Потребуется проверить соответствие `Restart`/`RecoverJournal`, current/crash edges. Если rehydration фактически не моделируется ими — STOP, а не незаметное расширение Init |
| Lean R2.3 | Связать independent origin и exact profile input bytes с имеющейся whole source/state relation; переиспользовать family/constructor/domain результаты и source decoders | `NativeReplayAdmission.prepareWhole`/`wholeStartupSource` дают decode/binding supplied base; **не доказывают** её origin. `NativeCurrentHistory.checkRow`/`rowSource`/`currentStateDerived` дают source-linked current components; composition ещё OPEN |
| Lean R3 | После отдельной команды — initial/reachable base, ordered WAL recovery, exact retry/unknown, retained own intent и activation/floor preservation в frozen recovery claim | `NativeConfigReplay`, `NativeArithmeticHistory`, `NativeCurrentHistory` reuse conditional results. Не предполагать recovery equality. Физические fsync/nonrollback/custody остаются именованными assumptions |

По объёму это малое schema addition, **среднее–большое runtime изменение** и
существенная композиция уже существующих formal components. Нельзя оценивать
его как «добавить manifest hash». Самый большой неопределённый участок —
независимые полные native producer rules: их отсутствие является конкретным
препятствием оценки часов до CLOSED, а не разрешением строить бесконечные слои.

Этот профиль не меняет certificate semantics и WAL identity по замыслу.
Но integration obligation остаётся: если source rules, signed payload association
или activation требуют protocol changes, implementation не начинается без нового
решения и formal-first gate. Существующий guard не снимается.

## 8. Residual и STOP

- R1/R2.1/R2.2 остаются accepted CLOSED. Для их reopening нужен конкретный
  контрпример, данный документ его не устанавливает.
- R2.3/R2 OPEN: требуется independent source-origin verification и её связь с
  уже замороженными full source/config/aliases/units, collections/current и
  initial/incomplete/ABORT obligations. Предложенный профиль фиксирует inputs
  и конечный порядок проверки; не является доказательством соответствия.
- R3 не начат. Новый deployment instance не заменяет general all-actor recovery
  claim и не вычёркивает допустимые Init/pre-first-ApplyQC states из frozen DoD.
  Nonempty imported pre-first-ApplyQC packages просто не поддерживаются здесь.
- Исторические proofs/evidence на прежних pins сохраняются; новые control
  encodings, trust/floor/activation и origin composition ими не покрыты.
  Actual implementation потребует affected source-bound requalification,
  без объявления старого PASS новым Formal GO.

Выбор механизмов для этой конфигурации закончен. До её operational instantiation
нужны genuine enrollment/keys/anchor/source artifacts и approved exact native
producer/signature/build bindings. Это не открытая альтернатива между TPM,
cloud trust service и новым QC: в v1 они не проектируются. Если независимый T
не принимается как trust assumption deployment, **этот профиль неприменим**;
нельзя молча расширить его защиту до rollback T/всей машины.

**STOP после profile.** Только документация. Никакого нового кода, schemas,
formal predicates, proofs, fixtures, runtime changes или запуска R3.
Дальнейшая реализация требует отдельной прямой команды пользователя.
