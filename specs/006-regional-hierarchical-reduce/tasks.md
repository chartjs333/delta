# Tasks: Regional and Parameter-Sharded BFT Integer Reduce

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed feature `005`.

## Phase 0: STOP checks

- [ ] T000 Prove no central coordinator, FP regional numerator/average or post-freeze region exclusion remains in the authoritative path; record evidence.

## Phase 1: Topology contracts

- [ ] T001 Define canonical `ReduceTopology`, region routing and committee epochs in `src/deltatorrent/domain/reduce_topology.py`.
- [ ] T002 Define regional/global result and QC contracts.
- [ ] T003 Implement exact ticket/domain/parameter coverage validator in `src/deltatorrent/reduce/routing.py`.
- [ ] T004 Extend accumulator proof composition for regional→global bounds.
- [ ] T005 Add golden topology/result/QC fixtures and contract tests.

## Phase 2: Regional committees

- [ ] T006 Implement regional input derivation from frozen set.
- [ ] T007 Implement checked regional integer reducer in `src/deltatorrent/reduce/regional.py`.
- [ ] T008 Implement regional vote/QC flow in `src/deltatorrent/reduce/regional_qc.py`.
- [ ] T009 Add unequal region/domain/count reference tests.
- [ ] T010 Add wrong-route/input/profile/proof and overflow tests.
- [ ] T011 Add regional double-vote/restart/quorum tests.

## Phase 3: Global parameter committees

- [ ] T012 Implement required regional-set validator in `src/deltatorrent/reduce/global_integer.py`.
- [ ] T013 Implement checked global partial summation and exact metadata combination.
- [ ] T014 Implement global parameter votes/QCs in `src/deltatorrent/reduce/global_qc.py`.
- [ ] T015 Add duplicate/conflicting/missing regional result tests.
- [ ] T016 Add INT64/INT128 composition boundary tests.

## Phase 4: Complete hierarchy

- [ ] T017 Implement complete domain×parameter-shard assembly in `src/deltatorrent/reduce/hierarchy_assembly.py`.
- [ ] T018 Implement flat oracle adapter using feature-003 reducer.
- [ ] T019 Add three-region bit-exact flat-equivalence integration test.
- [ ] T020 Add arrival/parallel/retry permutation suite.
- [ ] T021 Add mixed-view topology/input/profile/coefficient rejection suite.

## Phase 5: Failure and transport

- [ ] T022 Define bounded reduce protobuf in `proto/deltareduce/reduce/v1/reduce.proto`.
- [ ] T023 Implement regional/global gRPC adapters.
- [ ] T024 Add proposer/member failure, restart and insufficient-quorum scenarios.
- [ ] T025 Add WAN loss/reorder/timeout/cancellation tests.
- [ ] T026 Measure flat versus hierarchical cross-region object/message counts.

## Final Phase

- [ ] T027 Add partial-media distribution denylist regression.
- [ ] T028 Add hierarchy telemetry and inspect CLI.
- [ ] T029 Document protocol in `docs/deltareduce/hierarchical-reduce.md`.
- [ ] T030 Publish exit evidence, cross-artifact analysis and final Constitution Check.

## Dependencies

T000 blocks all work. T001–T005 block committees. T006–T011 block global combine. T012–T016 block complete assembly. T017–T021 are the mathematical gate. T022–T026 are resilience/performance evidence. T027–T030 are final.

## Exit Gate

All tasks pass; three-region hierarchical bytes/hashes equal flat reference; unsafe/mixed views never obtain QCs; committee failure behavior is bounded; cross-region fan-in evidence is recorded; partials remain undistributable.
