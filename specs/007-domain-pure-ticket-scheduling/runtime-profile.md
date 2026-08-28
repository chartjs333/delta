# Runtime Profile: 007 Domain-Pure Ticket Scheduling

**Primary runtime**: C++ deterministic scheduling state  
**Supporting runtime**: Java admission, capability collection and transport telemetry  
**Formal impact**: `REFINEMENT_ONLY`

**Constitution**: 2.1.0

**Exact predecessor**: feature-006 merge
`827d3393acf347c9b45eabdb3d652bdc98bcfe75`, source
`90cc7fac96675694bab15f4e1ae1e5c6e3f525be`, evidence
`b487ea81851cfd5b4769579392798841cb18afc0`.

No production source may be added until the exact predecessor/Formal GO preflight and canonical
scheduling schema gate pass.

## Responsibility split

C++ owns:

- canonical domain ticket plan;
- deterministic IDs/data ranges/order;
- lease epochs, logical expiry, bounded renewal and reassignment;
- commitment-versus-expiry ordering;
- infeasibility and missing-ticket terminal decisions.

Java owns:

- authenticated collection of capability evidence;
- transport compatibility checks and endpoint/region metadata;
- bounded delivery of plan/lease messages;
- operational telemetry.

Java cannot modify ticket bytes, `B/H`, `pi_d`, coefficient fields or mathematical weight based on GPU speed, memory, energy or completion time.

Python owns worker-local training against an already finalized ticket only. It cannot create plans,
admit workers, advance lease epochs or resolve commit-versus-expiry ordering.

## Capability boundary

Capability profiles are canonical evidence inputs. Native scheduling validates them against the fixed policy and emits an eligibility/lease decision. The Java layer cannot turn a self-reported benchmark into accepted mathematical state without a native transition.

## Lease timers

Native state emits opaque lease timer tokens. Java returns `TimerFired(token)`. C++ verifies current round/ticket/lease epoch and treats stale timer delivery as an idempotent no-op. A Java callback cannot reassign a ticket directly.

Every native transition that changes plan/lease state is journaled before its effect is returned.
Restart restores the journal and exact timer/lease state before accepting new commands.

## Failure behavior

Insufficient capacity returns an exact infeasibility report or follows the frozen close/abort policy. It never shrinks `B/H`, silently changes domain quotas, invents zero updates or renormalizes `pi_d`.

## Exit additions

- shuffled capability/profile input produces identical native plan/decision bytes;
- fast/slow scenarios change lease ownership/concurrency only;
- stale timer, commit/expiry race and restart traces are exact and formally valid;
- Java model contains no aggregation weight derived from device metrics;
- 50-worker plan meets the declared bounded planning target without weakening work.
