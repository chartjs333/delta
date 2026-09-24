# Certified PARAMETER conversion and schema placement

Candidate amendment 0001, T044/T048/T049/T057/T060. The mandatory project now
contains the conditional `nativeParameterConversionSound` conjunct. Mandatory
coverage advances to 43/45; `nativeApplyResultUnique` and
`nativeArithmeticRecoveryRefines` remain missing. Formal status stays NO_GO.

## Checked computation, not assumed expected equality

`deriveParameterCorpus` loads the authority's immutable frame and traverses the
full ordered domain-by-shard key matrix. For each key it executes the checked
body extractor from the preceding stage. `ParametersFor` proves exact entry
order and equality of every entry's resolved frame. No observed subset chooses
the expected keys; invalid input rows cannot be supplied separately.

`loadCertifiedParameters` loads the aggregate at the native anchor's reference.
After byte/hash/length/type checks it compares the **whole** decoded aggregate
against the independently derived ordered bodies and authority ID. The
successful return carries a constructed `Resolves` proof and the named
certificate-authentication premise from `Binding`. Body context, denominator,
numerators and all leaf IDs participate in equality. Equivalent fractions,
reordered/duplicate/subset bodies and self-consistently rehashed wrong results
do not become accepted aliases. Production cryptographic verification remains
the explicit trust-instantiation obligation.

Only after that complete check does conversion execute. Every numerator uses
the original assignment denominator and Q quantum and the native profile's
apply quantum. The existing arithmetic kernel checks both ordered numerator
products and denominator products and rounds once per domain coordinate.
`convertedParameterSound` proves the conversion trace, exact rounded values and
unchanged shard length. **INT128 accumulation does not widen output:**
`convertParameterValues` separately checks FULL_SIGNED_INT64, including its
asymmetric minimum. PARAMETER computation itself still succeeds when a later
conversion would overflow; no new PARAMETER admission condition is introduced.

`placeValues` attaches the native schema offset to each converted coordinate.
Induction proves that every cell comes from exactly its source list index and
offset. Domain assembly walks schema coordinates in order and requires one
matching cell at every position. Missing or duplicate cells reject; there is no
padding or last-writer-wins behavior. `nativePlacementSound` proves every output
coordinate's value and source shard/local index, plus singleton matching-cell
coverage. `conversionCellsWithinSchema` derives from the corpus key matrix,
partition range checks and actual converted length that no out-of-schema cell
or undeclared domain exists. Source arrival order cannot define vector order.

## Theorem and assumptions

`NativeConversionSound` records the independently resolved frame and validated
profile, authenticated exact aggregate bytes, all ordered source keys, row
bindings, arithmetic prefix safety, conversion products/rounding, INT64 output,
complete domain/schema placement and absence of extra cells. The theorem for a
successful `deriveNativeConversion` returns these facts. Its short final proof
uses the preceding general induction and arithmetic theorems. Proof-carrying
return structures make invalid results unconstructible without a proof;
no untrusted expected-result, valid-row or uniqueness hypothesis is added.

This is soundness of the checked mathematical pipeline under the same explicit
codec/hash/native-anchor/recovery/certificate premises as the graph theorem.
It is not a general ASCII/decimal/SHA implementation proof, canonical native body
serialization, cryptographic validation or physical native execution. Parser
resource limits and completeness, availability/repair, role/current/time vote
admission, snapshots/WAL/receipt encoding and native recovery refinement remain
mandatory. In particular, these proofs do not yet establish that a production
native adapter accepts every valid native input. APPLY/model/optimizer updates
are not part of this conjunct. A successful build does not authorize runtime
guard removal or Feature010 qualification.

## Vectors and review scope

The twelve original exact artifact byte strings now instantiate successful
certified-body loading and the entire conversion/placement pipeline, compared
with the separately executed Python proposal oracle. Seventeen new Lean
examples cover five successes and twelve rejections: aggregate subset/duplicate/
order/authority/denominator alias/context/leaves/numerators, schema-order assembly,
missing/duplicate/wrong-domain cells, INT128-to-INT64 output overflow, signed
minimum and a valid PARAMETER whose conversion fails. Existing arithmetic and
body-extraction vectors remain in the same project.

Three new Python generator tests change and rehash certified numerators,
equivalent fractions and ordering, update the aggregate anchor, and require
rejection before any Lean output is written. These are synthetic-source tooling
checks. The aggregate guard and placement examples exercise mathematical
boundaries, not new native C++ executions or TLA production mutants.

The new helpers, proof-producing functions, main theorem and all new examples
are audited in `AxiomAudit.lean`. Allowed library axioms are `propext`,
`Quot.sound` and `Classical.choice`; semantic trust premises are separately
named, not silently replaced by those library axioms. Self-review is not an
independent attestation.

Regenerate with `generate_trace_fixtures.py`, `generate_native_graph_vectors.py`
and `generate_parameter_kernel_vectors.py`, then run the full Lean build, fresh
kernel/axiom checks, tooling/oracle tests and public refinement checks. The
mandatory Lean evidence checker must fail only for the two remaining PO-AB1
targets. Contract freeze and clean offline reproduction/review gates remain
open, so the new source-bound report must remain NO_GO.
