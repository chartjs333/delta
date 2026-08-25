# Checklist: 003 Native BFT Runtime

- [x] Pure core and durability runtime are separate components.
- [x] Reference WAL ownership is native and persist-before-expose is explicit.
- [x] Java calls a small C ABI through FFM and cannot reconstruct consensus semantics.
- [x] Single writer, pointer lifetime and exception boundary are explicit.
- [x] Canonical bytes never depend on C++ memory layout.
- [x] GCC/Clang, sanitizers, fuzzing and Java compatibility are exit gates.
- [x] Crash injection covers durability and effect-return boundaries.
- [x] Every protocol-visible execution must refine the accepted formal semantics.
