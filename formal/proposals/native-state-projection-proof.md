# Complete current-state and APPLY-profile artifact projection

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-state-projection.json`.

`NativeStateArtifacts` computes every draft PROFILE field from the actual original
APPLY profile, checked accumulator width and an explicit quantum input. Original
domain order and rational coefficients are retained. The original native output
type supplies FULL_SIGNED_INT64; it does not supply units. Reduced bounded
fractions, positive quantum, supported width, domain order/identifiers and exact
original profile coefficient correspondence are checked. Original and draft
profile IDs use different preimages and are never equated.

`NativeStateProjection` loads the complete APPLY-profile list from the preceding
source policy, checks every canonical original profile and sorted unique IDs,
then selects the requested original profile by exact identity. That profile must
refer to the actual source accumulator proof. Its independent selection as the
configured profile is still a boundary; list membership alone is not authority.

The original pointer history is executed through NativeCurrentHistory. Its last
candidate must have the preceding preparation's schema; its recovered checkpoint
must equal the preparation's parent; its height must be strictly earlier. These
are explicit projection restrictions, not equivalence to all native admission
or recovery cases. Unknown/empty history cannot invent current vector values.

Quantum is obtained only from `UnitSource`, keyed by the complete original
context, APC, APPLY profile, accumulator and recovered pointer (both model and
optimizer IDs, QC and height). This is a named unresolved primitive metadata
source, not a native decoder or cryptographic authority. It returns only quantum,
not a whole translated profile, state, body or arithmetic approval flag. Missing
metadata rejects. The native profile, parent State and DomainAggregate formats
do not contain enough information to implement that source independently.

A general theorem and two small kernel cases exhibit this insufficiency: the
same original profile satisfies the numeric checks for two distinct positive
quanta and produces different complete draft profiles. No function of that
original profile alone can return both. The new API therefore does not silently
assume unit quantum or copy a value from a fixture.

The checker composes the full existing SCHEMA/Q/ISC/EC/PLAN/APC construction with
the computed PROFILE. MODEL and OPTIMIZER use its same actual schema reference,
quantum and exactly the current candidate's ordered values. Both complete vector
lengths must equal the source schema's coordinate count. All three new artifacts
have canonical complete encodings, 4 MiB bounds and actual store/hash/length/
decoded-payload comparisons. General theorems expose their exact bytes and
Resolves relations. The existing layout's 4096-coordinate representation bound
is retained; this is not a new native vector-width restriction.

The native current value-hash relation is inherited from checked history. A
separate named HashAdapter theorem connects it to codec.valueHash for the same
SHA function. Artifact hashes retain their different domain/preimages. No
collision resistance, concrete bounded hash/decoder implementation, source
authentication or full graph resource bound is proved here.

The raw `run` API first executes NativeVectorContext.bind on original preparation
bytes before constructing artifacts. Lower-level constructors remain conditional
components. No already supplied whole MODEL/OPTIMIZER/PROFILE translation or
whole-state equality is used. UnitSource availability still does not establish
authenticated metadata, and this stage does not construct complete Binding,
authority roots, all graph walks, historical reachability or initial snapshots.

Examples reuse a prior separately constructed native numeric profile and small
synthetic vector values. Three short encodings, with deliberately invalid short
schema IDs, are independently checked against Python canonical JSON. There is
no new positive full raw history/preparation/store execution, native capture,
authenticated unit-source example or full original/draft Binding instance.

`nativeArithmeticRecoveryRefines`, native decimal -00/-01 compatibility, original
008 captures, arbitrary-snapshot phase/QC/send/delivery/current/WAL/repair,
contract freeze, clean offline reproduction and independent review remain open.
Runtime guards, local PASS, qualifying GO and BenchmarkResultQC are unchanged.
