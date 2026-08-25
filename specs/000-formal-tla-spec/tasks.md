# Tasks: Formal TLA+ and Parametric Proof Baseline

**Input**: `spec.md`, `plan.md`, `failure-semantics.md`, `proof-obligations.md`, `refinement-contract.md`, Constitution 2.1.0 and ADR-0000/0001.

## Phase 0: Authority and scope freeze

- [x] T000 Record exact Constitution/ADR/DeltaReduce source hashes, modeled/non-modeled claims and formal semantic version in `formal/reports/baseline-inputs.json`.
- [x] T001 Build requirement→action→invariant→config→proof coverage matrix in `formal/reports/coverage-matrix.md`; unresolved semantics are a STOP.
- [x] T002 Validate `failure-semantics.md` against specs 003–008 conceptual contracts and resolve every ambiguous quorum/timeout/repair/abort path before model coding.
- [x] T003 Freeze stable formal IDs for actions, invariants, temporal properties, proof obligations, faults and report fields.

## Phase 1: Reproducible formal toolchain

- [x] T004 Pin TLA+/TLC/SANY/JVM artifacts and checksums in `formal/toolchain/tla.lock` and document approved update policy.
- [x] T005 Pin Lean toolchain and audited dependencies in `formal/proofs/lean-toolchain` and `lakefile.toml`.
- [x] T006 Create offline-capable formal container/build definition and checksum verification under `formal/toolchain/`.
- [x] T007 Add `make formal-parse`, `formal-safety`, `formal-liveness`, `formal-proofs`, `formal-mutants`, `formal-refinement`, `formal-report` and aggregate `formal-check` targets.
- [x] T008 Add CI workflow `.github/workflows/formal.yml` with bounded mandatory jobs and artifact retention.

## Phase 2: Canonical schemas and evidence contracts

- [x] T009 Define `formal/schemas/formal-trace.schema.json` from `refinement-contract.md`.
- [x] T010 Define `formal/schemas/formal-verification-report.schema.json`, deterministic GO/NO_GO function and compatibility ID.
- [x] T011 Implement canonical JSON/hash/report helpers in `formal/scripts/` without depending on production code.
- [x] T012 Add schema mutation, canonicalization and offline report verifier tests.

## Phase 3: TLA+ type, quorum and durable vote core

- [x] T013 Implement finite domains, constants, context keys, type predicates and `TypeOK` in `formal/tla/DeltaReduceTypes.tla`.
- [x] T014 Implement vote/QC formation, unique signers and validator epochs in `DeltaReduceQuorums.tla`.
- [x] T015 Implement durable-vote journal separate from volatile send/receipt state.
- [x] T016 Implement `Crash`, `Restart`, `RecoverJournal` and exact vote replay.
- [x] T017 Add basic config/QC uniqueness safety config and trace fixtures.
- [x] T018 Add crash-before/after-persist/send state coverage checks.

## Phase 4: Tickets, leases, commitments and availability

- [x] T019 Implement immutable ticket plan, lease epoch, expiry/reassignment and current-lease commit preconditions in `DeltaReduceTickets.tla`.
- [x] T020 Implement commitment registry and `CommitUniqueness`.
- [x] T021 Implement shard/content state, availability attestations, AC coverage and `AvailabilityBeforeISC` in `DeltaReduceAvailability.tla`.
- [x] T022 Implement corruption/loss and exact-ID bounded repair actions.
- [x] T023 Add lease race, commitment equivocation, AC shortfall and pre/post-freeze loss configs.

## Phase 5: ISC, randomness and certificate parent graph

- [x] T024 Implement canonical close/freeze, ISC votes/QC and `ISCImmutability` in `DeltaReduceCertificates.tla`.
- [x] T025 Implement ISC-bound seed transcript and `SeedAfterInputFreeze`.
- [x] T026 Implement EC subset/norm-evidence abstraction and parent checks.
- [x] T027 Implement APC seed/EC/ISC parentage, membership preservation, coefficient-bound abstraction and unsafe-plan abort.
- [x] T028 Add late input, early seed, wrong parent, replay and conflicting certificate configs.

## Phase 6: Parameter, aggregate, apply and distribution state

- [x] T029 Implement checked integer parameter-result abstraction, shard vote/QC and context binding in `DeltaReduceReduceApply.tla`.
- [x] T030 Implement complete domain×shard coverage and AggregateRootQC.
- [x] T031 Implement deterministic apply candidate, apply vote/QC and parent/current checks.
- [x] T032 Implement atomic/idempotent `AdvanceCurrentCheckpoint` and crash boundary.
- [x] T033 Implement certified global publication allowlist and `PlaneSeparation`.
- [x] T034 Add mixed-view, incomplete/duplicate aggregate, apply conflict and current-recovery configs.

## Phase 7: Failure, timeout, view-change and liveness model

- [x] T035 Implement asynchronous message multiset, reorder/duplicate/drop and partition controls in `DeltaReduceFailures.tla`.
- [x] T036 Implement soft timeout, view change and immutable hard-deadline abort.
- [x] T037 Implement proposer/validator/storage/apply fault schedules and legal terminal states.
- [x] T038 Compose `Init`, `Next`, invariants and terminal/deadlock predicates in `DeltaReduce.tla`.
- [x] T039 Add mandatory `f=1` safety config with four validators, ≥3 tickets, two domains and two shards.
- [x] T040 Add split-brain/partition, storage repair/loss, vote crash recovery, Frankenstein and ApplyQC recovery configs.
- [x] T041 Add phase-specific liveness specs/config from real `Init` under exact eventual-synchrony, honest-quorum, artifact-availability and fairness assumptions, including a full path to `APPLIED`.
- [x] T042 Generate action reachability/coverage evidence and justify symmetry/state constraints.

## Phase 8: Parametric theorem proofs

- [x] T043 Prove PO-Q1/PO-Q2 in `formal/proofs/DeltaReduce/Quorum.lean`.
- [x] T044 Prove PO-A1/PO-A2/PO-A3, intermediate width, canonical reduced-rational, common-denominator and ADR-0002 rounding results in `FixedPoint.lean`.
- [x] T045 Prove PO-H1/PO-H2 including domain/shard metadata equality in `Hierarchy.lean`.
- [x] T046 Prove PO-C1 canonical key/coverage ordering under named hash abstraction in `Coverage.lean`.
- [x] T047 Prove PO-AP1/PO-AP2/PO-D1/PO-R1/PO-R2, including ApplyQC/current uniqueness, CAS/replay and full durable recovery, in `Apply.lean`.
- [x] T048 Add concrete theorem instantiation examples for INT64, INT128, f=1 and representative topology bounds.
- [x] T049 Add no-`sorry` and axiom/dependency report gate.

## Phase 9: Mutants and expected counterexamples

- [x] T050 Add source-level mutants of production actions for missing durable vote, duplicate commitment, mutable ISC, early seed, missing APC/shard parent, incomplete aggregate, unchecked overflow, current-without-ApplyQC and partial publication.
- [x] T051 Run each mutant, normalize/minimize the expected counterexample and store property/config/tool hashes under `formal/fixtures/counterexamples/`.
- [x] T052 Fail CI if a mutant unexpectedly passes or fails for an unrelated property before reaching its intended fault.

## Phase 10: Trace/refinement baseline

- [x] T053 Implement formal action-labelled trace export/normalization with a hash-bound immutable RoundConfig/schema/shard-plan requirement matrix.
- [x] T054 Implement standalone trace/refinement checker in `formal/scripts/check-refinement.py`.
- [x] T055 Add legal fixtures for normal, view-change, repair, abort and ApplyQC pointer-recovery behaviors.
- [x] T056 Add every mandatory illegal fixture listed in `refinement-contract.md`.
- [x] T057 Publish feature ownership/refinement mapping and `formal_semantics_id`.

## Phase 11: Formal GO evidence and review

- [x] T058 Run all mandatory safety models and record modules/configs, states, distinct states, diameter, terminals and property results.
- [x] T059 Run liveness models and record exact assumptions/fairness plus counterchecks without assumptions where appropriate.
- [x] T060 Build theorem project and archive source/tool/dependency/axiom results.
- [x] T061 Run all mutants/refinement/schema/report verifiers.
- [ ] T062 Reproduce the full gate from a clean offline-capable environment.
- [ ] T063 Generate content-addressed `formal/reports/formal-verification-report.json` and evidence graph.
- [ ] T064 Obtain two independent technical reviews of model scope, liveness assumptions, proof statements and coverage.
- [x] T065 Run Spec Kit cross-artifact analysis and final Constitution Check.
- [ ] T066 Finalize `FormalVerificationReport(decision=GO)` only if every mandatory item verifies; otherwise record `NO_GO` and keep 001 blocked.

## Dependencies

- T000–T003 are hard prerequisites.
- T004–T012 block reproducible model/proof/report work.
- T013–T018 block every certificate safety claim.
- T019–T023 block ISC.
- T024–T028 block parameter/apply modeling.
- T029–T034 block complete safety configs.
- T035–T042 form the TLA+ mandatory gate.
- T043–T049 form the parametric proof gate and may proceed after contracts stabilize.
- T050–T052 prove non-vacuity after the correct model exists.
- T053–T057 establish the later implementation boundary.
- T058–T066 are final and cannot waive any failed predecessor.

## Implementation Strategy

Build the smallest type-correct model first, then add one safety domain at a time with reachable positive/negative traces. Prove parametric lemmas in parallel after contracts freeze. Add liveness only after safety actions/terminal states are stable. Counterexample mutants and trace refinement are mandatory before declaring GO.

## Exit Gate

All T000–T066 tasks complete; mandatory TLC safety/liveness configurations and Lean proofs pass; every mutant fails as expected; trace fixtures discriminate legal/illegal behavior; clean verification reproduces hashes; two independent reviews pass; FormalVerificationReport deterministically returns GO. Until then, all implementation work in 001–011 remains blocked.
