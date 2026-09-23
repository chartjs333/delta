# delta-ffi

Versioned C11 boundary for the feature-003 native runtime. The frozen public contract is
`include/delta_abi.h`; no C++ type, exception, allocator object or container crosses it.

Call `delta_runtime_descriptor` first and compare ABI, schema, protocol, formal-semantics, build
and schema-set identifiers. `delta_runtime_open` fails closed on any mismatch. Runtime ownership
is represented by an opaque `delta_runtime_t*` and ends with idempotent
`delta_runtime_release(&handle)`.

`delta_runtime_submit_borrowed` borrows input only for the synchronous call. The native side does
not retain the pointer. `delta_runtime_submit_copy` provides a bounded-copy alternative and must
produce identical canonical effects. Outputs use caller-owned buffers: a zero/short capacity call
returns `DELTA_STATUS_BUFFER_TOO_SMALL` and the exact `required` size. A submit sizing call may
perform the durable transition; the capacity retry is therefore an exact idempotent replay, not a
second transition. Every exported function catches native exceptions and clears partial output
metadata before returning a stable status.

The named `DELTA_ABI_FEATURE_SUBMIT_RECEIPT_V1` capability adds
`delta_runtime_submit_receipt_borrowed_v1` and `delta_runtime_submit_receipt_copy_v1` while keeping
the legacy submit entry points. Their versioned 48-byte wrapper returns the native
`journal_sequence` from the same `SubmitReceipt` as the canonical effect. The layout is
`struct_size:u32`, `reserved:u32`, `journal_sequence:u64`, then the 32-byte caller-owned effect
buffer. On a short-buffer result, the sequence and exact required size identify the transition
that already completed; exact live or recovered replay returns the same sequence and effect.
Invalid wrapper shapes are untouched, while a valid wrapper is reset before command validation.

The named `DELTA_ABI_FEATURE_RECORD_VOTE_V1` capability adds the durable vote path without
exporting policy structure to Java. `delta_runtime_open_with_vote_policy_v1` accepts one bounded,
canonical opaque policy blob. The borrowed/copy record operations accept an opaque canonical vote
frame and return one native-authored opaque receipt blob through a versioned 40-byte wrapper. Size
negotiation is non-mutating; only a call with adequate receipt capacity may enter native admission.
The same strict policy/receipt codec is shared with the isolated sidecar, including its frozen
transport-compatible bounds.

The startup blob is the canonically ordered native projection of the immutable `round_contract`,
not a per-call vote selector. Native open validates its closed action set, current round/config,
deadlines, validator identity, candidate ordering, and every action-specific typed parent, then
retains the decoded value for the handle lifetime. Each vote can only resolve an existing
`(action, height, view, context)` candidate with the exact body and current checkpoint; the receipt
copies its context and typed parents from that native binding. The canonical startup-policy digest
is stored with every durable vote and must match on recovery. Consequently Java can transport a
vote but cannot alter or synthesize its binding after open; changing the startup projection for a
durable journal fails recovery.

Feature 004 adds `delta_fixedpoint_shard_validate_borrowed` and
`delta_fixedpoint_shard_validate_copy`. Both invoke the production bounded DRQ1 parser, negotiate a
caller-owned output buffer and return the exact input envelope only after structural, payload-hash
and canonical INT16 checks pass. The borrowed function retains no pointer; the copy function owns a
temporary copy for the call. Context-specific admission remains in the native shard reader.

The JDK 25/26 FFM harness is test-only orchestration of this exact ABI. It neither owns consensus
logic nor turns borrowed native memory into a long-lived Java view. Transport remains outside this
library.

Feature 005 adds `delta_distribution_policy_evaluate_borrowed` and
`delta_distribution_policy_evaluate_copy`. Both execute the same production manifest/certificate
policy verifier and return one canonical typed decision effect. Semantic denials are successful
evaluations with `status=REJECT`; malformed lengths/flags still use stable ABI status codes. The
copy entry point checks attacker-controlled bounds before allocating. The borrowed entry point is
synchronous and retains neither input pointer.

Feature 008 adds `delta_certificate_inspect_borrowed` and
`delta_certificate_inspect_copy`. Both accept bounded canonical certificate bytes, verify their
content ID, formal-semantics ID, media type and domain, and return a caller-owned canonical
inspection result through size negotiation. Java receives only this verifier result; it never
reconstructs votes, quorums, robust weights, aggregate roots, Apply candidates or current-state
decisions.
