# ISC Commitment Profile v1

**Decision document к ADR-0014. Статус: APPROVED для конкретизации FR-004, variant A.**

Утверждение пользователя от 30 сентября 2026 было обусловлено двумя обязательными
правками; обе внесены: duplicate JSON member rejection и отсутствие утверждения
о достаточности parent binding. Это утверждение byte-level контракта, не реализации.

30 сентября 2026. Scope: только конкретизация существующего feature-008
FR-004/FR-005. Код, proofs, schemas и production fixtures не изменяются.
R2.3/R3 не продолжаются. Оценка 50–84 часа не утверждена и здесь не используется
как бюджет. `ISC Finalization WAL Capsule v1` утверждён отдельно как local
byte/storage contract, без разрешения implementation. I-B/S-RANK утверждены отдельно; их terminology/compatibility amendment
ниже не меняет tuple/tree FR-004 contract или V1–V5/N11 vectors.

Исходники: candidate `bc2c6df6dcb2402a919b1052526958af2ef27182`, native reference
`60c692f6e391f839829dfc64e93380db54cd507b`. Последний — source pin, не Formal GO.
[Инвентаризация источников и проверок документа](evidence/0014-isc-commitment-profile-v1-source-audit.json).
Инвентаризация сохраняет hashes исходной редакции; текущий terminology/compatibility
amendment фиксируется отдельным Git commit, без изменения нормативных root vectors.

## Утверждённое решение и рассмотренные альтернативы

Утверждённый минимальный профиль — **A**: существующие canonical
JSON bytes одного `InputTuple`, отдельный ISC leaf domain и существующее дерево
`delta::shards::merkle_root`. Новые поля в tuple, ISC, RoundConfig, vote или WAL
не добавляются. Leaf digest — вычисляемое промежуточное значение, не новый
certificate, protocol object, signer identity или журналируемый vote.

| Вариант | Конкретный выбор | Причины и compatibility consequences |
|---|---|---|
| **A — утверждён для FR-004** | Existing tuple JSON; новый leaf domain; existing `deltareduce.004.merkle-node.v1`; duplicate-last на каждом нечётном уровне | Переиспользует существующие tuple bytes и Merkle helper. Не вводит поля или новый tree codec. Root имеет известную неоднозначность при добавлении повторного последнего leaf; такие входы запрещены existing uniqueness contract и должны отвергаться **до** проверки root |
| B | Тот же tuple JSON и leaf domain, что в A; node domain `deltareduce.008.isc-merkle-node.v1`; рекурсивное деление массива по наибольшей степени двойки меньше его длины, без padding | Различает длины без зависимости от duplicate rejection. Singleton совпадает с A; multi-leaf preimages меняются, их roots нельзя считать совместимыми. Не выбран: текущий ISC contract уже требует уникальные tickets, а A повторно использует existing helper |
| C | SHA-256 от `ASCII("deltareduce.008.isc-input-array.v1") || 00 || ASCII("[" + comma-separated J(t) + "]")` | Другая root preimage для всех размеров; это не Merkle tree. Не соответствует FR-004 без отдельного изменения требования; не выбран |

Не допускается подмена A хешированием одних AC IDs: такое правило не задаёт
прямой commitment к четырём существующим tuple fields. Не допускается silent
fallback между A/B/C по тому, какой root подошёл.

Это **конкретная спецификация отсутствовавшего binding**. Она теперь утверждена
для FR-004, но её native implementation и формальная квалификация ещё не выполнены.
Одобрение документа не разрешает кодировать.

## Существующая tuple schema и ограничения

Источник: `InputTuple` в `delta-core-cpp/include/delta/certificates/contracts.hpp:69`
и `delta-protocol/schemas/008/input-set-certificate-v1.json`, `tuples.items`.
Объект содержит **ровно** эти четыре обязательных строковых поля:

| Поле | Existing type/constraint |
|---|---|
| `availability_certificate_id` | `^sha256:[0-9a-f]{64}$`, ровно 71 ASCII byte |
| `commitment_id` | `^sha256:[0-9a-f]{64}$`, ровно 71 ASCII byte |
| `domain_id` | `[A-Za-z0-9._:-]{1,128}` |
| `ticket_id` | `[A-Za-z0-9._:-]{1,128}` |

`additionalProperties=false`. Нет `leaf_index`, `leaf_count`, `profile_id`,
`round_id`, `parent_id`, `signature`, `length` или иных добавленных tuple fields.
Нельзя брать native struct memory или порядок ключей произвольного map.

При разборе tuple **любое повторение имени JSON-поля является ошибкой до построения
typed `InputTuple`**. Парсер не вправе применять first-wins, last-wins или объединение
значений, в том числе если оба значения одинаковы. Имена сравниваются после JSON
string decoding: эквивалентная escape-запись имени не скрывает повтор. Duplicate
member detection выполняется на исходном потоке members, до сведения к map,
JSON Schema validation и canonical reconstruction. `additionalProperties=false`
после обычного map parsing этой проверки не заменяет. Negative vector N11 хранит
исходные bytes со вторым `ticket_id`; ожидается `REJECT_DUPLICATE_JSON_MEMBER`
до typed construction/root evaluation. Это test outcome, не новый ABI status code.

Existing JSON schema требует `tuples.minItems=1`; отдельного `maxItems` в ней нет.
Existing native certificate constructor допускает не более 100000 entries и
existing `content_id` ограничивает целый certificate 4 MiB. Все действующие
ограничения размеров/выделения памяти сохраняются; 100000 не означает, что любой
массив такой длины поместится в certificate. Профиль не вводит новый меньший cap.

FR-005 и `InputLedger` дополнительно требуют исходную принадлежность ticket плану,
единственный commitment/availability для ticket и правильную связь этих объектов.
Один `ticket_id` не может занимать две позиции в ISC. Правильный root не отменяет
этих проверок. Перенос этих проверок в работающий producer здесь не реализуется.

## Canonical field encoding и порядок tuples

`J(t)` — точные ASCII bytes следующего объекта без пробелов, newline, BOM или
terminating NUL; `AC`, `C`, `D`, `T` заменяются существующими строковыми значениями:

```text
{"availability_certificate_id":"AC","commitment_id":"C","domain_id":"D","ticket_id":"T"}
```

Это уже существующий порядок полей в `contracts.cpp:249–257`, не новый JSON
canonicalization standard. Допустимые значения не содержат кавычек, backslash,
control bytes или Unicode, поэтому escape forms не нужны и не являются
альтернативным canonical encoding. ASCII и UTF-8 для этих символов дают одинаковые
bytes. Hex в content-ID fields остаётся **текстом**, не raw digest bytes.

Весь массив строго возрастает лексикографически по паре
`(ticket_id, commitment_id)` — unsigned ASCII byte order, без locale, case folding,
Unicode normalization или natural numeric sorting. Например:
`ticket-001 < ticket-002 < ticket-010 < ticket-2 < ticket-z`.
`domain_id` не переставляет элементы в отдельные domain groups.

Producer упорядочивает исходные entries **до** подписи proposal. Verifier проверяет
порядок уже переданного массива; он не исправляет подписанный body сортировкой,
deduplication или заменой значения. JSON parsing для чтения объекта не разрешает
хешировать произвольные исходные JSON bytes: для commitment используется только
`J(t)`, а signed canonical body отдельно должен соответствовать своему existing codec.

## Leaf preimage и domain separation

Пусть `H` — SHA-256 с 32-byte результатом; `||` — конкатенация bytes.

```text
D_leaf = ASCII("deltareduce.008.isc-input-leaf.v1")
leaf_preimage(t) = D_leaf || 0x00 || J(t)
L(t) = H(leaf_preimage(t))
```

Ровно один `0x00` отделяет domain от JSON. Ни length prefix, ни index, ни context,
ни array brackets не входят в leaf preimage. Завершающий NUL не добавляется.
Однозначность tuple encoding обеспечивают существующие field grammar и JSON
delimiters. `L` хранится в вычислении как raw 32 bytes; диагностический leaf ID
можно печатать как `sha256:<lowercase hex>`, но он не становится новым полем ISC.

Leaf domain отличается от shard leaf и ISC certificate domains. Existing ISC
certificate ID по-прежнему использует `deltareduce.008.input-set-certificate.v1`;
vote body ID — `deltareduce.vote.input-set-body.v1`. Эти три значения нельзя
подменять друг другом.

## Internal nodes и root

Повторно используется **точный** existing helper из
`delta-core-cpp/src/shards/envelope.cpp:127–166`:

```text
D_node = ASCII("deltareduce.004.merkle-node.v1")
N(left, right) = H(D_node || 0x00 || left || right)
```

`left` и `right` — ровно по 32 raw bytes в указанном порядке. Это не hex strings,
не `sha256:` labels, не JSON и не упорядоченная пара, отсортированная по digest.
Если вызывается existing helper, ему передаются leaf IDs, которые он декодирует
обратно в raw digests. Reuse node domain не делает root самостоятельным
идентификатором типа certificate: тип/profile/context проверяются вместе с ISC.

Начальный уровень — `L(t0), ..., L(t[n−1])` в исходном canonical order.
Пока узлов больше одного, при нечётном количестве копируется **последний узел
этого уровня** в конец; соседние пары заменяются `N(left,right)`. Повторяется
на каждом уровне, а не только на уровне leaves. Единственный оставшийся digest
`r` представляется в existing поле `input_root` как:

```text
"sha256:" || lowercase_hex(r)
```

Дополнительного root rehash, count prefix или root wrapper нет.

| Число tuples | Нормативное правило |
|---|---|
| 0 | INVALID: ISC не создаётся, root не определён. Нет special empty digest, empty certificate или автоматически введённого ABORT |
| 1 | Root равен `L(t0)`; leaf не удваивается и node hash не вызывается |
| 2 | `N(L0,L1)` |
| 3 | `N(N(L0,L1),N(L2,L2))` |
| 5 | `N(N(N(L0,L1),N(L2,L3)),N(N(L4,L4),N(L4,L4)))` |

Правило empty сохраняет existing native `InputLedger::freeze` rejection и schema
`minItems=1`. Оно **не** доказывает, что public `CloseInput/OMIT_UNAVAILABLE` никогда
не имеет пустого результата. Нельзя добавлять ограничение source domain или менять
`Init/Next`, чтобы скрыть такую ситуацию. Совместимость соответствующих исходных
состояний остаётся отдельной проверкой в уже существующем formal gate; R2 сейчас
не возобновляется.

## Duplicate и replay semantics

Дублированный tuple или повторный ticket в массиве — invalid input. Два разных
commitment/AC для одного ticket — conflict, а не два leaves. Producer/verifier
не удаляет дубликаты ради получения «подходящего» root. Existing commitment/AC
identity и parent/uniqueness checks по FR-005 остаются обязательными.

Повтор доставки того же commitment, AC или vote не добавляет tuple: existing
ledger replay остаётся replay. Повтор вычисления над теми же frozen tuples даёт
те же bytes/root. Повтор finalization не может заменить signers или body;
durable receipt/WAL механизм будет определён в следующем документе, не здесь.

**Ограничение выбранного дерева не скрывается:** unchecked tree для `[A,B,C]`
равен unchecked tree для `[A,B,C,C]`. Второй список запрещён из-за дублированного
tuple/ticket. Поэтому `input_root` нельзя использовать как единственное основание
принять произвольный список с multiplicity: сначала проверяются canonicality и
уникальность, а полный canonical ISC body также подписывает массив `tuples`.
Нет заявления об инъективности root для всех byte arrays или cryptographic proof.
Если в будущем будут разрешены duplicate tickets или иной смысл multiplicity,
потребуется отдельное решение о новом profile; такая возможность сюда не включена.

## Profile identifier и binding к round context

Идентификатор этого решения — **`deltareduce.008.isc-commitment.v1`**. Это имя
нормативного профиля в formal/source qualification, **не новое wire field**.
Отдельный `profile_id` не добавляется ни в tuple, ни в ISC, ни в RoundConfig.

Выбран один профиль для квалифицированной semantics version. Будущий exact Formal
GO должен фиксировать отображение существующих
`(formal_semantics_id, schema_version="1.0.0", type_name="INPUT_SET_CERTIFICATE")`
на данный документ и его normative vectors. Их SHA-256 должен входить в проверяемую
qualification/semantics dependency closure. Сейчас такое новое отображение не
утверждено; новый formal semantics ID не вычислен и не присвоен.
Unknown/old semantics ID нельзя автоматически считать поддерживающим этот профиль
на основании совпавшего root. Per-round negotiation и fallback не вводятся.

Root намеренно зависит только от tuples. Поэтому одинаковый допустимый input set
в двух contexts даёт одинаковый root. Context binding выполняется существующим
полным `VoteInputSetBody`/ISC: `round_id`, `height`, `view`, `round_config_id`,
`validator_epoch_id`, `parameter_schema_id`, `arithmetic_profile_id`, version/semantics
и root/tuples проверяются вместе.

**Этот профиль нормативно определяет только вычисление `input_root` из ordered
tuples. Он не утверждает достаточность существующего parent binding и не изменяет
full-context requirements ISC. Соответствие фактической ISC schema требованию
явной parent/context binding остаётся отдельным compatibility/refinement obligation.**
Транзитивные ссылки через RoundConfig/WorkTickets не объявляются его закрытием.
`parent_checkpoint_id` сейчас не добавляется; вопрос не решается новым полем
или ослаблением контракта в этом документе.

По отдельно утверждённому I-B `b=vote_input_set_body_id(B)` связывает context, root
и ordered tuples и служит consensus ISC identity. `c=content_id(C)` связывает
canonical certificate witness целиком, включая original signers, и является artifact
identity. Downstream ISC parent-reference и semantic replay используют b только в
будущей квалифицированной semantics version `σ_next`; original C/c не relabel.
Согласно S-RANK native `s` остаётся physical WAL slot, а public `V_a(s)` считает только
original kind-2 votes. Kind 3 не увеличивает V_a. Artifact c и consensus b, как и s/V_a,
не являются взаимозаменяемыми aliases; их documentary negatives заданы в
[WAL Capsule](0014-isc-finalization-wal-capsule-v1.md).
Round-scoped ISC `vote_context_id` не меняется и не заменяет full body checking.
Нельзя переносить root или подпись в другой context, даже когда leaf digests совпали.

## Нормативные cross-language vectors

[Полный vector document](evidence/0014-isc-commitment-profile-v1-vectors.json)
содержит tuple objects, exact ASCII/hex bytes, длины, полные leaf/node preimages,
все промежуточные уровни и expected roots. Это **утверждённые нормативные данные FR-004**
для будущих C++/Java/Python implementations, не изменённые runtime fixtures/schema.
Имена A–E/V1–V5 и поля vector document — метаданные документа, не protocol identities.

В обозначениях ниже `1×64` означает ровно 64 ASCII символа `1` после `sha256:`,
и аналогично для остальных digit/letter. В полном JSON все значения развёрнуты.
Это синтетические byte vectors без подписи, quorum или production authority.

| Tuple | `availability_certificate_id` suffix | `commitment_id` suffix | domain | ticket |
|---|---|---|---|---|
| A | `1×64` | `2×64` | `code` | `ticket-001` |
| B | `3×64` | `4×64` | `code` | `ticket-002` |
| C | `5×64` | `6×64` | `text` | `ticket-010` |
| D | `7×64` | `8×64` | `text` | `ticket-2` |
| E | `9×64` | `a×64` | `image` | `ticket-z` |

| Vector | Canonical input | Expected `input_root` |
|---|---|---|
| V1 | `[A]` | `sha256:53c4a71424b563cb8a7165ed477f1b4f201cab0c6398bbf9784886627b4f0a12` |
| V2 | `[A,B]` | `sha256:ea5081daf1a739ea246476d6944cbce6165fffe6f77633642a4bc61111411c71` |
| V3 | `[A,B,C]` | `sha256:6f9d421a765001b2bd67bc98b44b7386fa71f4a92bbd66de9001f374560d6404` |
| V4 | `[A,B,C,D]` | `sha256:2eceb77fafb12d859d448401b44aed0481e58f778aba9e5f70afb16dff37ae79` |
| V5 | `[A,B,C,D,E]` | `sha256:78377b6005906eafb6da0480d2c289688fad86aec5f1cf3edb2c19b35cf16f31` |

Обязательные отрицательные/relational cases в том же документе: empty, reversed
order, duplicate tail с root как у V3, одинаковый ticket с другим body, uppercase
digest, лишнее tuple field, повтор JSON member до typed construction,
неканонические tuple bytes, ASCII вместо raw children,
отсутствующий domain separator, повтор доставки и неизвестная profile authority.
Строки `REJECT_*` описывают исход проверки, **не вводят новые ABI status codes**.
Проверка raw Merkle tree без schema/order/uniqueness validation не является profile
conformance, даже если expected root совпал.

Численные bytes/hashes независимо рассчитаны через Python `hashlib` и сборку
preimages/SHA-256 в .NET. Это проверка точности документа; C++/Java conformance,
native producer execution, TLC/Lean results или новый Formal GO здесь не заявляются.

## Точные compatibility consequences

| Объект или claim | Следствие утверждения и последующего внедрения профиля |
|---|---|
| Existing tuple/ISC wire schema | Ни поля, ни field order, ни версии schema/type не добавляются. Тот же структурный parser ещё не означает semantic compatibility |
| Canonical ISC content-ID formula | Domain и алгоритм остаются прежними. При изменении `input_root` меняются canonical ISC bytes и их content ID |
| Proposal/votes | При изменении root меняется `vote_input_set_body_id`. Старые подписи/голоса не действуют для нового body; их нельзя «перепривязать» |
| Signers и quorum | IDs, epoch, threshold и signer-order rules сохраняются; root не доказывает наличие quorum |
| Root уже равен computed value | При полностью одинаковых прочих bytes ISC ID остаётся тем же. Однако допускается ли этот semantics ID для данного профиля — отдельная обязательная проверка |
| Existing constant-root fixtures | Их нельзя объявить profile-v1 producer evidence. Старые bytes/IDs сохраняются как исторический corpus; новые положительные profile vectors/fixtures должны быть отдельными |
| Existing finalized QC и downstream lineage | Не переписывать QC, ссылки, seeds/EC/APC или history. Новый root/semantics создаёт новый body только в новом разрешённом execution; не исправление finalized round |
| Approved I-B parent-reference | В будущей σ_next consensus ISC parent/index = b; c остаётся original witness/artifact identity. Это меняет native reference semantics и новые downstream signed bodies/QC IDs. Old c-based objects не проходят как b-based посредством relabel или fallback |
| Approved S-RANK / WAL sequences | Original signed s/checksums/receipts сохраняются. Public V_a(s) — rank original kind-2 votes, не physical s; kind 3 не vote. Counts/replay не перенумеровывают старые records. Этот FR-004 документ не утверждает W1 format |
| Current native structural guards | Будущая profile проверка root будет строже нынешней проверки hash-shaped string. Это observable admission/conformance change, а не чисто редакционное уточнение |
| Production TLA `Init/Next` | Изменения не предлагаются. Existing `canonicalRoot` abstraction требует отдельного refinement к этому byte contract; старые model результаты не доказывают новую SHA/Merkle связь |
| Accepted/candidate semantics IDs | `cc98f15a…` и `b96d2253…` не объявляются authority для нового binding. После approval требуются включение профиля/vectors в semantics closure, новый вычисленный semantics ID и exact compatible merged GO. Ни один ID сейчас не заменяется |
| Evidence | Старые результаты остаются верными для своих exact sources/statements. Нельзя повысить synthetic/static certificate evidence до production commitment correctness. Новая qualification должна проверять source→tuple bytes→root→body и compatibility с сохранёнными raw bytes |

Новый semantics ID будет также менять bytes полей, в которых он присутствует, и
зависящие от них IDs. Поэтому обещание сохранить **все новые** QC IDs одновременно
с новым root/semantics было бы ложным. Сохраняются **старые существующие объекты**
и формулы их identity; новый профиль не авторизует их rewrite или silent migration.
Никакой новой независимой authority или параллельного certificate protocol нет.

Даже без finalized ISC уже записанный старый vote intent запрещает повторно
подписать новый body в том же защищённом vote context. Смена profile/formal ID
не сбрасывает `VoteJournal` и не разрешает такой re-vote. Процедура live migration
между версиями данным документом не вводится.

Нынешняя JSON schema содержит `formal_semantics_id.const = cc98f15a…`. Будущая
поставка с новым квалифицированным ID потребует согласованного обновления этой
константы и native descriptor/constant с сохранением исторической версии, а не
ослабления проверки до «любой hash». Это изменение значения existing field и
source qualification, не добавление поля. Сейчас schema и constants не меняются;
старый reader должен fail closed на неподдерживаемую semantics version.

Конкретный расчёт на исходном `008/valid/certificate-contract-v1.json`:

| Значение | SHA-256 content ID |
|---|---|
| Existing fixture root | `sha256:1ec8ff982235c59be66cbc34206a90751c685d86a2aca810ec07fc9361564896` |
| Profile A root тех же исходных tuples | `sha256:3296dda0959e97ccda01050a65f1d06d0752d5eba6d4c46fadcaa64a9291d45e` |
| Existing fixture ISC ID | `sha256:abf1eaf832da858d0dbf41ffd146675be5189bee70a34a0c258429a3ac68ebac` |
| Только root заменён, остальные старые bytes/context удержаны для сравнения | `sha256:cbedd3198475b424cd7b9052a3c3b99068f7245be6f1b7e3df614b1ac9fb774b` |

Последняя строка — диагностическое сравнение byte sensitivity, **не** новый валидный
production certificate, не approved semantics и не разрешённая миграция. Исходный
fixture не изменён. Будущий real certificate будет иметь квалифицированный context
и fresh votes; его ID здесь не выдумывается.

## Граница утверждения и STOP

Утверждены только A и следующий byte-level контракт FR-004:

```text
validated ordered unique InputTuple list
→ canonical J(t) → domain-separated leaves
→ specified duplicate-last Merkle root → exact input_root
```

Утверждение включает duplicate-member fail-closed decoding и normative vectors.
Оно не означает, что production ISC producer реализован, parent/context binding
квалифицирован, quorum сформирован, ISC durable, старые QC можно мигрировать
или R2.3/R3 закрыты. Оценка 50–84 часа остаётся не утверждённой.

Две обязательные правки FR-004 уже зафиксированы; I-B/S-RANK впоследствии утверждены
отдельно. `ISC Finalization WAL Capsule v1` и Producer Integration документально
согласованы с ними. W1 теперь утверждён как local byte/storage contract; production sufficiency этим не установлена.
Ни код, ни proofs, ни schemas, fixtures, R2.3/R3 или runtime changes не разрешены
без обоих утверждённых contracts и отдельной команды с соблюдением exact compatible
merged Formal GO. Parent/context obligation нельзя закрыть самим WAL capsule.

**STOP на реализации сохраняется.** DoD R1–R7 и Snapshot Provenance Profile v1
не менялись; R1/R2.1/R2.2 CLOSED, R2.3/R2 OPEN.
