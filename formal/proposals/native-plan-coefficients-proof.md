# Original APC membership and proof-bound coefficients in Lean

T044/T048/T053/T054/T056/T057. **NO_GO**. No runtime changes.
Evidence: `formal/proposals/evidence/native-plan-coefficients.json`.

`NativePlanMembers.prepare` actually decodes original DVPOL policy and native
summary-state bytes through `NativePlanSection.prepare`. It selects the requested
APC from the complete checked finalized list. It does not take caller-decoded
certificates, an approved weight table, or a translated whole body. The earlier
section retains original ISC/EC/norm/seed/APC encodings, committees, finality-ID
sets and the primitive EC-to-seed field in the original policy. Those primitives
still require independent source authentication; checking them is not signing,
quorum delivery, historical finality, native exporter or full-state admission.

Additional cross-parent checks compare all five contexts, the common ISC,
EC/norm/seed references, complete norm ticket list and unique ISC ticket IDs.
The relation walks the complete ISC and EC lists in order, including rejected
members, checking every ticket/domain and decision. It filters accepted members
and matches the full original APC weight and bucket lists with no unmatched tail.
General lemmas retain every original tuple, entry, final alpha, EC gamma, bucket,
commitment and AC identity at its original position. These cross-parent and4096
membership guards are explicit stronger projection restrictions, not an
equivalence theorem for isolated native verify_plan or native error ordering.

`NativePlanCoefficients.bind` executes that byte-source relation, decodes the
actual config/proof/profile bytes using the APC's own accumulator ID, and checks
config schema and base-round-config identity against the actual APC context.
Both certificate and accumulator identity paths use one raw-digest adapter;
its SHA implementation, injectivity and provenance are UNVERIFIED. A wrong digest
width is rejected. Missing original proof bytes are not replaced by another
profile's proof. The retained original008 APC still cannot complete this join.

For each final APC alpha a/b, it checks the reduced nonnegative fraction, b|L
for the specific loaded denominator L, and derives c=a*(L/b). General theorems
prove c*b=a*L, original order/count, coefficient bound, separate product safety
and every subset/prefix bound for each domain. It uses positions, so zero terms
and equal coefficient values do not disappear. EC gamma is retained but never
multiplied into the final alpha again. L is not replaced by its minimal LCM.
The global accepted count bound is an explicitly stronger sufficient restriction.
The final source-to-bound theorem composes actual byte loading with these
inequalities. Its actual Q-value premise |q|<=32767 remains explicit: this stage
does not load or authenticate per-ticket Q vectors, availability or commitments.
It also does not prove conversion, domain mixture or optimizer safety.

Kernel examples reuse the previously checked original APC edge, preserve the
missing-proof distinction and reject the earlier cross-ISC counterexample.
Separate synthetic row components come from the existing versioned Python test
graph: four ISC/EC members, three accepted weights0,1/3,1/2, gamma1/7, L12 and
coefficients0,4,6 in two domains. The kernel checks complete alignment, rejected
membership, numeric bounds, exact domain filtering and failures for missing,
extra, reversed, duplicate or mismatched sources, fractions/counts and parent
metadata. These components do not constitute a new combined whole-policy/proof
kernel execution or a native run. Original captured bytes and sequences5/6/8
remain unchanged.

The separate native certificate decimal -00/-01 compatibility failure remains
open. A stricter parser does not repair or reclassify it. Original base/current/
model/optimizer/APPLY source bytes, authenticated availability and certificate
authority, full-vector original-to-draft correspondence, physical WAL and all
public phase/QC/send/current/crash/unknown/torn/repair behavior remain required.
`nativeArithmeticRecoveryRefines`, contract freeze, clean offline reproduction
and independent reviews are not discharged. No local acceptance PASS or GO.

Reproduce with `python formal/scripts/generate_native_plan_coefficients.py`,
`python -m unittest discover -s formal/tests -p test_native_plan_coefficients.py -v`
and the mandatory `lake --no-cache build DeltaReduce` plus fresh kernels and
axiom audit. `make formal-check` is not claimed when make is unavailable.
