# Minimal vector representation and scalar coordinate projection

Tasks: T044, T053–T057. Requested checkpoint:
**REQUIRES MODEL/ARCHITECTURE CHANGE** for the current scalar public bridge.
The two requested representation/arithmetic statements are established below;
this is not closure of R2. R1–R7 and their acceptance criteria are unchanged.
Do not continue another R2/R3 layer after this checkpoint without a new direct
user instruction.

## Minimal relation

For one original source object `S = (identity, entry, values)`, require
`values.length = entry.count`. Define one image

```text
V = (S.identity, S.entry, coordinate : Fin S.entry.count -> Int)
R(S,V) iff V.identity = S.identity
       and V.entry = S.entry
       and [V.coordinate(0), ..., V.coordinate(count-1)] = S.values.
pi_k(V) = Some(V.coordinate(k)) when k < count, otherwise None.
```

`represent` constructs this image by reading the original list at the same
index. It takes no translated vector, approval table or desired result equality.
`identity` is the original object, parametric in its type, not a new identifier.
Thus even the complete original shard/vote/certificate envelopes can be retained
unchanged. `identityObservablesPreserved` proves equality for every accessor of
their original identities. No coordinate allocates a vote or certificate, and
no hash or shard name is recomputed. The constructor does not authenticate an
identity or construct a missing certificate.

The entire entry is retained: name, ordinal, start, count, payload and offset.
The local coordinate remains `k`; its model position is `entry.start + k` and
its parameter position is `entry.offset + k`. `sliceSource` and
`globalCoordinateExact` prove that slicing a full vector reads that exact global
position. An out-of-range projection returns `None`, never a padded coordinate.
`noCollapse` derives equality of the source identity, entry and entire value
list from equality of the images. List construction keeps order and one image
per original object, including original multiplicity.

## Requested statement 1: original 4/8/8/8/8 partition

The Lean proposal reuses `NativeVectorArithmeticVectors.original` and its
already checked original manifest, without generating another fixture:

- `originalObjectsRetained`: image identities are exactly the original complete
  bound blocks, in the original order.
- `originalManifestEntries`: entries equal the original manifest's entry list.
- `originalWidths` and `originalStarts`: widths are `[4,8,8,8,8]`, starts are
  `[0,4,12,20,28]`.
- `originalFiveNotThirtySix` and `originalCoordinateCount`: five objects contain
  36 coordinates. They have not become 36 shards.
- `originalValuesRetained`: all values, including their order, equal the
  original source lists.

This is the existing original Q/manifest component. It is not a new joined
PARAMETER/APPLY vote-and-QC capture. Preservation of arbitrary original
vote/certificate identity is the general equality theorem above; provenance
and admission of those objects have not been newly established by this fixture.

## Requested statement 2: existing scalar arithmetic is a projection

For every successful existing vector PARAMETER computation and every valid
coordinate `k`, `scalarParameterIsCoordinate` proves

```text
checkedParameter(bounds, D, width, rows) = Some(result)
  => exists x,
       result[k] = Some(x)
       and checkedParameter(bounds, D, 1, map(rowAt(k), rows)) = Some([x]).
```

The scalar rows are local arithmetic views, not new protocol shards. The same
ordered members, coefficients, denominator and bounds are used. The proof
retains coefficient and product checks and every accumulator prefix;
`parameterCoordinateNeverPads` proves that every projected row actually has
that coordinate. `representedParameterCoordinate` identifies the result with
`pi_k`. `originalResultCoordinate` starts from the existing source reducer's
own successful result, constructs its image, and proves the same statement.
It does not accept an externally supplied whole-body translation. Existing
width-one `NativeScalarProjection.Parameter` results remain exactly unchanged
by `originalScalarResultUnchanged`.

The remaining existing numeric kernels commute with coordinate projection as
well, conditional on their existing accepted computations/traces:

- Conversion: `scalarConversionIsCoordinate` retains the original call to
  `checkedConvert` for each coordinate, including its products and rounding.
- Mixture: `scalarMixtureIsCoordinate` retains the ordered domain column,
  checked products/prefixes, denominator, rounded result and output bound.
- Optimizer: `scalarOptimizerIsCoordinate` retains the exact scalar checked
  optimizer call, with every intermediate check.
- `applyCoordinateFromSameVector` composes mixture and optimizer at the same
  index and proves that the actual rounded gradient is the optimizer input.
  `globalCoordinateExact` locates that index inside its original shard.

These statements use the SAME declared arithmetic bounds on both sides. They
do not infer limit127 acceptance from INT64/INT128 success, weaken a native
precondition, or turn separate coordinate results into independent votes.
They do not establish a whole-public-body, admission or transition refinement.

## Checkpoint and residual delta

The missing lossless numeric representation and its checked scalar projection
now have explicit kernel-checked statements. No additional top-level R item is
closed: **R1 CLOSED; R2 OPEN; R3 OPEN; R4–R7 deferred**.

The existing public representation is still scalar: `DeltaReduceArithmetic.tla`
declares one coordinate per shard, and `DeltaReduceReduceApply.tla` stores a
scalar PARAMETER value. The preceding `r2-domain-audit.lean` proves that the
current complete PARAMETER/APPLY body APIs require every shard length to be one,
independently of metadata or aliases. The new `Image` cannot satisfy those
unchanged types for widths 4/8/8/8/8. Therefore the current bridge still requires
a model/proof-architecture change: a vector-valued public representation or a
proved synchronized coordinate-family lifting that retains one original vote
and atomic all-coordinate admission. This checkpoint neither selects nor
implements that next layer, and does not claim all alternative refinements
impossible. No native protocol/identity change is required by the two numeric
statements proved here.

This is a local architectural limitation, not BLOCKED_EXTERNAL and not a new
DoD requirement. The remaining R2 target is the already frozen complete
source/body/state correspondence; R3 is its preservation over the already
frozen transitions. Their vocabulary and obligations are finite and unchanged;
the time needed to finish their proofs is not established by this proposal.

## Reproduction and authority boundary

From `formal/proofs`:

```text
lake build DeltaReduce.PublicApplyArithmetic DeltaReduce.NativeVectorArithmeticVectors
lake env lean ../proposals/vector-shard-representation.lean
```

The file includes an explicit axiom audit. Source/import hashes and exact
commands/logs are recorded in `evidence/vector-shard-representation.json`.
Only targeted proposal/dependency and unchanged-contract checks are claimed;
the full formal gate was not run as part of this limited task.

This proposal is outside the candidate semantic inventory and mandatory
theorem registry, and is separately source-bound. Candidate TLA/Lean semantics,
runtime, native guard, accepted DoD and frozen refs are unchanged. The historical
NO_GO report remains historical for its own source tree. No GO, native execution,
exporter authentication, recovery closure or independent review is claimed.
