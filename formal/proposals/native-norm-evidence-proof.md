# Original native norm evidence and finalized ISC edge

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO** remains.
No native code, arithmetic guard, closed admission/replay modes or demo changed.

`NativeNormEvidence` reads the complete original `fmtNorm` tree: context,
ordered entries (u64 scale denominator, original squared-norm string, ticket),
ISC certificate ID and primitive norm root. It constructs all13 native JSON
fields and all3 fields of each entry. The hash preimage uses the actual native
`deltareduce.008.norm-evidence.v1` domain, NUL and original JSON. The separate
byte entry composes the bounded policy codec, retains the complete wire, and
derives exact reencoding. The tree API is not itself a byte decoder.

Checks cover exact context, content-ID and ticket-label shapes, nonempty bounded
entry lists, strictly increasing ticket order, positive u64 scale and the actual
previously modeled certificate decimal rule. This intentionally accepts the
native `-00` spelling while rejecting `-0`. JSON contains the original string;
no `Int.repr`/normalization replaces its bytes. The native canonicality defect
remains open. Parsing nonnegative int64 does not compute a norm from worker Q.
Labels reuse the explicit ASCII profile; this is not a general theorem about
the C++ locale-sensitive `std::isalnum` implementation. Resource bounds on the
byte entry remain those of the prior policy codec, not a new native restriction.

General proofs retain every entry, source tree, original squared-norm bytes,
nonnegative parsed number, exact context and computed content ID. `linked`
computes the actual ISC certificate before comparing its QC ID with the norm's
parent. The low-level finalized-ID list alone is not finalization provenance.
`NativeNormSection` first executes `NativeFinalizedIscSection`, then checks every
original norm in the snapshot against that result's finalized IDs and requires
strict order of the computed norm IDs. Its induction derives exact original
list/count and a checked original ISC certificate witness for every parent.
Policy/state byte preparation composes existing readers; it is an isolated
section, not a full graph acceptance or recovery theorem.

The original native norm JSON and its exact wire section in the pinned codec-EC
snapshot are independently checked before vector generation. Three finite SHA
samples bind the ISC QC, ISC voted body and norm ID. Positive byte/parent examples
compose actual checked components. Negatives cover changed/unfinalized parents,
body-ID substitution, empty/duplicate/unordered entries, invalid ticket/root,
wrong context, zero/overflowing scales, negative/overflowing norm and hash failure.
Separate mathematical cases preserve `-00` and show equal numeric value but
different JSON from `0`; they are not new native policy/trace executions.

Explicit counterchecks retain structurally valid alternate norm-root IDs and a
ticket absent from the fixture ISC. Inspection of pinned `verify_norms` and its
snapshot loop shows only exact context/ISC-parent/content validation at this
edge. This layer does not invent a norm-to-ISC membership rule or claim that the
norm root, scale or value was recomputed from Q. The later EC relation must be
checked separately against its actual complete native membership rules.

The general compiled parser/serializer/SHA equivalence, original exporter and
finalization provenance, cryptographic signatures/randomness, complete EC/APC,
full admission/replay/public64-state relation and `nativeArithmeticRecoveryRefines`
remain open. Contract freeze, clean offline reproduction and independent review
are still mandatory. Earlier32 mixed native cases, TLC/mutants and arithmetic
path retain their existing scope; no fresh native execution/TLC/mutant run is
claimed here. Native decimal failure is not repaired. GNU make remains unavailable;
scoped checks are not aggregate `make formal-check` or original/local GO.

Reproduce from the repository root:

```text
python -X utf8 formal/scripts/generate_native_norm_evidence.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_norm_evidence.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeNormEvidence.lean
lake --no-cache env lean DeltaReduce/NativeNormSection.lean
lake --no-cache env lean DeltaReduce/NativeNormEvidenceVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final source/check hashes and scope: `evidence/native-norm-evidence.json`.
