# Implementation Plan: Deterministic Domain-Pure Ticket Scheduling

**Branch**: `007-domain-pure-ticket-scheduling` | **Date**: 2026-08-23 | **Spec**: `spec.md`

**Constitution**: 2.1.0

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

**Exact predecessor**: feature-006 merge `827d3393acf347c9b45eabdb3d652bdc98bcfe75`,
verified source `90cc7fac96675694bab15f4e1ae1e5c6e3f525be`, evidence overlay
`b487ea81851cfd5b4769579392798841cb18afc0` and final report SHA-256
`d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800`.

## Summary

Implement authoritative native domain quota/ticket planning, capability-policy validation,
deterministic capacity-aware lease assignment, durable logical timers and pre-commit reassignment.
Java collects authenticated capability evidence and transports bounded native decisions/effects;
Python consumes finalized tickets for worker-local ML only. Replace all adaptive-H/staleness behavior
with fixed work and explicit infeasibility.

## Technical Context

- C++20 deterministic single-writer planner and lease state over canonical policy/profile snapshots.
- Native journal recovery precedes commands; state-changing effects become visible after durability.
- Versioned C ABI with synchronous borrowed-direct and owned-copy parity.
- Java 25 reference and Java 26 compatibility FFM adapter for capability/transport only.
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
| Formal first | Existing lease/deadline/recovery actions only | Preflight + refinement traces |
| Runtime authority | C++ decides; Java transports; Python trains | Boundary/static/C ABI tests |
| Recovery | Persist native lease transition before effects | Crash/restart/replay tests |

**Final result**: EXIT PASS. T000–T033 and HR007-001–HR007-012 are complete; feature 008 remains
closed until it passes its own predecessor, Formal GO and implementation gates.

## Architecture and Data Flow

```text
Java authenticated capability transport
                │ canonical bounded bytes
                ▼
C ABI ──▶ native capability/policy validator
                │
DomainTicketPolicy + DatasetManifest
                │
                ▼
C++ deterministic ticket planner/lease WAL
                │ opaque plan/lease/timer effects
                ▼
Java delivery/timers/telemetry
                │ TimerFired(token), commitment command
                ▼
C++ expiry/reassign/commit ordering
```

## Mandatory preflight

No production source may be added until content-addressed evidence rederives the exact feature-006
merge/source/evidence/report chain, revalidates the inherited Formal GO and existing lease/failure
actions, confirms zero formal source diff and finds no Python/Java scheduling authority, adaptive work,
stale weighting, device-derived math or pre-ISC randomness path. Canonical policy, capability,
eligibility, ticket, plan, lease, timer-token and infeasibility contracts must then be frozen with
cross-language valid/invalid fixtures and stable IDs.

## Project Structure

```text
delta-protocol/
  schemas/007/{domain-ticket-policy,capability-profile,eligibility-decision,
               work-ticket,round-ticket-plan,ticket-lease,lease-timer-token,
               infeasibility-report}-v1.json
  fixtures/007/{valid,invalid,cross-language}/
delta-core-cpp/
  include/delta/scheduling/{contracts,planner,eligibility,leases,recovery}.hpp
  src/scheduling/
  tests/scheduling_*.cpp
  fuzz/scheduling_contract_fuzz.cpp
delta-ffi/
  src/scheduling_abi.cpp
  tests/scheduling_abi_test.cpp
delta-node-java/src/main/java/io/deltareduce/node/scheduling/
  {CapabilityCollector,AdmissionTransport,LeaseTimerRouter,
   SchedulingTelemetry,NativeScheduling}.java
specs/007-domain-pure-ticket-scheduling/
  scripts/ evidence/ tests/
```

## Implementation Sequence

1. Pass the exact feature-006 predecessor, Formal GO and forbidden-authority preflight.
2. Freeze policy/profile/eligibility/ticket/plan/lease/timer/infeasibility canonical contracts.
3. Implement the authoritative C++ ticket/data/quota planner and native eligibility boundary.
4. Implement deterministic feasibility, capacity-neutral mathematics and initial lease allocation.
5. Implement journaled logical expiry/renew/reassign and commit-versus-expiry ordering.
6. Expose bounded C ABI decisions/effects and implement Java transport/admission/timer adapters only.
7. Export legal/illegal native traces, kill production mutants and pass exact formal refinement.
8. Publish compiler/JDK/sanitizer, determinism, timing, recovery and final compatibility evidence.

## Test Strategy

Input-order permutations; exact quota/data coverage; profile expiry/mismatch; capacity infeasibility;
fast/slow ownership versus unchanged ticket/mixture; lease expiry/commit races; stale opaque timers;
restart/replay and region loss; borrowed/copy ABI parity; native trace refinement; architecture searches
for Python/Java authority, adaptive/stale/device-weight and early-randomness paths.

## Observability

Record policy/plan/profile roots, eligibility reasons, ticket counts by domain/region/worker, lease epochs, misses/reassignments, full-ticket durations and infeasibility constraints. Never emit an aggregation weight derived from device metrics.

## Rollout and Rollback

Run planner in deterministic simulation/shadow mode first. Rollback returns future rounds to a static fixed-ticket assignment policy, not legacy adaptive scheduling. Existing ticket/lease bytes remain immutable.

## Exit Gate

All semantic and HR007 obligations pass; 50-worker fixtures are byte-deterministic; domain quotas/B/H
are exact; lease races and restart preserve commitment uniqueness; speed scenarios do not alter
mixture policy; infeasible plans fail explicitly; C++/C ABI/Java matrices agree; implementation traces
refine the accepted formal actions; final Constitution 2.1.0 compatibility evidence passes.
