# DeltaReduce Hybrid Runtime Architecture

## Component context

```text
Python/PyTorch worker
  local fixed ticket → normalized contribution → canonical q-shards
                                      │ network bytes
                                      ▼
Java node shell (JDK 25 + Netty)
  TLS / framing / peers / backpressure / timers / P2P / telemetry
                                      │ C ABI via FFM
                                      ▼
C++ native runtime
  single-writer reactor / WAL / snapshots / recovery / durable vote guard
                                      │ pure function boundary
                                      ▼
C++ protocol core
  canonical parse / state transition / fixed-point / certificates / apply
```

The Java shell can run without understanding certificate mathematics. The native core can run in a deterministic harness without sockets. The Python worker can run scientific baselines without a validator node.

## Dependency direction

```text
delta-protocol
   ▲        ▲        ▲
Python    C++      Java
worker    core     node
            ▲
      C++ native runtime
            ▲
          C ABI
```

No circular build dependency is allowed. Generated bindings are outputs; the authoritative input is the reviewed C header plus canonical contract registry.

## Command/effect flow

1. Netty authenticates transport and validates only bounded outer framing.
2. Input is retained direct memory or copied to a bounded direct staging segment.
3. Java enqueues an opaque canonical command.
4. The consensus reactor performs one synchronous FFM downcall.
5. Native runtime verifies bytes and invokes the pure transition core.
6. If state-changing, runtime appends WAL and completes the durability barrier.
7. Runtime commits next state root and returns a canonical effect batch.
8. Java sends opaque frames, schedules opaque timer tokens and records transport metrics.
9. Borrowed input is released after the call.
10. Trace event records action ID, prior/next roots, parent/body/result hashes and durability sequence.

## State ownership

| State | Owner | Lifetime |
| --- | --- | --- |
| Netty connections, channel buffers, peer routes | Java | connection/process |
| bounded ingress staging memory | Java | one queued/downcall operation |
| parser scratch | C++ core/runtime | one call |
| active round arena | C++ runtime | one active round |
| votes, certificates, state roots | C++ durable runtime | WAL/snapshot retention |
| dataset/model/training checkpoint | Python worker/CAS | artifact policy |
| certified global object pieces | Java distribution/CAS | object retention |

An arena reset never deletes durable vote/certificate/evidence state.

## ABI handshake

At startup Java obtains the native descriptor and rejects mismatch in:

- ABI major/minor;
- C struct sizes/features;
- protocol and canonical schema version;
- formal semantics ID;
- build/provenance ID;
- required arithmetic/crypto capability bits.

The same values appear in deployment and run manifests.

## Backpressure

Every boundary is bounded:

- frame bytes;
- queued commands;
- in-flight retained buffers;
- native input/output bytes;
- effect count and total effect bytes;
- timer count;
- WAL record and snapshot size;
- native call watchdog/health policy.

Queue saturation results in transport backpressure or typed rejection. It never permits dropping an already durable protocol effect silently.

## Timer semantics

```text
Native effect: ScheduleTimer(token, deadline_nanos, purpose_code)
Java event:   TimerFired(token)
Native result: accepted transition | stale-token no-op | typed failure
```

`deadline_nanos` is local scheduling information, not consensus evidence. The formal logical-time/deadline transition remains authoritative.

## Native failure profiles

### Embedded FFM

One JVM process contains the native runtime. Use for initial conformance and canary latency measurements. ASan/UBSan cannot generally be treated as production mode; sanitizer and fuzz lanes are separate.

### Isolated sidecar

Java and native runtime are separate processes. IPC must preserve canonical command/effect bytes, ordering, backpressure, timer tokens and durability identity. A sidecar restart loads native WAL/snapshot before accepting commands.

## Verification matrix

| Concern | Required evidence |
| --- | --- |
| canonical bytes | Python/C++/Java golden fixtures |
| state transitions | implementation trace accepted by formal checker |
| fixed-point | Lean precondition instance + C++ boundary tests |
| ABI | descriptor/layout/version negative matrix |
| pointer lifetime | ASan plus retained/release and copy-fallback tests |
| threading | TSan lane and single-writer queue tests |
| parser safety | libFuzzer corpus and allocation limits |
| durability | crash injection before/after append/fsync/commit/effect return |
| Java transport | Netty leak detector, backpressure, timeout and cancellation tests |
| native crash | embedded process-loss and sidecar restart tests |
| architecture | dependency/import/socket/no-float static tests |

## Non-claims

This architecture does not prove that C++ is universally faster, that Netty will support a particular connection count, or that every path is zero-copy. Those are benchmarked configuration-specific targets. It does not change the formal cryptographic, worker-honesty or model-quality non-claims.
