# Delta ISC Sprint 16 — pipelined verification

Все sprint-файлы хранятся в Git и доступны на канонической ветке:

- branch: `agent/isc-s16-pipelined-sprint`
- path: `orchestration/sprints/isc-s16-pipelined/`
- source baseline: `codex/feature000-binding-candidate@ea5a70d8c5fd3516de243632f2c5681b0e5a6292`

Каждая рабочая и reviewer-ветка создаётся от `origin/agent/isc-s16-pipelined-sprint`. Поэтому sprint JSON, bootstrap, карта ветвей, task-spec и SHA manifest присутствуют в ancestry и доступны прямо на ветке агента.

## Импорт

- `parallel-sprint.json` — четыре параллельные lane: contract, W1, crypto, formal.
- `w1-one-branch-sequential-sprint.json` — только W1 с двумя reviewer gate.

Не импортируйте оба варианта одновременно: они используют одну W1-ветку.

## Обязательные правила

1. Assigned branch создаётся от `origin/agent/isc-s16-pipelined-sprint`.
2. `git merge-base --is-ancestor ea5a70d8c5fd3516de243632f2c5681b0e5a6292 HEAD` должен завершиться успешно.
3. Каталог `orchestration/sprints/isc-s16-pipelined/` нельзя удалять или менять рабочим lane.
4. Reference code не является production implementation и не снимает formal-first STOP.
5. Join/qualification запускается отдельным sprint после exact commit SHA всех lane.
