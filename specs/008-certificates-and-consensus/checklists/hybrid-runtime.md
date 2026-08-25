# Checklist: 008 Certificate Runtime

- [x] The entire certificate and Apply graph is native and matches formal semantics.
- [x] Every QC vote uses one durable persist-before-send lifecycle.
- [x] Java owns TLS/delivery/timers/artifact I/O only.
- [x] Randomness cannot exist before native ISC verification.
- [x] Aggregate coverage derives from the immutable required matrix.
- [x] Current state changes only through native ApplyQC CAS/replay.
- [x] Java/C++ crash and delivery traces are mandatory refinement evidence.
