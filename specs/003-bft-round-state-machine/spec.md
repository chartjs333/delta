# Feature Specification: DeltaReduce v1 BFT Round State Machine

**Feature Branch**: `003-bft-round-state-machine`  
**Created**: 2026-08-23  
**Status**: Planned — SpecKit reconciled; Phase 0 evidence required before implementation
**Depends on**: `002-local-round-engine`
**Constitution**: 2.1.0
**Formal Semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## 1. Architectural Mandate

This specification replaces the single central coordinator from legacy feature 003 with a replicated Byzantine Fault Tolerant State Machine. The system acts as a deterministic aggregation engine for `Domain-Pure Work Tickets`.

Adaptive local steps (`H_i`), stale-update weighting, device-speed contribution weighting and FP32 global reduction are strictly forbidden. Every honest validator must execute the same transition function over the same canonical bytes and obtain bit-for-bit identical state and aggregate hashes.

A configured validator set contains `3f+1` members. A transition or quorum certificate finalizes only after at least `2f+1` valid votes from that exact validator-set epoch.

## 2. Fixed-Point & Ticket Engine

All non-deterministic training arithmetic is resolved locally by the worker before consensus begins.

- **Domain-Pure Work Ticket**: a worker receives a ticket bound to exactly one data domain `d`, one immutable data range, fixed batch/token budget `B`, fixed local optimizer steps `H`, one parent checkpoint and one parameter schema.
- **Normalized Pseudo-Gradient**: after completing the ticket, the worker computes its local pseudo-gradient using feature 002 and divides it by the effective optimizer-step count `A_j` to produce `hat(Delta)_{j,d}`. A ticket is complete only when `A_j = H`; partial tickets cannot become eligible.
- **Prepared Integer Fixture Input**: feature 003 consumes signed integer vectors `q_{j,s}` encoded by the minimal `bft-int-fixture-v1` conformance profile. The worker-side production quantizer is not implemented in this feature.
- **INT64/INT128 Accumulator**: validators sum canonical integer values in a checked accumulator. Floating-point addition is banned in the BFT reduce phase.
- **Overflow Proof**: before `TICKETING_OPEN`, configuration validation proves that every possible `sum_j a_j q_{j,s}` fits the selected accumulator bounds, including signed extremes and declared clipping/weight headroom.

Feature 003 provides only the integer width, byte order, canonical zero and tensor/shard ordering needed by its conformance fixture. Feature 004 owns production `int16-fixed-v1` encoding, rounding/clipping rules, scalable wire/shard codecs and complete profile negotiation.

## 3. State Machine Lifecycle

| State | Transition Trigger | Deterministic action |
| :--- | :--- | :--- |
| **TICKETING_OPEN** | `RoundConfigQC` finalized | Emit locked domain-pure tickets to enrolled workers. |
| **COMMITTED** | unique Merkle root `C_j` accepted | Bind `ticket_id` to the canonical quantized shard-vector commitment. |
| **AVAILABLE** | availability certificate `AC_j` accepted | Record that all physical shards committed by `C_j` are retrievable from the required storage quorum. |
| **ELIGIBLE** | canonical input freeze finalized, then seed `rho_t` generated | Derive the exact eligible input ordering and committee/bucket inputs without post-seed inclusion changes. |
| **AGGREGATED** | all required parameter-shard quorum certificates formed | Certify checked fixed-point sums and one aggregate state root. |
| **ABORTED** | deterministic terminal failure rule | Preserve the parent checkpoint and publish only failure evidence. |

Feature 003 uses a basic `InputFreezeQC` and `ParameterQC` sufficient to prove BFT execution. Feature 008 upgrades these objects into the full ISC/EC/APC/ParameterShardQC/AggregateRootQC/ApplyQC hierarchy without changing the feature-003 state-transition invariants.

## 4. User Scenarios & Testing

### US1 — Open one deterministic BFT round (Priority: P1)

An operator submits one immutable `RoundConfig` to four validators (`f=1`). Validators independently validate arithmetic bounds and ticket definitions, then finalize one `RoundConfigQC`.

**Independent Test**: the same config delivered in different message orders produces one canonical config hash, the same ticket array and the same `TICKETING_OPEN` state root on all validators.

**Acceptance Scenarios**:

1. **Given** a validator set of `3f+1` and a valid config, **When** `2f+1` validators vote for the same config hash, **Then** exactly one `RoundConfigQC` finalizes for that round/height.
2. **Given** two conflicting configs at one height, **When** votes are processed, **Then** no honest validator signs both and at most one config can obtain a valid QC.
3. **Given** a config whose worst-case integer sum can overflow, **When** validation runs, **Then** ticketing never opens and a stable `ACCUMULATOR_BOUND_UNSAFE` decision is recorded.
4. **Given** identical domain quotas, **When** tickets are generated repeatedly, **Then** their IDs, domains, data ranges, `B`, `H` and ordering are byte-identical.

### US2 — Commit and prove availability of worker vectors (Priority: P1)

A worker completes one ticket, normalizes and quantizes its pseudo-gradient, then commits a Merkle root and uploads physical shards to storage peers.

**Independent Test**: a 100-ticket fixture accepts one root per ticket, rejects equivocation and moves a commitment to `AVAILABLE` only after all declared shards are attested retrievable.

**Acceptance Scenarios**:

1. **Given** a completed ticket with `A_j=H`, **When** canonical shard bytes are committed, **Then** `C_j` binds round/config/ticket/domain/parent/schema/profile and every shard leaf.
2. **Given** the same `ticket_id` and same root, **When** submission is retried, **Then** the original receipt is returned idempotently.
3. **Given** the same `ticket_id` and a different root, **When** submission is processed, **Then** it is rejected as `COMMIT_EQUIVOCATION` and cannot replace the first root.
4. **Given** missing, corrupt or mismatched shard bytes, **When** storage attestations are evaluated, **Then** no `AC_j` finalizes.
5. **Given** a valid availability quorum for every committed shard, **When** `AC_j` is verified, **Then** the ticket may advance to `AVAILABLE` exactly once.

### US3 — Freeze inputs before randomness (Priority: P1)

Validators close the availability window, canonically order the exact available tuple set and finalize an input-freeze root before any seed can be requested or revealed.

**Independent Test**: property tests attempt every API/message ordering and prove that no valid `rho_t` exists without the finalized input-freeze QC; later commitments do not alter the frozen root.

**Acceptance Scenarios**:

1. **Given** a set of available tuples, **When** freeze executes, **Then** entries are sorted by canonical `ticket_id` and one immutable root is finalized.
2. **Given** no finalized input-freeze QC, **When** seed generation is requested, **Then** the request fails closed with `INPUT_NOT_FROZEN`.
3. **Given** a finalized input root, **When** a late commitment or availability certificate arrives, **Then** it is recorded as late but cannot modify eligibility input.
4. **Given** the same freeze root and beacon transcript, **When** honest validators derive `rho_t`, **Then** they obtain identical seed bytes.

### US4 — Produce bit-identical fixed-point aggregates (Priority: P1)

Independent parameter aggregators retrieve the same eligible quantized shards and execute checked integer summation in canonical order.

**Independent Test**: at least four independent aggregator processes sum 100 simulated tickets across multiple parameter shards and produce exactly the same per-shard bytes, hashes, state root and QCs.

**Acceptance Scenarios**:

1. **Given** the same ordered eligible set, **When** messages and physical shard reads arrive in arbitrary order, **Then** canonical summation produces one exact result.
2. **Given** a runtime add/multiply that would exceed the configured bound, **When** checked arithmetic detects it, **Then** the shard and round abort; saturation or wraparound is never accepted.
3. **Given** a shard result from a different input-freeze/config/profile root, **When** a validator is asked to vote, **Then** it rejects the proposal before signing.
4. **Given** `2f+1` matching votes for every required shard, **When** assembly executes, **Then** the state machine enters `AGGREGATED` with one immutable aggregate root.

### US5 — Recover without equivocation or double transition (Priority: P2)

Validators restart or replay messages after a crash.

**Independent Test**: crash injection at every durable transition and vote boundary either resumes to the same state root/QC or aborts without accepting two commitments, votes or aggregates for one context.

**Acceptance Scenarios**:

1. **Given** a persisted vote, **When** the validator restarts and receives a conflicting proposal for the same height/view, **Then** it refuses to sign.
2. **Given** a finalized QC replayed after restart, **When** it is processed again, **Then** state remains unchanged and the same receipt is returned.
3. **Given** a partially written artifact, **When** recovery runs, **Then** only hash-verified durable bytes can become visible to the transition function.

## 5. Edge Cases

- `f=0` single-validator development profile versus the mandatory `f=1` exit gate.
- Duplicate validator IDs, invalid validator-set size or quorum threshold.
- Ticket with zero/negative `B`, `H`, `A_j`, empty domain or data overlap not allowed by config.
- Worker finishes fewer/more than `H` effective optimizer steps.
- Parameter schema with zero-length tensor, tied aliases or shard boundary inside a tensor.
- Prepared integer fixture value exactly at the positive/negative accumulator boundary.
- Negative coefficient `a_j`, zero coefficient or denominator mismatch.
- INT64 proof passes but runtime is configured for INT128, and vice versa.
- Merkle tree with odd leaf count, duplicate leaf index or inconsistent leaf length.
- Availability attestation references correct root but wrong round/ticket/storage epoch.
- Last availability message races with freeze boundary.
- Beacon output is unavailable, duplicated or bound to another input root.
- Byzantine proposer sends different shard bytes to different validators.
- Validator signs, crashes before journal flush and receives a conflicting proposal after restart.
- Timeout/partition leaves fewer than `2f+1` live validators.

## 6. Requirements

### Functional Requirements

- **FR-001**: The system MUST define a versioned canonical `RoundConfig` containing round/height, parent checkpoint, parameter schema, dataset/domain manifest, fixed ticket policy, validator-set epoch, fixed-point profile, accumulator type/bounds, availability policy, deadlines and protocol versions.
- **FR-002**: `RoundConfig` MUST define `f`, exactly `3f+1` unique validators and QC threshold `2f+1`; malformed sets MUST fail before voting.
- **FR-003**: A validator MUST persist a context-bound vote before transmitting it and MUST NOT sign two different hashes for the same round/height/view/vote type.
- **FR-004**: Quorum verification MUST reject duplicate signers, unknown/revoked validators, wrong epoch, malformed signatures and insufficient voting power.
- **FR-005**: The deterministic transition function MUST depend only on prior certified state and canonical command bytes, never wall-clock arrival order, local filesystem enumeration or platform floating behavior.
- **FR-006**: Every `WorkTicket` MUST bind exactly one `domain_id`, immutable data cursor/range, fixed `B`, fixed `H`, parent hash, schema hash, optimizer config hash, arithmetic profile and unique ticket ID.
- **FR-007**: Ticket generation MUST be canonical and preserve the per-domain ticket counts declared by `RoundConfig`.
- **FR-008**: Ticket `B`, `H`, domain, data range and arithmetic profile MUST NOT change after `RoundConfigQC`.
- **FR-009**: A completed worker contribution MUST report `A_j`; only `A_j=H` can be committed for eligibility.
- **FR-010**: The feature-002 worker artifact MUST attest that `hat(Delta)_{j,d}=Delta_{j,d}/A_j` was computed with `A_j=H`; feature 003 MUST bind that artifact and MUST NOT reinterpret or recompute worker floating-point values.
- **FR-011**: The minimal feature-003 `bft-int-fixture-v1` profile MUST define signed integer width, byte order, tensor/shard order and canonical zero encoding. It MUST NOT claim a production quantization, rounding, clipping or scale contract.
- **FR-012**: `Commitment C_j` MUST be a Merkle root over canonical metadata plus ordered shard leaves and MUST bind round/config/ticket/domain/parent/schema/profile.
- **FR-013**: `CommitUniqueness` MUST hold: one `ticket_id` can map to at most one distinct `C_j`; exact retry is idempotent and conflicting reuse is evidence of equivocation.
- **FR-014**: Storage peers MUST attest exact shard content IDs, lengths and retention epoch; an `AvailabilityCertificate AC_j` MUST satisfy the configured unique-attester quorum and cover all leaves in `C_j`.
- **FR-015**: A commitment without a valid `AC_j` MUST NOT enter the frozen input set.
- **FR-016**: Input freeze MUST canonically order exact `{T_j,C_j,AC_j}` tuples and finalize one root/QC before seed generation is callable.
- **FR-017**: `SeedAfterInputFreeze` MUST hold: `rho_t` derivation MUST bind the finalized input-freeze root and reject missing/wrong roots.
- **FR-018**: Late commitments/availability certificates MUST be immutable rejected evidence and MUST NOT mutate the frozen set.
- **FR-019**: Eligible parameter shards MUST be retrieved and verified against `C_j`/`AC_j` before arithmetic.
- **FR-020**: Consensus reduce MUST use only checked integer add/multiply operations in the configured INT64 or INT128 range; floating-point additions are forbidden.
- **FR-021**: Configuration validation MUST compute a conservative worst-case bound for every shard over maximum eligible tickets, integer vector range and coefficient range.
- **FR-022**: `FixedPointSafety` MUST hold strictly: maximum absolute sum plus declared headroom MUST be less than or equal to the accumulator maximum; otherwise ticketing cannot open.
- **FR-023**: Runtime overflow, underflow, saturation or wraparound MUST cause deterministic shard/round failure and MUST never produce a QC.
- **FR-024**: Summation MUST use canonical ticket order and canonical parameter/shard order even though integer addition is associative, so evidence and streaming checkpoints are identical.
- **FR-025**: Each parameter result MUST bind config, input-freeze, eligibility seed/transcript, shard plan, exact input leaf set and result bytes before validators vote.
- **FR-026**: `AGGREGATED` MUST require a complete non-overlapping set of required parameter QCs; missing, duplicate or conflicting shards MUST block transition.
- **FR-027**: State/vote/QC storage MUST be restart-safe and idempotent; replay MUST not advance the same transition twice.
- **FR-028**: Domain contracts MUST remain transport/BFT-engine/storage independent; adapters MUST not redefine transition semantics.
- **FR-029**: Canonical serialization MUST reject unknown critical fields, duplicate map keys, non-canonical integers and schema-version ambiguity.
- **FR-030**: Metrics/events MUST include state height/view, ticket/commitment/availability counts, vote/QC latency, rejected equivocations, accumulator headroom, shard duration and abort reason without logging tensor payloads or secrets.
- **FR-031**: No API in this feature may publish worker commitments, local shards or partial integer sums to the P2P distribution plane.

### Non-Functional Requirements

- **NFR-001**: The mandatory exit suite MUST run four independent validators/aggregators (`f=1`) and 100 tickets in a bounded offline CI environment.
- **NFR-002**: All honest instances MUST produce byte-identical ticket arrays, input roots, per-shard aggregates and final state hashes.
- **NFR-003**: Consensus and storage operations MUST be timeout-bounded, cancellable and replayable with an injected deterministic clock/network.
- **NFR-004**: The portable reference arithmetic path MUST not rely on GPU kernels, BLAS reduction order or host floating-point mode.
- **NFR-005**: Canonical fixtures MUST be executable by an independent implementation without importing application internals.
- **NFR-006**: Safety takes precedence over liveness: fewer than `2f+1` available validators, unavailable shards or uncertain arithmetic MUST stop/abort rather than guess.

### Key Entities

- **RoundConfig / RoundConfigQC**: immutable round, validator, ticket and arithmetic contract plus quorum proof.
- **DomainPureWorkTicket**: one-domain fixed-work assignment.
- **NormalizedPseudoGradient**: worker-local delta divided by exact effective step count.
- **FixedPointProfile**: canonical quantization and checked-accumulator rules.
- **Commitment / CommitmentReceipt**: ticket-bound Merkle root and idempotency/equivocation result.
- **AvailabilityAttestation / AC**: storage evidence that every committed shard is retrievable.
- **InputFreezeRecord / InputFreezeQC**: exact pre-randomness tuple set.
- **ValidatorVote / TransitionQC**: context-bound BFT evidence.
- **ParameterAggregate / ParameterQC**: exact integer shard result and quorum proof.
- **RoundStateRoot**: canonical hash of the replicated state-machine state.

## 7. Success Criteria

- **SC-001**: Four independent validators finalize one config/ticket set and reject conflicting configs/votes.
- **SC-002**: A 100-ticket commitment/availability fixture enforces one root per ticket and full shard retrievability.
- **SC-003**: No-seed-before-freeze property tests cover every message/API permutation.
- **SC-004**: Four independent aggregators produce bit-for-bit identical parameter bytes, hashes and state root for all 100 tickets.
- **SC-005**: Accumulator boundary corpus accepts the maximum safe vector and rejects the first unsafe vector/config without saturation.
- **SC-006**: Wrong config/input/profile/shard view, duplicate signer and Byzantine equivocation proposals never obtain a valid QC.
- **SC-007**: Crash/restart/replay matrix does not produce double votes, duplicate transitions or divergent state roots.
- **SC-008**: Architecture tests find no central authoritative writer, floating reduce or P2P path for local/partial artifacts.

## 8. Assumptions

- Validator and worker membership is permissioned for v1.
- Feature 002 remains the worker-local training primitive; feature 003 constrains valid completion to exact fixed-ticket semantics.
- The reference BFT harness may run in-process/loopback, but state and certificate contracts are production-shaped.
- The authoritative implementation is the native C++ core/runtime exposed through the versioned C ABI; Java is a conformance harness and Python is limited to existing fixture/evidence tooling.
- Robust clipping, randomized bucketing, full certificate hierarchy and outer-model application are completed by feature 008.

## 9. Out of Scope

- A central coordinator compatibility mode.
- Adaptive `H_i`, stale updates, asynchronous acceptance or device-speed weights.
- Floating-point consensus reduction or tolerance-based aggregate equality.
- Robust Byzantine ML filtering beyond structural/lineage checks.
- Full ISC/EC/APC/AggregateRootQC/ApplyQC semantics.
- Production quantization, `int16-fixed-v1`, rounding/clipping policy, scalable delta codecs and profile negotiation (feature 004).
- Protobuf/gRPC, Netty/TLS and production P2P transport (features 005/008).
- P2P distribution, QLoRA qualification and real WAN performance claims.
