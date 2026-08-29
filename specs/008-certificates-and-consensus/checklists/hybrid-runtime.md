# Checklist: 008 Certificate Runtime

**Status**: Native implementation and local conformance pass; exact-source CI evidence pending.

- [x] The entire certificate and Apply graph is native and matches formal semantics.
- [x] Every QC vote uses one durable persist-before-send lifecycle.
- [x] Java owns TLS/delivery/timers/artifact I/O only.
- [x] Randomness cannot exist before native ISC verification.
- [x] Aggregate coverage derives from the immutable required matrix.
- [x] Current state changes only through native ApplyQC CAS/replay.
- [x] Java/C++ crash and delivery traces are accepted as refinement evidence.
- [x] Exact feature-007 predecessor and Formal GO preflight evidence passes.
- [x] Canonical certificate/apply schemas and fixtures are frozen before production code.
