# Implementation Plan: Адаптивное планирование неоднородных workers

**Branch**: `007-adaptive-heterogeneous-scheduling` | **Date**: 2026-08-21 | **Spec**: `spec.md`

## Summary

Создать measurement→planning→feedback pipeline. Standard probes публикуют content-addressed capability profiles. Pure deterministic planner выбирает topology, budgets, `H_i` и deadlines, сохраняя explanation graph. После раунда controller обновляет effective caps по committed telemetry. Strict sync остаётся baseline; async intake реализуется отдельным guard layer и флагом.

## Technical Context

- Planner: pure Python domain/application code, deterministic sorting/decimal handling where needed.
- Measurement: worker microbenchmark + network probes через existing netem/transport ports.
- Persistence: profile/evidence/decision manifests в artifact store; controller CAS state.
- Simulation: discrete-event injected clock, trace fixtures, no wall-clock sleeps.
- Drift metrics: streamed summaries; exact full tensors не обязаны храниться вне existing artifacts.
- Async math: FP32 norms/cosine, versioned policy; separate reducer path.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Fixed-H sync control, replayable decisions, explicit experimental async | A/B regression tests |
| Plane separation | Scheduler меняет assignments, не distribution semantics | Architecture test |
| Versioned state | Profiles/policies/evidence/schedules hashed | Replay test |
| WAN realism | Measured/trace network inputs и formula | Simulator tests |
| Bounded heterogeneity | caps, hard deadlines, staleness bound, kill switch | Fault/guard suite |
| Observable/reversible | explanation codes, policy state, fixed fallback | Rollback gate |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
Worker probe + network probe ─▶ CapabilityProfile repository
                                      │
Prior controller state + policy ─────┤
                                      ▼
                              Deterministic Planner
                         schedule/topology/assignments
                                      │
                             execute strict round
                                      │
actual telemetry + drift summaries ─▶ Feedback Controller
                                      │
                             next effective caps

Optional stale update ─▶ AsyncGuard(lineage/norm/τ) ─▶ weighted experimental set
```

## Project Structure

```text
src/deltatorrent/
  domain/scheduling.py
  scheduling/
    profiles.py
    probes.py
    planner.py
    workload.py
    regions.py
    deadlines.py
    explanations.py
    controller.py
    drift.py
    staleness.py
    repository.py
    simulator.py
  coordinator/async_intake.py
  cli/schedule.py
proto/deltatorrent/scheduling/v1/scheduling.proto
tests/
  unit/test_h_formula.py
  unit/test_workload_planner.py
  unit/test_drift_controller.py
  unit/test_staleness_policy.py
  contract/test_scheduling_contract.py
  integration/test_heterogeneous_schedule.py
  integration/test_straggler_deadlines.py
  integration/test_async_guard.py
configs/scheduling/
docs/adaptive-scheduling.md
```

## Implementation Sequence

1. Зафиксировать profile/policy/schedule/evidence/staleness schemas и reason codes.
2. Реализовать standard compute/memory/network probes и compatibility keys.
3. Реализовать pure planner: feasibility, regions, workload, `H`, deadlines, fairness.
4. Реализовать deterministic simulator и planned-vs-actual reports.
5. Реализовать drift evidence/controller с hysteresis и rollback.
6. Интегрировать schedule generation с topology/coordinator.
7. Реализовать isolated async guard/reducer mode и kill switches.
8. Прогнать replay, straggler, drift и sync-regression gates.

## Test Strategy

- **Formula/property**: `H` boundaries, invalid inputs, monotonic response to network/step changes.
- **Planning**: capacity imbalance, contribution caps, fairness aging, memory incompatibility, infeasible quorum.
- **Replay**: schedule/controller byte identity from committed snapshots.
- **Simulation**: 50 workers, network/churn traces, hard-deadline terminal property.
- **Controller**: threshold/hysteresis/recovery/quarantine.
- **Async**: lineage/staleness/cosine edge cases and exact formula; flag-off regression.
- **Integration**: generated topology executes existing hierarchical round.

## Observability

Profile age/source/sample confidence; plan estimates/reasons; actual-vs-planned compute/communication/tokens/deadlines; drift signals/actions; async accepted/rejected weights and kill-state. No raw benchmark secrets or user data.

## Rollout and Rollback

Rollout stages: report-only planner → fixed policy with generated assignments → adaptive `H` for selected rounds → async only in experiment config. Every round can pin fixed schedule. Rollback disables controller/async and reuses static topology/fixed-H behavior.

## Risks and Mitigations

- **Bad estimates**: expiry, confidence, conservative fallback, actual feedback.
- **Oscillation**: windows/hysteresis/rate-limited cap changes.
- **Fast-node dominance**: contribution cap/fairness and token-weighted audit.
- **Async harms quality**: off by default, strict guards, automatic disable, benchmark gate.
- **Planner complexity**: pure deterministic heuristic before advanced optimization.

## Exit Gate

Deterministic profile/planner/replay, formula, infeasibility, drift/hysteresis, straggler terminality and async guard suites pass; fixed synchronous results unchanged; 50-worker planning evidence recorded; full quality/Constitution gates complete.
