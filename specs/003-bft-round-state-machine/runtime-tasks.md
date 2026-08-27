# Hybrid Runtime Tasks: 003 BFT Round State Machine

## HR003 Phase 0 — exact prerequisites

- [x] **HR003-001** Verify the exact feature-001/002 merge commits and exit evidence, the Formal GO `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`, and rederive all 24 formal artifact hashes.
- [x] **HR003-002** Before production source, freeze C++/Java toolchain manifests, the compiler/JDK/jextract matrix and the ADR-0010 `REFINEMENT_ONLY` formal-impact report.
- [x] **HR003-003** Create architecture tests proving `delta-core-cpp` has no socket, filesystem, wall-clock, JVM or Python dependency.

## HR003 Phase 1 — C++ pure core

- [x] **HR003-004** Define explicit canonical C++ domain types and encoders without serializing raw memory.
- [x] **HR003-005** Implement checked fixed-width helpers for prepared `bft-int-fixture-v1` values; production quantization/rounding/clipping remains feature 004 scope.
- [x] **HR003-006** Implement pure transition entry point over prior state and canonical command bytes.
- [x] **HR003-007** Implement deterministic state/effect/WAL-record canonical encoders and hashes.
- [ ] **HR003-008** Add GCC/Clang cross-compiler golden-state and endian fixtures.

## HR003 Phase 2 — native runtime and durability

- [ ] **HR003-009** Implement one-handle single-writer reactor and bounded MPSC submission port.
- [ ] **HR003-010** Implement append-only WAL record format, checksum, sequence and durability barrier.
- [ ] **HR003-011** Implement snapshot, WAL replay and vote-journal recovery before command admission.
- [ ] **HR003-012** Implement persist-before-expose effect release and idempotent request/effect replay.
- [ ] **HR003-013** Add crash injection at every append/durability/commit/effect boundary.

## HR003 Phase 3 — C ABI and Java FFM harness

- [ ] **HR003-014** Freeze `delta_abi.h`, descriptor, opaque handle, status taxonomy and size-negotiation rules.
- [ ] **HR003-015** Add boundary wrapper that catches all native exceptions without publishing partial state.
- [ ] **HR003-016** Implement JDK 25 FFM binding/harness and JDK 26 compatibility lane without protobuf/gRPC, transport or Java-owned consensus logic.
- [ ] **HR003-017** Implement direct borrowed-memory and bounded-copy paths with identical fixture results.
- [ ] **HR003-018** Add ABI/formal-semantics/schema/build mismatch startup matrix.
- [ ] **HR003-019** Add pointer-lifetime, release, output-capacity and repeated-call tests.

## HR003 Phase 4 — verification

- [ ] **HR003-020** Run four independent native runtimes over 100 pre-encoded integer tickets and compare exact state/effect/WAL hashes.
- [ ] **HR003-021** Run ASan/UBSan, separate TSan and parser fuzz smoke lanes.
- [ ] **HR003-022** Export normal/view-change/abort/crash/recovery traces and validate formal refinement.
- [ ] **HR003-023** Verify all relevant production mutants remain detectable against the native trace/conformance path.
- [ ] **HR003-024** Publish ABI, durability, compiler, sanitizer, Java compatibility and formal-refinement evidence.

## STOP rule

If implementation needs a new formal action, a Java-owned consensus decision, a split Java/native transaction, or a timer transition not representable by accepted semantics, stop and amend feature 000 before continuing.
