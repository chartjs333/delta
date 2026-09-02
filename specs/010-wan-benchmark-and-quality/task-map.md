# Feature 010 semantic/runtime task map

This map reconciles semantic tasks `T000–T054` with hybrid-runtime obligations
`HR010-001–HR010-018`. Both sets are mandatory. Synthetic fixtures cannot substitute for primary
quality/WAN evidence, and throughput cannot substitute for formal, exactness, sanitizer, durability
or process-isolation gates.

| Semantic tasks | Runtime obligations | Mandatory evidence boundary |
| --- | --- | --- |
| T000–T001 | HR010-001–HR010-003, HR010-007, HR010-017 | Exact predecessor, Formal GO, architecture scan and semantic STOP |
| T002–T007 | HR010-001–HR010-004, HR010-018 | Canonical benchmark/evidence/result contracts and cross-runtime fixtures |
| T008–T012 | HR010-001–HR010-004, HR010-018 | Preregistration, immutable definition and frozen policy |
| T013–T017 | HR010-001–HR010-006 | Reproducible environments, arm adapters and workload reconciliation |
| T018–T022 | HR010-008–HR010-013 | WAN/fault/process-isolation harness and exact trace replay |
| T023–T027 | HR010-003, HR010-015–HR010-018 | Immutable evidence graph and offline verification |
| T028–T034 | HR010-004–HR010-011 | Exact protocol, production attacks, sanitizer and safety gates |
| T035–T039 | HR010-016 | Preregistered token/domain-matched scientific-quality gate |
| T040–T045 | HR010-010, HR010-012–HR010-016 | WAN/P2P/resilience, embedded/sidecar and real-WAN gates |
| T046–T050 | HR010-017–HR010-018 | Deterministic result, governance attestation and no-override decision |
| T051–T054 | HR010-018 | Operations, evidence publication and final Constitution check |

## Authority and formal boundary

Python owns benchmark definitions, orchestration, scientific analysis and deterministic governance
decisions. C++ exposes protocol/runtime instrumentation and the isolated sidecar without acquiring
network or benchmark-policy authority. Java owns transport, fault delivery, deployment-profile
execution and bounded telemetry collection. None may create an alternate model-current authority.

Feature 010 is `REGRESSION_ONLY` against formal semantics
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
`BenchmarkDefinitionQC` and `BenchmarkResultQC` are evidence/governance attestations outside the
DeltaReduce runtime certificate graph. A new state-machine action, certificate-parent edge, failure
terminal, durability outcome or current transition is `SEMANTIC` and stops this branch pending a new
Feature 000 GO.

## Exact predecessor

- Feature 009 merge: `007eb08aa3aaee849128ba428274a9fbda561bf8`
- Feature 009 source: `f43e39fa1c60d256bab5d7e37e0756f28438d5e4`
- Feature 009 evidence: `a5e73b41feb2dad73aa11d810d0c700c548e11ba`
- Feature 009 final report SHA-256:
  `95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef`

Primary results remain forbidden until preflight passes, schemas are frozen, embedded-versus-sidecar
policy is immutable, and a complete primary `BenchmarkDefinition` has been attested.
