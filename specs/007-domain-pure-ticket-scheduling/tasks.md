# Tasks: Deterministic Domain-Pure Ticket Scheduling

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, accepted Formal GO and merged feature 006
`827d3393acf347c9b45eabdb3d652bdc98bcfe75`.

The authoritative planner, admission decision, lease/timer state and commitment ordering are native
C++/C ABI. Java owns authenticated capability collection, bounded transport, opaque timer delivery
and telemetry. Python owns worker-local ML only. `task-map.md` is normative.

## Phase 0: Mandatory predecessor/formal STOP

- [ ] T000 [HR007-012] Verify exact feature-006 merge/source/evidence/report ancestry and hashes.
- [ ] T001 [HR007-011] Revalidate Formal GO, ticket/lease/deadline/recovery actions, failure semantics
  and every runtime precondition used by feature 007.
- [ ] T002 [HR007-011] Prove zero formal source diff and classify the planned implementation
  `REFINEMENT_ONLY`; any new action/precondition/outcome is an unconditional STOP.
- [ ] T003 [HR007-007] Prove zero adaptive-H/B, stale/device-derived mathematical weight,
  Python/Java scheduling authority and pre-ISC randomness paths in the authoritative lineage.
- [ ] T004 [HR007-012] Emit content-addressed `evidence/preflight.json` binding T000–T003 and block
  every production-source task until it passes.

## Phase 1: Runtime-neutral canonical contracts

- [ ] T005 [HR007-001] Freeze canonical `DomainTicketPolicy`, dataset allocation constraints and
  immutable `WorkTicket` schemas with exact domain/data/B/H/parent/profile context.
- [ ] T006 [HR007-001] Freeze `CapabilityProfile`, `EligibilityDecision` and stable reason-code
  schemas without coefficient, mixture or robust-weight outputs.
- [ ] T007 [HR007-001] Freeze `RoundTicketPlan`, `TicketLease`, bounded renewal and prior-lease
  lineage schemas.
- [ ] T008 [HR007-001, HR007-005] Freeze opaque native lease-timer token and exact infeasibility
  report schemas with logical deadlines and bounded transition policy.
- [ ] T009 [HR007-001, HR007-007] Register schema/media/domain IDs and add valid, invalid and
  cross-language fixtures for permutations, mismatches and forbidden math fields.
- [ ] T010 [HR007-001, HR007-012] Publish deterministic contract evidence and parser/allocation
  limits; no C++/Java production scheduling source may precede this gate.

## Phase 2: Native exact ticket planner

- [ ] T011 [HR007-002] Implement bounded C++ canonical parsers and immutable context validation.
- [ ] T012 [HR007-002] Implement exact per-domain quota, deterministic data-range ownership,
  overlap rejection and ticket ID/order construction.
- [ ] T013 [HR007-002, HR007-010] Implement exact feasibility validation that returns canonical
  unmet constraints without changing K/B/H, data ranges or `pi_d`.
- [ ] T014 [HR007-007, HR007-008, HR007-010] Add input permutations, invalid policy/data coverage,
  50-worker and production adaptive-work/infeasibility mutants.

## Phase 3: Native capability and initial lease decisions

- [ ] T015 [HR007-003] Validate authenticated capability evidence against exact
  model/schema/mode/fixed-point/memory/expiry policy and emit stable eligibility reasons.
- [ ] T016 [HR007-003, HR007-007] Implement deterministic capacity-aware ownership/concurrency
  without copying throughput, memory, device or timing into `a_j`, `pi_d` or ticket bytes.
- [ ] T017 [HR007-003, HR007-008] Produce byte-identical initial leases across shuffled inputs and
  prove fast/slow scenarios change ownership/concurrency only.
- [ ] T018 [HR007-008, HR007-010] Add expired, manipulated, missing-evidence, region-loss and
  insufficient-capacity matrices.

## Phase 4: Native durable lease lifecycle

- [ ] T019 [HR007-004, HR007-005] Implement native-issued opaque timer tokens, logical expiry and
  stale/duplicate/reordered timer rejection.
- [ ] T020 [HR007-004] Persist renew/expire/reassign transitions before effects and recover exact
  lease/timer state before accepting commands.
- [ ] T021 [HR007-004] Preserve ticket ID/domain/data/B/H/profile across bounded renewal and
  reassignment; increment lease epoch and retain exact lineage.
- [ ] T022 [HR007-004, HR007-009] Order commitment versus expiry/current lease epoch through native
  state so at most one accepted root binds a ticket.
- [ ] T023 [HR007-009, HR007-010] Add crash/restart/replay, old/new holder, after-commit expiry,
  max-epoch, hard-deadline and missing-capacity terminal scenarios.

## Phase 5: C ABI and Java transport/admission only

- [ ] T024 [HR007-006] Add bounded C ABI commands/effects with synchronous borrowed-direct and
  owned-copy parity; native retains no Java-owned pointer.
- [ ] T025 [HR007-005, HR007-006] Implement Java authenticated capability collection, bounded plan/
  lease transport, opaque timer callbacks, backpressure, cancellation and telemetry without decisions.
- [ ] T026 [HR007-006, HR007-007] Add JDK 25/26 FFM conformance and static authority tests proving
  Java cannot alter eligibility, epoch, deadlines, ticket math or commitment ordering.

## Phase 6: Refinement, quality and final evidence

- [ ] T027 [HR007-011] Export implementation-derived legal plan/lease/expire/reassign/commit/restart
  traces and require acceptance by the exact feature-000 refinement checker.
- [ ] T028 [HR007-007, HR007-009, HR007-011] Reject old-holder, post-commit reassignment,
  adaptive-H, device-weight, stale-timer and early-randomness traces; kill production mutants.
- [ ] T029 [HR007-008, HR007-012] Measure deterministic 50-worker planning and speed-independence
  evidence without converting the target into a safety or WAN claim.
- [ ] T030 [HR007-012] Run C++20/C++23, Clang ASan/UBSan, native fuzz, C ABI, JDK 25/26 and full
  Python quality/regression matrices.
- [ ] T031 [HR007-012] Publish exact-source CI, recovery/refinement, boundary and determinism
  evidence with `semantic_completeness_claimed=false`.
- [ ] T032 [HR007-012] Document native fixed-ticket scheduling, Java adapter operations,
  observability, rollback and explicit feature-008 boundary.
- [ ] T033 [HR007-012] Publish final Constitution 2.1.0 compatibility report and close the phase.

## Dependencies

- T000–T004 are sequential and block canonical contract publication and every production source.
- T005–T010 freeze all runtime-neutral bytes/IDs before C++ or Java consumes them.
- T011–T014 block admission and leases.
- T015–T018 block mutable lease state.
- T019–T023 block C ABI/Java effects.
- T024–T026 block refinement and final measurement.
- T027–T033 close the phase without claiming feature-008 certificates, seed or Apply completion.

## Exit Gate

All T000–T033 and HR007-001–HR007-012 obligations pass; shuffled 50-worker inputs produce exact
native plan bytes; fast/slow capacity changes ownership only; K/B/H/data/mixture never adapt; lease,
timer, commitment and recovery races fail closed or replay idempotently; compiler/JDK/runtime
matrices agree; implementation traces refine the accepted formal actions; feature-008 remains closed.
