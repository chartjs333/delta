# Checked replay sublayer for native arithmetic recovery

Candidate amendment 0001, T044/T048/T049/T057/T060. `RecoveryKernel.lean`
implements sequential replay and proves soundness and completeness against an
independent inductive transition/history relation. It is a necessary sublayer,
not `nativeArithmeticRecoveryRefines`: mandatory coverage remains 44/45. The
native bridge, production adapters, contract freeze and independent review are
still required; FormalVerificationReport remains NO_GO.

## What is proved

Each vote record contains the entire formal context key, canonical command,
authority and body bytes, original receipt/effect bytes and original sequence.
The checked replay step requires admission at the then-current parent, next
sequence exactly equal to the existing vote count plus one, no previous record
with that key, and exact effect/receipt equality with the encoding adapter.
Duplicate keys are rejected even when all bytes match; retries use a distinct
lookup path and never append. The sequence is the diagnostic vote sequence, not
a physical WAL offset or a count of checkpoint entries.

`replaySound` constructs the entire accepted history by induction on journal
entries. `replayComplete` proves the converse. `replayExactRecords` proves that
replay preserves every original complete record in its original order. The
append and lookup lemmas establish `originalRecordRecovered`: an accepted
prefix, first persisted vote and any accepted suffix restore that exact record,
including receipt/effect/sequence. No recovered-state equality, assumed record
uniqueness, or equality of two pure function calls is used as the conclusion's
premise. The prefix/suffix hypotheses are successful executions of the checked
replay algorithm, rather than an assumed snapshot equivalence.

Votes preserve all checkpoint/model/optimizer pointers. A checkpoint entry must
carry an authenticated certificate and either match the current parent for a
compare-and-set or match the already installed next state for idempotent replay.
Historical receipt lookup does not readmit the old parent against that newer
state. Exact canonical command retry returns the original complete record;
different bytes conflict. Crashed, recovering, unknown and blocked modes cannot
retry. Pre-WAL preparation rejects failed admission without producing a pending
record. A pending record is internal data, not an outbound effect. Exposure
requires ready mode, committed stage and the exact record in the verified state.

For one interrupted append, scan authentication binds the initial state, prior
prefix, pending record and decoded scan claim. Even an authenticated scan must
match exactly either the prior prefix plus the complete pending record, or the
prior prefix under an explicit verified-absence claim. Both successful branches
run the actual replay algorithm. An ordinary complete scan of just the old
prefix cannot establish absence. Incomplete scans retain unknown sequence;
corrupt and ambiguous scans remain blocked. Continuing a blocked recovery cannot
silently make it ready. An absent reply is never an input proving absence.

## Explicit boundaries and remaining work

`Adapter.admitted` is a Boolean semantic-admission parameter. It must be connected
to independently anchored `NativeBinding` extraction, full PARAMETER/APPLY body
comparison, context/role/time/current-parent checks and public witness projection.
This stage does not supply that bridge. `Adapter.effect` and `Adapter.receipt`
are encoding functions; their agreement with native or public encoders is not a
generic theorem here. Certificate and scan authenticators are named parameters,
not cryptographic proofs. Complete physical scan coverage, native exporter
provenance and crash execution remain outside this mathematical layer.

The kernel is single-writer, sequential and has one unknown append at a time.
It does not define new production statuses or a repair/truncation permission.
Examples replay from the empty journal and explicit initial current pointers.
An arbitrary supplied initial state is not thereby certified as a valid native
snapshot. Partial byte decoding, torn-sector detection, atomicity/fsync, resource
limits, arbitrary failures, initial snapshot validation and repair remain open.
The stage/exposure predicate is not itself a proof of physical durability or
the full production persistence state machine. Those are mandatory refinement
work after the binding bridge, not implications of these helper theorems.

## Pinned examples and reproduction

`generate_recovery_kernel_vectors.py` first runs the existing native arithmetic
oracle and diagnostic durability checker against the separately hashed evidence
container. It emits 37 Lean kernel-decide examples and exact diagnostic bytes
for two PARAMETER records (original sequences 5 and 6) and one APPLY record
(sequence 8) from `durability-after-current.json`.

The other five vote slots preserve their fixture envelope/context and sequence,
but use synthetic envelope-as-command and empty receipt/effect values: the
public witness does not define receipt projections for those actions. They are
not represented as native receipt bytes. The ApplyQC entry uses the synthetic
public advance-event encoding, not a production certificate encoder. Lean uses
a finite admitted-data/receipt table and synthetic certificate/scan trust. Python
checks the anchored arithmetic before generation; the Lean example does not
replace the missing general native admission proof.

Examples cover full replay/current advance, original receipt lookup, stale
first-parent rejection, mismatch/missing authority, duplicate/sequence/receipt/
effect mutations, certificate authentication and parent checks, every exposure
stage, mode fencing, unacknowledged presence, explicit absence, truncation,
ordinary-prefix ambiguity, altered surviving bytes, unknown sequence and blocked
scan retention. Five tooling tests require byte-exact regeneration and reject
rehashed receipt/sequence mutations, missing outputs and missing optimizer
artifacts before any Lean/evidence output is emitted. These are kernel examples
and tooling counterchecks, not production TLA mutants or native C++ executions.

Reproduce the generator, full Lean build, fresh RecoveryKernel/RecoveryKernelVectors
checks, axiom audit and `check_lean_evidence.py`. The audit must still fail for the
missing mandatory `nativeArithmeticRecoveryRefines`, regardless of helper success.
