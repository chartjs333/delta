# Runtime Profile: 005 Certified P2P Distribution

**Primary runtime**: Java JDK 25 + Netty  
**Native integration**: C ABI/FFM certification and state-policy verification  
**Formal impact**: `REFINEMENT_ONLY`

## Java ownership

Java owns:

- authenticated peer connections and transport framing;
- non-authoritative peer discovery/leases;
- bounded concurrency, rate limits and backpressure;
- piece scheduling, resumable journal orchestration and CAS adapters;
- P2P telemetry and cancellation;
- FFM invocation of native certification/state checks.

Java does not decide whether an object is mathematically valid or current. The trusted object identity and certification policy derive from native certified state.

## Ingress memory paths

### Direct fast path

Allowed only when the readable region is direct, contiguous, retained and addressable for the complete synchronous downcall. Java retains the `ByteBuf`/segment until return and releases exactly once.

### Bounded-copy fallback

Heap, composite, fragmented or otherwise unsuitable input is copied into a bounded direct staging buffer. The copy and direct paths must produce identical native status/effect/hash results.

Native code cannot retain Java-owned pointers, reinterpret unknown lengths or free Java memory.

## Event-loop rule

FFM calls, content verification, filesystem CAS operations and durability barriers do not run on Netty event loops. A bounded executor/reactor boundary applies backpressure before memory grows without limit.

## Certification boundary

The Java publisher/fetcher submits canonical manifest/certificate references to native verification. Native response is a typed decision/effect; Java cannot downgrade an ApplyQC requirement or substitute a coordinator signature.

## Failure behavior

- peer/discovery failure may delay or fail distribution but cannot rewrite certified current state;
- corrupt/wrong-length pieces are discarded before visibility;
- initial seed loss succeeds only when the remaining verified union is complete;
- P2P unavailability does not revoke or mutate ApplyQC;
- local/partial media types are rejected before advertisement.

## Exit additions

- Netty leak detection and retained/release matrix pass;
- direct and copy paths are byte/effect identical;
- heap/composite/oversized/endless-stream cases are bounded;
- event-loop blocking detector passes;
- certification downgrade and local/partial publication fail closed;
- seed-loss/restart traces refine formal publication/repair behavior.
