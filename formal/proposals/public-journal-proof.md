# Full public vote-journal projection

Candidate amendment 0001, T044/T048/T049/T057/T060. `PublicJournal.lean`
connects `NativeReplay` to the ordered per-actor public envelope journal. It
includes every intervening non-arithmetic vote and preserves the original
arithmetic sequences 5, 6 and 8. Sixteen helper theorems, twenty executable
functions and 41 kernel-decide examples are axiom-audited. This is a journal
projection layer, not the complete public execution/recovery relation.
`nativeArithmeticRecoveryRefines` remains OPEN and mandatory coverage is 44/45.

## Checked slots and native provenance

The typed action enumeration covers the nine vote actions. Canonical envelope
encoding binds action, actor, round, height, epoch, context, ordered parents and
body hash, using the existing ASCII JSON escaping and bounded identifier/hash
checks. A fresh slot must belong to the journal actor, use the exact encoded
bytes/key, have no earlier context key and allocate the next sequence from the
count of **all** prior vote slots. Duplicate context or wrong sequence rejects.

PARAMETER/APPLY admission executes `NativeReplay.resolve` and `validVote` against
the independently resolved historical native inputs. It compares the entire
native-derived envelope with the public slot, plus original context/sequence,
effect and receipt. `checkedNativeHasPreparation` derives a complete
`NativePrepared` witness. The non-arithmetic authorization callback cannot admit
an arithmetic slot, even if it always returns true. No arithmetic admission flag
or assumed result equality replaces these computations.

For other actions, existing protocol phase/QC/role authorization remains an
explicit `otherAuthorized` premise. The public witness does not carry their
native receipt, so `Slot.native` is `none`. An admission-only erasure maps those
slots to their context and sequence in the older arithmetic State type; empty
fields in that private view are not persisted, exposed or claimed as original
native bytes. `replayAdmissionKeysExact` proves that this view retains the exact
keys along accepted replay. A future full exporter bridge must supply actual
non-arithmetic native records if the contract projects them.

Replay derives a separate checked transition history by induction and retains
exact slots/order/native records. It starts from an empty journal in the pinned
example. Current advancement uses the existing checked native ApplyQC adapter;
it does not rewrite any journal slot. Initial snapshot provenance and the
authentication of that certificate remain separate obligations.

## Computed public roots and observations

Envelope IDs use the exact artifact preimage. The journal root uses the existing
`deltareduce.vote-journal-projection.draft1` domain, NUL and canonical ordered
envelope-ID list. Prefix roots are recomputed from the retained slots, never
supplied as an assumed prefix equality. SHA-256 is a named adapter, not a proved
cryptographic implementation.

The append observation matcher checks both original prefix roots/sequences. An
exposed arithmetic observation must carry the original receipt/effect; an
unexposed observation must carry neither. Null post-sequence/root cannot claim a
completed known append. These checks do not establish the provenance of the
exposure flag, stage/barrier ordering, mandatory crash after an unexposed prefix,
`SendVoteEnvelope`, QC voting power or authenticated presence/absence scans.
Missing output therefore still cannot establish that no durable record exists.
The previous arithmetic-only recovery scan model retains its separate scope.

## Executed examples and remaining work

The generator first runs the complete Python public/native refinement checker
on the source trace, including non-arithmetic votes. It then extracts all eight
validator-1 vote slots without renumbering. CONFIG, ISC, EC, APC and ROOT retain
public bytes with no fabricated native receipt; two PARAMETER records and one
APPLY record retain original native bytes at 5/6/8. The concrete case covers seven
distinct action kinds; VIEW/ABORT are typed but not exercised by this example.

Forty-one kernel examples check eight envelope encodings, nine computed prefix
roots, full eight-vote replay/current advance, all original sequences, exact
arithmetic receipts and the three original native append observations. Negative
cases reject an omitted prefix, renumbering, arithmetic authorization bypass,
invented other receipts, missing native graph, changed body/bytes/actor/context,
wrong roots, unknown tips, incorrect exposed receipt and output on an unexposed
observation. Seventeen finite hash samples bind these exact preimages to Python
SHA-256 values; they are not a general hash proof. Non-arithmetic authorization
in examples is a finite set from the independently checked source trace, not a
Lean proof of every protocol phase/QC transition. Input codec and metadata/QC
trust retain their earlier finite/synthetic scope.

Six generator tests check byte-exact reproduction and reject a removed public
event (broken history), wrong epoch/sequence and rehashed root/receipt mutations
before producing output. No native C++, physical WAL or new TLA mutant executes
in this stage. Full public event snapshots/state roots, exposure/QC lifecycle,
crash/restart and unknown scan reconstruction must still be connected to this
all-vote journal before the mandatory recovery conjunct can be claimed. Concrete
bounded decoder/hash/exporter/WAL, arbitrary snapshots/failures/repair, contract
freeze, clean offline reproduction and independent reviews remain required.

Validation logs and exact input hashes are retained in
`formal/proposals/evidence/public-journal.json`. Production runtime and frozen
demonstration refs are unchanged. This conditional proof layer is not Formal GO.
