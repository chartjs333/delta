# Delta ISC S16 — continuous sequential pipeline

Этот sprint предназначен для nginx-qa, где подтверждён declared **sequential graph**.
Он продолжает работу после A01 и не использует parallel assignment.

## Canonical branch

- branch: `agent/isc-s16-continuous-sprint`
- source commit: `85a2a526468293e90daf019c0e10781e3d753a8c`
- completed A01: `agent/isc-s16-contract-freeze@a579a5c66586ba3f8f1d7cc26c454aba5addbd8f`
- historical A01 handoff: `agent/isc-s16-a01-handoff@85a2a526468293e90daf019c0e10781e3d753a8c`
- source baseline: `ea5a70d8c5fd3516de243632f2c5681b0e5a6292`
- sprint path: `orchestration/sprints/isc-s16-continuous/`

Все новые worker/reviewer branches создаются от
`origin/agent/isc-s16-continuous-sprint`. Поэтому sprint JSON, coordinator profile, task spec,
branch map, recovery state и checksum manifest доступны на каждой ветке.

## Главное изменение

В graph добавлен постоянный `Delta ISC Continuity Coordinator`. Обычные вопросы
решаются исполнителем на месте по coordinator protocol. `STOP`, `NEED_DECISION` и
formal `NO_GO` не ведут в terminal blocked: они переводят identity к Coordinator,
который фиксирует решение/remediation и возвращает работу в нужный node.

Единственный явный terminal — `completed`, достигаемый после ограниченного
formal-qualification `GO`. Системный `max_rework_cycles=100` остаётся аварийным
предохранителем nginx-qa, а не обычным выходом.

## Последовательность

```text
Continuity recovery/coordinator
→ W1 reference
→ crypto reference
→ formal linkage
→ formal qualification
→ completed

Любой вопрос/STOP/NO_GO
→ Continuity Coordinator
→ нужный предыдущий/следующий node
```

Каждый transition проходит два process-review gate. Поскольку sequential executor
может последовательно принимать reviewer identities, эти gate не выдаются за
независимые внешние аттестации Formal GO.

## Импорт

Используйте только:

`orchestration/sprints/isc-s16-continuous/sequential-sprint.json`

через sequential import/pending-sprint flow. Старые parallel и blocked sequential
sprints повторно не импортировать.

## User-authorized D01 recovery-proof exception

The narrow authorization is recorded in
[`ISC-S16-D01-RECOVERY-PROOF-ONLY.json`](scope-amendments/ISC-S16-D01-RECOVERY-PROOF-ONLY.json).
Only the existing `DeltaReduce.nativeArithmeticRecoveryRefines`, its axiom audit
and necessary lemmas are excepted from the R3 restriction. Existing task IDs,
graph edges and two process reviews are preserved.

Proof work requires both the committed amendment and a supported live nginx-qa
profile/task update preserving the current assignment/history/reviews. Do not
apply this updated sprint file through overwrite/reimport. If no safe supported
update exists, retain the assignment and report that limitation.

The first D01 phase is a prerequisite checkpoint within two active investigation
hours, not a theorem deadline. It returns `NEED_DECISION` through the two existing
process reviews to Coordinator. Only a positively sufficient, within-scope report
with two approvals for its exact commit permits `RESUME_FORMAL` for extended proof
work. An approved blocked report or amendment approvals cannot satisfy this gate.
The theorem's closure does not close original D01 integration, Q01, remaining R3
or Formal GO. Historical outcomes and evidence remain unchanged.
