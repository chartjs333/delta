# Checked APPLY arithmetic sublayer

Candidate amendment 0001, T044/T048/T049/T057/T060. Formal status remains NO_GO.
`ApplyKernel.lean` is part of the mandatory Lean project, but does not discharge
`nativeApplyResultUnique`. It operates on mathematical model/optimizer vectors,
domain rows and rational coefficients. Deriving those inputs from independently
anchored graphs, binding full expected body bytes and recovering them remain
separate obligations. Mandatory coverage stays 43/45.

## Operation graph

The kernel constructs the domain denominator from reduced nonnegative weights;
the command supplies no expected denominator. Induction proves positivity,
divisibility by each input denominator and divisibility into every common
multiple. Every successive LCM is checked against the arithmetic bounds. The
nonempty weight list must have exact normalized sum `sum(a * (P / b)) = P`.
As in the proposal oracle, this normalization identity is over mathematical
integers; it does not specify an unchecked machine implementation of that sum.

Each gradient coordinate uses the original ordered domain rows and checks both
products in `(value * a) * (P / b)` separately, then every sum prefix. The kernel
proves equality with the mathematical recurrence, its converse and exact
rejection equivalence for these prefix conditions. A safe final rational value
does not excuse an overflowing intermediate product. The final mixture is
rounded once, with the existing half-toward-positive-infinity rule. Per-domain
quantum conversion must already have occurred upstream; this layer does not move
it across the mixture.

For each coordinate, the optimizer checks this exact sequence:

```text
oldScaled = round(oldMomentum * mu.numerator, mu.denominator)
nextMomentum = oldScaled + gradient
nextScaled = round(nextMomentum * mu.numerator, mu.denominator)
direction = nextScaled + gradient
decay = round(theta * wd.numerator, wd.denominator)
directionWithDecay = direction + decay
step = round(directionWithDecay * lr.numerator, lr.denominator)
nextTheta = theta - step
```

All three coefficients must be reduced nonnegative fractions. All original
values and all twelve intermediate values, including products before division,
must fit. A zero learning rate does not bypass earlier checks. The mathematical
checker evaluates these expressions in Lean's unbounded integers to check each
bound; it makes no machine-width execution or error-priority claim. An
inductive optimizer trace preserves every coordinate, records the safety
conditions, and proves full output shape and bounds without truncating lists.

The complete checked program rejects empty model/domain lists and unequal
model/optimizer/domain lengths. Column extraction proves each actual source
coordinate is present, so the totalized mathematical expression's `getD 0`
fallback is never used on accepted input. It produces exactly the coordinates
in `List.range model.length`, then runs the checked optimizer traversal.
Two checked derivations from the same mathematical inputs have identical LCM,
gradients and next model/optimizer vectors. This follows from the LCM and
gradient soundness proofs and induction on optimizer traces, not an assumed
result equality. It still presupposes the same mathematical inputs and is not
cross-store native graph binding.

The nineteen helper theorems quantify over arbitrary list lengths and integer
bounds. The native amendment requires APPLY to instantiate FULL_SIGNED_INT64
throughout, even when the earlier PARAMETER accumulator uses INT128. The native
bridge must establish that instantiation; accepting arbitrary caller bounds in
this mathematical helper does not make them a production option.

## Vectors, assumptions and remaining obligations

`generate_apply_kernel_vectors.py` first checks exact artifact bytes/IDs, native
anchors and the full ordered certified PARAMETER body list in the two pinned
native fixtures. It derives domain vectors using the proposal oracle, then
generates `ApplyKernelVectors.lean` and `apply-kernel-vectors.json`. Two full
vector comparisons use the fixture's current model/optimizer, coefficients and
certified domain values, including the five-coordinate, three-domain fixture.
The other thirty cases cover signed rounding, normalized/noncanonical weights,
LCM, both multiplication stages, unsafe sum prefixes with a safe final sum,
every optimizer operation category, empty/unequal shapes and INT64 endpoints.
All thirty-two concrete assertions are checked by Lean kernel `decide`.

Five tooling tests cover byte-exact reproduction and rejection before output of
substituted bytes, missing/stale current optimizer, and a rehashed aggregate
containing an incorrect certified numerator. Artifact authentication and
conversion for these examples are performed by the proposal oracle, not by this
Lean module or a production native runtime. They are finite oracle/Lean vectors,
not native C++ executions, TLA production mutants or governance attestations.
The arithmetic module imports only ParameterKernel; its added proof dependencies
are audited, including proof-producing extraction functions. No new axioms are
declared.

The next native bridge must derive exact ordered rows and coefficient names from
`NativeConversion` and the anchored profile, bind the current model/optimizer,
instantiate the correct bounds, construct all APPLY body fields and next-state
hashes from those derived values, and prove agreement across independently
anchored stores. Canonical body encoding, actual native parser/authentication,
admission/availability and physical WAL refinement remain mandatory. Neither
this layer nor its vectors permit removing the native arithmetic guard.

Reproduce after proof-source changes, from the repository root:

```text
python formal/scripts/generate_apply_kernel_vectors.py
python formal/scripts/generate_trace_fixtures.py
python formal/scripts/generate_native_graph_vectors.py
python formal/scripts/generate_parameter_kernel_vectors.py
python formal/scripts/generate_apply_kernel_vectors.py
```

Repeat the last four commands to check byte-exact reproduction. Build with
`lake --no-cache build DeltaReduce` in `formal/proofs`, then run
`python formal/scripts/check_lean_evidence.py` from the root. Its overall failure
for missing `nativeApplyResultUnique` and `nativeArithmeticRecoveryRefines` is
intentional and must not be reported as Formal GO.
