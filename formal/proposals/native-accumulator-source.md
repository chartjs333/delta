# Original accumulator proof/configuration projection

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
This formal tooling stage changes no runtime, TLA, Lean, public schema or original
capture. It defines `deltareduce.original-accumulator-source.v1-candidate` in
`formal/scripts/native_accumulator_source.py`. It is a bounded Python relation,
not a new kernel proof, C++ execution or authenticated exporter.

## Computed source relation

`resolve_accumulator(store, proof_id)` takes a separately chosen original proof
identity. It resolves the exact original proof, its configuration and immutable
worker profile under their original004 domains, NUL separator and canonical JSON.
It checks all eighteen proof and twelve config fields, their shared inputs,
profile/scale/config links, historical formal/Lean IDs, schema/type versions and
the ordered theorem-name groups required by the pinned native source.
Matching names and `result=PASS` are required metadata, never sufficient proof.

Let `A` be the configured positive coefficient bound and `N` the positive uint64
contribution bound. The immutable worker profile has `Q=32767`. The checker
computes `P=Q*A` and `S=P*N`, checks the positive INT128 intermediate limits,
requires the original declared product and prefix to equal `P` and `S`, and
checks `P` against the separately selected product width. It requires the
declared final bound `F` to satisfy `S <= F <= selected_accumulator_max`.
INT64 and INT128 positive limits are inclusive. Negative values, alternative
decimal spellings, booleans masquerading as integers and overflow reject.
Wider product width does not waive the selected accumulator bound.

The exact positive uint64 `common_denominator` is retained without reducing it,
choosing an LCM or inferring it from Q quantum. This layer does not establish
that certified ticket weights have denominators dividing it, or that their
scaled coefficients/counts obey `A`/`N`. Those are still required source edges.
The existing FixedPoint theorems require those actual coefficient/count/Q
premises; matching the theorem names cannot supply them.

`resolve_bound_q_source` additionally executes the previous complete manifest,
schema, scale, plan and DRQ1 relation, then resolves the proof from that original
manifest. It compares the repeated exact source preimages to reject a changed
observation. All twelve original objects and every one of the36 coordinates are
retained. It accepts no supplied QSource, expected vector or approval Boolean.
The standalone proof API retains schema/scale/plan/base-config references; only
the composed API resolves the Q graph. Base-config/parent authority remains open.

## Headroom is not a serialized observation

Native `ConcreteProofInstance.request.headroom` is **not** a field of
`canonical_proof_instance_json`. The native validator computes
`final_abs_bound = maximum_absolute_sum + request.headroom` and requires the
declared final value to match. Therefore, among admissible requests for the
retained bytes, the only possible headroom is `F-S`. The checker reconstructs
that value, including nonzero headroom; it does not silently assume zero.

This is a reconstruction of the unique admissible value, not proof that a
particular native invocation supplied it. Two typed requests with different
headroom can serialize the same fields when their declarations are unchanged;
at most one can pass native validation. `check_request_headroom` compares a
separate primitive observation to the reconstructed value but authenticates
neither that observation nor the original proof identity. The pinned native
test's original request explicitly has zero headroom and agrees with the fixture.
No new native execution of that test is claimed.

## Separate worker and APPLY profiles

`resolve_apply_accumulator` checks the original008 profile's full ten-field
canonical JSON and hash, exact nonnegative reduced rational wire values,
ordered unique domain labels, `nesterov=true`, `HALF_TOWARD_POSITIVE`, then resolves
its actual `accumulator_proof_id`. Original008 labels use the128-character
colon-permitting grammar, not original004's255-character segment grammar.
The native profile layer does not require unit sum; no such rule is invented.

The original008 fixture still points to `sha256:222...222`, whose proof bytes are
absent from the retained store. Supplying original004's bytes under that ID fails
the content hash. A test that changes the ID and rehashes a new profile is
explicitly synthetic; it does not upgrade the original capture or its authority.
Original004's worker profile uses ties-to-even quantization. Original008 uses
half-toward-positive conversion/APPLY. They are different stages, not conflicting
names for one operation. Original008's profile has no `apply_quantum` field:
quantum/config/width identity to the draft graph and optimizer intermediate
bounds remain unproved. An accumulator bound for weighted Q sums does not prove
conversion, mixture or optimizer arithmetic safety.

## Evidence, reproduction and remaining limits

Eleven exact source files at native commit
`60c692f6e391f839829dfc64e93380db54cd507b` are pinned in the new boundary manifest;
four reuse retained byte-exact copies from the previous stage. Original fixture
bytes remain separately pinned by that stage. The generator records the original
computed values, source bytes, complete Q rows and the actual missing008 edge.

Run:

```text
python formal/scripts/generate_native_accumulator_source.py
python -m unittest discover -s formal/tests -p test_native_accumulator_source.py -v
```

Tests include every missing field/dependency, rehashed incorrect product/prefix,
final below prefix, historical metadata/theorem mutations, count/coefficient/Q
bounds, separate widths, exact limits, inferred headroom, specific denominator,
profile fraction/label/coverage checks and complete rehashed Q graphs carrying
invalid proof records. Prior content-only validation accepts those graphs;
the new composed numeric relation rejects them. This is tooling testing, not
new production-source mutants or proof of native error-order equivalence.

All Python/JSON/SHA and resource limits inherited from the Q-source relation
remain explicit. No native decoder, physical WAL, signature/certificate authority,
public transition, recovery or current-state theorem follows from this helper.
Native decimal `-00`/`-01` compatibility remains FAIL. The full mandatory
`nativeArithmeticRecoveryRefines`, original-to-draft source/graph/admission,
phase/QC/current/unknown/repair, arbitrary snapshots, bounded codec/SHA/exporter,
contract freeze, offline reproduction and independent reviews remain required.
The formal semantics ID stays unchanged because no semantic inputs changed.
