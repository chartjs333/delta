# Computed native ISC proposal admission

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO**. This layer supports
one ISC candidate and arbitrary ordered proposed ISC bodies. Finalized ISC
certificates and all later graph vectors remain explicitly unsupported. It does
not discharge nativeArithmeticRecoveryRefines or authorize runtime guard changes.

## Source-bound computation

NativeInputSetBody reads every field of a proposed ISC from the complete DVPOL
tree: all seven context fields, input root and the complete ordered tuple list.
General structural proofs reconstruct the exact source tree from successful
reading and preserve every tuple and list position. The separate native voted-body
preimage uses uint64 lengths/counts in the inspected source order; it is not the
DVPOL vector encoding, native certificate JSON, a public label hash or a QC ID.
SHA is a named byte function, not a finite accepted-policy table.

The checker validates exact expected context, content-ID spelling, native ASCII
labels, positive bounded tuple count and strict (ticket, commitment) pair order.
NativeIscAdmission computes this expected context from decoded policy/state and
snapshot schema/arithmetic IDs. It checks every proposed body, including bodies
not selected by the candidate. All body IDs are recomputed and strictly ordered;
every closed-set ID must resolve to one such body. The selected candidate must
belong to that closed set and have the exact native ISC round-only context,
height/view, config and complete allowed parent record. No whole translated body,
arithmetic-approval Boolean or recovered-state equality is supplied.

Startup uses actual complete DVPOL001/DRC1 decoders, checks the original complete
state content-ID preimage, committee/local identity/role, deadlines, config sets
and optional accumulator ID. Native proposal validation synthesizes all configured
validators as signer IDs for a shape-only ISC certificate; the new general
helper derives that this 3f+1 list has at least its computed 2f+1 threshold and
fits the native threshold word. Validator labels are checked because certificate
shape validation requires them. This does not authenticate actual signatures or
assert that a quorum voted. Finalized certificate inputs reject in this subset.

Live/recovery checks keep original vote bytes, actor, epoch, coordinates,
context/body/current checkpoint and expected outer sequence. Fresh ISC requires
AVAILABLE and a tick below the hard deadline. Recovery mode can run before ready
but cannot waive invalidation or expiry. Successful admission produces a checked
vote only, not a receipt, exposure, network message or successful recovery.
Low-level typed helpers do not replace the complete fromBytes composition.

## Deliberate boundaries confirmed against native code

The native immutable snapshot is supplied authority. Native admission neither
executes InputLedger.freeze nor checks current per-shard availability or the
preimage of input_root. It accepts a changed root or tuple primitive when the
entire proposal/body-ID/closed-list/candidate is consistently rebound. Changing
the inner RoundState state_root and recomputing snapshot.state_id likewise passes
byte consistency. All these retained checks keep native_export_authenticated
and gate_eligible false. They are not demonstrated attacks on an independently
authenticated full pipeline.

Native tuple shape orders (ticket, commitment) pairs. It accepts two tuples with
the same ticket and distinct commitments in increasing order. The new Lean
countercheck preserves this actual behavior; it does not silently impose the
separate InputLedger commitment uniqueness invariant. Exact duplicate/reversed
pairs reject. Both unused valid bodies and absent proposed/finalized CONFIG
assertions can pass the actual ISC component. These facts must remain distinct
from complete production CloseInput, ledger coverage and public TLA admission.

Only closed_input_set_ids and input_set_bodies may be nonempty after the first
six primitive/config snapshot fields. A separate nonempty abort-request graph
passes native startup but rejects this supported subset. No all-policy admission
completeness is claimed. Python's existing ISC/DRC1 diagnostic readers retain
smaller 4096-item/text/byte bounds; Lean uses the checked native policy and
certificate bounds. Neither implementation resource equivalence nor general
C++ parser/admission refinement has been proved.

## Retained verification

Three mandatory Lean modules provide 28 general helpers, 137 component/kernel
proofs and 50 definitions, all 215 names axiom-audited. The original ISC policy,
state and vote are loaded using compositional encoding proofs; the complete
original fromBytes admission is composed from those checked results. Exactly
three finite SHA samples cover state, ISC context and full proposed body. Byte
preimages are compared with the pinned native-derived source values. Negatives
retain readiness, invalidation, deadline, sequence, wrong action, missing body /
closed membership, mismatched schema and tuple ordering. Kernel evaluation of
large dependent graphs was avoided by reusing body/vote/encoding lemmas; discarded
draft builds are not evidence. The final vector build completed in 102 seconds.

Fresh unchanged C++ execution covers 60 cases: 26 startup accepts / 34 rejects;
14 vote accepts / 46 rejects. The 59 supported cases exactly match the computed
Python checker. The remaining abort-graph case demonstrates the explicit subset
boundary. Twelve original units / 28 blobs at
60c692f6e391f839829dfc64e93380db54cd507b are compiled with recorded MSVC19.29.30146
strict flags. No runtime edit, guard override, Runtime handle, WAL or network
execution is newly claimed. Original native witnesses, receipts and sequences
5/6/8 stay unchanged. The original ISC1/freeze2 mixed journal is still not accepted
by the older CONFIG-only replay gate; nothing is filtered or renumbered.

Eleven tooling tests cover every retained input/outcome, whole-policy omissions,
rehashed complete-context substitutions, canonical pair versus ticket ordering,
root/source counterchecks, unsupported graph rejection, readiness/sequence,
rehashed evidence/scope substitutions and byte-exact Lean regeneration. Final
full-build/audit/regression/regeneration results are in machine evidence
formal/proposals/evidence/native-isc-admission.json and its sibling directory.
No new TLC or production mutants are claimed. Mandatory44/45 remains incomplete;
Phase0 is unfrozen and GNU make unavailable, so aggregate formal-check is not claimed.

## Next stage

Compose the computed CONFIG and ISC gates with the existing mixed WAL fold using
a checked typed admission result. Reuse the actual original ISC1/freeze2 journal
and both original receipts, without an approval callback or a body-lookup table.
Historical lookup must precede freshness checks; original outer sequence,
policy identity, command outputs, caches and snapshot-position state must remain.
Then extend finalized ISC/seed/EC/APC and other graph admission, preserving actual
body versus QC identities. Independent snapshot/ledger/availability/root origin
remains mandatory before claiming a complete public-state relation.

DRS1 decoding, authenticated initialization/physical scan completeness, unknown
outcomes/repair/arbitrary failures, full public phase/send/delivery/QC/current
composition, nativeArithmeticRecoveryRefines, contract freeze, clean offline
reproduction and independent reviews remain open. No local acceptance PASS or GO.
