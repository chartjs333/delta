# Checked PARAMETER arithmetic sublayer

Candidate amendment 0001, T044/T048/T049/T057/T060. Formal status remains NO_GO.
This checkpoint advances the arithmetic part of PO-AB1, but deliberately does
not register `nativeParameterConversionSound` as proved. The bridge from the
authenticated typed graph to exact eligible/committed rows is still required.

`formal/proofs/DeltaReduce/ParameterKernel.lean` accepts raw nonnegative rational
weights, the specific denominator and ordered vectors. It derives coefficients
itself, checks reduced fractions and denominator divisibility, and proves
`coefficient * weight_denominator = weight_numerator * plan_denominator`.
It checks coefficient bounds and every coefficient-sum prefix even when all
coordinate values are zero. Each Q coordinate must fit the separately supplied
input bounds; coefficients, products and accumulator prefixes fit the accumulator
bounds. Both vector-length mismatches and empty top-level inputs are rejected.

Induction proves that accepted rows produce exactly the unchecked mathematical
recurrence, preserve the whole vector length and satisfy all prefix conditions.
The converse and rejection-equivalence proofs establish that the row kernel
rejects exactly when those conditions fail. A separate coordinate projection
theorem connects every present output coordinate to `checkedAccumulate`, using
coefficients derived from original weights in their original order. The index
fallback in its term representation is never used for an accepted row; the proof
exhibits the actual value at that index. This is not merely equality between two
calls to one pure function or an assumed expected-result equality.

The domain-vector sublayer validates positive reduced Q/apply quanta and the
native-specified denominator, checks each numerator, applies the existing checked
product sequence, and proves exact per-coordinate rounding and unchanged vector
length. Product bounds are retained even when algebraic cancellation could avoid
overflow. The existing `round` definition and proof implement Euclidean rounding
with half ties toward positive infinity. This layer does not move rounding past
domain mixture.

## Scope and missing binding

The proofs quantify over arbitrary list lengths and integer bounds. The finite
vectors instantiate signed INT64/INT128 accumulators with INT64 inputs. They do
not prove that an arbitrary native profile selects these bounds correctly.
The low-level row function permits an arbitrary initial accumulator and
coefficient sum; `checkedParameter` supplies zero and a nonempty fixed width.

Rows intentionally contain only weight numerator/denominator and vector values.
Ticket IDs, selected domain/shard, Q commitment identities, schema offsets,
canonical metadata and certificate/native authentication are absent. A future
`nativeParameterConversionSound` must derive these rows from the immutable
authority graph, prove exact eligible order/coverage, bind the full expected
PARAMETER body, and place converted coordinates by the schema. It must not
assume that an untrusted list already has those properties. These proofs do not
close that native obligation or justify removing the runtime arithmetic guard.
They also do not define new failure messages or production serialization.

## Reproducible vectors and audit

`formal/scripts/generate_parameter_kernel_vectors.py` reads exact canonical
native-fixture bytes, checks the draft content IDs, uses the existing native
oracle to resolve each pinned assignment, then evaluates the existing arithmetic
oracle. It generates `ParameterKernelVectors.lean` and
`formal/proposals/parameter-kernel-vectors.json`: 36 PARAMETER and 22 conversion
cases, including two native assignments and their conversions.

Cases cover signed endpoints, 64/128-bit accumulation, distinct native-bound
denominators, zero weights, reduced-fraction requirements, coefficient and
coefficient-sum overflow, product overflow, unsafe prefixes with safe final sums,
shape/empty inputs, INT64 Q/weight limits, nonunit quanta, signed half ties,
conversion overflow and cancellation. Lean checks all expected values/rejections
with kernel `decide`. These are mathematical cross-language vectors, not native
C++ execution or new TLA production-mutant results. Oracle rejection strings
are diagnostic; the Lean kernel only returns `none`, not a production error code.

Reproduce from the repository root:

```text
python formal/scripts/generate_parameter_kernel_vectors.py
python formal/scripts/generate_trace_fixtures.py
python formal/scripts/generate_parameter_kernel_vectors.py
```

Both outputs must remain byte-identical after public trace regeneration. Build
`lake --no-cache build DeltaReduce` from `formal/proofs`, then run
`python formal/scripts/check_lean_evidence.py` from the root. All new helpers are
in the mandatory project and axiom audit. Registered PO-AB1 coverage remains
42/45 until the three complete native obligations are discharged. Self-review
and synthetic vectors are not independent attestations.
