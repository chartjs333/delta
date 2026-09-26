# Native certificate decimal spelling: confirmed gap and lexical model

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO** remains. This is a
source-bound countercheck discovered while preparing the norm/EC proof. It does
not change production code, repair the parser, widen admission or supply GO.

## Reproduced observation

The unchanged native `contracts.cpp` at
`60c692f6e391f839829dfc64e93380db54cd507b` combines a spelling test with
`std::from_chars` into `int64_t`. Its spelling test rejects `-0`, but does not
reject `-00`, `-000` or negative leading zeros. A fresh MSVC19.29.30146 x64
component build confirms:

| Original string | Norm (nonnegative) | PARAMETER numerator (signed) |
|---|---|---|
| `0` | accepts | accepts |
| `-0` | rejects | rejects |
| `-00`, `-000`, minus followed by64 zeroes | accepts | accepts |
| `-01`, `-0001` | rejects | accepts |
| `00`, `01`, `+0` | rejects | rejects |
| `9223372036854775807` | accepts | accepts |
| `9223372036854775808` | rejects | rejects |
| `-9223372036854775808` | rejects | accepts |
| `-09223372036854775808` | rejects | accepts |

There are31 input strings, each executed against actual native `canonical_json`
and `content_id` for NormEvidence and ParameterShardQc:62 cases total. Empty,
trailing-space/newline/NUL, non-ASCII, invalid-sign, fractional/exponential/hex
and overflowing inputs are retained too. Nine accepted cases fail the separate
strict Python proposal spelling profile. These are **observations of a gap**,
not a passing canonicality gate or new production mutants.

The native serializer retains the original string. Four numerically equal zero
spellings produce four distinct JSON byte strings and content IDs for each
certificate type. There is no silent normalization in this evidence. This
disproves the claim that this component admits only canonical integer spellings.
It does **not** demonstrate conflicting finalization, a whole-runtime exploit,
or mathematical acceptance of an incorrect worker norm.

## Execution and evidence boundaries

The harness compiles the exact original `canonical.cpp`, `sha256.cpp`,
`certificates/contracts.cpp` and their headers. Ten reference blob hashes match
the prior pinned certificate evidence. The harness only constructs original
fixture-shaped objects, replaces the target string, invokes native components
and emits bytes/IDs/errors. Expected acceptance is a literal case table;
expected JSON and SHA are independently computed in Python. The result parser
requires every exact ordered row and rejects missing/extra/substituted results.

The source-level native messages call these strings canonical, but execution
shows otherwise. The previous `native_certificate_chain.py` tooling profile
explicitly promised no universal accepted-language equality and remains strict;
its accepted language is not silently broadened to conceal the discrepancy.
Native arithmetic guard, runtime/WAL, policy snapshots and old receipts remain
unchanged. No demo process is restarted. This is one compiler's component run,
not compiler/platform qualification, authenticated export, or physical recovery.

## Lean layer

`NativeCertificateDecimal` makes the original lexical distinction explicit:
the outer native spelling condition, optional minus, nonempty decimal digits,
signed64 bounds, and the separate nonnegative constraint. `parse` returns the
computed integer; `check` additionally retains every original byte. General
lemmas derive range, nonnegativity, digit validity, exact original retention,
signed acceptance from nonnegative acceptance, and distinct checked results
for distinct source bytes. A negative-spelled nonnegative result must be zero.

`Canonical` is a separate predicate. Kernel counterexamples prove that accepted
`-00`/`-01` are not canonical and refute universal canonicality of this model.
All62 observed native outcomes have separate kernel checks, plus six explicit
counterexample/retention proofs. This is not a theorem about the compiled C++
standard library or universal equality of native and Lean parsing. The model
is not yet composed with whole NormEvidence, EC, APC or native replay.

Strict native spelling would require a separately reviewed semantic repair and
compatibility/migration analysis; this stage neither changes nor approves it.
Until then, any exact-source projection must preserve original spellings/IDs
and cannot derive canonical spelling from native admission. The norm values,
norm-root preimages, seed randomness, primitive authority and producer provenance
remain unresolved independently of this lexical issue.

## Next and remaining gates

Reuse this lexical model when binding all13 original norm JSON fields, exact
wire/list/context and computed finalized ISC parent. Then derive complete EC
membership and separate seed metadata, APC coverage and full admission/replay.
Do not assume norm entries equal ISC membership without an actual native check.
Keep unknown physical outcomes unresolved and preserve original historical bytes.

General decoder/hash/native equivalence, public64-state/action refinement,
`nativeArithmeticRecoveryRefines`, arbitrary snapshots/failures/repair, contract
freeze, clean offline reproduction and independent reviews remain mandatory.
Mandatory theorem audit is still44/45; no arithmetic guard change or formal/local
GO follows from this stage. GNU make is unavailable; scoped checks are not the
aggregate `make formal-check`.

## Reproduce

```text
python -X utf8 formal/scripts/check_native_certificate_decimal.py --vcvars <VS2019-vcvars64.bat>
python -X utf8 formal/scripts/check_native_certificate_decimal.py
python -X utf8 formal/scripts/generate_native_certificate_decimal.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_certificate_decimal.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeCertificateDecimal.lean
lake --no-cache env lean DeltaReduce/NativeCertificateDecimalVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Exact source/tool/check evidence is in `evidence/native-certificate-decimal.json`
and its sibling directory. Draft compilation attempts are not final evidence.
