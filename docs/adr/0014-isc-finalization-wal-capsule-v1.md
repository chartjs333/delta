# ISC Finalization WAL Capsule v1

**Decision document к ADR-0014. WAL Capsule W1: APPROVED как local byte/storage contract; I-B и S-RANK: APPROVED.**

Amendment от 30 сентября 2026 переносит утверждённые
[identity/sequence решения](0014-isc-identity-sequence-amendment.md) в storage contract.
W1 утверждён пользователем как локальный byte/storage contract; это не разрешение
на реализацию или утверждение production/refinement sufficiency. Все новые значения ниже
нормативны только для будущей отдельно квалифицированной semantics version `σ_next`;
это метаобозначение, не присвоенный version string/hash или новое wire field.
Существующие accepted/candidate semantics IDs не активируют эти правила.

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

После local approval выполнен только [аудит трёх gates](0014-w1-three-gate-audit.md):
parent/context, source/authentication и whole-domain bounds — каждый **STOP**.
Новых решений или разрешения на implementation этот отчёт не добавляет.

Источники: candidate `45632414`, native pin
`60c692f6e391f839829dfc64e93380db54cd507b`, не merged Formal GO.
Исторические blobs и границы исходной редакции записаны в
[source audit](evidence/0014-isc-finalization-wal-capsule-v1-source-audit.json).
Его report hash относится к той редакции; amendment фиксируется отдельным Git commit.

### Нормативные identities и positions

| Обозначение | Единственный смысл в `σ_next` |
|---|---|
| `B`, `b` | Полный `VoteInputSetBody` и `b=vote_input_set_body_id(B)`: **consensus body identity** ISC. Используется в seed/assignment context, каждой downstream ссылке на ISC, finalized index и semantic replay |
| `C`, `c` | Полный typed ISC и `c=content_id(C)`: **certificate witness/artifact identity**. Original signer set и exact bytes сохраняются; разные C для одного B могут иметь разные c |
| `s` | **Physical WAL slot** в исходном журнале actor, не byte offset и не vote count. Native signed `Vote.durable_sequence` и native receipt сохраняют этот s |
| `V_a(s)` | **Public vote ordinal/count**: число original kind-2 records actor a в independently verified prefix до s включительно. Для vote в slot s это его public ordinal; для kind 1/3 это только неизменившийся count |

`b` не заменяет quorum evidence. `c` не является consensus parent. Ни одинаковая
`sha256:` grammar, ни hash-only equality не разрешают interchange: каждая позиция
проверяется своим typed resolver и exact source bytes. `C.body=B`, computed b и
computed c проверяются совместно. Generic QC ID — ещё отдельная existing identity.
`RoundState.durable_sequence` остаётся отдельным coarse command-state счётчиком.

| Позиция | Требуемая identity |
|---|---|
| IFQ1 command.body_hash; logical finalized `(round context) → b`; semantic replay `(round context,b)` | b |
| Seed/EC/APC/PARAMETER/ROOT field `input_set_certificate_id` и их ISC context; assignment authority | b в `σ_next`; historical c-meaning остаётся только в старом profile |
| IFS1 exact C; witness lookup `c → exact C`; PUBLISH_CERTIFICATE.body_hash; IFR1 certificate reference | c — artifact, не parent |
| DRW1.sequence; IFR1 sequence; native vote durable_sequence | s |
| Public durableSequence[a]; diagnostic public vote ordinal | V_a(s), не переписанный native receipt |

No new persisted identity field: b уже есть в IFQ1 command и восстанавливается
из B в IFS1 C; c сохраняется в existing proposed IFR1/publish positions.
Сравнение этих двух выводов обязательно, не inference из string prefix.

## 1. Выбранный минимальный вариант и альтернативы

| Вариант | Хранение | Совместимость и решение |
|---|---|---|
| **W1, APPROVED local byte/storage contract** | Один новый local `JournalKind=3` в прежнем DRW1 frame, четыре явно типизированные sections; self-contained относительно сохранённого trusted prefix/source bundle | Старые kinds 1/2, bytes, checksums и positions не переопределяются. Новый reader обязателен; старый отвергает kind 3. Есть один transaction commit, нет нового журнала certificate authority |
| W2 | Спрятать ISC в existing kind 1 / `FINALIZE_INPUT_FREEZE` | Отклонён: legacy replay вычисляет только coarse RoundState, не ISC membership/source. Existing `WalRecord.record_kind` допускает только `TRANSITION`. Reinterpretation разрушит старый replay contract |
| W3 | Отдельный ISC log/side file с pointer из основного WAL | Отклонён для v1: создаёт дополнительную durability/atomicity границу и восстановление двух журналов. Не нужен для одного bounded ISC; файл сам не может стать authority |

W1 — **утверждённое local storage encoding**, а не уже существующий codec.
Не регистрируем его в коде/schema без отдельного разрешения на реализацию и formal-first допуска.
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

`B(x)=U32(byte_length(x)) || x` — notation для length-prefix framing, не body B.
`s` — следующий собственный physical journal slot.
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

P0/P1 используют структурный layout existing `encode_vote_policy_v1`, включая full
`VoteAdmissionSnapshot`, но **не прежнее значение ISC reference fields**. Обе generation
уже принадлежат `σ_next`, выбранной независимо от payload. Legacy policy с c-membership
не превращается в P0 заменой IDs. Same binary layout не означает совместимость semantics.
Для одной finalization P1 отличается от P0 ровно set-union original C в
`snapshot.input_set_certificates` и **b** в `snapshot.finalized_input_set_ids`,
в canonical order. Witness index `c → exact C` и finalized `(round context) → b`
выводятся из проверенных collections/source, а не требуют новых wire fields.
Если exact C уже есть, bytes сохраняются один раз. Other original witnesses того же B,
уже присутствующие в source collections, не удаляются и не объявляются одним c.
Already finalized b обрабатывается как semantic replay: ни второй finalization,
ни union нового C посредством этой команды. Все остальные fields/collections,
existing b-memberships данного profile, downstream lineage и original objects сохраняются.

RoundState S0, его `state_id`, phase, current checkpoint/model/optimizer и coarse
`durable_sequence` не меняются: existing `FinalizeISC` меняет certificate collection,
а `BaseVariablesUnchanged` сохраняет остальное. Нельзя использовать legacy handler
для искусственного перехода в `ELIGIBLE`. Full generation commit включает P1 и
отдельный finalized-round/replay index; один coarse `state_root` её не описывает.

C — existing `InputSetCertificate{B.context,B.input_root,q,signer_ids,B.tuples}`.
Field order/content-ID domain сохраняются, original signer bytes не переписываются.
Для тех же полных C bytes c тот же; новый semantics context изменяет bytes/IDs.
P1 и JSON должны восстанавливаться независимо из P0/source и точно совпасть
с записанными values.
Saved P1 — проверяемый output, не permission заменить state caller snapshot.
Все прежние safety checks P1 остаются обязательными; их ISC lookup должен быть
квалифицирован для b в `σ_next`. Legacy validator, ожидающий c, не объявляется
достаточным и не обходится fallback. Если сохранённая
collection/candidate (например, exact-lineage ABORT body) делает P1 несовместимой
с ней, нельзя удалять или переписывать эту collection ради success: exact
source-valid witness означает STOP по уже существующему state-compatibility
обязательству. Здесь не предполагается, что добавление C всегда его сохраняет.

### Section 3 effect batch

Exact existing type-003 `EffectBatch` bytes с одним existing `PUBLISH_CERTIFICATE`:

- `body_hash=c`, `kind="PUBLISH_CERTIFICATE"`, `target_id="validators"`: это witness artifact reference, **не** consensus parent;
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
| T(command_id) | T(c) | T(effect_batch_id)
| D(P0) | D(P1)
```

IDs вычисляются existing domain/type functions. Нет receipt UUID, нового QC ID,
второго WAL sequence или self-referential hash. Операционный флаг replay не входит
в эти canonical bytes. Future dedicated ABI result должен возвращать этот receipt,
section-3 effect и exact ISC bytes; он не маскируется под старый `SubmitReceipt`.
Transport request nonce не меняет ранее сохранённый результат. IFR1.s равен outer
DRW1.s. IFR1.c должен совпасть с computed content_id exact IFS1 C, а IFQ1.command.body_hash
с computed b его B. Подстановка b в IFR1.c или c в command.body_hash отвергается до append.
Replay возвращает исходный c/s даже если позднее предъявлен другой валидный witness C′
того же B; semantic identity остаётся b.

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
signer-subset consensus rule. После finalization исходный local witness C/signers
неизменен; разные C одного B имеют общий b и разные artifact c. Они не создают разные
seed/assignment/ISC-parent contexts и не требуют ожидать один глобальный signer set.
Полная downstream liveness этим разделом не объявляется доказанной.

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
   finalized-round→b index, c→original-C witness index, request→original-result cache, policy digest и physical tip s; public vote count V_a(s) не увеличивается.
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
  result/receipt с исходным request/effect identity, c и s. Logical lookup использует b, а не c. Не создавать durable alias,
  дополнительный WAL slot или QC с расширенным signer set.
- Different full B/context для уже finalized round: fail closed до append; исходные
  state, prefix и receipt остаются. Root equality не отменяет body/context conflict.
- Recovery rebuild original request→result, finalized round context→b и witness
  c→original C/receipt/source. Это derived caches; source — только verified capsule/prefix.
- Late matching votes не меняют C. Валидный C′ с другим signer set для того же B —
  допустимый alternate witness, не body conflict и не новая finalization. Его original
  evidence проверяется/сохраняется в своей исходной lineage; c′ не подменяет c в старом
  receipt. Эта команда не добавляет ради C′ второй WAL record или новый finalized object.

Rejection сам по себе не создаёт новый durable vote/record или AbortQC. I/O failure
может оставить partial bytes и отличается от semantic conflict, отвергнутого до write.

## 9. Identity и seed release

Original vote frames, signatures, signer/epoch/context/body IDs, receipts и старые
QC/WAL bytes сохраняются под **исходным** semantics profile. I-B не обещает неизменность
IDs будущих downstream объектов: в `σ_next` их ISC parent-reference — b вместо c.
Это утверждённое изменение native certificate-reference semantics, не миграция.
No relabel, resign, replay conversion или rehash historical objects в новом profile.

S-RANK нормативно задаёт для полного original prefix actor a:

```text
physicalSequence = length(L_a) = p
V_a(s) = count(i in 1..s where L_a[i].kind = 2)
public durableSequence[a] = V_a(p)
native Vote.durable_sequence at vote slot s = s
s = V_a(s) + count(kind 1 through s) + count(kind 3 through s)
```

Учитываются все original local votes. Remote envelopes внутри kind 3 не становятся
local kind 2. Скан проверяет **каждый** frame, kind 3 нельзя пропускать как opaque
padding или считать vote через `kind != 1`. Projection original votes→public votes
должна сохранять identity/order и быть injective; collapse не исправляется dedup.
Для checkpoint counts выводятся из independently verified original prefix,
не обнуляются и не принимаются из caller metadata. Unknown kinds fail closed.

Kind 1/3 увеличивают physical p, но не V; kind 2 увеличивает оба. Native signed s
никогда не заменяется на V_a(s). Complete surviving frame после проверенного recovery
учитывается ровно один раз; exact retry/replay не увеличивает ни p, ни V и возвращает
original s/c. При uncertain append/barrier tip неизвестен до verified recovery:
не выдавать новый slot, success/effect или READY. Torn/corrupt required prefix не
ремонтируется. No new public recovery action или production recovery implementation.

Следующий новый vote после kind 3 подписывает следующий physical slot, поэтому его
bytes/ID могут отличаться от run без kind 3; это не изменение уже подписанного vote.
Old prefix/checksums не меняются; whole-file digest меняется только новым append.
Root profile A и новый semantics context также меняют **новые** B/C/IDs; historical
constant-root fixtures не «исправляются» и не становятся producer evidence.

Seed release требует finalized **b** в **committed durable generation**, проверенный
witness C с body B и existing seed-action predicates. Seed/assignment consensus identity
не зависит от выбранного c/signers. EC/APC/PARAMETER/ROOT ISC references разрешаются
через тот же b; artifact c lookup остаётся отдельной проверкой authority.
Candidate C, записанный но unverified record,
quorum count в памяти, successful `verify_input_set`, response cache без recovered
prefix или coarse phase `ELIGIBLE` не открывают gate. Finalization effect не содержит
random bytes/shares. Local replay обязан сначала завершить recovery, затем решить
separate existing `GenerateSeed`; receipt replay не запускает её автоматически.

## 10. Compatibility и последующая qualification

| Контракт | Consequence предлагаемого W1 |
|---|---|
| DRW1 version/checksum/framing kinds 1/2 | UNCHANGED. Новый kind 3 требует explicit dispatch; old reader отвергает его, не пропускает |
| Old `WalRecord`, command/vote/QC IDs, old evidence | UNCHANGED для исходных bytes. Новый receipt не выдаётся за existing WalRecord; его ID не выдумывается |
| Policy layout / semantic dispatch | Структурный layout reused только с independently pinned `σ_next`; finalized_input_set_ids и downstream ISC references теперь b. Original C/c witnesses сохранены. Old fixed-policy/c-based lookup proofs не покрывают изменение |
| C++ runtime/ABI/sidecar | Будущий new command/result dispatch и atomic generation cache. Старый API не может вернуть новый receipt через случайное type punning |
| Java | Opaque transport/authentication boundary, без вычисления membership/quorum/C/P1. Native проверяет semantic authority |
| Production TLA `Init/Next` | I-B/S-RANK не требуют их изменения: body-based ISC и vote count уже заданы. Нужна новая qualification phases→FinalizeISC, signer cut и mapping; она не выполнена |
| Native certificate-reference semantics / signed bytes | I-B меняет ISC parent/index c→b **только в σ_next**. Downstream signed bodies/QC IDs и bytes с новым formal_semantics_id новые; existing ISC C domain/formula не меняются. Сохранение old bytes не означает interop |
| Semantics version / compatibility | Новый version/hash должен быть вычислен из будущей qualified closure; сейчас не назначен. Old/unknown version, c-valued parent в σ_next и b-valued witness fail closed. Ни old records, ни signatures/QC не relabel/migrate |
| Lean и trace evidence | Existing codecs/quorum/static-body theorems сохраняют original scope. New capsule/generation/replay не следуют из v1-only WalScan/ConfigReplay proofs. Не менять старые statements ради claim |
| R1/R2.1/R2.2, R2.3/R3 | CLOSED части не открываются. R2.3/R2 OPEN; ни full source-domain sufficiency, ни recovery refinement здесь не закрыты |
| Downgrade | Writer, поддерживающий только kinds 1/2, не открывает журнал с kind 3. Не truncate, не rewrite, не fallback к coarse-only snapshot |

Будущий файловый footprint, **не разрешение редактировать**: `delta-runtime-cpp/src/`
`wal.hpp`, `wal.cpp`, `runtime.cpp`, dedicated capsule codec; `runtime.hpp`/dedicated
ABI dispatch, `delta-core-cpp` ISC producer; proposed schema documentation из
integration ADR. Affected proof targets — future NativeIscFinalizeBytes/Replay и
refinement wrapper. Exact existing requalification inventory —
[identity/sequence memo §3](0014-isc-identity-sequence-amendment.md#3-что-потребуется-переквалифицировать-после-approval).
Source-bound seed/parent proofs с parent.qcId и kinds-1/2-only replay/position theorems
не покрывают b/kind 3. Production `.tla`, schemas, 003 identities и approved provenance
profile **сейчас не меняются**; future schema/semantic dispatch не обходится старым parser. Новую source qualification,
semantics closure и exact compatible merged Formal GO нельзя заменить этим ADR.

### Нормативные documentary vectors I-B / S-RANK

Эти vectors задают expected outcomes будущей conformance qualification. Это
**typed relational vectors**, не serialized/signature fixtures, native executions
или новые proof results. Outcome names — обозначения документа, не ABI status codes.
Метки B/C/IDs ниже — символы exact исходных objects, не настоящие digest literals;
никакие private keys, подписи или «новые валидные QC» здесь не генерируются.

Общая база: один допущенный context `r`, B в `σ_next`, `b=body_id(B)`;
C_A=(B,q=3,signers=[h1,h2,z]), C_B=(B,q=3,signers=[h2,h3,z]). Для соответствующих
independently authenticated delivered cuts оба witnesses валидны, `c_A≠c_B`,
`b≠c_A`, `b≠c_B`. Original signatures/envelopes каждого cut остаются исходными.
Исходная finalization, если указана, уже durable: round r→b, witness c_A→C_A,
receipt (request_A,c_A,s=3). Root equality alone не заменяет полное равенство B.

| ID | Input / ошибочная операция | Expected outcome и неизменяемое состояние |
|---|---|---|
| ID-N1 c-for-b | При B/C_A передать c_A вместо b в IFQ1.command.body_hash, finalized membership или seed/EC/APC/PARAMETER/ROOT ISC-parent position | `REJECT_IDENTITY_ROLE_MISMATCH`; resolver требует computed b/full B. Никакого append, parent fallback c→b или seed release |
| ID-N2 b-for-c | Передать b вместо c_A в witness lookup, PUBLISH_CERTIFICATE.body_hash или IFR1.c при exact C_A | `REJECT_IDENTITY_ROLE_MISMATCH`; требуется computed c_A. Original receipt/effect и artifact identity не переписываются |
| ID-N3 same-B second-finalization | После durable C_A предъявить валидный C_B того же B и попытаться append второй finalization на s=4 или replace receipt c_A→c_B | `REJECT_SECOND_FINALIZATION` / `REJECT_WITNESS_RELABEL`; p,V и original request/C_A/c_A/s=3 неизменны |
| ID-C3 positive control | Те же C_A/C_B: проверить C_B как alternate witness и запросить уже finalized B | `VALID_ALTERNATE_WITNESS_SAME_CONSENSUS_BODY`; это **не** body conflict. Semantic replay возвращает original result C_A/c_A/s=3 без нового slot; c_B не объявляется c_A. Reject только за c_A≠c_B был бы ошибкой |
| ID-N4 witness-ID collapse | Два exact C_A≠C_B из двух retained source cuts представить как один artifact c_A, потеряв C_B/signers/source | `REJECT_WITNESS_RELABEL`; общий b не разрешает стереть исходную witness multiplicity |
| SQ-N1 original-vote collapse | Два distinct original kind-2 frames actor a в slots 2 и 4 с разными vote identities; candidate projection отображает оба в один public vote u, оставляя cardinality=1 | `REJECT_NONINJECTIVE_VOTE_PROJECTION`; V_a(4)=2. Ни dedup, ни удаление второго record, ни замена count на 1 не разрешены. Это negative projection, не утверждение production reachability произвольной пары |

Общий mixed-WAL control (проверенные исходные frames одного actor):

| Frame kind | s | V_a(s) | Native signed vote sequence | Public vote ordinal |
|---|---:|---:|---:|---:|
| 1 command | 1 | 0 | — | — |
| 2 ISC vote | 2 | 1 | 2 | 1 |
| 3 finalize B with C_A | 3 | 1 | — | — |
| 2 EC vote referencing b | 4 | 2 | 4 | 2 |

| ID | Mixed-WAL mutation / cut | Expected outcome |
|---|---|---|
| SQ-N2 kind-3-as-vote | Для того же 1→2→3→2 заявить V(3)=2 или V(4)=3 | `REJECT_VOTE_COUNT_MISMATCH`; правильные counts 0→1→1→2 |
| SQ-N3 physical-as-public | Заявить public durableSequence[a]=4 на complete prefix length 4 | `REJECT_VOTE_COUNT_MISMATCH`; physical 4 не public 2 |
| SQ-N4 signed renumber | Заменить original EC Vote.durable_sequence=4 на 2 либо original ISC sequence=2 на 1 ради public ordinal | `REJECT_ORIGINAL_SEQUENCE_REWRITE`; original signature/frame/receipt должны остаться byte-identical |
| SQ-N5 replay append | На complete prefix p=4,V=2 повторить finalized B и добавить kind 3 в slot 5, либо вернуть IFR1.s=V(3)=1 | `REJECT_DUPLICATE_APPEND` / `REJECT_PHYSICAL_RECEIPT_MISMATCH`; правильный replay возвращает original IFR1.s=3,c_A, сохраняя p=4,V=2 |
| SQ-C6 surviving unacknowledged control | Crash после complete kind 3, до подтверждённого barrier; independently verified surviving prefix 1→2→3 | После source/floor checks и required barrier: p=3,V=1, receipt s=3,c_A, без append. Следующий новый EC vote получает s=4,V=2 |
| SQ-N7 uncertain/corrupt recovery | При unknown durability объявить p=3,V=1/READY без проверки; либо при torn/corrupt slot 3 пропустить его и принять slot 4 | `BLOCK_READY_UNVERIFIED_PREFIX`; no exposure/renumber/tail repair. Проверенная absence до slot 3 — отдельный контроль, не вывод из timeout |

Vectors являются частью этих двух уже утверждённых решений и будущей новой semantics
closure; они не расширяют DoD и не закрывают R2/R3. Старые raw fixtures и прежние
source-specific evidence не изменяются; документальные controls не выдаются за tests.

## 11. Конечная граница решения и STOP

Утверждённый W1 фиксирует kind 3 и четыре sections, исходные
source/signature dependencies, derived P0→P1 commit, receipt semantics, no-tail-repair
поведение выбранного profile и fail-closed compatibility. Никакой альтернативный
provenance mechanism не предлагается.

Уже существующие вопросы, которые **не закрывает** этот storage contract:

1. **Explicit parent/context binding:** отдельное compatibility/refinement obligation
   из правки пользователя. Наличие parent в local source record его не удовлетворяет;
   новых ISC полей здесь нет. Если его закрытие требует дополнительного certificate change сверх утверждённого I-B — STOP.
2. **Concrete source/authentication authority:** producer/delivery history и закреплённые
   signature codec/keys должны существовать независимо. Source pin содержит opaque
   authentication callbacks и signature IDs, не полное доказательство этого binding.
   Capsule сохраняет evidence, но не создаёт её. Нельзя объявить integration GO,
   подставив fictional signature verifier или structural-only `verify_input_set`.
3. **Representation/storage coverage:** admissible cut должен быть представим в old
   policy/full-state bounds и bounded capsule. Empty close и whole-state bounds не
   объявляются доказанными; корректный oversized/unrepresentable cut требует STOP,
   не silent source-domain narrowing. Это existing compatibility gate, не новый DoD.

I-B/S-RANK и W1 local byte/storage contract утверждены. Для реализации всё равно необходима прямая
команда на следующий ограниченный этап и соблюдение formal-first STOP. Реализация
producer, code/proofs/schemas/fixtures, R2.3/R3, new predicates и recovery не начаты.
**STOP после этого документа.**
