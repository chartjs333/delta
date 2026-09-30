# Bootstrap — Delta ISC S16 sequential graph

Репозиторий: `https://github.com/chartjs333/delta.git`
Sprint branch: `agent/isc-s16-sequential-sprint`
Sprint file: `orchestration/sprints/isc-s16-sequential/sequential-sprint.json`

## Запуск

1. Архивируйте/замените ошибочно импортированный sprint. Не пытайтесь вручную завершить
   assignment `7fec1504-4c14-4a93-80bc-ea257c951594`.
2. Импортируйте `sequential-sprint.json` через sequential route.
3. Вызовите `GET` или `POST http://localhost:8025/api/v1/agents/whoami`.
4. В выданный `reply_url` один раз отправьте:
   `{"git_address":"https://github.com/chartjs333/delta.git"}`
5. Используйте только выданные `agent`, `profile`, `git_branch`, `active_task`,
   `assignment_id`, `graph_position` и current assignment endpoint.
6. Сразу выполняйте active_task.
7. Outcome отправляйте в current assignment endpoint с exact:
   `assignment_id`, allowed status, `result`, `from_commit`, `git_commit`, `git_branch`.
8. Только после принятого handoff снова вызывайте общий `/api/v1/agents/whoami`.
9. Reviewer использует только `APPROVE` или `REJECT`; REJECT требует actionable feedback.
10. Не выбирайте следующую identity/branch/task вручную.

## Git

Каждая новая assigned branch создаётся от:

```bash
git fetch origin --prune
git switch -c <assigned-branch> origin/agent/isc-s16-sequential-sprint
```

Проверьте наличие `orchestration/sprints/isc-s16-sequential/` и ancestry
`ea5a70d8c5fd3516de243632f2c5681b0e5a6292`.

A01 handoff node не меняет старую A01 branch. Он создаёт только handoff record на своей
assigned branch и передаёт exact A01 commit на reviewer gate.
