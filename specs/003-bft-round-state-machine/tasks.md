# Tasks: DeltaReduce v1 BFT Round State Machine

**Input**: `spec.md`, `plan.md`, Constitution 2.0.0 and completed features `001–002`.

## Phase 0: Mandatory architecture STOP

- [ ] T000 Search specs/code for authoritative central coordinator, adaptive `H_i`, stale weighting and floating-point reduce paths; record blocking findings in `specs/003-bft-round-state-machine/evidence/preflight.md` and do not implement until none remain in the authoritative lineage.

## Phase 1: Canonical contracts

- [ ] T001 Define `RoundConfig`, validator-set epoch and protocol version models in `src/deltatorrent/domain/round_config.py`.
- [ ] T002 [P] Define `DomainPureWorkTicket` and deterministic ticket-ID/data-range rules in `src/deltatorrent/domain/tickets.py`.
- [ ] T003 [P] Define commitment, shard leaf, availability attestation and AC models in `src/deltatorrent/domain/commitments.py` and `availability.py`.
- [ ] T004 [P] Define vote, quorum certificate, state root and stable error taxonomy in `src/deltatorrent/domain/consensus.py`.
- [ ] T005 Define parameter aggregate/QC models in `src/deltatorrent/domain/aggregates.py`.
- [ ] T006 Implement canonical serialization/hash-domain helpers in `src/deltatorrent/protocol/canonical.py`.
- [ ] T007 Implement canonical Merkle tree rules in `src/deltatorrent/protocol/merkle.py`.
- [ ] T008 Add golden fixtures for all contracts in `tests/fixtures/contracts/deltareduce_v1/003/`.
- [ ] T009 Add cross-language-ready golden contract tests in `tests/contract/test_deltareduce_003_bytes.py`.

## Phase 2: Fixed-point and overflow foundation

- [ ] T010 Define minimal `FixedPointProfile` including integer width, scale, rounding, clipping/rejection, byte order and zero encoding in `src/deltatorrent/fixedpoint/profile.py`.
- [ ] T011 Implement deterministic worker normalization/quantization reference in `src/deltatorrent/fixedpoint/quantize.py`.
- [ ] T012 Implement checked INT64/INT128 add/multiply primitives in `src/deltatorrent/fixedpoint/checked.py`.
- [ ] T013 Implement conservative per-shard accumulator proof in `src/deltatorrent/fixedpoint/bounds.py`.
- [ ] T014 [P] Add rounding/quantization golden vectors in `tests/unit/test_fixedpoint_quantize.py`.
- [ ] T015 [P] Add signed boundary and first-overflow corpus in `tests/unit/test_checked_accumulator.py`.
- [ ] T016 Add config rejection tests for unsafe accumulator headroom in `tests/unit/test_accumulator_bounds.py`.

## Phase 3: Deterministic tickets and transition core

- [ ] T017 Implement canonical domain quota/ticket generation in `src/deltatorrent/consensus/ticketing.py`.
- [ ] T018 Implement pure state and transition function for `TICKETING_OPEN/COMMITTED/AVAILABLE/ELIGIBLE/AGGREGATED/ABORTED` in `src/deltatorrent/consensus/transition.py`.
- [ ] T019 Implement deterministic state-root calculation in `src/deltatorrent/consensus/state_root.py`.
- [ ] T020 Add exhaustive legal/illegal transition model tests in `tests/unit/test_transition_model.py`.
- [ ] T021 Add ticket determinism/domain purity/fixed-`B/H` tests in `tests/unit/test_fixed_tickets.py`.

## Phase 4: BFT votes and durable safety

- [ ] T022 Implement validator-set and `2f+1` quorum verification in `src/deltatorrent/consensus/validator_set.py` and `qc.py`.
- [ ] T023 Implement persist-before-send anti-double-vote guard in `src/deltatorrent/consensus/vote_guard.py`.
- [ ] T024 Implement append-only state/vote journal and replay in `src/deltatorrent/consensus/state_store.py`.
- [ ] T025 Implement deterministic four-validator message harness in `src/deltatorrent/consensus/bft_harness.py`.
- [ ] T026 Add conflicting-config/equivocation/duplicate-signer/wrong-epoch tests in `tests/integration/test_bft_safety.py`.
- [ ] T027 Add crash-after-vote and journal-replay tests in `tests/integration/test_vote_recovery.py`.

## Phase 5: Commitments and availability

- [ ] T028 Implement idempotent commitment registry and `CommitUniqueness` guard in `src/deltatorrent/consensus/commitment_registry.py`.
- [ ] T029 Implement bounded shard verifier/storage-peer port in `src/deltatorrent/availability/storage_peer.py`.
- [ ] T030 Implement AC coverage/quorum verifier in `src/deltatorrent/availability/verifier.py`.
- [ ] T031 Add exact-retry/conflicting-root tests in `tests/unit/test_commit_uniqueness.py`.
- [ ] T032 Add missing/corrupt/wrong-context/duplicate-attester AC tests in `tests/integration/test_availability_certificates.py`.

## Phase 6: Input freeze and seed gate

- [ ] T033 Implement canonical available-tuple freeze/root/QC transition in `src/deltatorrent/consensus/input_freeze.py`.
- [ ] T034 Implement seed derivation port bound to finalized input root in `src/deltatorrent/consensus/seed.py`.
- [ ] T035 Add late-input immutability and message-permutation tests in `tests/unit/test_input_freeze.py`.
- [ ] T036 Add property-based `SeedAfterInputFreeze` tests in `tests/property/test_seed_after_freeze.py`.

## Phase 7: Integer parameter aggregation

- [ ] T037 Implement shard retrieval/root verification and canonical input iterator in `src/deltatorrent/reduce/input_reader.py`.
- [ ] T038 Implement checked integer shard reducer in `src/deltatorrent/reduce/integer_shard.py`.
- [ ] T039 Implement parameter vote/QC and complete non-overlapping assembly in `src/deltatorrent/reduce/assembly.py`.
- [ ] T040 [P] Add flat scalar/vector integer reference tests in `tests/unit/test_integer_shard_reduce.py`.
- [ ] T041 Add wrong-input/config/profile/missing/duplicate shard rejection tests in `tests/integration/test_parameter_qc_assembly.py`.
- [ ] T042 Execute four independent aggregator processes over 100 tickets in `tests/integration/test_100_ticket_bit_identity.py`.

## Phase 8: Adapters, recovery and observability

- [ ] T043 Define protobuf contract in `proto/deltareduce/consensus/v1/consensus.proto` without leaking transport types into domain models.
- [ ] T044 [P] Implement loopback gRPC validator/client adapters in `src/deltatorrent/adapters/grpc/consensus_server.py` and `consensus_client.py`.
- [ ] T045 Implement round CLI/config inspection in `src/deltatorrent/cli/round.py`.
- [ ] T046 Implement structured consensus/ticket/availability/arithmetic telemetry in `src/deltatorrent/consensus/telemetry.py`.
- [ ] T047 Add injected crash points and full transition/QC/artifact replay matrix in `tests/integration/test_consensus_recovery.py`.
- [ ] T048 Add architecture tests in `tests/architecture/test_no_central_or_float_reduce.py`.

## Final Phase: Validation and documentation

- [ ] T049 Document canonical state, vote/QC and arithmetic protocol in `docs/deltareduce/round-state-machine.md`.
- [ ] T050 Publish exit-gate hashes, traces and accumulator proof in `specs/003-bft-round-state-machine/evidence/exit-gate.md`.
- [ ] T051 Run Spec Kit cross-artifact analysis and resolve every mismatch.
- [ ] T052 Run full quality gate and final Constitution Check.

## Dependencies

- T000 is a hard prerequisite for all implementation tasks.
- T001–T009 block serialization and BFT integration.
- T010–T016 block `RoundConfigQC` and aggregation.
- T017–T021 block commitments and state transitions.
- T022–T027 block any finalized QC claim.
- T028–T036 block eligibility and seed generation.
- T037–T042 form the primary mathematical exit gate.
- T043–T048 follow stable domain/transition behavior.
- T049–T052 are final and cannot waive a failed safety gate.

## Implementation Strategy

Prove canonical bytes and checked arithmetic first, then implement the pure transition function, then BFT orchestration. Network adapters and optimizations are last. Do not introduce feature-004 codecs, feature-008 robust filters or model application early.

## Exit Gate

All T000–T052 are complete; four independent aggregators sum 100 tickets and emit identical bytes/hashes; unsafe accumulator configurations, equivocation, unavailable shards, seed-before-freeze and wrong-view proposals are rejected; crash/replay produces no double vote or divergent state; quality and Constitution gates pass.
