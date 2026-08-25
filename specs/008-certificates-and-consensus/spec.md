# Feature Specification: Certificates, Robust Aggregation and Apply Consensus

**Feature Branch**: `008-certificates-and-consensus`  
**Created**: 2026-08-23  
**Status**: Planned — ready for implementation  
**Depends on**: `007-domain-pure-ticket-scheduling`

## 1. Certificate Hierarchy

This phase implements the cryptographic proofs preventing Frankenstein updates—mixing parameter shards, workers, clipping decisions or configurations from different views—and completes Byzantine-robust machine-learning aggregation. No update may advance without its explicit parent certificate.

The mandatory DeltaReduce v1 chain is:

1. **InputSetCertificate (ISC)**: locks the exact canonical array of `{T_j, C_j, AC_j}` before any round randomness is generated or revealed.
2. **EligibilityCertificate (EC)**: binds exact global vector-norm evidence, deterministic trimming/rejection decisions, accepted tickets/workers and clipping limits `gamma_j`.
3. **AggregationPlanCertificate (APC)**: binds the post-ISC seed transcript `rho_t`, randomized bucket assignment, iterative centered-clipping profile/transcript and exact fixed-point scalar weights `alpha_{j}` / `alpha_{b,r}` used by parameter committees.
4. **ParameterShardQC (`QC_s`)**: certifies the exact fixed-point result for one complete `(domain, parameter_shard)` context under one ISC/EC/APC view.
5. **AggregateRootQC**: a Merkle-root quorum certificate tying every required ordered ParameterShardQC together and proving complete non-overlapping model/domain coverage.
6. **ApplyQC**: certifies the unique next global checkpoint and outer-optimizer state derived from one AggregateRootQC.

Every certificate includes protocol version, round/height, validator-set epoch, parent certificate hashes, config/schema/arithmetic roots, canonical body hash and at least `2f+1` unique signatures from its configured `3f+1` validator set.

## 2. Robust Filtering & Aggregation Plan (APC)

Before parameter committees perform fixed-point addition, the BFT protocol must generate an `AggregationPlanCertificate`.

- **Randomized Bucketing**: using a bias-resistant seed `rho_t` generated strictly after ISC finalization, accepted input tickets are assigned to canonical buckets. The seed cannot influence which commitments entered ISC.
- **Exact Norm Evidence**: global vector norms `nu_j = ||u_j||_2` are computed from committed fixed-point vectors using a canonical integer/rational norm profile. Floating-point norms are forbidden in certificate decisions.
- **Eligibility and Trimming**: deterministic global norm rules produce accepted/rejected tickets and exact clipping limits `gamma_j`, finalized by EC.
- **Iterative Centered Clipping**: a versioned algorithm executes over canonical bucket/order inputs for a fixed iteration count and emits exact integer/rational coefficients. Unversioned convergence tolerances or platform floating reductions are forbidden.
- **Accumulator Weights**: APC contains the exact scalar weights and common denominators used by parameter committees. It also contains/references a renewed accumulator safety proof valid for those actual coefficients.

Parameter committees do not choose workers, recompute policy from local views or substitute coefficients. They verify the full certificate chain and execute the linear fixed-point plan exactly.

## 3. Outer Optimizer Consensus (ApplyQC)

The application of the global domain mixture `pi_d`, outer momentum, weight decay and Nesterov update executes within the consensus layer, not on a single coordinator.

Each apply validator locally computes the versioned deterministic transition:

`g_t = sum_{d=1..D} pi_d * tilde(g)_{d,t}`

`m_{t+1} = mu * m_t + g_t`

`theta_{t+1} = Nesterov(theta_t, m_{t+1}, g_t)`

The exact representation, coefficient denominators, rounding, weight-decay placement and Nesterov formula are fixed by `ApplyArithmeticProfile` in `RoundConfig`. Validators must produce byte-identical model and optimizer-state artifacts; tolerance-based equality is forbidden.

Validators sign the tuple:

`(round_height, parent_checkpoint_hash, theta_{t+1}_hash, m_{t+1}_hash, AggregateRootQC_hash, RoundConfig_hash, ApplyArithmeticProfile_hash)`

Gathering `2f+1` valid signatures yields `ApplyQC`. Only then may the current-checkpoint pointer advance and the checkpoint enter the P2P distribution policy for applied models.

## 4. Safety Invariants

- **SeedAfterInputFreeze**: `rho_t` cannot exist as a valid round seed without a finalized ISC and must bind that ISC hash.
- **CertificateParentage**: every certificate/QC references the exact required parent hashes; missing, mismatched or weaker parents fail closed.
- **ViewAtomicity**: all ParameterShardQCs in one AggregateRootQC share one RoundConfig/ISC/EC/APC/schema/apply context.
- **AggregateCompleteness**: AggregateRootQC covers every required domain×parameter shard exactly once.
- **ApplyUniqueness**: for one AggregateRootQC/height, at most one ApplyQC can ever finalize.
- **DomainMixturePreservation**: `pi_d` coefficients are applied exactly as specified in RoundConfig and are agnostic to worker device speed, ticket owner and wall-clock completion time.
- **FixedPointSafety**: robust coefficients and apply coefficients satisfy renewed checked accumulator bounds before parameter/apply votes.

## 5. User Scenarios & Testing

### US1 — Freeze inputs and reveal randomness in the only legal order (Priority: P1)

Validators finalize an ISC over exact tickets/commitments/availability certificates, then derive a bias-resistant seed transcript bound to that ISC.

**Independent Test**: message/API permutation and Byzantine proposer corpus proves that no seed/EC/APC can validate before ISC and late inputs cannot alter the certified array.

**Acceptance Scenarios**:

1. **Given** canonical available tuples, **When** `2f+1` validators sign the same ordered array root, **Then** one ISC finalizes.
2. **Given** no ISC, **When** seed generation or EC/APC voting is requested, **Then** it fails `INPUT_SET_NOT_CERTIFIED`.
3. **Given** a finalized ISC, **When** beacon/reveal shares produce `rho_t`, **Then** the seed transcript binds the ISC and validator-set epoch.
4. **Given** a late commitment/AC after ISC, **When** received, **Then** it cannot enter EC/APC for this round.
5. **Given** two conflicting ISC bodies, **When** votes are evaluated, **Then** quorum intersection and double-vote guards permit at most one final ISC.

### US2 — Certify deterministic robust eligibility and aggregation plan (Priority: P1)

Validators retrieve committed q-vectors, compute exact norm evidence, trim/clip, bucket and execute the fixed robust profile.

**Independent Test**: independent validators produce identical norm evidence, EC/APC bytes and weights under reordered storage/message delivery; malformed/non-canonical/overflowing plans fail.

**Acceptance Scenarios**:

1. **Given** fixed-point vectors, **When** squared norms are computed, **Then** exact integer/rational results match golden fixtures without floating operations.
2. **Given** the EC policy, **When** trimming runs, **Then** accepted/rejected sets, reasons and `gamma_j` are canonical and ISC-subset constrained.
3. **Given** finalized ISC and seed transcript, **When** bucketing runs, **Then** ticket-to-bucket mapping is deterministic and cannot add/remove tickets.
4. **Given** iterative centered-clipping profile, **When** executed, **Then** the fixed iteration transcript and final rational/fixed-point weights are byte-identical across validators.
5. **Given** weights whose worst-case sum violates headroom, **When** APC validation runs, **Then** no APC finalizes.

### US3 — Certify parameter shards and aggregate root atomically (Priority: P1)

Parameter committees execute the APC over their exact shards and form QCs, then aggregate validators bind all QCs under one Merkle root.

**Independent Test**: valid complete shards finalize one AggregateRootQC; missing, duplicate, wrong-domain, wrong-APC or mixed-view shard QCs are rejected.

**Acceptance Scenarios**:

1. **Given** a valid certificate chain, **When** a parameter committee sums `alpha_j * q_{j,s}`, **Then** checked integer bytes and denominator metadata match the direct APC reference.
2. **Given** `2f_s+1` matching votes, **When** `QC_s` finalizes, **Then** it binds exact domain/shard coverage and all parent roots.
3. **Given** one `QC_s` from another ISC/EC/APC/config, **When** aggregate assembly runs, **Then** the entire proposal is rejected as `MIXED_VIEW_SHARD`.
4. **Given** every required ordered QC exactly once, **When** the Merkle aggregate body is signed by `2f+1`, **Then** one AggregateRootQC finalizes.

### US4 — Apply domain mixture and outer optimizer under consensus (Priority: P1)

Apply validators reconstruct domain aggregate values, apply exact `pi_d`, momentum, weight decay and Nesterov transition, and sign one next-state tuple.

**Independent Test**: four apply validators produce byte-identical model/momentum artifacts and one ApplyQC; conflicting output/checkpoint proposals cannot both finalize.

**Acceptance Scenarios**:

1. **Given** AggregateRootQC and parent state, **When** apply executes, **Then** exact `pi_d` from RoundConfig is used regardless of ticket ownership/speed/count distribution.
2. **Given** the same inputs/profile, **When** apply validators execute independently, **Then** theta/momentum bytes and hashes are identical.
3. **Given** a proposal with another parent, aggregate root, `pi_d`, rounding or optimizer state, **When** voting occurs, **Then** validators reject it.
4. **Given** one finalized ApplyQC, **When** a conflicting tuple is proposed for the same aggregate/height, **Then** persist-before-sign guards prevent a second QC.
5. **Given** valid ApplyQC, **When** publication runs, **Then** current pointer advances once and feature-005 `apply-qc-v1` distribution policy accepts the checkpoint.

### US5 — Reject a Frankenstein update (Priority: P1)

A malicious aggregator combines mostly valid parameter shard QCs but substitutes one shard from another configuration/view.

**Independent Test / Exit Gate**: automated malicious mixed-view test is rejected specifically because the proposed shard's parent roots do not match the AggregateRootQC body.

**Acceptance Scenarios**:

1. **Given** one shard from a different APC or ISC, **When** root assembly starts, **Then** it is rejected before aggregate signing.
2. **Given** a Merkle proof for the wrong ordered leaf position, **When** verified, **Then** it fails.
3. **Given** correct shard bytes but a QC from the wrong validator-set epoch/domain/shard, **When** verified, **Then** it fails closed.

## 6. Edge Cases

- ISC array contains duplicate ticket, root or availability certificate.
- Seed transcript has duplicate shares, wrong epoch, missing ISC binding or bias/fallback timeout.
- Norm squared exceeds INT128 and requires declared arbitrary-precision reference representation.
- Zero vector, identical norms, exact trimming boundary and tie ordering.
- Bucket count larger than eligible set or empty bucket.
- Centered-clipping distance zero or exact coefficient rounding tie.
- EC accepts ticket missing from ISC or APC adds ticket missing from EC.
- Alpha denominator zero, non-canonical fraction or negative weight outside policy.
- Actual APC coefficient bound exceeds feature-004 reserved headroom.
- Parameter committee receives correct q bytes under wrong ticket/domain leaf.
- Aggregate has complete shards but one domain missing.
- Apply coefficient multiplication requires wider accumulator than reduce.
- Parent model/optimizer state unavailable or hash mismatch.
- Apply validator crash after signing but before persistence (must be prevented by persist-before-sign).
- Two validator-set epochs overlap at round boundary.
- Certificate signature is valid but signer role/scope is wrong.

## 7. Requirements

### Certificate and consensus requirements

- **FR-001**: Every certificate MUST use canonical bytes, domain-separated hash, round/height/view, validator-set epoch, parent roots, config/schema/profile roots and unique signer set.
- **FR-002**: Certificate verification MUST reject duplicate/unknown/revoked/wrong-role signers, invalid signatures, wrong epoch/context and fewer than `2f+1` valid validators.
- **FR-003**: Validators MUST persist vote intent before signing/transmitting and MUST NOT sign conflicting bodies for the same certificate type/round/height/view.
- **FR-004**: `ISC` MUST contain the exact canonical ordered array of `{ticket, commitment, availability certificate}` and its Merkle root.
- **FR-005**: ISC validation MUST enforce ticket/commit/availability uniqueness, full context binding and subset of the finalized RoundConfig ticket plan.
- **FR-006**: No seed-generation, EC or APC command can be valid before ISC finalization.
- **FR-007**: Seed transcript MUST bind ISC hash, round/height, validator epoch, algorithm/profile and all accepted reveal/beacon evidence.
- **FR-008**: Late or non-ISC inputs MUST be impossible to add to EC/APC.
- **FR-009**: EC MUST bind exact norm evidence root, robust policy/profile, accepted/rejected entries with reason, clipping limit `gamma_j` and ISC parent.
- **FR-010**: EC accepted set MUST be a strict subset of ISC and MUST preserve ticket/domain identity.
- **FR-011**: APC MUST bind ISC, seed transcript, EC, bucket assignment, clipping iteration transcript, final exact weights, coefficient denominator/profile and accumulator proof.
- **FR-012**: ParameterShardQC MUST bind RoundConfig, ISC, EC, APC, domain, shard plan/range, input leaf set, result integer bytes, denominator/count metadata and committee epoch.
- **FR-013**: AggregateRootQC body MUST contain the ordered complete leaf table of all required ParameterShardQC hashes plus a Merkle root and coverage proof.
- **FR-014**: Aggregate assembly MUST reject missing, duplicate, overlapping, wrong-domain, wrong-shard and any parent-root mismatch before voting.
- **FR-015**: Certificate/QC processing MUST be idempotent and restart/replay safe.

### Robust aggregation requirements

- **FR-016**: Norm computation MUST use a versioned canonical integer/rational profile over fixed-point q-vectors and exact scale tables; floating norms are forbidden.
- **FR-017**: Norm arithmetic MUST define ordering, common denominator/scale, squared-sum width, integer square-root/rounding if used and overflow behavior.
- **FR-018**: Robust policy MUST fix trimming rules, tie-break order, bucket counts by domain, centered-clipping formula, iteration count, initial center and exact coefficient quantization.
- **FR-019**: Bucketing MUST derive only from finalized ISC, EC-eligible entries and post-ISC `rho_t`; it cannot change membership.
- **FR-020**: All robust decisions MUST be reproducible from certificate inputs and committed policy bytes.
- **FR-021**: APC scalar weights MUST be canonical non-negative integer/rational values within policy bounds and MUST not depend on worker device speed or completion time.
- **FR-022**: APC MUST include/refer to a checked accumulator proof for actual coefficient bounds; unsafe APC cannot receive votes.
- **FR-023**: Parameter committees MUST execute the APC exactly and MUST NOT independently alter workers, buckets, clipping or weights.
- **FR-024**: Parameter arithmetic MUST remain checked integer/fixed-point with no floating conversion.
- **FR-025**: Domain aggregates MUST remain separate through ParameterShardQC/AggregateRootQC so `pi_d` is applied only in the apply transition.

### Apply consensus requirements

- **FR-026**: `ApplyArithmeticProfile` MUST define exact representations, coefficient scales, multiply/add order, rounding, overflow, weight-decay placement, Nesterov formula and model/checkpoint serialization.
- **FR-027**: `pi_d`, `mu`, learning rate, weight decay and all apply coefficients MUST be canonical integer/rational/fixed-point values committed by RoundConfig/profile.
- **FR-028**: Apply validators MUST verify AggregateRootQC completeness/lineage and parent checkpoint/optimizer hashes before arithmetic.
- **FR-029**: Apply MUST compute `g_t=sum_d pi_d*tilde(g)_{d,t}`, `m_{t+1}=mu*m_t+g_t` and the versioned Nesterov transition exactly.
- **FR-030**: `DomainMixturePreservation` MUST hold: scheduler/worker speed/ownership and arrival order cannot modify `pi_d`.
- **FR-031**: Apply arithmetic MUST be bit-deterministic across validators and use checked widths/proofs; tolerance-based model comparison is forbidden.
- **FR-032**: Apply vote tuple MUST bind round/height, parent model/optimizer, next model/optimizer, AggregateRootQC, RoundConfig and apply-profile hashes.
- **FR-033**: `ApplyQC` MUST require `2f+1` unique apply-validator signatures from the exact epoch.
- **FR-034**: `ApplyUniqueness` MUST hold through persist-before-sign guards and current-pointer compare-and-set: at most one ApplyQC/current checkpoint per aggregate/height.
- **FR-035**: Failed/insufficient apply quorum, arithmetic overflow or artifact mismatch MUST leave parent checkpoint/current pointer unchanged.
- **FR-036**: Feature-005 distribution MUST register `aggregate-root-qc-v1` and `apply-qc-v1`; current checkpoint media type requires ApplyQC.

### Security, observability and interface requirements

- **FR-037**: Worker/storage/validator/committee/apply roles and signing keys MUST be permissioned and scope-checked for each certificate/vote type.
- **FR-038**: Replay store MUST bind signer, certificate/vote type, round/height/view, parent roots and body hash; exact replay is idempotent, conflicting reuse is evidence.
- **FR-039**: Certificate bodies, vote records and audit events MUST be content-addressed and append-only; tensor payloads/private keys are never logged.
- **FR-040**: Verification APIs MUST be transport-independent and support standalone offline certificate-chain verification.
- **FR-041**: CLI MUST expose certificate inspect/verify, robust-plan replay, aggregate-root verify and apply verify commands.
- **FR-042**: Metrics MUST include certificate/vote latency, seed/ISC ordering failures, eligibility reasons, norm/bucket/clipping summaries, coefficient/headroom bounds, mixed-view rejects, apply hash agreement and double-vote evidence.

### Non-Functional Requirements

- **NFR-001**: Four independent validators MUST produce byte-identical ISC/EC/APC/AggregateRootQC/ApplyQC bodies and state hashes for mandatory fixtures.
- **NFR-002**: Mixed-view Frankenstein test MUST be deterministic/offline and reject before AggregateRootQC voting.
- **NFR-003**: Norm/robust/apply reference paths MUST not rely on GPU/BLAS floating reduction behavior.
- **NFR-004**: Fewer than `2f+1` valid signatures or uncertain certificate parentage must fail closed.
- **NFR-005**: Certificate verification SHOULD stream/verify large leaf tables without unbounded allocation.
- **NFR-006**: Robust aggregation is not claimed to defeat every poisoning attack; only specified deterministic policy and BFT view safety are guaranteed.

### Key Entities

- **ISC / SeedTranscript / EC / APC**: exact input, randomness, eligibility and aggregation plan chain.
- **NormEvidence / RobustPolicy / ClippingTranscript**: deterministic robust filtering evidence.
- **ParameterShardQC / AggregateRootQC**: exact shard result and atomic whole-model binding.
- **ApplyArithmeticProfile / ApplyState / ApplyQC**: deterministic outer optimizer and unique next checkpoint proof.
- **CertificateVerifier / VoteGuard / ReplayRecord**: context-bound BFT/security enforcement.

## 8. Success Criteria

- **SC-001**: Seed/EC/APC cannot validate before ISC; late inputs never alter the certified set.
- **SC-002**: Exact norm, trimming, bucket and centered-clipping fixtures produce identical EC/APC bytes on independent validators.
- **SC-003**: Parameter committees produce identical fixed-point results and valid QCs under one APC.
- **SC-004**: Malicious mixed-view parameter shard is rejected due to AggregateRootQC parent/root mismatch.
- **SC-005**: Complete correct shard table finalizes one AggregateRootQC; incomplete/duplicate/overlapping tables cannot.
- **SC-006**: Four apply validators produce identical theta/momentum hashes and one ApplyQC.
- **SC-007**: Conflicting apply proposals, wrong parent/mixture/profile and arithmetic overflow leave current checkpoint unchanged.
- **SC-008**: Distribution accepts certified aggregate/current objects only under the correct policy strength.

## 9. Assumptions

- Validator/committee membership and signing keys are permissioned.
- Robust policy parameters are selected and committed before the round; this spec defines reproducibility/safety, not universal statistical optimality.
- Feature 004 scale/headroom reserves are sufficient only after APC-specific revalidation.
- Local worker training remains outside consensus; only committed fixed-point vectors and certified transforms enter reduce/apply.

## 10. Out of Scope

- Permissionless/Sybil-resistant validator selection and economics.
- Private secure aggregation or hiding worker vectors from committees.
- Zero-knowledge proof of honest local training.
- Unbounded adaptive filtering or convergence-tolerance termination.
- Floating-point/tolerance-based apply fallback.
- Guaranteed detection of every model poisoning/backdoor attack.
