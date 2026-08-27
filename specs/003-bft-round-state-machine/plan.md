# Implementation Plan: DeltaReduce v1 BFT Round State Machine

**Branch**: `003-bft-round-state-machine` | **Date**: 2026-08-27 | **Spec**: `spec.md`
**Constitution**: 2.1.0
**Formal Semantics**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`
**Formal Impact**: `REFINEMENT_ONLY`, unless implementation requires an action or outcome absent from the accepted semantics

## Summary

Implement the feature-003 validator as a C++ pure deterministic transition core, a C++ single-writer durable runtime, a versioned C ABI and a minimal Java FFM conformance harness. Python remains limited to existing fixture and evidence tooling. Transport, production quantization and compressed delta codecs are later-feature work.

No production source may be created until Phase 0 emits a passing, content-addressed `evidence/preflight.json` that binds both predecessors, the exact Formal GO, all formal artifacts, ADR-0010, the current source tree and a zero-finding architecture scan.

## Technical Context

- Core language: portable C++20 baseline, continuously compiled in C++20 and C++23 modes with pinned GCC and Clang toolchains.
- Native runtime: one reactor thread owns each handle; bounded MPSC submission, canonical WAL, durability barrier, snapshot and deterministic recovery.
- ABI: versioned C header with opaque handles, byte slices, caller-buffer size negotiation, stable status values and no exception escape.
- Java: JDK 25 FFM conformance harness plus JDK 26 compatibility lane; no Java-owned consensus decisions.
- Arithmetic: checked fixed-width integer operations over prepared `bft-int-fixture-v1` values; no floating-point reduction.
- Canonical data: explicit encoders only; raw C/C++ object layout and unordered iteration are forbidden.
- Hashing: SHA-256 over versioned, domain-separated canonical bytes.
- Durability: no vote/message/timer effect becomes visible before its canonical WAL record is durable.
- Time and network: inputs are canonical commands/effects. The pure core has no clock, socket, filesystem, JVM or Python dependency.

Production `int16-fixed-v1` quantization, rounding/clipping, compressed codecs and profile negotiation belong to feature 004. Protobuf/gRPC, Netty/TLS and P2P transport belong to features 005/008.

## Constitution Check

| Principle | Design response | Gate |
| --- | --- | --- |
| Formal-first | Exact Formal GO and 24-artifact manifest are prerequisites | `evidence/preflight.json` |
| Replicated state | `3f+1` validators, `2f+1` QCs, no authoritative singleton | Conflicting-command and vote tests |
| Deterministic core | Pure C++ transition over prior state plus canonical command bytes | Architecture and golden-state tests |
| Integer arithmetic | Checked fixed-width operations over prepared integer fixtures | Boundary and first-overflow corpus |
| Input freeze | Seed command requires finalized input root | State/refinement tests |
| Durable voting | WAL durability precedes effect exposure | Crash matrix and replay tests |
| Runtime boundary | Versioned C ABI; Java drives bytes, never transitions | ABI mismatch and direct/copy parity tests |

**Pre-implementation result**: PENDING Phase 0 evidence. Any central authority, adaptive work, floating reduction, Java-owned transition or missing durability outcome is a hard STOP.

## Architecture and Data Flow

```text
canonical command/state bytes
          |
          v
delta-core-cpp (pure transition)
          |
          +--> candidate state bytes/root
          +--> canonical effect/WAL-record bytes
                         |
                         v
delta-runtime-cpp (single writer, WAL, snapshot, recovery)
                         |
                         v
delta-ffi (versioned C ABI) <--> delta-node-java (JDK FFM harness)
```

The core performs no I/O. The runtime persists and commits one transition before returning its exact effect batch. The Java harness validates descriptor IDs and exercises the ABI; it does not implement consensus or transport.

## Project Structure

```text
delta-protocol/
  schemas/003/
  fixtures/003/{valid,invalid,cross-language}/
delta-core-cpp/
  include/delta/core/
  src/
  tests/
  toolchain/
delta-runtime-cpp/
  include/delta/runtime/
  src/{reactor,wal,recovery}/
  tests/
delta-ffi/
  include/delta_abi.h
  src/
  tests/
  toolchain/
delta-node-java/
  src/
  gradle/
  toolchains.toml
integration/traces/003/
specs/003-bft-round-state-machine/evidence/
```

## Implementation Sequence

1. Reconcile SpecKit artifacts and freeze one T-to-HR task map.
2. Produce Phase 0 predecessor, formal, architecture and formal-impact evidence; stop on any finding.
3. Freeze compiler, CMake/Ninja, JDK/jextract and dependency manifests before production source.
4. Freeze canonical schemas, hash domains, valid/invalid/cross-language bytes and ABI descriptor fields.
5. Implement explicit C++ types, fail-closed parsers and checked integer helpers.
6. Implement the pure transition/state/effect/WAL-record function and cross-compiler golden tests.
7. Implement the single-writer reactor, WAL, durability barriers, snapshots and journal-first recovery.
8. Freeze and implement the C ABI, then the JDK 25 FFM harness and JDK 26 lane.
9. Export normal/view-change/abort/crash/recovery traces and run formal refinement plus production-mutant regressions.
10. Run four native runtimes over 100 prepared integer tickets, sanitizer/fuzz gates and publish final evidence.

## Test Strategy

- **Canonical contracts**: exact valid, invalid and cross-language command/state/effect/WAL/descriptor bytes and hashes.
- **Pure transition**: all legal/illegal state changes, wrong parent/view/schema/profile and message-order permutations.
- **BFT safety**: conflicting proposals, duplicate signers, wrong epochs, vote uniqueness and quorum intersection.
- **Arithmetic**: signed fixed-width boundaries, exact zero, safe maximum and first overflow over prepared integers.
- **Durability**: crash injection before/during/after append, durability, commit and effect exposure.
- **ABI/FFM**: mismatch matrix, output sizing, pointer lifetime, release, retries and direct/copy parity.
- **Portability**: GCC/Clang, C++20/C++23, little-endian fixtures and explicit rejection of incompatible data.
- **Formal refinement**: accepted legal traces, rejected illegal traces and applicable production mutants.
- **Native exit**: four independent runtimes process 100 tickets and produce identical state/effect/WAL hashes.

## Observability

The runtime emits canonical effects containing IDs, hashes, height/view, stable rejection categories and logical deadlines. It never logs tensor payloads, private keys or dataset contents. Observability cannot alter transition state or durability ordering.

## Rollout and Rollback

Feature 003 is exercised first through the offline native harness and Java FFM conformance lane. A failed round preserves the parent checkpoint. Protocol, ABI, schema and formal-semantics IDs are immutable; rollback disables an unsupported descriptor rather than reinterpreting durable bytes.

## Risks and Mitigations

- **Spec/runtime drift**: one normative task map and exact artifact IDs gate source creation.
- **Undefined native behavior**: checked arithmetic, explicit encoders, sanitizers and fuzzing.
- **Vote exposure before durability**: one WAL/commit/effect sequence with crash injection at every boundary.
- **Cross-language lifetime errors**: caller-owned synchronous slices, explicit handle ownership and bounded-copy fallback.
- **Hidden transport coupling**: pure-core dependency scan and absence of socket symbols.
- **Semantic discovery**: reclassify as `SEMANTIC`, amend feature 000 and obtain a new Formal GO before continuing.

## Exit Gate

- Phase 0 evidence binds merged features 001–002, exact Formal GO, all formal artifacts, ADR-0010 and zero architecture findings.
- Canonical schema, descriptor and cross-language byte fixtures pass on pinned toolchains.
- Four native validators (`f=1`) process 100 prepared integer tickets and emit byte-identical state/effect/WAL hashes.
- Unsafe arithmetic, equivocation, wrong-view input, unavailable shards and seed-before-freeze fail closed.
- Crash/replay produces no double vote, partial effect or divergent state.
- GCC/Clang C++20/23, JDK 25/26, ASan/UBSan, separate TSan and parser-fuzz gates pass.
- Legal and illegal implementation traces satisfy the accepted formal refinement checker and applicable production mutants remain detectable.
- Final evidence and Constitution 2.1.0 checks pass.
