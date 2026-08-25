# Implementation Plan: Deterministic Domain-Pure Ticket Scheduling

**Branch**: `007-domain-pure-ticket-scheduling` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Implement domain quota/ticket planning, measured worker admission, deterministic capacity-aware lease assignment and pre-commit reassignment. Replace all adaptive-H/staleness behavior with fixed work and explicit infeasibility.

## Technical Context

- Pure deterministic planner over canonical policy/profile snapshots.
- Logical/BFT time for lease expiry; no worker clock authority.
- Capability benchmarks are versioned artifacts tied to exact model/config/profile.
- Assignment algorithm may optimize lease concurrency but cannot alter ticket or weight semantics.
- Feature-003 commitment registry remains the final uniqueness guard.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Fixed work | `K_d/B_d/H_d` immutable in config/tickets | Golden ticket tests |
| Domain mixture | `pi_d` unaffected by capacity/ownership | Scenario comparison |
| BFT state | Plan/lease/reassign are transition commands | Replay/race tests |
| No adaptivity | Schemas and architecture tests forbid adaptive/stale fields | STOP gate |
| Determinism | Canonical profile snapshot and planner | Permutation tests |

**Pre-implementation result**: PASS.

## Architecture and Data Flow

```text
DomainTicketPolicy + DatasetManifest
                │
CapabilitySnapshot ──▶ EligibilityEvaluator
                │
                ▼
DeterministicTicketPlanner ──▶ complete ticket array
                │
                ▼
CapacityAwareLeaseAllocator ──▶ TicketLease epochs
                │
      expire/reassign before commitment only
                ▼
feature-003 CommitmentRegistry
```

## Project Structure

```text
src/deltatorrent/domain/scheduling.py
src/deltatorrent/scheduling/
  capability.py
  eligibility.py
  tickets.py
  feasibility.py
  leases.py
  planner.py
  replay.py
  telemetry.py
src/deltatorrent/cli/schedule.py
configs/scheduling/fixed-ticket-v1.json
tests/contract/test_schedule_bytes.py
tests/unit/test_domain_ticket_plan.py
tests/unit/test_eligibility.py
tests/integration/test_lease_reassignment.py
tests/integration/test_speed_independent_domain_mix.py
tests/architecture/test_no_adaptive_or_stale_scheduling.py
```

## Implementation Sequence

1. Freeze policy/profile/plan/lease/infeasibility canonical schemas.
2. Implement exact domain ticket/data allocation and golden fixtures.
3. Implement profile compatibility/admission and measured benchmark artifact path.
4. Implement deterministic feasibility and capacity-aware lease allocation.
5. Implement logical expiry/reassignment through consensus state.
6. Integrate commitment uniqueness and race handling.
7. Add replay simulator, metrics, CLI and documentation.

## Test Strategy

Input-order permutations; exact quota/data coverage; profile expiry/mismatch; capacity infeasibility; fast/slow ownership versus unchanged ticket/mixture; lease expiry/commit races; region loss; architecture search for adaptive/stale/device-weight fields.

## Observability

Record policy/plan/profile roots, eligibility reasons, ticket counts by domain/region/worker, lease epochs, misses/reassignments, full-ticket durations and infeasibility constraints. Never emit an aggregation weight derived from device metrics.

## Rollout and Rollback

Run planner in deterministic simulation/shadow mode first. Rollback returns future rounds to a static fixed-ticket assignment policy, not legacy adaptive scheduling. Existing ticket/lease bytes remain immutable.

## Exit Gate

50-worker fixtures are byte-deterministic; domain quotas/B/H are exact; lease races preserve commitment uniqueness; speed scenarios do not alter mixture policy; infeasible plans fail explicitly; architecture and Constitution gates pass.
