# Hybrid Runtime Tasks: 011 Multi-Region Pilot

## Definition and supply chain

- [ ] **HR011-001** Bind PilotDefinition to the exact approved embedded/sidecar profile, ABI, formal semantics and Java/C++/Python build IDs.
- [ ] **HR011-002** Build, sign and attest separate Java node, native runtime/library and Python worker artifacts with SBOMs.
- [ ] **HR011-003** Define external secrets, role separation and durable-volume ownership for Java/native/Python units.
- [ ] **HR011-004** Add startup/admission rejection for ABI/schema/formal-semantics/image/config mismatch.

## Provisioning and recovery

- [ ] **HR011-005** Implement idempotent provisioning for the approved hybrid node process layout.
- [ ] **HR011-006** Verify native WAL/snapshot recovery completes before Java protocol admission.
- [ ] **HR011-007** Implement bounded FFM or IPC queues, health checks and backpressure alerts.
- [ ] **HR011-008** Add separate Java/native/Python metrics, logs and evidence identities.

## Canary and fault campaign

- [ ] **HR011-009** Run four-validator hybrid canary with exact trace/state/effect agreement.
- [ ] **HR011-010** Execute Java crash, native crash, WAL corruption/loss, queue saturation and rolling mismatch scenarios.
- [ ] **HR011-011** Execute Netty leak/stall, stale timer/duplicate delivery and P2P seed-loss scenarios.
- [ ] **HR011-012** Execute Python OOM/partial-ticket/base-cache and worker-loss scenarios.
- [ ] **HR011-013** Verify rollback/upgrade only between rounds and no certified history reinterpretation.

## Decision

- [ ] **HR011-014** Include runtime-profile compliance and unresolved native/JVM discrepancy as mandatory pilot gates.
- [ ] **HR011-015** Reconstruct all mandatory hybrid traces and evidence offline.
- [ ] **HR011-016** Permit PilotResultQC(GO) only for the exact benchmark-approved runtime profile.
