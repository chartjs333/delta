# DeltaReduce Hybrid Runtime Map

## Authority

This document maps accepted feature semantics onto the reference C++/Java/Python implementation. It is subordinate to the Constitution and accepted formal baseline but normative for implementation branches.

## System-wide boundaries

- **Pure C++ core** decides legality and canonical next state.
- **C++ native runtime** owns single-writer durability/recovery and exposes a C ABI.
- **Java node** owns transport and operations while treating consensus effects as opaque.
- **Python worker** owns local ML and scientific evaluation.
- **delta-protocol** owns runtime-neutral canonical schemas and fixtures.

## Per-feature map

### 001 — Reproducible baseline

Python/PyTorch scientific reference; introduce `delta-protocol` and repository boundaries. C++/Java directories are placeholders only. First action after predecessor merge is Formal GO verification.

### 002 — Local round engine

Python fixed-ticket execution, exact `A_j=H`, normalized pseudo-gradient and canonical contribution candidate. No consensus state or FFI invocation.

### 003 — BFT round state machine

Implement C++ pure transition core, native reactor/WAL/recovery, C ABI and minimal Java FFM conformance harness. Use embedded FFM only for the first gate. Every mutating operation is single-writer and persist-before-expose.

### 004 — Fixed-point delta protocol

C++ reference encoder/parser/shard/bound implementation. Python may produce worker fixture candidates; Java must pass opaque bytes. All three runtimes agree on exact bytes and hashes.

### 005 — Certified P2P distribution

Java/Netty implements peer transfer, discovery hints, CAS orchestration and backpressure. C++ verifies certification policy/state lineage through commands. Direct-buffer zero-copy is optional and tested against copy fallback.

### 006 — Hierarchical reduce

C++ executes regional/global checked integer sums and QCs. Java routes region/shard messages but cannot average, exclude regions or choose weights.

### 007 — Ticket scheduling

C++ state machine deterministically creates plans, leases, expiry/reassignment and commitment ordering. Java gathers capability evidence and performs transport admission; capability fields cannot enter mathematical weights.

### 008 — Certificates and apply

C++ implements ISC/EC/APC, exact robust plan, ParameterShardQC, AggregateRootQC, deterministic apply and current pointer. Java owns authenticated message delivery and opaque timer scheduling. Full vote lifecycle uses native durability before send.

### 009 — QLoRA

Python loads the frozen base and trains adapters under fixed tickets. C++ certifies and applies adapter q-vectors. Java transports and distributes base/adapter artifacts.

### 010 — Benchmark

Run the complete polyglot system: Python quality arms, C++ exact state/arithmetic, Java WAN/P2P. Mandatory suites include GCC/Clang, x86_64/aarch64 where available, ASan/UBSan, TSan lane, parser fuzzing, JDK 25/26, embedded/sidecar crash behavior and exact cross-language fixtures.

### 011 — Pilot

Deploy Java node + native runtime for validators/reducers/apply/P2P and Python workers for training. The PilotDefinition chooses embedded or sidecar profile explicitly. No implicit crash-isolation claim is permitted.

## ABI and effect categories

Java-visible native effects are limited to versioned categories such as:

- outbound canonical frame;
- schedule/cancel opaque timer;
- artifact read/write/repair request;
- state/evidence publication request;
- structured metric/event record;
- typed status/rejection.

Adding a new protocol-visible effect category requires formal-impact review.

## Cross-language fixture rule

A contract is not accepted until Python, C++ and Java implementations—or an independent reference encoder where a runtime is not yet present—agree on exact canonical bytes, hashes, status codes and negative parsing outcomes.

## Start rule

Do not begin with Netty, FFM or custom allocators. Begin with merged Formal GO verification, runtime-neutral canonical fixtures and the Python scientific baseline. Native/JVM production code starts in 003 after 001–002 exit gates.
