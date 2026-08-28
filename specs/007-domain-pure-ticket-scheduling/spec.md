# Feature Specification: Deterministic Domain-Pure Ticket Scheduling

**Feature Branch**: `007-domain-pure-ticket-scheduling`  
**Created**: 2026-08-23  
**Status**: Restacked — production implementation blocked by T000–T010
**Depends on**: `006-regional-hierarchical-reduce`

**Exact predecessor**: feature-006 merge
`827d3393acf347c9b45eabdb3d652bdc98bcfe75`, verified source
`90cc7fac96675694bab15f4e1ae1e5c6e3f525be`, evidence overlay
`b487ea81851cfd5b4769579392798841cb18afc0` and final report SHA-256
`d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800`.

**Formal impact**: `REFINEMENT_ONLY` against
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

## Summary

This feature replaces legacy adaptive heterogeneous scheduling. DeltaReduce v1 handles worker heterogeneity without changing local optimizer steps or contribution weights.

`RoundConfig` fixes, for every domain `d`, the ticket count `K_d`, batch/token budget `B_d`, local optimizer steps `H_d`, data-allocation policy and later domain-mixture coefficient `pi_d`. Every emitted ticket is immutable and domain-pure. Worker capability may determine eligibility, concurrency and how many complete tickets a worker can lease before the round closes, but it cannot change a ticket's `B/H/domain/data`, cannot create device-speed weights and cannot alter `pi_d`.

A ticket may be reassigned only before a commitment exists and only under a predeclared deterministic lease-expiry rule. After `C_j` is accepted, worker/ticket binding is immutable for that round.

The authoritative planner, eligibility decision, lease epoch, timer-token validation,
commit-versus-expiry ordering and recovery state live in the native C++ runtime. Java collects and
transports authenticated capability evidence and opaque effects only. Python remains a worker-local
ML runtime and is not a scheduling authority.

## User Scenarios & Testing

### US1 — Build one deterministic fixed-ticket plan (Priority: P1)

The scheduler receives a committed worker eligibility snapshot and domain quota table and creates the exact ticket array and initial leases.

**Independent Test**: shuffled worker/profile input order and repeated execution produce byte-identical plan/ticket/lease hashes while preserving every configured domain quota.

**Acceptance Scenarios**:

1. **Given** domain table `{K_d,B_d,H_d,pi_d}`, **When** planning runs, **Then** exactly `K_d` tickets are created for each domain and every ticket contains the unchanged `B_d/H_d`.
2. **Given** fast and slow eligible workers, **When** leases are assigned, **Then** capacity may affect the number/concurrency of leases, but ticket bytes and domain quotas remain unchanged.
3. **Given** identical canonical inputs, **When** planning runs on independent validators, **Then** one plan root and identical assignment decisions result.
4. **Given** insufficient eligible capacity to meet the declared issue/deadline policy, **When** validation runs, **Then** the round does not open and returns a deterministic infeasibility report; it does not shrink `H`, `B` or quotas.

### US2 — Admit workers without allowing self-reported influence on mathematics (Priority: P1)

Workers provide measured hardware/software/network evidence used for compatibility and capacity planning.

**Independent Test**: compatible, expired, mismatched and manipulated profiles yield deterministic eligibility decisions; no profile field is copied into aggregation weight or domain mixture.

**Acceptance Scenarios**:

1. **Given** a profile tied to exact model/schema/mode/profile versions, **When** compatibility passes, **Then** the worker is eligible for the matching ticket class.
2. **Given** expired, wrong-model, insufficient-memory or unsupported fixed-point profile evidence, **When** admission runs, **Then** the worker is excluded with a stable reason.
3. **Given** a worker reporting higher speed, **When** plan math is inspected, **Then** only lease capacity/concurrency may differ; `a_j`, `pi_d`, `B_d` and `H_d` remain config/certificate-derived.
4. **Given** missing measurements, **When** conservative fallback is disallowed, **Then** the worker is not assigned work.

### US3 — Reassign an uncommitted lease deterministically (Priority: P1)

A worker disconnects before publishing `C_j`. After a fixed lease deadline, the same immutable ticket may be leased to the next eligible worker.

**Independent Test**: lease-expiry/retry/race simulation proves that at most one worker commitment can bind the ticket and that reassignment never changes domain/data/B/H.

**Acceptance Scenarios**:

1. **Given** an expired lease with no accepted commitment, **When** reassignment executes, **Then** the same `ticket_id` and ticket bytes are assigned under a new lease epoch.
2. **Given** an accepted commitment, **When** a late lease-expiry command arrives, **Then** reassignment is rejected and binding remains immutable.
3. **Given** old and new workers race to commit, **When** the BFT commitment registry orders commands, **Then** only the first valid commitment for the current lease epoch can bind; all conflicts are evidence.
4. **Given** no replacement capacity by the hard planning deadline, **When** policy resolves, **Then** the ticket remains missing and the round follows its predeclared freeze/abort rule; no synthetic contribution is created.

### US4 — Preserve domain mixture independently of device speed (Priority: P1)

Researchers verify that schedule outcomes do not change the configured domain-level model objective.

**Independent Test**: two capacity scenarios assign tickets to different workers but create the same domain ticket set and later `pi_d` table; feature-008 apply input is identical at the domain-policy level.

**Acceptance Scenarios**:

1. **Given** the same `RoundConfig` and different compatible worker speeds, **When** plans are compared, **Then** ticket ownership may differ but domain ticket IDs/data/B/H and `pi_d` are identical.
2. **Given** a domain has fewer completed tickets than another, **When** aggregation/apply policy is constructed, **Then** scheduling does not silently renormalize `pi_d`; the round uses its explicit missing-domain/quorum rule.
3. **Given** a proposal to weight a ticket by throughput, wall-clock time or GPU class, **When** validated, **Then** it is rejected as `DEVICE_SPEED_WEIGHT_FORBIDDEN`.

## Edge Cases

- Zero domain quota, zero/negative `B/H` or `pi_d` table with invalid normalization policy.
- Overlapping data ranges across tickets when overlap is forbidden.
- Same data range assigned under two domains.
- Worker supports model mode but not required quantization/accumulator profile.
- Capability profile measured against another sequence length/batch setting.
- Worker capacity is less than one full ticket before deadline.
- Lease expiration races with commitment submission.
- Two validators observe progress heartbeats in different order.
- Reassignment chain reaches configured maximum epochs.
- Worker is revoked between lease and commitment.
- Region loses all eligible workers for one domain.
- Domain quota cannot be completed but other domains can.

## Requirements

### Functional Requirements

- **FR-001**: `DomainTicketPolicy` MUST bind `domain_id`, `K_d`, fixed `B_d`, fixed `H_d`, data-allocation policy, optimizer/profile compatibility and `pi_d` reference.
- **FR-002**: `RoundTicketPlan` MUST contain the complete canonical ticket array, worker eligibility snapshot hash, assignment policy/version, region constraints, lease policy and plan root.
- **FR-003**: Ticket generation MUST create exactly `K_d` immutable tickets per domain with deterministic IDs/data ranges and no per-worker variation of `B/H`.
- **FR-004**: Adaptive `H_i`, adaptive `B_i`, staleness policies and device-speed contribution weights MUST be rejected by schema and architecture tests.
- **FR-005**: `CapabilityProfile` MUST bind worker identity, hardware/software/model-mode/schema/fixed-point profile, memory, measured complete-ticket throughput, network/reliability evidence, sample size and expiry.
- **FR-006**: Admission MUST use verified/benchmark evidence rather than trusting arbitrary self-reported capacity.
- **FR-007**: Capability data MAY influence eligibility, maximum concurrent leases, region route and number of tickets leased, but MUST NOT modify ticket bytes, coefficient `a_j`, domain mixture `pi_d` or later clipping weights.
- **FR-008**: Identical canonical policy/profile inputs MUST produce byte-identical eligibility decisions, ticket plan and initial leases.
- **FR-009**: Planner MUST validate total/per-domain feasibility against eligible capacity and deadlines; infeasible policy MUST fail explicitly rather than mutate fixed work.
- **FR-010**: Data allocation MUST be deterministic and enforce overlap/domain ownership rules declared by the dataset manifest.
- **FR-011**: `TicketLease` MUST bind ticket, worker, lease epoch, issue/expiry logical times, region route and prior lease lineage.
- **FR-012**: Lease expiry MUST use BFT/logical time or certified transition height, not worker wall-clock claims.
- **FR-013**: Reassignment is allowed only when no commitment is accepted for the ticket and the current lease expiry transition is finalized.
- **FR-014**: Reassignment MUST preserve exact ticket ID/domain/data/B/H/profile and increment the lease epoch.
- **FR-015**: Commitment intake MUST validate current lease worker/epoch and then make the ticket binding immutable under `CommitUniqueness`.
- **FR-016**: Exact lease/commit retries MUST be idempotent; conflicting lease epochs or workers MUST fail closed.
- **FR-017**: Progress/heartbeat messages MAY inform observability but MUST NOT extend hard deadlines or change ticket mathematics unless a deterministic predeclared transition explicitly permits a bounded lease renewal.
- **FR-018**: Lease renewal, if enabled, MUST preserve ticket/worker binding, have a fixed maximum count and be decided by canonical state rather than reported speed.
- **FR-019**: Domain quotas and `pi_d` MUST be independent of worker/device speed and remain immutable after `RoundConfigQC`.
- **FR-020**: Missing tickets/domains MUST be handled only by explicit round freeze/quorum/abort policy; the scheduler MUST NOT fabricate zero updates or silently renormalize `pi_d`.
- **FR-021**: Scheduler decisions MUST record input hashes, deterministic reason codes and exact policy version for replay.
- **FR-022**: Simulation API MUST replay worker eligibility, lease, disconnect and region-failure traces with deterministic logical time.
- **FR-023**: Metrics MUST include eligible/excluded workers, tickets by domain/worker/region, lease epochs, completion/miss rates, planned/actual full-ticket time and infeasibility reasons.
- **FR-024**: Planning/service APIs MUST be transport-independent and operate through the BFT transition command path.
- **FR-025**: Canonical plan, eligibility, lease, expiry, renewal, reassignment, infeasibility and
  commitment-ordering decisions MUST execute in the native C++ single-writer state and recover from
  its durable journal before new commands are accepted.
- **FR-026**: Java MUST treat capability, plan, lease and timer payloads as bounded canonical bytes;
  it MUST NOT decide eligibility, lease epoch, expiry validity, reassignment or commitment acceptance.
- **FR-027**: Lease timers MUST be native-issued opaque tokens bound to round, ticket, lease epoch and
  logical deadline; stale, duplicate and reordered timer delivery MUST be an idempotent no-op.
- **FR-028**: Borrowed-direct and owned-copy C ABI paths MUST produce identical decisions, return
  bounded effects and retain no Java-owned pointer after a call.
- **FR-029**: Native scheduling executions MUST export implementation-derived traces for the accepted
  formal action vocabulary; any newly required action, failure terminal or deadline fallback is a
  semantic STOP requiring a new Formal GO.

### Non-Functional Requirements

- **NFR-001**: Planning 50 workers and representative domain/shard topology SHOULD complete in under 5 seconds on CI-class CPU; this is measured evidence, not a safety requirement.
- **NFR-002**: Same inputs always produce byte-identical decisions.
- **NFR-003**: No round/ticket lease remains non-terminal beyond configured hard transition/deadline plus bounded cleanup.
- **NFR-004**: Safety wins over utilization; planner must declare infeasibility rather than adapt fixed work.
- **NFR-005**: Capacity-based assignment must be auditable and cannot leak into certified mathematical weights.

### Key Entities

- **DomainTicketPolicy**: immutable domain quota, fixed work and mixture reference.
- **CapabilityProfile / EligibilityDecision**: measured compatibility/capacity and deterministic admission result.
- **RoundTicketPlan**: complete ticket array and assignment policy root.
- **TicketLease / LeaseEpoch**: temporary pre-commit worker ownership.
- **InfeasibilityReport**: exact unmet constraints without policy mutation.
- **SchedulingTrace**: replayable logical-time events and decisions.

Native C++ owns the canonical state of every entity above. Java may retain operational transport
metadata, while Python may consume an already finalized ticket; neither runtime may author or repair
the certified scheduling state.

## Success Criteria

- **SC-001**: 50-worker heterogeneous fixtures produce deterministic plans and exact per-domain ticket quotas.
- **SC-002**: Every ticket retains configured domain/data/B/H through lease and reassignment.
- **SC-003**: Expired/mismatched/incompatible profiles are excluded with stable reasons.
- **SC-004**: Lease races produce at most one accepted commitment and never duplicate data contribution.
- **SC-005**: Different speed scenarios change ownership/concurrency only, not domain ticket set or `pi_d`.
- **SC-006**: Infeasible capacity causes explicit failure without shrinking H/B/quotas.
- **SC-007**: Architecture tests reject adaptive/stale/device-weight code and schemas.
- **SC-008**: C++20/C++23, sanitizer, C ABI and JDK 25/26 matrices accept byte-identical scheduling
  decisions and opaque effects.
- **SC-009**: Legal lease/recovery traces refine the accepted formal vocabulary and illegal
  adaptive-H, device-weight, stale-timer and old-holder traces are rejected.

## Assumptions

- Worker identities and benchmark evidence are permissioned.
- `rho_t` from feature 008 is not used for scheduling; it remains unavailable until ISC finalization.
- Capacity estimates are advisory for feasibility/leases, not proofs of honest compute.
- Region membership is fixed for one round topology.

## Out of Scope

- Adaptive local steps or batch/token budgets.
- Stale/asynchronous update acceptance.
- Throughput-, energy- or reputation-based mathematical weights.
- Learned/RL scheduling and cloud procurement.
- Permissionless job market/economics.
- Python or Java scheduling/state-machine authority.
- New certificate types, ApplyQC/current-pointer behavior or post-ISC randomness semantics reserved
  for feature 008.
