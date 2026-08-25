# Feature Specification: Permissioned Multi-Region DeltaReduce v1 Pilot

**Feature Branch**: `011-multiregion-pilot`  
**Created**: 2026-08-23  
**Status**: Planned — blocked until compatible feature-010 GO  
**Depends on**: `010-wan-benchmark-and-quality`

## Summary

This feature deploys the first real multi-region DeltaReduce v1 pilot on approximately 20–50 permissioned workers across 3–5 regions. It is an operational validation of the already specified architecture, not a place to invent or relax protocol behavior.

The pilot includes:

- fixed domain-pure work tickets and immutable `B/H`;
- one or more `3f+1` BFT validator/committee sets with a minimum `f=1` four-validator safety profile;
- commitment and storage availability certificates;
- `ISC → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC`;
- regional and parameter-sharded checked-integer aggregation;
- deterministic domain mixture and outer optimizer under ApplyQC;
- content-addressed P2P distribution of certified global checkpoints;
- permissioned identity, signed images/configuration, external secrets, audit/evidence collection and controlled chaos exercises.

Remote deployment is prohibited unless feature 010 produced an exact compatible `BenchmarkResultQC(decision=GO)`. The pilot may not add a central coordinator, adaptive local steps, stale updates, floating-point consensus accumulation, post-freeze membership changes or manual certificate overrides.

## Pilot Scope and Required Topology

The exact deployment is frozen in a `PilotDefinition` before provisioning. It must declare:

- 20–50 admitted worker identities and 3–5 regions for the target wave;
- model/training mode: certified full-model profile or certified QLoRA profile;
- dataset/domain policy, fixed ticket quotas, `B/H`, `pi_d` and all arithmetic/certificate profiles;
- global, regional, parameter and apply validator sets and fault threshold `f`;
- storage-peer placement and availability quorum;
- P2P peer/relay/discovery topology;
- software/image/SBOM/provenance roots;
- network, time, key, secret, observability and evidence policies;
- rollout waves, chaos schedule, abort/rollback criteria and final decision gates.

A role may share physical hardware only when the definition explicitly permits it and the resulting failure-domain assumptions remain valid. Logical identities, signing roles and vote scopes remain separate.

## Rollout Waves

1. **Wave 0 — Deployment qualification**: offline artifact/image/config verification; no remote training.
2. **Wave 1 — Four-validator canary**: minimum `f=1` validator set, storage peers and a small worker subset across at least two regions; one complete fixed-ticket round.
3. **Wave 2 — Regional hierarchy canary**: at least three regions, regional/parameter committees and P2P checkpoint propagation.
4. **Wave 3 — Target pilot**: 20–50 workers across 3–5 regions under the frozen primary workload.
5. **Wave 4 — Controlled fault campaign**: preregistered worker, validator, storage, region, key and P2P failures.
6. **Wave 5 — Sustained run and decision**: the declared round/token duration, quality evaluation, evidence sealing and `PilotResultQC`.

Each wave has an independent promotion certificate/checklist. Promotion is monotonic and manual approval cannot waive a failed mandatory gate.

## User Scenarios & Testing

### US1 — Verify the benchmark prerequisite and freeze the pilot definition (Priority: P1)

Operators submit the exact feature-010 result, intended inventory/topology and workload to the pilot review committee.

**Independent Test**: deployment tooling refuses all remote provisioning/training commands unless the supplied `BenchmarkResultQC` is valid, has decision `GO`, and matches the expected source/protocol/model/data/profile compatibility policy.

**Acceptance Scenarios**:

1. **Given** a compatible `BenchmarkResultQC(GO)`, **When** prerequisite verification runs, **Then** its definition/result/evidence roots and signatures are accepted and recorded in `PilotDefinition`.
2. **Given** `NO_GO`, missing evidence, wrong model/data/profile/source, stale compatibility window or insufficient signatures, **When** verification runs, **Then** all remote deployment tasks are blocked.
3. **Given** a complete pilot definition, **When** `2f_p+1` pilot-review validators sign it, **Then** one immutable `PilotDefinitionQC` finalizes.
4. **Given** a post-QC change to inventory, validator set, ticket policy, image, secrets policy, chaos gate or thresholds, **When** rollout is attempted, **Then** a new definition/QC is required.

### US2 — Provision and admit only exact permissioned roles (Priority: P1)

Operators deploy pinned worker, validator, storage, reducer/apply and P2P services using externally supplied secrets and a private/controlled network.

**Independent Test**: apply/reapply/restart/uninstall and identity/role matrix tests prove idempotent deployment; unknown, revoked, wrong-role, wrong-image/config or incompatible nodes cannot join the active pilot.

**Acceptance Scenarios**:

1. **Given** signed/pinned images, configuration and an enrolled node, **When** provisioning runs, **Then** deployed services match expected image/config/SBOM/provenance roots.
2. **Given** wrong/revoked/expired identity or role, **When** the node connects or votes/attests, **Then** authentication/authorization fails before payload use.
3. **Given** a worker with incompatible hardware/model/fixed-point/QLoRA profile or time/network preflight, **When** admission runs, **Then** it is excluded with a stable reason.
4. **Given** provisioning repeated after interruption, **When** automation reruns, **Then** it converges without duplicating identities, votes, volumes, services or secrets.
5. **Given** real private keys/tokens/model credentials, **When** deployment occurs, **Then** they are injected outside images/repository and are redacted from evidence/logs.

### US3 — Complete certified fixed-ticket rounds across regions (Priority: P1)

The admitted target topology executes the frozen workload through all DeltaReduce lifecycle and certificate stages.

**Independent Test**: every honest validator/reducer/apply node reaches the same finalized state roots, hierarchical integer results match the flat oracle, and only ApplyQC-certified checkpoints become current/distributable.

**Acceptance Scenarios**:

1. **Given** an active wave and `RoundConfigQC`, **When** tickets are issued, **Then** every ticket is domain-pure and retains fixed `B/H/data/profile` regardless of worker speed.
2. **Given** completed tickets, **When** commitments and ACs finalize, **Then** ISC freezes exact available tuples before any seed transcript exists.
3. **Given** ISC/EC/APC, **When** regional/parameter committees execute, **Then** checked integer results and QCs bind one exact view and match flat reference for sampled/full verification policy.
4. **Given** complete ParameterShardQCs, **When** AggregateRootQC and apply execute, **Then** all apply validators produce identical next checkpoint/optimizer hashes and one ApplyQC.
5. **Given** ApplyQC, **When** P2P publication/fetch runs, **Then** peers reconstruct exact certified bytes and no local/partial artifact is distributed.
6. **Given** any certificate/arithmetic/coverage mismatch, **When** validators process it, **Then** the round safely rejects/aborts with parent current unchanged.

### US4 — Operate the pilot with complete observability and auditable controls (Priority: P1)

Operators monitor phase progress, certificates, capacity, network, quality and incidents without making dashboards authoritative.

**Independent Test**: dashboards/alerts can be rebuilt from immutable evidence exports; loss of the dashboard does not lose protocol state or the ability to verify a round.

**Acceptance Scenarios**:

1. **Given** an active round, **When** telemetry is collected, **Then** it covers tickets, commitments/ACs, certificate/QC stages, regional/global bytes/times, accumulator headroom, apply hashes, P2P and worker/GPU/resource state.
2. **Given** an alert, **When** an operator inspects it, **Then** the alert links to immutable IDs/hashes and runbook action, not mutable text alone.
3. **Given** an emergency, **When** the kill/stop command is finalized, **Then** new ticketing stops and current certified checkpoint remains unchanged; no unsigned/manual model is promoted.
4. **Given** evidence/log export, **When** verified offline, **Then** all required hashes/signatures/QCs and redaction policies pass.
5. **Given** audit/evidence storage pressure, **When** retention limits approach, **Then** ticketing/promotion follows fail-safe policy rather than discarding mandatory evidence silently.

### US5 — Survive the preregistered worker, validator, storage and P2P fault campaign (Priority: P1)

The pilot executes controlled failure scenarios within and beyond its declared assumptions.

**Independent Test**: within-threshold faults retain safety and the expected liveness; beyond-threshold/availability failures cause a deterministic abort without conflicting certificates or current checkpoint.

**Acceptance Scenarios**:

1. **Given** approximately 10% worker loss with enough completed tickets in every mandatory domain, **When** freeze/deadline policy resolves, **Then** the round completes using only exact certified inputs and unchanged `pi_d`.
2. **Given** concentrated worker loss violating a mandatory domain/quorum rule, **When** deadline resolves, **Then** the round aborts; no adaptive H, synthetic update or implicit domain renormalization occurs.
3. **Given** up to `f` Byzantine/crashed validators and eventual synchrony, **When** conflicting/duplicated/replayed messages occur, **Then** at most one value finalizes and the declared liveness outcome is met.
4. **Given** fewer than `2f+1` reachable validators or unavailable required shards, **When** deadline resolves, **Then** no descendant QC/ApplyQC is fabricated and parent remains current.
5. **Given** initial P2P seed loss after sufficient piece replication, **When** a late worker catches up, **Then** it reconstructs exact checkpoint bytes from remaining peers.
6. **Given** signer revocation/rotation during the campaign, **When** new operations occur, **Then** role/epoch policy is enforced and historical artifacts remain verifiable under recorded trust state.

### US6 — Recover and roll back without rewriting certified history (Priority: P1)

Processes, hosts or regions restart, and operators may stop a failed wave.

**Independent Test**: injected crashes at vote, certificate, artifact and current-pointer boundaries recover to the same state or safe abort; rollback never deletes/reinterprets finalized certificates.

**Acceptance Scenarios**:

1. **Given** persisted votes/state, **When** services restart, **Then** they cannot double-vote, double-commit residuals or apply a checkpoint twice.
2. **Given** an incomplete wave, **When** rollback executes, **Then** services stop/uninstall idempotently while immutable evidence/CAS state and the last ApplyQC checkpoint are retained according to policy.
3. **Given** a config/image upgrade, **When** it is deployed, **Then** it occurs only between rounds/waves under a new signed definition/config epoch.
4. **Given** a failed new version, **When** rollback selects the prior version for future rounds, **Then** previously certified bytes keep their original protocol interpretation.

### US7 — Produce the final pilot decision (Priority: P1)

After the sustained workload and fault campaign, independent evaluators verify all evidence and compute the declared pilot gates.

**Independent Test**: all evaluators over the same evidence root produce the same gate table and `GO`, `NO_GO` or `INCONCLUSIVE` outcome; only `GO` certifies readiness for a subsequent separately specified phase.

**Acceptance Scenarios**:

1. **Given** complete verified evidence and every mandatory safety, quality, efficiency, resilience and operational gate passing, **When** `2f_p+1` evaluators sign, **Then** `PilotResultQC(decision=GO)` finalizes.
2. **Given** any mandatory gate failure, **When** decision runs, **Then** result is `NO_GO` with exact failed gates.
3. **Given** mandatory evidence unavailable/unverifiable under the predeclared policy, **When** decision runs, **Then** result is `INCONCLUSIVE`, never GO.
4. **Given** operator commentary, **When** report is finalized, **Then** it cannot override deterministic gate outcome.

## Edge Cases

- Inventory contains duplicate logical identity or correlated validator failure domains beyond declared policy.
- One physical host runs several roles and fails, reducing multiple quorums simultaneously.
- DNS/overlay route changes while signed endpoint topology remains stale.
- Time synchronization drifts beyond certificate/lease policy.
- Image digest matches but host kernel/driver does not.
- Worker is admitted, then loses free VRAM or disk before ticket execution.
- Storage AC finalizes but retention/disk fails before aggregation.
- ISC deadline races with the final AC.
- Regional committee has quorum but global committee does not.
- Byzantine validator sends different proposal bytes to different regions.
- Apply validators agree on aggregate but disagree due to environment/profile drift.
- P2P discovery fails while existing peer snapshot remains usable.
- Relay/NAT path creates a bandwidth bottleneck not present in emulation.
- Audit/evidence collector becomes unavailable.
- Emergency stop races with an ApplyQC/current-pointer transition.
- Pilot GO prerequisite is cryptographically valid but references another source/image/profile.
- Required licensed model/data cannot be redistributed to one region.

## Requirements

### Prerequisite, definition and governance requirements

- **FR-001**: Remote provisioning/training MUST be blocked until a compatible `BenchmarkResultQC(decision=GO)` from feature 010 is verified.
- **FR-002**: Prerequisite compatibility MUST bind benchmark definition/result/evidence roots, source/tree, protocol versions, model/mode/base/tokenizer/schema, data/domain/ticket profiles, arithmetic/certificate profiles and allowed time/version window.
- **FR-003**: `PilotDefinition` MUST bind target inventory/topology, workload, all role/validator/storage sets, images/configs, network/time/secret policies, waves, chaos scenarios, metrics, thresholds, rollback and decision function.
- **FR-004**: `PilotDefinitionQC` MUST require `2f_p+1` unique signatures from a declared `3f_p+1` review validator set.
- **FR-005**: Any material post-QC change to workload, topology, identities, images, protocol or gates requires a new definition/QC and explicit migration/wave boundary.
- **FR-006**: Pilot deployment MUST be permissioned; anonymous/public participation and unsanctioned role sharing are forbidden.
- **FR-007**: Each wave MUST have preconditions, promotion gates, maximum scope/duration and rollback trigger; failed mandatory gates cannot be waived.

### Deployment, identity and supply-chain requirements

- **FR-008**: Reference deployment MUST provide pinned OCI images for worker, validator/consensus, storage/availability, regional/global reduce, apply, P2P and observability components.
- **FR-009**: Every image/build MUST have content digest, source revision, dependency lock, SBOM, vulnerability-scan result, signature and provenance attestation according to the pilot definition.
- **FR-010**: Provisioning MUST be idempotent and support validate/dry-run/apply/reapply/restart/upgrade/rollback/uninstall while preserving required durable state.
- **FR-011**: Node enrollment MUST bind immutable logical ID, role(s), project/region scope, TLS identity, signing keys, validity, revocation/rotation state and hardware/software fingerprint.
- **FR-012**: Authentication MUST use verified credentials; authorization MUST be deny-by-default by method, role, project, region, round and certificate/vote type.
- **FR-013**: Validator/storage/worker/peer endpoints MUST require authenticated encrypted transport outside explicit local test mode.
- **FR-014**: Private keys, API/model tokens and sensitive configuration MUST be externally injected, least-privilege, rotatable and absent from repository/images/logs/evidence.
- **FR-015**: Pilot networking MUST use a documented private/controlled overlay, relay and reachability policy; public exposure requires explicit approved endpoint policy.
- **FR-016**: Exact time synchronization source, maximum skew and fail-safe behavior MUST be monitored for every role.
- **FR-017**: Admission MUST verify image/config/protocol identity, role keys, region, clock, storage, network, hardware/memory and model/fixed-point/QLoRA compatibility before active inventory inclusion.
- **FR-018**: Revoked/quarantined/incompatible nodes MUST be removed from new tickets, votes, attestations and advertisements according to deterministic epoch policy.

### Protocol-operation requirements

- **FR-019**: The target wave MUST include 20–50 admitted workers across 3–5 regions, unless the frozen definition documents a smaller canary wave before promotion.
- **FR-020**: Every consensus/committee set MUST satisfy exact `3f+1` membership and `2f+1` quorum; the primary pilot MUST support at least `f=1`.
- **FR-021**: Validator placement MUST account for independent failure domains and document any physical/administrative correlation.
- **FR-022**: Every work unit MUST be a feature-007 domain-pure ticket with immutable data, `B`, `H`, parent and profile; worker speed affects only admission/lease capacity.
- **FR-023**: Only complete tickets with `A_j=H` may commit; partial, stale or adaptively modified work cannot enter ISC.
- **FR-024**: Commitments and ACs MUST bind exact shards/storage epochs and satisfy `CommitUniqueness` and availability quorum before ISC.
- **FR-025**: Seed generation/reveal MUST be impossible before ISC; EC/APC/parameter committees MUST verify the exact certificate parents.
- **FR-026**: All robust, regional/global reduce and apply arithmetic MUST use the configured canonical integer/rational fixed-point profiles and checked accumulator proofs.
- **FR-027**: Hierarchical output MUST equal the flat integer oracle for the declared verification sample/full policy; any mismatch stops the wave.
- **FR-028**: AggregateRootQC MUST cover every required domain×parameter shard exactly once and reject mixed views.
- **FR-029**: Apply validators MUST produce byte-identical checkpoint/optimizer artifacts and one ApplyQC; no single service can advance current state.
- **FR-030**: Current checkpoint pointer MUST advance only through valid ApplyQC compare-and-set and remain unchanged on failed/aborted rounds.
- **FR-031**: Distribution MUST accept only media types with the required certification policy; local/commitment/availability/partial artifacts remain hard-denied.
- **FR-032**: P2P clients MUST verify manifest, certificate policy, pieces and full object before use/seeding.
- **FR-033**: Every mutating protocol/deployment command MUST be idempotent/replay-protected and restart-safe.

### Observability, operations and evidence requirements

- **FR-034**: Metrics/logs/audit/evidence MUST cover node/inventory state, tickets, C/AC/ISC/seed/EC/APC, shard/AggregateRoot/Apply QCs, accumulator headroom, bytes/latencies, GPU/resources, P2P, quality, alerts and incidents.
- **FR-035**: Dashboards MUST be reconstructible views; protocol/evidence truth remains durable signed/content-addressed records.
- **FR-036**: Alert rules MUST be versioned and include quorum risk, double-vote/equivocation, certificate-parent mismatch, accumulator risk, storage unavailability, clock drift, image/config drift, missing domain tickets, apply disagreement, P2P piece loss and evidence-health failures.
- **FR-037**: Operator controls MUST provide status, pause/stop ticketing, quarantine identity, revoke/rotate key, inspect/verify certificates, retry safe operations and execute rollback without unsigned model promotion.
- **FR-038**: Emergency stop MUST be a deterministic/authenticated control that prevents new work while preserving any already finalized certificate/current checkpoint semantics.
- **FR-039**: Runbooks MUST cover worker/validator/storage/region/P2P failure, certificate conflict, overflow, key compromise, clock drift, image drift, disk pressure and evidence-collector outage.
- **FR-040**: Evidence exports MUST contain source/build/image/SBOM, definition/inventory/config, all certificate roots, run/round manifests, network/fault traces, metrics summaries, quality results, incidents/actions and final decision inputs.
- **FR-041**: Offline verifier MUST validate hashes, signatures, QCs, configuration compatibility, gate calculations and redaction/retention without relying on live services.
- **FR-042**: Mandatory evidence loss/corruption MUST fail wave promotion/final GO according to the predeclared policy.

### Fault campaign, recovery and decision requirements

- **FR-043**: Chaos scenarios MUST be frozen before execution and identify target roles/regions, timing/transition, expected safety/liveness/abort outcome, evidence and recovery criteria.
- **FR-044**: Mandatory worker scenario MUST remove approximately 10% of workers and include both dispersed sufficient-domain capacity and concentrated insufficient-domain capacity variants.
- **FR-045**: Worker loss MUST not change fixed tickets, post-freeze membership, device weights or `pi_d`; only the predeclared complete/freeze/abort policy applies.
- **FR-046**: Mandatory validator scenarios MUST include crash/restart, duplicate/reordered/replayed messages, proposer failure and up to `f` Byzantine equivocation attempts.
- **FR-047**: Mandatory storage scenarios MUST include peer loss before/after AC, unavailable required shard and recovery/retention verification.
- **FR-048**: Mandatory regional scenarios MUST include high delay/loss and partition within/beyond liveness assumptions.
- **FR-049**: Mandatory P2P scenario MUST include initial seed loss with complete and incomplete remaining piece unions.
- **FR-050**: Mandatory identity scenario MUST include key rotation/revocation and historical verification.
- **FR-051**: Within declared assumptions, the system MUST retain safety and meet the predeclared liveness result; outside assumptions it MUST abort/fail closed without conflicting QC/ApplyQC/current checkpoint.
- **FR-052**: Crash/restart tests MUST cover vote persistence, commitment/AC, certificate/QC, optional residual, artifact and current-pointer boundaries.
- **FR-053**: Rollback MUST stop future work/services while preserving immutable certified history, evidence and last valid current checkpoint.
- **FR-054**: `PilotResult` MUST contain definition/prerequisite/evidence roots, inventory/waves/rounds, gate table, measured quality/efficiency/resilience, incidents, limitations and decision `GO`, `NO_GO` or `INCONCLUSIVE`.
- **FR-055**: Final decision MUST be deterministic: GO requires every mandatory gate and evidence item; a failed gate yields NO_GO; unverifiable mandatory evidence yields INCONCLUSIVE.
- **FR-056**: `PilotResultQC` MUST require `2f_p+1` unique evaluator signatures and bind the exact result body.
- **FR-057**: Operator commentary cannot override the decision; any subsequent broader deployment requires a new specification based on the certified result.

### Non-Functional Requirements

- **NFR-001**: Provisioning/recovery/verification workflows are idempotent, bounded and documented for operators.
- **NFR-002**: No secret/private key/restricted model or private data is committed to repository, images, logs or public evidence.
- **NFR-003**: Protocol safety takes precedence over availability/utilization; uncertain identity, parentage, arithmetic or quorum fails closed.
- **NFR-004**: Target pilot evidence is sufficient for an independent reviewer to reproduce deterministic decisions and verify every finalized certificate/checkpoint.
- **NFR-005**: The pilot does not claim permissionless security, universal poisoning resistance or performance/quality beyond the exact tested definition.
- **NFR-006**: All measured targets remain labeled with their exact hardware/network/workload/profile context.

### Key Entities

- **PilotDefinition / PilotDefinitionQC**: immutable prerequisite, topology, workload, rollout, chaos and gate contract.
- **NodeEnrollment / PilotInventory / AdmissionEvidence**: exact permissioned role and compatibility state.
- **WavePlan / WavePromotionRecord**: staged scope, prerequisites, result and rollback decision.
- **DeploymentManifest / ImageProvenance / SecretPolicy**: reproducible supply-chain and operational state.
- **PilotRoundEvidence / IncidentRecord / ChaosResult**: certified protocol run and fault-campaign evidence.
- **PilotEvidenceManifest**: complete content-addressed evidence graph.
- **PilotResult / PilotResultQC**: deterministic final gate table and decision.

## Success Criteria

- **SC-001**: No remote task executes without exact compatible feature-010 `BenchmarkResultQC(GO)` and `PilotDefinitionQC`.
- **SC-002**: Idempotent deployment admits only correctly scoped, pinned and compatible nodes; secrets/supply-chain scans pass.
- **SC-003**: Target wave operates 20–50 workers across 3–5 regions with valid `3f+1`/`2f+1` sets and full certificate chain.
- **SC-004**: Honest validators agree exactly on all finalized roots/checkpoints; hierarchy matches flat oracle and only ApplyQC advances current state.
- **SC-005**: Mandatory 10% worker, validator, storage, region, P2P and identity scenarios produce their exact safe complete-or-abort outcomes.
- **SC-006**: Initial seed loss succeeds with a complete remaining union and fails diagnostically otherwise.
- **SC-007**: Dashboards/runbooks/alerts and offline evidence verifier cover all mandatory operational and protocol states.
- **SC-008**: Recovery/rollback does not double-vote/apply, lose required evidence or rewrite certified history.
- **SC-009**: Sustained-run quality/efficiency/resilience gates meet the frozen pilot definition.
- **SC-010**: Independent evaluators produce one reproducible `PilotResultQC`; GO exists only if every mandatory gate passes.

## Assumptions

- Permissioned participants, operators and review/evaluator validator sets are available across multiple administrative/network failure domains.
- Exact cloud/on-prem/volunteer hosts and overlay technology are selected through implementation ADRs before `PilotDefinitionQC`.
- Required model/data licenses allow the declared regional access/distribution policy.
- Feature-010 GO is narrow and compatibility-checked; it does not guarantee pilot success.

## Out of Scope

- Public/permissionless enrollment, Sybil resistance, staking or economics.
- Automatic architecture/protocol changes during the pilot.
- Adaptive/stale training fallback.
- General production service/SLA or deployment beyond the target 20–50-worker experiment.
- Claims beyond the exact certified pilot definition and evidence.
