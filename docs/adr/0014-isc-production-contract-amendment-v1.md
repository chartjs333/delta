# ISC production contract amendment v1

**DRAFT — одна консолидированная спецификация выбранных P-EXPLICIT,
SIG-ISC-ED25519-v1 и ISC-EVIDENCE-BUDGET-v1. Не разрешение на реализацию.**

30 сентября 2026. Existing tasks T053/T016, HR008-001/002/003/018.
Пользователь выбрал три направления для дальнейшей спецификации. Точные новые
encodings, численные budgets и integration consequences ниже представлены на
утверждение этим amendment; они не объявляются уже реализованными или прошедшими GO.
W1 сохраняет **APPROVED as local byte/storage contract**. Producer Integration
остаётся заблокированным. Это один контракт входов и перехода ISC, не три proof layers.

Источник: candidate `2a0e68375ca070eac391dbb6c8d3b980b972888e`, native reference
`60c692f6e391f839829dfc64e93380db54cd507b`.
См. [предыдущий audit](0014-w1-three-gate-audit.md),
[W1](0014-isc-finalization-wal-capsule-v1.md),
[Producer Integration](0014-isc-producer-integration-v1.md),
[I-B/S-RANK](0014-isc-identity-sequence-amendment.md).
Точные source blobs и документальные расчёты сохранены в
[inventory](evidence/0014-isc-production-contract-amendment-source-audit.json).

## 1. Version и identity boundary

`σ` ниже — будущий независимо закреплённый `formal_semantics_id`, всегда 71 ASCII
byte `sha256:` + 64 lowercase hex. Значение **не назначено**. Запись `σ_next` не
может попасть в реальные bytes. Для нового ISC C и ISC Vote предлагается отдельный
schema dispatch `schema_version="2.0.0"`; это proposed schema revision, не значение σ.
Старые readers/writers и evidence не получают поддержку нового контракта автоматически.

- `B/b` — ISC consensus body / его ID; `C/c` — exact signer-dependent witness / ID.
- `V/v` — canonical ISC Vote / vote ID; `G/g` — detached signature artifact / его ID.
- `s` — original sender physical WAL slot; `V_a(s)` — original kind-2 vote ordinal/count.

Ни c вместо b, ни signature artifact g вместо vote v не допускаются. Original old
objects/signatures/QC/WAL сохраняются byte-for-byte под старым decoder/profile.
Миграции, relabel, повторного голосования в уже защищённом context или сброса
sequence этим amendment не разрешается. Fresh unenrolled node, epoch change,
rollback/compromise T и сетевой bootstrap остаются вне выбранного profile.

## 2. P-EXPLICIT: поля и canonical body/certificate

Новый обязательный member **`parent_checkpoint_id : ContentId`** добавляется только
в `VoteInputSetBody` и `InputSetCertificate`. Общий семипольный `certificates::Context`
не расширяется для всех остальных certificate types. B и C имеют собственное поле
parent; `body(C)` переносит его без lookup или синтеза из configuration.

Проверяется равенство B.parent = C.parent = parent исходного finalized RoundConfig
= parent каждого original WorkTicket = parent independently admitted round source.
Проверка относится к исходному round/cut, а не требует равенства старого ISC самому
новому current после последующих ApplyQC. Ошибка любого равенства закрывает admission.
Context/config/schema/arithmetic/epoch/height/view checks сохраняются целиком.

Обозначения bytes: `U16/U32/U64` — unsigned big-endian; `T8(x)=U64(|ASCII(x)|)||ASCII(x)`;
`L(x)=U32(|x|)||x`; `T4(x)=L(ASCII(x))`; `ID(d,x)="sha256:"||hex(SHA256(ASCII(d)||00||x))`.
Никаких padding, locale conversion, host structs, implicit terminators или trailing bytes.

Полный canonical preimage B задаётся так, используя existing hash helpers и tuple order:

```text
PB = T8(σ) || T8("2.0.0")
   || T8(arithmetic_profile_id) || U64(height)
   || T8(parameter_schema_id) || T8(round_config_id)
   || T8(round_id) || T8(validator_epoch_id) || U64(view)
   || T8(parent_checkpoint_id) || T8(input_root) || U64(tuple_count)
   || for each original ordered tuple:
        T8(availability_certificate_id) || T8(commitment_id)
        || T8(domain_id) || T8(ticket_id)
b = ID("deltareduce.vote.input-set-body.v2", PB)
```

Это новый hash contract, не вызов старого `vote_input_set_body_id` с незаметно
изменённым layout. Все original tuple identities и FR-004 root construction
сохраняются. Parent непосредственно входит в B bytes; подпись V аутентифицирует
этот B через b. Одной транзитивной ссылки на RoundConfig больше недостаточно.

Canonical C JSON использует existing ASCII/strict-order/number rules и ровно keys
в следующем порядке (duplicate member, unknown/missing member — reject до typed parse):

```text
arithmetic_profile_id, formal_semantics_id, height, input_root,
parameter_schema_id, parent_checkpoint_id, quorum_threshold,
round_config_id, round_id, schema_version, signer_ids, tuples,
type_name, validator_epoch_id, view
```

`formal_semantics_id=σ`, `schema_version="2.0.0"`,
`type_name="INPUT_SET_CERTIFICATE"`; height/view/quorum — canonical unsigned decimal
JSON numbers; IDs — quoted ASCII; signers — sorted unique original IDs;
tuples — exact approved J(t) array. No whitespace/BOM/newline/escape alternatives.
`c=ID("deltareduce.008.input-set-certificate.v2", J(C))`.
Quorum в выбранном deployment остаётся 3 из 4; C содержит весь matching delivered
signer set своего cut (3 или 4), не выбранный first-q subset.

Existing round-scoped ISC vote-context rule сохраняется. Parent **не** добавляется
в anti-equivocation key так, чтобы позволить одному honest signer голосовать за два
parents того же round. Разные B, включая разные parent, конфликтуют в прежнем
защищённом round context. Seed и downstream ISC references по I-B используют новый b.

## 3. SIG-ISC-ED25519-v1: exact Vote и устранение self-reference

Нельзя одновременно определять `signature_id` как hash подписи и подписывать полный
старый Vote, уже содержащий этот ID: получится круговая зависимость. **Предлагаемое
явное изменение нового ISC Vote:** удалить `signature_id` из signable V и хранить
signature artifact отдельно. Это не маскирование/обнуление поля старого Vote и не
переименование signature ID в key ID. Изменение требует утверждения этого amendment.

V переиспользует DRC1 encoding и type code 3 (`VOTE`), с новым schema/semantics/kind
dispatch. Ровно 12 keys, в порядке ASCII:

```text
body_hash, context_id, durable_sequence, formal_semantics_id, height,
kind, round_id, schema_version, type_name, validator_epoch_id, validator_id, view
```

Все values — DRC1 text. `body_hash=b`, `kind="ISC"`, `type_name="VOTE"`,
`schema_version="2.0.0"`, `formal_semantics_id=σ`; height/view/sequence — decimal
strings без leading zero, sequence > 0 и равен original physical slot s. Остальные
ASCII labels ограничены 1–128 bytes и `[A-Za-z0-9._:-]`; content IDs — ровно 71 bytes.
Существующий context_id вычисляется native round-context function, не caller.

```text
Txt(x) = 21(hex) || U32(|ASCII(x)|) || ASCII(x)
payload = 31(hex) || U32(12) || concatenation(Txt(key) || Txt(value))
V = ASCII("DRC1") || 01 00 || U16(3) || U32(|payload|) || payload
v = ID("deltareduce:003:vote:v2", V)
```

Верификация требует exact canonical re-encoding = input V. Это новые ISC bytes;
другие vote kinds не получают новый signing profile автоматически. Их existing
authority obligations остаются, но Ed25519/preimage для EC/APC/Apply здесь не проектируется.

## 4. Independently provisioned epoch registry

Authority остаётся existing independently retained bootstrap на T. Snapshot, G,
certificate или TLS peer не выбирают public keys. Для одного fixed epoch предлагается
следующий closed registry R; он детерминированно собирается из trusted bootstrap,
закреплённого signature profile и fixed budget object §6, а не из imported snapshot:

| Field R | Exact value / source |
|---|---|
| `evidence_budget_id` | Content ID fixed object E из §6 |
| `formal_semantics_id` | σ из независимо закреплённого bootstrap/build |
| `origin_id` | Exact bootstrap origin, existing ASCII label |
| `quorum_threshold` | String `"3"`, equals bootstrap/RoundConfig policy |
| `schema_version` | `"1.0.0"` для этого registry object |
| `signature_profile` | `"SIG-ISC-ED25519-v1"` |
| `validator_epoch_id` | Exact existing epoch ID, не переопределяется как hash R |
| `validators` | Четыре entries sorted by original validator_id: `{key_ref,roles,validator_id}`; role list для этой ISC projection ровно `["validator"]` |

`key_ref` переиспользует bootstrap key reference. В этом profile он указывает на
closed canonical KeyDescriptor K с keys `algorithm, public_key_hex, schema_version`:
values `"Ed25519"`, ровно 64 lowercase hex chars public key, `"1.0.0"`.
`key_id=key_ref=ID("deltareduce.isc-ed25519-key.v1", J(K))`.
Registry ID `r=ID("deltareduce.isc-epoch-registry.v1", J(R))`.

J для новых control objects — existing provenance-profile canonical JSON: sorted
keys, ASCII без quote/backslash в значениях, no whitespace/BOM/newline, integer
values представлены decimal strings. Unknown/duplicate members запрещены. Schema
включает ровно перечисленные fields; R/K/E не содержат собственный ID. Public keys
32 bytes; один key на validator/epoch, разные validators не могут иметь один public
key. Wrong role/epoch, duplicate IDs/keys, unavailable key_ref или mismatch между
R и independently trusted bootstrap — reject. Registry не может делегировать trust
сам себе своей подписью. R/K/E — config artifacts, **не новый certificate protocol**.

Новых bootstrap wire fields не требуется: validator IDs/key_ref/roles/q/origin/epoch
уже существуют; σ/codec/producer/build pins выбираются независимо. `signature_codec_id`
и `producer_rules_id` должны указывать на будущие квалифицированные manifests,
закрепляющие ровно этот profile/encoding/E, а не на arbitrary plugin. Их hashes сейчас
не назначаются. R/E хранятся на T как воспроизводимые artifacts; checker дополнительно
проверяет derivation от trusted inputs. Бюджеты одинаковы для всех четырёх validators.

## 5. Signature preimage, artifact и verification

```text
M = ASCII("deltareduce.isc-vote.ed25519.v1") || 00
    || T4(r) || T4(key_id) || L(V)
sig = Ed25519.Sign(secret_key, M)                    // ровно 64 raw bytes
G = ASCII("ISG1") || U16(1) || U16(0)
    || T4(r) || T4(key_id) || L(V) || sig
g = ID("deltareduce.isc-signature.v1", G)
```

Подписывается **весь M с exact V**, не только b, digest V, JSON adaptation или
V с обнулёнными/исключёнными при проверке полями. Используется pure Ed25519,
не Ed25519ph/ctx и не application-level SHA256 prehash. Domain separation находится
в M. Это профиль поверх [RFC 8032 §5.1](https://www.rfc-editor.org/rfc/rfc8032.html#section-5.1);
структура primitive и размер подписи берутся из RFC, не из нового алгоритма.

Для будущей native реализации выбран конкретный путь: qualified build
[libsodium 1.0.22](https://github.com/jedisct1/libsodium/releases/tag/1.0.22-RELEASE),
single-part `crypto_sign_detached` / `crypto_sign_verify_detached`, deterministic
build без `ED25519_NONDETERMINISTIC`. Его exact source/build digest необходимо
квалифицировать до deployment; зависимости сейчас не устанавливаются.
Single-part и multipart APIs используют разные варианты — это не взаимозаменяемый
fallback. [Официальный контракт API](https://doc.libsodium.org/public-key_cryptography/public-key_signatures).

Конечная verification procedure для G:

1. Проверить outer lengths/version, V ≤4096 bytes, sig ровно 64 bytes; malformed
   encoding не нормализуется. Прочитать r/key_id/V и проверить hash g, если он задан
   source ref; g сам по себе не подтверждает подпись.
2. r должен равняться R, независимо восстановленному по §4. Resolve key_id именно
   для V.validator_id, того же epoch и ISC role. Public key не берётся из G/TLS.
3. Decode V по точным 12 fields/versions/kind; проверить original s и контекст;
   проверить PB, b, explicit parent/config/ticket association из §2. При offline
   проверке s подтверждается original source/journal lineage, не slot получателя.
4. Построить exact M. Public key A и Rpoint=первые 32 bytes sig должны быть canonical
   nonidentity points prime-order subgroup; S=последние 32 bytes sig — little-endian
   integer < L. Затем проверить Ed25519 signature. Для point checks используются
   `crypto_core_ed25519_is_valid_point(A/Rpoint)` из выбранной версии; версия ≤1.0.20
   не считается эквивалентной: official docs описывают ошибку subgroup check в старых
   версиях. [Point-validation contract](https://doc.libsodium.org/advanced/point-arithmetic).
5. Только после crypto success original V может участвовать в grouping/quorum.
   Полный context/B должны совпадать. Signers считаются по distinct original
   validator IDs; repeated deliveries или разные signatures одного V quorum не увеличивают.

Нет fallback через signature_id, structural validation, authenticationTag, TLS
или supplied boolean. Signature не доказывает producer legality/remote fsync:
полный source verifier всё ещё проверяет existing native producer/dependency lineage.
ISC profile не аутентифицирует заодно ApplyQC/остальной graph. Для их provenance
остаются прежние independently qualified inputs; отсутствующий verifier закрывает READY.

## 6. ISC-EVIDENCE-BUDGET-v1: фиксированные budgets

E — один closed control object, canonical J из §4. Он содержит
`profile_id="ISC-EVIDENCE-BUDGET-v1"`, `schema_version="1.0.0"`,
`formal_semantics_id=σ` и **все** следующие fields с указанными decimal-string values.
`e=ID("deltareduce.isc-evidence-budget.v1", J(E))`; e входит в R и тем самым M.
Эти конкретные числа — предлагаемые значения amendment, не измеренная ёмкость.

| Field | Decimal value | Meaning |
|---|---:|---|
| `max_delivery_events` | 4096 | Cumulative original admitted ISC delivery events одного round |
| `max_delivery_bytes` | 33554432 | Сумма exact W1 delivery entries, включая framing и все repeats |
| `max_vote_bytes` | 4096 | Exact signable DRC1 V |
| `max_vote_frame_bytes` | 4096 | Original kind-2 frame V |
| `max_signature_artifact_bytes` | 4322 | Exact G: 226 + len(V) |
| `max_signed_payload_bytes` | 4282 | Exact M: 186 + len(V) |
| `max_peer_id_bytes` | 128 | Existing original peer label |
| `signature_bytes` | 64 | Exact size, не только upper bound |
| `key_id_bytes` | 71 | Exact content ID size |
| `max_command_bytes` | 65536 | Exact finalization Command |
| `max_round_state_bytes` | 65536 | Exact S0 |
| `max_policy_bytes` | 4194304 | Каждый полный P0 и P1 |
| `max_isc_bytes` | 4194304 | Exact J(C) |
| `max_effect_bytes` | 1048576 | Exact W1 EffectBatch |
| `max_wal_frame_bytes` | 67108864 | Existing full DRW1 ceiling |
| `max_output_bytes` | 16777216 | Existing result ceiling |
| `max_result_metadata_bytes` | 8192 | Metadata вне Result в bounded transport response |

Counters принадлежат одному native receiving actor/handle и привязаны к
`(origin, epoch, round_id)` и полному его исходному prefix/cut. Это не общий
расходуемый счётчик четырёх узлов; local actor не выбирается envelope. Они
не сбрасываются при другом body, witness, view, retry, snapshot или restart того же
round. Все source-admitted ISC deliveries этого round учитываются, включая repeats
и conflicting context/body evidence. Изменение counter key ради обхода cap запрещено.
Старые profile caps 4 MiB control document / 65536 refs / 64 GiB bundle / 1000000
events/records тоже остаются; одно ограничение не отменяет другое.

**Новая admission граница явная.** Перед production delivery admission вычисляются
будущие N/D на текущем native source prefix и проверяются N≤4096, D≤33554432.
Если не помещается, envelope не становится admitted protocol delivery, счётчики
не увеличиваются, новый WAL/effect не создаётся; native возвращает отказ/backpressure.
Пакет, отвергнутый до admission, не объявляется delivered source event задним числом.
Любой event, уже присутствующий в проверяемой original history, нельзя выкинуть под
этим предлогом: oversized imported history целиком fail closed. Exact retry одного
и того же source event не новый event; новая доставка тех же bytes — новый event.

Это **сознательное сужение будущего source/admission domain**, выбранное пользователем,
а не доказательство вместимости всего прежнего profile domain. Все ранее admitted
votes/events/lineage сохраняются. Для текущего cut finalization отдельно проверяет
exact P0/P1/C/Command/S0/E/result sizes; если P1 union не помещается, прежнее состояние
и prefix остаются, а finalization не append. Свободное место нельзя получить удалением
старого certificate, witness, ABORT lineage или replacement snapshot.

Budgets фиксируются до round через independently provisioned R/E/σ, не выбираются
caller/capsule и не поднимаются после неудачи. Single writer связывает size check
с тем же cut, который append: TOCTOU между измерением и bytes исключается. Расчёты
размеров используют checked integer arithmetic; allocation/truncation/overflow не
подменяют отказ. После crash counters выводятся из полной verified original source
history; недоступный prefix не считается пустым. Новый per-delivery WAL kind этим
текстом не вводится; durable source-event binding — обязанность уже выбранной интеграции.

## 7. Exact sufficiency calculation и влияние на W1

Approved outer DRW1 framing и IFQ1/IFS1/IFR1 layouts не меняются. В новом profile
`original_vote_frame=V`, `original_signed_payload=M`, `original_signature_bytes=sig`,
`original_key_id=key_id`. Все дубли bytes проверяются на equality; это не дополнительная
независимая подпись и не повод удалить повтор. r извлекается из M и сверяется с R; exact G восстанавливается из V/r/key_id/sig
и должен совпасть с original source artifact, включая его g.
Parent входит в C и исходный B/policy. Original source_index/cut должен ссылаться
на retained R/E/K, исходный delivered G и остальные dependencies.

Для n entries, f_i=|V_i|, m_i=|M_i|, p_i=|peer_i|, k_i=71:

```text
d_i = 28 + p_i + f_i + m_i + 64 + k_i
D   = sum(d_i for every original admitted delivery i, in original order)
Q   = |IFQ1| = 76 + |Command| + 71 + |S0| + |P0| + D
S   = |IFS1| = 16 + |P1| + |J(C)|
Rcp = |IFR1| = 156 + 71 + 71 + 71 = 369
W   = 72 + Q + S + |EffectBatch| + Rcp
```

Здесь 71 в Q — source_index_id; receipt содержит три exact content IDs.
Композиция caps §6 даёт:

```text
W ≤ 604 + 2*65536 + 3*4194304 + 33554432 + 1048576
  = 47317596 bytes < 67108864 bytes.
```

4096 — не заменитель byte budget: обе проверки обязательны. Signer count также
не заменяет delivery count. Размеры всех sections включают framing, а upper bound
не предполагает, что каждый independent maximum одновременно достижим.

Чтобы output limit также имел точный смысл, предлагается закончить ранее не
зафиксированный dedicated result codec W1 минимальной последовательностью:

```text
Result = L(IFR1) || L(EffectBatch) || L(J(C))
O = 12 + 369 + |EffectBatch| + |J(C)|
  ≤ 5243261 bytes < 16777216 bytes.
```

Нет нового receipt ID, signature, sequence или consensus effect. IFR1 уже имеет
versioned header; endpoint/capability определяет тип result. Transport replay flag
остаётся вне этих bytes; ABI/sidecar response metadata учитывается отдельно в
existing 8 KiB metadata allowance, не в O. Тогда logical response ≤5251453 bytes
< existing 16785408-byte limit; с existing 128-byte IPC header ≤5251581 bytes
<16785536. Future wrapper обязан проверить и эти exact totals; wrapper не может
добавлять безразмерные fields или скрывать дополнительные bytes вне metadata budget.

Это конечный **документальный** size argument при указанных admission premises,
не выполненный Lean proof или compatibility test. P1≤4 MiB — явная pre-append
проверка полной generation, а не следствие одного P0≤4 MiB. Runtime checker обязан
пересчитать exact W/O на реально сериализованных bytes даже при наличии upper bound.

## 8. Durable vote storage и Producer Integration

**FR-003 требует durable vote intent до signing/transmitting**, а не только
barrier перед отправкой. Поэтому kind 2 хранит **exact V**, не G, и предшествует
вызову signing primitive. Меняется schema самого будущего ISC V, но original
DRW1 framing/kind/physical-slot meaning сохраняются. Старый 13-field DRC1 Vote
не reinterpret как новый 12-field Vote. Reader выбирает codec по независимо
закреплённому σ/schema/capability; unknown/mixed format fail closed.

Один конечный local vote path:

1. Validate original context/B/registry; single writer выбирает s=next physical slot,
   создаёт V/v и anti-equivocation intent. Append kind-2 V → barrier → commit intent.
   До этого signing primitive не вызывается. Unknown append/barrier блокирует writer;
   s нельзя переиспользовать, пока prefix не восстановлен однозначно.
2. Только от committed intent построить M и детерминированно получить sig/G/g.
   Verify собственный output тем же verifier. Без готовых ключей/верификатора intent
   сохраняется pending; нет outbound effect, нового vote или обхода guard.
3. Сохранить G как immutable original signature artifact в existing content-addressed
   store на T **по g**, с original source association к committed V/v/s. Имя — locator,
   не authority; contents проверяются на V/v/r/key_id/sig/g. Write bounded temporary
   file → file durability barrier → atomic no-replace installation → directory
   barrier; original source/artifact refs также должны быть durable до exposure.
   Существующий different artifact не перезаписывать. Это local effect materialization
   в retained store, **не новый certificate, consensus journal kind, physical WAL slot
   или второй голос**. Derived v→g cache не становится authority: после crash он
   восстанавливается из retained original source refs и проверенных G, в пределах
   существующих source-scan bounds. Missing/ambiguous association закрывает exposure.
4. Только после обеих durability границ вернуть sendable canonical G. Java передаёт
   его opaque; receipt/source различают original vote v и signature artifact g.

Это уточнение existing retained signature/source storage, а не обещание, что оно уже
реализовано. Atomic artifact installation и association с original kind-2 intent
требуют qualification в той же интеграции. Private key остаётся в native signing
custody, не в artifact G и не в Java/WAL. Source refs/registry не могут подменить ключ.

Crash после intent barrier, но до завершения artifact materialization, сохраняет
pending original V/s: разрешено закончить **этот же** intent, без нового WAL record,
нового context или другой подписи/encoding. До exposure deterministic signing может
повторить вычисление exact M; это не повторное голосование. Intact committed G
возвращается byte-for-byte и не пересигнивается. Если source/commit свидетельствует
о готовом G, а original artifact отсутствует или повреждён, READY закрыт: его нельзя
заменить newly generated bytes. Crash при ambiguous artifact installation требует
проверки surviving exact artifact и barriers до exposure. Никакой lost/torn evidence
не объявляется пустым. Trusted-volume rollback/compromise остаётся вне profile.

`vote_id=v` вычисляется из V, `signature_id=g` относится к detached artifact/source
metadata. Existing receipt frame binding сохраняет exact V; новый sendable G
проверяемо связан с ним, а не хэшируется как old V. Original records с различными
actor/s/context не схлопываются. Новая доставка V/G не создаёт local kind-2 record.
Возможные разные valid signature artifacts одного V сохраняются как evidence, не
увеличивают quorum и не заменяют already committed local G; crypto uniqueness не
предполагается. Replay готового результата сохраняет V/G/v/g/s.

Finalization остаётся одним W1 kind 3:
validate authenticated complete cut + explicit parent + exact budget/sizes
→ append → barrier → commit full P1/index → expose original C/result.
S-RANK: kind 2 увеличивает s/V_a, kind 3 — только s; mixed 1→2→3→2 сохраняет
original signed slots 2/4 и public counts 0/1/1/2. Seed закрыт до committed durable b.

P0/P1 не могут использовать старый policy decoder, который не читает explicit
B/C parent. Предлагается следующий native policy codec `DVPOL002` с добавлением
parent после existing Context каждого ISC body/certificate; other serialized fields
и full collections сохраняются. Magic/version switch и exact ID/hash/size проверяются
по independently pinned new codec. `DVPOL001` остаётся immutable legacy baseline.

## 9. Compatibility и liveness consequences

| Объект/claim | Последствие будущего amendment |
|---|---|
| B/b | Direct parent + schema/σ + v2 hash domain дают новые bytes/ID. Old B нельзя «дополнить» parent и оставить old b |
| C/c | Новый parent/schema/σ/domain дают новый witness ID; исходные signer identities сохраняются. Несколько C одного B допустимы по I-B, не второй finalized B |
| Votes/signatures | Новый V без signature_id; exact detached preimage/G. Старые signatures не проверяют новые bytes и не пересчитываются для миграции |
| Generic QC / downstream | Existing QC ID recipe/type concept не подменяется, но новые vote IDs, ISC b и downstream parent-bound bodies дают другие QC IDs/bytes. Старые EC/APC/ROOT/Apply объекты не relabel |
| WAL | Old frames/checksums/payloads/slots неизменны. Новые kind-2 V и kind-3 W1 квалифицируются отдельно; G хранится в retained store после intent barrier. Новый V меняет future payload/checksum, не смысл s или V_a(s) |
| FR-004 roots | Ordered tuples/J(t)/Merkle unchanged; V1–V5 roots остаются историческими arithmetic vectors. Old full ISC IDs/fixtures не становятся новыми C |
| Formal semantics | **SEMANTIC_CHANGE**, не прежний `REFINEMENT_ONLY`: explicit record field, authenticated Vote format и bounded admission требуют feature-000 qualification, new dependency closure и будущей σ. Сейчас σ не назначается |
| Arrival cuts / liveness | В пределах budget разные arrival cuts могут дать разные C/c и общий b; это прежний I-B. Но duplicates/conflicts могут исчерпать N/D раньше полезного quorum. Без budget-availability premise прежняя liveness не переносится |

Нет обещания, что выбранные caps обеспечивают progress при любом Byzantine delivery
schedule. Предлагаемый liveness claim условен: допустимый authenticated quorum и
его полный source cut успевают пройти existing deadline, event/byte budgets и
whole-P1/output checks. При истощении — fail closed/backpressure, без нового ABORT
reason/terminal, pruning или автоматического увеличения caps. Existing hard-deadline
behavior само по себе не доказывает успешную ISC finalization. Если продукт требует
сильнее unconditional liveness, этот amendment её не предоставляет; quotas/reserve
policy не проектируются автоматически.

Полный source-history legality не следует из подписи. Frozen R1/R2.1/R2.2 остаются
CLOSED для принятых statements; эта новая version не наследует их qualification
по умолчанию. R2.3/R3 не продолжаются и не закрываются документом.

## 10. Единый finite qualification и implementation footprint

Это перечень обязанностей одной ISC integration после отдельного разрешения,
не начало работ и не три новых слоя доказательств. Existing files относятся к
зафиксированным pins; новые версии ниже ещё не созданы.

| Area | Existing files / required delta |
|---|---|
| Production TLA data/parent | `formal/tla/DeltaReduceTypes.tla` (`InputSetBodies`), `DeltaReduceCertificates.tla` (`InputBody`, `CloseInput`, `VoteISC`, `FinalizeISC`, `GenerateSeed`): explicit parent с equality к config/source; проверить сохранение `CertificateVoteUniqueness`, `CertificateQCUniqueness`, `ValidCertificateQuorums`, `SeedAfterInputFreeze` и downstream parentage |
| Production TLA bounds | `DeltaReduceTypes.tla`, `DeltaReduceQuorums.tla` (`SendVoteEnvelope`, `DeliverVoteEnvelope`), `DeltaReduceFailures.tla` (`DuplicateMessage`), `DeltaReduce.tla`: cumulative admitted ISC event/byte budget и complete-cut finalization readiness должны быть отражены в модели. При выбранном model-visible budget accounting Init инициализирует counters, Next delivery/finalization guards меняются. Старое обещание unchanged Init/Next в Integration ADR к этому amendment не применимо; текущие файлы не меняются |
| Public state/trace | `DeltaReducePublicState.tla`, `DeltaReduceRefinement.tla`, `formal/scripts/check-refinement.py`: exact parent и budget/event association, никаких отброшенных deliveries. Transport pre-admission rejects не маскировать под successful public Deliver. Liveness premises и bounded-state configurations квалифицировать с новым domain |
| Lean bytes/binding | `formal/proofs/DeltaReduce/NativeInputSetBody.lean`; `NativeIscCertificate.lean` (`valueRead`, `checkedContext`, `checkedBody`, `checkedQuorum`, `bodyIgnoresSigners`, `bytesSource`); `NativeIscAdmission.lean` (`bindSource`, `prepareSource`, `fromBytesSource`, `sequencePreserved`): new version branches для explicit parent и authenticated B/V/C association, original signer/state preservation |
| Lean Vote/storage | `NativeVoteBytes.lean` (`WireVote`, `fields`, `readFrameEncoded`, `wireEncodingInjective`, `votePreimage`, `bindReceipt`); `NativePolicyBytes.lean`, `NativePolicyCodec.lean`, `NativeWalBytes.lean`, `NativeWalScan.lean`, `NativeVoteCache.lean`, `NativeConfigReplay.lean`, `NativeWholeReplay.lean`: V/G distinction, intent-before-sign и artifact-before-expose, version dispatch, exact size arithmetic, full W1 and S-RANK/replay. Existing generic encoding lemmas may be reused only under their existing hypotheses |
| Cryptographic boundary | Named Ed25519/hash assumptions remain explicit; Lean structural signer proof is not a proof of unforgeability or of libsodium binary. Qualify exact library build, strict verify wrapper, key/role/epoch association and cross-language byte/signature acceptance independently of caller booleans, within this integration gate |
| Schemas | Versioned successors of `delta-protocol/schemas/008/input-set-certificate-v1.json`, `003/protocol-types-v1.json`, `003/hash-domains-v1.json`, `003/canonical-binary-v1.md`; closed definitions for R/K/E/G and result; native policy version/ABI capabilities. Do not overwrite legacy schema meaning or existing fixtures |
| C++ core | `delta-core-cpp/include/delta/certificates/contracts.hpp`, `src/certificates/contracts.cpp`, `src/certificates/verifier.cpp`, `src/certificates/vote_admission.cpp`, `include/delta/core/consensus.hpp`, `src/consensus.cpp`, `src/protocol.cpp`: parent, new hash/codec dispatch, pure signature verification and complete-cut grouping/budget plan; planned ISC producer from Integration ADR |
| Native runtime | `delta-runtime-cpp/src/runtime.cpp`, `src/certificate_runtime.cpp`, `src/wal.cpp`, `src/wal.hpp`, `src/vote_codec.cpp` and existing public runtime headers: native key custody/bounded inputs, V persist-before-sign/G persist-before-expose, source counter reconstruction, W1 atomic generation/index/result, strict size/failure/replay paths |
| ABI/transport | `delta-ffi/include/delta_abi.h`, `src/delta_abi.cpp`, `src/certificates_abi.cpp`; sidecar protocol/server and Java `AuthenticatedCertificateTransport`/native adapter: bounded opaque G/result, exact capability/version rejection, no Java authority |
| Evidence | Existing 003/008 fixtures and `formal/proposals/evidence/native-isc-*`, `native-wal-*`, `native-vote-cache`, `native-whole-replay`, `b-family-constructors` remain old-source evidence. New exact vectors must cover parent mismatch, modified byte/domain/key/epoch, bad signature/point/scalar, budget ±1, complete duplicate inventory, P1 overflow, crash cuts, mixed 1→2→3→2, original-result replay and two C for B |

Public budget counters guard admission, но original delivery records не превращаются
в новые votes/certificates/coordinates. Budget exhaustion и parent/auth failures
не могут превращаться в GO или synthetic quorum. Сначала feature-000 qualification
затронутого контракта; runtime implementation — только после separately authorized
task и exact compatible merged FormalVerificationReport(GO). Этот документ не даёт GO.

## 11. Обновлённая оценка интеграции

Условная оценка **70–116 активных часов** после утверждения exact amendment и при
наличии independently provisioned artifacts. Она заменяет прежнюю rough 50–84h
оценку только для планирования этой integration, не является execution budget.

| Работа в едином scope | Активные часы |
|---|---:|
| New parent/V/G/R/K/E byte contracts, versioned schemas и exact vectors | 8–14 |
| Совместная feature-000 TLA/Lean/compatibility qualification и budget liveness boundary | 20–32 |
| Native crypto binding и pure ISC producer | 10–16 |
| V/G/W1 policy generations, durability/index/replay/size admission | 14–24 |
| Bounded ABI/FFM/sidecar/Java forwarding | 4–8 |
| Crash/authentication/bounds integration evidence и source-specific requalification | 14–22 |
| **Всего** | **70–116** |

Рост связан с явным parent/hash change, detached Vote/G и kind-2 intent/effect binding, конкретной
crypto/key boundary, двух durability границ signing effect и admission semantics. Не включены ожидание approval/merged GO,
внешние независимые attestations, реальное key provisioning, полный provenance
import/recovery, closure R2.3/R3 или Formal GO в целом. Обнаружение несовместимого
existing source producer не покрывается обещанием «исправить в этом интервале»:
это отдельный STOP, а не автоматическое расширение scope.

## 12. Checkpoint

Для review особенно существенны предложенные детали: удаление signature_id из
нового signable ISC V с переносом в detached artifact identity; kind-2 intent
до signing и retained G до exposure; concrete budget values и conscious domain/liveness restriction; semantic
model changes вместо старого unchanged-Init/Next обещания. Они явно описаны,
а не скрыты как implementation detail уже approved W1.

**STOP после documentary amendment.** Никаких code/schema/proof/fixture changes,
production recovery, R2.3/R3, нового semantics ID или автоматической реализации.
Старые objects/signatures/QC/WAL и frozen evidence остаются неизменными.
