# Feature 007 scheduling operations

Feature 007 runs fixed, domain-pure ticket scheduling as an embedded native C++ authority. The Java
node is an authenticated ingress and bounded opaque transport adapter. Python starts only after it
receives an already-finalized work ticket and has no planning, lease or commitment-ordering API.

## Startup and admission

1. Verify that the runtime descriptor, scheduling schemas and formal semantics ID equal the frozen
   feature-007 values before accepting traffic.
2. Recover `scheduling.wal` completely. A checksum, sequence or canonical-state error is a startup
   failure; do not skip a frame or create a replacement lease.
3. Load the immutable round config, parameter schema, parent checkpoint, arithmetic profile, domain
   policies and ticket plan.
4. Admit a capability profile only through `delta_scheduling_capability_evaluate_borrowed` for a
   synchronous direct buffer or `delta_scheduling_capability_evaluate_copy` otherwise. Both paths
   must produce the same canonical decision bytes.
5. Enqueue native plan, lease and timer-token bytes in `AdmissionTransport`/`LeaseTimerRouter`
   without decoding or repairing them in Java.

The native planner fixes domain, data range, `B`, `H`, parent, schema and arithmetic profile before
lease allocation. Capability throughput may change eligible concurrency and ownership only. It
cannot change ticket bytes, domain mixture, coefficients or deadlines.

## Runtime signals

Operators should record content IDs rather than payloads wherever possible:

- round config, policy, capability snapshot and plan IDs;
- eligibility reason counts by region and worker identity epoch;
- fixed ticket counts by domain and region;
- active, renewed, expired, reassigned and committed lease counts;
- lease epoch, logical expiry tick and WAL sequence lag;
- stale, duplicate, early and committed timer no-op counts;
- queue depth, backpressure rejection, cancellation and native callback counts;
- explicit infeasibility constraints without a derived weight or reduced work budget.

Logical/BFT time is authoritative. Worker wall clocks and heartbeats are observability inputs only.
Never infer a renewal, expiry or reassignment from Java timer delivery order.

## Failure and recovery

Every renew, expire, reassign and commit transition is appended and synced before its effect is
visible. After a crash, restart the native state machine against the same plan and WAL; replaying an
exact command is idempotent. A stale/duplicate/reordered timer is forwarded as opaque bytes and the
native state returns a no-op. An old holder, wrong epoch, conflicting commitment, post-commit
reassignment, maximum-epoch breach, hard-deadline breach or corrupt journal fails closed.

Backpressure is not permission to mutate the plan. Pause or reject new transport input, retain the
native durable state and resume from canonical IDs when capacity returns. If fixed eligible
capacity remains insufficient, publish the canonical infeasibility result or follow the frozen
abort policy.

## Rollback

Rollback affects future rounds only:

1. Stop new capability admission and drain or cancel Java transport queues.
2. Preserve the native WAL, plan, leases, timer tokens and accepted commitments for audit/replay.
3. Let the current round finish under its frozen policy or reach its declared hard-abort outcome.
4. Configure a static fixed-ticket assignment policy for the next round.

Do not restore legacy adaptive `H`, stale-update weighting, device-speed weighting, arrival-order
fallback or mutable ticket budgets. Existing content-addressed ticket and lease artifacts are never
rewritten during rollback.

## Feature-008 boundary

Feature 007 does not create the input-set certificate, seed `rho_t`, eligibility/aggregation
certificates, parameter/root QCs, ApplyQC or current-checkpoint transition. No scheduling path may
read `rho_t` before ISC. The phase ends with fixed tickets, eligibility decisions, durable leases,
commitment intake and refinement evidence; certificate and Apply completion remain closed until
feature 008 passes its own formal and implementation gates.
