# R2.3 — implementation/proof plan для утверждённого Profile v1

29 сентября 2026. T000/T044/T047/T053–T057. **PLAN ONLY — STOP после отчёта.**
Source base: `7c018975f483b6be0a0193a44c456745aae9ad26`.
Пользователь утвердил [Snapshot Provenance Profile v1](0013-snapshot-provenance-profile-v1.md)
для текущего production scope. Его bytes SHA256:
`7cd4170171d554e8f3b34f0a76e28643dfa9650dc49e06ff42526e6236063e4a`.
Профиль не пересматривается. Этот план не разрешает программирование.

Цель — **R2.3 CLOSED для утверждённого profile**: из independently anchored
исходных данных и проверенной native history получить admissible source state
и общую полную static family relation, переиспользующую CLOSED R2.1/R2.2.
Production recovery, atomic activation implementation, READY transition proof
и `nativeArithmeticRecoveryRefines` относятся к R3/последующей implementation;
на этом этапе они не выполняются. Не добавляются новые provenance mechanisms.

## 1. Что уже есть и что конкретно ещё отсутствует

| Existing component | Reuse / обязательная граница |
|---|---|
| `NativeReplayAdmission.prepareWhole`, `wholeStartupSource`; `NativeCandidateAuthority.bindPolicy`, `preparedSource` | Decode/binding полного supplied policy/state и source-linked candidates. **Не выводят origin** этой базы от genesis |
| `NativeConfigReplay.History`, `recoveryComputed`; `NativeArithmeticHistory.History`, `recoveryComputed` | Existing finite native journal fold components. Использовать только для описания статического исходного prefix; не объявлять их general recovery refinement |
| `NativeCurrentHistory.checkRow`, `rowSource`, `currentStateDerived` | Exact original current/QC/candidate/optimizer association. Не заменяет independent bootstrap authority или floor |
| `FamilyInputs.loadOriginalNumericConfiguration`, `originalConfiguredInputTotal`; `FamilyAuthority.originalConfiguredInputLoaded`, `originalAuthorityLoaded`; `FamilyApply.originalApplyCheckedFromConstructed` | CLOSED constructors/domain. Import unchanged; не переделывать scalar arithmetic или original 4/8/8/8/8 representation |
| `FamilyRelation.Direct.loadObservedState` | Уже соединяет durable votes, sequence, certified current и часть namespaces. **Не покрывает весь state** |
| `loadCertificateBasis`, `loadCertificateParameter`, `loadCertificateRoot`, `loadSufficientAbort`, `loadAbortStateLink` в `FamilyRelation.lean` | Conditional nonempty certificate/ABORT components. Включить в полную relation, сохранив old/current-round lineage и original identities |
| `PublicState.load`, `fieldNames`, `admissible` | Existing 64-field inventory и document guards: depth≤64, nodes≤250000, bytes≤4194304. Их применимость должна быть выведена; нельзя просто добавить public acceptance в source assumptions |

Нынешний blocker — не отсутствие ещё одного numerical lemma. Не соединены
independent source origin, полный snapshot/config/aliases/units и оставшиеся
collections с complete public state. Arbitrary prefilled policy, hash consistency
или callback `authenticated=true` не являются этим соединением.

## 2. Конечный перечень файлов для будущего изменения

Все implementation/proof изменения остаются в существующем proposal boundary.
Ниже имена **планируемых** новых файлов/declarations, не утверждение их наличия.

| Файл относительно repository root | Изменение и output |
|---|---|
| `formal/proposals/b-family-transfer/profile-v1.schema.json` — новый | Одна closed schema family для approved bootstrap/manifest/source-index/trust-record; fixed epoch/local identity, original refs, original cut/sequence, exact floor F и profile bounds. Никаких дополнительных admission restrictions |
| `formal/proposals/b-family-transfer/ProfileSource.lean` — новый | Typed profile metadata, exact canonical-byte binding, primitive trust interface, native-only source-domain/checker и soundness/completeness statements; без imports `FamilyRelation` или public acceptance predicates в source-domain |
| `formal/proposals/b-family-transfer/FamilyRelation.lean` — существующий | `Direct.constructProfileFamily`, полное field/collection/source соединение, applicability и завершающий `Direct.profileR2_3Closed` |
| `formal/proposals/b-family-transfer/ProfileChecks.lean` — новый | Проверяемые positive/non-vacuity и negative boundary instances для того же statement; original widths и identities сохраняются. Synthetic logical instances явно не production attestations |
| `formal/proposals/b-family-transfer/check_profile.py` — новый | Offline schema/source loader + isolated Lean runner, declaration/axiom/dependency audit, source pins и machine-readable closure receipt. Python PASS не заменяет Lean theorem |
| `formal/proposals/b-family-transfer/CONSTRUCTORS.md` — существующий | Одна итоговая запись residual: source domain, theorem names, precise assumptions, covered frozen obligations и limitation до R3 |
| `formal/proposals/evidence/b-family-profile.json` и `formal/proposals/evidence/b-family-profile/` — новые generated evidence | Только новый результат и его kernel/source-audit logs; старые evidence не переписывать |
| `docs/feature010-progress.md` — существующий | Итоговый checkpoint CLOSED либо точный STOP/OPEN, без изменения DoD |

Read-only dependencies: `formal/scripts/native_trace_witness.py`, существующие
source loaders, `formal/proofs/DeltaReduce/Native*`, `PublicState.lean`,
`FamilyInputs/Authority/Parameter/Apply*`, `ShardFamily/StateFamily`.
Existing R2.1/R2.2 checker/evidence не переопределяется новым runner.
`delta-protocol`, `delta-core-cpp`, `delta-runtime-cpp`, production TLA,
mandatory schemas/fixtures/reports и frozen candidate contract не изменяются.
Если этого конкретного file set недостаточно из-за semantic requirement — STOP,
а не автоматическое добавление нового proof project.

## 3. Пять работ, в указанном порядке

| Работа | Точные acceptance criteria | Активные часы |
|---|---|---:|
| **1. Source coverage / stop-check** | Для каждой из 33 native policy позиций, source/config/aliases/units и каждой из 64 public state позиций зафиксирован исходный producer/read path и existing requirement. Проверены native-only genesis/finalization rules и original signed-payload binding; supplied startup не выдаётся за producer. Определено, выводятся ли existing whole-public-state bounds из разрешённого source domain | **2–4** |
| **2. Profile metadata binding** | Schema и `ProfileSource` проверяют canonical bytes, pinned origin/epoch/local identity/codecs, exact F/ApplyQC refs, ordered source refs, retained own cuts и budgets. Bootstrap/floor взяты из независимого trust input. Bad/unknown/missing fields, stale/fork/unsupported epoch не могут стать empty/default authority | **4–8** |
| **3. Independent admissible source** | Native-only checker выводит complete cut из finite original history от pinned genesis и exact source inputs; для каждой collection есть проверенный source constructor/producer. Quorum/context/finalization/current/WAL association проверяется на исходных objects. Есть soundness **и applicability на всём approved source domain**, без R2/public-success premise | **10–18** |
| **4. Full static family relation** | Все 64 public поля и original relevant collections связаны с тем же source/config/aliases/units. Применены CLOSED R2.1/R2.2, синхронные coordinate views без новых protocol identities. Nonempty lineage, current, initial/incomplete legal cuts и sufficient ABORT сохранены. Whole-document guards и static state constraints выведены. General constructor total на admissible profile states | **12–20** |
| **5. Closure audit / receipt** | Exact final statements/dependencies проверены kernel; нет sorry/admit/скрытого oracle. Нельзя пройти только за счёт always-reject/empty domain. Изменения источника, namespace collision, пропущенная collection/vote, неверный QC/floor/cut и потеря ABORT lineage обнаруживаются. Receipt связывает точные source/profile/proof hashes и residual | **4–6** |

**Итого: 32–56 активных часов**, условная инженерная оценка только до R2.3,
если работа 1 подтверждает достаточность existing native source contracts.
Это не бюджет, уже разрешённый пользователем, не срок Formal GO и не стоимость
R3/production recovery/полного R4 gate. Главный риск — complete producer binding
и total applicability complete-state representation, а не schema boilerplate.

После первых **2–4 часов будущей реализации** должен быть содержательный
checkpoint: конечная source map достаточна либо конкретный STOP. Если не найдён
existing producer rule, его нельзя изобрести в оставшиеся часы или заменить
более сильным trust assumption. Остаток бюджета не расходуется на новый scope.

## 4. Планируемые Lean statements и критерий CLOSED

Имена ниже — targets, не созданные Lean definitions. `PrimitiveTrust` содержит
только разрешённые hash/signature/codec abstractions, independently enrolled
epoch/config identity и faithful durable observations/floor в accepted threat
boundary. Не включает legal-origin Boolean, public body, public well-formedness,
успех family checker, recovered-state equality или итог refinement.

1. `ProfileSource.decodeProfileSound`: successful typed load связывает **те же
   raw bytes** с fixed profile fields, canonical encoding, exact refs и bounds.
   Typed descriptor, извлечённый Python, перепроверяется через exact encoding
   equality в Lean; отдельное доказательство универсального JSON parser не нужно.
2. `ProfileSource.checkSourceSound`: успешная проверка при primitive trust
   выводит `AdmissibleSource` из independent native producer rules и original
   prefix. Не из `PublicState.load` и не из translated source equality.
3. `ProfileSource.checkSourceComplete`: для independently specified valid
   profile input/source history checker принимает cut; source-domain определяется
   исходными правилами, а не его собственным successful return. Нельзя скрыть
   неудобный admissible EC/QC case в новом rejection predicate.
4. `FamilyRelation.Direct.profileFieldsExact`: same original source полностью
   определяет поля/configuration/names/units, certificate/candidate/environment
   collections и current; forward/backward coverage сохраняет identities,
   исходные sequences, multiplicity и непустую downstream lineage.
5. `FamilyRelation.Direct.profileFamilyTotal`: для каждого admissible source
   существует constructed synchronous family с действующими public guards и
   complete-state constraints; общая лемма для допустимых original lengths,
   не отдельная подстановка пяти размеров.
6. `FamilyRelation.Direct.profileR2_3Closed`: композиция пунктов 1–5 с точными
   существующими R2.1/R2.2 constructor/domain results.

Требуемый смысл финального statement:

```text
primitive independent trust + valid approved-profile raw inputs
  + independently checked native producing history
    => derived admissible original source cut
    => complete static family relation + existing R2.1/R2.2 conclusions
```

Soundness после `check=success` **недостаточна без completeness/totality** на
approved domain. `AdmissibleSource` не может означать «тот, для которого удалось
построить public state». Whole-state canonical/depth/node/byte constraints
выводятся из исходного domain; новый `fits_R2` guard не допускается. Если profile
допускает исходное состояние, которое не помещается в существующую representation,
нужен точный source counterexample и STOP, а не новый cap или изменение schema.

Initial/incomplete здесь включают законные незавершённые phase/collections при
existing certified current F и source-prefix states, нужные для их происхождения.
Unknown source evidence не превращается в пустое содержимое. Pending anchor и
nonempty pre-first-ApplyQC **import** уже отвергаются approved profile; это не
новые ограничения плана и не удаление general Init/recovery obligations из R3.
ABORT связывается существующим sufficient projection, без нового full-body gate.

Non-vacuity подтверждается legal source construction с непустой certificate
lineage и оригинальной vector shape; hash/signature premises остаются явно
символическими при отсутствии real capture. Нельзя склеить original004 vectors
с чужими scalar008 votes/QCs/WAL и назвать это production evidence. Отсутствие
real external attestation само по себе не создаёт новый local R2 gate, но отсутствие
согласованного допустимого source witness/общей applicability не позволяет CLOSED.

## 5. Stop conditions и граница R3

Немедленный STOP: необходим новый production `Init/Next`, signed certificate
context/semantics, QC/WAL identity, admission restriction или расширение profile.
В частности, два genuinely admissible ISC/QC variants нельзя схлопнуть ради EC
uniqueness. Не добавлять публичную uniqueness в source validity, чтобы исключить
контрпример; показать original native cut/history и конкретную несовместимость.

Не реализуются T volume, filesystem barriers, activation, key provisioning,
signing library, transport, pending-anchor repair или readiness transition.
Не доказывается сохранение relation через crash/persist/expose/send/recovery:
это R3. Проверка **статического** исходного journal/history witness необходима
для R2.3 origin и не объявляется доказательством поведения recovery runtime.

`R2.3 CLOSED` допустим только при general source-to-family theorem, его source
binding/applicability и проверяемом receipt по всему перечисленному scope.
Не достаточно schema PASS, нескольких fixtures или числа проверок. R1/R2.1/R2.2
остаются CLOSED без reopening; R3 и последующие gates остаются незавершёнными.

**STOP после плана.** Сегодня созданы только этот документ и progress checkpoint.
Ни один planned schema/checker/theorem не создан и код не изменён.
