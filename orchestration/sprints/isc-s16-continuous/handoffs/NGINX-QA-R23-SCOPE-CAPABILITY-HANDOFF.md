# Delta → nginx-qa: additional scope amendments

Статус: **WAITING_FOR_EXTERNAL_NGINX_QA_CAPABILITY**. Задание разработчику nginx-qa,
не проект scope-control v2 и не разрешение Delta-исполнителю менять nginx-qa.
Связанные задачи: ISC-S16-CONTINUITY, ISC-S16-D01, T053, HR008-018.

## Требуемый результат

Поддержать второй и последующие **distinct scope amendments** в существующем
сохранённом sprint либо предоставить совместимую forward migration с тем же
наблюдаемым результатом. Внутреннее устройство реализации выбирает разработчик
nginx-qa. Новый sprint, reimport graph, сброс assignment и ручная подмена runtime
не являются допустимым решением.

Пользователь уже разрешил полный R2.3 в пределах принятого Snapshot Provenance
Profile v1, затем `DeltaReduce.nativeArithmeticRecoveryRefines` и применимые gates.
Разрешены formal/reference implementation, Lean/TLA, schemas/checkers, source
binding, evidence, tests, prerequisite closure и штатные reviewer cycles.
Дополнительного разрешения на техническую декомпозицию R2.3 не требуется.
Текущий блокер его запуска — исключительно невозможность отразить это разрешение
в live effective scope. Это не утверждение, что R2.3 уже доказан или что дальнейшие
архитектурные вопросы заведомо отсутствуют.

Production integration, guard removal, изменение утверждённых protocol semantics,
новая trust/authority model, полный R3 и отказ от обязательных gates не разрешены.
Ни scope update, ни migration сами по себе не меняют Formal NO_GO.

## Точка сохранения

| Объект | Точное значение |
| --- | --- |
| API | `http://127.0.0.1:18025` — не порт 8025 |
| Project / sprint | `9000` / `sprint-0001-783ef52c` |
| Repository | `https://github.com/chartjs333/delta.git` |
| Coordinator role | `2750`, `isc-s16-continuity-coordinator` |
| Node / phase / occurrence | `continuity-coordinator` / `node` / `4` |
| Current assignment | `89e70d7d-7b35-43ff-b5c2-cfe96f8526c6` |
| Current graph state | `active`, execution revision `74` |
| Assigned branch | `agent/isc-s16-continuous-sprint` |
| Delta baseline before this handoff | `ca61d5300148c127d76d23cf90592c6247840785` |
| Installed nginx-qa source baseline | `d28726bbcbb552dd21f8cda1042f39f2ee2a21ec` |
| Existing amendment / effective revision | `ISC-S16-D01` / `1` |
| Existing ACK | `scope-ack-c32b5df9df042413dd48394724696bc5` |

Existing amendment source commit:
`65074657df5f9ba3f16b7ac4912a563128d902ee`;
path: `orchestration/sprints/isc-s16-continuous/scope-amendments/ISC-S16-D01-RECOVERY-PROOF-ONLY.json`.
Source SHA-256: `1637f837aca3e028a66e5e1a306a83c695a4d010e35f7b53e54e44cecd38d655`.
Effective-core SHA-256: `a90f0dd692aadfaf356f97489b3741a928d0cb326f8bf8e8aeb63e5bf6f33544`.

Полный текущий `scope_context`, receipt preflight и hashes сохранённых API-компонентов
находятся в [машиночитаемом baseline](NGINX-QA-R23-SCOPE-CAPABILITY-BASELINE.json).
Он фиксирует наблюдение, а не подменяет authoritative live API. Перед любой будущей
mutation заново читать API; revision 74 не использовать как вечное значение CAS.

## Воспроизведённое ограничение

Авторизованный `GET /api/v1/projects/9000/sprints/sprint-0001-783ef52c/scope-amendments/preflight`
возвращает HTTP 200, `amendment_mode=one_shot_v1`,
`accepts_new_amendment=false`, `scope_control_present=true`, `mutated=false`.

В установленной версии второй distinct amendment имеет контракт ответа
`409 {"detail":{"error":"SCOPE_ADDITIONAL_AMENDMENT_UNSUPPORTED"}}`.
Основание: `main.py`, `legacy_scope_replay_transaction`, строки 26517–26555;
`docs/LEGACY_SCOPE_CONTROL_LIMITED_ROLLOUT.md`, строки 991–999.
Этот 409 подтверждён исходниками/документацией, **не выдаётся за выполненный POST**.
Заведомо отклоняемая mutation ради демонстрации ошибки не выполнялась.
Точные source pins сохранены в [предыдущем evidence](ISC-S16-CONTINUITY-R23-SCOPE-INFRA.json).

## Совместимость и критерии приёмки

1. После установки совместимой версии либо forward migration сохраняются project,
   sprint identity, текущие assignment/node/phase/occurrence, graph topology,
   assignments/results/reviews, принятые commits, pending transition и очередь.
   Само обновление не выполняет dequeue, переход узла, новый review или completion.
   Изменение формата хранения требует проверяемого соответствия старых и новых
   записей; не допускает исчезновения или переинтерпретации их содержания.
2. Первый amendment, его source/hash/receipt, предыдущие effective scopes и ACK
   сохраняются как история. Новый distinct amendment не заменяет их identity и
   не переиспользует их idempotency key для другого содержания.
3. Штатный preflight сообщает возможность следующего amendment. Штатный apply
   использует актуальные CAS/assignment/source checks и idempotency. Exact retry
   не создаёт дубликат; конфликтующий retry и stale CAS не дают частичной mutation.
   Эти случаи квалифицировать в тестовом окружении, не разрушительными пробами
   против живого Delta sprint.
4. После нового apply тот же assignment получает новый проверяемый effective
   scope/context с явным приоритетом над конфликтующим historical issued scope.
   Старый ACK не считается согласием с новым scope. Требуется ACK exact нового
   context; stale context не принимается вместо него в result/review submission.
5. Новый scope применяется к предусмотренным участникам текущего графа и их будущим
   assignments. Для каждой новой reviewer identity остаются собственные GET/ACK
   и содержательное решение. Никаких пропущенных reviewer/qualification gates.
6. Квалификация охватывает не только второй, но и последующий distinct amendment,
   перезапуск с сохранением history/lineage и отсутствие частично применённого
   scope при сбое. Это критерии внешнего поведения, не выбор storage design.
7. Сохраняется административная/ролевая граница authentication. Нужен совместимый
   документированный путь для существующих локальных credentials/wrappers либо
   предоставленная разработчиком совместимая замена. Секреты не передаются в
   prompt, JSON body, Git, evidence или chat.

До появления совместимой версии Delta сохраняется без mutation. При последующем
разрешённом apply могут добавиться новый scope/ACK и соответствующий audit с
revision/timestamps; это не разрешение переписывать прежнюю историю или graph.

## Что передать Delta-исполнителю после готовности

- Идентификатор установленной совместимой версии и compatibility/test evidence.
- Документированную процедуру обновления/migration, подтверждение сохранности
  старого sprint и amendment/ACK lineage, список ожидаемых metadata changes.
- Штатные preflight/apply/GET/ACK API и их актуальные payload/CAS/idempotency rules.
  Не требуется присылать секрет или вручную собирать Delta amendment JSON.
- Рабочий безопасный credential-wrapper path, если существующий интерфейс изменён.

Разработку, установку и migration выполняет отдельный владелец nginx-qa.
Delta-исполнитель не проектирует, не патчит и не перезапускает nginx-qa.
Существующий `Delta-Operator.ps1 -Action Launch` — **pre-amendment launcher**,
который отказывает при наличии `scope_control`; он не подходит для рестарта
текущего состояния. Не обходить этот отказ прямым запуском `run.bat`.

Локальная инструкция по credentials:
`C:/Users/madoev/AppData/Local/nginx-qa/ops/delta-18025/USAGE.txt`.
GET effective scope выполняется свежим процессом ролевой обёртки для фактической
роли; admin credential применяется только к штатным operator операциям.
Не менять здоровые demo 8870/8865/8872, другой сервис 8025 или frozen Delta refs.

## Разрешённое автоматическое возобновление

1. Читать текущие HTTP state/preflight и совместимый runbook. Пока capability
   отсутствует, только чтение; при неизменном состоянии — без уведомлений.
2. Проверить сохранность текущего sprint/assignment и предыдущей scope/ACK lineage.
   Не выводить identity из локальных runtime файлов или старого импортированного JSON.
3. После положительного compatible preflight оформить отдельный source-bound
   R2.3 amendment на назначенной Git-ветке, validate и применить через штатный API
   с актуальным CAS и собственным idempotency key. Граф не переимпортировать.
4. Получить effective scope фактической ролью, проверить source/hash/priority,
   выполнить ACK exact возвращённого нового `scope_context`.
5. Продолжить существующий graph: штатные coordinator result/reviews и назначения,
   reviewed закрытие полного R2.3, затем named recovery theorem, axiom audit и
   применимые pinned formal/refinement/compatibility gates. Новый Formal GO возможен
   только по действительным evidence и требуемым authority/review.

R1/R2.1/R2.2 остаются CLOSED; R2.3 OPEN, разрешён к работе после инфраструктурного
разблокирования. Нынешний NO_GO и исторические evidence не relabel. Sequential
reviewer роли одного исполнителя не являются независимой Formal GO аттестацией.
