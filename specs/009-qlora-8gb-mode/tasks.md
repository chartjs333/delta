# Tasks: Certified Fixed-Ticket QLoRA Mode for 8 GiB GPUs

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `008-certificates-and-consensus`.

## Phase 0: Mandatory STOP checks

- [ ] T000 Verify the authoritative path contains no base mutation, adaptive `H`, partial-ticket eligibility, FP adapter reduce or coordinator-only adapter publication; record evidence in `specs/009-qlora-8gb-mode/evidence/preflight.md`.

## Phase 1: Base, mode and adapter contracts

- [ ] T001 Define `BaseModelManifest`, `QuantizedBaseProfile`, `AdapterConfig`, `AdapterParameterSchema` and composition contracts in `src/deltatorrent/qlora/manifests.py`.
- [ ] T002 Define canonical fingerprints and explicit base-omission policy.
- [ ] T003 Define license/provenance/access-policy fields and repository-safe import contract.
- [ ] T004 Create tiny offline base/tokenizer/adapter fixtures in `tests/fixtures/models/tiny_qlora/`.
- [ ] T005 Add canonical contract/golden fingerprint tests.

## Phase 2: Backend, schema and frozen-base invariants

- [ ] T006 Define backend-neutral quantized-model/adapter port in `src/deltatorrent/qlora/backend.py`.
- [ ] T007 Implement tiny/mock offline backend and pinned production adapter.
- [ ] T008 Implement deterministic target-module resolution and ordered adapter schema in `src/deltatorrent/qlora/adapter_schema.py`.
- [ ] T009 Implement pre/post base logical-hash and buffer checks.
- [ ] T010 Add zero/duplicate/unexpected target, tied parameter and backend-version mismatch tests.
- [ ] T011 Add optimizer/gradient/payload tests proving base tensors never participate.

## Phase 3: Compatibility and memory preflight

- [ ] T012 Implement exact accelerator/kernel/dtype/model/profile compatibility checks in `src/deltatorrent/qlora/preflight.py`.
- [ ] T013 Implement memory estimate, configured hard budget and runtime peak recorder.
- [ ] T014 Add unsupported kernel/dtype/sequence/batch/profile test matrix.
- [ ] T015 Add preflight and runtime budget-exceeded no-publication tests.

## Phase 4: Fixed-ticket local adapter training

- [ ] T016 Implement feature-007 ticket adapter and full `A_j=H` completion guard in `src/deltatorrent/qlora/trainer.py`.
- [ ] T017 Implement adapter-only local optimizer and deterministic data/accounting integration.
- [ ] T018 Implement `parent_adapter-final_adapter`, `A_j` normalization and adapter contribution manifest in `src/deltatorrent/qlora/contribution.py`.
- [ ] T019 Integrate canonical `int16-fixed-v1` adapter sharding/commitment.
- [ ] T020 Add full-ticket reference, OOM, cancellation, data-exhaustion and partial-step tests in `tests/integration/test_fixed_qlora_ticket.py`.

## Phase 5: Certificate and hierarchical reduce integration

- [ ] T021 Add base/mode/schema compatibility checks to ISC/EC/APC paths.
- [ ] T022 Configure robust norm/bucketing/clipping over adapter q-vectors.
- [ ] T023 Add adapter domain×parameter shard plan and committee tests.
- [ ] T024 Add direct fixed-point aggregate comparison in `tests/integration/test_adapter_certificate_chain.py`.
- [ ] T025 Add base/tokenizer/quantization/rank/target/profile mismatch rejection corpus.
- [ ] T026 Add base tensor injection and incomplete adapter coverage rejection tests.

## Phase 6: Adapter ApplyQC and publication

- [ ] T027 Implement exact adapter domain-mix/outer apply adapter in `src/deltatorrent/apply/adapter_engine.py`.
- [ ] T028 Bind base/schema fingerprints into AggregateRootQC and ApplyQC bodies.
- [ ] T029 Implement adapter checkpoint/current-pointer transaction.
- [ ] T030 Add four-validator byte/hash equality and ApplyQC uniqueness tests in `tests/integration/test_adapter_apply_qc.py`.
- [ ] T031 Add base mutation/wrong parent/profile and crash/replay tests.

## Phase 7: Distribution, composition and resume

- [ ] T032 Register certified base and ApplyQC adapter media policies.
- [ ] T033 Implement base cache reuse and adapter-only fetch in `src/deltatorrent/qlora/composition.py`.
- [ ] T034 Implement exact composition/resume/evaluation verification.
- [ ] T035 Add base-cache byte accounting in `tests/integration/test_base_cache_reuse.py`.
- [ ] T036 Add incompatible resume and derived export provenance/license tests.

## Phase 8: Physical 8 GiB qualification

- [ ] T037 Select and license-review the exact reference model/revision; record the decision without committing weights/tokens.
- [ ] T038 Freeze `configs/qlora/8gb-reference.yaml` before execution.
- [ ] T039 Implement physical qualification harness in `src/deltatorrent/qlora/qualification.py` and `tests/hardware/test_qlora_8gb_qualification.py`.
- [ ] T040 Execute one complete fixed ticket plus certified adapter path on the designated physical GPU.
- [ ] T041 Record device/runtime/config/peak/headroom/base-hash/adapter-ratio and result evidence.

## Final Phase

- [ ] T042 Add QLoRA/qualification telemetry and `qlora import/preflight/train/compose/qualify` CLI.
- [ ] T043 Document mode, operational import and qualification in `docs/deltareduce/qlora-8gb.md`.
- [ ] T044 Publish exit evidence and run cross-artifact analysis.
- [ ] T045 Run full quality gate, secret/license scan and final Constitution Check.

## Dependencies

T000 blocks all work. T001–T005 block model loading. T006–T011 block local training. T012–T015 block ticket assignment. T016–T020 block certificate integration. T021–T026 block ApplyQC. T027–T031 block publication/resume. T032–T036 block qualification evidence. T037–T041 are the physical claim gate. T042–T045 are final.

## Exit Gate

All tasks pass; base is immutable and absent from optimizer/delta/shards; only complete fixed tickets commit; adapter certificate/ApplyQC hashes are exact; cache reuses base bytes; the preregistered physical 8 GiB profile completes within budget with auditable evidence.
