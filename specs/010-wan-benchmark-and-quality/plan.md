# Implementation Plan: Preregistered WAN, BFT Safety and Model-Quality Benchmark

**Branch**: `010-wan-benchmark-and-quality` | **Date**: 2026-08-23 | **Spec**: `spec.md`

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
src/deltatorrent/benchmark/
  definition.py
  review.py
  orchestrator.py
  arms.py
  network_profiles.py
  fault_profiles.py
  attacks.py
  evidence.py
  quality.py
  efficiency.py
  safety.py
  resilience.py
  decision.py
  verifier.py
  report.py
  telemetry.py
src/deltatorrent/cli/benchmark.py
configs/benchmark/primary.yaml
configs/benchmark/network/
configs/benchmark/faults/
tests/contract/test_benchmark_definition_bytes.py
tests/integration/test_benchmark_reproducibility.py
tests/integration/test_attack_corpus.py
tests/integration/test_seed_loss_and_churn.py
tests/integration/test_go_no_go_decision.py
tests/architecture/test_benchmark_cannot_weaken_protocol.py
reports/README.md
```

## Implementation Sequence

1. Freeze benchmark definition/result/evidence/compatibility canonical schemas and reviewer QC rules.
2. Implement definition completeness validation and preregistration workflow.
3. Implement reproducible environment/build/data/model/evaluation capture.
4. Implement arm orchestration and token/domain identity reconciliation.
5. Implement deterministic network/fault/attack harnesses.
6. Implement immutable evidence collector and offline verifier.
7. Implement safety, quality, efficiency and resilience analyzers.
8. Implement deterministic all-mandatory GO/NO_GO and ResultQC.
9. Run emulated primary benchmark; only after pass run approved real-WAN variant.
10. Publish report/evidence and final Constitution Check.

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
