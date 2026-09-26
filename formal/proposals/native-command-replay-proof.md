# Computed command replay and historical receipts (candidate)

T044/T048/T049/T053/T057/T060; amendment 0001. NO_GO.

NativeCommandReplay derives a command journal from parsed configured initial
state, starting at outer WAL sequence one and an empty request cache. Each
entry must be a command at the next exact position. It decodes the original
command, reuses NativeTransition to compute all three stored outputs and
compares those exact bytes. Duplicate request IDs fail before insertion. No
caller-provided state equality, transition callback or finite admission table
defines the accepted history.

General induction extracts actual executable step histories, exact sequence
and cache lengths, preservation of the prior cache, unique request IDs and
the original entry/command/computation behind every cached receipt. Cached
receipts retain the original state/effect/inner-WAL bytes, computed IDs and
outer WAL sequence, with replay=false. The state counter is separate from the
outer WAL sequence. These proofs do not erase or renumber any intervening vote.
This API explicitly rejects votes, including the previously recorded native
ISC(1)/freeze(2) complete journal. Its single-command sequence-one Lean example
is a separate mathematical history reusing the old command bytes; the original
mixed fixture remains unchanged. A separate one-step example retains sequence2.

The chronological proof list represents unique keyed cache contents, not the
native std::map storage or iteration order. No canonical serialization of the
cache or general equivalence of native map implementation is asserted.

When supplied with an initial clock, the command path checks nondecreasing
logical time and sets authority invalidation after a command. Without a policy
clock, the runtime does not apply those updates. The Option Nat argument is
the primitive initial tick/presence of a separately validated startup policy,
not a policy validator. Its uint64 bound is checked. General DVPOL001 decoding,
native policy validity, independent startup provenance and vote admission
remain open. It cannot authorize a vote.

Historical retry decodes the original request and computes its command ID,
looks up the saved request and compares the ID before returning the original
receipt with replay=true. It has no fresh phase/time/current-state test and
performs no append. A general theorem proves independence from all fields
except the saved request cache. Native conflict is by command ID: byte equality
does not follow without the named hash assumptions. SHA remains an explicit
function, with finite actual preimages reused in kernel examples.

Optional snapshot metadata is typed here, with its state bytes parsed by the
existing concrete state decoder. A positive snapshot position must occur and
its exact state bytes must equal the state actually replayed at that entry.
The final state always comes from initial state plus journal execution. The
general positive-snapshot theorem extracts that exact entry from history.
Native Runtime::recover initializes matched=true for sequence zero: such a
snapshot is still parsed but need not equal the initial or final state. The
model and counterexamples preserve that fact rather than inventing a stronger
native check. General DRS1 byte decoding/checksum and physical snapshot identity
are not proved by this typed snapshot relation.

recoverObserved composes the actual DRW1 observed-byte scanner with replay,
requiring no torn suffix. This is a deliberately incomplete observation API:
it grants no truncation permission and does not reproduce native torn-tail
repair. A byte-complete supplied buffer is not proof of a complete physical
file, authenticated absence, current file identity or successful durability.
Missing responses, unknown outcomes and incomplete/corrupt/ambiguous scans do
not confer readiness, receipt exposure, network send or quorum power.

A fresh isolated Windows C++ harness compiled the twelve unchanged native
translation units already pinned by native-policy-wal, including runtime,
transition, vote policy and WAL. Its 22 cases have 11 successes and 11 failures.
A live three-command freeze/view/abort journal uses exact outer sequences1/2/3,
stores a snapshot at2 and retries the first request after advancement/reopen.
Every returned receipt field, final state and outer sequence is compared with
a separate bounded Python replay. The original native source and fixture graph
remain pinned; no native guard, deployment or demonstration is changed.

Negative cases cover request conflict, backwards time, wrong/ahead snapshot,
changed state/effects/inner-WAL, reordered/gapped sequence and duplicate request.
The empty effect/record native cases reject at WAL structural validation; Python
tests additionally rehash nonempty substituted sections to exercise computed
output rejection. Sequence-zero snapshots with different valid states and a
submit-only old-time command explicitly retain the native scope boundaries.
This is local Runtime/WAL execution, not an OS power-loss campaign, production
mutant suite, native arithmetic execution, independent exporter authentication
or general C++ implementation proof. Lean examples and native cases are
separately identified; no new full mixed-public trace is claimed.

Next derive the actual native policy reader and admission/recovery relation
for intervening votes, then compose it with these command/cache/snapshot steps
without an arbitrary vote callback. Connect all public protocol states/actions,
availability, CloseInput, phase/send/delivery/QC/current and independently bound
configuration/exporter provenance. The full nativeArithmeticRecoveryRefines,
arbitrary failures/repair, contract freeze, offline reproduction, independent
reviews and runtime/profile/GPU/Docker acceptance remain mandatory. This
conditional command sublayer does not issue Formal GO or local acceptance PASS.
