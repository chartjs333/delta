# Delta ISC Sprint 16 — sequential recovery pipeline

Этот manifest предназначен для текущего nginx-qa, где проверен только declared
**sequential graph**. Parallel import для этого запуска не используется.

## Canonical branch

- branch: `agent/isc-s16-sequential-sprint`
- source ancestry includes completed A01 commit: `a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`
- source baseline: `ea5a70d8c5fd3516de243632f2c5681b0e5a6292`
- path: `orchestration/sprints/isc-s16-sequential/`

Все следующие implementation/reviewer branches должны создаваться от
`origin/agent/isc-s16-sequential-sprint`. Поэтому sprint JSON, bootstrap, task spec, branch map и
checksum manifest доступны на каждой новой ветке.

## Почему это новый sprint

Предыдущий импорт создал `sequential/queue_graph` без declared workflow/transitions.
Assignment `7fec1504-4c14-4a93-80bc-ea257c951594` остаётся orchestration blocker и не
продвигается ручным handoff.

A01 не повторяется. Первый node создаёт source-bound handoff record для уже готового:

- branch: `agent/isc-s16-contract-freeze`
- from: `4873b3559b390318c0fc8ff80dd00ecea4ea7b59`
- commit: `a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`

Затем два постоянных reviewer gate проверяют переход. После их APPROVE один executor
последовательно меняет identity:

```text
A01 handoff
→ reviewer 1
→ reviewer 2
→ W1 reference
→ reviewer 1
→ reviewer 2
→ crypto reference
→ reviewer 1
→ reviewer 2
→ formal linkage
→ reviewer 1
→ reviewer 2
→ formal qualification
→ reviewer 1
→ reviewer 2
→ terminal
```

## Импорт

Используйте только:

`orchestration/sprints/isc-s16-sequential/sequential-sprint.json`

Импорт должен идти через sequential endpoint/pending-sprint flow либо direct project
import, который сохраняет top-level `execution` + `nodes`.

Не импортируйте historical `parallel-sprint.json` для этого запуска.

## Граница

Reference lanes не являются production integration. Producer Integration, R2.3, R3,
sigma assignment и native guard removal остаются запрещены.
