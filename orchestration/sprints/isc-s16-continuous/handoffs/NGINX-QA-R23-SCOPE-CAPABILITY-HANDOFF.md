# nginx-qa: Human Scope Decisions and Graph Execution UI

Статус: продуктовые требования разработчику nginx-qa. Документ задаёт наблюдаемое
поведение и критерии приёмки; внутренний дизайн и реализация принадлежат отдельному
разработчику инфраструктуры.

Product requirements этого документа универсальны для **любых проектов и
поддерживаемых типов sprint nginx-qa**. Scope approval, Pending decisions и
execution visualization — согласованные части общего UI, без отдельного режима
или hardcoded логики для Delta. Приведённые ниже Delta identifiers служат только
конкретным compatibility/handoff case; роли, nodes, branches и project-specific
qualification статусы UI получает из модели соответствующего проекта.

## Требуемый результат

Поддержать второй и последующие **distinct scope amendments** в существующем
сохранённом sprint либо предоставить совместимую forward migration с тем же
наблюдаемым результатом. Внутреннее устройство реализации выбирает разработчик
nginx-qa. Новый sprint, reimport graph, сброс assignment и ручная подмена runtime
не являются допустимым решением.

**Backend capability недостаточно: обязателен штатный human-approval workflow
в UI nginx-qa.** Оператор принимает semantic scope decision, а оркестратор сам
создаёт versioned amendment, выполняет validation/preflight/CAS/idempotency/apply,
выдаёт effective scope и продолжает граф после exact ACK исполнителя.
Оператор не создаёт JSON, не вычисляет hashes, не запускает PowerShell и не
вызывает REST API для технической доставки решения. Оператор не вводит, не копирует
и не передаёт raw bearer credentials вручную. Это не запрещает UI использовать
штатные authentication tokens/sessions внутри реализации.
Исполнитель или coordinator подаёт структурированный scope request; он не должен
каждый раз вручную писать amendment или переносить длинное ТЗ через пользователя.

## Product requirement: Approve scope change

Название пользовательской операции — **«Разрешить изменение scope» / «Approve
scope change»**. Это append-only переход `scope revision N → N+1`, не reset.

Требуемый поток:

```text
<executor/coordinator> → NEED_SCOPE_CHANGE → nginx-qa persists structured request
→ UI: Approve / Reject / Изменить границы
→ nginx-qa: versioned amendment + validation/CAS/idempotency/apply
→ new effective_scope → exact ACK current role
→ resume existing graph + audit/evidence
```

`NEED_SCOPE_CHANGE` здесь — требование к будущему штатному workflow. Это не
утверждение о поддержке такого outcome установленным API и не команда отправить
его в текущий граф до появления совместимой реализации. Wire schema, endpoints
и внутреннее устройство остаются задачей отдельного разработчика nginx-qa.

Структурированный запрос должен позволять однозначно связать исходный
sprint/assignment/роль и текущий scope revision с запрашиваемой границей,
причиной/зависимостью, сохраняемыми запретами и source/evidence. Это смысловые
данные для серверной проверки и UI, не назначение конкретной wire schema.

Пример карточки для **ещё не принятого** semantic scope decision:

```text
Требуется решение о scope
Graph execution state: <authoritative execution state>
Operator attention: authorization required
Запрашивается: <requested scope>
Причина: <dependency / reason>
Сохраняемые ограничения: <current upper-level boundaries and gates>
[Разрешить] [Отклонить] [Изменить границы]
```

Для уже принятого semantic decision UI показывает «одобрено, ожидает применения»
и его provenance, а не запрашивает то же согласие повторно. Нельзя выдумывать
клик пользователя или автоматически одобрять другие границы. Конкретный ранее
одобренный запрос приведён в compatibility fixture ниже.

### Приёмка пользовательского workflow

1. Исполнитель отправляет machine-readable request непосредственно оркестратору.
   nginx-qa сохраняет его и показывает человеку scope, причину и сохраняемые
   запреты. Передача JSON или длинного технического письма через человека не нужна.
2. `Approve` связывает решение с exact содержанием запроса и текущей версией scope.
   nginx-qa сам оформляет и применяет следующий amendment через штатные проверки.
   Повторный клик/retry не создаёт лишнюю версию; stale решение не применяется
   молча к изменившимся scope или границам.
3. `Reject` сохраняет запрос и отказ в истории; запрошенное расширение не вступает
   в силу, прежний scope/ACK/history не стираются. При `Approve with changes` /
   «Изменить границы» отредактированное решение проходит **ту же server-side
   validation, что и исходный request**. До подтверждения UI показывает **exact
   resulting scope diff** относительно актуального effective scope, включая
   сохраняемые ограничения. Approval относится именно к проверенному результату;
   изменение исходной revision требует обновлённых validation и diff. Исправленное
   содержание не наследует approval другого содержания. Исполнитель получает
   фактически одобренные границы.
4. Предыдущие amendments, ACK, assignments, results и reviews остаются immutable.
   Audit/evidence связывает request → decision → amendment → effective scope
   → ACK → resume. Старый ACK не разблокирует работу по новой версии.
5. После exact ACK текущей роли граф автоматически продолжает штатный цикл,
   сохраняя reviewer и qualification gates. Человек не доставляет результат
   обратно агенту и не выполняет API/PowerShell-команды.
6. Внутри уже разрешённых верхнеуровневых границ обычные prerequisites, helper
   lemmas, файлы, tests и reviewer cycles не порождают повторных запросов approval.
   Новое участие человека нужно для следующего semantic scope decision за этими
   границами, а не для технической доставки предыдущего решения.

Эти требования дополняют backend compatibility ниже. Scope decision не заменяет
review, qualification или иные обязательные gates соответствующего проекта.

## Product requirement: Graph observability / execution visualization

Главный экран sprint объединяет **Graph**, **Current assignment**, **Pending
decisions** и **Execution timeline**. Пользователь без PowerShell, curl, raw JSON,
filesystem или Git inspection видит: что и кем выполняется, где находится sprint,
что уже прошло, где и почему возникло ожидание, требуется ли решение человека и
что произойдёт после него. Расположение, цвета и конкретные компоненты выбирает
разработчик UI; отдельный Delta dashboard не требуется.

### Topology и текущее выполнение

UI показывает полный graph topology, текущие node и phase, current assignment,
выданную роль/agent и Git branch при её наличии. Видны пройденные, ожидающие,
заблокированные и reviewer nodes, выполненные transitions, повторные visits,
execution revision, active effective scope revision, pending scope request,
ACK status и terminal state. Formal/qualification status отображается, если он
предусмотрен моделью проекта; его отсутствие не означает PASS или NO_GO.

### Graph execution state и operator attention state

UI явно разделяет две независимые характеристики:

| Характеристика | Значение и источник |
| --- | --- |
| `graph execution state` | Фактическое состояние выполнения из authoritative execution model: текущая позиция, phase и terminal status. |
| `operator attention state` | Причина ожидания или требуемого внимания, связанная с сохранёнными request/decision/application/ACK events; не подменяет execution state. |

Например, одновременно могут отображаться `execution_state=active` и
`attention=waiting_for_scope_application`: решение уже принято, техническое
применение ещё ожидается. Это смысловой пример отображения, не новый API enum
или обязательное имя wire field. UI показывает причину, статус решения и
следующий ожидаемый шаг. Ожидание operator decision, scope application и ACK
различаются; отсутствие нового решения человека не означает отсутствие ожидания.

Изменение attention само по себе не передвигает execution pointer и не создаёт
фиктивный `blocked` или terminal state. И наоборот, terminal state нельзя
определять по attention или project-specific qualification status.

Состояния и события должны визуально различаться; смысловые примеры:
`completed`, `active`, `waiting`, `blocked`, `review_pending`, `rejected`,
`skipped`, `terminal`. Это требования к отображению реальных состояний, а не
единый enum для execution, attention и review. Непройденный conditional branch
не помечается `skipped` без соответствующего решения графа. Неизвестные либо
отсутствующие данные показываются явно, не подменяются успехом или нулём.

Topology и execution history — разные сущности. Возврат в тот же node создаёт
новый отображаемый occurrence/visit, сохраняя предыдущие:

```text
<node>
  visit #1 — completed
  visit #2 — completed
  visit #3 — completed
  visit #4 — waiting (reason visible)
```

UI не ограничивается перекраской одной вершины и не выводит прошлые посещения
из её нынешнего статуса. Каждый visit связан с собственными assignments,
результатами, reviews, scope и ACK. Примеры имён и номеров не являются fixtures
или hardcoded правилами реализации.

### Execution timeline и drill-down

Помимо topology view необходим упорядоченный timeline с timestamp и привязкой
к execution revision/event identity. В нём отдельно видны assignment issued,
delivery/claim, result submitted, reviewer assignment, review decision, transition,
повторный visit, scope request, решение оператора, применение scope, ACK, resume
и terminal event — в пределах событий, реально сохранённых данной моделью.

Любое событие открывается для просмотра связанных metadata: project/sprint,
node/visit, assignment, роль, result/review, transition, scope revision, ACK,
commit/evidence references и причины отказа/ожидания. Это навигация по связям
сохранённых записей; пользователю не нужно вручную сопоставлять IDs через API.
Старые события не пересчитываются на основании current state.

### Scope overlay и Pending decisions

Для конкретного assignment/visit отображаются действовавший effective scope,
его revision и соответствующий ACK. Открываемая из graph карточка pending
decision — тот же объект и те же действия, что в общем Pending decisions UI,
а не отдельная копия approval workflow.

Различимы состояния «решение pending», «approved, применение pending»,
«новый scope применён, ACK pending» и «ACK accepted, graph resumed».
Запрошенная будущая revision показывается только если её уже определил сервер;
предложение N+1 нельзя выдавать за применённый scope. Один click Approve не
означает, что ACK уже получен или выполнение возобновилось.

Scope overlay использует раздельные execution/attention характеристики выше.
Qualification status проекта остаётся отдельным показателем и сам по себе
не означает terminal state sprint.

### Reviewer gates и queue/assignments

Review — отдельное execution event. Его карточка содержит reviewer role,
assignment, decision, timestamp, точный reviewed result/evidence/commit,
required approvals, фактически полученные применимые approvals и reject reason
при наличии. Approval другого результата не считается approval текущего.
Возвраты на rework и повторные reviews сохраняются в истории; итоговая галочка
не заменяет эти события.

UI показывает current active и queued/pending assignments, их адресатов,
породившие node/visit, branch при наличии, delivery/claim/ACK status и scope,
который к ним привязан или будет применён согласно authoritative API.
Если future scope ещё не определён, UI показывает это явно. Чтение графа или
раскрытие карточки не должно claim/dequeue assignment или посылать ACK за агента.

### Live updates и historical mode

Автоматическое обновление обязательно; WebSocket, SSE или polling с
revision/event cursor выбирает разработчик. Ручной refresh не требуется.
При reconnect пользователь должен получить пропущенные события без потери и
визуального дублирования history. UI показывает состояние синхронизации и
наблюдаемую revision, не выдавая устаревший snapshot за подтверждённое новое
состояние. Historical view не перепрыгивает в latest mode без выбора пользователя.

После завершения sprint этот же экран работает как audit viewer. Выбор
`Project → Sprint → execution revision / timestamp` открывает topology и
сохранённую execution history на выбранный момент, включая старые assignments,
reviews, scope revisions, ACK и transitions. Текущий scope не подставляется в
карточки прошлых visits. Источником служит сохранённая история, не реконструкция
из нынешнего graph pointer.

### Разрешённые действия

Из graph доступны открытие pending scope decision, Approve/Reject/Изменить
границы в пределах прав оператора, assignment/result/review, evidence,
effective scope и audit trail. Действуют те же authorization и concurrency
checks, что у общего workflow. Просмотр истории не даёт права менять её.

Произвольное перетаскивание execution pointer или ручная отметка node completed
не входят в обычный UI. Возможная administrative recovery operation требует
отдельного явного полномочия и не проектируется этим handoff.

### Проверяемая приёмка общего UI

1. На compatibility fixture ниже и другом поддерживаемом проекте один
   экран показывает topology, active assignment/роль, branch при наличии,
   revisions и раздельные execution/attention states. Optional поля корректно
   отсутствуют; ожидание применения одобренного scope не создаёт ложный terminal.
2. Цикл с возвратом в node сохраняет несколько occurrences; drill-down каждого
   показывает собственные result/reviews/scope/ACK, не последние общие значения.
3. Два reviewer gate, reject/rework и повторный review отображаются отдельными
   событиями с привязкой к reviewed result и корректным счётчиком approvals.
4. Pending decision проходит request → decision → applied scope → exact ACK
   → resume в graph и timeline согласованно с API. Уже одобренный запрос не
   получает лишнего consent; Reject сохраняет историю. `Approve with changes`
   проходит ту же server-side validation и показывает exact resulting scope diff
   до подтверждения; stale diff не применяется к новой revision.
5. Queue item открывается вместе с породившими node/visit и delivery/claim/ACK;
   чтение UI не изменяет assignment, очередь, scope или execution pointer.
6. При live updates/reconnect история догружается, а выбор старой revision
   воспроизводит её сохранённое состояние. Terminal sprint доступен для audit.
7. В нормальном workflow пользователь получает ответы о progress/blocker/decision
   через UI без scripts/JSON. Нельзя произвольно продвинуть pointer, закрыть node
   или обойти review/ACK через элементы визуализации.

Изменений runtime, schemas или реализации визуализации в этом документе нет.

## Compatibility fixture: existing Delta sprint

**Приложение: реальный migration/compatibility fixture.** Все конкретные IDs,
SHA, роли, branches, ограничения, endpoints и Formal NO_GO ниже относятся только
к существующему Delta deployment. Они не являются полями, константами или
обязательными статусами core-модели nginx-qa. Раздел служит проверке сохранности
реального состояния при реализации общих product requirements выше.

Статус fixture: **WAITING_FOR_EXTERNAL_NGINX_QA_CAPABILITY**.
Связанные задачи: ISC-S16-CONTINUITY, ISC-S16-D01, T053, HR008-018.
Реализация nginx-qa остаётся у отдельного разработчика; Delta-исполнитель не
проектирует scope-control v2 и не меняет nginx-qa.

### Авторизация и границы fixture

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
Ни scope update, ни migration сами по себе не меняют Formal NO_GO. Product scope
этого документа не добавляет proof/qualification gate R2.3/R3 и не меняет Delta DoD.

Для **текущего** R2.3 решение уже принято пользователем. Его состояние —
«одобрено, ожидает инфраструктурного применения», а не «нужно снова разрешить».
Совместимая версия должна штатно отразить уже принятое решение с его provenance;
никакого выдуманного клика, нового consent или автоматического одобрения иных
границ. Источник текущей авторизации указан в
[сохранённом evidence](ISC-S16-CONTINUITY-R23-SCOPE-INFRA.json).

В этом fixture graph API остаётся `active`, а attention означает ожидание
применения уже одобренного scope. Нельзя создавать вместо этого фиктивный
terminal `blocked`, pending human decision или новый approval request.
Formal NO_GO остаётся отдельным project-specific qualification status.

### Точка сохранения

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

### Воспроизведённое ограничение

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

### Совместимость и критерии приёмки fixture

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

### Что передать Delta-исполнителю после готовности

- Идентификатор установленной совместимой версии и compatibility/test evidence.
- Документированную процедуру обновления/migration, подтверждение сохранности
  старого sprint и amendment/ACK lineage, список ожидаемых metadata changes.
- Штатные preflight/apply/GET/ACK API и их актуальные payload/CAS/idempotency rules.
  Не требуется присылать секрет или вручную собирать Delta amendment JSON.
- Рабочий machine-readable scope-request flow, UI `Approve / Reject / Изменить
  границы` и evidence автоматического request-to-ACK-to-resume сценария, включая
  штатное отражение уже принятого решения по текущему R2.3.
- Общий Graph/Timeline/Pending decisions UI и evidence его приёмки: повторные
  visits, reviewer gates, scope/ACK overlay, очередь, live updates и historical
  audit на Delta и другом поддерживаемом проекте.
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

### Разрешённое автоматическое возобновление

1. Читать текущие HTTP state/preflight и совместимый runbook. Пока capability
   отсутствует, только чтение; при неизменном состоянии — без уведомлений.
2. Проверить сохранность текущего sprint/assignment и предыдущей scope/ACK lineage.
   Не выводить identity из локальных runtime файлов или старого импортированного JSON.
3. После положительной проверки совместимости использовать штатный структурированный
   scope-request/approval flow nginx-qa и provenance уже принятого решения R2.3.
   Создание source-bound amendment, hashes, validation/CAS/idempotency/apply —
   обязанность оркестратора, не ручная процедура пользователя или Delta-исполнителя.
   Не запрашивать повторное разрешение R2.3; не имитировать отсутствующий UI/API
   ручной правкой runtime. Граф не переимпортировать.
4. Получить effective scope фактической ролью, проверить source/hash/priority,
   выполнить ACK exact возвращённого нового `scope_context`.
5. Продолжить существующий graph: штатные coordinator result/reviews и назначения,
   reviewed закрытие полного R2.3, затем named recovery theorem, axiom audit и
   применимые pinned formal/refinement/compatibility gates. Новый Formal GO возможен
   только по действительным evidence и требуемым authority/review.

R1/R2.1/R2.2 остаются CLOSED; R2.3 OPEN, разрешён к работе после инфраструктурного
разблокирования. Нынешний NO_GO и исторические evidence не relabel. Sequential
reviewer роли одного исполнителя не являются независимой Formal GO аттестацией.
