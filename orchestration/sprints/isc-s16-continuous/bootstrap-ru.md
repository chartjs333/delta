# Bootstrap — Delta ISC S16 continuous sequential graph

Репозиторий: `https://github.com/chartjs333/delta.git`
Sprint branch: `agent/isc-s16-continuous-sprint`
Sprint file: `orchestration/sprints/isc-s16-continuous/sequential-sprint.json`

## Запуск

1. Импортируйте новый `sequential-sprint.json` через sequential route.
2. Вызовите `GET` или `POST http://localhost:8025/api/v1/agents/whoami`.
3. В выданный `reply_url` один раз отправьте:
   `{"git_address":"https://github.com/chartjs333/delta.git"}`
4. Используйте только выданные `agent`, `profile`, `git_branch`, `active_task`,
   `assignment_id`, `graph_position` и current assignment endpoint.
5. Сразу выполняйте active_task.
6. Outcome отправляйте в current assignment endpoint с exact:
   `assignment_id`, allowed status, `result`, `from_commit`, `git_commit`, `git_branch`.
7. Только после принятого handoff снова вызывайте общий `/api/v1/agents/whoami`.
8. Reviewer использует только `APPROVE` или `REJECT`; это process gate, не
   независимая Formal GO attestation.
9. Не выбирайте следующую identity/branch/task вручную.

## Git

Если assigned branch отсутствует:

```bash
git fetch origin --prune
git switch -c <assigned-branch> origin/agent/isc-s16-continuous-sprint
```

Если branch уже существует после возврата от Continuity Coordinator:

```bash
git fetch origin --prune
git switch <assigned-branch>
git status --short
git log --oneline --decorate -n 10
```

Затем включите только новые sprint/coordinator decisions из
`origin/agent/isc-s16-continuous-sprint`. При неожиданном code/formal diff верните
`NEED_DECISION`, а не выполняйте слепое merge.

Всегда проверяйте наличие:

- `orchestration/sprints/isc-s16-continuous/README.md`
- `continuity-agent.md`
- `lane-tasks.md`
- `sequential-sprint.json`
- `SHA256SUMS.json`

## Непрерывность

Обычные вопросы решайте в пределах task по `continuity-agent.md`.
Если требуется изменение frozen authority, верните `NEED_DECISION` или `STOP`.
Graph передаст работу Coordinator node; промежуточного blocked terminal нет.
