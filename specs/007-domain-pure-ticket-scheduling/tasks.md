# Tasks: Deterministic Domain-Pure Ticket Scheduling

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `006`.

## Phase 0: Mandatory adaptive-scheduling STOP

- [ ] T000 Remove/block `H_i` adaptation, communication-share formula, staleness acceptance/weights, drift controller and device-speed aggregation weights from the authoritative lineage; record evidence.

## Phase 1: Contracts

- [ ] T001 Define `DomainTicketPolicy`, capability, eligibility, plan, lease and infeasibility models in `src/deltatorrent/domain/scheduling.py`.
- [ ] T002 Define canonical policy/profile/plan/lease serialization and reason codes.
- [ ] T003 Create golden fixtures in `tests/fixtures/contracts/deltareduce_v1/007/`.
- [ ] T004 Add contract tests in `tests/contract/test_schedule_bytes.py`.

## Phase 2: Domain ticket planning

- [ ] T005 Implement exact per-domain ticket/data allocation in `src/deltatorrent/scheduling/tickets.py`.
- [ ] T006 Implement quota/overlap/domain ownership validation.
- [ ] T007 Add deterministic ID/order and exact `K/B/H` tests in `tests/unit/test_domain_ticket_plan.py`.
- [ ] T008 Add infeasible/invalid domain policy tests.

## Phase 3: Capability and eligibility

- [ ] T009 Implement versioned benchmark/profile builder in `src/deltatorrent/scheduling/capability.py`.
- [ ] T010 Implement exact compatibility/expiry/admission evaluator in `src/deltatorrent/scheduling/eligibility.py`.
- [ ] T011 Add model/schema/memory/fixed-point/expiry matrix tests.
- [ ] T012 Add guard proving profile speed fields cannot enter coefficient/mixture models.

## Phase 4: Feasibility and initial leases

- [ ] T013 Implement deterministic capacity/deadline feasibility report in `src/deltatorrent/scheduling/feasibility.py`.
- [ ] T014 Implement capacity-aware but math-neutral lease allocator in `src/deltatorrent/scheduling/planner.py`.
- [ ] T015 Add 50-worker input permutation and performance target tests.
- [ ] T016 Add fast/slow ownership with unchanged ticket/`pi_d` scenario.
- [ ] T017 Add explicit failure tests proving no H/B/quota shrink on infeasibility.

## Phase 5: Lease lifecycle and commitment race

- [ ] T018 Implement consensus/logical lease transitions in `src/deltatorrent/scheduling/leases.py`.
- [ ] T019 Implement bounded renewal (if enabled), expiry and immutable-ticket reassignment.
- [ ] T020 Integrate current lease epoch validation with feature-003 commitment registry.
- [ ] T021 Add expiry/reassign/old-vs-new commit race tests in `tests/integration/test_lease_reassignment.py`.
- [ ] T022 Add restart/replay/idempotency/max-epoch tests.
- [ ] T023 Add region/domain capacity-loss terminal behavior tests.

## Phase 6: Replay and boundaries

- [ ] T024 Implement deterministic scheduling trace replay in `src/deltatorrent/scheduling/replay.py`.
- [ ] T025 Add `tests/integration/test_speed_independent_domain_mix.py`.
- [ ] T026 Add architecture test `tests/architecture/test_no_adaptive_or_stale_scheduling.py`.
- [ ] T027 Verify scheduling uses no `rho_t` or pre-ISC randomness.

## Final Phase

- [ ] T028 Add schedule telemetry and `schedule plan/inspect/replay` CLI.
- [ ] T029 Document fixed-ticket policy in `docs/deltareduce/ticket-scheduling.md`.
- [ ] T030 Publish exit evidence and run cross-artifact analysis.
- [ ] T031 Run full quality gate and final Constitution Check.

## Dependencies

T000 blocks everything. T001–T004 block planner state. T005–T008 block leases. T009–T012 block admission. T013–T017 block open-round decisions. T018–T023 are the uniqueness/liveness gate. T024–T027 are architectural proofs. T028–T031 are final.

## Exit Gate

All tasks pass; 50-worker plans are byte-identical and quota-exact; lease races never duplicate commitments; speed affects ownership only; infeasibility does not mutate work; no adaptive/stale/device-weight path exists.
