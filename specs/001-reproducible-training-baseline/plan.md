# Implementation Plan: Воспроизводимый training baseline и WAN-эмулятор

**Branch**: `001-reproducible-training-baseline` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

After independently verifying the exact compatible `000-formal-tla-spec` GO report, create a minimal typed Python codebase in which training core is separated from artifact storage, CLI and network emulation adapters. The implementation fixes canonical schemas/fixtures first, then builds the single-node trainer, safe checkpoint/resume, verifier and unprivileged/optional privileged netem adapters.

No package or production source task may start before the formal prerequisite passes. Baseline artifact/failure events must remain compatible with the formal trace/recovery abstractions they instantiate.

## Technical Context

- **Mandatory predecessor**: verified content-addressed Formal GO and `formal_semantics_id`.
- **Language/runtime**: Python 3.12.
- **Dependency/build**: `uv`, `pyproject.toml`, committed lockfile.
- **ML runtime**: PyTorch; `safetensors` for tensor payload.
- **Schema/validation**: typed domain dataclasses/Pydantic boundary models; canonical JSON UTF-8 with sorted keys.
- **CLI**: thin composition layer; business logic callable as Python API.
- **Tests**: pytest, property tests where valuable; ruff and mypy.
- **Storage**: filesystem artifact store with atomic publish; interface allows later CAS replacement.
- **Network emulation**: deterministic in-process proxy/stream adapter; `tc/netem` only as marked integration test.
- **Formal compatibility**: canonical action/outcome/durability IDs and a small projection fixture for artifact/recovery events.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Formal before code | T000 verifies exact Formal GO before T001+ | prerequisite negative/positive matrix |
| Scientific correctness | Token count, seeds, data order and manifests are domain contract | determinism/resume tests |
| Content-addressed state | Every persisted input/output gets SHA-256 and schema/media type | corruption tests |
| Failure/recovery | Atomic publish/replay semantics align with formal identity/idempotency | crash/projection tests |
| WAN realism | Offline fault profiles and optional real netem adapter | deterministic suite |
| Safe boundaries | unsafe deserialization prohibited | static gate |
| Observable increments | JSONL metrics/events, typed failures, independent exit gate | full branch gate |

**Pre-implementation result**: PASS — T000/HR001-001 independently verified the merged Formal GO and recorded its report, evidence graph, source, toolchain and semantics hashes in `evidence/formal-prerequisite.json`. Repeat against the final diff and formal semantics ID at T035.

## Architecture and Data Flow

```text
FormalVerificationReport(GO) ──verify──▶ FormalPrerequisiteRecord
                                              │
BaselineConfig ──validate──▶ BaselineService   │
DatasetManifest ────────────────┤              │
                                ▼              │
                    deterministic data/model/trainer
                                │
                metrics + checkpoint candidate
                                │
                                ▼
                     atomic ArtifactStore publish
                                │
                                ▼
                         immutable RunManifest

NetworkProfile ──▶ FaultyStream/Proxy ──▶ local loopback scenario
```

Training code depends on ports `ArtifactWriter`, `MetricsSink`, `Clock` and `DeviceRuntime`; filesystem, real clock and CLI remain adapters. Reproducibility class fixes platform/device/dtype contract. Trace projection is limited to formal abstractions actually used by this branch.

## Project Structure

```text
pyproject.toml
uv.lock
src/deltatorrent/
  domain/
    artifacts.py
    manifests.py
    network.py
    errors.py
    formal_compat.py
  training/
    config.py
    data.py
    model.py
    baseline.py
    checkpoint.py
  artifacts/
    canonical_json.py
    filesystem.py
    verifier.py
  adapters/netem/
    simulated.py
    linux_tc.py
  cli/
    main.py
    baseline.py
    artifacts.py
    netem.py
tests/
  unit/
  contract/
  integration/
  fixtures/
configs/baseline/
configs/netem/
docs/reproducibility.md
specs/001-reproducible-training-baseline/evidence/
```

## Implementation Sequence

0. Verify Formal GO/report/evidence/semantics compatibility and record immutable prerequisite evidence.
1. Fix packaging, quality tooling and unsafe-serialization prohibition.
2. Implement canonical JSON, hashes, manifests and atomic artifact-store port.
3. Add deterministic corpus/tokenizer/model fixtures and token accounting.
4. Implement baseline loop, checkpoint boundary and exact resume state.
5. Add CLI and bundle verifier.
6. Implement seeded unprivileged WAN simulator; then optional `tc` adapter.
7. Add formal projection fixtures for artifact lifecycle/failure/recovery abstractions.
8. Close determinism, corruption, timeout and offline integration tests.
9. Run final Constitution/formal-compatibility check.

## Test Strategy

- **Prerequisite**: GO/NO_GO/missing/corrupt/incompatible semantics/evidence cases.
- **Unit**: schema validation, canonicalization, hashing, token counting, sampler cursor, timeout math.
- **Numerical**: one-step direct reference; finite-value guards; dtype-aware worker-local tolerances.
- **Contract**: run/checkpoint/network schemas, stable errors and formal action IDs used here.
- **Integration**: continuous-vs-resume, repeated deterministic runs, artifact corruption, local loopback with faults.
- **Projection**: legal atomic publish/recovery traces pass; identity-changing repair/double-completion traces fail.
- **Platform**: CPU required; CUDA smoke marked; `tc` marked `requires_net_admin`.
- **Offline**: blocked DNS/outbound and repo fixtures only.

## Observability

- `metrics.jsonl`: step/token/loss/lr/throughput/memory.
- `events.jsonl`: lifecycle, checkpoint, retry, timeout and fault events with stable action/outcome IDs.
- `run-manifest.json`: final status and artifact graph.
- `formal-prerequisite.json`: verified report/evidence/semantics IDs.
- Manifests/metrics are authoritative evidence; logs are diagnostic.

## Rollout and Rollback

This feature does not modify a remote system. Rollback returns to the previous commit; schema versions are not reused. Temporary files are ignored/cleaned after ownership/hash checks. A formal semantic incompatibility stops development and returns changes to branch 000 rather than creating a local exception.

## Risks and Mitigations

- **Work starts without formal baseline**: hard T000 and no production task dependency path around it.
- **Nondeterministic kernels**: deterministic algorithms, platform fingerprint, tolerance class.
- **Incomplete checkpoint state**: explicit state inventory and resume-equivalence test.
- **Heavy CI fixture**: tiny model/corpus and separate full profile.
- **Leaked `tc` rules**: context manager/finalizer and cleanup verification.
- **Manifest before data**: two-phase atomic publish; manifest last.
- **Trace overclaim**: project only abstractions used by 001; full BFT refinement belongs to 003/008.

## Exit Gate

- T000 verifies exact compatible Formal GO before T001.
- All T001–T035 tasks and evidence are complete.
- Offline ruff/format/mypy/pytest pass.
- Deterministic repeat, resume, corruption, WAN timeout and projection suites pass.
- No pickle on trust/artifact boundaries.
- Formal semantics compatibility remains valid against final diff.
- Final Constitution Check = PASS and README contains reproducible smoke command.
