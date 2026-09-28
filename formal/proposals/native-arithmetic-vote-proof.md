# Original arithmetic vote selection and a checked mixed prefix

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-arithmetic-vote.json`.

NativeArithmeticVote defines a separate candidate arithmetic relation. It reloads
the original complete policy/snapshot, executes the original first-match candidate
selection and parent/body authority checks, and checks validator, epoch, round,
height, view, context, body identity, checkpoint, global position, readiness or
recovery, invalidation, phase, failure requests and the strict hard deadline.
The unchanged NativeSelectedVote guard still rejects both arithmetic actions;
an explicit theorem retains that rejection even when candidate selection passes.
The small Checks predicate alone is not arithmetic admission.

PARAMETER selects its actual original body from that same checked snapshot,
derives the shard ordinal from the source plan, and executes NativeVectorAuthority
against actual source Q rows and the constructed Binding. Complete common fields,
vote context, original body ID, ordered leaf coverage and canonical decimal values
are compared. Equality of both original source representations is derived from
their checked decoders, not supplied by a caller. The original body hash has its
actual native body preimage; the projected artifact hash is a different domain.
No later aggregate or APPLY result is required for this path.

APPLY recomputes NativeApply using the earlier complete finalized PARAMETER
corpus and aggregate relation, checking full original ROOT/profile identity and
all output values and native hashes. The original selected candidate ID and
ROOT-derived vote context are retained. Raw source wrappers reuse the actual
constructed authority and selected original profile with a common HashAdapter.
They reject a torn preceding current-pointer history. Binding, aggregate,
UnitSource/configured-profile and source availability/custody premises remain
independent; no cryptographic authority is inferred by selection or arithmetic.

NativeArithmeticPrefix scans the complete supplied original WAL prefix and
executes the existing guarded mixed command/vote replay from its supplied initial
snapshot. It checks that the resulting entire canonical state equals the source
preparation state; the source-loading proof binds exactly the same policy bytes.
It derives time, invalidation and global sequence from that executed prefix,
rejects an existing vote key, parses the exact next original DRW1 entry and DRC1
VOTE, binds the policy record hash, executes candidate arithmetic and constructs
the original receipt container. Every previous cached vote has an actual executed
position, canonical command/receipt/parents and suffix; a matching count alone
is insufficient. Unknown, corrupt, reordered or torn prefix observations do not
qualify. The next VOTE position counts both previous commands and votes.

This is deliberately ONE candidate arithmetic record after an original guarded
prefix. That prefix cannot already contain arithmetic votes. Command invalidation
is retained and is not cleared to manufacture an eligible history. The selected
next bytes are checked data, not evidence they were appended, fsynced or exposed.
The receipt is a mathematical container, not a returned native admission receipt.
Initial snapshots, source-loading facts and physical observations still require
independent authentication. No complete joined raw instance is asserted.

The original complete VOTE is retained, including signature ID, view, sequence
and historical native semantic ID. These fields cannot be dropped when joining
ArithmeticBinding.NativePrepared: its distinct draft JSON envelope omits several
of them and its diagnostic sequence counts only draft votes. That lossless
metadata/pre-WAL bridge, actual repeated arithmetic mixed histories, public
durable-set correspondence, phase/send/delivery/QC/current/crash/unknown/repair
and physical persist-before-expose remain OPEN. This stage neither constructs
an authenticated VoteMetadata instance nor proves nativeArithmeticRecoveryRefines.

Small kernel cases reuse original VOTE records and existing mixed journal/scanner
components, with explicit synthetic phases/times and finite SHA adapters. There
is no new fixture graph/native capture, signature proof, full native admission,
runtime edit or guard removal. Native decimal -00/-01 and full-width compatibility,
bounded concrete codec/hash/exporter resources, amendment freeze, clean offline
reproduction and independent review remain required before exact merged GO.
