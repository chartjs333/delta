# Native-derived pre-WAL records and diagnostic bytes

Candidate amendment 0001, T044/T048/T049/T057/T060. This stage connects native
arithmetic extraction to complete internal vote records. It adds fourteen
general helper theorems in `ArithmeticBinding.lean`; it does not yet discharge
`nativeArithmeticRecoveryRefines`. The mandatory count remains 44/45 and Formal
GO remains blocked. No production runtime or arithmetic guard is changed.

## Arithmetic origin and preparation

`loadedRowUnique` and `rowsBoundUnique` compare independently resolved Q bytes
at the same authenticated references. `derivedParameterBodyUnique` then derives
equal ordered inputs and complete PARAMETER bodies from the checked authority,
frame, assignment, partition and integer computation. Neither assumed row/result
equality nor a later AggregateRootQC is needed for first PARAMETER admission.

`VoteSource` selects the actual `deriveParameter` or `deriveNativeApply` program.
`ExpectedNativeVote` retains the checked source, complete encoded body, projected
APC/aggregate reference, PARAMETER context check, actor/context key and full vote
envelope. The command contains the fixed action tag and that complete body.
Independent-store identity is proved for body, command, context, envelope,
effect and the complete data record. The admitted command does not supply
arithmetic inputs, expected outputs or a substitute authority.

`prepareNativeFirst` checks native readiness, validator role, sampled logical
time before the hard deadline, current checkpoint/model/optimizer, native integer
ranges and metadata/schema identifier bounds. It then checks absence of the
formal actor/context key, exact canonical request equality and the request byte
bound, and allocates sequence `state.votes.length + 1`. The original sequence is
not read from the request. A previous record makes this first-admission path
reject; historical retry must use the recovery lookup path, without re-admitting
the old parent. Failed fresh-state checks run before arithmetic extraction.

`NativePrepared` carries all these checks and the computed receipt encoding.
`nativePreparedIdentity`, `nativePreparedFresh` and `nativePreparedRecordUnique`
prove exact record fields and agreement across independent stores. General
rejection helpers cover wrong bytes, stale/unready state and an existing context.
`prepareNativeAvailable` returns no record when the independently checked graph
is absent, and every successful result carries a real `NativePrepared` derivation.
The record is internal pre-WAL data; constructing its receipt bytes does not
authorize exposing them before durability and commit.

## Exact diagnostic encoding

The envelope writes sorted keys for action, actor, body hash, height, parent
certificate, round, epoch and formal context. The effect writes `projection_version`
and the envelope. The receipt writes command/effect IDs, version, original sequence
and the same envelope. IDs use lowercase hexadecimal, numbers use decimal and
separators are exact. These are the draft public evidence encodings in
`native_durability_witness.py`, not a production C ABI or physical WAL format.

`jsonASCII` supports the whole ASCII domain with JSON escaping, including quotes,
backslashes, control characters and DEL; it does not narrow metadata to the
arithmetic identifier grammar. Unicode is rejected under the existing ASCII
witness profile. The native actor/context bounds remain 1..256; authority round,
epoch and parent use the existing 1..128 arithmetic identifier grammar.
Receipt sequences match the witness snapshot's positive signed-64 range.
The existing `HashAdapter` premises bind exact artifact-domain command/effect
preimages; SHA-256 itself is not implemented or proved here.

## What remains open

`NativeVoteTrust.authenticated` must bind the entire metadata projection to the
independently exported native event snapshot. Actual authentication and proving
that time/view/epoch/role metadata belongs to the current call are external
refinement obligations, not consequences of a caller setting a Boolean. Graph
`Binding` retains its named canonical-codec/hash/anchor/recovery/certificate
premises. A concrete native graph loader, bounded decoder, hash adapter, all
allocation/resource limits and admission completeness remain open.

The replay kernel's general `Adapter.admitted`, receipt functions and authenticated
scan/QC relation have not yet been instantiated from this proof-producing path.
An arbitrary supplied prefix is not thereby proved to be the recovered native
history. Full record provenance, old snapshot replay, current-advance evidence,
unknown durability outcomes and initial prefix/snapshot/repair semantics still
need the general recovery bridge. Thus these preparation helpers are not the
mandatory recovery conjunct, nor a claim of physical persist-before-expose.

## Executed examples

`NativeVoteVectors.lean` contains 46 kernel-decide examples. The two PARAMETER
preparations use a binding whose aggregate anchor is `none`; the APPLY preparation
uses the anchored certified aggregate. All three execute native graph arithmetic
and construct full records equal to the original pinned diagnostic records at
sequences 5, 6 and 8. Each resulting record is also consumed by the checked replay
step. Negative examples cover canonical command changes, all three current
pointers, deadline, recovery/role, duplicates, missing authority, wrong context/
projection, malformed certificate/hash IDs, metadata bounds and sequence bounds.
The full 128-character ASCII alphabet and maximum receipt sequence match Python.

Input decoding still covers twelve pinned artifact strings. The finite hash
table now includes the derived APPLY body and diagnostic command/effect samples,
as well as PARAMETER bodies. These samples do not expand the accepted input
decoder/collision proof or prove a general SHA implementation. Metadata trust
is synthetic. The replay example still uses the finite adapter and explicitly
synthetic non-arithmetic prefix slots from the earlier recovery vectors; it does
not establish the missing general native replay admission bridge.

The generator validates the native/durability evidence before emitting examples.
Five tooling tests cover exact regeneration and rejected receipt/body mutations,
wrong role and missing current optimizer. They are tooling/kernel checks, not
new production TLA mutants or native C++ executions. Run the full Lean build,
fresh native body/vector checks, axiom audit, tooling/oracle/refinement checks and
byte-exact regeneration. The obligation checker must still report the missing
`nativeArithmeticRecoveryRefines`, and the complete report must remain NO_GO.
