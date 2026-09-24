# Checked native PARAMETER body extraction

Candidate amendment 0001, T044/T048/T049/T057/T060. Formal status remains NO_GO.
This checkpoint connects the typed byte graph to the checked PARAMETER kernel.
It does not register the complete `nativeParameterConversionSound` obligation.

`ArithmeticBinding.lean` now implements a checked mathematical extractor.
`loadPayload` reads the exact reference from a store and checks content hash,
length, canonicality, decoded type and typed outgoing edges. Its successful
result carries a constructed `Resolves` proof. `loadParameterFrame` resolves the
schema, plan and ISC/EC/APC projections at the authority's own references and
retains the source bytes in its origin relation. Neither loader accepts supplied
rows or a claimed expected result.

The frame check establishes ordered unique coordinates/shards/domains, exact
schema coverage, supported arithmetic profile and current-vector lengths/ranges.
It checks certificate parent references, plan schema/profile references, ordered
eligible membership, exact plan ticket order, committed leaf coverage and domain
agreement. The assignment matrix must be exactly the ordered domain-by-shard
product, with distinct vote contexts and valid denominators/quanta. Every schema
coordinate has exactly one covering shard; range checks exclude extra positions.

For the selected assignment, contribution ticket IDs must equal the eligible
domain ticket list in order. Each row resolves its Q bytes at the plan reference
and checks the full commitment reference, ticket, domain, shard, schema, quantum
and length. Weights come directly from the original contribution. Recursive
`RowsBound` preserves this one-to-one positional relation; `rowsBoundAt` exhibits
the actual source contribution and Q artifact for any extracted row, and
`rowsBoundLength` excludes padding, omission and truncation.

`deriveParameter` executes these checks and then the existing `ParameterKernel`.
It derives the unreduced numerator vector using the plan's specific denominator,
and constructs every field of the typed expected body: kind, authority ID,
context, domain/shard, denominator, numerators and ordered input-leaf IDs.
`derivedParameterBodySound` connects that body to exact eligible coverage,
unchanged vector shape, the mathematical ordered recurrence and every checked
coefficient/product/prefix. `derivedParameterCoordinateRefines` connects each
present output coordinate to the checked scalar accumulator. No equality to a
caller-provided expected result is assumed.

## Exact scope and remaining obligations

The extractor takes a `Binding`, whose codec/hash/anchor/recovery/certificate
premises are explicitly documented in `native-graph-proof.md`. The proof-carrying
rows and validation witnesses are constructed by the checked functions; they are
not additional unauthenticated command fields. `Binding` itself still needs its
production native instantiation. The actual decoder's resource bounds, decimal
encoding, content-ID spelling, snapshot provenance, role/time/current admission
checks and physical WAL are outside this helper layer. List proofs are general;
they do not establish the concrete decoder's maximum input sizes or availability.

The body is a typed value. This checkpoint does not prove canonical body
serialization or reject every alias of a general native byte parser. It does not
compare a certified aggregate to all recomputed bodies, convert all certified
shards, or prove final schema placement. Those are still required by
`nativeParameterConversionSound`. APPLY and recovery also remain open. Mandatory
coverage stays 42/45; successful compilation is not Formal GO.

Quantum conversion is deliberately separate from PARAMETER computation. A
PARAMETER body can be valid even when later conversion overflows. This extractor
must not add conversion success as a PARAMETER vote precondition. Its `none`
result is mathematical rejection, not a new observable production failure code.
Domain-weight normalization belongs to APPLY, as in the proposal oracle.

## Finite examples and reproduction

`generate_native_graph_vectors.py` still derives its graph from the twelve exact
artifact byte strings in `formal/fixtures/traces/native/normal-apply.json`.
It now emits kernel-checked frame loading/validation and two complete expected
PARAMETER body comparisons against independently executed proposal-oracle results.
Twenty-one additional rejection examples cover missing/substituted/wrong-length
bytes, unplanned keys, eligibility/parent/matrix mistakes, identifiers, Q
schema/quantum/ticket/domain/shard/shape/commitment mismatches, schema gaps/overlap/
overrun, assignment order and duplicate contexts. The four earlier graph
rejection proofs remain. Frame/row negative examples test those checked
boundaries, rather than claiming full rehashed native mutation executions.

The codec is still a finite lookup table and the fixture trust is synthetic.
These examples are neither native C++ execution nor new TLA production mutants.
All new proof-producing functions, four general helper theorems and twenty-five
new concrete proofs are included in `AxiomAudit.lean`.
Their kernel dependencies are limited to permitted `propext`, `Quot.sound` and
`Classical.choice`; `loadPayload` has no axiom dependencies. These library axioms
are distinct from the explicit semantic codec/trust premises. No new axioms,
proof holes or assumed result-uniqueness propositions are introduced.

Regenerate with `python formal/scripts/generate_native_graph_vectors.py`, then
build `lake --no-cache build DeltaReduce` from `formal/proofs`. Run the mandatory
Lean evidence checker; it must still report the three missing native targets.
No runtime guard, frozen demo reference or qualifying benchmark is changed.
Self-review is not independent attestation.
