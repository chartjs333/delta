# Native input ledger, frozen tuples and the remaining closure boundary

T044/T048/T049/T053/T057/T060; formal proposal only. No native implementation,
arithmetic admission guard, original certificate or legacy journal is changed.
Formal authority and separate SIMULATED_LOCAL acceptance remain absent.

## Actual component execution

The harness compiles complete unchanged consensus.cpp, canonical.cpp, sha256.cpp
and certificates/contracts.cpp from PR50 commit
60c692f6e391f839829dfc64e93380db54cd507b with their exact headers.
MSVC 19.29.30146 x64 C++20 /EHsc /W4 /WX is recorded from the compiler output.
Twelve native source blobs are pinned, including read-only admission source and
the previous primitive fixture sources. There is no replacement InputLedger,
Python state machine or approval callback in this execution.

Thirty-six ordered operations run against one actual native InputLedger. They
exercise reverse arrival order; identical commitment/availability retry;
equivocation; malformed and unknown IDs; missing/wrong commitment; exact leaf
coverage including missing/extra/duplicate/reversed lists; attester membership,
order and threshold; freeze/repeated freeze; historical retry; and late evidence.
Late commitments and availability have separate storage. Availability whose
commitment exists only in that late store is rejected by the active-commitment
lookup. Conflicting late evidence also rejects.

Every operation emits its actual disposition/error code and before/after values
of the native accessors: full active commitments, full active availability
proofs, full frozen rows, the frozen flag and two late-evidence counts. All match
the independently hand-authored expected component frames. Those expectations
describe these cases, not a replacement definition of TLA Next.

This diagnostic projection is **not a complete private-state snapshot**: late
payloads have no public accessor and are represented only by counts. Rejection
and retry preserve the checked accessor projection; a general native-state
stuttering/recovery theorem is not inferred. The output JSON is harness
diagnostics, not native protocol, WAL or snapshot bytes. No native reactor,
filesystem adapter, durability barrier, Java transport or authenticated exporter
runs. Generated binaries stay ignored.

## Exact frozen-list to certificate relation

After the operation sequence the harness constructs a NEW native ISC using
every actual FrozenInput row, in native order. Ticket, commitment ID and AC ID
are copied from the ledger; a separate explicit fixture mapping supplies domain
and rejects unknown tickets. Context, signer list and input_root retain their
explicit primitive fixture status. The entire native certificate ASCII, QC
content ID and pre-quorum voted-body ID match Python construction from the
expected frozen rows.

The proposal bind_frozen_isc checks the original certificate's canonical bytes,
hash and shape, then derives and compares its entire ordered tuple list. It
rejects missing, extra, duplicate, reordered or substituted rows and absent/wrong
domain metadata. It does not accept a caller-supplied whole body translation.
Authenticating the ledger observation and domain mapping remains a separate
premise; an arbitrary list and its hash cannot establish that premise.

The preceding singleton native ISC is retained byte-exact and FAILS against this
two-row ledger. It is not silently updated. The new certificate has a distinct
content ID. The old native formal semantics cc98f15a remains in its bytes;
candidate amendment authority is not inferred from this component compatibility.
Original public/native label hashes, receipts, journal roots and sequences 5/6/8
remain untouched. The mandatory mixed-prefix bridge remains incomplete.

## Confirmed limits of freeze versus production CloseInput

Read-only source: InputLedger::record_availability and freeze in consensus.cpp;
VoteAdmissionSnapshot in consensus.hpp; ISC snapshot validation/admission in
certificates/vote_admission.cpp; production CanonicalEligibleEntries, InputBody
and CloseInput in DeltaReduceCertificates.tla and HasCompleteAvailability in
DeltaReduceAvailability.tla.

The native component checks exact required leaf IDs and permitted attesters
under the supplied threshold and binds availability to an active commitment.
It neither reads artifact storage nor authenticates per-shard attestations at
freeze time. These primitive parameters and evidence need an external source.
TLA HasCompleteAvailability instead checks current available locations separately
for every shard. A flat accepted native proof cannot supply those observations
merely by enumerating a leaf list and an attester list.

freeze accepts the available subset of four permitted tickets in the retained
run: two are frozen, one has no availability, one arrives late. It has no close
policy parameter. The separate necessary ticket-coverage check accepts that
subset for OMIT_UNAVAILABLE and rejects it for ABORT_ON_INCOMPLETE. Conversely,
native freeze rejects an empty available set while TLA's OMIT_UNAVAILABLE
coverage conjunct permits empty entries. These APIs are not equivalent.
The proposal coverage helper is only that named conjunct, not production
CloseInput, full admission or an amendment to native behavior.

No input_root field or hashing operation occurs in InputLedger::freeze.
FrozenInput also has no domain, payload/content preimage, configuration, clock
or policy. The exact tuple relation therefore keeps
root_preimage_verified=false. A countercheck changes the root and rehashes a
certificate: its tuple relation still matches under the supplied new ID and
still claims no root provenance. It rejects against the original certificate ID.

ISC vote admission separately checks membership in the immutable snapshot's
closed_input_set_ids and input_set_bodies, plus native vote context. The tested
component does not produce or authenticate that snapshot. Its state_id binds
the native RoundState representation; that summary cannot automatically replace
the full 64-variable public state. The present results identify required adapter
boundaries, not an established defect in the complete production pipeline.

## What remains

The complete public/native relation must independently bind configuration,
required tickets/leaf identities, ticket-to-domain/content and commitment
preimages, actual storage locations/per-shard attestations, close policy and
snapshot origin. Native ISC context uses round_id; public ISC context uses
height/epoch. Root construction requires an exact normative/source contract,
not a new hash formula invented to match a fixture. The helper layer cannot
waive missing source fields or native old-versus-candidate semantic compatibility.

Next build a field-level adapter around the real immutable native admission
snapshot and complete public pre-state, retaining these explicit gaps. Establish
complete source provenance before enabling non-arithmetic PublicDurablePrefix
branches. CONFIG/VIEW/ABORT and phase/send/delivery/QC/current/crash/unknown
composition remain open. Unknown/incomplete outcomes retain their unresolved
status; missing response is never absence. General native adapters/WAL/admission,
arbitrary initial snapshots/availability/failures/repair, contract freeze, clean
offline reproduction and independent reviews remain mandatory.
nativeArithmeticRecoveryRefines is still missing; no GO or local PASS is issued.

## Reproduction and verification

Run python formal/scripts/generate_native_input_ledger_vectors.py. Add
--vcvars pointing at VS2019 vcvars64.bat to compile/run the exact native Git
blobs in ignored formal/build/native-input-ledger. Run unittest discovery with
-s formal/tests -p test_native_input_ledger.py.

Nine tests check all actual operation frames, original frozen-row preservation,
full certificate/tuple binding, missing/extra/reordered/forged rows and metadata,
close-policy/root counterchecks, strict complete output parsing and exact
source/harness/fixture reproduction. Boolean-versus-integer substitutions in
diagnostics reject through canonical-byte equality.

Evidence is formal/proposals/evidence/native-input-ledger.json and its sibling
directory. The fixture, harness and component result reproduce byte-exactly;
compiler log whitespace is normalized for archival. Earlier 322 generated files
and the six ISC/certificate-chain fixture/harness/results remain unchanged.
Lean/TLA/protocol schema/runtime sources are unchanged, so no new Lean/TLC proof
or production-mutant result is claimed.
