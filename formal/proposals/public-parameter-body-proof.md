# Checked complete PARAMETER body and native preparation composition

Tasks T044/T048/T049/T053/T057/T060; Feature000 amendment 0001. This layer
constructs and compares all fifteen public PARAMETER fields. It does not
establish complete public admission, native recovery or Formal GO. The
mandatory recovery conjunct remains missing. APPLY is explicitly rejected by
this new complete-body wrapper, rather than accepted through numeric checks.

`PublicParameterBody.lean` takes an actual `DerivedParameter`. It obtains the
scalar from that result and reruns the checked row computation at the projected
model bounds. Equality with the native numerator follows from the exact row
recurrence proved by ParameterKernel at both widths. Neither an expected
numerator nor an arithmetic-approval Boolean is supplied. General proofs retain
every coefficient, product and ordered prefix check and the scalar checked fold.
Wide native success alone does not produce public `checked=true`.

The two production range guards differ. `ABInRange` uses [-limit-1, limit],
whereas `CheckedParameterValue` uses [-AccumulatorBound, AccumulatorBound].
This projection supports configurations in which AccumulatorBound equals the
projected limit and checks the separate symmetric result range. Matching these
values to the independently bound configuration is still required; this is not
a theorem for arbitrary configurations. For limit 127, arithmetic -128 fits but
the public result guard rejects it. Rechecking ParameterKernel additionally
requires the denominator to fit the narrow accumulator. That is a stronger
representability restriction than ABParameterChecked, not an equivalent native
admission rule. Input Q/model/optimizer range checks come from the separate
source-bound NativeInputProjection; a raw row-kernel calculation is insufficient.

The native frame is checked against the actual input corpus. The selected
assignment and ordered loaded rows must match exactly. Its native denominator,
quantum, committed Q payloads and weights are retained by general lemmas. Domain
and shard aliases are looked up using the original native keys and must belong
to the configured vocabulary. The entire public authority, ISC, seed, EC, APC,
round, config, parent, schema and profiles come from PublicAuthority; no whole
translated body is supplied. Canonicality and equality compare the whole
candidate, including its authority. The previous numeric-only body lacking
authority is rejected by a general theorem, without expanding a large fixture.

`PublicParameterJoin.lean` loads this source-bound body and combines it with
PublicScalarNumbers' actual original NativePrepared witness, original all-vote
sequence and complete PublicVoteEffects before/after footprint. The known-cut
operation then calls PublicRecovery.persist and composes its actual executable
result with PublicReachability. UNKNOWN cannot enter this complete-state API.
Known unexposed records retain the existing mandatory crash/recovery handling;
the composition does not grant network delivery or quorum power. It does not
prove equality of the whole prior public durable set with the native journal:
the inherited count check is still insufficient. The public after-state is
still not connected to a complete TLA phase/send/QC/current relation.

The source codec/hash/anchor/certificate/metadata premises remain explicit.
Primitive MetadataTrust values are synthetic in fixtures. Alias maps used by
the authority, state identity and numeric interfaces still require a shared
independently authenticated configuration relation. Configured policy, seed,
norm/coefficient validity, phase deadlines, committee membership, ticket
availability, delivered quorum eligibility and full TLA admission are not
proved by a canonical body. No conversion or later aggregate is required to
construct a PARAMETER body. APPLY leaf/aggregate/output construction and its
separate conversion/mixture/optimizer guards remain open.

The three modules include 23 general helper theorems, 14 executable definitions
and 33 component/kernel examples plus five small fixture definitions. Three
examples evaluate original pinned native PARAMETER derivation/narrow checking;
the remaining arithmetic vectors separately cover endpoints, wide-versus-narrow
acceptance, coefficients at zero output, unsafe products/prefixes despite safe
final cancellation, fractions, empty/vector rows and the stronger denominator
restriction. Complete body examples reuse prior pinned authority components;
they are not a new joined full-state/native execution. Production field/range
inventories and mandatory import/audit coverage have three Python checks. No
new public trace, production mutant, native execution or authenticated export
is claimed. Original native bytes and sequences 5/6/8 remain unchanged.

Reproduce with `lake --no-cache build DeltaReduce`, then fresh `lake --no-cache
env lean DeltaReduce/PublicParameterBody.lean`, `PublicParameterJoin.lean`,
`PublicParameterBodyVectors.lean` and `AxiomAudit.lean`, from formal/proofs.
From the repository root run `python -m unittest discover -s formal/tests -v`.
Final stable-source evidence is formal/proposals/evidence/public-parameter-body.json.
General bounded decoder/hash/exporter/WAL/admission, arbitrary initial snapshots,
availability/failures/repair, contract freeze, clean offline reproduction and
independent review remain required. Docker/synthetic acceptance stays separate
SIMULATED_LOCAL; neither qualifying GO nor local PASS is issued here.
