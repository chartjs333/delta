# W1 — parent/context, source/authentication, bounds audit

30 сентября 2026. Existing tasks T053/T016, HR008-002. **Documentary audit / STOP.**

W1 утверждён только как local byte/storage contract. Статусы и cross-references
обновлены сначала, отдельным commit `5c343f2b72fdba5bbac6c06d5bbc89b349827094`;
при заключительной сверке исправлены также две оставшиеся status labels в §1 W1.
I-B/S-RANK и FR-004 Profile A остаются утверждёнными в своих прежних границах.
Ни один из трёх gates не получает PASS по одному лишь одобрению storage format.

Проверены candidate на указанном commit и native reference
`60c692f6e391f839829dfc64e93380db54cd507b`. Путь, Git blob, SHA-256 и диапазоны
источников зафиксированы в [source audit](evidence/0014-w1-three-gate-source-audit.json).
Это анализ существующих контрактов и исходников, не новый predicate, proof layer,
TLC counterexample, выполненный native trace или FormalVerificationReport.

| Gate | Результат |
|---|---|
| Parent/context | **STOP — требуется архитектурное/семантическое решение** |
| Source/authentication | **STOP — требуется архитектурное/семантическое решение** |
| Bounds | **STOP — требуется архитектурное/семантическое решение** |

## 1. Parent/context

Существующее typed `Context` содержит `arithmetic_profile_id`, `height`,
`parameter_schema_id`, `round_config_id`, `round_id`, `validator_epoch_id`, `view`.
`InputSetCertificate` добавляет root, threshold, signers и tuples. Ни typed ISC,
ни canonical JSON, ни закрытая JSON schema не содержат `parent_checkpoint_id`.
`vote_input_set_body_id(B)` хэширует этот context, root и tuples; ISC vote-context
хэширует `round_id`. Наличие parent в отдельном `VoteCandidateBinding` или W1
source bundle не добавляет его в эти ISC bytes.

Verified content-addressed RoundConfig и WorkTickets дают **транзитивную** связь с
parent при обычных hash/verification assumptions. Аудит не утверждает, что два
разных parent могут иметь один проверенный config ID без нарушения этих assumptions.
Однако это не удовлетворяет сохранённому требованию **явной** parent/context binding:
008 FR-001/005/038 требуют parent/full-context/replay binding, а принятая пользователем
правка [Commitment Profile — context binding](0014-isc-commitment-profile-v1.md#profile-identifier-и-binding-к-round-context)
прямо оставляет соответствие ISC schema явному parent требованию незакрытым.
Формулировка рукописи `parent=H_r` была предоставлена пользователем; отдельный
tracked manuscript с этой формулой в этом checkout не найден и не цитируется как файл.

Таким образом, имеющийся контракт не даёт права объявить транзитивность достаточной
для этого gate. Нужно отдельное решение о соответствии существующей transitive
binding требуемой explicit binding либо об изменении byte/schema/semantics contract.
Ни вариант, ни новое поле здесь не выбираются. I-B устраняет b/c неоднозначность
downstream references, но не решает этот вопрос. Изменение production Init/Next
из данного наблюдения само по себе не следует и этим аудитом не разрешается.

Источники: native `contracts.hpp:49–83`, `contracts.cpp:240–275`,
`consensus.cpp:302–319,419–424`; schema `input-set-certificate-v1.json:1–122`;
008 spec FR-001/005/038; Commitment Profile «Profile identifier и binding к round context»; W1 §2.

## 2. Source/authentication

В inspected native certificate path `ValidatorPolicy` содержит epoch, validator IDs
и threshold, но не key registry. `ChainVerifier::validate_signers` проверяет quorum,
порядок, уникальность и membership IDs. `verify_input_set` проверяет context/signers
и вычисляет content ID. `make_vote` проверяет grammar `signature_id`, а не подпись
над original payload. Это полезные structural checks, но не требуемый verifier.

Java `AuthenticatedCertificateTransport` вызывает переданный `Authenticator`.
Это interface `authenticate(peerId, opaqueBytes, authenticationTag)`, не конкретный
ISC signing codec/key/source verifier. Единственное найденное создание этого
transport в inspected tree находится в conformance test и использует условие
`tag.length == 1 && tag[0] == 7`. Peer/TLS authentication также не является
standalone original-voter signature verification для retained history.

В репозитории есть конкретная Ed25519 verification для worker/controller AdmissionRecord
и отдельный benchmark governance path. Они не определяют подпись protocol ISC vote;
утверждённый [Snapshot Provenance Profile §3](0013-snapshot-provenance-profile-v1.md)
прямо запрещает такое заимствование. В нём `signature_codec_id`, key refs и
`producer_rules_id` — необходимые independently pinned inputs, **не готовые
реализации**. Сам профиль фиксирует отсутствие полного key/signature binding.

Минимально отсутствует конкретная утверждённая связь:
original ISC signed payload/preimage ↔ signature bytes/ID ↔ validator key/role/epoch
↔ named offline verifier; для source cut нужен соответствующий independently
qualified native producer verifier. Opaque callbacks, stored booleans и checksum
её не заменяют. Это недостаточность существующего контракта/компонентов, а не
запрос private keys и не утверждение, что в проекте вообще нет криптографии.
Новый algorithm, authority, signing preimage или producer rule не выбирается.

Источники: native `verifier.hpp:26–30`, `verifier.cpp:107–184`;
`AuthenticatedCertificateTransport.java:22–65,114–121` и его conformance test;
008 FR-002/037/040, NFR-004; Snapshot Profile §3–4; W1 §2, §4 IFQ1, §5.

## 3. Bounds

Аудит учитывает **уже выбранные** limits, не предполагает бесконечный source bundle:

| Объект | Existing limit |
|---|---|
| Каждый control document, включая source index | 4 MiB |
| Artifact refs / source events / WAL+pointer records | 65 536 / 1 000 000 / 1 000 000 |
| Суммарно прочитанные source bytes | 64 GiB |
| Каждый P0/P1; canonical ISC | 4 MiB; 4 MiB |
| Полный DRW1 frame; bounded output | 64 MiB; 16 MiB |

Stricter existing per-object/parser limits также сохраняются. В частности,
1 000 000 events — верхний count cap, **не** доказательство того, что миллион
записей с любыми descriptors помещается в 4 MiB source index.

Из уже утверждённого W1 framing точный размер одного frame равен
`72 + |IFQ1| + |IFS1| + |EffectBatch| + |IFR1|` bytes. Для каждого сохранённого
delivery IFQ1 расходует
`28 + |peer_id| + |vote_frame| + |signed_payload| + |signature| + |key_id|` bytes.
IFQ1 сохраняет эти bytes **для каждого** original delivery, включая повторные
доставки; исходный source index может ссылаться на одни original artifact bytes
многократно. Ограничение размера индекса или unique artifact table поэтому не
равно ограничению развёрнутой суммы IFQ1.

Existing transport capacity ограничивает одновременно pending queue: delivery
удаляет entry и освобождает capacity. Аналогично `MaxMessageCopies` в TLA — bound
текущего `messageMultiplicity`, не cumulative delivery count. При разрешённом
DuplicateMessage и MaxMessageCopies ≥ 2 оставшаяся copy допускает повтор
duplicate → deliver другой copy. Это чтение existing actions, **не** новый trace
и не утверждение о конкретном production-importable overflow snapshot.

Чтобы дать PASS для всего утверждённого domain, из существующих source constraints
должны следовать одновременно: полная указанная сумма ≤ 64 MiB, union C/b без
удаления lineage оставляет P1 ≤ 4 MiB, exact original result ≤ 16 MiB.
Такой aggregate binding в inspected contracts отсутствует. В частности, не задан
конкретный protocol signature codec, из которого выводились бы размеры retained
signed payload/signature; нет связи cumulative delivery bytes с W1 frame budget
и нет зарезервированного/выведенного места для полного P0→P1 роста.

**Минимальный остаток этого gate — совместимость полного retained source cut и
его P1/output с тремя существующими byte limits.** Это не дополнительные R2
требования. Gate остаётся STOP: существующий контракт недостаточен, чтобы
объявить whole-domain sufficiency; необходима архитектурная фиксация этой
совместимости, без скрытого уменьшения domain. Аудит не доказывает, что конкретный
валидный snapshot уже переполнил frame, и не выдаёт произведение независимых
maxima за достижимый контрпример. Для PASS нельзя считать domain пустым из-за
отсутствующего authentication verifier. Подвыбор quorum, dedup доставки, удаление
lineage, новый admission cap или смена encoding здесь не допускаются и не выбираются.

Источники: Snapshot Profile §3, §5 (resource caps); W1 §3–4 и §5;
native `wal.cpp:35–43`, `vote_codec.hpp:14–26`, `sidecar_protocol.hpp:21–28`;
Java transport `offer/deliverReady`; TLA `DuplicateMessage` / `DeliverVoteEnvelope`.

## Stop boundary

Новых решений по трём STOP не принято. W1 local approval сохраняется.
Production C++, ABI, Java, sidecar, schemas, proofs, fixtures и runtime не менялись;
R2.3/R3 не начаты; production Init/Next и old objects/signatures/QC/WAL не изменены.
Новая semantics version/hash не назначена. R1/R2.1/R2.2 остаются CLOSED;
R2.3/R2 остаются OPEN. Автоматического продолжения после этого отчёта нет.
