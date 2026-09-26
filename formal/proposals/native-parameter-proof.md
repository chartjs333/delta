# Complete original native PARAMETER section

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO remains.** No runtime,
native arithmetic guard, closed CONFIG/proposed-ISC admission/replay or demo change.

NativeParameter retains every original PARAMETER field, all20 canonical JSON
fields, the complete bounded positive-u64 denominator, ordered nonempty content-ID
leaf list, nonempty original signed-decimal results, domain/shard, exact context,
configured quorum and actual signers. Its policy and JSON codecs preserve every
original string. The earlier source-bound native decimal model deliberately
accepts the observed -01/-00 spellings; parsing does not prove canonical spelling.
No normalization or replacement by separately computed arithmetic is performed.

The certificate, vote body and policy bytes are distinct. The native body hash
contains context/parents/denominator/domain/leaves/results/shard, and omits the
separate assignment vote_context_id. Policy bytes retain that field. A general
lemma proves changing only that field leaves the body hash unchanged while a
different original context changes the policy value. This matches the pinned
consensus.cpp projection; it is not a SHA collision or a whole-runtime exploit.
The enclosing vote envelope's context and full admission must still be checked.

NativeParameterLineage resolves the original ISC, EC and APC and requires all
three finalized identities. Proposed bodies additionally require the APC's
exact ISC/EC parents, required domain/shard membership, a nonempty assignment
context and at least one accepted EC entry in the domain. The finalized loop
does not repeat those proposed-only checks; the model preserves this distinction.
The source require_id checks only nonemptiness, not label/content-ID syntax.
No stronger invented context rule is substituted. Successful checks retain
original policy trees, exact computed body/QC ID and resolved parent witnesses.

NativeParameterSection executes the previous whole plan/EC/norm/seed/ISC section,
both complete PARAMETER lists, computed-ID ordering, finalized subset and ordered
unique required matrix. Proposed assignment checks model the source map and set:
a repeated key must keep its context, and a context may occur only once. General
induction derives distinct keys and contexts across every accepted list. This is
not a per-fixture membership table. Section lemmas derive original lists, counts,
matrix, and actual checked ISC/EC/APC witnesses. Bounded policy/state decoding and
reencoding use the existing checked codec; general C++ library equivalence remains
an explicit gap. Checking the sorted matrix before lookup is equivalent only in
this accepted sorted profile; the model does not claim native error-code ordering.

The source-bound generator pins the complete existing native observation files
before extracting codec-PARAMETER and codec-AGGREGATE_ROOT sections. Certificate
JSON/ID and policy wire are existing native observations. PARAMETER body bytes
and its hash are recomputed from the pinned consensus.cpp formula, with separate
Lean/Python encodings; this is **not a new observed C++ PARAMETER body hash**.
Two finite SHA samples extend eight existing parent samples. Checked components
compose actual previous parent checks and both new modes, without claiming a
whole-policy or runtime execution. Mathematical assignment/decimal/bounds cases
are distinct from native observations. No new TLC or production mutants.

Native verify_shard only checks context, parent IDs, signers and the serialized
certificate shape/hash. It does not recompute numerators, denominator or Q leaf
coverage. A shape-valid altered numeric result makes this limitation explicit.
The earlier checked native arithmetic graph must be joined through original
bytes/provenance; body shape and parent identity cannot replace that relation.
Signer lists do not authenticate signatures; finite SHA does not authenticate
producers. Native canonical-spelling compatibility still fails.

Next: complete original aggregate-root exact leaf matrix/Merkle/certificate
section, APPLY/current, then shared original admission/replay. Arbitrary initial
snapshots, unknown physical outcomes, authenticated scans, repair, full public
64-state/action binding, nativeArithmeticRecoveryRefines, contract freeze, clean
offline reproduction and independent review remain required. The mandatory
conjunct is still missing. No local acceptance PASS or original GO is issued.

Reproduce from repository root:

```text
python -X utf8 formal/scripts/generate_native_parameter.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_parameter.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeParameter.lean
lake --no-cache env lean DeltaReduce/NativeParameterLineage.lean
lake --no-cache env lean DeltaReduce/NativeParameterSection.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final stable source/check hashes and exact limits: evidence/native-parameter.json.
