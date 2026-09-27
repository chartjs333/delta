# Original APC weights bound to an original accumulator

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
`deltareduce.original-plan-weights.v1-candidate` is a bounded Python source
relation in `formal/scripts/native_plan_weights.py`. It changes no native
runtime, TLA, Lean, public schema or original fixture. It is not a new Lean
proof, native execution, certificate authentication or admission theorem.

## Complete source membership

`resolve_members(store, plan_id, ec_seed_bindings)` resolves exact original008
APC, EC, ISC, seed and norm preimages by their own canonical content domains.
The root is the APC; no later PARAMETER, aggregate or APPLY is required. Each
document retains its full canonical bytes, original context, parents, signers
and source identity. Bounded canonical ASCII JSON decoding precedes the existing
certificate shape/hash decoder. Its stricter4096-entry limits and label/profile
limits are proposal restrictions, not general native codec completeness.

All five contexts agree. EC, seed and norm point to the same ISC. EC's seed
identity is absent from its wire certificate: the keyed primitive
`(EC content ID, seed content ID)` is checked separately and retained. This
primitive requires independent original policy/state provenance; a supplied
mapping is not authenticated just because its identifiers match. There is no
whole-body translation or caller approval Boolean.

The entire ordered `(ticket, domain)` list must agree between ISC and EC,
including rejected participants. Norm ticket coverage is checked too. An ISC
with duplicate ticket IDs cannot silently collapse through a dictionary even
if its `(ticket, commitment)` pairs are distinct. Accepted EC tickets must
equal both complete ordered APC weight and bucket lists. Every retained row
contains the original ticket/domain, bucket, final alpha fraction, EC gamma,
commitment and availability-certificate identifiers. Missing, extra, substituted,
duplicate or reordered rows reject. Commitment/availability bodies, input-root,
norm values, robust clipping/transcript and seed derivation are not established.
These cross-parent checks are stronger than isolated native `verify_plan`:
no equivalence to that predicate or its failure ordering is claimed.

## Actual coefficients, denominator and count

`resolve_plan_weights` calls the source resolver itself and resolves the proof
actually named by the APC through `resolve_accumulator`. It takes no supplied
decoded result. The original proof/config/profile arithmetic and all declared
bounds are rechecked. The proof config's schema and base-round-config IDs must
match the original APC context. Their equality does not authenticate the
configuration's contents or current state; schema/scale/plan payloads are still
handled by the separate Q-source relation, not silently inferred here.
The resolved proof profile is the immutable original004 worker profile. APC's
original008 `arithmetic_profile_id` is retained as common context only; its
separate APPLY profile/proof edge is not joined by this API.

For the specific proof denominator `L`, and each reduced nonnegative final APC
weight `alpha_j = a_j / b_j`, the checker requires `b_j | L` and computes
`c_j = a_j * (L / b_j)`. It does not choose another LCM, round a fraction or
reduce `L`. It checks `c_j <= A`, where `A` is that proof's coefficient bound.
**APC alpha is already the final scalar weight. EC gamma is preserved as source
metadata and is not multiplied into it again.**

The global accepted-ticket count, including zero coefficients, must be at most
the proof bound `N`. This is an explicitly stronger sufficient projection
restriction where a per-domain interpretation would otherwise allow more total
participants. Every domain then has at most `N` terms. Filtering the original
ticket order yields exact per-domain coefficients; no supplied coverage table
is accepted. For each prefix the checker computes `32767 * sum(c_j)` and checks
the proof product/prefix limits. These are worst absolute bounds for Q values
in `[-32767,32767]`, not observed Q products or actual accumulation results.
Original proof width checks ensure the retained bounds fit their separate
product and accumulator widths. Conversion/mixture/optimizer bounds do not
follow from these weighted-Q bounds.

## Original capture versus separately constructed example

The original APC is extracted by the existing `generate_native_plan.source`
from pinned original native policy observations, not a new source chosen to fit
the proof. Its exact bytes, parent bodies, required-proof identity and finalized
membership match the earlier retained observation. Its proof identity is
`sha256:ffff...ffff`; that preimage is missing from the retained store. The
membership checker succeeds and the complete coefficient/proof join **rejects**
with that exact missing identity. The original004 proof has a different ID and
cannot be installed under the missing one. This is a fixture/store gap, not a
claim of global absence or a new failure of native execution.

`deltareduce.synthetic-plan-weight-example.v1` is a separate generated test
graph, never an upgrade of the original capture. It contains four ISC/EC
tickets, three eligible rows in two domains, final weights0,1/3,1/2, EC gamma1/7,
proof denominator12 and derived coefficients0,4,6. Twelve deliberately differs
from the minimal LCM6. All eight source objects are retained. The constructed
context/config/proof identities are explicit. No original bytes, snapshots,
envelopes or sequence numbers are overwritten, and no native run is claimed.

A deliberate countercheck uses unconfigured signer names and still passes the
content/numeric helper. It demonstrates that signer shape/threshold and source
hashes are not committee authority, signatures or finality. Existing Lean
NativePlanSection/Lineage provide original typed policy/state relationships,
but their composition with this numeric helper is not yet a kernel theorem.

## Reproduction and remaining work

```text
python formal/scripts/generate_native_plan_weights.py
python -m unittest discover -s formal/tests -p test_native_plan_weights.py -v
```

The source manifest pins four relevant native files at
`60c692f6e391f839829dfc64e93380db54cd507b`, reusing exact retained copies where
available. A fifth source, `verifier.cpp`, is separately retained and byte-checked
against that same commit in `verifier-source-check.json`. The candidate checkout's
older verifier differs, so its working bytes are not substituted for the pinned
original source. Tests check source pins/regeneration, exact rational scaling against
Python Fraction, nonminimal denominators, all contexts, full membership,
counts/zero weights, fraction spelling/ranges, rehashed invalid proof fields,
coefficient limits, missing/corrupt source bytes, independently missing seed
metadata, complete-field omissions and the signer-authority counterexample.

Next: join exact committed Q manifest/DRQ1/schema/range/quantum preimages with
these original ticket/commitment/availability sources, then the independently
anchored draft graph. Original004/008 IDs cannot be equated to draft IDs; the
missing original source fixture cannot be repaired by invented labels or a
rehashed valid wrapper. PARAMETER must remain admissible before later aggregate.
Original008 APPLY quantum is absent and needs an actual provenance contract.
Full64-state phase/send/delivery/QC/current, physical WAL/unknown/torn repair,
arbitrary snapshots, codec/SHA/exporter, `nativeArithmeticRecoveryRefines`,
contract freeze/offline reproduction and independent reviews remain required.
Semantics stays unchanged because semantic inputs did not change. No local PASS
or GO is issued; the native arithmetic guard remains untouched.
