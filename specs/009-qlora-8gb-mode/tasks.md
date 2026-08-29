# Tasks: Certified Fixed-Ticket QLoRA Mode for 8 GiB GPUs

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0 and exact completed feature-008 chain:

- merge `62124e58062d876dc4c2fd903b57cfc7d89872d7`;
- source `4ef4daead4e3fcdf19d6947cf8120c4974af09fe`;
- evidence `d86473a3f864b4e61d2312584afa080c8fd4fbab`;
- final report SHA-256 `fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c`;
- formal semantics `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

All semantic tasks are reconciled to `HR009-001–HR009-012` in `task-map.md`. The branch is
`REFINEMENT_ONLY`, keeps `semantic_completeness_claimed=false`, and reuses the feature-008
certificate graph without QLoRA-specific ISC/root/ApplyQC types.

## Phase 0: Mandatory STOP checks

- [x] T000 Verify the exact feature-008 merge/source/evidence/report and Formal GO; reject base mutation, adaptive `H`, partial-ticket eligibility, FP adapter reduce, Java/Python current authority and any parallel QLoRA certificate graph; record physical-runner readiness and canonical evidence in `specs/009-qlora-8gb-mode/evidence/preflight.json`.

## Phase 1: Base, mode and adapter contracts

- [x] T001 Define closed runtime-neutral schemas for mode, base, quantization, adapter config/schema, ticket context, contribution, checkpoint, composition and memory qualification under `delta-protocol/schemas/009/`.
- [x] T002 Define canonical fingerprints, exact resolved ordered target-module list and explicit base-omission/ephemeral-cache policy in protocol schemas and fixtures.
- [x] T003 Define license/provenance/access-policy fields and repository-safe import contract in `delta-worker-python/src/deltatorrent/qlora/manifests.py`.
- [x] T004 Create tiny offline base/tokenizer/adapter fixtures under `delta-protocol/fixtures/009/tiny-offline/` and `delta-worker-python/tests/fixtures/models/tiny_qlora/` without external downloads.
- [x] T005 Add deterministic schema generator/validator plus valid, invalid and cross-language golden fingerprint tests under `specs/009-qlora-8gb-mode/`.

## Phase 2: Backend, schema and frozen-base invariants

- [x] T006 Define the backend-neutral quantized-model/adapter port in `delta-worker-python/src/deltatorrent/qlora/backend.py`.
- [x] T007 Implement tiny/mock offline backend and pinned production adapter.
- [x] T008 Implement deterministic target-module resolution and ordered adapter schema in `delta-worker-python/src/deltatorrent/qlora/adapter_schema.py`.
- [x] T009 Implement pre/post base logical-hash and buffer checks.
- [x] T010 Add zero/duplicate/unexpected target, tied parameter and backend-version mismatch tests under `delta-worker-python/tests/qlora/`.
- [x] T011 Add optimizer/gradient/payload tests proving base tensors never participate and approved ephemeral caches are the only excluded base state.

## Phase 3: Compatibility and memory preflight

- [x] T012 Implement exact accelerator/kernel/dtype/model/profile compatibility checks in `delta-worker-python/src/deltatorrent/qlora/preflight.py`.
- [x] T013 Implement memory estimate, configured hard budget and runtime peak recorder.
- [x] T014 Add unsupported kernel/dtype/sequence/batch/profile test matrix.
- [x] T015 Add preflight and runtime budget-exceeded no-publication tests.

## Phase 4: Fixed-ticket local adapter training

- [x] T016 Implement the feature-007 ticket adapter and full `A_j=H` completion guard in `delta-worker-python/src/deltatorrent/qlora/trainer.py`.
- [x] T017 Implement adapter-only local optimizer and deterministic data/accounting integration.
- [x] T018 Implement `parent_adapter-final_adapter`, `A_j` normalization and adapter contribution manifest in `delta-worker-python/src/deltatorrent/qlora/contribution.py`.
- [x] T019 Integrate canonical `int16-fixed-v1` adapter sharding/commitment.
- [x] T020 Add full-ticket reference, OOM, cancellation, data-exhaustion and partial-step tests in `delta-worker-python/tests/qlora/test_fixed_ticket.py`.

## Phase 5: Certificate and hierarchical reduce integration

- [x] T021 Add C++ `QLORA_ADAPTER` base/tokenizer/quantization/schema context compatibility to the existing ISC/EC/APC paths under `delta-core-cpp/include/delta/qlora/` and `delta-core-cpp/src/qlora/`.
- [x] T022 Configure existing C++ robust norm/bucketing/clipping over canonical adapter q-vectors without a second certificate engine.
- [x] T023 Add the immutable adapter domain×parameter required-key matrix and committee tests.
- [x] T024 Add direct fixed-point aggregate comparison in `delta-core-cpp/tests/qlora_certificate_chain_test.cpp`.
- [x] T025 Add base/tokenizer/quantization/rank/target/profile mismatch rejection fixtures and native tests.
- [x] T026 Add production base-tensor injection and incomplete/extra adapter coverage mutants and tests.

## Phase 6: Adapter ApplyQC and publication

- [x] T027 Implement exact adapter-only domain-mix/outer apply specialization in `delta-core-cpp/include/delta/qlora/adapter_apply.hpp` and `delta-core-cpp/src/qlora/`.
- [x] T028 Bind the existing AggregateRootQC and ApplyQC contexts to mode/base/tokenizer/quantization/schema/parent-adapter fingerprints without new QC types.
- [x] T029 Implement the adapter checkpoint/current-pointer effect through the existing native ApplyQC WAL/CAS transaction.
- [x] T030 Add four-validator byte/hash/effect/WAL equality and ApplyQC uniqueness tests in `delta-core-cpp/tests/qlora_apply_test.cpp`.
- [x] T031 Add base mutation/wrong parent/profile and native crash/replay tests plus bounded C ABI parity in `delta-ffi/src/qlora_abi.cpp` and `delta-ffi/tests/qlora_abi_test.cpp`.

## Phase 7: Distribution, composition and resume

- [x] T032 Register certified base and ApplyQC adapter media policies in the existing C++ distribution verifier and Java transport registry.
- [x] T033 Implement content-addressed base/tokenizer/profile cache reuse and adapter-only fetch in `delta-node-java/src/main/java/io/deltareduce/node/qlora/BaseObjectCache.java` and `AdapterTransport.java`.
- [x] T034 Implement exact native-verified composition/resume/evaluation metadata in Python and Java `ModelComposition` adapters.
- [x] T035 Add Java base-cache byte accounting proving the second adapter fetch transfers zero base bytes.
- [x] T036 Add incompatible resume and derived export provenance/license tests across Python and Java boundaries.

## Phase 8: Physical 8 GiB qualification

- [x] T037 Select and license-review the exact reference model/revision; record the decision without committing weights/tokens.
- [x] T038 Freeze `configs/qlora/8gb-reference.json` before execution.
- [ ] T039 Implement the physical qualification harness in `delta-worker-python/src/deltatorrent/qlora/qualification.py` and `delta-worker-python/tests/hardware/test_qlora_8gb_qualification.py`.
- [ ] T040 Execute one complete fixed ticket plus certified adapter path on the designated physical GPU.
- [ ] T041 Record device/runtime/config/peak/headroom/base-hash/adapter-ratio and result evidence.

## Final Phase

- [ ] T042 Add Python QLoRA/qualification telemetry and `qlora import/preflight/train/compose/qualify` CLI plus Java cache/transport telemetry.
- [ ] T043 Document mode, operational import and qualification in `docs/deltareduce/qlora-8gb.md`.
- [ ] T044 Publish exit evidence and run cross-artifact analysis.
- [ ] T045 Run full quality gate, secret/license scan and final Constitution Check.

## Dependencies

T000 blocks production work. T001–T005 block model loading. T006–T011 block local training. T012–T015 block ticket assignment. T016–T020 block certificate integration. T021–T026 block ApplyQC. T027–T031 block publication/resume. T032–T036 block qualification evidence. T037–T041 are a hard physical claim gate: no runner means `BLOCKED_HARDWARE`, not `PASS`. T042–T045 are final.

## Exit Gate

All tasks pass; base is immutable and absent from optimizer/delta/shards; only complete fixed tickets commit; the existing feature-008 adapter certificate/ApplyQC hashes are exact; cache reuses base bytes; the preregistered physical 8 GiB profile completes within budget with auditable evidence. Tiny/mock evidence cannot satisfy T040–T041 or HR009-011.
