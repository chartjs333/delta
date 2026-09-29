# R2.3 stage 1 — INSUFFICIENT / ARCHITECTURE STOP

29 сентября 2026. T047/T053. Только аудит existing producer rules / bounds.
Начало: 21:25:07 UTC; бюджет максимум 4 активных часа. Остановка до исчерпания
бюджета по найденному producer gap. Этапы 2–5 и R3 не начаты.

Source base: `65a2ab46a1726fffd66dbd0721c6eb51bdd06352`.
Native policy/WAL pin: `60c692f6e391f839829dfc64e93380db54cd507b` (PR50,
не merged runtime authority). Approved Profile v1 SHA256:
`7cd4170171d554e8f3b34f0a76e28643dfa9650dc49e06ff42526e6236063e4a`.
Frozen DoD и профиль не изменены. Это source audit, не новый formal proof,
не native execution и не обнаруженная production-reachable EC атака.

## Минимально недостающее правило

**Не задан независимый native producer transition, связывающий финализацию
первого ISC с изменением полного `VoteAdmissionSnapshot` и исходной history.**
В частности, отсутствует source-bound переход для пары
`input_set_certificates` / `finalized_input_set_ids`: из предшествующего native
состояния и исходных голосов получить конкретный finalized certificate с его
исходным signer set/QC identity, зафиксировать membership коллекций и связь
с существующей policy/journal history.

Это уже требуется Profile v1 §4, пункты 1–4: использовать existing native
producer, выводить поля из prior state/original inputs, различать наличие
certificate и событие финализации, воспроизводить весь cut от genesis.
Нового safety obligation здесь не добавлено. Аудит показывает, что требуемый
producer contract нельзя получить простой композицией имеющихся readers,
validators и replay folds.

Минимальная иллюстрация недостающего ребра — **не новый predicate и не
исполненный контрпример**:

```text
один закрытый исходный ISC body + исходные quorum votes
предшествующий cut: input_set_certificates=[], finalized_input_set_ids=[]
        -- отсутствующее native producing/finalization binding -->
следующий cut:      input_set_certificates=[q], finalized_input_set_ids=[id(q)]
```

Для этой иллюстрации не нужны два EC, конфликтующие QCs, coordinate identities,
большая history или изменение shard widths. Даже происхождение одного первого
ISC не выводится имеющимися native rules. Approved nonempty import требует
ApplyQC/current F и его ISC lineage; ограничить source domain пустым genesis
или только уже реализованными guarded executions нельзя.

## Проверенные основания

Номера native строк ниже относятся **к PR50 pin**, не к старой C++ копии в
candidate checkout. Хеши и диапазоны сохранены в
[source audit](evidence/0013-r2-3-stage1-source-audit.json).

| Источник | Что существует | Почему это не закрывает producing edge |
|---|---|---|
| `specs/008-certificates-and-consensus/spec.md`: US1, FR-003–FR-006; `runtime-profile.md`: Native ownership | Quorum финализирует ISC, downstream требует finalized ISC; graph принадлежит C++ | Нормативное требование уже есть. Оно не задаёт native history event, полный snapshot update и связь с исходным WAL |
| `formal/tla/DeltaReduceCertificates.tla:4–16,187–201` | `CertificateInit` пуст; `FinalizeISC(body)` использует `ISCSigners(body)`, quorum и отсутствие finalized ISC для round; добавляет certificate | Это существующий **public** producer. Profile §4 запрещает заменить независимый native producer вызовом public `Next`/успехом R2. Перенос public action на native bytes/identities ещё не является существующим native правилом |
| `delta-core-cpp/include/delta/core/consensus.hpp:233–251` | Snapshot прямо объявлен immutable projection уже подготовленного состояния; обе коллекции — входные поля | Prepared state не имеет доказанного origin только от факта его передачи |
| `delta-core-cpp/src/certificates/verifier.cpp:181–185`; `vote_admission.cpp:465–479` | Проверка context/signers/content ID, ordering и finalized-ID subset typed certificates | Функции читают готовый certificate/collection; не выбирают событие финализации, не обновляют предшествующий snapshot |
| `delta-runtime-cpp/src/vote_codec.cpp:868–881` | Декодирование supplied snapshot заполняет обе коллекции | Decode присваивает переданные bytes, не производит их из protocol history |
| `delta-core-cpp/src/transition.cpp:84–95,165–222` | `FINALIZE_INPUT_FREEZE` меняет `RoundState.phase` на `eligible`; `apply` вычисляет RoundState/effects/WalRecord | В аргументах/result нет полного `VoteAdmissionSnapshot`; ISC collections не обновляются. Название команды не даёт недостающей семантики |
| `delta-runtime-cpp/include/delta/runtime/runtime.hpp:65–77,106–134`; `src/runtime.cpp:126–130,232–305,423–428,488–503` | Startup принимает immutable policy; submit меняет RoundState и invalidates vote authority; vote WAL закрепляет startup policy identity | Нет операции финализации/замены policy с origin continuity. Перезапуск с другой policy не чинит её происхождение: replay проверяет прежнюю policy identity |
| `formal/proofs/DeltaReduce/NativeReplayAdmission.lean:20–30`; `NativeCandidateAuthority.lean:186–226` | `prepareWhole`, `bindPolicy`, `preparedSource` связывают supplied policy/state и проверенные entries | Theorem premises уже содержат policy bytes; получение этих collections от genesis не следует |
| `formal/proofs/DeltaReduce/NativeConfigReplay.lean:18–20,50–62`; `NativeCurrentHistory.lean:32–42` | Journal fold обновляет core/votes при фиксированном policy; current row читает supplied policy и finalized ApplyQC | Ни один fold не производит полные policy collections. Правильный current suffix не доказывает origin его исходной базы |

Дополнительно проверены `NativeIscAdmission` и `NativeIscCertificate`: первое
явно исключает finalized graph из proposal subdomain; второе проверяет shape,
quorum/IDs уже переданного certificate. Их свойства остаются действительными.
`CertificateVoteRuntime` в PR50 делегирует `persist_and_expose` тому же
`Runtime::record_vote`; отдельного скрытого finalize producer там нет.

Поиск всех упоминаний двух native полей в production C++ pin, вместе с
исчерпывающей dispatch-веткой `apply_command` и API Runtime, обнаруживает
объявления, serializer/decoder и validation reads, но не history transition
создания/финализации этих collections. Это ограниченный вывод о проверенных
sources; не утверждение о невозможности будущего корректного producer.

## Почему нельзя объявить SUFFICIENT

Доверенный bootstrap, genuine signatures, известный floor и сохранённый WAL
не превращают supplied immutable snapshot в state, произведённый отсутствующим
native transition. Даже если предоставить все разрешённые crypto/trust inputs,
этот gap остаётся. `producer_rules_id` закрепляет правила, но не создаёт их.

Использовать validation готового snapshot как origin означало бы подменить
утверждённый профиль. Принять public `FinalizeISC` за native action без
source binding либо самостоятельно определить update для snapshot означало бы
добавить producer rule, что пользователь прямо запретил на данном этапе.
Ни один из этих обходов не реализован. Из результата также **не следует**, что
обязательно нужно менять production `Init/Next`, certificate semantics или
QC/WAL identities: пока установлен более ранний недостающий contract edge.

Старый API witness `ISC@1 → EC@2 → EC@3` здесь не используется как допустимый
production/profile counterexample. Его reachability этим аудитом не доказана.

## Representation bounds и остаток

| Проверка | Результат |
|---|---|
| Existing native producer rules достаточны для approved full source history | **INSUFFICIENT** — отсутствует указанное ISC producing/finalization binding |
| Existing whole-public-state bounds следуют из всего approved source domain | **НЕ УСТАНОВЛЕНО**; дальнейший вывод остановлен на producer gap |

Сверены exact guards `PublicState.admissible`: depth ≤64, nodes ≤250000,
whole document bytes ≤4194304. Profile limits — control document ≤4 MiB,
refs ≤65536, bundle ≤64 GiB, source events ≤1000000 и WAL/pointer records
≤1000000 суммарно. Эти ограничения относятся к разным объектам; меньший лимит
на public document не является сам по себе контрпримером. Не предъявлен
допустимый produced cut, который его превышает, и не доказана общая совместимость.
Новый `fits_R2` guard, pruning lineage или cap не добавлены.

Полный planned 33/64-field coverage inventory **не завершён**: immediate STOP
сработал на первом необходимом certificate edge. Это не новое разложение R2.3
и не переход к следующему proof layer. Бинарный итог определяется уже найденной
недостаточностью producer rules; незавершённая проверка bounds не маскируется
как PASS или как самостоятельный доказанный архитектурный дефект.

**R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; R3 не начат.** Код, proofs, schemas,
fixtures, source-domain restrictions и protocol identities не менялись.
19 pinned baseline input hashes проверяются audit receipt; старые formal results
не инвалидируются documentation-only checkpoint и не объявляются новыми GO.

Предыдущая оценка следующих этапов **30–52 активных часа была условной** на
SUFFICIENT. Условие не выполнено, поэтому это больше не подтверждённая оценка
до CLOSED; стоимость устранения producer gap в неё не включена. Новую численную
оценку без отдельного решения о недостающем binding дать обоснованно нельзя.
Разрешённый этап завершён: **INSUFFICIENT / ARCHITECTURE STOP**.
Никакого автоматического продолжения R2.3, исправления или R3.
