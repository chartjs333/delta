# ISC Finalization WAL Capsule v1

**Decision document к ADR-0014. Статус: PROPOSED, требуется отдельное утверждение.**

30 сентября 2026. Existing tasks T053/T016, HR008-001/002/018.
Только спецификация хранения одного native `FinalizeISC`.
[ISC Commitment Profile v1, A](0014-isc-commitment-profile-v1.md) утверждён для
FR-004 после двух правок в commit `45632414`. Его approval не квалифицирует
parent/context completeness, подписи, producer, durability или R2/R3.
Код, schemas, fixtures и proofs здесь не создаются и не меняются.

Цель: сохранить исходные votes, полный доставленный cut, полученный canonical ISC
и результат одной finalization в существующем native-owned WAL. Предлагаемые
локальные framing tags ниже не являются новыми certificates или authority.
Документ **не утверждает готовность production transition**: существующие
parent/context и source/authentication obligations сохраняются (§11).
Оценка 50–84 часа не утверждена; новый execution budget здесь не предлагается.

Источники: candidate `45632414`, native pin
`60c692f6e391f839829dfc64e93380db54cd507b`, не merged Formal GO.
Точные blobs и границы проверены в
[source audit](evidence/0014-isc-finalization-wal-capsule-v1-source-audit.json).

## 1. Выбранный минимальный вариант и альтернативы

| Вариант | Хранение | Совместимость и решение |
|---|---|---|
| **W1, предложен** | Один новый local `JournalKind=3` в прежнем DRW1 frame, четыре явно типизированные sections; self-contained относительно сохранённого trusted prefix/source bundle | Старые kinds 1/2, bytes, checksums и positions не переопределяются. Новый reader обязателен; старый отвергает kind 3. Есть один transaction commit, нет нового журнала certificate authority |
| W2 | Спрятать ISC в existing kind 1 / `FINALIZE_INPUT_FREEZE` | Отклонён: legacy replay вычисляет только coarse RoundState, не ISC membership/source. Existing `WalRecord.record_kind` допускает только `TRANSITION`. Reinterpretation разрушит старый replay contract |
| W3 | Отдельный ISC log/side file с pointer из основного WAL | Отклонён для v1: создаёт дополнительную durability/atomicity границу и восстановление двух журналов. Не нужен для одного bounded ISC; файл сам не может стать authority |

W1 — **новое предлагаемое local storage encoding**, а не уже существующий codec.
Не регистрируем его в коде/schema до решения пользователя и formal-first допуска.
Операция требует read capability kind 3 и согласованных codec/build/semantics pins
до открытия writer; импортированный frame не выбирает версию verifier.

## 2. Authority и вход одного transition

C++ core получает из одной сериализованной native generation:

- independently admitted round/config/epoch/validator set, quorum policy и parent;
- ранее closed/frozen `VoteInputSetBody B`, original ordered tuples и их исходные
  ticket/commitment/AC bindings; `input_root` проверяется по approved A;
- полный original delivered ISC inventory для round на этом cut, с исходными
  signed payload/signature/key bindings, включая repeats/conflicts;
- исходные RoundState bytes `S0`, policy bytes `P0`, проверенный source-index/cut
  утверждённого Snapshot Provenance Profile v1 и собственный committed WAL prefix;
- exact request bytes существующего `protocol::Command` с proposed dispatch value
  `command_kind="FINALIZE_ISC"`; `body_hash=vote_input_set_body_id(B)`, native local
  actor/request ID и round/height/view/logical tick. Это новый dispatch, **не**
  переопределение `FINALIZE_INPUT_FREEZE` и не новая public TLA action.

Тот же source cut независимо определяет parent и configuration. Наличие parent
в RoundConfig, source witness или capsule **не делает parent подписанным полем ISC**
и не закрывает explicit-parent obligation, оставленное commitment profile.

Bootstrap/signature codec/key registry/source bytes не берутся на веру из capsule.
`signature_id`, SHA-256, transport authenticationTag или stored boolean `valid`
не заменяют проверку подписанного payload. Signed bytes и key identity сверяются
с единственным уже независимо закреплённым verifier/profile. Новый signing
preimage, algorithm, quorum или trust service этим решением не вводится.

Ремарка о durable remote votes: finalizer проверяет исходную подпись/envelope и
production delivery lineage. У него нет новой remote fsync attestation. Для honest
signers persist-before-send остаётся существующей предпосылкой; Byzantine threshold
не заменяется предположением о честности каждого signer. Remote vote не вставляется
как local vote в `VoteJournal` получателя и не получает его WAL sequence.

## 3. Точный outer frame

Переиспользуется `delta-runtime-cpp/src/wal.cpp:161–182`. Все integers unsigned
big-endian, без padding. Для kind 3 предлагается тот же frame:

```text
ASCII("DRW1") | U16(1) | U16(0 flags) | U32(total_frame_bytes)
| U64(s) | U8(3) | 00 00 00
| B(request_and_source) | B(candidate_state)
| B(effect_batch) | B(receipt)
| SHA256(all preceding frame bytes) [32 raw bytes]
```

`B(x)=U32(byte_length(x)) || x`; `s` — следующий собственный physical journal slot.
`total_frame_bytes` включает checksum. Existing maximum frame — 64 MiB. Unknown
kind/version, nonzero reserved/flags, integer overflow, wrong lengths/checksum,
trailing bytes или invalid nested encoding дают отказ. Checksum — integrity,
**не authority** и не новый certificate/WAL protocol ID.

Названия четырёх members `JournalEntry` остаются прежними. Для kind 3 их единственное
предлагаемое толкование: `command_or_vote_bytes=request_and_source`,
`next_state_bytes=candidate_state`, `effect_batch_bytes=effect_batch`,
`wal_record_bytes=receipt`. Last section **не** existing type-003 `WalRecord`.
Legacy `parse_wal_record` и `SubmitReceipt.wal_record_id` к ней не применяются.
Так мы не вводим новый смысл старого `record_kind="TRANSITION"` или его ID.

## 4. Persisted sections и canonical encoding

`H(tag)=ASCII(tag[4]) || U16(1) || U16(0)` — local section header, ровно 8 bytes.
`T(s)=B(ASCII(s))`; identifiers сохраняют свои existing grammar/limits, не case-folded.
`D(p)` — **64 ASCII lowercase hex bytes** SHA-256 от existing policy codec bytes,
как `runtime.cpp:38–47`, без `sha256:` prefix. Никаких JSON objects вокруг binary
sections, optional fields, alignment или trailing bytes. Canonical equality каждой
nested сущности проверяется её existing codec. Для tuple JSON действует новое
нормативное duplicate-member rejection до typed construction.

### Section 1 request and source

Последовательность полей фиксирована:

```text
H("IFQ1")
| B(original_command_bytes)
| U64(prior_wal_byte_length)
| raw32(SHA256(exact prior WAL bytes))
| T(source_index_id) | U64(source_cut_event_index)
| B(S0) | B(P0)
| U32(delivery_count)
| delivery[0] | ... | delivery[delivery_count-1]
```

Каждый `delivery` имеет ровно:

```text
U64(original_source_event_index)
| T(original_peer_id)
| B(original_vote_frame)
| B(original_signed_payload)
| B(original_signature_bytes)
| T(original_key_id)
```

Это storage fields для **существующего** signature evidence, перечисленного в
approved provenance profile, не новый wire envelope. Relationship signed payload ↔
vote/signature IDs определяется закреплённым signature codec; capsule не задаёт
новый signing preimage. AuthenticationTag транспортного adapter не подменяет
original signature bytes. Если approved codec/key evidence отсутствует, verification
не может завершиться; checksum не предоставляет fallback.

Events перечисляются в строгом исходном source-event order и образуют **полную**
проекцию доставленных ISC envelope events данного round до cut включительно.
Другие bodies/context и повторные доставки сохраняются. Нельзя сохранить только
удобные q votes или отбросить multiplicity. Индексы — существующие source-index
positions, не coordinate/vote/certificate identities и не новые WAL slots.
Missing original observation нельзя заменить synthetic index. Для каждого event
проверяется равенство независимому source entry и его dependency lineage.

`source_index_id/cut` ссылаются только на **уже retained и проверенный** конечный
source bundle на T из выбранного provenance profile; он предшествует finalization.
Он включает exact configuration/ticket/AC/proposal/close/delivery dependencies.
Lookup bounded/local, без network bootstrap. P0 обязан равняться generation,
восстановленной из этого bundle и WAL prefix; caller P0 не становится authority.
Source completeness не доказывается digest, который прислал сам caller.

Self-contained здесь означает: record + retained independently authorized prefix
и source bundle восстанавливают все bytes. Не standalone snapshot certification.
Referenced bytes должны быть durable до append; отсутствующий объект закрывает
READY. Никакой garbage collection этих dependencies или нового snapshot format
этим профилем не разрешается.

### Section 2 candidate state

```text
H("IFS1") | B(P1) | B(canonical_ISC_JSON)
```

P0/P1 — точные bytes **существующего** `encode_vote_policy_v1`, включая full
`VoteAdmissionSnapshot`; не новый full-state codec. Для одной finalization P1
отличается от P0 ровно set-union C в `snapshot.input_set_certificates` и
`ISC_ID(C)` в `snapshot.finalized_input_set_ids`, в canonical order существующего
codec. Если exact C уже есть в первой collection, его bytes сохраняются один раз;
существующее finalized membership обрабатывается как replay, не новый append.
Повтор/конфликт проверен раньше. Все остальные поля/collections/candidates,
existing finalized IDs, downstream lineage и исходные objects сохраняются.

RoundState S0, его `state_id`, phase, current checkpoint/model/optimizer и coarse
`durable_sequence` не меняются: existing `FinalizeISC` меняет certificate collection,
а `BaseVariablesUnchanged` сохраняет остальное. Нельзя использовать legacy handler
для искусственного перехода в `ELIGIBLE`. Full generation commit включает P1 и
отдельный finalized-round/replay index; один coarse `state_root` её не описывает.

C — existing `InputSetCertificate{B.context,B.input_root,q,signer_ids,B.tuples}`.
Его canonical JSON, content-ID domain и signer bytes не меняются. P1 и JSON должны
восстанавливаться независимо из P0/source и точно совпасть с записанными values.
Saved P1 — проверяемый output, не permission заменить state caller snapshot.
Полная existing policy validation P1 остаётся обязательной. Если сохранённая
collection/candidate (например, exact-lineage ABORT body) делает P1 несовместимой
с ней, нельзя удалять или переписывать эту collection ради success: exact
source-valid witness означает STOP по уже существующему state-compatibility
обязательству. Здесь не предполагается, что добавление C всегда его сохраняет.

### Section 3 effect batch

Exact existing type-003 `EffectBatch` bytes с одним existing `PUBLISH_CERTIFICATE`:

- `body_hash=ISC_ID(C)`, `kind="PUBLISH_CERTIFICATE"`, `target_id="validators"`;
- `effect_id="effect:" + original_request_id + ":02:publish"`;
- batch `request_id/round_id` исходного command;
- `prior_state_root=next_state_root=content_id(Type::round_state,S0)`.

Это proposed instance существующего output type, не вызов legacy `make_effect_batch`:
его PERSIST_STATE effect и hash-only command path не выполняют этот transaction.
Равные coarse state roots не означают отсутствия certificate-state change; exact
P0/P1 binding находится в capsule. Новую hash formula вместо existing effect/batch
ID не вводим. Полные canonical ISC bytes из section 2 сопровождают публикацию;
одного hash для внешнего получателя недостаточно. Никакого seed effect в batch нет.

### Section 4 receipt

```text
H("IFR1") | U64(s)
| T(command_id) | T(ISC_ID(C)) | T(effect_batch_id)
| D(P0) | D(P1)
```

IDs вычисляются existing domain/type functions. Нет receipt UUID, нового QC ID,
второго WAL sequence или self-referential hash. Операционный флаг replay не входит
в эти canonical bytes. Future dedicated ABI result должен возвращать этот receipt,
section-3 effect и exact ISC bytes; он не маскируется под старый `SubmitReceipt`.
Transport request nonce не меняет ранее сохранённый результат.

Все lengths/counts проверяются до allocation и append. P0/P1 ≤ existing 4 MiB каждый;
ISC ≤ existing 4 MiB; votes и nested types сохраняют existing limits; полный DRW1 ≤
64 MiB и output должен помещаться в существующий 16 MiB bounded result. Совокупная
совместимость whole source domain этим документом **не доказана**. Нельзя подогнать
frame удалением delivery entries или lineage. Допустимый source cut, который не
помещается, означает compatibility STOP с exact witness, а не новый меньший cap R2.

## 5. Проверка quorum и canonical ISC

Native finalizer для единственного ранее closed B последовательно:

1. Проверяет origin/source/policy/WAL-prefix association, RoundConfig/parent/epoch,
   исходные closed inputs и logical preconditions existing `OrdinaryNext`/FinalizeISC.
   Command logical tick совпадает с tick этого source cut; finalization не создаёт
   Tick/advance-time action. Java не выбирает members или quorum cut.
2. Проверяет полный tuple array, unique ticket/order, FR-004 root и full B bytes.
   Нельзя принимать только совпадение `input_root`.
3. Для каждого delivered envelope проверяет original signature/key/role/epoch,
   original canonical vote, ISC kind, full B/context association,
   `body_hash=vote_input_set_body_id(B)` и existing round-scoped `vote_context_id`.
   Другой body не голосует за B; repeated delivery не добавляет signer.
4. Берёт **весь** matching delivered signer set на этом cut, sorted unique; q=2f+1
   для original 3f+1 members (в выбранном deployment 3 из 4). Не first-q subset.
   Conflicting Byzantine evidence остаётся в source inventory; не все remote votes
   пропускаются через honest local `VoteJournal` как будто Byzantine невозможны.
5. Получает C и запускает existing `verify_input_set` плюс перечисленные source,
   signature/root checks, которых structural verifier сам по себе не доказывает.
6. Вычисляет P1, effect и receipt, сверяет все sizes/conflicts и только затем append.

Соответствие существующим действиям: prior `VoteISC` → persist original envelope;
`Send/DeliverVoteEnvelope` → original source events; durable finalization → existing
`FinalizeISC(B)` с полным `ISCSigners(B)`; внутренние prepare stages stutter.
Не создаётся новый vote, `GenerateSeed` или публичный recovery action. Разные legal
cuts могут иметь разные signer sets/QC IDs; документ не вводит новый global
signer-subset consensus rule. После finalization исходный signer set неизменен.

## 6. Validate append barrier commit expose

1. **Validate:** single writer проверяет request replay/conflict до новой сборки;
   выполняет §5 в private candidate, preallocates bounded outputs/caches. Никакой
   новой committed membership, policy authority или observable effect.
2. **Append:** один complete kind-3 DRW1 record в тот же own WAL, с `s=last+1`;
   checked exhaustion, exact prior length/hash и pinned directory/file identity.
3. **Barrier:** existing native `append_and_sync` contract, включая file fsync и
   необходимую directory durability, затем повторная file/directory binding check.
   Любая ошибка оставляет operation uncertain и закрывает дальнейшие mutations и
   exposure до verified recovery. Не считать неудачный fsync доказательством absent.
4. **Commit:** единая publication generation для P1/certificate membership,
   finalized-round index, request→original-result cache, policy digest и physical tip s.
   Readers получают old либо whole new generation, не смесь. Никакая allocation
   failure после barrier не разрешает продолжить из старого state с новым WAL tip.
5. **Expose:** только после commit и последней binding check возвращаются original
   receipt/effect/ISC bytes; Java может отправлять их как opaque bytes.

P0 и P1 сохраняются для historical verification; old vote records сохраняют свой
original policy digest. Новая generation не сбрасывает no-double-vote cache,
`authority_invalidated` или прежние запреты. Переход P0→P1 разрешается только как
проверенный результат этого transaction, не общий caller-controlled policy reload.
Этот документ не добавляет candidates для EC/seed или других следующих producer
operations и не разрешает их реализацию.

## 7. Crash cuts и восстановление этого record

| Cut | Что разрешено после restart |
|---|---|
| До append, включая validation/preallocation failure | Old generation, no effect; новая попытка только после обычных checks |
| Partial/torn append | Ни ISC exposure, ни автоматический truncation. Для выбранного provenance profile ambiguous/torn required own prefix блокирует READY. Native legacy `recover()` truncation не переносится в этот contract без проверки trusted floor/continuity |
| Complete append, barrier ещё не выполнен либо вернул ошибку | Record может отсутствовать или сохраниться. Failed call ничего не публикует. Скан и independent source/floor определяют действительный prefix; неизвестность нельзя заменить старым tip |
| Complete intact record пережил unacknowledged append | Проверить всю capsule и original prefix, обеспечить durability barrier surviving bytes, реконструировать тот же C/P1/receipt/s. Новый record не дописывается |
| Barrier завершён, commit не завершён | Recompute из original P0/source, exact equality всех sections, затем whole-generation commit исходного record |
| После commit, до возврата / после возврата, до network send | Replay исходного receipt/effect/ISC и sequence; ни новой finalization, ни нового signer set |
| После network send, acknowledgement потерян | Повтор доставки идентичен; receiver dedup по existing objects/IDs; WAL остаётся прежним |
| Complete corrupt/unknown-kind/mismatched-source record, missing dependency или floor conflict | Fail closed до READY/exposure. Не вычищать lineage, не откатывать trusted floor и не создавать replacement QC |

Verified absence допустимо только если authoritative retained prefix действительно
заканчивается до s и нет floor/evidence, требующих s. Отсутствие файла или timeout
не является verified absence. Полнота/подлинность history — существующее требование
approved provenance profile, не утверждение о достаточности одной checksum.

Это требования к восстановлению **данного transaction**, не выполненный R3 и не
реализация production recovery. Доказательства crash cuts пока отсутствуют.
Legacy DRS1 snapshot хранит coarse RoundState: он не заменяет P1/source/replay index.
Для W1 всё это восстанавливается из retained prefix/capsules; pruning/compaction
и новый snapshot cache format здесь не проектируются.

## 8. Idempotent replay и conflict handling

- Все request IDs проверяются в общем namespace legacy и новых commands;
  совпадение с другим command kind/bytes — conflict, не новый отдельный namespace.
- Same request ID + exact original command bytes: после проверки binding найти
  original transaction, вернуть его bytes и sequence **до** расчёта quorum по новым
  arrivals. Смена live source cut не заставляет пересобрать уже committed certificate.
- Same request ID + different command bytes: conflict, no append/state change.
  Если caller пытается приложить иные evidence bytes к exact historical retry,
  они не заменяют authoritative saved capsule и не обрабатываются как новый source.
- New request ID + already finalized exact full B/context: вернуть original finalized
  result/receipt с исходным request/effect identity. Не создавать durable alias,
  дополнительный WAL slot или QC с расширенным signer set.
- Different full B/context для уже finalized round: fail closed до append; исходные
  state, prefix и receipt остаются. Root equality не отменяет body/context conflict.
- Recovery rebuild двух индексов: original request→result и finalized round→original
  full B/C/receipt. Это derived caches; source — только verified capsule/prefix.
- Late matching votes не меняют C. Другой quorum certificate с иным signer set
  нельзя молча объявить тем же content ID или вставить вторым finalized ISC.

Rejection сам по себе не создаёт новый durable vote/record или AbortQC. I/O failure
может оставить partial bytes и отличается от semantic conflict, отвергнутого до write.

## 9. Identity и seed release

Сохраняются original vote frame, `signature_id`, signer, epoch, `context_id`,
`body_hash`, `Vote.durable_sequence` и все прежние certificate IDs. Typed ISC ID,
proposal body ID и generic QC ID — разные existing identities, не aliases.

В native pin `Vote.durable_sequence` — **позиция vote в own physical WAL отправителя**,
не число одних votes. Finalization потребляет новый local physical slot, поэтому
следующий ещё не подписанный local vote использует уже следующий slot. Старые
signed envelopes не перенумеровываются. Remote signer sequence не равен slot
получателя. Public per-validator `durableSequence` увеличивается только для
производимого vote: storage kind 3 не добавляет абстрактный vote. Требуется прежняя
явная native→public sequence mapping, а не равенство этих чисел.

Root profile A может изменять **новые** B/C bytes относительно исторического
constant-root fixture; эта несовместимость уже записана в commitment decision.
Capsule не мигрирует old QC/votes, не resigns защищённый context и не выдаёт новый
семантический ID. Existing kinds 1/2 и their exact hashes/interpretation unchanged;
whole-file digest после нового append закономерно изменяется, old prefix — нет.

Seed release требует finalized ISC membership в **committed durable generation**
и existing seed-action predicates. Candidate C, записанный но unverified record,
quorum count в памяти, successful `verify_input_set`, response cache без recovered
prefix или coarse phase `ELIGIBLE` не открывают gate. Finalization effect не содержит
random bytes/shares. Local replay обязан сначала завершить recovery, затем решить
separate existing `GenerateSeed`; receipt replay не запускает её автоматически.

## 10. Compatibility и последующая qualification

| Контракт | Consequence предлагаемого W1 |
|---|---|
| DRW1 version/checksum/framing kinds 1/2 | UNCHANGED. Новый kind 3 требует explicit dispatch; old reader отвергает его, не пропускает |
| Old `WalRecord`, command/vote/QC IDs, old evidence | UNCHANGED для исходных bytes. Новый receipt не выдаётся за existing WalRecord; его ID не выдумывается |
| Existing policy codec | Bytes/identity function reused. Runtime immutable-at-startup assumption needs explicit derived-generation integration; старые fixed-policy proofs этого не покрывают |
| C++ runtime/ABI/sidecar | Будущий new command/result dispatch и atomic generation cache. Старый API не может вернуть новый receipt через случайное type punning |
| Java | Opaque transport/authentication boundary, без вычисления membership/quorum/C/P1. Native проверяет semantic authority |
| Production TLA `Init/Next`, certificate semantics | Изменения не предлагаются. Нужна qualification implementation phases→existing `FinalizeISC`, включая signer cut и unchanged vote sequences; документ не доказывает её |
| Lean и trace evidence | Existing codecs/quorum/static-body theorems сохраняют original scope. New capsule/generation/replay не следуют из v1-only WalScan/ConfigReplay proofs. Не менять старые statements ради claim |
| R1/R2.1/R2.2, R2.3/R3 | CLOSED части не открываются. R2.3/R2 OPEN; ни full source-domain sufficiency, ни recovery refinement здесь не закрыты |
| Downgrade | Writer, поддерживающий только kinds 1/2, не открывает журнал с kind 3. Не truncate, не rewrite, не fallback к coarse-only snapshot |

Будущий файловый footprint, **не разрешение редактировать**: `delta-runtime-cpp/src/`
`wal.hpp`, `wal.cpp`, `runtime.cpp`, dedicated capsule codec; `runtime.hpp`/dedicated
ABI dispatch, `delta-core-cpp` ISC producer; proposed schema documentation из
integration ADR. Affected proof targets — future NativeIscFinalizeBytes/Replay и
refinement wrapper. Production `.tla`, certificate schema, 003 identities и approved
provenance profile не меняются данным документом. Новую source qualification,
semantics closure и exact compatible merged Formal GO нельзя заменить этим ADR.

## 11. Конечная граница решения и STOP

Для утверждения W1 требуется согласиться с kind 3 и четырьмя sections, исходными
source/signature dependencies, derived P0→P1 commit, receipt semantics, no-tail-repair
поведением выбранного profile и fail-closed compatibility. Никакой альтернативный
provenance mechanism не предлагается.

Уже существующие вопросы, которые **не закрывает** этот storage contract:

1. **Explicit parent/context binding:** отдельное compatibility/refinement obligation
   из правки пользователя. Наличие parent в local source record его не удовлетворяет;
   новых ISC полей здесь нет. Если его закрытие требует certificate change — STOP.
2. **Concrete source/authentication authority:** producer/delivery history и закреплённые
   signature codec/keys должны существовать независимо. Source pin содержит opaque
   authentication callbacks и signature IDs, не полное доказательство этого binding.
   Capsule сохраняет evidence, но не создаёт её. Нельзя объявить integration GO,
   подставив fictional signature verifier или structural-only `verify_input_set`.
3. **Representation/storage coverage:** admissible cut должен быть представим в old
   policy/full-state bounds и bounded capsule. Empty close и whole-state bounds не
   объявляются доказанными; корректный oversized/unrepresentable cut требует STOP,
   не silent source-domain narrowing. Это existing compatibility gate, не новый DoD.

После отдельного утверждения обоих byte contracts всё равно необходима прямая
команда на следующий ограниченный этап и соблюдение formal-first STOP. Реализация
producer, code/proofs/schemas/fixtures, R2.3/R3, new predicates и recovery не начаты.
**STOP после этого документа.**
