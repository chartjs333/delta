# Checklist: 007 Scheduling Runtime

**Status**: Reconciled with Constitution 2.1.0; implementation gates remain open.

- [x] C++ owns all plan and lease state transitions.
- [x] Java capability collection cannot change mathematical weights.
- [x] Timers are opaque tokens and stale delivery is harmless.
- [x] Infeasibility cannot adapt fixed work or domain mixture.
- [x] Lease/commit races and recovery are formal trace gates.
- [x] Python has no planning, admission, lease or commitment-ordering authority.
- [ ] Exact feature-006 predecessor and Formal GO preflight evidence passes.
- [ ] Canonical scheduling schemas and cross-language fixtures are frozen before production code.
