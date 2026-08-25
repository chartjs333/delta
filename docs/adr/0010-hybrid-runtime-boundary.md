# ADR-0010: Hybrid Runtime Boundary — C++ Core, Java Node, Python Worker

**Status**: Accepted for implementation planning  
**Date**: 2026-08-25  
**Formal impact**: `REFINEMENT_ONLY` against formal semantics `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Context

DeltaReduce requires exact deterministic state transitions, checked integer arithmetic, durable no-double-vote recovery and high-concurrency WAN transport. Local model training simultaneously depends on the mature PyTorch ecosystem. Implementing every concern in one runtime would either expose consensus to garbage-collection/network framework behavior or force ML/data tooling into an unnecessarily low-level stack.

The original DeltaTorrent concept supports long worker-local training and separates reduce from distribution. It does not prescribe implementation languages. This ADR is therefore a project implementation decision, not a source-derived claim.

## Decision

Use a three-runtime reference architecture.

### 1. C++ pure protocol core

`delta-core-cpp` implements canonical parsing, transition legality, fixed-point/norm/coverage logic, certificate verification and deterministic next-state computation. It has no sockets, TLS, DNS, wall clock, Java/Python object access or filesystem adapter.

### 2. C++ native runtime

`delta-runtime-cpp` owns one single-writer consensus reactor, WAL, snapshots, durable vote guard, artifact-state journal and restart/replay ordering. It wraps the pure core and releases outbound effects only after durable commit.

This resolves the WAL ownership decision: the reference validator does **not** split a transition across C++ candidate state and a Java-owned WAL. A future Java WAL requires a separate ADR and crash/refinement proof.

### 3. Java node shell

`delta-node-java` uses the reference JDK 25 runtime, Netty and FFM. It owns network connections, TLS, framing, peers, rate limits, backpressure, opaque timers, P2P transfer and observability. JDK 26 is a compatibility lane, not the baseline.

Java cannot choose transition legality, quorum, membership, buckets, weights, aggregate completeness or current checkpoint.

### 4. Python/PyTorch worker

`delta-worker-python` owns data/token accounting, local AdamW, QLoRA, normalized pseudo-gradient construction and scientific evaluation. Its contribution enters consensus only as canonical normalized/quantized bytes.

## C ABI

The Java/native boundary is a small versioned C ABI. C++ ABI types never cross it.

The preferred interface is command/effect based:

```c
typedef struct delta_runtime delta_runtime_t;

typedef struct {
  uint32_t abi_major;
  uint32_t abi_minor;
  uint32_t struct_size;
  const char* formal_semantics_id;
  const char* build_id;
  uint64_t feature_bits;
} delta_descriptor_t;

typedef struct { const uint8_t* data; uint64_t size; } delta_slice_t;
typedef struct { uint8_t* data; uint64_t capacity; uint64_t written; } delta_mut_slice_t;
typedef struct { uint32_t code; uint32_t category; uint64_t required_capacity; } delta_status_t;

delta_status_t delta_runtime_open(delta_slice_t config, delta_runtime_t** out) noexcept;
delta_status_t delta_runtime_submit(delta_runtime_t*, delta_slice_t command,
                                    delta_mut_slice_t* effects) noexcept;
delta_status_t delta_runtime_snapshot(delta_runtime_t*, delta_mut_slice_t*) noexcept;
delta_status_t delta_runtime_close(delta_runtime_t*) noexcept;
const delta_descriptor_t* delta_runtime_descriptor(void) noexcept;
```

No exported function may throw. Boundary wrappers catch internal exceptions and convert them to stable status without exposing partial state.

## Memory ownership

- Java/Netty-owned memory is borrowed only for a synchronous downcall.
- C++ cannot store its pointer after return and cannot call `free` on it.
- Native output is written to caller-provided bounded memory or returned through explicitly native-owned handles with a matching release function.
- Round scratch, active-round arena and durable state are separate lifetimes.
- `std::pmr` reference allocators are preferred before custom allocators; custom allocation requires profiler evidence.

## Zero-copy

Zero-copy is an optimization, not a correctness requirement.

Fast path requires direct, contiguous, retained input with a valid address for the complete downcall. Heap, composite or non-contiguous input is copied to a bounded direct staging buffer. Both paths must emit identical canonical effects and traces.

## Threading and timers

Netty event loops feed a bounded MPSC queue. Exactly one reactor thread performs mutating native calls per runtime handle. FFM/WAL/fsync never blocks a Netty event loop.

C++ requests timers by opaque token. Java schedules delivery and later submits `TimerFired(token)`. C++ rejects stale tokens and decides whether `ViewChange`, `HardAbort` or no transition is legal. Java never calls transition-specific timer functions by phase name.

## Durability sequence

```text
parse/validate → compute candidate → append WAL → durability barrier
→ commit state root → expose canonical effects → Java sends
```

Failure before durability returns no externally sendable effect. Restart replays durable records before accepting new commands.

## Native crash containment

Two profiles are defined:

- `embedded-ffm`: Java loads native runtime in-process; lowest latency, no process crash isolation.
- `isolated-sidecar`: Java communicates with a native process through a versioned local IPC/shared-memory contract; stronger crash containment, additional complexity.

Feature 003 may begin with embedded FFM. Feature 010 must compare both or explicitly approve embedded-only risk before the pilot validator profile.

## Determinism rules

Consensus code uses fixed-width integers, checked operations, explicit endian encoding, deterministic sorting and canonical encoders. It forbids raw-struct hashing, signed overflow, pointer-derived state, host map iteration, locale dependence, wall-clock reads, `random_device`, `fast-math` and floating reduce.

## Consequences

### Positive

- deterministic core and durable runtime are isolated from transport framework behavior;
- Java provides mature WAN/TLS/backpressure tooling;
- Python retains ML ecosystem productivity;
- formal trace projection has a clear single-writer durability point;
- zero-copy can be optimized without becoming a safety assumption.

### Costs

- three toolchains and cross-language fixtures;
- FFI lifetime and native crash risks;
- additional build/release complexity;
- isolated-sidecar profile may require extra IPC and recovery work.

## Formal compatibility rule

This ADR does not add a formal action. WAL, timer delivery, retries and publication must project to existing actions/stuttering. If implementation needs a new externally visible state or outcome, work stops and feature 000 is amended before code continues.
