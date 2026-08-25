# Hybrid Runtime v1 amendment — provenance and interpretation

**Supplied through project conversation**: 2026-08-25  
**Status**: implementation-architecture input  
**Not a protocol-semantic amendment by itself**

## User-provided direction

The requested continuation proposed a hybrid C++/Java implementation:

- Modern C++ consensus/state-machine core;
- Java transport based on Netty and the Foreign Function & Memory API;
- C-compatible FFI boundary;
- off-heap/direct-buffer fast path;
- arena-based memory management;
- single-threaded mutation of consensus state;
- strict no-exception and memory-ownership rules across FFI.

## Project interpretation and accepted refinements

The SpecKit adopts the hybrid direction with these clarifications:

- Python/PyTorch remains a first-class worker-local training runtime.
- C++ is split into a pure deterministic core and a native durability/runtime layer.
- The reference JVM baseline is JDK 25, with JDK 26 compatibility testing.
- FFM calls a versioned C ABI, not a C++ ABI.
- Zero-copy is an optional direct/contiguous fast path with bounded-copy fallback.
- Native code cannot retain Java-owned pointers after a synchronous call.
- The C++ native runtime owns the reference WAL to preserve persist-before-expose atomically.
- Java delivers opaque timer tokens and cannot choose state transitions.
- Embedded FFM and isolated native sidecar are distinct deployment profiles.
- Every runtime binds the accepted `formal_semantics_id` and emits formal trace projection evidence.

## Relationship to the original DeltaTorrent concept

Source-derived and retained:

- long worker-local training rather than per-layer WAN collectives;
- reduce plane separated from distribution plane;
- P2P used for identical global artifacts;
- WAN realism, resumability and 8 GB/QLoRA goals.

Not source-derived:

- C++/Java/Python language allocation;
- FFM/Netty/C ABI;
- native WAL ownership;
- timer-token design;
- embedded versus sidecar process layout.

These are implementation decisions governed by ADR-0010 and feature runtime profiles.
