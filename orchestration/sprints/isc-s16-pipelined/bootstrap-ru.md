# Bootstrap — Delta ISC Sprint 16

Репозиторий: `https://github.com/chartjs333/delta.git`
Sprint manifest branch: `agent/isc-s16-pipelined-sprint`
Sprint files path: `orchestration/sprints/isc-s16-pipelined/`
Source baseline: `codex/feature000-binding-candidate@ea5a70d8c5fd3516de243632f2c5681b0e5a6292`

## Общие правила

1. Общайся с nginx-qa только через HTTP API. Не читай напрямую runtime/state/queue-файлы nginx-qa.
2. Все сообщения и JSON отправляй в UTF-8.
3. Используй только identity, task и `git_branch`, выданные nginx-qa.
4. Выполни `git fetch origin --prune`.
5. Если assigned branch отсутствует, создай её строго от `origin/agent/isc-s16-pipelined-sprint`.
6. Проверь `git merge-base --is-ancestor ea5a70d8c5fd3516de243632f2c5681b0e5a6292 HEAD`.
7. Проверь наличие `orchestration/sprints/isc-s16-pipelined/README.md`, `lane-tasks.md` и sprint JSON.
8. Прочитай `lane-tasks.md` и выполняй только свой task ID.
9. Sprint-файлы не изменяй и не удаляй.
10. Работай только в assigned scope; при пересечении ownership верни `STOP` с blocker/evidence.
11. Commit + push результата; не merge.
12. В outcome укажи from_commit, git_commit, git_branch, changed files, commands, tests/evidence и manifest-presence check.
13. Join/qualification и production-ветки автоматически не запускай.

Для sequential W1-варианта сначала вызови общий `/api/v1/agents/whoami`, один раз отправь `git_address` в выданный `reply_url`, а официальный результат отправляй в current assignment endpoint с сохранённым `assignment_id`. Reviewer использует только `APPROVE` или `REJECT`.
