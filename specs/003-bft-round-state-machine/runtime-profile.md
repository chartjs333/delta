# Runtime Profile: 003 BFT Round State Machine

**Status**: Normative hybrid-runtime addendum  
**Primary runtime**: C++20/23 pure core + C++ native runtime  
**Integration runtime**: Java JDK 25 FFM conformance harness  
**Formal impact**: `REFINEMENT_ONLY` unless a missing action/outcome is discovered

## Scope

Feature 003 is the first branch allowed to implement validator state. It creates:

- `delta-core-cpp`: deterministic transition and canonical state/hash logic;
- `delta-runtime-cpp`: single-writer reactor, WAL, snapshot and recovery;
- `delta-ffi`: reviewed versioned C ABI;
- `delta-node-java`: minimal JDK 25 FFM harness and loopback command/effect adapter, not the full P2P transport.

## Pure core rules

The core accepts prior certified state plus canonical command bytes and returns a candidate next state/effect description. It does not:

- open sockets or inspect peers;
- read wall clock or schedule timers;
- write files;
- use Java/Python objects;
- rely on unordered iteration, raw struct layout or floating arithmetic.

State hashes are computed from explicit canonical encoders only.

## Native runtime rules

One reactor thread owns each `delta_runtime_t`. The runtime sequence is:

```text
parse/validate command
→ invoke pure transition
→ append canonical WAL record
→ durability barrier
→ atomically commit next state root
→ return canonical effect batch
```

No outbound vote/message/timer effect is visible before durability. Restart verifies descriptor/config, replays WAL/snapshot and recovers vote journal before accepting commands.

## C ABI

The ABI exposes opaque handles and command/effect byte slices. It must provide:

- descriptor with ABI/schema/protocol/formal-semantics/build IDs;
- open/submit/snapshot/close;
- caller-buffer size negotiation;
- stable numeric status categories;
- no exception escape;
- no C++ standard-library type crossing;
- explicit ownership and lifetime documentation.

The Java FFM layer is handwritten or generated from a pinned header/toolchain, but the C header and conformance fixtures are authoritative.

## Java harness

The initial Java harness:

- loads the native library;
- validates the descriptor and `formal_semantics_id`;
- calls open/submit/snapshot/close;
- uses a dedicated reactor executor;
- exercises direct and bounded-copy input paths;
- never calls transition-specific setters such as `changeView()` or `abort()`.

Full Netty/TLS/P2P behavior belongs to 005/008.

## Memory model

- per-call scratch arena;
- active-round arena;
- durable state represented by WAL/snapshot and immutable objects;
- no arena reset may erase durable vote/certificate evidence;
- Java-owned memory is borrowed for the synchronous call only;
- native-owned handles have explicit release APIs.

## Mandatory failure matrix

Crash injection covers:

- before WAL append;
- during/after append before durability;
- after durability before in-memory commit;
- after commit before effect return;
- after effect return before Java send;
- restart before/after journal recovery;
- output-buffer-too-small retry;
- stale/duplicate command replay.

Every trace must refine the accepted feature-000 actions and preserve exact effect identity.

## Exit additions

- four independent native runtimes (`f=1`) produce identical state/effect/WAL hashes for 100 tickets;
- C++ GCC/Clang results match;
- ASan/UBSan and separate TSan gates pass;
- Java direct/copy paths produce identical effects;
- ABI mismatch and stale formal-semantics startup fail closed;
- crash/replay traces pass the formal checker;
- no socket symbol/dependency exists in pure core.
