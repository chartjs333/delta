# Delta ISC Sprint 16 — pipelined verification

Все sprint-файлы хранятся в Git и доступны на канонической ветке:

- branch: `agent/isc-s16-pipelined-sprint`
- path: `orchestration/sprints/isc-s16-pipelined/`
- source baseline: `codex/feature000-binding-candidate@ea5a70d8c5fd3516de243632f2c5681b0e5a6292`

Каждая рабочая и reviewer-ветка создаётся от `origin/agent/isc-s16-pipelined-sprint`. Поэтому sprint JSON, bootstrap, карта ветвей, task-spec и SHA manifest присутствуют в ancestry и доступны прямо на ветке агента.

## Импорт

- `parallel-sprint.json` — первоначальный запуск четырёх параллельных lane: contract, W1, crypto, formal.
- `parallel-resume-after-a01.json` — безопасное возобновление после уже выполненного `ISC-S16-A01`: два независимых reviewer задания для commit `a579a5c66586ba3f8f1d7cc26c454aba5addbd8f` плюс параллельные W1/crypto/formal lane.
- `w1-one-branch-sequential-sprint.json` — только W1 с двумя reviewer gate.

`parallel-sprint.json` и `parallel-resume-after-a01.json` должны импортироваться только как **parallel** sprint: через direct project import или parallel Telegram/pending-sprint route. Не отправляйте их в sequential endpoint. Sequential endpoint принудительно создаёт `queue_graph`; `agents.items` тогда не имеет declared workflow/transitions/reviewer gate.

Не импортируйте одновременно несколько вариантов, использующих одну и ту же рабочую ветку.

## Обязательные правила

1. Assigned branch создаётся от `origin/agent/isc-s16-pipelined-sprint`.
2. `git merge-base --is-ancestor ea5a70d8c5fd3516de243632f2c5681b0e5a6292 HEAD` должен завершиться успешно.
3. Каталог `orchestration/sprints/isc-s16-pipelined/` нельзя удалять или менять рабочим lane.
4. Reference code не является production implementation и не снимает formal-first STOP.
5. Join/qualification запускается отдельным sprint после exact commit SHA всех lane и reviewer reports.
6. В parallel mode роли постоянны на время sprint; общий `/api/v1/agents/whoami` и sequential assignment outcome routing не используются.
7. Если sprint был ошибочно запущен как sequential `queue_graph`, не делайте новый dequeue и не выбирайте successor вручную. Заархивируйте mis-imported sprint административно и импортируйте подходящий parallel resume JSON.
