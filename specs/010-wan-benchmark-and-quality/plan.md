# Implementation Plan: Preregistered WAN, BFT Safety and Model-Quality Benchmark

**Branch**: `010-wan-benchmark-and-quality` | **Date**: 2026-08-23 | **Spec**: `spec.md`

**Authority**: Constitution 2.1.0; Feature 009 merge
`007eb08aa3aaee849128ba428274a9fbda561bf8`; inherited formal semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.

**Formal impact**: `REGRESSION_ONLY`. Benchmark governance attestations gate Feature 011 but never
participate in protocol certificate parentage or current-state application.

## Summary

Build a reproducible benchmark control plane that freezes workload/gates before execution, launches token/domain-matched reference and DeltaReduce arms, injects deterministic WAN/Byzantine/churn profiles, collects immutable evidence, computes quality/efficiency/safety gates and produces a quorum-certified GO/NO_GO result.

## Technical Context

- Benchmark orchestration is separate from training/consensus domain behavior and invokes only published interfaces.
- Definitions/results use canonical serialization and `3f_b+1` benchmark reviewer/evaluator sets.
- Reproducible Python analysis uses pinned dependencies and deterministic table/metric transformations; raw evidence remains immutable.
- Network simulator supports unprivileged deterministic mode; Linux `tc/netem` adapter is optional and must match profile semantics.
- Metrics are exported to machine-readable files/CAS; dashboards are views, not evidence authorities.
- Quality evaluators are versioned/pinned and operate on immutable model/checkpoint/evaluation inputs.
- Real-WAN variant follows only after local/emulated gates pass.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Scientific correctness | Equal token/domain exposure and downstream/post-training metrics | Quality analyzer |
| BFT determinism | Exact hash comparisons and attack corpus | Safety gate |
| Fixed work | Definition rejects adaptive/stale behavior | Schema/architecture test |
| WAN realism | Deterministic network/fault profiles plus approved real-WAN variant | Trace evidence |
| Evidence integrity | Content-addressed graph and ResultQC | Offline verifier |
| No gate waiver | Deterministic all-mandatory decision | GO/NO_GO test |

**Pre-implementation result**: PASS. No benchmark may alter protocol invariants to make targets pass.

## Architecture and Data Flow

```text
BenchmarkDefinition → review validators → BenchmarkDefinitionQC
         │
         ▼
ExperimentOrchestrator
  ├─ scientific reference arm
  ├─ flat DeltaReduce arm
  ├─ hierarchical primary arm
  ├─ QLoRA/full-model selected arm
  └─ fault/attack/seed-loss scenarios
         │
         ▼
EvidenceCollector → immutable EvidenceManifest
         │
  ┌──────┼───────────┬───────────┐
  ▼      ▼           ▼           ▼
quality safety   efficiency   resilience analyzers
  └──────┴───────────┴───────────┘
         │ deterministic gate table
         ▼
BenchmarkResult → evaluator QC → GO/NO_GO
```

## Project Structure

```text
delta-worker-python/src/deltatorrent/benchmark/
  definition.py
  preregistration.py
  review.py
  orchestrator.py
  arms.py
  reconciliation.py
  evidence.py
  quality.py
  safety.py
  efficiency.py
  resilience.py
  decision.py
  report.py
  verifier.py

delta-node-java/src/main/java/io/deltareduce/node/benchmark/
  RuntimeIdentityCollector.java
  NetworkFaultController.java
  ProcessProfileRunner.java
  EmbeddedFfmRunner.java
  SidecarRunner.java
  NettyMetricsCollector.java
  BenchmarkTransport.java

delta-runtime-cpp/src/benchmark/
  trace_export.cpp
  fault_control.cpp
  metrics.cpp
  sidecar_server.cpp

delta-ffi/src/benchmark_abi.cpp

delta-protocol/schemas/010/
  benchmark-definition-v1.json
  benchmark-definition-attestation-v1.json
  benchmark-arm-v1.json
  network-profile-v1.json
  fault-profile-v1.json
  run-manifest-v1.json
  environment-manifest-v1.json
  quality-evidence-v1.json
  safety-evidence-v1.json
  efficiency-evidence-v1.json
  resilience-evidence-v1.json
  evidence-manifest-v1.json
  benchmark-result-v1.json
  benchmark-result-qc-v1.json

configs/benchmark/
integration/benchmark/
reports/benchmark/
```

## Implementation Sequence

1. Verify the exact Feature 003–009 predecessor/evidence chain and inherited Formal GO.
2. Freeze benchmark definition/result/evidence/compatibility canonical schemas and reviewer rules.
3. Implement definition completeness validation and immutable preregistration workflow.
4. Complete a tiny synthetic vertical slice without claiming primary evidence.
5. Freeze the exact primary definition, thresholds, missing-run policy and embedded/sidecar policy.
6. Implement reproducible environment/build/data/model/evaluation capture.
7. Implement arm orchestration, token/domain reconciliation and both deployment profiles.
8. Implement deterministic network/fault/attack harnesses and formal-regression projection.
9. Implement immutable evidence collection, offline verification and all gate analyzers.
10. Run emulated primary benchmark; only after pass run an approved real-WAN variant.
11. Produce the deterministic governance ResultQC, report and final Constitution Check.

## Test Strategy

- Canonical definition/QC/result fixtures and mutation tests.
- Threshold/missing-policy completeness and no-post-hoc-edit tests.
- Flat/hierarchy hash equality and run-repetition checks.
- Full mandatory attack corpus, including Frankenstein and ApplyQC conflict.
- Token/domain mismatch rejection and downstream-failure-overrides-loss case.
- Network byte/time accounting reconciliation.
- 10% worker loss, validator/storage crash/partition and seed-loss complete-or-abort scenarios.
- Evidence deletion/mutation/reordering/incompatibility tests.
- Independent evaluator agreement and no manual GO override.

## Observability

Emit definition/run/evidence/result roots, arm/seed/workload identity, ticket/domain counts, certificate/checkpoint hashes, network/fault trace IDs, quality metrics, byte/time/utilization distributions, safety attack outcomes, missing evidence and final gate decisions. Secrets and raw private data are redacted from logs but preserved through authorized content refs where required.

## Rollout and Rollback

The benchmark cannot mutate production current state; it uses isolated project/round namespaces. Abort preserves evidence and parent checkpoints. A failed/invalid run is never overwritten; a new certified definition/version is required for a rerun that changes policy. No pilot deployment is permitted without a compatible GO ResultQC.

## Risks and Mitigations

- **Post-hoc metric selection**: definition QC before results and immutable thresholds.
- **Token/domain mismatch**: admission/reconciliation gate before analysis.
- **Metrics loss**: redundant append-only evidence files and explicit missing policy.
- **Environment drift**: image/source/dependency/SBOM fingerprints.
- **Overstated BFT claim**: distinguish safety, liveness assumptions and tested fault scope.
- **Performance optimization violating safety**: architecture test and Constitution gate.
- **Manual report bias**: deterministic analyzers plus evaluator quorum.

## Exit Gate

Definition is preregistered; mandatory run/evidence graph verifies; protocol hashes are exact; attack corpus is rejected; quality and WAN/resilience targets pass; independent evaluators produce one `BenchmarkResultQC(decision=GO)`. Otherwise feature 011 remains blocked.
