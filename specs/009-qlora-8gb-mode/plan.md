# Implementation Plan: Certified Fixed-Ticket QLoRA Mode for 8 GiB GPUs

**Branch**: `009-qlora-8gb-mode` | **Date**: 2026-08-23 | **Spec**: `spec.md`

## Summary

Add an immutable base/quantization/adapter schema, adapter-only local training for fixed tickets, canonical adapter q-vector integration with the full certificate chain, deterministic adapter ApplyQC, content-addressed base reuse and a preregistered physical 8 GiB qualification gate.

## Exact predecessor and formal boundary

- feature-008 merge: `62124e58062d876dc4c2fd903b57cfc7d89872d7`;
- feature-008 source: `4ef4daead4e3fcdf19d6947cf8120c4974af09fe`;
- feature-008 evidence: `d86473a3f864b4e61d2312584afa080c8fd4fbab`;
- feature-008 report SHA-256: `fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c`;
- formal semantics: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`;
- classification: `REFINEMENT_ONLY`;
- `semantic_completeness_claimed=false`.

Feature 009 specializes the merged certificate/apply runtime. It does not introduce QLoRA-specific
ISC, root or ApplyQC types. Any new protocol-visible state, action, failure terminal, durability
outcome or partial-apply transition is a `SEMANTIC` change and stops implementation pending a new
feature-000 Formal GO.

## Technical Context

- Python 3.12/PyTorch reference worker stack.
- Reference QLoRA adapter integration behind a backend-neutral port; external libraries and versions are pinned by the mode profile.
- Tiny local model/mock quantized backend for offline CI.
- Base and tokenizer imported into existing CAS/P2P; no runtime dependency on a public registry after import.
- Local worker arithmetic may use declared FP16/BF16 kernels, but consensus input is only canonical `int16-fixed-v1` adapter shards.
- Existing ISC/EC/APC/ParameterShardQC/AggregateRootQC/ApplyQC implementations are reused without alternate formulas.
- C++ owns adapter context compatibility, exact coverage/reduce/apply and native current authority; Java owns content-addressed cache/transport only.
- Physical memory gate records allocator and device evidence under an exact committed configuration.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Fixed work | QLoRA uses immutable domain tickets and requires `A_j=H` | Completion/abort tests |
| Integer consensus | Adapter delta normalized then canonical q encoded | No-float-reduce test |
| Certificate lineage | Base/schema fingerprints in every certificate stage | Mismatch corpus |
| Domain mixture | Adapter ApplyQC uses fixed `pi_d` | Speed-independence regression |
| Atomic model | Only ApplyQC advances adapter current pointer | Four-validator/crash tests |
| Evidence | 8 GiB claim tied to exact physical profile | Qualification artifact |
| Formal-first | Existing feature-008 actions are specialized without a parallel certificate graph | Exact preflight and refinement traces |
| Hardware truth | No mock/tiny run can satisfy the physical claim | Physical runner identity or `BLOCKED_HARDWARE` |

**Pre-implementation result**: PASS. Any proposal that adapts `H`, aggregates floating adapter deltas or allows base mutation is an automatic STOP.

## Architecture and Data Flow

```text
BaseModelManifest + QuantizedBaseProfile
                 │
                 ▼
        frozen quantized base
                 + AdapterParameterSchema + parent adapter
                 │
       fixed DomainPureWorkTicket
                 │
                 ▼
       local adapter-only training
                 │ A_j=H
                 ▼
normalized adapter delta → int16 q shards → C/AC
                 │
        ISC → EC → APC → shard QCs
                 │
        AggregateRootQC → adapter ApplyQC
                 │
 certified adapter checkpoint → P2P (base reused)
```

## Project Structure

```text
delta-protocol/schemas/009/
  training-mode-v1.json
  base-model-manifest-v1.json
  quantized-base-profile-v1.json
  adapter-config-v1.json
  adapter-parameter-schema-v1.json
  qlora-ticket-context-v1.json
  adapter-contribution-manifest-v1.json
  global-adapter-checkpoint-v1.json
  model-composition-manifest-v1.json
  memory-qualification-profile-v1.json
  memory-qualification-evidence-v1.json
delta-protocol/fixtures/009/{valid,invalid,tiny-offline,cross-language}/

delta-worker-python/src/deltatorrent/qlora/
  manifests.py
  backend.py
  model_loader.py
  adapter_schema.py
  preflight.py
  trainer.py
  contribution.py
  composition.py
  qualification.py
  telemetry.py
delta-worker-python/src/deltatorrent/cli/qlora.py

delta-core-cpp/include/delta/qlora/
  context.hpp
  compatibility.hpp
  adapter_coverage.hpp
  adapter_apply.hpp
delta-core-cpp/src/qlora/
delta-core-cpp/tests/
delta-core-cpp/fuzz/

delta-ffi/src/qlora_abi.cpp
delta-ffi/tests/qlora_abi_test.cpp

delta-node-java/src/main/java/io/deltareduce/node/qlora/
  BaseObjectCache.java
  AdapterTransport.java
  NativeAdapterContext.java
  ModelComposition.java
  AdapterCheckpointPublisher.java
  QLoRATelemetry.java

configs/qlora/8gb-reference.yaml
delta-worker-python/tests/fixtures/models/tiny_qlora/
delta-worker-python/tests/qlora/
specs/009-qlora-8gb-mode/{scripts,tests,evidence}/
```

## Implementation Sequence

1. Verify the exact feature-008/Formal predecessor and record physical runner availability.
2. Freeze base, quantization, adapter, composition and memory canonical contracts plus license policy.
3. Implement the offline tiny backend and exact adapter schema resolution.
4. Implement compatibility/memory preflight and frozen-base/adapter-only invariants.
5. Integrate fixed-ticket local training, full-completion rule and normalized adapter contribution.
6. Connect adapter shards to feature-004 and the existing feature-008 certificate chain.
7. Implement deterministic native adapter outer apply and ApplyQC/current pointer specialization.
8. Implement Java content-addressed base reuse and adapter checkpoint transport/composition.
9. Execute the preregistered physical 8 GiB qualification profile last.
10. Publish evidence and run final cross-artifact/Constitution checks.

## Test Strategy

- Base/tokenizer/quantization/adapter-schema golden fingerprints.
- Frozen parameter, buffer, optimizer membership and payload-set tests.
- Fixed `B/H`, `A_j=H`, OOM/incomplete/cancellation no-commit matrix.
- Base/schema/mode mismatch at every certificate stage.
- Direct fixed-point adapter aggregate and four-validator ApplyQC equality.
- Current-pointer crash/replay and base-mutation rejection.
- P2P base cache and adapter-only transfer byte accounting.
- Resume/composition compatibility and derived-export provenance.
- Separate physical 8 GiB memory qualification.

## Observability

Record mode/base/schema/profile/certificate hashes, trainable/total parameters, base/adapter/q bytes, ticket completion, peak memory, cache reuse, robust/aggregation/apply timings and qualification result. Never log model-access tokens, private keys or raw training examples.

## Rollout and Rollback

Run tiny offline and shadow certificate paths first. Enable hardware profile only after configuration/license sign-off. Rollback disables future QLoRA rounds and retains the last ApplyQC-certified adapter; it never mutates the base or downgrades certificate requirements.

## Risks and Mitigations

- **Backend version drift**: exact profile fingerprint and hard compatibility check.
- **Hidden base mutation**: pre/post logical hash, optimizer/gradient/payload assertions.
- **8 GiB variability**: committed physical profile with explicit headroom and no generalized claim.
- **Adapter schema ambiguity**: resolved ordered names/shapes committed before ticketing.
- **Apply nondeterminism**: existing portable exact apply profile and byte conformance.
- **License leakage**: operator import and repository/secret scans.

## Exit Gate

Offline and physical qualification gates pass; full fixed ticket is required; base remains immutable;
adapter-only fixed-point certificate/ApplyQC path is exact; base cache reuse is demonstrated; full
quality and final Constitution Check pass. If the preregistered physical runner cannot execute the
frozen profile, the only legitimate exit is `BLOCKED_HARDWARE`; offline evidence cannot waive it.
