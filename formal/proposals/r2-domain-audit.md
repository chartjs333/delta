# R2 checkpoint: the current complete-body bridge excludes vector shards

Tasks: T044, T053–T057. Status: **ARCHITECTURAL_BLOCKER_IN_CURRENT_BRIDGE**.
R1 remains CLOSED and accepted by the user. R2/R3 remain OPEN. This diagnostic
does not change the accepted R1–R7 Definition of Done or introduce a new gate.

## Established result

`r2-domain-audit.lean` checks the following facts against the existing candidate:

- Every `PublicParameterJoin.Body` entails `native.partition.length = 1`.
  Consequently a native result with a longer shard has no such body at all:
  the complete loader returns `none` for **every** candidate, alias vocabulary,
  metadata source and `ModelLimit`. This is not just a failed positive fixture.
- Every `PublicApplyJoin.Body` likewise entails length 1 for **every** shard of
  its certified source corpus. A single vector shard rules out that relation.
- The already checked original manifest has block lengths **4, 8, 8, 8, 8**.
  Its partition therefore lies outside this complete-body bridge. This reuses
  the existing original-manifest source theorem; it is not a new runtime run,
  an authenticated exporter, or a joined native admission/recovery execution.
- Separately, the current PARAMETER result guard rejects `INT64_MIN` for every
  permitted `ModelLimit`, not merely limit127. This is a limitation of this
  checker. It is not a claim that this particular PARAMETER endpoint is reachable
  from the original int16-Q production source, nor a new native precondition.

The first two results are general statements about the existing complete-body
APIs, not a proof that every possible vector refinement is impossible. Earlier
components correctly recorded their scalar restrictions. What is now established
is that composing those APIs unchanged cannot close R2 over its accepted domain.
No amount of ABORT-body completion or additional metadata can repair that type
restriction. The blocker is local proof/model representation, not BLOCKED_EXTERNAL.

## Existing obligation and fixed domain

PO-AB1 (`proof-obligations.md`, arithmetic binding statement) already requires
every allowed width/vector length and the whole recomputed result. Amendment
0001 already binds complete schema offsets/lengths and every coordinate. R1's
`candidate-contract.md` expressly retains that domain and forbids treating scalar
checker restrictions as native admission restrictions. These requirements predate
this diagnostic; none is added here.

`DeltaReduceArithmetic.tla` explicitly models one coordinate per shard, while
`DeltaReduceReduceApply.tla` stores one scalar PARAMETER value and a scalar model
value per shard. `NativeScalarProjection`, `NativeInputProjection` and the public
complete-body APIs implement that representation. The native source/schema and
arithmetic modules already retain vectors. The missing general representation
link is therefore substantive, rather than a metadata equality left to fill in.

## Residual delta and bounded continuation

No additional top-level residual has closed in this checkpoint:
**R1 CLOSED; R2 OPEN; R3 OPEN; R4–R7 deferred.** The reduction is diagnostic:
the proposal to close R2 solely by composing the existing scalar complete-body
constructors has been ruled out. It must not consume further proof work under
the assumption that it covers native vectors.

The next change stays within R2: make the arithmetic image retain the original
shard and its ordered coordinates, together with separate existing accumulator
and output bounds. Either a vector-valued image or a coordinate-wise family must
be connected to the existing formal actions with a proved, faithful relation.
A family is not sufficient merely because each coordinate computes correctly:
one original vote/context/certificate, atomic admission, all-coordinate coverage
and the complete state-root preimage must still be retained. Splitting one native
vote into independent public votes, dropping coordinates, or shrinking admission
to scalar shards is not an accepted repair.

After that representation link, the remaining R2 work is still the same fixed
source/configuration/alias/parent/body/state correspondence, including sufficient
ABORT identity and terminal/current projection. R3 is still preservation of that
relation over the existing phase, persistence, exposure, delivery/QC/current,
crash/unknown/recovery/replay transitions and complete prior state. The residual
is bounded by that existing data/action vocabulary and those statements; it is
not a promise about proof-search time or an invitation to add helper-layer gates.

The independent universal full public ABORT-body constructor remains FUTURE WORK.
No R4–R7 acceptance work, runtime/guard change, full formal gate or new GO report
was performed. The Lean file lives in proposals as a diagnostic of the unchanged
candidate, outside the mandatory theorem registry. Its own source and imported
candidate dependencies are recorded separately; it does not silently claim to be
part of the candidate semantics digest or discharge `nativeArithmeticRecoveryRefines`.
