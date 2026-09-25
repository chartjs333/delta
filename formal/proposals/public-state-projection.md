# Complete public state identity and checked replay (candidate)

T009/T011/T012/T044/T048/T049/T053/T054/T056/T057/T060; amendment 0001.
This candidate is a new formal evidence profile, not a native wire/WAL format.
It does not retroactively upgrade the existing public trace v1 fixtures.

## Identity boundary

`deltareduce.full-public-state.v1-candidate` includes **every** variable in
`DeltaReduceTypes.ProtocolVariables`, including transport multiplicities,
delivered votes, durable and volatile votes, per-actor recovery/sequence,
availability/repair, all intermediate certificates, pointer recovery, timeout,
partition, phase and crash coverage. No field is optional, summarized or erased.
`DeltaReducePublicState.tla` explicitly maps those variables to record fields.
The tooling checks declaration, tuple and record coverage independently and
rejects omissions/extra fields. A future model variable requires profile review.

The JSON preimage contains `profile`, `model` and `variables`. The model identity
binds the formal semantics ID, normalized source hashes of the nine production
TLA modules and the public-state projection module, and the exact bytes of the
registered replay configuration. That configuration includes every production
constant assignment/override and has no symmetry, constraint, VIEW or overriding
Init/Next. The initial supported configuration is deliberately finite and pinned;
it is not an arbitrary-config parser or a native environment description.

TLA values have one tagged representation: `["bool", boolean]`,
`["int", canonical_decimal_string]`, `["str", ASCII_printable_string]`,
`["model", configured_model_value_name]`, `["set", ordered_values]`, or
`["fun", ordered_key_value_pairs]`. Records and sequences **are functions**:
record keys are strings; sequence keys are integers 1..n. Separate record/sequence
tags would introduce aliases and are forbidden. Empty functions differ from
empty sets. Model values differ from same-spelled strings. Sets and function
domains are sorted by canonical value bytes; duplicates and noncanonical order
are rejected. No floats, null, ellipsis, opaque fingerprint or unsupported value
kind stands for missing state. Unsupported values fail, they are never omitted.
ASCII strings are a deliberate candidate restriction, not a claim about all
possible native data. Hash identities are byte identities; cryptographic
collision resistance remains an assumption.

Canonical JSON uses the existing sorted-key/no-whitespace profile. The state ID
is SHA-256 of ASCII `deltareduce.full-public-state.v1-candidate`, NUL, and those
canonical JSON bytes. Each observation supplies the full preimage and exact ID;
the verifier recomputes both. Resource bounds limit the proposal tooling, not
production parser or arithmetic admission. Sequence order is never set order.

## Allowed action relation

Full-state identity alone does not establish refinement. A separate generated
TLC replay binds every unprimed/primed variable to the two complete states and
evaluates the **existing production** `Init`, `TypeOK`, `[Next]_ProtocolVariables`
and the selected production action. It does not implement a second Python Next.
The replay checks a single explicit candidate path, not all reachable behavior.
The initial state must exist exactly once and satisfy Init; action labels come
from a closed tested vocabulary. Stutter requires equality of all variables.
Implicit terminal stuttering introduces no protocol change. A replay counter is only
a harness variable; it is not hashed as protocol state. No supplied equality,
action-approval Boolean or finite action-membership lookup establishes legality.

The first path exercises RoundConfig proposal, all three honest persist/send/
delivery paths, crash/restart/recovery before exposure, QC formation and stutter.
This tests global delivered-vote quorum power in the actual model for that path.
It does not yet cover the complete arithmetic public event trace. Deliberately
rehashed invalid full states must fail the TLA relation, even with valid roots.

## Remaining integration obligations

Native exporter provenance and abstraction of each of these variables are still
missing. RoundState's summary fields cannot substitute for this record. A native
exporter must separately bind original snapshots, immutable configuration,
action arguments, canonical artifact bytes, actor/context/epoch/sequence, stages,
receipt/effect and exact durable observations to this state/action relation.
The existing `PublicReachability`/`PublicSnapshot` Lean layer has not yet been
composed with this full-state replay. No new Lean mandatory theorem is claimed.

An unresolved append is an **incomplete observation**, not a complete native
state. It cannot be filled with the last known journal and called this profile.
Presence/absence requires authenticated scans; corrupt/ambiguous scans remain
blocked. A complete retrospective projection must retain original records.
All vote kinds, arithmetic/current advancement, arbitrary initial snapshots,
failures/repair, bounded decoders/hash/WAL adapters, offline reproduction,
contract freeze and independent review remain open. Status: NO_GO; the remaining
`nativeArithmeticRecoveryRefines` obligation is not discharged by this stage.
