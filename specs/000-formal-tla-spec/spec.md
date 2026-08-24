# Feature Specification: Formal TLA+ and Parametric Proof Baseline

**Feature Branch**: `000-formal-tla-spec`  
**Created**: 2026-08-23  
**Status**: Planned — mandatory predecessor; Formal GO not yet established  
**Depends on**: `main`  
**Blocks**: every implementation task in `001–011`

## 1. Architectural Mandate

Before any Python/PyTorch/BFT/storage/P2P implementation begins, DeltaReduce v1 MUST have an executable and reviewable formal baseline covering:

1. the replicated round state machine;
2. vote, quorum and certificate parentage;
3. commitment and availability lifecycle;
4. input freeze before randomness;
5. parameter-shard and aggregate atomicity;
6. deterministic ApplyQC/current-state transition;
7. explicit failure, timeout, view-change, repair, abort and crash-recovery behavior;
8. parametric quorum, fixed-point, hierarchy and Apply uniqueness theorems;
9. a stable trace/refinement boundary for later implementations.

The formal baseline has two complementary layers:

- **TLA+/TLC** checks finite state spaces, asynchronous interleavings, faults, retries and liveness under declared assumptions.
- **Machine-checked theorem proofs** (reference toolchain: Lean 4) establish parametric statements that finite model checking cannot prove for arbitrary admissible sizes.

Neither layer substitutes for the other. A passing finite model is not a general arithmetic proof; a theorem about sets/integers does not explore crash/message interleavings.

No branch `001–011` may start implementation without an exact compatible `FormalVerificationReport(decision=GO)` produced by this feature.

## 2. Formal System Boundary

### 2.1 Modeled roles

- enrolled workers;
- ticket scheduler/lease transition commands executed by the replicated state machine;
- `3f+1` round/certificate/apply validators;
- regional/parameter committees;
- availability storage peers;
- non-authoritative P2P peers;
- durable vote/state/artifact journals;
- logical timeout/view-change and hard-abort mechanism.

### 2.2 Cryptographic abstraction

Hashes are modeled as collision-resistant identifiers, signatures as unforgeable and role/epoch scoped, and canonical serialization as injective over modeled values. The model verifies correct binding and use of these abstractions, not cryptographic algorithms themselves.

### 2.3 Arithmetic abstraction

Consensus-visible tensors are finite integer vectors or abstract content hashes constrained by a `FixedPointProfile`. TLA+ checks representative bounded values and overflow guards. Lean proves the general accumulator and hierarchical-composition bounds. Floating-point operations do not exist in the consensus model.

### 2.4 Fault model

The mandatory model includes:

- asynchronous message reorder, duplicate, delay and drop;
- proposer equivocation;
- up to `f` Byzantine validators in a `3f+1` set;
- validator crash/restart at every persist/send/finalize boundary;
- temporary and permanent network partitions;
- insufficient quorum;
- worker commitment equivocation;
- storage attestation equivocation;
- missing/corrupt/lost shards before and after ISC;
- bounded repair/retrieval attempts;
- seed/beacon/reveal failure;
- missing/mixed/duplicate parameter shard QCs;
- apply disagreement, apply quorum loss and crash between ApplyQC and current-pointer update;
- replay of commands, votes, certificates and artifacts;
- epoch/key change only between rounds, with emergency abort for compromised active epochs.

Permissionless identities, cryptographic breaks, arbitrary worker-compute verification and universal poisoning resistance are not modeled.

## 3. State and Action Vocabulary

The authoritative TLA+ model MUST expose at least the following state variables, possibly factored into modules:

- `phase`, `height`, `view`, `validatorEpoch`;
- `roundConfig`, `parentCheckpoint`, `currentCheckpoint`;
- `ticketPlan`, `leases`, `ticketStatus`;
- `commitment`, `availabilityCertificate`, `artifactState`;
- `inputSetCertificate`, `seedTranscript`, `eligibilityCertificate`, `aggregationPlanCertificate`;
- `parameterResult`, `parameterQC`, `aggregateRootQC`;
- `applyCandidate`, `applyQC`;
- `volatileVotes`, `durableVotes`, `finalizedCertificates`;
- `timeoutVotes`, `viewChangeQC`, `abortQC`;
- `messages`, `alive`, `byzantine`, `partition`, `logicalTime`;
- `repairAttempts`, `abortReason`, `publishedObjects`.

The action vocabulary MUST include:

- `ProposeRoundConfig`, `VoteRoundConfig`, `FinalizeRoundConfig`;
- `IssueTicket`, `LeaseTicket`, `ExpireLease`, `ReassignTicket`;
- `CommitTicket`, `AttestAvailability`, `FinalizeAvailability`;
- `CloseInput`, `VoteISC`, `FinalizeISC`, `GenerateSeed`;
- `VoteEC`, `FinalizeEC`, `VoteAPC`, `FinalizeAPC`;
- `ProposeParameterResult`, `VoteParameter`, `FinalizeParameterQC`;
- `AssembleAggregateRoot`, `VoteAggregateRoot`, `FinalizeAggregateRootQC`;
- `ComputeApplyCandidate`, `VoteApply`, `FinalizeApplyQC`, `AdvanceCurrentCheckpoint`;
- `SoftTimeout`, `VoteViewChange`, `ViewChange`, `VoteHardAbort`, `HardAbort`;
- `Crash`, `Restart`, `RecoverJournal`;
- `CorruptArtifact`, `LoseArtifact`, `RepairArtifact`;
- `PublishCertifiedObject`, `ReplayMessage`.

Internal implementation steps may refine these actions through stuttering, but no implementation may add an externally visible state transition absent from this vocabulary without first amending the formal baseline.

## 4. Mandatory Safety Properties

The model and proofs MUST establish or explicitly discharge:

- **TypeOK**: every state variable remains inside its declared domain.
- **ConfigUniqueness**: at most one RoundConfigQC finalizes per `(height, epoch)`.
- **TicketImmutability**: domain, data, `B`, `H`, parent and profile never change after config/ticket finalization.
- **LeaseCommitSafety**: only the current lease epoch may commit; an accepted commitment prevents reassignment.
- **CommitUniqueness**: one `ticket_id` maps to at most one distinct commitment root.
- **VoteUniqueness**: an honest validator never durably signs two bodies for one vote context.
- **QCUniqueness**: two conflicting QCs of the same type/context cannot both finalize.
- **AvailabilityBeforeISC**: every ISC tuple has a valid AC covering every committed shard.
- **ISCImmutability**: finalized ISC membership/order/root cannot change.
- **SeedAfterInputFreeze**: no valid seed transcript exists without and outside its finalized ISC.
- **ECSubsetISC**: EC cannot introduce a ticket absent from ISC.
- **APCParentage**: APC binds exact ISC, seed and EC and cannot change membership.
- **ConsensusIntegerOnly**: all modeled reduce/apply values and coefficients are canonical integers/rationals within proved bounds.
- **NoOverflow**: no finalized parameter/apply result contains an unchecked out-of-range intermediate or final value.
- **ShardViewAtomicity**: every ParameterShardQC in an aggregate has identical config/ISC/EC/APC/schema/profile parent roots.
- **AggregateCompleteness**: AggregateRootQC covers every required domain×parameter shard exactly once, with no gaps/overlaps/duplicates.
- **ApplyUniqueness**: at most one ApplyQC finalizes for one `(height, AggregateRootQC)`.
- **CurrentCertified**: current checkpoint changes only to the exact checkpoint named by valid ApplyQC.
- **AbortPreservesParent**: an aborted/non-applied round cannot change current checkpoint.
- **RecoveryIdempotence**: crash/restart/replay cannot create a new vote, certificate, commitment, residual advance or pointer transition beyond the original legal action.
- **ViewChangeCertified**: finalized view metadata changes only with one valid `ViewChangeQC` containing `2f+1` unique context-bound votes from the exact epoch.
- **AbortCertified**: `ABORTED` exists only with one valid `AbortQC`; reaching a hard deadline without quorum blocks non-abort progress but cannot fabricate terminal certification.
- **PlaneSeparation**: worker vectors, commitments, AC fragments and regional/parameter partials never appear in `publishedObjects`.
- **CertifiedPublishOnly**: every distributed current checkpoint has the required certificate policy and lineage.

## 5. Mandatory Liveness Properties and Boundaries

Liveness MUST be stated conditionally. The model MUST NOT claim progress during permanent partition, absence of `2f+1` responsive validators, irrecoverable post-ISC artifact loss or unfair perpetual message suppression.

Under explicit assumptions of eventual synchrony, honest responsive quorum, required artifact availability/repairability, finite worker/committee computation and weak/strong fairness as declared, verify:

- **ConfigEventuallyFinalizesOrAborts**;
- **CommittedEventuallyAvailableOrRejectedBeforeISC**;
- **FrozenRoundEventuallyGetsPlanOrAborts**;
- **PlannedShardEventuallyGetsQCOrRoundAborts**;
- **AggregateEventuallyAppliesOrAborts**;
- **ExistingApplyQCEventuallyRepairsCurrentPointer**;
- **SoftTimeoutEventuallyChangesView**;
- **HardDeadlineEventuallyTerminatesNonfinalizedRound**.

When assumptions fail, required behavior is safety plus an explicit blocked or deterministic `ABORTED` terminal state according to configured hard-deadline policy.

## 6. Explicit Failure and Recovery Semantics

The normative detailed matrix is in `failure-semantics.md`. The following rules are non-negotiable:

1. **Insufficient signatures**: no quorum before a soft deadline triggers deterministic view change; no quorum before hard deadline triggers abort. There is no central/single-validator fallback.
2. **Crash before vote persistence**: no vote exists. Crash after persistence but before/after send restores the same vote and forbids a conflicting one.
3. **Partition**: may block progress but cannot produce conflicting finalized values within the fault model.
4. **Missing AC before ISC**: the tuple is excluded only by the predeclared close policy. After ISC, membership is immutable.
5. **Shard loss after ISC**: retrieve/repair from attested replicas under a bounded policy; if impossible, abort the round without replacing the ticket or changing ISC.
6. **Seed failure**: only a predeclared, ISC-bound fallback transcript may be used; otherwise abort.
7. **Missing/mixed parameter QC**: change view/retry while permitted, then abort; never assemble a partial or Frankenstein aggregate.
8. **Apply disagreement/quorum loss**: parent remains current. A finalized ApplyQC may be replayed to idempotently repair a crashed pointer update.
9. **Epoch/key change**: validator/storage membership is immutable during a round. Normal rotation applies to a later epoch; confirmed active-epoch compromise follows emergency-abort policy.
10. **Finalized history**: recovery or upgrade never deletes, rewrites or reinterprets finalized certificates.

## 7. Parametric Proof Obligations

The theorem layer MUST provide machine-checked proofs for at least:

1. **QuorumIntersection**: for `n=3f+1`, any two subsets of size at least `2f+1` intersect in at least `f+1`; therefore at least one honest validator lies in the intersection when at most `f` are Byzantine.
2. **ConflictingQCImpossible**: quorum intersection plus honest durable no-double-vote implies two conflicting QCs for one context cannot both exist.
3. **FixedPointAccumulatorSafety**: if `|q_j|≤Q`, `|a_j|≤A`, number of terms `N≤Nmax`, and `Nmax*A*Q≤M`, every partial/final sum fits accumulator bound `M`; extend to exact rational common denominators and intermediate multiplication widths.
4. **HierarchicalEqualsFlat**: if regional ticket sets form an exact disjoint partition, summing regional integer numerators equals summing all tickets flat, including domain/shard indexing and exact metadata totals.
5. **AggregateCoverageUniqueness**: exact non-overlapping complete shard coverage has one canonical ordered leaf table/root under the hash abstraction.
6. **ApplyUniqueness**: quorum intersection plus apply vote uniqueness yields at most one ApplyQC/current checkpoint per aggregate/height.
7. **DomainMixturePreservation**: applying immutable `pi_d` to complete per-domain aggregates is independent of worker ownership, speed and arrival order.

The exact theorem statements, assumptions and ownership are normative in `proof-obligations.md`.

## 8. User Scenarios & Testing

### US1 — Detect conflicting BFT finalization (Priority: P1)

A reviewer explores all modeled message orders with one Byzantine validator in a four-validator set.

**Independent Test**: TLC exhaustively checks the mandatory `f=1` safety model; no trace finalizes conflicting config/certificate/apply values.

**Acceptance Scenarios**:

1. **Given** two conflicting proposals and one equivocating validator, **When** messages are arbitrarily reordered/duplicated/dropped, **Then** at most one proposal obtains a valid QC.
2. **Given** honest validator crash after durable vote, **When** it restarts and receives a conflicting proposal, **Then** the restored journal prevents a second vote.
3. **Given** a mutant that removes persist-before-sign, **When** TLC checks it, **Then** the expected double-vote/conflicting-QC counterexample is produced and archived.

### US2 — Verify freeze, availability and repair semantics (Priority: P1)

A reviewer exercises AC shortfall, late commitments and post-ISC shard loss.

**Independent Test**: model checking proves that only AC-covered tuples enter ISC, late tuples never mutate ISC and irrecoverable post-ISC loss leads to abort with parent unchanged.

**Acceptance Scenarios**:

1. **Given** commitment without AC at close, **When** ISC is formed, **Then** the tuple is absent according to the fixed close policy.
2. **Given** finalized ISC, **When** a late AC/commitment arrives, **Then** membership/root do not change.
3. **Given** required shard loss after ISC and another valid replica, **When** repair executes, **Then** exact bytes become available without changing certificate lineage.
4. **Given** no recoverable replica by hard deadline, **When** failure resolves, **Then** round aborts and current checkpoint stays parent.
5. **Given** a mutant that rewrites ISC after shard loss, **When** checked, **Then** ISCImmutability fails with an expected counterexample.

### US3 — Verify no-seed-before-freeze and Frankenstein rejection (Priority: P1)

The model attempts early seed generation and mixed-view shard assembly.

**Independent Test**: every reachable valid seed has an ISC parent; every aggregate root contains only one exact parent view and complete coverage.

**Acceptance Scenarios**:

1. **Given** no ISC, **When** GenerateSeed is attempted, **Then** the action is disabled.
2. **Given** finalized ISC, **When** seed is generated, **Then** it binds the exact ISC hash/epoch.
3. **Given** one shard QC from another APC/config, **When** aggregate assembly is attempted, **Then** the action is disabled/rejected.
4. **Given** a mutant omitting APC parent from shard QC, **When** checked, **Then** a mixed-view counterexample is produced.

### US4 — Verify timeout, partition and recovery boundaries (Priority: P1)

The model loses proposers, validators and connectivity across soft/hard deadlines.

**Independent Test**: safety holds in all mandatory partition/crash models; liveness holds only in configurations enabling eventual synchrony, honest quorum and fairness; permanent insufficient quorum ends in configured abort/block state without current mutation.

**Acceptance Scenarios**:

1. **Given** proposer crash and honest quorum, **When** soft timeout occurs, **Then** view changes and progress can resume.
2. **Given** fewer than `2f+1` responsive validators through hard deadline, **When** timeout resolves, **Then** no QC is fabricated, ordinary progress is disabled and the round remains blocked until an abort quorum can certify the canonical abort body.
3. **Given** finalized ApplyQC and crash before pointer commit, **When** recovery replays it, **Then** pointer advances exactly once.
4. **Given** permanent partition without quorum, **When** liveness is evaluated, **Then** no unconditional progress claim is asserted.

### US5 — Prove arithmetic and hierarchy claims parametrically (Priority: P1)

A reviewer builds the theorem project independently.

**Independent Test**: theorem-prover build checks all mandatory theorems without `sorry`/axiom placeholders beyond explicitly approved cryptographic/hash abstractions.

**Acceptance Scenarios**:

1. **Given** profile bounds satisfying the inequality, **When** accumulator theorem is instantiated, **Then** all permitted sums fit.
2. **Given** first unsafe profile, **When** assumptions are checked, **Then** the theorem precondition cannot be established and config validation must reject it.
3. **Given** exact regional partition, **When** hierarchy theorem is instantiated, **Then** global integer sum equals flat sum.
4. **Given** overlapping/missing regional sets, **When** the theorem is attempted, **Then** partition assumptions fail explicitly.

### US6 — Establish implementation refinement contract (Priority: P1)

Later implementations export canonical traces projected onto the formal vocabulary.

**Independent Test**: a reference trace validator accepts legal model traces and rejects illegal extra transitions, wrong parents, duplicate votes and state-root changes not justified by a formal action.

**Acceptance Scenarios**:

1. **Given** a legal implementation execution, **When** projected, **Then** it is a TLA+ behavior up to allowed stuttering/internal events.
2. **Given** an implementation-specific retry with no external state change, **When** projected, **Then** it maps to stuttering or `ReplayMessage` without inventing a transition.
3. **Given** current pointer changes without ApplyQC, **When** trace is checked, **Then** refinement fails.
4. **Given** a protocol semantic change, **When** no formal model/proof update exists, **Then** formal-impact gate blocks merge.

## 9. Functional Requirements

- **FR-001**: The project MUST provide pinned, checksummed TLA+/TLC and theorem-prover toolchains runnable from a clean offline-capable CI image/cache.
- **FR-002**: Formal modules MUST be separated into types/constants, round lifecycle, availability, certificates, reduce/apply, failures/recovery and refinement/trace layers.
- **FR-003**: Every TLA+ variable/action/invariant/temporal property MUST have a stable identifier and prose mapping.
- **FR-004**: The main `Spec` MUST initialize all variables and define `Next` as the disjunction of explicit protocol/failure/recovery actions plus allowed stuttering.
- **FR-005**: No action may use real wall clock, random choice without modeled transcript, floating-point values or implementation-specific file/network ordering.
- **FR-006**: Validator sets, quorum threshold, workers, tickets, domains, shards, storage peers, messages and fault controls MUST be finite constants in TLC configs.
- **FR-007**: Mandatory safety configuration MUST include `f=1`, four validators, at least three tickets/workers, two domains, two parameter shards and enough storage peers to model availability loss/repair.
- **FR-008**: Separate reduced configs MAY isolate state-explosion-heavy fault families, but every mandatory invariant MUST be checked in at least one relevant config and the coverage map MUST be explicit.
- **FR-009**: Symmetry sets, model values, state constraints and fingerprints MAY reduce state space only when they preserve the checked property; rationale MUST be documented.
- **FR-010**: TLC deadlock detection MUST distinguish legal terminal states (`APPLIED`, `ABORTED`) from accidental deadlocks.
- **FR-011**: Liveness configs MUST declare exact fairness, eventual-synchrony, quorum and artifact-availability assumptions in both TLA+ and prose.
- **FR-012**: Safety configs MUST NOT assume synchrony or honest delivery beyond the cryptographic/Byzantine threshold abstraction.
- **FR-013**: Durable vote persistence MUST be modeled separately from volatile send/receipt state.
- **FR-014**: Crash/restart actions MUST clear only volatile state and recover durable journal/state before new voting.
- **FR-015**: View change MUST require `2f+1` unique durable timeout/view-change votes from the exact validator epoch and MUST preserve finalized state, durable votes and frozen config/ticket/ISC data.
- **FR-016**: Hard abort MUST require `2f+1` unique durable votes over one deterministic content-addressed reason/context body, be terminal for the round and preserve parent current checkpoint. Reaching the hard deadline without this quorum MUST disable non-abort transitions and remain safely BLOCKED.
- **FR-017**: Commitment/lease/availability actions MUST encode exact preconditions for uniqueness, current lease epoch and complete shard coverage.
- **FR-018**: ISC action MUST accept exactly the canonical AC-covered tuple set allowed by the close policy and become immutable.
- **FR-019**: Seed action MUST require finalized ISC and bind its hash/epoch/transcript profile.
- **FR-020**: EC/APC actions MUST be subset/parent preserving and contain no worker-speed-derived mathematical weight.
- **FR-021**: Parameter result/QC actions MUST bind one complete context and checked arithmetic result.
- **FR-022**: AggregateRoot action MUST require exact complete non-overlapping domain×shard coverage and one parent view.
- **FR-023**: Apply actions MUST bind parent current, aggregate root, next model/optimizer hashes and apply profile; current transition requires ApplyQC.
- **FR-024**: Artifact loss/repair MUST preserve content identity; repair cannot substitute bytes or rewrite ISC/certificates.
- **FR-025**: Publication action MUST enforce distribution media/certificate policy and deny local/partial artifacts.
- **FR-026**: Every mandatory safety invariant listed in section 4 MUST appear as executable invariant or as a theorem-linked check with traceability.
- **FR-027**: Every liveness property listed in section 5 MUST appear as a temporal property in a config with explicit assumptions.
- **FR-028**: The theorem project MUST contain no admitted placeholder for mandatory theorems and MUST produce a dependency/axiom report.
- **FR-029**: Quorum theorem MUST be parametric in natural `f` and derive intersection lower bound.
- **FR-030**: Fixed-point theorem MUST cover signed values, intermediate multiply width, sum width, common denominator and hierarchical composition assumptions.
- **FR-031**: Hierarchy theorem MUST require exact disjoint partition and prove per-domain/per-shard sum/metadata equality.
- **FR-032**: Apply uniqueness theorem MUST use explicit vote-context uniqueness and quorum intersection assumptions.
- **FR-033**: Hash/Merkle/canonical-serialization properties MAY be axiomatized only behind named abstractions and MUST not be presented as cryptographic implementation proofs.
- **FR-034**: At least one intentionally weakened mutant MUST exist for each critical class: no durable vote, seed before ISC, mutable ISC, missing shard parent, incomplete aggregate, unchecked overflow and current advance without ApplyQC.
- **FR-035**: Each mutant MUST produce the expected invariant/counterexample; an unexpected pass is a test failure.
- **FR-036**: Counterexample traces MUST be minimized when practical, normalized to canonical JSON and stored with model/config/tool hashes.
- **FR-037**: Formal trace schema MUST include action ID, round/height/view/epoch, actor/role, parent/body/result hashes, durability sequence, logical time and state root.
- **FR-038**: Refinement checker MUST allow documented stuttering/internal events but reject externally visible transitions outside the formal action relation.
- **FR-039**: Later protocol branches MUST map requirements/tasks/tests to formal action/invariant/proof IDs and rerun affected configs/theorems.
- **FR-040**: `FormalVerificationReport` MUST bind source tree, Constitution/ADR/spec hashes, toolchain hashes, modules/configs, explored states/diameter, properties, theorem build, mutants/counterexamples, coverage, limitations, reviewer attestations and `GO|NO_GO`.
- **FR-041**: Decision MUST be `GO` only when all mandatory artifacts pass and verify; missing/incompatible evidence yields `NO_GO`.
- **FR-042**: Report and evidence bundle MUST be content-addressed, reproducible from a clean environment and independently verifiable offline.
- **FR-043**: CI MUST fail on parser/type errors, invariant/liveness violation, deadlock outside legal terminals, theorem/admission placeholder, mutant unexpectedly passing, trace-schema drift or report mismatch.
- **FR-044**: Formal verification MUST run without access to private keys, model weights, datasets or public network.
- **FR-045**: Documentation MUST clearly distinguish proved properties, finite checked scopes, assumptions, abstractions, limitations and unproved claims.
- **FR-046**: A formal semantic change MUST invalidate prior Formal GO through compatibility/hash rules until the new report passes.

## 10. Non-Functional Requirements

- **NFR-001**: Mandatory pull-request formal suite SHOULD complete within 30 minutes on the designated CI runner; deeper nightly models MAY run longer but cannot replace mandatory coverage.
- **NFR-002**: Model/tool versions and JVM/theorem-prover dependencies MUST be pinned and checksummed.
- **NFR-003**: Model-checking results MUST be deterministic for the same source/config/toolchain, modulo documented nondeterministic performance metadata.
- **NFR-004**: State-space optimizations MUST not silently remove a fault/action required by the coverage matrix.
- **NFR-005**: Formal artifacts MUST remain transport/storage/accelerator implementation independent.
- **NFR-006**: The feature MUST not claim proof of cryptographic primitives, permissionless Sybil resistance, honest worker computation, poisoning resistance, convergence or model quality.

## 11. Key Entities

- **FormalConstantSet**: finite model values and derived quorum/profile limits.
- **FormalState / FormalAction**: canonical abstract protocol state and transition.
- **SafetyInvariant / TemporalProperty**: executable state/behavior assertions.
- **FaultScenario / FairnessAssumption**: explicit environment behavior and liveness boundary.
- **ProofObligation / TheoremArtifact**: parametric statement, assumptions, dependencies and checked result.
- **Mutant / ExpectedCounterexample**: deliberately weakened semantics and required failing trace.
- **FormalTrace / RefinementMap**: implementation-to-model event projection.
- **FormalVerificationReport**: content-addressed gate evidence and deterministic decision.

## 12. Success Criteria

- **SC-001**: Mandatory TLC safety configurations complete without invariant violations or illegal deadlocks.
- **SC-002**: Liveness properties hold exactly under their declared assumptions and are not asserted outside them.
- **SC-003**: Every required mutant produces its expected counterexample, demonstrating non-vacuous checks.
- **SC-004**: Machine-checked quorum, fixed-point, hierarchical and Apply theorems build without admitted placeholders.
- **SC-005**: Failure/recovery models cover proposer/validator/storage/network/apply crash points and preserve current state on abort.
- **SC-006**: Legal trace fixtures pass refinement; illegal transition, wrong-parent, double-vote and current-without-ApplyQC fixtures fail.
- **SC-007**: Independent clean-environment verification reproduces the evidence/report hashes and decision.
- **SC-008**: `FormalVerificationReport(decision=GO)` is finalized before any implementation task in 001 begins.

## 13. Assumptions

- At most `f` validators in a `3f+1` epoch are Byzantine for safety theorems.
- Honest validators durably record vote intent before external signature transmission and never conflict within one vote context.
- Cryptographic hashes/signatures/canonical encoding satisfy their named abstractions.
- Liveness assumptions are scenario-specific and never implicit.
- Permissioned identity prevents unbounded Sybil creation within the modeled epoch.

## 14. Out of Scope

- Python/PyTorch implementation or performance optimization.
- Proof of cryptographic algorithms or hardware correctness.
- Permissionless identity/economics/Sybil resistance.
- Verification that workers honestly performed local ML training.
- Universal robust-aggregation/poisoning guarantees.
- Statistical convergence, downstream quality and WAN performance.
- Exhaustive verification of unbounded nodes/messages/state; parametric theorems cover only their stated abstractions.
