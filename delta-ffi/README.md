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
returns `DELTA_STATUS_BUFFER_TOO_SMALL` and the exact `required` size without consuming the
request, so retry is idempotent. Every exported function catches native exceptions and clears
partial output metadata before returning a stable status.

Feature 004 adds `delta_fixedpoint_shard_validate_borrowed` and
`delta_fixedpoint_shard_validate_copy`. Both invoke the production bounded DRQ1 parser, negotiate a
caller-owned output buffer and return the exact input envelope only after structural, payload-hash
and canonical INT16 checks pass. The borrowed function retains no pointer; the copy function owns a
temporary copy for the call. Context-specific admission remains in the native shard reader.

The JDK 25/26 FFM harness is test-only orchestration of this exact ABI. It neither owns consensus
logic nor turns borrowed native memory into a long-lived Java view. Transport remains outside this
library.
