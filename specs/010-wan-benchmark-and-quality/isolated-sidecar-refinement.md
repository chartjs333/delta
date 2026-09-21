# Isolated-sidecar refinement design

**Status**: design-only prerequisite; not implemented; no measurement authority
**IPC contract**: `delta-local-sidecar-ipc/1.0`
**Historical exactness outcome**: `FAIL` at
`fc012861d8a1577f155abb94877102adef5cbf36` (tree
`deeb2bda4c0a7e68015843d2ebe6fe4396edfb7b`)
**Formal semantics**:
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`

## Authority boundary

This document freezes the refinement boundary required before isolated-sidecar
implementation. It does not implement the sidecar, authorize a benchmark run,
or select a deployment profile. The historical FAIL commit and its omission-risk
decision remain immutable history; they are not rewritten or promoted by this
design.

This design claims no sidecar implementation completion. T028/T029 and
HR010-013/014 remain open. `selected_profile` remains `null`. There is no Gate A,
B, C, or D qualification, `BenchmarkResultQC`, Feature 010 GO, pilot authority,
Feature 011 authority, primary observation, or performance claim.

The machine-readable normative companion is
`sidecar-refinement-design.json`. If prose and that artifact disagree, the more
restrictive fail-closed rule applies and implementation stops for review.

## Formal-impact decision

The design is `REFINEMENT_ONLY`. It adds no formal action, vote context, QC type,
failure terminal, durability outcome, current transition, or consensus-visible
field. IPC/session/shared-memory identities are operational only and never enter
canonical commands, state roots, effects, certificates, or protocol hashes.

Implementation must stop and return to Feature 000 before code continues if it
needs any of the following:

- an `IPCFailure`, handshake, graceful-shutdown, sidecar-restart, degraded, or
  accepted-but-not-durable formal action/outcome;
- any changed deadline, availability rule, certificate-parent edge, arithmetic
  precondition, current-state behavior, or effect category;
- a Java/watchdog decision that directly changes view, aborts, applies, advances
  current, or interprets a protocol deadline;
- Java ownership of the WAL, vote journal, snapshot authority, state root,
  current pointer, replay decision, or a semantic effect outbox;
- cancellation or rollback of an admitted command, effect exposure before the
  native durability barrier, or command admission before journal recovery;
- a profile-specific canonical effect or formal trace after operational
  stuttering is erased.

## Ownership and process model

Java owns process supervision, local endpoint creation, framing, bounded ingress,
backpressure, health checks, operational watchdogs, opaque timer delivery, and
telemetry. These responsibilities cannot decide consensus legality or synthesize
effects.

The native sidecar owns the exclusive durable-directory lock, exactly one
single-writer reactor per runtime handle, the WAL, durability barriers,
snapshots, durable vote journal, state/current roots, recovery, replay identity,
and canonical effects. A replacement process cannot become ready while an older
generation still owns the durable-directory lock.

Netty event loops only enqueue bounded requests and receive completions. They
never wait for IPC, FFM, WAL, snapshot, replay, or process termination. The
sidecar may accept multiple framed requests into its bounded ingress queue, but
exactly one dispatcher invokes mutating native functions in monotonically
increasing admitted sequence order. `STATE`, `SNAPSHOT`, and `CLOSE` are ordered
behind every previously admitted mutation.

Shared memory transports transient canonical bytes only. It is not a Java WAL,
effect outbox, snapshot, state cache, or source of replay authority.

## Descriptor handshake

The local control channel begins in `DESCRIBE_ONLY`. Before `OPEN`, Java sends a
`CLIENT_HELLO` and the sidecar returns `SERVER_DESCRIPTOR`. Both bind:

- IPC contract major/minor, header size, canonical encoding, operation set, and
  the exact frozen v1 bounds table identified by `BOUNDS_SHA256`;
- the exact payload-schema registry, message-type table, flag table, bounds, and
  shared-memory layout by their frozen SHA-256 IDs;
- session ID and monotonically increasing process generation;
- sidecar executable SHA-256 and build ID;
- outer benchmark deployment profile `ISOLATED_SIDECAR`;
- the complete nested C ABI descriptor: `struct_size`, ABI major/minor, feature
  bits, schema version, protocol version, formal-semantics ID, build ID,
  schema-set ID, and native runtime profile;
- the SHA-256 digest of the canonical nested descriptor bytes.

The descriptor also binds the canonical frame-layout SHA-256, numeric message
types, numeric flags and rules, and the canonical-encoding ID
`sha256:393cd207a2cd3fd4da366be56095a3467e3184c2c5db1d300d1c07d49cdd7aff`.
The other v1 handshake IDs are:

- bounds:
  `sha256:32d9e791ac35dc6bb061aaedb0a67ee28ad1a2662bbb0ffd1bfc9177b055d0f8`;
- flag table:
  `sha256:6aa94eb75b5b6af99132f71b2753d56988454be86a371b46f46241cf7a8e33d5`;
- frame layout and carrier rules:
  `sha256:46fcc91280fc2c878cb176bf6e9d855f8e39ac9fffcf18709b1a6b80a30ce18e`;
- message-type table:
  `sha256:dfa3fe65b946e6527b317168ef0ea000a4610bba1e9c1ed9ebd099adff71e64e`;
- payload schemas:
  `sha256:31edfa48d707fb06cd24624d1790946981294bb093d74d44c202a5d15c5376c5`;
- shared-memory layout:
  `sha256:0a48282fddae72060e9b93c02f97f174b56f8a20b07aabb88ee51f7ef03f5aa4`.

Both hello and descriptor carry the exact `BOUNDS_SHA256`; its pre-versioned
table is the only v1 bounds value. A missing or unequal hash fails the handshake.

The outer deployment profile and nested native-library profile are distinct
identity fields and cannot be substituted for one another. Version or identity
mismatch fails before `OPEN`; there is no downgrade negotiation. Major versions
must be equal. A minor version is admitted only when every required field,
operation, flag, and bound has an exact supported interpretation; unknown
required fields or flags fail closed.

The nested C ABI descriptor is never raw struct memory. Its canonical bytes are
`DELTABI1` at offset 0 (8 bytes), total encoded length `u32be` at offset 8,
`struct_size:u32be` at 12, ABI major/minor `u16be` at 16/18, and
`feature_bits:u64be` at 20. Starting at offset 28, schema version, protocol
version, formal-semantics ID, build ID, schema-set ID, and native runtime profile
appear in that order as `u32be length || canonical UTF-8 NFC bytes`, each at most
256 bytes, with no NUL or trailing bytes. The nested descriptor SHA-256 covers
exactly its declared total length; C pointers, padding, and host layout never
enter it.

After `OPEN`, the sidecar acquires the durable-directory lock, invokes the
existing native open/recovery path, replays and verifies the journal, then emits
`READY`. No `SUBMIT` or timer delivery is admitted before `READY`.

## Canonical bounded framing

Control frames use the existing canonical-binary rules: explicit unsigned
big-endian integers, no raw structs or pointers, no padding-dependent bytes, and
no trailing data. V1 has this exact 128-byte header:

| Offset | Bytes | Field | Encoding/value |
| ---: | ---: | --- | --- |
| 0 | 8 | magic | ASCII `DELTAIPC` |
| 8 | 2 | IPC major | `u16be`, exactly 1 |
| 10 | 2 | IPC minor | `u16be`, exactly 0 |
| 12 | 2 | header length | `u16be`, exactly 128 |
| 14 | 2 | message type | `u16be`, frozen opcode table |
| 16 | 4 | flags | `u32be`, frozen bit table |
| 20 | 16 | session ID | opaque bytes |
| 36 | 8 | generation | `u64be` |
| 44 | 16 | transport correlation ID | opaque bytes |
| 60 | 8 | sequence | `u64be` |
| 68 | 8 | payload length | `u64be` |
| 76 | 8 | response capacity | `u64be` |
| 84 | 32 | payload SHA-256 | raw digest bytes |
| 116 | 12 | reserved | all zero |

Request/response opcode pairs are `OPEN=0x10/0x11`, `SUBMIT=0x20/0x21`,
`STATE=0x30/0x31`, `SNAPSHOT=0x40/0x41`, `CLOSE=0x50/0x51`, and
`HEALTH=0x60/0x61`; `CLIENT_HELLO=0x01`, `SERVER_DESCRIPTOR=0x02`,
`SHARED_MEMORY_ACK=0x70`, and `ERROR_RESPONSE=0xff`. Flags are
`PAYLOAD_INLINE=0x01`, `PAYLOAD_SHARED_MEMORY=0x02`,
`RESPONSE_EXPECTED=0x04`, and `READ_ONLY=0x08`. Inline and shared-memory payload
flags are mutually exclusive when a payload exists; any unknown bit fails.
`CLIENT_HELLO` and `SERVER_DESCRIPTOR` are inline-only because shared memory is
not available before the descriptor handshake. `SHARED_MEMORY_ACK` is also inline-only, so the message
that releases a shared-memory reference never depends on that same reference.
Every opcode accepts only the exact flag set frozen in the normative JSON;
`READ_ONLY` is required only on `STATE_REQUEST` and `HEALTH_REQUEST`, never on
the ordered, durable `SNAPSHOT_REQUEST`. Every response-expecting request,
including `CLIENT_HELLO`, sets `RESPONSE_CAPACITY` exactly to the frozen v1
maximum logical payload of 16,785,408 bytes; every other message sets it to
zero. Transport `SEQUENCE` starts at one and increments
by one independently in each direction and session. Zero is reserved, overflow
permanently fences the generation, and this counter is distinct from native
`ADMITTED_SEQUENCE`.

`MESSAGE_TYPE` is also the sole payload type code. Each logical payload starts
with the exact 16-byte prefix
`schema_type:u16be || major:u16be || minor:u16be || reserved-zero:u16be || value_length:u64be`;
the type equals `MESSAGE_TYPE` and the schema version is 1.0. The value is an
ordered TLV sequence with the exact header
`field_id:u16be || wire_type:u8 || flags-zero:u8 || length:u32be`. Field IDs are
strictly increasing and unique. All fields in the selected schema are required;
unknown, duplicate, missing, mis-sized, non-canonical UTF-8, or trailing fields
fail before admission. Wire-type codes are `U8=1`, `U16_BE=2`, `U32_BE=3`,
`U64_BE=4`, `ID128=5`, `SHA256=6`, `BYTES=7`, `CANONICAL_UTF8=8`, and
`SHM_REFERENCE_64=9`. Scalar lengths are exact. A textual SHA-256 identity is
validated as `sha256:` plus 64 lowercase hexadecimal digits and carried as its
32 raw digest bytes.

The normative JSON freezes every field ID, order, wire type, and maximum. Its
message schemas are summarized here without changing that order:

| Message | Exact logical fields after the prefix |
| --- | --- |
| `CLIENT_HELLO`, `SERVER_DESCRIPTOR` | contract name; IPC major/minor; encoding, frame, payload-schema, message-table, flag-table, bounds, and SHM-layout digests; session; generation; executable digest; sidecar build; outer profile; canonical nested ABI descriptor and digest |
| `OPEN_REQUEST` | request ID/digest; submission capacity; durable-directory UTF-8; initial state; nested-descriptor digest |
| `OPEN_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; runtime instance; durable sequence; state root; ready bit |
| `SUBMIT_REQUEST` | request ID/digest; opaque canonical command |
| `SUBMIT_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; effect identity; opaque canonical effect and digest; durable sequence; prior/next state roots |
| `STATE_REQUEST`, `SNAPSHOT_REQUEST` | request ID/digest; runtime instance |
| `STATE_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; durable sequence; state root; canonical-state digest and bytes |
| `SNAPSHOT_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; durable sequence; state root; snapshot-receipt digest and bytes |
| `CLOSE_REQUEST` | request ID/digest; runtime instance; `DRAINED_TERMINAL_ONLY=1` or local `TERMINATE_AND_FENCE=2` |
| `CLOSE_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; durable sequence; state root; closed bit |
| `HEALTH_REQUEST` | request ID/digest; runtime instance or all-zero pre-open value |
| `HEALTH_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; operational health state; generation; last admitted sequence; outstanding count; lock-held and ready bits |
| `SHARED_MEMORY_ACK` | request ID/digest; exact 64-byte reference; ACK/rejection disposition |
| `ERROR_RESPONSE` | echoed request ID/digest; admission state/sequence; native status; local error; offending type; required capacity; bounded diagnostic detail |

For request messages, `REQUEST_DIGEST` is SHA-256 over ASCII
`DELTAIPCREQUEST1`, then message type/schema major/schema minor as `u16be`, then
the complete encoded operation-specific request TLVs (field IDs 16 and above).
Responses and errors echo that request digest; they never rehash their own
response fields. `CLIENT_HELLO`/`SERVER_DESCRIPTOR` payload session and
generation must equal both the frame header and the current session/generation;
the same equality holds for `HEALTH_RESPONSE` generation. Admission-state values
are `NOT_APPLICABLE=0`,
`NOT_ADMITTED_PROVEN=1`, `ADMITTED_OUTCOME_AVAILABLE=2`, and
`OUTCOME_UNKNOWN=3`; only native recovery may turn an unknown admitted request
into an exact replay result. Java may compare and route these opaque bytes but
cannot reconstruct a consensus transition from them.

When admission fields are present, `NOT_APPLICABLE` requires admitted sequence
zero, native status zero, and no result authority. `NOT_ADMITTED_PROVEN` requires
sequence zero, reserved unavailable native status `4294967295`, and
`ERROR_RESPONSE`. A successful admitted operation uses its operation response
with a nonzero sequence, native status zero, and every result field present; an
admitted nonzero native status uses `ERROR_RESPONSE`. `OUTCOME_UNKNOWN` requires
a nonzero sequence and `ERROR_RESPONSE` with no operation-result fields; when no
native status is recoverable it also uses `4294967295`. Present empty bytes use
zero length and SHA-256(empty); an absent fixed ID/hash is all zero only where
its schema name explicitly says `OR_ZERO`. A safe pre-parse error may use empty
request ID, SHA-256(empty), sequence zero, and `4294967295` only after the current
session/generation, header, and correlation are trusted. Otherwise the frame is
dropped without a response, the channel closes, the generation is permanently
fenced, and no native call occurs.

For inline transfer, header length/digest cover the complete logical payload.
For shared-memory transfer, the control-channel body is exactly the 64-byte
reference below while header length/digest equal the referenced logical length
and SHA-256. The resolved logical payload still obeys the same schema. A
no-payload frame has neither payload flag, zero length, no body, and
SHA-256(empty).

Carrier eligibility is per message and frozen. `CLIENT_HELLO`,
`SERVER_DESCRIPTOR`, `OPEN_RESPONSE`, `STATE_REQUEST`, `SNAPSHOT_REQUEST`, both
`CLOSE` messages, both `HEALTH` messages, `SHARED_MEMORY_ACK`, and
`ERROR_RESPONSE` are inline-only. `OPEN_REQUEST`, both `SUBMIT` messages,
`STATE_RESPONSE`, and `SNAPSHOT_RESPONSE` may use inline or SHM. Thus handshake
cannot depend on unnegotiated SHM and an ACK cannot recursively consume a slot.

Every length/offset addition is checked before allocation or dereference.
Truncation, trailing bytes, unknown version/opcode/flag, bad digest, generation
mismatch, non-monotonic sequence, or out-of-bounds shared-memory reference is
rejected before native admission. Nonzero reserved bytes also fail closed.

Frozen hard bounds for v1 are:

- canonical control envelope: at most 16,785,536 bytes, including the 128-byte
  header and maximum inline logical payload;
- inline and logical payload: at most 16,785,408 bytes;
- canonical command or effect payload: at most 16 MiB;
- logical IPC payload including frozen metadata: at most 16,785,408 bytes, with
  at most 8,192 metadata bytes around a 16 MiB command/effect;
- request IDs: at most 256 bytes; identity text: at most 256 bytes; durable
  directory UTF-8: at most 4,096 bytes;
- ingress queue capacity: 64 requests;
- in-flight correlations: 64;
- shared-memory regions: 2, one per direction;
- slots per region: 64;
- reference/control record/control prefix: 64/128/8,192 bytes;
- bytes per region: 1 GiB;
- timers tracked per runtime: 65,536;
- one mutating native call at a time.

V1 does not negotiate or lower bounds. Both peers use the exact frozen table
identified by `BOUNDS_SHA256`; any other table or hash is a pre-`OPEN` mismatch.
Before admitting a mutation, the sidecar reserves bounded response storage or a
retrievable replay slot. Output backpressure can never discard a durable effect.
`QUEUE_FULL`/`BACKPRESSURE` is valid only before native admission and leaves the
abstract state unchanged.

The nested FFI may report `BUFFER_TOO_SMALL` after a command has already become
durable. V1 therefore preallocates the frozen maximum or retries the identical
canonical request ID/body inside the same hard bound; it never treats buffer
sizing as proof that admission did not occur and never exposes a prefix.

## Shared-memory and buffer ownership

The mandatory path copies every legal logical payload, including the maximum,
through bounded staging. The
optional shared-memory fast path must produce exactly the same command bytes,
status, effect bytes, roots, durable sequence, and projected trace.

A shared-memory reference is exactly 64 bytes, never a pointer:

| Offset | Bytes | Field |
| ---: | ---: | --- |
| 0 | 4 | region ID `u32be` (`JAVA_TO_NATIVE=1`, `NATIVE_TO_JAVA=2`) |
| 4 | 4 | slot `u32be` |
| 8 | 8 | generation `u64be` |
| 16 | 8 | offset `u64be` |
| 24 | 8 | logical length `u64be` |
| 32 | 32 | logical-payload SHA-256 |

Each of the 64 slots has one aligned 128-byte control record at `slot * 128`:
atomic state `u32be` at 0, region ID at 4, generation at 8, slot at 16, four
zero bytes at 20, offset at 24, length at 32, SHA-256 at 40, and 56 zero bytes at
72. Thus the control prefix is exactly 8,192 bytes and all live data offsets are
at or above it. Checked ranges must fit the 1 GiB region and cannot overlap any
other non-free slot.

States are `FREE=0`, `WRITING=1`, `PUBLISHED=2`, `READING=3`, `ACKED=4`, and
`REJECTED=5`. The only transitions are
`FREE -> WRITING -> PUBLISHED -> READING -> ACKED|REJECTED -> FREE`. The
producer acquires the free slot with an acquire-release CAS, writes metadata and
the complete data/digest, then release-stores `PUBLISHED`. The consumer
acquire-loads and CASes to `READING` before any read and release-stores its final
ACK/rejection only after all access ends. The producer acquire-loads that final
state before clearing and release-storing `FREE`. The handshake requires aligned,
lock-free interprocess 32-bit big-endian atomics; otherwise the SHM path is
disabled and the mandatory bounded-copy path is used.

After the consumer release-stores `ACKED` or `REJECTED`, it may send the
inline-only `SHARED_MEMORY_ACK` as a notification. That frame is not slot-release
authority: the producer still must acquire-observe the matching terminal control
state before clearing it to `FREE`. A lost or duplicate ACK frame stutters and
cannot cause early or repeated reuse.

The producer exclusively owns a slot while writing. The consumer is read-only
until it acknowledges or rejects the reference. Reuse is forbidden until the
producer observes the terminal slot state with acquire semantics. Session loss
permanently fences that generation and invalidates every old-generation
reference, but reclamation occurs only after peer death, endpoint close, and
unmap are confirmed. Frame session, generation, correlation,
monotonic sequence, region, slot, length, and digest checks reject delayed or
stale references before access. Reference and control-record generation must
equal both the frame generation and the current generation.

Java-owned input remains valid through completion of the synchronous native call
or is copied first. Native code retains no Java/Netty pointer. Native output is
invisible until the native call returns, the full payload is present, and the
sidecar has verified its length and digest. An unexpected `BUFFER_TOO_SMALL`
does not expose a prefix; the identical request is replayed with adequate
bounded capacity.

## Correlation, retry, timeout, and stale responses

`transport_correlation_id` is local and distinct from the canonical protocol
`request_id`. Response acceptance requires the current session ID and
generation plus an exact match of correlation ID, operation, canonical request
ID, and request digest. Java binds the admitted sequence from the first validated
native or recovery result: it must be zero for
`NOT_APPLICABLE`/`NOT_ADMITTED_PROVEN` or a positive native-assigned value for an
admitted request. A retry/recovery response must match the persisted native
recovery proof exactly. Unknown, completed, conflicting, or prior-generation
responses are discarded and cannot be sent to peers. Reconnect within the same
generation is forbidden.

The same canonical `request_id` with a different operation or body is a
fail-closed conflict. An exact retry keeps the same operation, request ID, and
body. If the request was never
admitted it may execute once; if it was durably committed but its response was
lost, native recovery/replay returns the same effect identity and durable
sequence. A Java cache is never the authority for that decision.

Watchdog timeouts are operational only. Before admission they may remove a
queued request. After admission they mean `OUTCOME_UNKNOWN`: Java permanently
fences the generation, stops admission and rejects all later responses from it.
It checks the OS process handle. If the process is still alive, Java requests
shutdown, waits the fixed 10,000 ms bound, then force-terminates it. The same
generation is never unfenced or reused. Replacement is forbidden until process
exit, endpoint closure, and durable-directory lock release are all confirmed.
Only after a replacement acquires the lock, completes journal recovery, and is
`READY` may the identical request be retried. Failure to confirm exit or lock
release leaves the runtime `UNREADY`, with no admission and `selected_profile`
still `null`. Timeout cannot mean protocol rejection, view change, hard abort,
or rollback.

V1 uses a Java monotonic operational clock with a 1,000 ms heartbeat interval,
five missed heartbeats before suspicion/fencing, a 30,000 ms request watchdog,
a 10,000 ms graceful-shutdown bound, and a 120,000 ms recovery-to-ready bound.
Restart attempts per incident are limited to three with a fixed 1,000 ms
backoff, and begin only after confirmed exit and lock release. Exhaustion
leaves the runtime unready with no admission and no profile selection; it is not
a new consensus terminal. These values may only be lowered by a separately
reviewed contract version before measurement, never adapted from live results.

Confirmed native death fences the generation. A new process must acquire the
exclusive durable-directory lock, complete `Restart`/`RecoverJournal`, and emit
`READY` before any request is admitted. Heartbeat loss while the process remains
alive is message delay/stuttering, not a formal crash.

## Persist-before-expose

For every mutating `SUBMIT`, including `TimerFired(token)`, the native boundary
remains:

```text
validate command -> compute candidate -> append WAL -> durability barrier
-> commit state root -> return canonical effects -> frame/publish response
-> Java may send
```

The sidecar cannot emit an effect frame before the native call returns. Failure
before durability returns no externally sendable effect. A crash after durable
commit but before a complete IPC response is recovered through exact replay;
partial frames and partial shared-memory writes are never visible.

## Trace projection

Before the first clean `OPEN`, lifecycle events are diagnostic-only: no formal
state root exists, and they are excluded from the exported trace. The first clean
`OPEN` binds the `Init` root. Every later operational event records the
before/after abstract state root and durable sequence plus a projection reason.
The exported formal trace deterministically erases stutters and contains only
already accepted actions.

Every stutter requires identical prior/next state roots, an unchanged durable
sequence, and creates no new effect identity or protocol outcome. The
lost-response re-emission stutter may re-expose only the exact previously durable
effect identity, status/effect bytes, and durable sequence; it creates no new
transition. The wrapper cannot erase or rewrite an existing action ID, request
ID, parent/body/result hash, state root, durable sequence, outcome, or artifact
reference.

| Concrete lifecycle event | Required projection |
| --- | --- |
| initial process start, endpoint creation, descriptor/auth handshake, shared-memory map, pre-Init heartbeat | diagnostic-only; no formal root; excluded from exported trace |
| first clean `OPEN` | formal `Init` boundary; open mechanics stutter |
| post-Init heartbeat | stutter; state root and durable sequence unchanged |
| replacement acquires the durable lock after confirmed death | exactly one existing `ACT-RESTART` per new generation |
| recovery `OPEN` begin | stutter; no command admission |
| completed WAL/journal recovery | exactly one existing `ACT-JOURNAL-RECOVER` |
| `STATE`, health, drained terminal `CLOSE`/native release | read-only or lifecycle stutter |
| ordered durable `SNAPSHOT` compaction | operational native mutation; consensus-state stutter |
| active close request, kill request, or heartbeat suspicion | stutter; fence only, no death action |
| confirmed death/removal of an active formal actor | exactly one existing `ACT-CRASH` per generation |
| `SUBMIT` dispatch/framing | stutter; native trace owns semantic projection |
| each native trace event excluding `ACT-CRASH`, `ACT-RESTART`, `ACT-JOURNAL-RECOVER`, `ACT-MESSAGE-REPLAY`, and `ACT-MESSAGE-DROP` | the same existing action ID and canonical fields, one-to-one |
| timer schedule/cancel/wait or timer-frame arrival | stutter; preserve any separate native-emitted logical-time/timeout action |
| stale timer rejected before a native formal event | stutter with no native mutation |
| lost-response retry or identical effect re-emission | stutter with identical effect identity/durable sequence |
| native trace emits existing `ACT-MESSAGE-REPLAY` | preserve it one-to-one only when its accepted formal preconditions hold |
| native trace emits existing `ACT-MESSAGE-DROP` | preserve it one-to-one only when its accepted formal preconditions hold |
| duplicate envelope discarded before native or retry not yet admitted | stutter |
| conflicting retry, queue/backpressure reject, stale response reject | stutter; no native mutation |
| invalid frame rejected before formal enqueue or live-channel loss before admission | stutter |
| `SNAPSHOT` compaction | stutter; certified/current state unchanged |

Java records lifecycle evidence but never synthesizes a consensus/native
transition. A deterministic refinement projector may map verified death and
replacement-lock evidence to existing `ACT-CRASH`/`ACT-RESTART` only after their
accepted formal preconditions hold. A wrapper never synthesizes
`ACT-MESSAGE-DELIVER`, `ACT-MESSAGE-REPLAY`, or
`ACT-MESSAGE-DROP`; only an existing native trace event may carry an accepted
semantic action. A `CLOSE`/kill intent itself stutters. If the active formal
actor is subsequently confirmed removed, that alive-to-dead edge projects once
to the existing crash abstraction. If any projection cannot satisfy the
accepted preconditions, implementation is `BLOCKED_FORMAL`.
Supervisor-confirmed lifecycle evidence is the sole projector input for crash,
restart, and journal-recovery for that generation; a matching native or duplicate
projection is forbidden. Replay/drop remain native-trace-only. This makes every
concrete event key contribute at most one exported action.

## Immutable embedded-versus-sidecar comparison

The comparison consists of two separately admitted exact runs joined by one
comparison manifest. Existing Feature 010 admission continues to require one
deployment profile per run; it is not weakened to admit two profiles into one
identity.

The pair differs only in deployment profile, outer sidecar contract identity,
and measurements inherently caused by that boundary. It must have identical
source/tree, formal/ABI/schema/protocol/build/schema-set IDs, native core,
hardware allocation, toolchains, initial WAL/snapshot hashes, canonical input
bytes, request IDs and order, timer tokens/order, queue/in-flight bounds,
warm-up count, measured repetitions, offered-load schedule, paired core fault
trace, and aggregation rules. For every paired run, canonical statuses, effects,
state roots, WAL receipts/durable sequences, replay effect identities, and the
projected formal trace bytes after stutter erasure must be exact matches.

The frozen run schedule is 1,000 warm-up operations followed by 10 fixed-load
blocks. Each fixed-load block offers exactly 6,000 operations at 100 operations
per second for 60 seconds and requires all operations to complete. Ten further
60-second blocks run at saturation. Fixed-load latency percentiles pool all
60,000 completed operations per profile and use nearest-rank over integer
nanoseconds. Saturation throughput for a profile is the minimum completed count
across its 10 blocks. The p99 latency ratio is
`ceil(sidecar_p99 * 10000 / embedded_p99)`; the saturation-throughput ratio is
`floor(sidecar_min * 10000 / embedded_min)`. Arithmetic is checked and a zero
denominator, missing operation/block/metric, or overflow fails closed without
imputation.

Both profiles execute the exact native crash points `before_wal_append`,
`during_wal_append`, `after_wal_append_before_durability`,
`after_durability_before_commit`, `after_commit_before_effect_return`, and
`after_effect_copy_before_return`, plus the paired boundary after native return
and before Java send. Sidecar-only supplemental cases inject death during IPC
response framing and shared-memory publication; they are not falsely presented
as paired inputs. Every case proves exact state/effect/WAL/replay identity and
absence of any pre-durability effect. Containment records whether Java survives
native-process death; embedded is reported honestly as co-failure/no isolation.

Required integer measurements are p50/p95/p99 end-to-end and phase latency,
fixed-load and saturation throughput, restart-to-ready latency, inline ingress/
egress copy bytes, shared-memory ingress/egress bytes, separate staging-fallback
ingress/egress bytes, zero-copy eligible/hit counts, retries, duplicate
responses, stale responses, and rejected frames. Per-operation fallback copy is
the checked sum of staging-fallback ingress plus egress; selection uses the
maximum across all measured operations.

The common hard gates are exact canonical status/effect/state/WAL bytes, exact
projected traces, persist-before-expose at every paired cut, recovery before
admission, replay identity, fail-closed descriptor mismatch, framing arithmetic
and digest bounds, pre-admission-only backpressure, shared-memory ownership and
copy equivalence, stale-response fencing, nonblocking Netty loops, and complete
evidence. Sidecar additionally must keep Java alive through every native-death
injection and pass both supplemental partial-response recovery cases.

## Preregistered profile selection

Selection happens only after the immutable comparison evidence is complete:

1. Any missing/failed exactness, trace projection, bounds, backpressure,
   persist-before-expose, stale-response, restart/replay, or evidence-integrity
   gate yields `selected_profile=null`.
2. Select `ISOLATED_SIDECAR` when all hard gates pass, Java survives every
   sidecar native-death injection, sidecar p99 fixed-load latency is at most
   12,500 basis points of embedded, sidecar minimum saturation throughput is at
   least 9,000 basis points of embedded, and fallback-copy bytes are at most the
   exact preregistered 33,570,816-byte per-operation bound.
3. If sidecar is safe but misses a performance bound, `EMBEDDED_FFM` is eligible
   only when it passes all hard gates and an independently reviewed, immutable,
   premeasurement pilot-risk acceptance explicitly accepts process co-failure
   and disclaims crash isolation.
4. If both qualify, prefer `ISOLATED_SIDECAR`. Any ambiguity, post-hoc threshold,
   missing risk acceptance, or arithmetic error yields `null` and NO_GO.

This rule is frozen before measurement. This design does not apply it and does
not create the separately required risk acceptance.
