# Original CurrentPointerCommand and separate pointer WAL

T044/T048/T049/T053/T057/T060; Feature000 amendment0001. **NO_GO remains.**
The reference is native commit60c692f6e391f839829dfc64e93380db54cd507b.
Exact Git blobs, their hashes and the original feature008 golden contracts are
retained in evidence/native-current-pointer/. Runtime sources are unchanged.

NativeCurrentPointer constructs all14 canonical command fields from the original
typed command. It checks the complete context, four content IDs, inclusive4MiB
JSON bound, domain-separated command ID and complete ApplyQC JSON ID. The native
store computes the command ID even though it does not persist it; this model
retains that computation. There is no invented DRW1 current-pointer command.
This is a typed-input serializer/checker, not a new arbitrary JSON byte decoder.

The five actual command/QC relationships are checked: computed QC identity,
entire context, parent checkpoint, next model/checkpoint and next optimizer.
The low-level QC shape checks retain the exact original uint32 threshold,
ordered unique labelled signers and content-ID/context rules. They do NOT require
membership in an independently configured committee, a2f+1 threshold, signatures,
arithmetic hash preimages or finalization. A kernel example with a single
unconfigured signer deliberately passes shape validation. This exposes a caller
precondition; it is not a newly demonstrated accepted end-to-end runtime exploit.

The separate fromFinalized bridge actually executes NativeApplySection.bindSection
on the original policy/state, resolves a certificate by its computed ID and
requires original finalized membership before preparing the command. Its general
lemmas recover the actual selected source, complete checked ROOT/profile lineage,
candidate identity, candidate model/optimizer and original current parent. This
is stronger than the low-level store and is NOT claimed to be performed by that
store. Native metadata, signatures, arithmetic and source provenance remain
independent obligations. No caller approval Boolean or translated whole body is
accepted by this bridge. No new concrete full-policy bridge example is claimed.

Replay is tested before the parent/height compare-and-set, but after the complete
command/QC relationship. Replay requires exact current checkpoint, optimizer and
height. A fresh update requires a different QC, the actual current parent and a
strictly greater height. General lemmas prove exact replay identity, fresh
preconditions, next-state validity and replay after advance. These local facts
alone do not prove quorum uniqueness or global public-state refinement.

## Actual separate text journal and recovery

NativePointerWal models the five-field payload and sixth checksum field:
`height|parent|checkpoint|optimizer|ApplyQC|checksum` followed by LF. SHA is over
the original payload without a domain prefix; the checksum is lowercase hex,
not a sha256 content ID. The exact unsigned decimal parser is reused. Every
complete line must pass checksum, field count, increasing height, parent
extension and content-ID shape. Recovery does not reload the ApplyQC body.

The pure byte scanner retains empty fields and the final unterminated suffix.
The native source truncates that suffix; the proposal retains its bytes in the
result so it is not mistaken for authenticated absence. This is a model of the
observed-byte computation, not a proof of filesystem truncation or crash repair.
An unknown observation rejects; it is distinct from a known empty byte string.
General history lemmas derive every parsed record and state extension, monotonic
height and valid resulting pointer. Rehashed well-formed fabricated pointer IDs
deliberately pass the low-level recovery example: checksum/shape is not
authentication. Physical integrity/completeness and initial-state provenance
must be supplied by a substantive independent observation relation.

The source crash labels are reproduced precisely. Both before_wal_append and
after_wal_append_before_durability throw BEFORE this pointer store appends.
during_wal_append durably appends the literal `truncated`, then throws.
after_durability_before_commit has the complete line but old memory and no
response; the two post-commit cuts have new memory and no response. Success
returns advanced only after the full line and memory update. Exact replay writes
nothing. The unknown cut does not return a complete outcome for a fresh update.
These pure known-cut outcomes do not prove real fsync, failure atomicity or
which bytes survived an unobserved I/O error. The generic prepared-record recovery
lemma composes fresh admission, parent/height recovery and subsequent exact replay.
The executable wrapper conditions fresh outcomes on successful line serialization
before selecting a cut. With its partial SHA adapter this is an explicit narrower
domain; native early-error/allocation ordering is not proved by that wrapper.

## Examples and checks

Original feature008 golden command and ApplyQC JSON/IDs are retained byte-exact.
The new WAL lines are explicitly SYNTHETIC source-derived examples, not captures
from a new C++ execution. Four finite real SHA samples cover the original command,
original QC, generated pointer payload and a rehashed countercheck payload.
This is not a general SHA proof or authenticated native exporter. Examples cover
fresh update, original replay, complete/torn/empty/unknown recovery, duplicate
lines, checksum substitution, CRLF, parent/height mismatch, command/QC field
substitutions, missing/duplicate signers and integer bounds. Canonical byte
construction and computed hash branches are checked in the Lean kernel.

All named definitions/theorems are axiom-audited; no new axiom, admitted proof or
native_decide is introduced. Full Lean build, Python tests, canonical regeneration,
legacy trace refinement, lint and report verification are retained in the
machine-readable evidence. No fresh native/TLC/production-mutant run is claimed.
The21TLA modules, schema, runtime, original147native witnesses and original
arithmetic positions5/6/8 remain unchanged. Legacy public roots keep their known
opaque scope; only their source semantics identity is refreshed.

## Remaining boundary

Full native arithmetic admission and recovery, joint64-variable public state,
phase/send/delivery/quorum/current refinement, arbitrary snapshots and failure/
repair, authenticated exact presence/absence, bounded codecs/SHA/exporter/physical
WAL, decimal-canonicality compatibility, contract freeze, clean offline reproduction
and independent review remain required. The generic finalized bridge is not a
proof of equality between structured TLA model symbols and native content IDs.
The native arithmetic guard stays in place. Mandatory nativeArithmeticRecoveryRefines
is still missing; no local acceptance PASS, independent attestation, BenchmarkResultQC
or GO is produced. GNU make is unavailable; scoped checks are not make formal-check.
