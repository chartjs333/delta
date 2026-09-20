# Feature Specification: Permissioned Multi-Region Pilot

**Feature branch**: `feature/overnight-010-011-requalification`
**Reconciled**: 2026-09-20
**Status**: `BLOCKED_ON_FEATURE010_GO`
**Current-lineage base**: `7a9faf852e0ccae4d25fdc363fbf39ecf1719341`
**Formal semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Authority and admission rule

This directory is the proposed current-lineage SpecKit authority for Feature 011
and becomes current-main authority only after review and merge. The earlier
`011-multiregion-pilot@72601567a278f221efcdc381432d5c8ae1735865`
specification is a design input from an older lineage, not a deployment authority.

No remote provisioning, enrollment, training, fault injection, or pilot execution
may begin until both prerequisites verify on the exact candidate:

1. the accepted `FormalVerificationReport(GO)` and formal semantics ID; and
2. a compatible Feature 010 `BenchmarkResultQC(decision=GO)` bound to a published
   `FEATURE010_GO_CHECKPOINT_SHA`.

The second prerequisite is absent. Feature 011 has zero provisioning runs, zero
pilot runs, and no `PilotDefinitionQC` or `PilotResultQC`.

## Pilot scope

The target pilot is a permissioned deployment of 20–50 admitted workers across
3–5 real regions. It uses one or more `3f+1` validator/committee sets with at least
an `f=1` four-validator profile and includes the full accepted lifecycle:

```text
fixed domain-pure tickets
→ commitments and availability certificates
→ ISC → seed/EC → APC
→ ParameterShardQC → AggregateRootQC → ApplyQC
→ compare-and-set current checkpoint
→ certified P2P distribution
```

The pilot validates an existing architecture. It may not add a central authority,
adaptive `H`, stale updates, floating-point consensus accumulation, post-freeze
membership rewrite, implicit domain-weight renormalization, manual QC/current
override, or a new terminal behavior.

## PilotDefinition requirements

Before Wave 0, an immutable `PilotDefinitionQC` with `2f_p+1` signatures from a
declared `3f_p+1` review set must bind:

- exact Formal and Feature 010 prerequisite roots and compatibility window;
- 20–50 worker identities, 3–5 real regions, role placement, administrative and
  network failure domains, and every validator/storage/P2P set;
- model/mode/base/tokenizer/schema, licensed dataset/domain policy, immutable
  tickets, `B/H`, `pi_d`, arithmetic, certificate, robust, and apply profiles;
- approved `embedded-ffm` or `isolated-sidecar` profile, ABI and separate
  Java/native/Python image/build IDs;
- signed OCI digests, source revisions, locks, SBOMs, vulnerability scans, and
  provenance;
- private/controlled overlay, endpoint/reachability policy, time source/skew,
  observability, evidence, retention, and secret policies;
- TLS/signing identity enrollment, validity, rotation/revocation, and deny-by-
  default role/project/region/round authorization;
- rollout waves, chaos schedule, expected complete/abort outcomes, rollback,
  metrics, thresholds, missing-evidence policy, and deterministic decision.

A concrete PKI/mTLS and deployment/network design must be selected by approved ADRs
and the PilotDefinition. Local development certificates, cloud account presence,
or untracked files cannot supply this authority.

## Required rollout waves

1. **Wave 0 — offline deployment qualification**: verify all images, identities,
   configs, secrets policy, network/time policy, and idempotent lifecycle without
   remote training.
2. **Wave 1 — four-validator canary**: deploy `f=1`, storage/P2P peers, and a small
   worker subset across at least two real regions; complete one certified round and
   restart/replay matrix.
3. **Wave 2 — regional hierarchy canary**: use at least three real regions,
   regional/parameter committees, exact flat/hierarchy comparison, and certified
   P2P catch-up/seed loss.
4. **Wave 3 — target pilot**: admit the signed 20–50-worker inventory across 3–5
   regions and run the frozen workload for its declared duration.
5. **Wave 4 — controlled fault campaign**: exercise dispersed and concentrated
   approximately 10% worker loss, validator, storage, region, P2P, key, evidence,
   and emergency-stop faults.
6. **Wave 5 — sustained result**: recover/restart/rollback, seal evidence, evaluate
   all gates, and obtain the signed pilot decision.

Promotion is sequential. A narrative or operator approval cannot waive a failed or
missing mandatory gate.

## Deployment and identity requirements

- All remote endpoints require authenticated encrypted transport. Node enrollment
  binds logical ID, role, project/region scope, TLS identity, signing keys,
  validity, rotation/revocation, and hardware/software fingerprint.
- TLS, signing, cloud, model, and dataset credentials are externally injected,
  least-privilege, rotatable, and absent from Git, images, browser storage, logs,
  and public evidence.
- Provisioning is idempotent for validate/dry-run/apply/reapply/restart/upgrade/
  rollback/uninstall and preserves native WAL/snapshot plus Java-owned
  content-addressed-storage (CAS) I/O. Native C++ alone owns the consensus
  current-pointer compare-and-set transition.
- Java/Netty owns transport/TLS/backpressure; only the native single-writer runtime
  mutates consensus state; Python workers own local training and never hold
  validator or current-state authority.
- Native replay completes before Java admits new protocol traffic. Embedded and
  sidecar crash-containment claims remain distinct.

## Mandatory operational gates

- full ISC-through-ApplyQC lineage, persist-before-expose, exact honest state/effect
  roots, and exact hierarchical-versus-flat integer equality;
- restart at durable vote, certificate, artifact, WAL, snapshot, and current-pointer
  boundaries without double-vote, double-apply, or history reinterpretation;
- certified P2P reconstruction after initial seed loss and diagnostic failure for
  an incomplete remaining piece union;
- dispersed worker loss completes only with frozen sufficient domain capacity;
  concentrated insufficient capacity aborts without synthetic work or `pi_d`
  rewrite;
- within-threshold validator/region faults preserve safety and declared liveness;
  beyond-threshold/quorum/availability failures preserve the parent current and
  create no descendant QC;
- key rotation/revocation, image/config mismatch, clock drift, TLS failure,
  evidence outage, and emergency stop all fail closed;
- dashboards are reconstructible views; immutable signed/content-addressed records
  remain the evidence authority.

## Decision rule

`PilotResultQC(decision=GO)` requires all waves, every mandatory safety, quality,
efficiency, resilience, security, recovery, and evidence gate, offline verification,
and `2f_p+1` evaluator signatures over the exact result body. A failed mandatory
gate yields `NO_GO`. Missing or unverifiable mandatory evidence yields
`INCONCLUSIVE` or `NO_GO` according to the frozen policy, never GO.

## Atomic acceptance scenarios

These existing scenario identities remain unexecuted on the current lineage.

### US1 — Verify prerequisite and freeze definition

1. **Given** compatible Feature 010 GO, **When** verification runs, **Then** exact
   definition/result/evidence roots and signatures are accepted and recorded.
2. **Given** NO_GO, missing evidence, mismatched identity, stale window or weak
   quorum, **When** verification runs, **Then** remote deployment is blocked.
3. **Given** a complete definition, **When** `2f_p+1` reviewers sign, **Then** one
   immutable PilotDefinitionQC finalizes.
4. **Given** a post-QC material change, **When** rollout is attempted, **Then** a new
   definition/QC is required.

### US2 — Admit exact permissioned roles

1. **Given** signed pinned images/config and enrolled identity, **When** provisioned,
   **Then** deployed bytes match expected digest/SBOM/provenance.
2. **Given** wrong/revoked/expired identity or role, **When** it connects, **Then**
   authorization fails before payload use.
3. **Given** incompatible hardware/model/arithmetic/time/network, **When** preflight
   runs, **Then** admission fails with a stable reason.
4. **Given** interrupted provisioning, **When** automation repeats, **Then** it
   converges without duplicate identities, votes, volumes, services or secrets.
5. **Given** real credentials, **When** deployment occurs, **Then** they stay outside
   Git/images and are redacted from logs/evidence.

### US3 — Complete certified rounds

1. **Given** an active wave, **When** tickets issue, **Then** each remains domain-
   pure with fixed data, `B/H`, parent and profile.
2. **Given** completed tickets, **When** commitments/ACs finalize, **Then** ISC
   freezes exact available tuples before seed generation.
3. **Given** ISC/EC/APC, **When** committees execute, **Then** checked results bind
   one view and match the flat oracle under frozen verification policy.
4. **Given** complete ParameterShardQCs, **When** aggregate/apply executes, **Then**
   validators emit identical next checkpoint/state and one ApplyQC.
5. **Given** ApplyQC, **When** P2P publishes/fetches, **Then** only exact certified
   bytes are distributed.
6. **Given** any parent/arithmetic/coverage mismatch, **When** processed, **Then**
   the round rejects/aborts with parent current unchanged.

### US4 — Operate with auditable controls

1. **Given** an active round, **When** telemetry collects, **Then** all ticket,
   certificate, arithmetic, bytes/time, P2P and resource stages are covered.
2. **Given** an alert, **When** inspected, **Then** it links immutable IDs and a
   runbook action.
3. **Given** an emergency, **When** authenticated stop finalizes, **Then** new work
   stops without unsigned/current override.
4. **Given** evidence export, **When** verified offline, **Then** hashes/signatures/
   QCs and redaction pass.
5. **Given** evidence pressure, **When** limits approach, **Then** promotion follows
   fail-safe policy rather than dropping mandatory evidence.

### US5 — Execute the fault campaign

1. **Given** about 10% dispersed worker loss with sufficient domain capacity,
   **When** freeze resolves, **Then** only certified inputs and unchanged `pi_d` are
   used.
2. **Given** concentrated insufficient capacity, **When** deadline resolves,
   **Then** the round aborts without adaptive work or renormalization.
3. **Given** up to `f` Byzantine/crashed validators and eventual synchrony, **When**
   messages conflict/replay, **Then** safety and frozen liveness outcomes hold.
4. **Given** insufficient quorum or required shards, **When** deadline resolves,
   **Then** no descendant QC/ApplyQC/current is fabricated.
5. **Given** initial seed loss after replication, **When** a late worker catches up,
   **Then** it reconstructs exact certified bytes.
6. **Given** signer rotation/revocation, **When** new operations occur, **Then**
   epoch policy applies while old evidence remains verifiable.

### US6 — Recover without rewriting history

1. **Given** persisted state, **When** services restart, **Then** they cannot double-
   vote, double-commit residuals or apply twice.
2. **Given** an incomplete wave, **When** rollback runs, **Then** services stop
   idempotently while certified state/evidence remains.
3. **Given** an upgrade, **When** deployed, **Then** it occurs only between rounds/
   waves under a new signed epoch.
4. **Given** version rollback, **When** prior software is selected for future work,
   **Then** old certified bytes retain their original interpretation.

### US7 — Produce the pilot decision

1. **Given** complete verified evidence and all gates passing, **When** `2f_p+1`
   evaluators sign, **Then** PilotResultQC GO finalizes.
2. **Given** a failed mandatory gate, **When** decision runs, **Then** it returns
   NO_GO with exact failed gates.
3. **Given** unavailable/unverifiable mandatory evidence, **When** decision runs,
   **Then** it returns the frozen INCONCLUSIVE/NO_GO outcome, never GO.
4. **Given** operator commentary, **When** finalizing, **Then** it cannot override
   the deterministic result.

## Numbered requirements

### Prerequisite and governance

- **FR-001**: Remote provisioning/training MUST be blocked until compatible Feature
  010 ResultQC GO verifies.
- **FR-002**: Compatibility MUST bind benchmark roots, source/tree, protocol,
  model/data/ticket/arithmetic profiles and validity window.
- **FR-003**: PilotDefinition MUST bind inventory/topology, workload, role sets,
  images, network/time/secrets, waves, chaos, metrics, rollback and decision.
- **FR-004**: PilotDefinitionQC MUST require `2f_p+1` signatures from a declared
  `3f_p+1` review set.
- **FR-005**: A material post-QC change MUST require a new definition/QC and wave
  boundary.
- **FR-006**: Deployment MUST be permissioned; anonymous participation and
  unsanctioned role sharing are forbidden.
- **FR-007**: Every wave MUST freeze preconditions, scope/duration, promotion and
  rollback; failed gates are not waivable.

### Deployment, identity and supply chain

- **FR-008**: Pinned OCI identities MUST exist for every pilot role.
- **FR-009**: Every artifact MUST bind digest, source, locks, SBOM, scan, signature
  and provenance.
- **FR-010**: Provisioning MUST be idempotent across validate through uninstall and
  preserve required durable state.
- **FR-011**: Enrollment MUST bind logical ID, roles/scopes, TLS/signing identities,
  validity/revocation and hardware/software fingerprint.
- **FR-012**: Authentication MUST be verified and authorization deny-by-default by
  role/project/region/round/operation.
- **FR-013**: Remote endpoints MUST require authenticated encrypted transport.
- **FR-014**: Secrets MUST be external, least-privilege, rotatable and absent from
  Git/images/logs/public evidence.
- **FR-015**: Networking MUST use an approved private/controlled overlay and
  reachability policy.
- **FR-016**: Every role MUST enforce a monitored time source/skew limit and
  fail-safe behavior.
- **FR-017**: Admission MUST verify identity, image/config/protocol, clock, region,
  network, storage, hardware and scientific profiles.
- **FR-018**: Revoked/quarantined/incompatible nodes MUST leave new ticket/vote/
  attestation/advertisement sets under deterministic epoch policy.

### Protocol operation

- **FR-019**: Target wave MUST have 20–50 admitted workers across 3–5 regions.
- **FR-020**: Each committee MUST satisfy exact `3f+1`/`2f+1`; primary pilot MUST
  support at least `f=1`.
- **FR-021**: Placement MUST document independent and correlated failure domains.
- **FR-022**: Work units MUST be immutable domain-pure tickets; speed affects only
  lease capacity.
- **FR-023**: Only complete `A_j=H` tickets may commit; partial/stale/adaptive work
  is forbidden.
- **FR-024**: Commitments/ACs MUST bind exact shards/epochs and availability quorum.
- **FR-025**: Seed MUST follow ISC; EC/APC/committees MUST verify exact parents.
- **FR-026**: Robust/reduce/apply arithmetic MUST use frozen canonical checked
  integer/rational profiles.
- **FR-027**: Hierarchy MUST equal the flat integer oracle under the frozen policy.
- **FR-028**: AggregateRootQC MUST cover required domain×parameter shards exactly
  once and reject mixed views.
- **FR-029**: Apply validators MUST emit identical artifacts and one ApplyQC; no
  single service can advance current state.
- **FR-030**: Current pointer MUST advance only by native valid-ApplyQC compare-and-
  set and remain unchanged on failure.
- **FR-031**: Distribution MUST hard-deny uncertified/local/partial media.
- **FR-032**: P2P consumers MUST verify manifest, certificate, pieces and full
  object before use/seeding.
- **FR-033**: Mutating commands MUST be idempotent, replay-protected and restart-
  safe.

### Observability and evidence

- **FR-034**: Telemetry MUST cover inventory, tickets, every certificate/QC,
  arithmetic headroom, bytes/latency, resources, P2P, quality and incidents.
- **FR-035**: Dashboards MUST be reconstructible views; signed/content-addressed
  records remain authority.
- **FR-036**: Versioned alerts MUST cover quorum, equivocation, parents, arithmetic,
  storage, clock, image/config, domain, apply, P2P and evidence health.
- **FR-037**: Authenticated controls MUST support status, stop, quarantine,
  revoke/rotate, verify, safe retry and rollback without unsigned promotion.
- **FR-038**: Emergency stop MUST block new work without rewriting finalized state.
- **FR-039**: Runbooks MUST cover every mandatory fault/incident.
- **FR-040**: Evidence export MUST bind supply chain, definitions/inventory,
  certificates, rounds, traces, metrics, quality, incidents and decision inputs.
- **FR-041**: Offline verification MUST validate hashes, signatures, QCs,
  compatibility, calculations and redaction without live services.
- **FR-042**: Mandatory evidence loss/corruption MUST block promotion/GO.

### Faults, recovery and decision

- **FR-043**: Chaos scenarios MUST be frozen with target, timing, expected outcome,
  evidence and recovery criteria.
- **FR-044**: Worker loss MUST cover dispersed sufficient and concentrated
  insufficient variants near 10%.
- **FR-045**: Loss MUST NOT alter tickets, membership, weights or `pi_d`.
- **FR-046**: Validator faults MUST cover crash/restart, replay/reorder, proposer
  loss and up-to-`f` equivocation.
- **FR-047**: Storage faults MUST cover loss before/after AC, unavailable shards and
  recovery/retention.
- **FR-048**: Regional faults MUST cover delay/loss and partitions within/beyond
  liveness assumptions.
- **FR-049**: P2P faults MUST cover seed loss with complete/incomplete remaining
  unions.
- **FR-050**: Identity faults MUST cover rotation/revocation and historical
  verification.
- **FR-051**: Within assumptions safety/liveness MUST hold; beyond them the system
  MUST fail closed without conflicting QC/current.
- **FR-052**: Crash tests MUST cover votes, commitments/AC, QCs, residuals,
  artifacts and current-pointer boundaries.
- **FR-053**: Rollback MUST preserve certified history, evidence and last current.
- **FR-054**: PilotResult MUST bind prerequisite/evidence roots, inventories, waves,
  gates, measured results, incidents, limitations and decision.
- **FR-055**: Decision MUST be deterministic: all-pass GO, failed-gate NO_GO,
  frozen-policy missing-evidence outcome never GO.
- **FR-056**: PilotResultQC MUST require `2f_p+1` unique signatures over exact bytes.
- **FR-057**: Commentary cannot override; broader deployment needs a new spec.

## Numbered success criteria

- **SC-001**: No remote task runs without exact Feature 010 GO and PilotDefinitionQC.
- **SC-002**: Idempotent deployment admits only pinned compatible identities and
  passes secret/supply-chain scans.
- **SC-003**: Target operates 20–50 workers/3–5 regions with valid committees and
  complete lineage.
- **SC-004**: Honest roots agree, hierarchy equals flat and only ApplyQC advances
  current.
- **SC-005**: Worker/validator/storage/region/P2P/identity faults produce exact safe
  outcomes.
- **SC-006**: Seed loss succeeds only for a complete verified remaining union.
- **SC-007**: Dashboards/runbooks/alerts and offline verifier cover mandatory state.
- **SC-008**: Recovery/rollback never double-votes/applies or rewrites history.
- **SC-009**: Sustained quality/efficiency/resilience pass the frozen definition.
- **SC-010**: Evaluators reproduce one PilotResultQC; GO requires every gate.

## Current external blockers

- no Feature 010 GO checkpoint or BenchmarkResultQC;
- no approved PilotDefinition/reviewer quorum;
- no approved 20–50-worker/3–5-region inventory or real endpoint credentials;
- no approved deployment/network ADRs, private overlay, PKI/mTLS identity inventory,
  signed role images, or pilot secret injection;
- no licensed regional model/data distribution decision;
- no pilot evaluator quorum or real operations team/failure-domain evidence.

The honest outcome remains `WORKING_VERSION_READY` for the local single-host
deliverable and `BLOCKED_ON_FEATURE010_GO` for this feature.
