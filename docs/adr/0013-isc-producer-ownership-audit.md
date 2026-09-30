# ISC producer ownership audit — MISSING PRODUCTION TRANSITION

30 сентября 2026. T053 / T016 (feature 008) / HR008-002/003.
Только source/design audit, без реализации или продолжения R2/R3.
Source base: `54f028e1dc55e6b5966701f609801312be5fb28f`.
Native/sidecar pin: `60c692f6e391f839829dfc64e93380db54cd507b` (PR50).

**Результат: 3. MISSING PRODUCTION TRANSITION.**

Существенное уточнение классификации: **owner, абстрактный protocol contract и
формальный producer уже существуют**. Неверно говорить, что ISC не был
спроектирован вообще. Отсутствует полный исполняемый native путь
`received quorum votes → finalized canonical ISC → durable/exposed state`
и конкретная привязка этой транзакции к native state/WAL. Контракта передачи
этого производства внешнему authority не найдено; действующая архитектура
прямо запрещает Java/Python принимать такие consensus decisions.

Это пропущенное звено ранее запланированного native production пути,
а не обнаруженное намеренное делегирование и не только несвязанный R2 lemma.

## 1. Кому первоначальный design поручил работу

Под первоначальным design здесь понимается принятый BFT/hybrid design до
R2 и ADR-0013, а не отменённый central-coordinator prototype.

| Design source | Уже существующее назначение |
|---|---|
| ADR-0001, первоначальный commit `644770e5c19badc4b3403c80d1718371a92b29e1`, 23 августа | BFT validators и quorum certificates заменяют authoritative central coordinator. Возврат central authority требует отдельного major amendment |
| ADR-0010, первоначальный commit `1ef5950d94c7046409c739d46cff265f7f4dd918`, 25 августа | Pure C++ core вычисляет legal canonical next state; `delta-runtime-cpp` владеет single-writer reactor/WAL/snapshots и release-after-durable-commit; Java не выбирает quorum/membership |
| Feature 008 `runtime-profile.md`, первоначальный commit `1dd8cfe1b8fad4434f1dbccc80e4c2600e6e70c1`, строки 3–38 | C++ owns complete ISC→…→ApplyQC graph; native vote lifecycle; Java sends only returned canonical frames |
| Feature 008 `plan.md`, тот же первоначальный commit, строки 32–53 | Прямо предусмотрен `ISCBuilder/QC → SeedTranscript`; в нынешнем плане это строки 44–67 и implementation step 4, строка 110 |
| `specs/HYBRID-RUNTIME-MAP.md:9–13,45–47` | C++ core/runtime — semantics и durability; Java — transport; `delta-protocol` — runtime-neutral schemas |

Следовательно, owner — **native consensus implementation**, разделённая на
pure C++ computation/validation и native runtime durability/exposure.
Java/Netty доставляет сообщения этому owner. Он не становится producer при
отсутствии C++ обработчика. Controller не является запасным ISC authority.

## 2. Что именно уже определяет formal contract

В `formal/tla/DeltaReduceCertificates.tla`:

- `VoteISC` (167–185) вызывает `PersistVoteEnvelopeChanges` и добавляет ISC vote;
- `ISCSigners(body)` (116–118) берёт validators из **delivered** votes;
- `FinalizeISC(body)` (187–201) требует closed input body, quorum и отсутствие
  finalized ISC для round, затем добавляет `[body, signers]` в
  `inputSetCertificates`;
- `FinalizeISCAction` входит в `CertificateNext` (774–778), тот — в production
  `DeltaReduce.OrdinaryNext/Next` (22–29,47).

`DeltaReduceQuorums.tla:50–60,110–145` отдельно задаёт persist, send и delivery
голосов. Таким образом, formal финализация не равна накоплению локальных votes,
созданию произвольного certificate object или проверке его hash.

`FinalizeISC` — абстрактный state transition; он не объявляет Java callback,
внешний signer service или отдельный controller authority. Его `BaseVariablesUnchanged`
не задаёт конкретного native WAL record/полного snapshot update. Общий порядок
`compute → append WAL → barrier → commit → expose` уже требует ADR-0010.
Самостоятельно дополнять этот порядок новым concrete producer здесь нельзя.

## 3. Проверенный production путь и точка разрыва

Native номера строк далее относятся к PR50 pin; Java certificate classes
совпадают byte-for-byte в pin и candidate. Exact blob hashes — в
[source audit](evidence/0013-isc-producer-ownership-source-audit.json).

| Компонент / точный entry point | Фактическая роль | Полный ISC producer? |
|---|---|---|
| `delta-core-cpp/src/consensus.cpp`: `InputLedger::freeze` (690–711) | Замораживает ordered available tuples | Нет quorum votes, certificate signer selection или durable finalization |
| Там же: `VoteJournal::record` (513–538), `validate_quorum` (543–587) | Запись/uniqueness отдельного vote; проверка уже переданного generic QC | Не собирают finalized typed ISC из received votes |
| `certificates/contracts.cpp:240–275`; `verifier.cpp:181–185` | Canonical bytes/content ID и проверки supplied typed ISC | Нет stateful finalization/commit |
| `certificates/vote_admission.cpp:323–332,453–479` | `as_input_certificate` временно оборачивает proposal с `policy.validator_ids` для validation; finalized collections проверяются как supplied inputs | Helper не выбирает signers из полученного quorum и не публикует/фиксирует QC; его нельзя считать producer |
| `consensus.cpp:352–358`: `project_input_set_vote_body` | Извлекает proposal body из готового certificate | Направление certificate→body, а не votes→certificate |
| `transition.cpp:84–106`: `FINALIZE_INPUT_FREEZE` | Проверяет AVAILABLE/nonempty count, переводит `RoundState.phase` в eligible | Не проверяет quorum votes и не формирует ISC collections |
| `runtime.cpp:126–130,232–305,423–428,488–503` | Startup policy immutable; submit durably меняет RoundState и invalidates vote authority; record_vote сохраняет vote и policy identity | Нет complete certificate-state finalize/update transaction; общая durability инфраструктура не добавляет её сама |
| `delta-ffi/src/delta_abi.cpp:282,290–316`; `sidecar_server.cpp:748–774,811–835` | FFM/sidecar вызывают именно `Runtime::record_vote` или `Runtime::submit` | Другого semantic handler за boundary не обнаружено |
| Java `LocalSidecarClient.submitRequest/voteRequest:228–247` | Передаёт opaque command/vote bytes | Transport-only |
| Java `AuthenticatedCertificateTransport.deliverReady:55–66` | Передаёт envelope в `NativeSink.accept` | Callback доставки не содержит producer contract/authority |
| Java `NativeCertificateVerifier.inspect:21–48` → `certificates_abi.cpp:103–136` | Read-only certificate bytes/ID inspection; возвращает inspection effect | Не quorum assembly и не durable state mutation |

Из этих входов не получается цепочка от quorum ISC votes к durable finalized
certificate. Наличие serializer, `verify_input_set`, callback `NativeSink`,
generic `PUBLISH_CERTIFICATE` effect или prepared snapshot не заполняет этот
разрыв. Нет найденного отдельного production `ISCBuilder` за пределами плана.

Аудит проверил обе группы возможных обходов: native typed constructors/codec
и Java/FFM/sidecar forwarding. Поэтому вывод не основан только на поиске имени
`ISCBuilder` или на отсутствии отдельного exported `finalize_isc` символа.

## 4. Controller и существующие contracts

`delta-controller-python/README.md` назначает controller роли Authorization Gate:
caller authentication, policy, grants, idempotency и подпись `AdmissionRecord`
для worker execution. Это другая authority и другой signed object.
`specs/admin-ui/step5c-controlled-live-execution/runtime-profile.md:11–21,38–40`
прямо исключает consensus decisions и отличает controller ledger от consensus
WAL. `spec.md:91–95` запрещает local fabrication QC/WAL fields. Ни live demo,
ни подпись admission не делегируют controller право создавать finalized ISC.

Существуют три группы релевантных contracts:

1. **Protocol rule / ownership:** feature-008 US1/FR-003–006, ADR-0010,
   `formal-refinement.md` и TLA выше. Они требуют именно native refinement.
2. **Object/bytes:** `InputSetCertificate` в `contracts.hpp:78–85`, canonical
   encoder/content ID и `delta-protocol/schemas/008/input-set-certificate-v1.json`.
   Поля — context, input_root, quorum_threshold, signer_ids, tuples, версии.
   Schema определяет объект, не producer или authority внешнего сборщика.
3. **Generic native boundary/durability:** Runtime/FFM/sidecar command/vote API
   и persist-before-expose. Отдельного concrete ISC-finalization transaction
   contract, соединяющего входной quorum, finalized collections и existing
   WAL/replay/exposure, в проверенных источниках нет.

Поэтому результат **не INTENTIONALLY EXTERNAL PRODUCER**. Назначить такую
authority по факту наличия callback или принятых prefilled bytes противоречило
бы действующему ownership.

## 5. Почему старые завершённые задачи/evidence не дают другого ответа

Feature-008 `T016` отмечен выполненным, но checkbox не заменяет production path.
Native test `certificates_test.cpp:71–87` создаёт `InputSetCertificate` с явно
заданными signers; это fixture construction. Trace generator
`generate_refinement_traces.py:20–40` берёт ID из golden fixture и записывает
`ACT-ISC-FINALIZE`; это не capture исполнения недостающего native producer.
`native-execution.json` и `certificate-refinement.json` явно содержат
`semantic_completeness_claimed: false`.

Старые результаты остаются результатами своих exact sources/statements.
Аудит не переписывает task checkboxes, не инвалидирует существующие proofs и
не объявляет новые test/formal runs. Он не повышает partial evidence до
end-to-end production completeness.

## 6. Контрольная точка

**3. MISSING PRODUCTION TRANSITION — при уже заданных native owner и
abstract formal semantics.** Фраза «ни producer, ни его контракт» применима
здесь только к **конкретному production переходу и его state/WAL binding**;
она была бы неверна применительно к исходному protocol/ownership contract.

Требуется отдельное production architecture decision о реализации/интеграции
этого отсутствующего native звена в рамках уже заданного ownership. Этот audit
не выбирает новый transition, predicate, authority, WAL encoding или QC identity.
Не установлено, что нужно менять formal `Init/Next` или certificate semantics.

R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN. R2/R3 не продолжались. Profile v1 и DoD
сохранены; healthy demo не трогалось. **STOP после audit**, без автоматической
реализации, proof work или нового architecture design.
