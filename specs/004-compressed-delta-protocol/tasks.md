# Tasks: Canonical Fixed-Point Delta and Shard Protocol

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, accepted Formal GO and merged feature 003
`53da4d3c0b236726566fb242fdcae84032b42679`.

The authoritative implementation boundary is C++ core/runtime. Python is an independent fixture
producer and Java is an opaque-byte/FFM conformance harness. `task-map.md` is normative.

## Phase 0: Mandatory predecessor/formal STOP

- [ ] T000 [HR004-001] Verify the exact feature-003 merge, source, evidence overlay, final
  compatibility hash, task closure and ancestry.
- [ ] T001 [HR004-001] Reverify exact Formal GO/semantics and the accepted PO-A1/PO-A2/PO-A3
  theorem artifact/conjunct metadata without claiming PO-A3 proves worker ties-to-even.
- [ ] T002 [HR004-010] Scan the merged tree and planned feature-004 paths for accepted FP
  contribution formats, q→float reduce, per-worker scales, saturation, legacy Python authority and
  residual runtime; require zero findings.
- [ ] T003 [HR004-001] Classify the reconciled plan as `REFINEMENT_ONLY`, bind the concrete Lean
  proof-instance boundary and stop on any new arithmetic/durability/failure semantic.
- [ ] T004 Emit content-addressed `evidence/preflight.json` binding T000–T003 and the exact
  reconciled SpecKit source tree; block every production-source task until it passes.

## Phase 1: Runtime-neutral profile and golden contracts

- [ ] T005 [HR004-002] Freeze `int16-fixed-v1`: signed range, rational scale representation,
  segment/shard scale granularity, signed ties-to-even, canonical zero, little endian, range action,
  maximum shard count/size and accumulator-width selection.
- [ ] T006 [HR004-002] Define versioned profile, scale-table, contribution-manifest, shard,
  shard-plan and accumulator-proof-instance schemas in `delta-protocol/schemas/004/`.
- [ ] T007 [HR004-002] Define valid and bounded invalid profile/shard/proof fixtures, including
  zero-denominator, non-reduced fraction, wrong context and allocation-limit cases.
- [ ] T008 [HR004-002] Commit cross-language golden vectors containing normalized source, profile
  bytes, q integers, payload/envelope bytes, leaf/root hashes, status and proof result.
- [ ] T009 [HR004-006] Implement the independent Python fixture producer under
  `delta-worker-python/src/deltatorrent/reference/` without importing native acceptance code.
- [ ] T010 Register every schema/fixture/media type and publish a deterministic golden-hash
  manifest.
- [ ] T011 Add runtime-neutral schema/fixture verification and negative canonicalization tests.
- [ ] T012 Verify task-map, schema IDs, Formal ID and feature-003 descriptor compatibility before
  native implementation.

## Phase 2: Toolchain and architecture gates

- [ ] T013 [HR004-008] Bind the pinned GCC/Clang C++20/23, CMake, JDK 25/26 and Python toolchains
  to content-addressed execution manifests.
- [ ] T014 Define isolated CMake targets for fixed-point, shard, fuzz and conformance tests without
  new external runtime dependencies.
- [ ] T015 [HR004-010] Add architecture checks proving no accepted float codec, dynamic worker
  scale, q→float reduce, implicit saturation, Python authority or residual runtime exists.
- [ ] T016 Add offline CI lanes for compiler modes, Java conformance, sanitizers and bounded fuzz.

## Phase 3: Authoritative portable C++ encoder

- [ ] T017 [HR004-003] Implement explicit profile/scale/q/proof domain types and canonical
  encoders without raw-memory struct serialization.
- [ ] T018 [HR004-003] Implement reduced positive-denominator rational scale parsing and checked
  intermediate numerator arithmetic.
- [ ] T019 [HR004-003] Implement portable signed round-to-nearest-ties-to-even with explicit
  positive/negative half-way behavior.
- [ ] T020 [HR004-003] Implement fail-closed INT16 encoding over the shared lattice with no
  saturation, wraparound, NaN/Inf coercion or platform casts.
- [ ] T021 [HR004-003] Implement checked INT64 and portable INT128 product/add/prefix helpers and
  exact accumulator width selection.
- [ ] T022 Add zero, smallest-nonzero, half-way, signed-limit, first-out-of-range and huge-input
  native tests.
- [ ] T023 [HR004-008] Require GCC/Clang C++20/23 byte/hash identity against frozen vectors.

## Phase 4: Deterministic shards and language boundary

- [ ] T024 [HR004-004] Implement exact schema-covering deterministic shard planning with no gap,
  overlap or duplicate ordinal.
- [ ] T025 [HR004-004] Implement bounded canonical shard envelopes and writer with explicit
  context/range/length fields.
- [ ] T026 [HR004-004] Implement a streaming reader/verifier that validates limits and context
  before allocation or payload exposure.
- [ ] T027 Implement domain-separated leaf hashes, ordered shard table and commitment root.
- [ ] T028 Add reorder/idempotent-duplicate/conflicting-duplicate/corrupt/truncated/oversized/
  trailing-data tests.
- [ ] T029 [HR004-009] Add parser fuzz/allocation-limit corpus and production-parser mutant cases.
- [ ] T030 [HR004-007] Add JDK 25/26 FFM direct/copy byte-preservation and malformed-envelope
  conformance without q decoding or aggregation.

## Phase 5: Concrete theorem-precondition evidence

- [ ] T031 [HR004-001] [HR004-005] Define a content-addressed proof instance binding theorem IDs,
  `Q`, `A`, `Nmax`, product/partial/final widths, denominator metadata and config/profile/schema
  hashes.
- [ ] T032 [HR004-005] Implement fail-closed native validation of every proof precondition before
  ticketing and every actual input bound before arithmetic.
- [ ] T033 [HR004-005] Add mandatory `maximum-safe: PASS` and `first-unsafe: REJECT` INT64/INT128
  fixtures, including multiplication and incremental-prefix boundaries.
- [ ] T034 [HR004-001] Verify the exact Lean source/build/axiom metadata and named theorem-to-field
  mapping for every concrete instance.
- [ ] T035 Add proof invalidation tests for any profile, scale, count, coefficient, shard coverage,
  config or schema hash change.

## Phase 6: Feature-003 direct-q integration and refinement

- [ ] T036 [HR004-011] Stream bounded verified q values directly into existing feature-003
  checked integer accumulators with no float conversion.
- [ ] T037 [HR004-011] Regress feature-003 prior state plus canonical q stream through native
  state/effect/WAL execution and require exact deterministic identity or an explicitly versioned
  compatibility fixture.
- [ ] T038 [HR004-006] Compare independent Python and authoritative C++ q/payload/envelope/root
  bytes for the full golden corpus.
- [ ] T039 [HR004-011] Export legal direct-q/unsafe-bound traces to the accepted refinement checker
  and require unchecked-overflow/saturation production mutants to be rejected.
- [ ] T040 Add distribution-plane denylist regression for worker q shards and contribution
  manifests.

## Phase 7: Native verification matrix

- [ ] T041 [HR004-009] Run ASan/UBSan and bounded parser fuzz lanes over encoder, proof validator,
  shard writer/reader and C ABI boundary.
- [ ] T042 [HR004-008] Run GCC/Clang C++20/23 and endian identity; add aarch64 only when an exact
  pinned runner is available and report absence without overclaiming.
- [ ] T043 [HR004-007] Run JDK 25/26 direct/copy/malformed input parity against the real native
  boundary.
- [ ] T044 [HR004-010] Re-run architecture/static gates and require zero float/dynamic-scale/
  saturation/Python-authority/residual paths.

## Finalization

- [ ] T045 Document profile, proof-instance, parser and direct-q integration without claiming
  quality, WAN, residual, transport, hierarchy or Apply completion.
- [ ] T046 [HR004-012] Publish content-addressed profile, proof, compiler, parser, Java,
  sanitizer, refinement and feature-003 regression evidence.
- [ ] T047 Run cross-artifact consistency, complete offline quality gate and final Constitution
  2.1.0 check; emit deterministic exit evidence.

## Dependencies

- T000–T004 are strictly sequential and block all production-source tasks.
- T005–T012 freeze bytes and IDs before C++/Python/Java implementations consume them.
- T013–T016 freeze toolchains and architecture gates before native source.
- T017–T023 precede shard and proof integration.
- T024–T030 precede direct-q integration.
- T031–T035 block any accepted RoundConfig/profile.
- T036–T040 precede the final verification matrix.
- T041–T044 precede final evidence.
- Residual/error-feedback runtime is not a feature-004 task and must remain rejected.

## Exit gate

All T000–T047 and HR004-001–HR004-012 obligations pass; two independently designed encoders emit
identical canonical bytes; shard coverage/parser limits and maximum-safe/first-unsafe instances
behave exactly; accepted q values reach feature-003 checked integer accumulation without float
conversion; state/effect/WAL and formal-refinement gates pass; no residual or later-feature path is
used to close the phase.
