# ADR-0012 — decision memo: provenance на границе Formal GO

29 сентября 2026. T000–T003/T047/T053–T057. **PROPOSED; выбор не сделан.**
Source base: `4c7c03c7fa866213e05c47531ebfef15e5c40355`.

Пользователь принял `MISSING SNAPSHOT PROVENANCE CONTRACT` как архитектурный
blocker R2.3. Этот memo сравнивает два способа задать недостающую границу доверия.
Он не вводит normative predicate, код, schema, theorem или proof layer и не
изменяет принятый DoD. Все формулы ниже — **предлагаемые statements для решения**,
а не существующие или уже доказанные Lean declarations.

R1/R2.1/R2.2 остаются приняты CLOSED. R2.3/R2 OPEN. R3 не начат; A/B/C из
предыдущего ADR не реализуются. Ни P1, ни P2 сами по себе не закрывают R2 и не
доказывают невозможность EC context mismatch на окончательно выбранном domain.

## 1. Решение, которое требуется

| | P1: external provenance assumption | P2: provenance проверяется внутри Formal GO |
|---|---|---|
| Кто отвечает за origin исходного среза | Внешняя явно названная authority; истинность её утверждения — premise | Проверенный source-only verifier выводит origin из независимо аутентифицированных исходных свидетельств |
| Что доказывает GO | Корректность R2/R3 **при условии** допустимого native origin | Дополнительно корректность проверки origin; затем те же R2/R3 |
| Что остаётся внешним | Достоверность происхождения всего initial cut, кроме прежних crypto/observation premises | Trust root, ключи/epoch, hash/signature abstractions и faithful observation физических bytes; не корректность producing history |
| Основной риск | Сильное условие может быть ошибочно представлено как доказанный результат | Подпись под тем же недоказанным origin assertion может быть ошибочно названа его проверкой |
| Предварительный blast radius | Малый по runtime, средний по statement/domain/evidence | Средний–большой по contract/verification/evidence; deployment отдельно после GO |

Проверка подписи доказывает, **кто подписал какие bytes**. Из неё не следует,
что подписанное состояние получено допустимой историей. Если в P2 это просто
объявить поведением доверенного подписанта, получится P1 с подписанным документом.

## 2. P1 — точная внешняя предпосылка и условные statements

### 2.1. Предлагаемый текст assumption

Для фиксированных native semantics/source version, immutable configuration,
enrolled epochs и snapshot cut внешняя authority удостоверяет следующие факты:

1. Переданные original state/policy/artifact bytes и их inventory относятся
   именно к этому cut и этим идентичностям. Полные нужные certificate/candidate/
   current/environment collections не подменены и не дополнены другим prefix.
2. Существует исходный execution prefix от закреплённого genesis, исполняющий
   независимо заданные **native producer rules** соответствующей версии.
   Непустые collections созданы его действительными событиями; native finalization
   отличается от наличия валидных подписей и от локального API acceptance.
3. Наблюдаемые per-actor durable records — точные срезы этого prefix, с исходными
   bytes, multiplicity, signer/context/QC identities и sequence. Known, absent и
   unknown/incomplete observations сообщены правдиво. Последние не утверждают
   отсутствия записи или готовности восстановленного validator к голосованию.

Здесь нет утверждений о public body/state, переводе aliases, публичной uniqueness,
успехе R2 checker или равенстве результата recovery. Authority не передаёт готовый
переведённый state. Raw identity/configuration observations остаются входами;
их согласование с public namespace и source-body derivation остаётся R2.

**Существенное ограничение:** полный native producer contract для происхождения
предзагруженных collections сейчас не закреплён. Выбор P1 должен явно принять
именно эту внешнюю гарантию и её source/version/issuer scope. Нельзя назвать
существующий `NativeConfigReplay.History` таким полным contract: он начинается
от supplied initial machine. Нельзя определить producer rules через public
`Next` после искомого projection. Нельзя ограничиться guarded runtime, где
арифметические first votes отключены: это сделало бы arithmetic claim пустым.

В частности, две подлинные ISC QC signer variants нельзя исключить из domain
потому, что они неудобны public EC context. Если independently fixed native
producer rules допускают их именно в конфликтующем состоянии/журнале, P1
сохраняет этот случай и representation blocker остаётся. Подпись authority
не доказывает обратного; A/B/C не выбираются этим memo.

### 2.2. Обозначения statements — не новые definitions

- `theta`: фиксированные native/model versions, bounds, immutable config,
  authenticated primitive identity/alias/unit bindings и существующие FR-033
  hash/signature/canonical/durable-observation premises. Произвольной truth-table
  для полного public body в `theta` нет.
- `O_theta(E,n)`: сокращение **только текста внешней предпосылки §2.1** о raw
  evidence `E` и native cut `n`. Сейчас такого sufficient predicate в коде нет.
- `B_theta(n)`: существующие raw decoding, source metadata и numerical/domain
  preconditions; ни public acceptance, ни representability в них не включаются.
- `Pi_theta`: подлежащий завершению детерминированный family constructor из
  исходных bytes. `F` — полное синхронное семейство coordinate views по исходным
  shards, не множество новых shard/vote/certificate objects.
- `R_theta(n,F)`: **требуемый вывод замороженного R2**: полные constructors,
  guards, config/aliases/units, все relevant collections и state constraints,
  sufficient ABORT, сохранение identity, lineage, порядка и multiplicity.
- `N_theta`: независимо фиксированная native lifecycle transition relation
  согласованного formal scope, включая failure observations. Это не имя
  существующей уже полной implementation proof и не `R`-filtered relation.
- `P_theta` — неизменённые production `DeltaReduce.Init/Next`, используемые
  синхронно каждым coordinate view. Соответствие action/stutter фиксировано
  refinement contract; нельзя скрыть неудобное событие произвольным stuttering.

Для полноценных известных cuts предлагаемый R2 statement:

```text
forall theta, E, n:
  H(theta) and O_theta(E,n) and B_theta(n)
  implies exists unique F:
    Pi_theta(n) = Some(F) and R_theta(n,F).
```

`H` — перечисленные старые абстракции из `theta`, а не успешность theorem.
Полнота охватывает все исходно допустимые lengths/INT64/INT128, включая
4/8/8/8/8, initial и непустые downstream states. При incomplete/corrupt observation
должны сохраняться ровно известные facts и explicit incompleteness; формула
не требует выдуманного полного READY state. Его недопустимость и сохранение
блокировки входят в failure/recovery часть R3. Это не исключение таких inputs
из общей области R2/R3.

Предлагаемый R3 preservation statement:

```text
forall theta, n, a, n', F:
  H(theta) and R_theta(n,F) and N_theta(n,a,n')
  implies exists F':
    R_theta(n',F') and F --existing projection of a--> F'.
```

Он квантифицируется по разрешённым existing actions и типам наблюдений;
для неизвестных cuts `R` сохраняет incomplete information, а не объявляет его
полным состоянием. Внутренние стадии дают только предусмотренный action/stutter;
все views шагают согласованно с одной общей identity/journal/transport частью.

Полный R3 theorem, соответствующий цели `nativeArithmeticRecoveryRefines`,
должен затем устанавливать:

```text
forall theta, E0, n0, finite native suffix sigma starting at n0:
  H(theta) and O_theta(E0,n0) and B_theta(n0)
  and every suffix step satisfies the fixed N_theta
  implies exists public family trace Phi:
    Phi starts at Pi_theta(n0), represents every observed cut,
    extends a production-Init/Next family prefix for that initial cut,
    and every suffix step has its required existing action/stutter projection;
    verified recovery and exact replay preserve the original certified state,
    bytes/effects/sequences and journal multiplicity;
    unknown/incomplete/corrupt scans do not enable READY or establish absence;
    durable, exposed, sent, delivered and quorum-eligible remain distinct;
    current changes only by the existing ApplyQC/current rule.
```

Проекция исходного prefix в public `Init/Next` здесь **вывод**, не часть `O`.
Она требует base correspondence и preservation для независимо описанного
producing prefix. R2 нельзя считать закрытым только потому, что `O` названо;
R3 нельзя заменить фразой «доверенная authority уже гарантирует recovery».
Промежуточное `R(n,F)` в step lemma нормально: итоговый theorem обязан получить
base из raw inputs/R2 и сохранить relation индукцией, не потребовать её для
каждого recovered state на входе.

### 2.3. Почему это assumption не содержит результата refinement

Это логическая проверка предлагаемых statements, **не новый machine-checked
proof и не доказательство R2/R3**.

1. `O` использует только native bytes, native event/producer rules, исходные
   identities, cut и свидетельства authority. В нём нет `Pi`, `R`, public state,
   public guards/`Next`, recovery output или равенства переведённых bodies.
2. Зафиксируем одни и те же допустимые native facts и истинное `O`. Заменим
   только public constructor ошибочным: он меняет одну представленную model
   coordinate либо сливает две исходные journal entries. Все аргументы и
   истинность `O` останутся прежними, а требуемое R2 correspondence нарушится.
   Значит, `O` само по себе не влечёт корректности mapping.
3. Аналогично `O` фиксирует происхождение начального cut. Ошибочное последующее
   recovery, выделяющее второй sequence для exact retry, не делает это начальное
   утверждение ложным. Исключить такой результат обязан R3 из independently
   specified transition rules; предпосылка его не исключает по определению.

Проверка не утверждает, что ошибочный constructor/recovery удовлетворяет всем
остальным hypotheses корректного theorem. Она показывает, что **сам assumption
не равен искомому выводу и не зависит от выбора implementation projection**.
Native-origin premise сильная: она выносит правильность producing history за
границу доказательства. Это открытое ограничение claim, даже без логического круга.

Недопустимые замены: `exists F, R(n,F)`, `checkR2(n)=OK`, «все public invariants
уже истинны», «recovery совпадает с ожидаемым», «нет EC collision после projection».
Каждая такая замена предполагала бы часть требуемого результата.

## 3. P2 — минимальный предлагаемый trust contract

### 3.1. Authority и объект evidence

Предлагаемый минимальный объект — **recovery evidence bundle**, привязанный к
ранее закреплённому genesis/epoch trust root и существующей certificate chain.
Он не становится новым protocol QC, командой или способом advance current.
Центральный operator не получает право выбирать current или подтверждать
произвольное prepared state (Constitution III/VI/VII).

В bundle нужны две различные части authority:

- **Сертифицированное состояние:** существующие original QCs с прежними
  подписями/context/threshold/epoch, включая ApplyQC, если checkpoint уже current.
  Они удостоверяют именно свои прежние bodies и parents, не всю WAL.
- **Происхождение наблюдения:** role/epoch-authorized producer удостоверяет
  точные captured bytes/inventory/cut своего runtime; для нескольких actors —
  отдельные source statements либо независимо доверенный faithful observer.
  Эти заявления не удостоверяют законность history: её проверяет verifier.

Нельзя потребовать «2f+1 подписей под каждым local WAL»: persisted-but-unexposed
vote может существовать только у владельца и не иметь сетевого кворума.
Нельзя переносить signer set checkpoint QC на полномочия backup producer.
Producer enrollment/role scope должны быть закреплены отдельно; существующий
контракт пока их для полного snapshot не определяет.

### 3.2. Что подписывается / связывается

Предлагается подписывать domain-separated, versioned **manifest исходных bytes**,
а не public projection и не Boolean «snapshot корректен». Минимальный смысл:

| В manifest / referenced original content | Необходимая связь |
|---|---|
| Protocol/formal/native source version, network/genesis, actor, runtime incarnation, epoch и назначение cut | Не допускает foreign-network/epoch/producer substitution; credential scope проверяется от отдельного trust root |
| Original RoundState bytes и **полная** policy/snapshot inventory; config/schema/profile/assignment refs, raw alias/unit source refs | Не позволяет подменить certificate collections при сохранённом `state_id` или подобрать другой numeric/configuration namespace |
| Parent и current checkpoint/model/optimizer IDs и bytes refs; exact certificate bodies/QC IDs/signers/parents/finalized events | Связывает checkpoint с фактом finalization и исходной цепочкой; genesis/incomplete cuts могут ещё не иметь ApplyQC |
| Для каждого actor — исходные WAL bytes/ranges/tips, original vote/receipt/effect refs, физические позиции и существующие logical sequences | Сохраняет порядок, multiplicity и no-double-vote history; физический WAL offset не переименовывается в per-actor vote sequence |
| Cut boundary, зависимые records и exact pre-cut origin evidence от genesis либо ранее **проверенного этим же contract** cut | Запрещает смешивание срезов и циклическую цепочку «backup доверяет backup» без основания |
| Complete / unknown / incomplete observations и источники сведений о presence/absence | Отсутствие bytes/response не считается verified absence; неизвестность не позволяет загрузить READY |

Хэши связывают manifest с bytes. Подпись связывает manifest с разрешённым
источником наблюдения. **Отдельная source-only проверка** связывает этот cut с
genesis и законным producing prefix. Для evidence допускаются ссылки на original
content; копировать всё в один новый формат не обязательно. Existing certificate,
vote, shard и WAL identities/bytes остаются неизменными.

Для всех relevant actors нужна полнота наблюдения требуемого prefix, но не
обязательна одинаковая физическая sequence или одновременный wall-clock snapshot.
Учитываются уже обязательные cross-actor dependencies и различия send/delivery;
согласованность такого cut не следует только из отдельных верных checksums.
Новый signature primitive/доказательство fsync не входит в этот минимальный P2:
старые FR-033 и faithful durable-observation abstractions сохраняются явными.

У цепочки previously verified cuts должно быть конечное основание в закреплённом
genesis. Если вместо него без проверки принимается произвольный непустой
«trusted checkpoint», origin этой базы снова является внешним P1 assumption.
Даже подлинный ApplyQC доказывает свой tuple, а не отсутствие потерянных local
votes до checkpoint. Verification failure сохраняет BLOCKED/quarantine; оно
не разрешает очистку журнала, rollback сертификатов или новый unsigned terminal.

### 3.3. Кто должен проверять и что остаётся недостающим

| Существующий владелец / компонент | Ответственность при выборе P2; нынешний предел |
|---|---|
| `delta-core-cpp` certificate/policy verification | Canonical IDs, role/epoch/signers, original context/parent graph и полный input inventory. `ChainVerifier`/policy validation сами не проверяют происхождение всех preloaded collections; signer IDs не заменяют signature verification |
| `delta-runtime-cpp::Runtime::recover`, WAL/snapshot reader | Проверка source/cut association, ordered replay и readiness **до** новых votes. Сейчас replay от supplied initial не доказывает origin самой базы |
| `CurrentPointerStore` + current/certificate verifier | Current parent/CAS и связь exact ApplyQC с model/optimizer и pointer WAL. Current pointer не служит authority для всех оставшихся collections |
| `NativeReplayAdmission.prepareWhole`, `NativeConfigReplay`, `NativeArithmeticHistory`, `NativeCurrentHistory` | Переиспользовать decode/replay/lineage components; обосновать native-only base origin и producing prefix. Их нынешние conditional `History` результаты недостаточны для этого нового contract binding |
| `native_trace_witness.py::NativeEvidence`, `PublicSnapshot`, `PublicAuthority` и `FamilyRelation` | Source bundle проверяется до public construction; затем действующие R2 obligations выводят projection. Digest-only evidence нельзя повысить до trusted origin; public checker не должен решать native domain через собственный успех |
| Java transport/FFM/sidecar | Доставляет opaque bytes, аутентифицирует назначенную transport роль. Не устанавливает допустимость snapshot, membership или current; эти полномочия остаются native boundary |
| Formal report/coverage/review | Фиксирует actual trust inputs, checker soundness и statement dependencies; synthetic evidence отдельно от real producer attestations |

Ключевой дополнительный результат P2 — soundness проверки producing prefix
от независимой исходной authority. Его нельзя получить одним расширением JSON
или подписью manifest. **Сейчас нет готового полного independently specified
producer/checker для этой задачи.** Это конкретный риск реализации выбранного
P2, а не причина уже сейчас создавать новый proof layer.

Если проверка возможна только через новый production action, новую certificate
semantics или новый WAL identity, минимальный P2 перестаёт быть refinement-only.
Потребуется отдельное решение formal semantics; этот memo такого изменения не
разрешает. P2 не следует реализовывать через A/B/C без отдельного выбора.

## 4. DoD, существующие результаты и blast radius

| Область | P1 | P2 |
|---|---|---|
| Августовский DoD / FR-033 | Условное refinement совместимо с разрешёнными abstraction premises; происхождение всех preloaded collections сильнее простой hash/signature premise | Проверка origin согласуется с FR-014/037/038 и PO-R2; production crypto proof по-прежнему не требуется |
| Замороженный R1–R7 / candidate contract 1.1.0 | Не автоматическая трактовка без изменений: явное **усиление external assumptions и сужение unconditional claim**. Нужен одобренный пересмотр trust/scope inventory. R2/R3 нельзя вычеркнуть | Уточняет существующий source/initial obligation, **но добавляет отсутствовавший authority/evidence contract**. Должен быть явно принят; полный production exporter или отдельный новый consensus QC выходили бы за минимальный вариант |
| Логическое противоречие | Возникает, если authority гарантирует public validity/refinement/recovery equality, либо single operator выбирает finalized state. Предложенный P1 этого не разрешает | Возникает, если произвольный manifest/backup заменяет BFT QC или unknown превращается в absence. Предложенный P2 этого не разрешает |
| Production `Init/Next`, vote/certificate/WAL identity | Изменений не предполагается; невозможность соответствия на допустимом source-domain всё равно STOP | В минимальной evidence форме изменений не предполагается. Не гарантировано, пока producer contract не спроектирован и не сопоставлен с existing actions |
| R2/R3 proof impact | Statements/precondition/dependency audit, origin-domain instance, затем оставшиеся static binding и transition proof. Статусы CLOSED у R2.1/R2.2 не меняются | Те же работы плюс проверка origin evidence и её soundness; реальное подключение runtime отдельно после exact merged GO |
| TLA / finite safety | Старые результаты сохраняют собственные hypotheses; не доказывают новую applicability | Аналогично; affected startup/recovery abstraction и mutants подлежат новой квалификации, если изменится формальная область |
| Schemas/checkers | Возможно повторное использование при отдельно связанном evidence; сейчас sufficiency не установлена. Не выдавать существующий digest-only witness за контракт P1 | Manifest/evidence contract и source checker потребуют нового binding/versioning; public trace format может сохраниться, если внешние refs достаточны |
| Evidence / claims / report | Обновление R1 inventory/compatibility, R2/R3 statements и R4–R7 exact-source qualification. Исторические отчёты не переписываются | То же плюс provenance-positive/negative evidence для verifier; synthetic data не становятся independent attestation |

Это impact будущего выбора, **не повторное открытие принятых R1/R2.1/R2.2 в этом
этапе**. Никакой R8 не добавляется. Ни один вариант нельзя молча объявить уже
охваченным неизменённым frozen assumption inventory. Названия старых закрытых
результатов сохраняются с их реальными hypotheses; отсутствие новой provenance
authority не опровергает их kernel proofs. Ни один текущий NO_GO не повышается.

Blast radius P1 ограничен преимущественно contract/statement/source-domain и
dependent evidence; вычислительные kernels и 4/8/8/8/8 family projection доступны
для reuse. P2 затрагивает дополнительно startup/backup authority, capture/cut
binding, source verification и future runtime ingress. Если нужен новый BFT
certificate type, radius становится протокольным и уже не минимальным P2.
Достоверной оценки часов P2 до выбора root/producer semantics пока нет; наличие
готовых replay lemmas не даёт оснований оценивать его как «добавить подпись».

## 5. Как меняются claims статьи

Полный текст исходной статьи/`Pasted markdown(1).md` не хранится в checkout.
В наличии [source provenance memo](../source/deltatorrent-concept.ru.md) и
[DeltaReduce amendment](../source/deltareduce-v1-amendment.md). Поэтому ниже —
точные **предлагаемые формулировки технических claims**, а не цитаты из статьи
или утверждение, что в ней уже написано более сильное обещание.

| Claim | При P1 | При P2 после всех требуемых доказательств |
|---|---|---|
| Full native/public correspondence | «Для independently authenticated initial cuts с внешне гарантированным допустимым native origin mapping сохраняет state/body/context/identity» | «Проверка provenance выводит допустимый native origin из authenticated evidence; mapping сохраняет state/body/context/identity» |
| Crash/recovery, no-double-vote и current | «R3 сохраняет certified state и original journal identities при trusted initial origin и прежних fault/durability assumptions» | «То же, причём принятие initial/recovered evidence обосновано проверенным origin checker; неполные scans остаются blocked/incomplete» |
| Untrusted imported snapshots / arbitrary API input | Общего claim нет: подлинность подписи trusted source не доказывает, что его statement истинен | Можно заявлять fail-closed проверку в точно доказанной области bundle/checker; не универсальный arbitrary-backup recovery и не physical I/O correctness |
| BFT без центрального решающего узла | Сохраняется для protocol transitions; отдельно раскрывается внешнее доверие initial-state provenance | Сохраняется при genesis/epoch/QC-rooted evidence и native verification; обычный backup signer не становится consensus authority |
| Integer arithmetic, hierarchy, fixed domain mixture | Установленные локальные теоремы не меняются; привязка к реальному snapshot остаётся условной | Теоремы переиспользуются; origin checking входит в обоснование применимости |
| WAN, 8 GB, качество обучения, independent custody | Ничего не усиливается | Ничего не усиливается; formal provenance verification не является real-WAN/physical-GPU/quality measurement или независимой custody attestation |

Нельзя писать ни для одного варианта сейчас: «полное восстановление доказано»
или «Formal GO получен». Выбор P1 меняет место доверия; выбор P2 переносит
проверку origin внутрь доказуемой области. Оба оставляют содержательные R2/R3
обязательства и исходные final gates.

## 6. Источники и STOP

- [Принятый provenance audit](0012-snapshot-provenance-audit.md) и
  [его source hashes](evidence/0012-snapshot-provenance-source-audit.json):
  точные inspected definitions, native pin и границы существующего evidence.
- [Frozen residual](../../specs/000-formal-tla-spec/accepted-residual-20260928.md),
  [candidate contract](../../specs/000-formal-tla-spec/candidate-contract.md):
  R2/R3, permitted assumptions и запрет assuming desired conclusion.
- [Spec §2.2 / FR-014/033/037/038](../../specs/000-formal-tla-spec/spec.md),
  [PO-AB1/PO-R2](../../specs/000-formal-tla-spec/proof-obligations.md),
  [recovery §7](../../specs/000-formal-tla-spec/failure-semantics.md),
  [refinement contract](../../specs/000-formal-tla-spec/refinement-contract.md).
- [Domain analysis](0012-r2-domain-analysis.md),
  [native policy/WAL evidence scope](../../formal/proposals/native-policy-wal.md),
  [R2.1/R2.2 component scope](../../formal/proposals/b-family-transfer/CONSTRUCTORS.md).

**Решение отложено до выбора пользователя.** Документ не принимает P1/P2, не
добавляет новый predicate/authority object в систему и не разрешает продолжать
R2.3/R3. Code/proofs/schemas/runtime, normative contract и frozen DoD неизменны.
