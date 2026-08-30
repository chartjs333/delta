# Tasks: Preregistered WAN, BFT Safety and Model-Quality Benchmark

**Input**: `spec.md`, `plan.md`, `task-map.md`, Constitution 2.1.0 and exact merged Feature `009`
(`007eb08aa3aaee849128ba428274a9fbda561bf8`).

**Formal impact**: `REGRESSION_ONLY`; benchmark attestations gate Feature 011 but do not extend the
runtime certificate graph or change current state.

## Phase 0: Mandatory STOP prerequisites

- [ ] T000 Verify features 003–009 exit evidence and compatibility; any missing/failed determinism, certificate, fixed-point, ApplyQC or 8 GiB mode gate blocks primary benchmark execution.
- [ ] T001 Search benchmark code/config for adaptive `H`, stale acceptance, FP consensus fallback, threshold override or central-current authority; record zero-tolerance preflight evidence.

## Phase 1: Definition, evidence and result contracts

- [ ] T002 Define `BenchmarkDefinition`, arm, threshold, fault/network profile and compatibility models in `delta-worker-python/src/deltatorrent/benchmark/definition.py` and `delta-protocol/schemas/010/`.
- [ ] T003 Define `RunManifest`, environment/build/data/evaluation and immutable evidence graph models.
- [ ] T004 Define gate table, `BenchmarkResult`, GO/NO_GO decision and reviewer/evaluator QCs.
- [ ] T005 Implement canonical serialization/hash/signature contexts.
- [ ] T006 Create golden definition/run/evidence/result fixtures in `delta-protocol/fixtures/010/`.
- [ ] T007 Add contract/mutation tests in `delta-worker-python/tests/benchmark/` and cross-runtime fixture consumers.

## Phase 2: Preregistration and completeness

- [ ] T008 Implement definition completeness/license/immutable-dependency validation.
- [ ] T009 Implement benchmark governance review/attestation workflow in `delta-worker-python/src/deltatorrent/benchmark/review.py` without adding runtime certificate types.
- [ ] T010 Freeze exact primary model/mode, dataset/domain policy, fixed tickets, evaluation tasks, repetitions/seeds, thresholds and missing-run rules in `configs/benchmark/primary.yaml`.
- [ ] T011 Freeze network/fault/attack profiles under `configs/benchmark/`.
- [ ] T012 Add post-QC mutation, missing-threshold and mutable-dependency rejection tests.

## Phase 3: Reproducible execution foundation

- [ ] T013 Implement source/build/image/dependency/SBOM/environment capture.
- [ ] T014 Implement isolated benchmark namespace and deterministic run orchestrator in `delta-worker-python/src/deltatorrent/benchmark/orchestrator.py`.
- [ ] T015 Implement scientific, flat, hierarchical and selected QLoRA/full-model arm adapters.
- [ ] T016 Implement token/domain/workload identity reconciliation before run comparison.
- [ ] T017 Add environment drift, wrong arm and token/domain mismatch tests.

## Phase 4: WAN and fault harness

- [ ] T018 Implement deterministic unprivileged network/fault profiles across `delta-worker-python/src/deltatorrent/benchmark/`, `delta-node-java/.../benchmark/` and `delta-runtime-cpp/src/benchmark/`.
- [ ] T019 [P] Implement optional `tc/netem` adapter and profile-conformance tests.
- [ ] T020 Implement worker/validator/storage/region crash, restart, partition and churn traces in `fault_profiles.py`.
- [ ] T021 Implement Byzantine attack corpus in `attacks.py`.
- [ ] T022 Add exact trace replay and terminal-outcome tests.

## Phase 5: Immutable evidence collection

- [ ] T023 Implement append-only/content-addressed run evidence collector in `delta-worker-python/src/deltatorrent/benchmark/evidence.py`.
- [ ] T024 Collect ticket/certificate/checkpoint/model/evaluation identities.
- [ ] T025 Collect phase timing, byte accounting, GPU/resource and P2P metrics.
- [ ] T026 Implement offline evidence graph verifier in `delta-worker-python/src/deltatorrent/benchmark/verifier.py`.
- [ ] T027 Add missing/mutated/reordered/incompatible evidence tests.

## Phase 6: Protocol determinism and safety gate

- [ ] T028 Execute repeated independent validator/aggregator/apply processes and compare exact hashes.
- [ ] T029 Execute flat versus hierarchical exact equality at primary workload scale.
- [ ] T030 Run conflicting config/commit/vote, seed-before-ISC and AC mutation attacks.
- [ ] T031 Run mixed-view Frankenstein, incomplete/duplicate aggregate and wrong-epoch attacks.
- [ ] T032 Run unsafe accumulator/runtime overflow and conflicting ApplyQC attacks.
- [ ] T033 Run P2P certificate downgrade attack.
- [ ] T034 Implement deterministic safety gate analyzer in `delta-worker-python/src/deltatorrent/benchmark/safety.py`.

## Phase 7: Scientific quality gate

- [ ] T035 Execute preregistered reference and DeltaReduce repetitions/seeds with equal token/domain exposure.
- [ ] T036 Run validation loss/perplexity and all preregistered downstream/post-training evaluations.
- [ ] T037 Implement quality joins/statistics/thresholds/missing-run policy in `delta-worker-python/src/deltatorrent/benchmark/quality.py`.
- [ ] T038 Add normal-loss-but-downstream-failure and missing-seed tests.
- [ ] T039 Record fixed-point/robust diagnostics and required ablations.

## Phase 8: WAN efficiency, P2P and resilience gates

- [ ] T040 Execute all emulated network profiles and reconcile phase times/bytes.
- [ ] T041 Execute initial seed loss with complete and incomplete remaining piece unions.
- [ ] T042 Execute approximately 10% worker loss with sufficient and insufficient domain capacity.
- [ ] T043 Execute validator/storage crash/restart and region delay/partition scenarios.
- [ ] T044 Implement efficiency and resilience analyzers in `efficiency.py` and `resilience.py`.
- [ ] T045 Run approved real-WAN pre-pilot variant only after emulated mandatory gates pass.

## Phase 9: Decision and certified report

- [ ] T046 Implement deterministic all-mandatory decision function in `delta-worker-python/src/deltatorrent/benchmark/decision.py`.
- [ ] T047 Implement result evaluator vote/QC path and no-override guard.
- [ ] T048 Generate machine-readable and human-readable reports from the same immutable gate table.
- [ ] T049 Add GO-all-pass, one-gate-fail, missing-evidence and incompatible-definition tests in `integration/benchmark/` and runtime-local suites.
- [ ] T050 Produce and verify `BenchmarkResultQC` for the primary definition.

## Final Phase

- [ ] T051 Implement benchmark CLI and operational documentation.
- [ ] T052 Publish complete evidence/report under content-addressed artifact refs; do not commit restricted data/model weights.
- [ ] T053 Run cross-artifact analysis and architecture guard under `integration/benchmark/` proving that benchmark code cannot weaken protocol semantics.
- [ ] T054 Run full quality gate and final Constitution Check.

## Dependencies

T000–T001 are hard STOPs. T002–T007 block preregistration. T008–T012 block any primary run. T013–T017 block comparisons. T018–T022 block WAN/fault scenarios. T023–T027 block gate decisions. T028–T034, T035–T039 and T040–T045 are independent mandatory gate families. T046–T050 require all evidence. T051–T054 are final.

## Exit Gate

All mandatory tasks and preregistered gates pass; evidence independently verifies; exact protocol/safety, scientific quality, WAN/P2P and resilience gates are green; `BenchmarkResultQC(decision=GO)` is finalized. Any other result blocks feature 011.
