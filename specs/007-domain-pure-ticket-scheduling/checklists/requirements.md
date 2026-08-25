# Specification Quality Checklist: 007 Domain-Pure Ticket Scheduling

**Reviewed**: 2026-08-23  
**Status**: Ready for implementation

- [x] Legacy adaptive `H_i` and stale weighting are explicitly replaced.
- [x] Every domain fixes `K_d/B_d/H_d`; every ticket is immutable/domain-pure.
- [x] Capability affects eligibility/leases only, never mathematical weights or `pi_d`.
- [x] Infeasibility fails explicitly rather than shrinking fixed work.
- [x] Reassignment is pre-commit only and preserves ticket bytes.
- [x] Commitment races are ordered by BFT state and `CommitUniqueness`.
- [x] Scheduling does not use `rho_t` before ISC.
- [x] 50-worker deterministic, speed-independence and lease-race gates are measurable.
- [x] No unresolved clarification remains; failed fixed-work/domain gate blocks feature 008.
