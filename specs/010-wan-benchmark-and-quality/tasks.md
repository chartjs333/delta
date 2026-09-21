# Tasks: Reconciled WAN, BFT Safety and Model-Quality Benchmark

**Input**: `spec.md`, `plan.md`, `task-map.md`, Constitution 2.1.0 and exact merged
Feature 009 (`007eb08aa3aaee849128ba428274a9fbda561bf8`).

**Formal impact**: `NONE`; benchmark attestations remain outside the runtime
certificate graph and cannot change current state.

Historical task completion from unmerged PRs is not inherited. A checkbox below
is complete only when current-lineage implementation and machine-readable evidence
exist. The reconciliation verifier completes T000 only; T001 is the next STOP.

## Phase 0: Mandatory STOP prerequisites

- [x] T000 Verify features 003–009 exit evidence and compatibility; any missing or
  failed determinism, certificate, fixed-point, ApplyQC or 8 GiB mode gate blocks
  primary benchmark execution. Current evidence:
  `evidence/reconciliation-status.json` plus
  `scripts/verify_reconciliation_status.py`.
- [ ] T001 Search the future current-lineage benchmark implementation/config for
  adaptive `H`, stale acceptance, floating-point consensus fallback, threshold
  override or central-current authority; publish a zero-tolerance preflight bound
  to its exact source.

## Phase 1: Definition, evidence and result contracts

- [ ] T002 Define `BenchmarkDefinition`, arm, threshold, fault/network profile and
  compatibility models in current-lineage worker/protocol paths.
- [ ] T003 Define `RunManifest`, environment/build/data/evaluation and immutable
  evidence-graph models.
- [ ] T004 Define gate table, `BenchmarkResult`, deterministic GO/NO_GO decision and
  reviewer/evaluator QCs.
- [ ] T005 Implement canonical serialization/hash/signature contexts.
- [ ] T006 Create golden definition/run/evidence/result fixtures under schema 010.
- [ ] T007 Add contract/mutation tests and cross-runtime fixture consumers.

## Phase 2: Preregistration and completeness

- [ ] T008 Implement definition completeness, license and immutable-dependency
  validation.
- [ ] T009 Implement benchmark governance review/attestation without adding runtime
  certificate types.
- [ ] T010 Freeze exact primary model/mode, dataset/domain policy, fixed tickets,
  evaluation tasks, repetitions/seeds, thresholds and missing-run rules.
- [ ] T011 Freeze network/fault/attack profiles.
- [ ] T012 Add post-QC mutation, missing-threshold and mutable-dependency rejection
  tests.

## Phase 3: Reproducible execution foundation

- [ ] T013 Implement source/build/image/dependency/SBOM/environment capture.
- [ ] T014 Implement an isolated benchmark namespace and deterministic run
  orchestrator.
- [ ] T015 Implement scientific, flat, hierarchical and selected QLoRA/full-model
  arm adapters, including the bound Python → Java/Netty → native C++/WAL primary
  path.
- [ ] T016 Implement token/domain/workload identity reconciliation before run
  comparison.
- [ ] T017 Add environment-drift, wrong-arm and token/domain mismatch tests.

## Phase 4: WAN and fault harness

- [ ] T018 Implement deterministic unprivileged network/fault profiles across the
  Python, Java and native runtimes.
- [ ] T019 Implement optional `tc/netem` adapter and profile-conformance tests;
  every output remains labeled `SIMULATED`.
- [ ] T020 Implement worker/validator/storage/region crash, restart, partition and
  churn traces.
- [ ] T021 Implement the Byzantine attack corpus.
- [ ] T022 Add exact trace replay and terminal-outcome tests.

## Phase 5: Immutable evidence collection

- [ ] T023 Implement append-only/content-addressed run evidence collection.
- [ ] T024 Collect bound ticket, stage-receipt, certificate, effect, checkpoint,
  model and evaluation identities for every primary observation.
- [ ] T025 Collect phase timing, byte accounting, GPU/resource and P2P metrics.
- [ ] T026 Implement an offline evidence-graph verifier.
- [ ] T027 Add missing/mutated/reordered/incompatible evidence tests.

## Phase 6: Protocol determinism and safety gate

- [ ] T028 Execute repeated independent validator/aggregator/apply processes and
  compare exact hashes.
- [ ] T029 Execute flat-versus-hierarchical exact equality at primary workload
  scale.
- [ ] T030 Run conflicting config/commit/vote, seed-before-ISC and AC-mutation
  attacks.
- [ ] T031 Run mixed-view Frankenstein, incomplete/duplicate aggregate and
  wrong-epoch attacks.
- [ ] T032 Run unsafe accumulator/runtime-overflow and conflicting-ApplyQC attacks.
- [ ] T033 Run the P2P certificate-downgrade attack.
- [ ] T034 Implement the deterministic safety-gate analyzer.

## Phase 7: Scientific quality gate

- [ ] T035 Execute preregistered reference and DeltaReduce repetitions/seeds with
  equal token/domain exposure.
- [ ] T036 Run validation loss/perplexity and every preregistered downstream and
  post-training evaluation.
- [ ] T037 Implement quality joins/statistics/thresholds/missing-run policy.
- [ ] T038 Add normal-loss-but-downstream-failure and missing-seed tests.
- [ ] T039 Record fixed-point/robust diagnostics and required ablations.

## Phase 8: WAN efficiency, P2P and resilience gates

- [ ] T040 Execute every emulated network profile and reconcile phase times/bytes.
- [ ] T041 Execute initial seed loss with complete and incomplete remaining piece
  unions.
- [ ] T042 Execute approximately 10% worker loss with sufficient and insufficient
  domain capacity.
- [ ] T043 Execute validator/storage crash/restart and region delay/partition
  scenarios.
- [ ] T044 Implement efficiency and resilience analyzers.
- [ ] T045 Run the approved real-WAN pre-pilot variant only after every emulated
  mandatory gate passes.

## Phase 9: Decision and certified report

- [ ] T046 Implement the deterministic all-mandatory decision function.
- [ ] T047 Implement result evaluator vote/QC path and the no-override guard.
- [ ] T048 Generate machine-readable and human-readable reports from one immutable
  gate table.
- [ ] T049 Add GO-all-pass, one-gate-fail, missing-evidence and incompatible-
  definition tests.
- [ ] T050 Produce and verify `BenchmarkResultQC` for the primary definition.

## Final phase

- [ ] T051 Implement the benchmark CLI and operational documentation.
- [ ] T052 Publish complete evidence/report under content-addressed artifact refs;
  never commit restricted data/model weights or secrets.
- [ ] T053 Run cross-artifact analysis and architecture guard proving benchmark
  code cannot weaken protocol semantics.
- [ ] T054 Run the full quality gate and final Constitution Check.

## Dependencies

T000 is the formal/predecessor implementation gate and is complete. T002–T034 and
their mapped HR tasks may implement and test the current-lineage benchmark while
T001 remains open, but T001 blocks DefinitionQC, authorization and every primary,
simulated-WAN or real-WAN execution. T002–T007 block preregistration; T008–T012
block any primary run; T013–T017 block comparisons; T018–T022 block WAN/fault
scenarios; T023–T027 block gate decisions. T028–T034, T035–T039 and T040–T045 are
independent mandatory gate families. T046–T050 require all evidence. T051–T054 are
final.

## Exit gate

All mandatory tasks and preregistered gates pass; every primary DeltaReduce
observation is bound to the complete polyglot stage-receipt lineage; exact
protocol/safety, scientific quality, WAN/P2P and resilience gates are green; and
`BenchmarkResultQC(decision=GO)` is finalized. Any other result blocks Feature 011.
