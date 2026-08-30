# Runtime Profile: 010 Polyglot WAN, Safety and Quality Benchmark

**Runtimes under test**: Python/PyTorch worker, C++ core/runtime, Java JDK 25 node  
**Compatibility lanes**: JDK 26, GCC/Clang, supported CPU architectures  
**Formal impact**: regression-only; no benchmark override of accepted semantics

**Exact predecessor**: Feature 009 merge `007eb08aa3aaee849128ba428274a9fbda561bf8`,
source `f43e39fa1c60d256bab5d7e37e0756f28438d5e4`, evidence
`a5e73b41feb2dad73aa11d810d0c700c548e11ba`, final-report SHA-256
`95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef`.

Benchmark definition/result QCs are governance attestations only. They do not enter the protocol
certificate lineage and cannot mutate the runtime current checkpoint.

## Benchmark identity additions

`BenchmarkDefinition` binds:

- C++ compiler/version/flags and native build ID;
- ABI descriptor and `formal_semantics_id`;
- Java runtime, Netty and binding generator/revision;
- Python/PyTorch/dependency lock and accelerator runtime;
- embedded FFM or isolated sidecar deployment profile;
- canonical protocol fixture set;
- sanitizer/fuzz/architecture evidence identities.

A result from another ABI/runtime profile cannot silently satisfy the primary arm.

## Mandatory polyglot gates

### Exactness

- Python fixture → C++ q/certificate/apply → Java transport bytes agree exactly.
- GCC and Clang state/effect hashes agree.
- direct and copy FFM paths agree.
- flat and hierarchical C++ results agree.
- every runtime projects the same accepted formal action/state identities.

### Native safety

- ASan/UBSan gate;
- separate TSan gate;
- parser/libFuzzer corpus and allocation limits;
- crash injection across WAL/durability/effect/current boundaries;
- ABI mismatch and pointer-lifetime negative tests.

### Java safety

- Netty leak and event-loop-blocking checks;
- bounded queue/backpressure/stream limits;
- stale timer and duplicate delivery matrix;
- JDK 25 primary and JDK 26 compatibility.

### Process isolation

Benchmark both `embedded-ffm` and `isolated-sidecar`, or preregister an explicit reason/risk decision for omitting one. Report native crash blast radius, restart time, replay correctness and latency/throughput cost separately.

### Scientific quality

Python reference and distributed arms remain token/domain matched. Native/Java performance cannot compensate for failed validation/downstream/post-training quality.

## Decision rule

Any failed formal regression, exact byte/hash gate, sanitizer/fuzz gate, durability crash gate, Java lifetime/backpressure gate or required isolation-profile gate is mandatory `NO_GO` regardless of throughput.

## Exit additions

- complete polyglot evidence graph is offline-verifiable;
- zero-copy claims include measured hit rate and fallback cost;
- latency is broken down into Java queue, FFM, native transition, WAL, network and artifact phases;
- performance targets are configuration-bound and do not weaken safety.
