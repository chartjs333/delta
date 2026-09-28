# R2: family constructors, numeric domain and source composition

Tasks T044/T047/T053–T057. Basis `4d67478f35450638799076edf89152efc34708a7`.
The user authorized only the three frozen R2 obligations for at most four active
hours. R1 remains CLOSED. R2 remains OPEN; no R3 work, production Init/Next,
certificate semantics, WAL identity, runtime guard, mandatory semantics/report,
or frozen DoD change is part of this proposal. This is self-review evidence.

## Residual delta

| Frozen obligation | Result and precise remaining work |
|---|---|
| 1. Family → complete public input/body constructors | **PARTIAL.** `FamilyInputs` selects each original full row by its actual shard-local coordinate, preserves original contribution order and commitments, and uses the complete 23-field encoder. `FamilyAuthority` constructs all authority and ISC/EC/APC parents. `FamilyParameter`, `FamilyApply`, and `FamilyRoot` construct all PARAMETER/aggregate/APPLY fields, with exact original certified leaf order. ROOT does not require a later APPLY or conversion to succeed. General constructor-existence proofs start from a checked input authority, derive same-store frame/row identity, and apply at arbitrary positive vector lengths; they do not accept a translated whole body. The PARAMETER value is recomputed from the exact Q/weight/denominator rows in its own embedded input image, not a separately supplied numerical view. The executable PARAMETER gate is total given checked source authority and primitive canonical names; aggregate canonicality is derived from complete constructed leaves and the existing encoded-leaf uniqueness condition. **Remaining:** complete configured ticket inputs for OMIT_UNAVAILABLE, full original source-domain coverage, and general canonicality/completeness of the entire input-authority loader (the PARAMETER/aggregate results above are conditional on that loader and primitive names). |
| 2. Native INT64/INT128 → existing public guards | **PARTIAL.** `FamilyGuards` derives exact coefficient/product/prefix, conversion, mixture and optimizer numeric guards from actual typed native computations at both accumulator widths. All numeric clauses of the existing input guard are also derived from that same input image: domain/ticket order and shape, reduced fractions, quantum, Q/current ranges, denominator divisibility, exact mixture LCM and normalization. The symmetric PARAMETER result bound is kept distinct from the asymmetric arithmetic bound. Original optimizer arithmetic with unsigned 64-bit denominators is additionally checked through the actual magnitude/tie branches, all checked intermediates and checked negation of the step. Whole-vector traversal retains order and rejects shape mismatch. An original decoded profile is retained by its existing checker and content ID. **Remaining:** compose this full original numeric domain with the source/input/body loader, whose older `ParameterFrameValid`/`ProfileChecks`/`ApplyComputation` path still has additional representability restrictions. Numeric implications are not full admission equivalence. |
| 3. Source/config/aliases/certificates/state → one checked R2 relation | **OPEN, partial composition.** `FamilyRelation.checkOriginal` composes the unchanged original arithmetic journal checker, exact vote identity/context and complete computed family body. `FamilyRoot.join` composes actual ROOT/leaf source checks with primitive metadata agreement; full public ISC/EC/APC equality is then derived. `checkConfiguredArithmetic` joins the original decoded policy to the same captured arithmetic source. Actor aliases are a checked bijection onto that original committee; the generic signer image preserves membership and cardinality, and an actual checked ISC certificate retains its quorum threshold. A general theorem rejects two distinct public actors mapping to one original actor. This is not yet a signer/certificate join for every state collection. **Remaining:** one coherent authenticated public configuration/alias/source relation across the existing object kinds, and exact full static state/certificate/vote collection coverage. No whole-state mapping or refinement conclusion is accepted as an input assumption. |

The complete APPLY checker now also has a construction-to-acceptance proof:
`FamilyApply.checkedFromConstructed`. Its next-model and next-optimizer tables
derive canonicality from the same source input tables and exactly the same shard
keys; no whole APPLY-body canonicality premise is supplied. The remaining
primitive conditions are canonical checked authority/names/checkpoint and the
existing encoded-leaf uniqueness check. `coordinateComputesNextCells` derives
the scalar mixture/optimizer result for each original shard-local selection from
the current values in that input image to the next values encoded in this body,
using the same original global offset and ordered converted rows.

No top-level R2 obligation is declared closed by counting helpers or fixtures.
The three obligations and their existing safety meaning have not changed.

The source-loader path is now constructive on its explicitly checked domain:
`FamilyInputs.corpusLoaderComplete` derives the exact original block/row/frame
loads, including unique shard lookup. `projectFromComputed` derives the exact
family input load, and `FamilyRelation.inputsLoaderComplete` composes it with
the same authority and configured width checks. These are equalities to the
executable loaders, not extra successful-loader assumptions. They do not supply
missing source artifacts or establish that every originally admitted source
has such a complete input image. In particular, OMIT_UNAVAILABLE coverage and
general input-encoding canonicality from primitive configuration remain open.
`parameterBodyConstructorTotal` and `applyBodyFromConstructed` then connect this
same source/input loading directly to the complete PARAMETER and APPLY body
gates. The constructed candidate is the checked result, not a supplied whole
body equality. For APPLY, `applyConstructorTotal` supplies the preceding
construction from the same native result and the existing checkpoint boundary;
primitive canonical names and exact encoded-leaf uniqueness remain explicit.

`FamilyAuthority.checkedAuthorityFromConstructed` also removes the premise that
the complete authority value is already canonical. It reconstructs the original
atom/header/commitment loaders, then assembles ISC/seed/EC/APC and the complete
authority from primitive canonical metadata and exact encoded-set uniqueness.
The supplied input image must still be the existing checked complete encoder
result. This does not establish that such an image exists for omitted inputs,
and does not authenticate a public alias or configuration by itself.

## Exact source and domain limits

* The family selection removes `shard.length = 1`. The previous original manifest
  binding and ordered reconstruction for widths 4/8/8/8/8 remain unchanged. A
  coordinate is a representation index; it creates no native shard, signer,
  certificate, vote, current pointer, receipt or WAL sequence.
* PARAMETER constructor completeness derives equality of both loaders' frames
  from the same canonical store, locates the original assignment and derives
  full original row equality. It does not demand first-vote freshness for an
  already stored historical arithmetic record.
* `applyConstructorTotal` and `FamilyRoot.constructorTotal` quantify over all
  original corpus entries. They require the existing named primitive metadata
  boundary and already checked family input authority; they do not prove that
  this authority exists for every native admitted source. Missing aliases,
  payloads and noncanonical public values are rejected by the executable checks.
* `FamilyAuthority.omittedMemberRequiresInputCompletion` proves an actual
  remaining restriction: the current input image lists eligible tickets, so a
  committed ISC member omitted by EC cannot be hidden by an injective alias map.
  Closing this requires source-complete configured inputs or a justified latent
  input relation under the existing contract. No unknown Q bytes were replaced
  with zero, no member was dropped and no availability rule was changed.
* `unsignedDenominatorIsOriginalDomain` and `unsignedOptimizerComputes` show an
  original profile with learning-rate denominator 2^63, accepted by the original
  fraction domain and numeric optimizer graph, while the older signed-denominator
  adapter excludes it. The new numeric graph covers it, but the full body/source
  adapter has not yet been generalized. This is an adapter gap, not evidence that
  production Init/Next or certificate/WAL semantics must change.
* Domain-weight denominators differ from optimizer denominators:
  `nativeLcmScale` equates the exact native `initial * (denominator / gcd)`
  recurrence with LCM, and `originalMixtureLcmCompletes` derives the old signed
  denominator/prefix checks from the native engine's existing final
  `LCM <= INT64_MAX` guard, for arbitrary ordered weight lists. This particular
  representability restriction is now justified numerically, without a new
  native guard. Connecting that result to the complete source loader remains.
* Normalization is already required by amendment 0001 and `ABInputsValid`.
  `NativeApplyProfile.Valid`/native profile canonicalization alone does not
  establish it. The family input image currently derives normalization through
  a checked `WeightPlan`, not from arbitrary decoded profile validity. The same
  normalized immutable configuration must still be source-bound; profile syntax
  acceptance alone is not native admission and is not an architectural
  counterexample. No production-predicate change is inferred from that gap.
* The general body path still depends on the older binding's domain restrictions
  (including fraction bounds, identifier/layout projection bounds and complete
  source availability). These must be derived from actual source guarantees or
  removed in the refinement adapter; they are not new native admission rules.
* The existing checkpoint checker maps a separately configured model symbol to
  the exact computed next-model hash spelling. Authentication/coherence of that
  configuration and the whole current/certificate relation remain open. No new
  checkpoint ID is invented and a structured TLA vector is not a crypto ID.
* The original004 vector artifacts still lack a joined native vector vote/QC/WAL
  capture. No original008 scalar identities or synthetic certificate were joined
  to them. This does not add a new exporter project or automatically classify R2
  as BLOCKED_EXTERNAL.
* The source-reviewed mathematical optimizer graph is not a C++ execution or
  compiler correctness proof. Named codec/hash/metadata/authentication boundaries
  remain explicit. `MetadataTrust` is not replaced by a fabricated complete map.

## Why the remaining work is finite

The remaining work is confined to the same three interfaces: complete input
coverage, numeric domain coverage, and static source/configuration/state
composition over the existing schema/actions. No theorem per vector length is
needed. No additional protocol object, universal ABORT-body gate, production
exporter, new model configuration campaign or R8 is introduced. Preservation of
the relation through transitions and recovery is R3 and has not been attempted.


## Exact remaining interfaces (no new obligation)

1. **R2.1 / configured inputs:** `FamilyInputs.project` derives `tickets` from
   `corpus.frame.plan.tickets` (the eligible set). `FamilyAuthority.Projection`
   also requires every original ISC member to be in the configured vocabulary.
   `omittedMemberRequiresInputCompletion` proves these disagree when EC omits
   a committed member and aliases preserve identity. Complete the original ISC
   input namespace, or justify the existing abstraction of unobserved inputs;
   never change the original ISC/EC membership or assert unavailable bytes.
2. **R2.1–2 / source-domain coverage:** the path still reaches
   `NativeVectorLayout.Small`/`LayoutChecks`, `NativeVectorArtifacts.QChecks`,
   `NativeBinding.ParameterFrameValid` and the existing profile/Apply checks.
   Their 4096-coordinate/Q-vector caps, generated ordinal/decimal identifiers,
   name/encoded-size bounds and signed fraction restrictions have not all been
   derived from the original admitted domain. The family relation itself does
   not need a theorem per length. The demonstrated unsigned optimizer case is
   mathematically covered but still rejected by this older body-source path.
   Every retained restriction must be justified from the frozen source contract
   or removed in the representation adapter, without altering native admission.
3. **R2.3 / common configuration and complete static state:** bind the one public
   configuration/identity, vocabulary, primitive metadata and checkpoint mapping
   to the same original source used by `checkConfiguredArithmetic` and ROOT.
   Then compose the existing CONFIG/ISC/EC/APC/PARAMETER/ROOT/APPLY/VIEW/ABORT
   projections and the full existing `PublicState.fieldNames` inventory,
   including exact certificate/vote contents, current, availability and unknown
   observations. Arithmetic-only acceptance must not stand in for this complete
   relation. ABORT needs only the already frozen sufficient projection; there is
   no new universal full-body requirement. Transition/recovery preservation is
   excluded here and remains R3.

The remaining configuration and namespace work is a checked correspondence under
named hash/authentication assumptions, not a request for production crypto or an
independent exporter project. No production-predicate change has been shown to be
necessary. This checkpoint remains local work in progress, not BLOCKED_EXTERNAL.

## Self-review and scope check

The constructor existence statements start from source-bound `Corpus`, `Binding`
and checked `Projection` values. They prove the constructors and their executable
gates on that domain; they are not a proof that every originally admitted source
loads through the older restricted adapter. The original unsigned optimizer
counterexample remains rejected by that adapter and is not hidden by widening
the public result bound. Likewise, normalized configuration is not inferred from
mere profile syntax validity. No body equality, whole-state translation or final
refinement theorem is supplied as an axiom. Named metadata/hash/signature
assumptions and the checkpoint primitive convention remain visible.

No production change was needed for the work completed here. That is not a proof
that no further correspondence obstruction exists. R2 remains OPEN; the proposal
has no new merged authority or GO report, and R3 was not started. The residual is
the same finite input/domain/static-state interfaces listed above, with all
length-specific family construction removed from the remaining work.

## Reproduction

From the candidate root:

```powershell
C:/Python312/python.exe -X utf8 formal/proposals/b-family-transfer/check_constructors.py
```

The runner checks protected-source/DoD/semantics equality, reproduces the original
byte-source artifact inventory read-only, compiles fresh isolated proposal
kernels, audits every named local declaration and pins the complete local proof
dependency closure plus inspected C++ sources. Allowed axioms are only `propext`,
`Quot.sound`, `Classical.choice`. The small numeric checks exercise unsigned
denominators, negative rounding, signed minimum rejection, overflow despite zero
learning rate and exact vector shape; they are not finite approval tables.

Evidence: `../evidence/b-family-constructors/checks.json` and
`../evidence/b-family-constructors.json`. No fresh TLC, new native execution,
complete `make formal-check`, independent attestation or Formal GO is claimed.
