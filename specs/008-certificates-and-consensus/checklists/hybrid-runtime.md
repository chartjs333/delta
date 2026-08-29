# Checklist: 008 Certificate Runtime

**Status**: SpecKit reconciled; production exit evidence pending.

- [ ] The entire certificate and Apply graph is native and matches formal semantics.
- [ ] Every QC vote uses one durable persist-before-send lifecycle.
- [ ] Java owns TLS/delivery/timers/artifact I/O only.
- [ ] Randomness cannot exist before native ISC verification.
- [ ] Aggregate coverage derives from the immutable required matrix.
- [ ] Current state changes only through native ApplyQC CAS/replay.
- [ ] Java/C++ crash and delivery traces are accepted as refinement evidence.
- [x] Exact feature-007 predecessor and Formal GO preflight evidence passes.
- [ ] Canonical certificate/apply schemas and fixtures are frozen before production code.
