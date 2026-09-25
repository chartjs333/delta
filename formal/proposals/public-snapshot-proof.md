# Existing native snapshot bytes and first-event binding

Candidate amendment 0001; T044/T048/T049/T053/T054/T056/T057/T060.
`PublicSnapshot.lean` checks the existing `nativeSnapshot` v1 format against
the independently selected native inputs and the reachable all-vote machine.
Thirteen general helper theorems and fifteen functions are axiom-audited.
This stage does not discharge `nativeArithmeticRecoveryRefines` (44/45 remains).

## Exact snapshot boundary

The encoder produces the existing sorted ASCII canonical JSON keys and complete
native anchor, including optional aggregate ID/length, authority reference,
parent/current model/optimizer identities, role/recovery metadata, round/view/
epoch/deadline/time, contract, original pre-state root and prospective sequence.
It uses the existing ASCII string escaping and full lowercase content IDs.
The domain-separated hash preimage is exactly
`deltareduce.native-snapshot-witness.v1`, NUL, canonical snapshot bytes.
No new C ABI, WAL layout or public snapshot schema is introduced.

The caller supplies a snapshot ID; a separately supplied registry resolves its
exported bytes and typed fields. Producer provenance is an explicit `ExportTrust`
predicate, independent of the command and of digest equality. Loading checks
canonical re-encoding against all supplied bytes, digest identity, nonempty
length bounded by 4 MiB and the 32-byte content ID. A decoded typed export is an
adapter input: this does not prove a general parser, allocation/item/depth bounds,
SHA-256, or genuine exporter authentication.

First binding re-executes `PublicJournal.checkSlot` and `NativeReplay.resolve`.
It compares the exported anchor and all native vote metadata with the resolver's
independently authenticated original input. The snapshot's contract, prior root,
prospective sequence and finalized parent must match the separate trace context,
event and known journal. It compares the full event envelope with the expected
native envelope fields/body hash, exact command, validator role, view and logical
time. The checked slot retains the actual recomputed native arithmetic result,
effect, receipt and sequence. Arithmetic cannot use other-action authorization.

The trace contract ID and finalized-parent set are supplied by the public
context adapter; this module does not prove the entire contract's coordinate
projection or how its parent set was certified. The earlier Python checker
continues validating that broader fixture context.

Accepted/finalized first votes report the original prospective sequence.
Unknown append reports FAULT with a null sequence and an unchanged public root;
it never claims the old tip as a known post-write sequence. `executeFirst`
performs the existing persistence operation only after successful binding.
Successful execution composes with `PublicReachability` and therefore derives
exact journal replay. Unknown execution preserves the known prefix and pending
candidate. This module is a first-event projection, not a complete event decoder
or a replacement for the full durability-observation checker. It does not apply
fresh-time/pre-state checks to historical retries; those retain the previous
recovery layer's original-record semantics.

## Proof and example scope

Fifty-two kernel-decide cases compare the exact original three snapshots and
hash preimages with independently generated Python bytes, retain arithmetic
sequences 5/6/8, and check native binding, original first execution and unknown
stutter. Rejections cover changed prior root/view/time/sequence/command/role,
missing snapshot/finalized parent, wrong contract, noncanonical bytes, and
unknown outcomes falsely claiming a known sequence or state change. Four
mutated typed snapshots are re-encoded and assigned synthetic matching hashes:
they load but their changed sequence/current/model metadata/projection is
rejected against the independent native input. One additional composition
theorem derives reachability of any successful first execution from the proved
four-vote prefix. The example SHA adapter has only three actual snapshot
preimage samples; mutated examples use an explicitly synthetic hash adapter.

Seven Python tests check byte-exact regeneration, five rehashed snapshot
substitutions rejected before output, and the root limitation below. Existing
whole-trace refinement validation runs before vector generation. No new native
or public trace, production mutant, physical crash, exporter attestation or
native runtime execution is claimed. All provenance predicates in examples
are synthetic; old finite graph/hash/native/QC adapters retain their scope.

## Public root gap found during this stage

`generate_trace_fixtures.trace` currently hashes `trace_id:state:index` labels.
`validate_trace_document` checks state-root adjacency, not a hash of complete
public state. Some durability branches additionally check required stutters.
An explicit countercheck replaces the initial root and first event's prior root,
preserving adjacency; the current checker still accepts that trace. This is
recorded as **FULL_PUBLIC_STATE_ROOT_NOT_VERIFIED**, never semantic equivalence
or full refinement. Exact snapshot identity only binds an opaque root to its
producer's original snapshot; it does not establish that root's state preimage.

Next work must define and bind the full canonical projected state and check
allowed public actions, including non-arithmetic phase/QC rules and global
SendVoteEnvelope/quorum eligibility. The per-actor journal or sent list must not
be relabeled as that full state. Concrete native decoder/hash/exporter/WAL,
availability changes, arbitrary failures/snapshots/repair, contract freeze,
clean offline reproduction and independent reviews also remain required.

Evidence: `formal/proposals/evidence/public-snapshot.json`. Formal status stays
NO_GO; self-review is not independent attestation and runtime guards stay intact.
