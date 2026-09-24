# Conditional native APPLY result identity

Candidate amendment 0001, T044/T048/T049/T057/T060. `nativeApplyResultUnique`
is now in the mandatory Lean project and axiom audit. This closes the conditional
mathematical APPLY conjunct of PO-AB1, not the native implementation or Formal GO.
Recovery, concrete adapters/admission, contract freeze, clean reproduction and
independent review remain required. Mandatory coverage is 44/45 after execution
of the recorded proof checks.

## Independently anchored inputs

The theorem takes two independently supplied stores and `Binding` witnesses for
the same authenticated native anchor. Canonical-codec collision resistance,
anchor/recovery authentication and certificate validation remain named premises.
Neither caller-provided result equality nor graph/row uniqueness is a premise.

`frameOriginUnique` compares actual resolved schema, plan, ISC, EC and APC payloads
at the authority's references. `certifiedFrameBodiesUnique` resolves the same
anchored aggregate in both stores and derives exact equality of the full ordered
PARAMETER body lists. Both lists were independently derived and checked before
conversion. Model, optimizer and profile equality follows from the earlier
ordered native graph theorem.

`DerivedParameter` now retains two proof fields for the actual assignment and
partition `find?` outcomes. They are supplied by the existing checked loader;
no selection behavior or new runtime precondition is introduced. These witnesses
fix the conversion quantum and schema offset for each body. Induction pairs
converted entries in their certified order, proves equal converted values and
placed cells, then derives equal complete per-domain vectors. Missing/duplicate
placement cannot be hidden by assuming equal final vectors.

`alignApplyRows` consumes both the profile's ordered domain weights and the
certified vectors, checks the domain name at every position and rejects unequal
lengths. General proofs retain exact weights, values and names. The actual native
program obtains these lists itself; it does not take mathematical rows from the
command. `NativeApplyCore` applies `ApplyKernel` at fixed FULL_SIGNED_INT64 bounds
to the independently bound current model/optimizer and profile coefficients.
All mixture and optimizer safety/shape/rounding properties from that kernel are
retained, even when earlier PARAMETER accumulation used INT128.

## Full body, bytes and hashes

The result constructs all `APPLY_EXPECTED` fields: authority ID, anchored aggregate
ID, every encoded PARAMETER body ID in order, next model/optimizer vectors and
their domain-separated value hashes. These are constructed from computed values,
not accepted from the candidate. Exact authority identity transitively binds
the context, parent checkpoint, schema, profile, current state and certificate
parents.

Lean's output encoders spell sorted JSON keys, exact decimal integers,
lowercase hexadecimal 32-byte content IDs, separators and array order explicitly.
Identifiers must satisfy the amendment's existing bounded ASCII grammar; invalid
quotes/Unicode and malformed ID lengths are rejected. Encoding writes byte lists
directly, avoiding dependence on a host JSON serializer. `asciiBytes` is only used
on checked identifiers or fixed ASCII/decimal spellings; it is not a general
Unicode encoder. These encoders do not prove a production decoder's completeness,
its 4 MiB/4096-item/depth limits or runtime allocation behavior. Those limits must
be connected by the concrete native refinement layer; this mathematical program
does not define a new production error code or admission rule.

`HashAdapter` explicitly assumes a SHA-256 primitive implementing these exact
preimages: draft artifact domain plus NUL plus canonical body bytes, and the
existing model/optimizer value domains plus NUL plus semicolon-terminated decimal
coordinates. The theorem proves body IDs, candidate hash input and next-state
value-hash inputs use those encodings. It does not implement SHA-256 or prove
cryptographic collision resistance. Input canonical decoding remains the earlier
explicit `Codec` parameter.

`nativeApplyResultUnique` derives identical full typed bodies and canonical bytes
across independent stores, exact output lengths and full INT64 bounds, plus
the hash-preimage bindings above. Same-input arithmetic uniqueness is only an
internal helper used after the native input equalities have been proved.
The checked derivations carry their own arithmetic/encoding evidence. Soundness
does not establish native admission completeness, runtime availability, role/
deadline enforcement, signatures, persist-before-expose or physical WAL replay.

## Executed examples and audit

Seventeen additional kernel examples cover exact PARAMETER encoding, complete
APPLY body and bytes from the pinned graph, all three hash preimage domains,
INT64/INT128 signed decimal endpoints, malformed kind/hash/identifier rejection,
and missing/extra/wrong/reordered domain alignment. The fixture hash table now
also contains the two exact encoded PARAMETER bodies and next-state value hashes.
Its input decoder still accepts only the twelve pinned artifact byte strings;
its collision proof is restricted to those accepted strings. This is a finite
synthetic codec/trust witness, not a general parser/hash proof or native C++ run.
The seventeen examples use kernel `decide`, not native-evaluation axioms.

Two further Python tests require stale/missing current optimizer artifacts to
stop generation before emitting Lean. Existing tests cover noncanonical or
substituted bytes and rehashed but incorrect certified bodies. The separate
32 APPLY-kernel cases remain, including the larger three-domain fixture; that
larger fixture is not relabeled as a full native output-encoding execution.

Reproduce with `generate_native_graph_vectors.py`, then regenerate public traces
and all three vector generators. Repeating regeneration must be byte-exact.
Run the full `lake --no-cache build DeltaReduce`, fresh body/vector kernel checks,
axiom audit and `check_lean_evidence.py`. The overall Lean report must still fail
for missing `nativeArithmeticRecoveryRefines`. Full FormalVerificationReport
remains NO_GO and does not authorize removing the runtime arithmetic guard.
