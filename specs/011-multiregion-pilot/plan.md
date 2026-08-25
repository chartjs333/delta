# Implementation Plan: Permissioned Multi-Region DeltaReduce v1 Pilot

**Branch**: `011-multiregion-pilot` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Build a reproducible permissioned deployment for worker, BFT validator, storage/availability, regional/global reduce, apply, P2P and observability roles; freeze a compatible pilot definition; roll out from four-validator canary to 20–50 workers/3–5 regions; execute certified rounds and preregistered fault campaign; collect immutable evidence and finalize a quorum-certified pilot decision.

## Technical Context

- Remote deployment begins only after exact feature-010 GO verification.
- OCI images are pinned/signed with SBOM/provenance; deployment reference uses Ansible plus Compose/systemd or an ADR-approved equivalent.
- Private/controlled overlay and relays are selected through ADR; protocol endpoints use authenticated encrypted transport.
- PKI/signing keys and model/data credentials are externally managed and rotated/revoked by operator workflows.
- Durable state uses role-specific volumes/CAS/journals with backup/retention and no shared mutable coordinator database.
- Observability exports OpenTelemetry/Prometheus-compatible metrics and structured logs to immutable evidence bundles; dashboards are replaceable.
- Deployment/inventory/configuration, fault traces and evidence are canonical/content-addressed.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Replicated state | Real `3f+1` validators/committees, no central writer | Topology/round tests |
| Fixed work | Immutable domain tickets, complete `A_j=H` only | Ticket evidence |
| Integer consensus | Profile/proof roots and flat equality | Arithmetic gate |
| Certificate lineage | Full ISC→ApplyQC chain | Offline verifier |
| Plane separation | Only certified global objects in P2P | Media audit |
| Permissioned safety | Enrollment, role auth, revocation, supply chain | Admission/security matrix |
| WAN realism | Multi-region target plus controlled faults | Pilot evidence |
| Reversibility | Staged waves, stop/rollback, immutable history | Recovery drills |

**Pre-implementation result**: BLOCKED until T000 verifies a compatible `BenchmarkResultQC(GO)`. After that prerequisite, the design is constitutionally admissible.

## Architecture and Data Flow

```text
PilotDefinitionQC + compatible BenchmarkResultQC(GO)
                         │
                         ▼
        Provisioning / enrollment / preflight
                         │
   ┌───────────┬─────────┼─────────┬────────────┐
   ▼           ▼         ▼         ▼            ▼
workers   BFT validators storage  reduce/apply  P2P peers
   │           │         peers     committees      │
   └──── fixed tickets → C/AC → ISC/EC/APC ───────┘
                              │
                       shard QCs/AggregateRootQC
                              │
                            ApplyQC
                              │
                  certified checkpoint P2P
                              │
              immutable telemetry/audit/evidence
                              │
                         PilotResultQC
```

## Project Structure

```text
deploy/
  images/
  compose/
  systemd/
  ansible/
    roles/
    inventories/
  overlay/
  observability/
  evidence/
configs/pilot/
  definition.yaml
  waves/
  alerts/
  chaos/
  runbooks/
src/deltatorrent/pilot/
  prerequisite.py
  definition.py
  inventory.py
  preflight.py
  admission.py
  waves.py
  control.py
  chaos.py
  evidence.py
  decision.py
  verifier.py
  telemetry.py
src/deltatorrent/cli/pilot.py
tests/operations/test_provisioning_idempotency.py
tests/integration/test_pilot_preflight.py
tests/integration/test_pilot_canary_round.py
tests/integration/test_pilot_fault_campaign.py
tests/integration/test_pilot_recovery.py
tests/integration/test_pilot_decision.py
docs/adr/0002-pilot-deployment.md
docs/adr/0003-pilot-network.md
docs/pilot/runbook.md
```

## Implementation Sequence

1. Verify exact feature-010 GO and freeze pilot compatibility/prerequisite contract.
2. Choose deployment and private-network approaches through ADRs.
3. Build, scan, sign and publish pinned role images and deployment templates.
4. Implement external secret/identity enrollment, inventory and comprehensive remote preflight.
5. Deploy observability/evidence/control plane and validate idempotent recovery/uninstall.
6. Freeze `PilotDefinitionQC`, target inventory, waves, alerts, runbooks and chaos profiles.
7. Execute Wave 0/1 deployment and four-validator canary; stop on any safety mismatch.
8. Promote to regional hierarchy canary and target 20–50-worker wave.
9. Execute sustained fixed-ticket workload and full fault campaign.
10. Seal/verify evidence, compute gate table and finalize PilotResultQC.

## Test Strategy

- Prerequisite GO/mismatch/NO_GO/stale/missing-signature matrix.
- Definition/inventory/image/config canonical identity and mutation tests.
- Provisioning dry-run/apply/reapply/restart/upgrade/rollback/uninstall.
- Enrollment, role, revocation, clock, image/config/hardware/network/storage admission matrix.
- Four-validator and three-region exact round/certificate/apply/P2P canaries.
- Flat/hierarchy hash sampling/full policy.
- Worker/validator/storage/region/P2P/key fault campaign within/beyond assumptions.
- Emergency stop, crash at vote/artifact/current pointer and rollback drills.
- Evidence loss/mutation/redaction/offline-verification tests.
- Deterministic GO/NO_GO/INCONCLUSIVE result tests.

## Observability

Provide dashboards and alerts for inventory/admission, ticket/domain progress, C/AC/ISC/seed/EC/APC, QCs, validator quorum/equivocation, accumulator headroom, reduce/apply hash agreement, P2P pieces, bytes/latencies, GPU/resource state, quality, clock/image/config drift, evidence health and incidents. Every view links to immutable IDs and can be reconstructed from exports.

## Rollout and Rollback

Promotion is wave-gated and bounded. Emergency stop prevents new ticketing. Rollback preserves immutable CAS/journals/certificates/evidence and the last ApplyQC-certified current checkpoint, then idempotently stops or removes services. Protocol/config/image changes occur only between waves/rounds under new signed identities.

## Risks and Mitigations

- **Correlated validator failures**: placement/failure-domain review and explicit topology evidence.
- **Operational centralization**: no shared authoritative database; BFT state and certificate roots remain authoritative.
- **Secret/supply-chain compromise**: external secrets, signatures, SBOM/provenance, revocation and admission checks.
- **WAN/NAT/relay bottlenecks**: preflight, measured routes, regional placement, P2P evidence and fail-safe deadlines.
- **Storage disappears after AC**: retention monitoring, redundant attestations and mandatory failure drills.
- **Evidence outage**: redundant export/retention and promotion stop on mandatory evidence risk.
- **Manual pressure to continue**: deterministic gates and QC-bound definitions/results.

## Exit Gate

A compatible feature-010 GO and PilotDefinitionQC exist; target 20–50-worker/3–5-region waves and fault campaign complete; all honest hashes/certificates/apply states agree exactly; quality/efficiency/resilience/operations gates pass; evidence verifies offline; one `PilotResultQC` is finalized with the deterministic outcome.
