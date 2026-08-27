# Tasks: DeltaReduce v1 BFT Round State Machine

**Input**: `spec.md`, `plan.md`, `runtime-profile.md`, `runtime-tasks.md`, Constitution 2.1.0 and merged features `001–002`.
**Formal Semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

Every task is incomplete until its declared tests and content-addressed evidence pass. Python helpers may generate or inspect fixtures/evidence, but cannot close a validator-state, arithmetic, durability or ABI task.

## Phase 0: Mandatory pre-implementation STOP

- [x] T000 [HR003-001] Verify the exact feature-001 and feature-002 merge commits and their accepted exit-evidence manifests.
- [x] T001 [HR003-001] Verify the exact Formal GO/semantics ID and rederive the 24 formal artifact hashes from the merged baseline.
- [x] T002 [HR003-003] Scan the authoritative lineage and planned native tree for a coordinator, adaptive/stale/device weighting, floating reduce, Java/Python validator state and forbidden core dependencies; require zero findings.
- [x] T003 [HR003-002] Classify ADR-0010 and the planned implementation as `REFINEMENT_ONLY`; emit content-addressed `evidence/preflight.json` binding T000–T002 and stop on any mismatch.

## Phase 1: Canonical protocol contracts

- [x] T004 Define the feature-003 schema registry and domain-separated hash namespaces in `delta-protocol/schemas/003/`.
- [x] T005 Define canonical `RoundConfig`, validator-set and fixed-ticket schema plus valid fixtures.
- [x] T006 [P] Define canonical vote, QC, signer-set and stable rejection schema plus valid/invalid fixtures.
- [x] T007 [P] Define canonical prior-state, command, next-state and effect-batch schema plus fixtures.
- [x] T008 [P] Define canonical WAL record, snapshot and ABI descriptor schema plus fixtures.
- [x] T009 Add malformed, duplicate-key, non-canonical-integer, wrong-version and cross-language fixture corpora.
- [x] T010 Add a runtime-neutral fixture validator and golden-hash manifest; require independent decoding without application internals.

## Phase 2: Toolchains and architecture gates

- [x] T011 [HR003-002] Freeze GCC/Clang, CMake/Ninja, C++ modes, JDK 25/26, jextract and build/dependency lock manifests.
- [x] T012 Define CMake targets for `delta-core-cpp`, `delta-runtime-cpp`, `delta-ffi` and their isolated tests.
- [x] T013 [HR003-003] Add architecture checks proving the pure core has no socket, filesystem, wall-clock, JVM, Python or floating-reduce dependency.
- [x] T014 Add offline CI lanes for GCC/Clang in C++20/C++23 modes and JDK 25/26 descriptor compatibility.
- [x] T015 Publish content-addressed compiler, dependency, source and license manifests.

## Phase 3: C++ pure core

- [ ] T016 [HR003-004] Implement explicit canonical C++ domain types and encoders without raw-memory serialization.
- [ ] T017 [HR003-004] Implement bounded fail-closed parsers for commands, prior state, QCs and prepared integer fixtures.
- [ ] T018 [HR003-005] Implement checked fixed-width signed add/multiply helpers for INT64 and INT128 paths.
- [ ] T019 [HR003-005] Implement conservative accumulator-bound validation for `bft-int-fixture-v1`; do not implement a production quantizer.
- [ ] T020 [HR003-006] Implement the pure transition entry point over prior-state bytes and canonical command bytes.
- [ ] T021 [HR003-007] Implement deterministic next-state, effect-batch and WAL-record encoders and hashes.
- [ ] T022 Add legal/illegal transition, quorum, vote-uniqueness, commitment, availability, input-freeze and abort tests.
- [ ] T023 [HR003-008] Add GCC/Clang cross-compiler and endian golden-byte/state-root fixtures.
- [ ] T024 Run the pure core over the canonical 100-ticket prepared-integer fixture and require exact repeatability.

## Phase 4: Native runtime and durability

- [ ] T025 [HR003-009] Implement one-handle single-writer reactor with a bounded MPSC submission port.
- [ ] T026 [HR003-010] Implement the append-only canonical WAL format, checksum, monotonic sequence and durability barrier.
- [ ] T027 [HR003-011] Implement verified snapshots, WAL replay and deterministic state-root recovery.
- [ ] T028 [HR003-011] Recover the durable vote journal before command admission and reject conflicting post-restart votes.
- [ ] T029 [HR003-012] Implement persist-before-expose effect release and idempotent request/effect replay.
- [ ] T030 [HR003-013] Add crash injection before/during/after append, durability, commit and effect-return boundaries.
- [ ] T031 Add bounded restart, corrupt/torn-record, stale/duplicate command and uninterrupted-versus-replayed equivalence tests.

## Phase 5: Versioned C ABI and Java FFM harness

- [ ] T032 [HR003-014] Freeze `delta_abi.h`, descriptor fields, opaque handles, stable status taxonomy and size-negotiation rules.
- [ ] T033 [HR003-015] Implement the C boundary wrapper; catch every native exception and expose no partial state/effect.
- [ ] T034 [HR003-014] [HR003-019] Implement caller-buffer negotiation, synchronous borrowed-memory rules and explicit handle release.
- [ ] T035 [HR003-016] Implement the minimal JDK 25 FFM descriptor/open/submit/snapshot/close conformance harness.
- [ ] T036 [HR003-016] Add the JDK 26 compatibility lane without protobuf, gRPC, Netty or Java consensus logic.
- [ ] T037 [HR003-017] Require direct borrowed-memory and bounded-copy paths to produce identical canonical effects.
- [ ] T038 [HR003-018] Add ABI/schema/protocol/formal-semantics/build mismatch startup tests that fail closed.
- [ ] T039 [HR003-019] Add pointer-lifetime, release, output-capacity retry and repeated-call tests.

## Phase 6: Refinement and native verification

- [ ] T040 [HR003-022] Export canonical normal, view-change, abort, crash and recovery implementation traces.
- [ ] T041 [HR003-022] Validate legal and illegal traces against the exact accepted feature-000 refinement checker.
- [ ] T042 [HR003-023] Run applicable mutations against real production transition/durability paths and require expected counterexamples.
- [ ] T043 [HR003-020] Run four independent native runtimes (`f=1`) over 100 prepared integer tickets and compare exact state/effect/WAL hashes.
- [ ] T044 [HR003-020] Compare crash/restart execution with uninterrupted execution byte-for-byte.
- [ ] T045 [HR003-021] Run ASan/UBSan lanes on core, runtime and ABI tests.
- [ ] T046 [HR003-021] Run a separate TSan lane over reactor submission, shutdown and recovery.
- [ ] T047 [HR003-021] Run bounded parser and ABI fuzz smoke lanes over the canonical invalid corpus.
- [ ] T048 Re-run architecture/static gates and require no forbidden dependencies, symbols or implementation paths.

## Finalization

- [ ] T049 Update runtime, ABI, durability, recovery and fixture documentation without claiming later-feature transport or quantization.
- [ ] T050 [HR003-024] Publish content-addressed compiler, ABI, sanitizer, Java, native-exit and formal-refinement evidence.
- [ ] T051 Run cross-artifact consistency checks across spec, task map, schemas, descriptors, fixtures, reports and source commit.
- [ ] T052 Run the complete offline phase gate and final Constitution 2.1.0 check; mark tasks complete only from passing evidence.

## Dependencies

- T000–T003 are strictly sequential and block every production-source task.
- T004–T010 freeze bytes before T016–T039 consume them.
- T011–T015 freeze supported toolchains and architecture boundaries before native implementation.
- T016–T024 precede runtime, ABI and Java work.
- T025–T031 precede trace, crash/recovery and four-runtime exit evidence.
- T032–T039 precede Java compatibility and final ABI evidence.
- T040–T048 precede T050–T052.

## Exit Gate

All T000–T052 are complete; four independent native runtimes process 100 prepared integer tickets and emit identical state/effect/WAL hashes; unsafe arithmetic, equivocation, unavailable inputs, seed-before-freeze and wrong-view proposals fail closed; crash/replay exposes no uncommitted effect and creates no double vote or divergent state; compiler, ABI, sanitizer, Java, formal-refinement, quality and Constitution gates pass.
