# Checked native inputs to the complete scalar arithmetic record

Tasks T044/T048/T049/T053/T057/T060; Feature000 amendment 0001. This is a
conditional input correspondence layer, not Formal GO or native execution.

`NativeInputProjection.lean` loads the authority-bound parameter frame, complete
plan and independently resolved Q artifacts. It reuses the existing frame,
schema, commitment, eligible-ticket and Q-metadata checks. Its `Corpus` does not
load the later aggregate, compute a PARAMETER result or require APPLY success.
Every assignment is retained in plan order. Every scalar cell carries its
original contribution and has a theorem extracting the actual checked
`LoadedRow`, canonical artifact reference, quantum and commitment equality.
No caller supplies an expected arithmetic-input record or an approval Boolean.

The scalar model has representability limits. Each native shard must cover
exactly one coordinate; vector shards remain valid native possibilities but
cannot enter this projection. Native weights are per assignment, whereas the
TLA inputs have one weight per ticket: all shard copies must agree exactly.
Likewise, every assignment in a domain must have the same denominator. Missing
or duplicate domain/shard/ticket matches reject, rather than picking a first
match or inserting zero. Original reduced fractions, Q cells and quanta are
retained. A positive model limit no larger than INT64_MAX bounds Q and current
model/optimizer cells; the example limit 127 is not full-width native admission.
The existing checked weight plan derives the normalized mixture LCM. These
projection checks do not establish equivalence of all TLA and native action
guards or introduce new runtime admission rules.

`PublicArithmeticInputs.lean` constructs all 23 `NativeArithmeticInputs` fields:
ticket/domain orders, ticket domain, Q table, weight numerators/denominators,
domain denominators, quantum and mixture fractions, mixture denominator, apply
quantum, current model/optimizer, momentum, learning rate, weight decay and
limit. Values come from the checked `Projected` object and bound native profile.
Separately supplied aliases only name symbols. The projected ticket/domain/shard
sets must equal the complete configured namespaces without duplicates. In
particular, the current projection does not invent Q values for configured but
noneligible tickets; such a larger ticket universe is unrepresentable here.

Table construction preserves every pair, validates shape before zipping and
checks canonical tagged encoding. The complete fixed field inventory is checked
against production `ZeroArithmeticInputs` by a syntactic tooling test. Canonical
function key order is lexicographic encoded-byte order, including sequence
indices above nine. `checkProjected` recomputes and compares the entire record.
`encodeImage` is a lower-level codec for mathematical data; acceptance there
alone is not graph authentication. The source-bound entry point is
`encodeProjected`/`checkProjected`.

The native examples reuse the original twelve-artifact finite codec and synthetic
trust. They load both input blocks and project the original Q [1,-2], quanta
1/2, model [20,-20] and optimizer [2,-2]. Separate small mathematical cases use
multiple tickets/domains and reject inconsistent weights/denominators, missing
or duplicate assignments, wrong domain, vector shape, bounds and row-count
substitution. The generated public example checks the exact complete canonical
record bytes against the separately pinned Python fixture derivation. Component
lemmas avoid expanding large dependent computations into a single kernel term.
These are Lean computations, not new native traces or production TLA mutants.

This record has no authority, parent, ISC/EC/APC, certificate or journal fields.
Their complete identity/body chain, the whole prior durable prefix, actual
phase/send/delivery/QC/current transitions and recovery composition remain open.
Aliases, codec/hash/authentication premises remain explicit; the finite mapping
is not cryptographic native identity or authenticated exporter provenance.
Unknown/incomplete observations still require the separate exact authenticated
presence/absence relation; this complete input API supplies no durability fact.
`nativeArithmeticRecoveryRefines` is not discharged. General bounded adapters,
admission, arbitrary snapshots/availability/failures/repair, contract freeze,
offline reproduction and independent review remain required before Formal GO.

Reproduce from `formal/proofs` with `lake --no-cache build DeltaReduce`, then
`lake --no-cache env lean DeltaReduce/AxiomAudit.lean`. Fresh generic checks are
`lake --no-cache env lean DeltaReduce/NativeInputProjection.lean` and
`lake --no-cache env lean DeltaReduce/PublicArithmeticInputs.lean`. From the
repository root, run `python formal/scripts/generate_public_arithmetic_inputs_lean.py`
and `python -m unittest discover -s formal/tests -v`. The mandatory audit remains
44/45 (the recovery conjunct is still missing); a successful build is not GO.
Exact final outputs and source hashes are retained in
`formal/proposals/evidence/native-input-projection.json` and its sibling directory.
