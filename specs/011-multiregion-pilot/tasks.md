# Tasks: Permissioned Multi-Region DeltaReduce v1 Pilot

**Input**: `spec.md`, `plan.md`, Constitution 2.1.0, completed features `001–010`
and an exact compatible Feature 010 result.

All tasks remain open. Reconciliation of this SpecKit does not complete a pilot
implementation, external appointment, deployment or run.

## Phase 0: Mandatory STOP prerequisite

- [ ] T000 Implement/execute prerequisite verification for exact
  `BenchmarkResultQC(decision=GO)`, definition/result/evidence/source/protocol/
  model/data/profile compatibility and signatures; block every remote task T014+
  on any failure.
- [ ] T001 Search authoritative deployment/config for a central coordinator,
  adaptive/stale work, floating consensus reduce, unsigned current-pointer path or
  certificate override; record zero-tolerance evidence.

## Phase 1: Pilot contracts and ADRs

- [ ] T002 Define `PilotDefinition`, prerequisite compatibility, inventory, wave,
  incident, chaos, evidence and result models.
- [ ] T003 Define canonical serialization, review/evaluator validator sets and
  PilotDefinitionQC/PilotResultQC.
- [ ] T004 Create pilot golden fixtures.
- [ ] T005 Add definition/result/prerequisite contract tests.
- [ ] T006 Select and approve the deployment orchestrator ADR.
- [ ] T007 Select and approve the private overlay/relay/reachability ADR.
- [ ] T008 Define failure-domain/role-colocation constraints and validator/storage
  placement policy.
- [ ] T009 Freeze exact workload, model/data/license, fixed ticket/domain profiles,
  validator/storage/P2P topology, waves, chaos, gates and decision policy before
  remote launch.
- [ ] T010 Finalize `PilotDefinitionQC` and store its prerequisite linkage.

## Phase 2: Reproducible deployment foundation

- [ ] T011 Create minimal pinned OCI definitions for worker, validator,
  storage/availability, regional/global reduce, apply, P2P and observability roles.
- [ ] T012 Implement build, dependency lock, SBOM, vulnerability scan, signing and
  provenance workflow.
- [ ] T013 Create idempotent service templates and durable-volume/backup policy.
- [ ] T014 Create remote provisioning roles and inventory schema.
- [ ] T015 Implement external secret injection, permission checks,
  rotation/revocation and redaction.
- [ ] T016 Implement private overlay/relay/reachability automation.
- [ ] T017 Implement time synchronization/skew monitoring and fail-safe policy.
- [ ] T018 Add dry-run/apply/reapply/restart/upgrade/rollback/uninstall tests.
- [ ] T019 Add image/config/provenance and secret-leak scans.

## Phase 3: Identity, inventory, preflight and admission

- [ ] T020 Implement node enrollment/trust/role/scope/epoch models and operator
  workflows.
- [ ] T021 Implement remote preflight checks.
- [ ] T022 Implement the signed inventory builder.
- [ ] T023 Implement admission for identity, image/config/protocol, clock, region,
  network, storage, hardware/memory, model and fixed-point/QLoRA compatibility.
- [ ] T024 Implement revocation/quarantine removal from tickets/votes/attestations/
  peer advertisements.
- [ ] T025 Implement continuous image/config/time/eligibility drift monitoring.
- [ ] T026 Add unknown/revoked/wrong-role/image/config/memory/network/storage/time
  test matrix.
- [ ] T027 Obtain and sign canary and target inventories, including 20–50 workers
  across 3–5 regions.

## Phase 4: Observability, evidence and operator controls

- [ ] T028 Deploy metrics/log/audit collectors and immutable evidence export.
- [ ] T029 Add versioned dashboards/alerts for protocol, quorum, arithmetic, P2P,
  resource, drift and evidence-health states.
- [ ] T030 Implement evidence manifest/sealing/offline verifier.
- [ ] T031 Implement authenticated status/pause/stop/quarantine/revoke/retry/
  rollback controls.
- [ ] T032 Implement deterministic emergency stop that blocks new ticketing without
  rewriting finalized state.
- [ ] T033 Write runbooks for every mandatory failure/incident.
- [ ] T034 Add dashboard-loss, evidence-pressure/outage, redaction and offline-
  rebuild tests.

## Phase 5: Wave 0 — Deployment qualification

- [ ] T035 Verify all image/config/SBOM/provenance/signature/secret/network/time
  artifacts offline.
- [ ] T036 Exercise provisioning and recovery in non-remote/local staging.
- [ ] T037 Verify no remote training endpoint can start before T000, T010 and Wave
  0 promotion.
- [ ] T038 Seal Wave 0 evidence and finalize its promotion record.

## Phase 6: Wave 1 — Four-validator canary

- [ ] T039 Deploy a minimum `f=1` four-validator set, storage/P2P peers and a small
  worker subset across at least two real regions.
- [ ] T040 Execute one complete fixed-ticket round from RoundConfigQC through
  ApplyQC/P2P.
- [ ] T041 Verify exact state/certificate/checkpoint hashes across honest nodes and
  the flat oracle.
- [ ] T042 Exercise restart at vote, certificate, artifact and current-pointer
  boundaries.
- [ ] T043 Verify forbidden local/partial distribution and certification-downgrade
  rejection.
- [ ] T044 Seal canary evidence and finalize Wave 1 promotion or stop.

## Phase 7: Wave 2 — Regional hierarchy canary

- [ ] T045 Deploy at least three real regions with regional/global parameter
  committees and declared failure domains.
- [ ] T046 Execute a hierarchical fixed-ticket round and compare exact integer
  outputs against the flat oracle.
- [ ] T047 Verify full C/AC/ISC/seed/EC/APC/shard/AggregateRootQC/ApplyQC lineage
  offline.
- [ ] T048 Verify P2P catch-up and initial-seed loss after sufficient replication.
- [ ] T049 Seal Wave 2 evidence and finalize promotion or stop.

## Phase 8: Wave 3 — Target 20–50-worker pilot

- [ ] T050 Admit the signed target inventory across 3–5 regions without changing
  PilotDefinition.
- [ ] T051 Execute the preregistered sustained fixed-ticket workload for the
  declared round/token duration.
- [ ] T052 Continuously verify domain ticket quotas, complete `A_j=H`, certificate
  parentage, accumulator headroom and apply-hash agreement.
- [ ] T053 Measure quality, wall-clock, GPU utilization, phase/bytes/latency, P2P
  and operational metrics.
- [ ] T054 Seal target-run evidence and assess promotion to the fault campaign.

## Phase 9: Wave 4 — Controlled fault campaign

- [ ] T055 Implement deterministic chaos controller/traces.
- [ ] T056 Execute dispersed approximately 10% worker loss with sufficient per-
  domain capacity.
- [ ] T057 Execute concentrated worker loss causing insufficient mandatory-domain
  capacity and verify safe abort.
- [ ] T058 Execute validator proposer/member crash/restart, replay/reordering and
  up-to-`f` equivocation attempts.
- [ ] T059 Execute insufficient validator quorum and verify no descendant QC/current
  mutation.
- [ ] T060 Execute storage loss before/after AC and unavailable required-shard
  scenarios.
- [ ] T061 Execute regional latency/loss and within/beyond-assumption partitions.
- [ ] T062 Execute P2P initial-seed loss with complete/incomplete remaining piece
  unions.
- [ ] T063 Execute key rotation/revocation and historical-verification scenario.
- [ ] T064 Execute evidence collector/storage pressure/outage and emergency-stop
  scenarios.
- [ ] T065 Verify every scenario's exact safety/liveness/abort/recovery result and
  seal evidence.

## Phase 10: Wave 5 — Recovery, sustained result and decision

- [ ] T066 Execute a full service/host/region restart and idempotent recovery drill.
- [ ] T067 Execute rollback/uninstall while preserving certified history, evidence
  and current checkpoint.
- [ ] T068 Run final preregistered quality/efficiency/resilience/operations
  analyzers.
- [ ] T069 Build deterministic PilotResult gate table and
  GO/NO_GO/INCONCLUSIVE decision.
- [ ] T070 Obtain `2f_p+1` evaluator signatures and finalize PilotResultQC.
- [ ] T071 Verify complete pilot evidence/result offline from a clean verifier
  environment.

## Final phase

- [ ] T072 Implement the pilot validate/preflight/provision/status/stop/chaos/
  evidence/verify/decision CLI.
- [ ] T073 Publish operator/deployment/protocol/evidence documentation and a
  sanitized final report.
- [ ] T074 Run SpecKit cross-artifact analysis and resolve every finding.
- [ ] T075 Run full quality gate, secret/license/supply-chain scan and final
  Constitution Check.

## Dependencies

- T000–T001 are hard STOPs for remote work; T002–T013 may prepare reviewed local
  contracts, ADRs and artifacts while T000 is false.
- Remote tasks T014+ require both T000 GO and T010 PilotDefinitionQC.
- T002–T010 block deployment identity; T011–T019 block remote provisioning.
- T020–T027 block active inventory/admission; T028–T034 block wave promotion.
- Waves T035–T071 are sequential and no promotion gate may be skipped.
- HR011-001–008 are local implementation/qualification work; real canary/fault/
  decision obligations HR011-009–016 are remote work and require T000 GO, T010
  PilotDefinitionQC and their corresponding sequential wave promotion.
- T072–T075 cannot override a failed wave or mandatory gate.

## Exit gate

All required waves and tasks complete under the frozen definition; target
20–50-worker/3–5-region evidence verifies; exact BFT/fixed-point/certificate/
apply/P2P invariants hold; the fault campaign produces expected safe outcomes;
and PilotResultQC is finalized with the deterministic decision.
