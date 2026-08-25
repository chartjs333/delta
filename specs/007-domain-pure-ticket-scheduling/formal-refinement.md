# Formal Refinement Obligations: 007 Domain-Pure Ticket Scheduling

This file is normative for `007-domain-pure-ticket-scheduling`.

## Refined state/actions

The implementation projects immutable ticket-plan, `LeaseTicket`, bounded renewal if enabled, `ExpireLease`, `ReassignTicket`, `CommitTicket`, replay and hard-deadline actions.

## Mandatory properties

- Ticket domain/data/`B`/`H`/parent/profile never change after plan finalization.
- Capability/throughput influences admission, concurrency and ownership only; it cannot enter `pi_d`, ticket bytes or certified coefficient fields.
- Reassignment is enabled only after logical/certified lease expiry and absence of accepted commitment.
- Reassignment preserves ticket ID/content and increments lease epoch.
- Only the current lease worker/epoch may commit; BFT ordering plus CommitUniqueness accepts at most one root.
- Missing capacity does not adapt `B/H` or fabricate updates; it yields exact infeasibility, missing-ticket close outcome or abort according to the frozen policy.
- Scheduling does not access `rho_t` before ISC.

## Required evidence

1. Legal plan/lease/expire/reassign/commit traces accepted by the 000 checker.
2. Old/new holder race, reassignment-after-commit, adaptive-H, device-weight and early-randomness traces rejected.
3. 50-worker input permutations produce one abstract plan/lease trace modulo actor assignment allowed by the fixed deterministic policy.
4. Relevant ticket/commit/freeze mutants remain detectable.
5. Formal-impact report binds exact policy and semantics IDs.
