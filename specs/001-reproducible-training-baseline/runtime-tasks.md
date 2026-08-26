# Hybrid Runtime Tasks: 001 Reproducible Training Baseline

These tasks supplement `tasks.md`. They are mandatory and use `HR001-*` IDs to avoid renumbering the existing feature tasks.

## Phase HR0: predecessor and architecture gate

- [x] **HR001-001** Verify that PR #1 is merged and independently validate the exact `FormalVerificationReport(GO)`, source commit, evidence graph and `formal_semantics_id`; write `specs/001-reproducible-training-baseline/evidence/formal-prerequisite.json`.
- [x] **HR001-002** Run a formal-impact classification for ADR-0010 and confirm `REFINEMENT_ONLY`; any required new formal action, timer transition, durability rule or failure terminal is a STOP and returns to feature 000.
- [x] **HR001-003** Record the accepted runtime decisions and source provenance in `docs/adr/0010-hybrid-runtime-boundary.md`, `docs/architecture/hybrid-runtime.md` and `docs/source/hybrid-runtime-v1-amendment.md`.

## Phase HR1: polyglot repository foundation

- [x] **HR001-004** Create the top-level component directories and ownership README files for `delta-protocol`, `delta-worker-python`, `delta-core-cpp`, `delta-runtime-cpp`, `delta-ffi`, `delta-node-java` and `integration`.
- [x] **HR001-005** Define dependency-direction checks: protocol imports nothing runtime-specific; Python worker cannot import native/JVM implementations; future Java and C++ modules consume only canonical contracts.
- [x] **HR001-006** Add root build orchestration documentation without introducing native/JVM production code; define pinned toolchain manifests as future inputs rather than silently using host defaults.

## Phase HR2: canonical shared contracts

- [x] **HR001-007** Create runtime-neutral artifact/media/schema registry under `delta-protocol/`.
- [x] **HR001-008** Add canonical JSON and safe tensor fixture vectors with exact expected bytes and SHA-256.
- [x] **HR001-009** Add formal action/outcome/error projection fixtures used by the Python baseline.
- [x] **HR001-010** Add negative tests proving Python memory layout, pickle, map iteration order and locale cannot define protocol bytes.

## Phase HR3: Python baseline integration

- [x] **HR001-011** Place the Python package under `delta-worker-python/` or document an equivalent migration-compatible layout before T001 implementation.
- [x] **HR001-012** Bind run/checkpoint manifests to protocol schema and formal-semantics compatibility fields.
- [x] **HR001-013** Export legal artifact lifecycle/recovery traces and verify them with the feature-000 trace checker where applicable.

## Final gate

- [x] **HR001-014** Run Python quality gates, protocol contract tests, dependency-boundary tests and formal compatibility verification.
- [x] **HR001-015** Publish a start-ready evidence note stating exactly which directories are placeholders and which contain executable code.

## Dependency rule

`HR001-001` is a hard prerequisite for all production tasks in both `tasks.md` and this file. `HR001-004` through `HR001-010` precede publication of the first immutable baseline bundle.
