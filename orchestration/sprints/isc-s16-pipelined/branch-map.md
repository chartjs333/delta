# Delta ISC Sprint 16 — branch map

## Каноническая ветка

- Sprint manifest branch: `agent/isc-s16-pipelined-sprint`
- Sprint files path: `orchestration/sprints/isc-s16-pipelined/`
- Source baseline: `codex/feature000-binding-candidate@ea5a70d8c5fd3516de243632f2c5681b0e5a6292`
- Formal state: `NO_GO`
- Production integration: `STOP`

Все рабочие и reviewer-ветки создаются от `origin/agent/isc-s16-pipelined-sprint`. Поэтому все sprint-файлы доступны на каждой ветке и не должны удаляться или изменяться рабочими lane.

## Параллельные lane

| Lane | Ветка | Разрешённый scope |
|---|---|---|
| A | `agent/isc-s16-contract-freeze` | ADR/status/non-circular dependency DAG/checklist |
| B | `agent/isc-s16-w1-reference-engine` | quarantined W1 codec, file harness, replay и fault tests |
| C | `agent/isc-s16-ed25519-reference` | quarantined K/E/R/V/M/G bytes и Ed25519 conformance |
| D | `agent/isc-s16-formal-linkage` | TLA+/Lean integration points, mutants и formal report |

## Join gate

После завершения четырёх lane создаётся отдельный sprint `agent/isc-s16-formal-qualification`. Он получает точные четыре commit SHA, проверяет нормативные bytes/vectors/proofs и не разрешает production merge при `NO_GO`.

## Последующие ветви

1. `agent/isc-s16-formal-qualification`
2. `agent/isc-s16-formal-merge-record`
3. `agent/isc-s16-core-producer`
4. `agent/isc-s16-runtime-w1`
5. `agent/isc-s16-ffi-transport`
6. `agent/isc-s16-integration-evidence`
7. `agent/isc-s16-r2-3-closure`
8. `agent/isc-s16-r3-recovery`
9. `agent/isc-s16-final-closure`

Каждая следующая ветка запускается отдельным sprint после принятого predecessor commit. `STOP` не открывает следующую ветку.
