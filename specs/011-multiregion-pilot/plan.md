# Implementation Plan: Permissioned Multi-Region Pilot

**Current result**: `BLOCKED_ON_FEATURE010_GO`
**Formal impact**: `NONE`

## Constitution checks

**Pre-implementation check — PASS for reconciliation scope.** The accepted Formal
GO verifies, Feature 010 GO is explicitly absent, and this plan permits no remote
provisioning, execution or semantic change.

**Final candidate check — PASS/BLOCKED.** The candidate changes only SpecKit and
the runtime map, leaves every protected semantic/runtime path untouched, preserves
native current-pointer authority, and keeps all T000–T075/HR011-001–016 pilot work
open. A sealed verifier run after commit is mandatory before handoff.

## Sequence

1. Verify exact compatible Formal GO and Feature 010 GO checkpoint/ResultQC.
2. Approve deployment and private-network/PKI ADRs.
3. Freeze and quorum-sign `PilotDefinition`, inventories, workload, topology,
   runtime profile, waves, chaos, evidence, and decision policy.
4. Build, scan, sign, attest, and publish separate Java node, native runtime, and
   Python worker images with locks/SBOM/provenance.
5. Establish external TLS/signing/model/data secrets, private overlay, time/skew,
   identity enrollment, deny-by-default authorization, and durable volume policy.
6. Qualify idempotent provisioning, recovery, rollback, uninstall, observability,
   evidence export, and offline verification in Wave 0.
7. Execute Waves 1–5 in order: four-validator canary, at-least-three-region
   hierarchy canary, target 20–50-worker run, complete fault campaign, and sustained
   decision.
8. Seal all evidence and obtain `PilotResultQC` only from the frozen deterministic
   decision and real evaluator quorum.

## Current STOP

Step 1 fails because Feature 010 has no GO checkpoint. Therefore no remote
provisioning, TLS enrollment, cloud mutation, model/data transfer, or pilot command
was attempted. Local NICs, VM adapters, a VPN adapter label, or a generic cloud
credential are not a multi-region inventory.

## Test strategy after admission

- prerequisite GO/mismatch/stale/missing-signature matrix;
- signed definition/inventory/image/config mutation matrix;
- TLS identity, revocation, role/scope, clock, hardware, storage, network, and
  secret admission matrix;
- idempotent provision/restart/rollback/uninstall;
- four-validator and three-region exact canaries;
- full certificate/current/P2P evidence reconstruction;
- worker/validator/storage/region/P2P/key/evidence fault campaign;
- deterministic GO/NO_GO/INCONCLUSIVE and offline evidence verification.

## Exit gate

All waves and mandatory tasks complete on the exact frozen definition; all honest
roots agree, recovery preserves certified history, real fault outcomes match their
preregistered complete-or-abort result, and a quorum-certified PilotResultQC is
independently reproducible.
