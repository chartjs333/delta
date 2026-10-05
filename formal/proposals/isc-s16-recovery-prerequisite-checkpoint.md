# ISC-S16-D01 — recovery prerequisite checkpoint

Task IDs: ISC-S16-D01, T047, T049, T053, T057, T060, HR008-018.
5 October 2026. **INSUFFICIENT WITHIN AUTHORIZED SCOPE — NEED_DECISION.**
Source: `74cbca071dba1586a94eedfad56e7501b378864e` on
`agent/isc-s16-formal-linkage`. Assignment:
`5ed18c16-bc68-4657-977e-475a0083cee5`.
Only the prerequisite investigation was performed. No proof, model, schema,
production code or historical evidence was changed. The reviewed coordinator
scope decisions were merged; the earlier formal NO_GO remains in ancestry.

## Required statement, without manufacturing a Lean declaration

The exact registry target is `DeltaReduce.nativeArithmeticRecoveryRefines`,
`PO-AB1:admission-recovery-refinement`, in
`formal/proofs/DeltaReduce/ArithmeticBinding.lean` (registry:
`formal/scripts/check_lean_evidence.py:23–31`). There is **no existing Lean
signature or proof** for this target and no axiom-audit result. An invented
`True` theorem, an empty-journal specialization, or a wrapper around a premise
called refinement would not implement its required statement.

The required content is fixed by PO-AB1's final recovery conjunct,
`candidate-contract.md` (R2/R3 section), and frozen residual R3. In precise
acceptance notation, with names below used only as prose and not new predicates:

For every original native initial/source cut allowed by the frozen contract
(genesis or a verified reachable-history cut; nonempty import uses the approved
Profile v1), every finite allowed admission/persistence/exposure/send/delivery/
QC/current/crash/restart/recovery/retry history, and the already allowed primitive
trust assumptions, derive a synchronous family of public states over all original
coordinates such that:

1. The initial and every recovered source cut satisfy the **same source-bound
   R2 relation**. The complete relevant native inputs, configuration, aliases,
   units, full PARAMETER/APPLY results, original all-actor journal,
   certificate/candidate/current/environment collections and sufficient ABORT
   lineage remain represented. No new coordinate-level protocol identity exists.
2. Every represented adjacent transition is the existing production formal
   action or documented stutter; original action context, parent/body, phase,
   signer and delivery/QC power are preserved. An unready/mismatched first vote
   has no admitted effect, journal append or current change.
3. A verified recovery reconstructs the same certified state and complete
   retained records. Historical exact retry returns original bytes, receipt,
   effect and sequence without another append, including after current advances.
4. Unknown append is not absence; durable-but-unexposed, exposure and delivery
   remain distinct. Missing/incomplete/corrupt/ambiguous observations do not
   enable READY or voting. Current changes require the existing valid ApplyQC;
   ABORT preserves current and required lineage.

This is the normalization of the existing obligation, not a newly strengthened
contract. The frozen sources explicitly say that the mandatory theorem must
**establish** the relation, not assume it. A preservation lemma conditional on
an arbitrary `R` is useful mathematics but is not this complete registry claim.
An elaborated type cannot be honestly finalized from today's modules without
resolving the missing source-to-full-state relation described below.

## Dependency cut

| Class | Exact existing artifacts | Usable conclusion / boundary |
|---|---|---|
| Existing checked arithmetic components | `ArithmeticBinding.nativeArithmeticGraphUnique`, `nativeParameterConversionSound`, `nativeApplyResultUnique`; CLOSED R2.1/R2.2 `FamilyInputs`, `FamilyAuthority`, `FamilyParameter`, `FamilyApply`, `FamilyGuards` | Retain original admitted widths/lengths and whole numeric bodies under named source/codec/trust inputs. Neither component closure nor arithmetic uniqueness establishes full snapshot origin. R2.1/R2.2 are not reopened. |
| Existing replay components | `NativeReplay.replayHasNativeHistory`, `genesisReplayHasNativeProvenance`, `preparedRecordRecovered`; `PublicRecovery.readyRecoveryDerivesAllVoteHistory`; `PublicReachability.reachableInvariant`, `reachableArithmeticPreparation` | Computed arithmetic admission, original records, exact retries, crash/unknown/scan rules. `PublicReachability.Invariant.emptyInitial` and `Reachable.initial` start an empty all-vote journal. `PublicJournal.Environment.otherAuthorized` remains an uninstantiated phase/QC boundary for this full claim. |
| Existing concrete byte fold | `NativeReplayAdmission.prepareWhole` / `wholeStartupSource`; `NativeWholeReplay.observedWhole`, `entryWholeSource`, `retryWholeOrigin` | Decode and bind **supplied** initial policy/state and complete scans. No source producer from genesis. `arithmeticScanRejected` retains current PARAMETER/APPLY refusal; using that refusal to prove the target vacuously is forbidden. |
| Existing partial static join | `FamilyRelation.Direct.loadObservedState`, `loadCertificateBasis`, `loadCertificateParameter`, `loadCertificateRoot`, `loadSufficientAbort`, `loadAbortStateLink` | Conditional durable-vote/current/config and nonempty lineage components. `ObservedState` contains durable, certified current, actor policy, current field, parents and config alias checks. It has no full source-origin/collection applicability theorem. |
| Already permitted external assumptions | FR-033 / candidate contract: named hash/codec injectivity, signatures/enrolled epoch and Byzantine threshold, independently anchored primitive metadata/artifact/certificate observations; approved Profile v1: independent bootstrap/floor, faithful retained bytes/barriers and trusted-volume custody | These may remain explicit. Actual production keys, hardware fsync proof and a universal exporter are not prerequisites of this formal investigation. These assumptions cannot supply translated body equality, successful R2 loading, full legal-origin Boolean or recovered-state equality. |
| **Open and excluded prerequisite** | R2.3 source-to-complete-family applicability under Profile v1; planned `ProfileSource.checkSourceSound/checkSourceComplete`, `FamilyRelation.Direct.profileFamilyTotal/profileR2_3Closed` | Not implemented or proved. The source-origin/complete-state connection cannot be promoted to a new trusted assumption by this exception. This is exactly the pre-existing R2.3 residual, not a new proof layer. |

“Existing checked” refers to existing proof sources and retained audit evidence;
this investigation did not rerun the Lean kernel or claim new proof evidence.
The three PO-AB1 arithmetic conjuncts are retained PASS, while the recovery
conjunct remains FAIL. The source statements and audit registration were checked.

## Minimal missing entailment and why it blocks this theorem

Take the allowed nonempty imported snapshot at independently trusted checkpoint
F, with an intact retained own journal at tip L and **no new vote after import**.
The target already has to establish the relation for that recovered cut, before
any induction step can preserve it. Correct hash/signature/floor/scan facts alone
do not derive its complete native snapshot collections and their public image.
This is the missing base obligation, not a newly executed counterexample or a
claim that a particular malicious history is production-reachable.

The dependency is visible directly in current definitions:

- `prepareWhole` decodes caller-supplied policy and state, then calls
  `NativeCandidateAuthority.bindPolicy`. `wholeStartupSource` concludes those
  decoding/check equations; it does not derive native production origin.
- `PublicReachability.initial` uses `PublicRecovery.initial actor current`;
  its invariant requires empty initial slots. Applying it to arbitrary nonempty
  imported state would require exactly the absent source/history bridge.
- `FamilyRelation.Direct.loadObservedState` checks supplied state/collections;
  successful partial checks are not total applicability on the approved source
  domain and cannot be substituted for an independent initial predicate.

Profile v1 section 4 expressly requires original native producing rules from
pinned genesis, retaining full collection membership and original multiplicity;
it forbids using public `Next` or successful R2 loading as an origin oracle.
The accepted R2.3 implementation plan explicitly allocates this missing bridge
and full static family relation to R2.3. Its planned `ProfileSource.lean`,
`ProfileChecks.lean`, `profile-v1.schema.json` and `check_profile.py` are absent.
Their absence alone is not the argument: the signatures above show the missing
conclusion that no existing imported theorem supplies.

The earlier ISC producer gap is a concrete source-side witness of this boundary:
`input_set_certificates=[] / finalized_input_set_ids=[]` to a first finalized
original ISC requires a producing/history binding, not merely validation of a
supplied certificate. The accepted W1 reference at `9744e701` only handles local
framing/storage; crypto at `af13fd25` only handles canonical/signature conformance.
Their explicit scopes exclude consensus admission and R2.3. They contain no new
TLA/Lean producer or source-to-family theorem. They were inspected at their exact
Git commits without merging reference code into this branch.

The old `ISC@1 -> EC@2 -> EC@3` API witness is **not** used as an admissible
production counterexample. No claim that production `Init/Next` must change is
established here. No certificate/WAL change, source-domain restriction or new
provenance authority is proposed or implemented.

## Finite file/check scope and routing

This checkpoint adds only:

- this `formal/proposals/isc-s16-recovery-prerequisite-checkpoint.md`;
- `formal/proposals/evidence/isc-s16-recovery-prerequisites.json` with exact Git
  input pins, source observations, scope/ACK binding and time accounting.

**Authorized proof continuation file set now: empty.** No positive sufficiency
claim exists, so no extended proof starts. After an independently resolved and
reviewed R2.3 prerequisite, a new checkpoint would need to instantiate the named
recovery target against that actual relation and bound any necessary changes to
`ArithmeticBinding.lean`, existing `PublicRecovery/PublicReachability` composition,
`DeltaReduce.lean`, `DeltaReduce/AxiomAudit.lean` and the existing proof-evidence
registry. This is a dependency pointer, not approval or a complete cost estimate.

For this document-only checkpoint: verify exact source blobs and theorem
presence/absence, scope core hash and ACK, protected sprint hashes, unchanged
production/formal source diff and historical report bytes; run `git diff --check`.
Do not run the report generator merely to overwrite the known historical FAIL.
Actual future proof qualification requires the existing pinned build/axiom audit
and applicable formal/refinement/compatibility gates, with new source-bound
reports rather than historical relabeling. No additional gate is introduced.

Route **NEED_DECISION** through the two existing process reviews to Coordinator.
Approval of this accurate blocked report does not authorize R2.3. Coordinator
cannot select extended-proof RESUME_FORMAL on this result; a user scope decision
or an externally supplied exact qualified R2.3 dependency is needed. Keep the
existing graph/assignment history and accepted reference work; no unchanged loop,
new sprint or reimport. Formal GO remains NO_GO; process roles here are the same
sequential executor and are not independent attestations.
