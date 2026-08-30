# Hybrid Runtime Tasks: 010 Polyglot Benchmark

## Identity and environment

- [x] **HR010-001** Extend BenchmarkDefinition with C++/ABI/Java/Python/build/formal semantics and deployment-profile identities.
- [x] **HR010-002** Freeze primary compiler/JDK/Python/Netty/native flags and canonical fixture corpus before results.
- [x] **HR010-003** Add runtime compatibility admission and evidence capture.

## Exact cross-language gates

- [x] **HR010-004** Run Python/C++/Java exact canonical bytes, hashes, status and negative parsing corpus.
- [ ] **HR010-005** Run GCC/Clang and supported architecture exact state/effect comparison.
- [ ] **HR010-006** Run direct-versus-copy FFM and flat-versus-hierarchy exact comparison.
- [x] **HR010-007** Run complete implementation trace projection/refinement and production-mutant regression.

## Safety and failure gates

- [ ] **HR010-008** Execute ASan/UBSan, separate TSan and parser fuzz campaigns at preregistered bounds.
- [ ] **HR010-009** Execute WAL/durability/effect/current crash matrix and verify replay identity.
- [ ] **HR010-010** Execute Netty leak, event-loop block, backpressure, stream bound and stale timer matrix.
- [ ] **HR010-011** Execute ABI/schema/formal-semantics mismatch and native pointer lifetime negatives.

## Embedded versus sidecar

- [x] **HR010-012** Implement/freeze isolated-sidecar IPC profile or preregister a formal risk decision for omission.
- [ ] **HR010-013** Compare embedded/native-process crash containment, restart/replay, latency and throughput.
- [ ] **HR010-014** Select the pilot validator profile through immutable benchmark evidence.

## Reporting

- [ ] **HR010-015** Report zero-copy eligibility/hit rate, copy fallback bytes and phase latency decomposition.
- [ ] **HR010-016** Join runtime gates with token/domain-matched scientific quality and WAN/P2P gates.
- [x] **HR010-017** Make any failed mandatory runtime/formal gate force deterministic `NO_GO`.
- [ ] **HR010-018** Publish complete offline-verifiable polyglot evidence and BenchmarkResultQC.
