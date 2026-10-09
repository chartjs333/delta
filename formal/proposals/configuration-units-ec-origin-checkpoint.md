# ISC-S16-D01: schema-3 configuration composition and first-EC origin

T047/T053. 9 October 2026. Assignment
`13069d7e-a148-475a-bd49-9885bf2f283d`, scope 15, source base
`4dea988bae971c6b05f004319764a220cd9e4717`.

**NEED_DECISION / R2.3 OPEN / Formal NO_GO.** The new decision concerns the
missing independent first-EC native producing contract, not permission to work
on R2.3, units, W1 or crypto again. Scope 15 and exact ACK
`scope-ack-3af86533ad045e34125ea0b923d80680` were confirmed by a fresh GET for
this same assignment. Nothing in this checkpoint creates a new producer rule.

## Completed source conjunct

`ProfileConfigurationUnits.lean` now implements the selected complete schema-3
DRC1 configuration grammar and checks the original configuration's numeric R.
It retains all original configuration fields and validity checks. The old
schema-2 interpreter remains identical by `originalInterpreterUnchanged`.
Universal `frameEncoded` / `frameDecoded` link the new grammar to the exact
original bytes. `checked`, `complete` and `entireOriginalConfiguration` establish
the stated source conjunction and canonical numeric source, without assuming a
public state or an APC.

`admitted` and `noParentUnitOverride` check the enrolled configuration against
the supplied full current tuple, parent, height, schema and both parent units
before APC exists. The full current tuple remains present, including optimizer
and ApplyQC references; it is not replaced by a model hash. The outer source
history must still derive that parent from the independently pinned genesis or
an accepted original current transition. This helper does not prove that origin.
The existing numeric lexer completeness limitation also remains explicit.

Qualification uses pinned Lean 4.32.1, exact source/log hashes, declaration axiom
audit, 13 kernel-evaluated byte/admission vectors, focused Python unit checks,
configuration regression and the complete profile-source regression. It rejects
wrong schema/epoch/parent height/model or optimizer unit, old schema, duplicate
keys and trailing bytes. These synthetic vectors are not a valid full genesis
or an authenticated original producing history. The machine receipt in
`evidence/profile-configuration-units/receipt.json` records 66 successful commands,
165 exact source/generated hashes, 11 focused tests, 22 configuration tests and
140 profile-source regression tests. Axiom dependencies are confined to
`propext`, `Classical.choice` and `Quot.sound`. Hashes of all 98 immutable audit
sources were also rechecked. An initial Python lint failure was corrected before
the complete successful rerun; no proof or protocol gate was weakened.

## Exact dependency preventing full composition

R2.3 needs a source edge of this form, before it can establish the EC collection
of an admissible complete cut:

```text
verified prior native state P0 and original ISC/seed/norm dependencies
  + original authenticated received EC votes at that event's actual cut
  + the selected native first-finalization/retry rule
    -> exact original EC witness and the computed P1 collection delta
    -> retained original journal/source association and all unchanged fields
```

The third line is not supplied by the inspected selected contracts. It cannot
be replaced by the existence of a valid certificate or by a successful public
`FinalizeEC` action. The evidence is narrowly about this missing EC edge; it is
not another general inventory of R2.3.

| Immutable source | What it establishes; why it is insufficient for this edge |
|---|---|
| Native N `60c692f6e391f839829dfc64e93380db54cd507b`, `runtime.hpp:67–83`, `runtime.cpp:108–136` | An immutable startup vote policy is supplied and validated. No policy-producing EC transition is exposed. |
| N `consensus.cpp:543–588` | `validate_quorum` checks supplied vote IDs, signer IDs and coordinates. It neither derives a policy delta nor publishes an EC from a prior state. |
| N `certificates/vote_admission.cpp:530–558` | Validates supplied EC/ISC/seed/norm/quorum and finalized-ID membership. It does not establish the first finalization event. |
| N `vote_codec.cpp:883–892` | The EC collection assignments decode supplied bytes. Decoding is not a producing rule. |
| Selected W1, `0014-isc-finalization-wal-capsule-v1.md:342–347`; `ProfileIscFinalization.lean:153–200` at the base commit | W1 explicitly excludes EC/seed and other subsequent producer operations. Its implemented delta changes only ISC fields; other fields are preserved. |
| Selected SIG-NON-ISC at `bb9fce957dae329701a8cd473a7148e198e1ca12:docs/adr/0015-non-isc-authority-binding-v1.md`, §§1,5–7 | Supplies exact original vote/body/signature/witness binding. It explicitly adds no producer transition, does not wrap non-ISC QCs in W1, and retains independent producer/source verification. |
| `ProfileCertificateVotes.ec`, `bindEvent`, `originalFinalizationCut` at the base commit | Bind the supplied original EC to actual prior delivered vote rows and retained source position. They intentionally do not infer lawful first-finalization from quorum. |
| Existing public `DeltaReduceCertificates.tla:359–374` | `FinalizeEC` has an explicit first-finalization guard. Profile v1 §4 prohibits using public action success as the independent native origin under refinement. |
| Scope-15 Arithmetic Unit Source Binding v1 | Selects U/R/P and common-unit continuity; retains original EC/APC authority and producer rules. It supplies no missing EC producer. |

`audit_ec_origin.py` reads and hashes all 92 native source/header files in N's
core/runtime/FFI source and include directories, inventories every reference to
the two EC collections, and records the relevant immutable excerpts. Every
collection reference belongs to carrier declarations, validation/lookup or
serialization/decoding. This is bounded source evidence, not a kernel proof
of absence of every conceivable external contract. A separately applicable
immutable native contract would have to be inspected before proposing a new one.

The existing feature-008 plan names the EC-producing stage and deterministic
arithmetic. That planned stage does not provide the missing concrete native
P0/input/P1 first-finalization, original witness selection, retry and journal
binding contract. The selected non-ISC contract approval explicitly retains
"No invented producer rule". General implementation authority does not select
those absent semantics.

## Required resolution and excluded shortcuts

The coordinator should first check whether an already applicable immutable
native EC producer contract resolves this edge. If it does not, a Pending
decision must address that specific future-generation contract and its original
source association. It must not reopen R2.3 permission or pretend that approval
of the byte/signature contract already approved a new finalization transition.
This checkpoint does not propose a WAL kind, new trust authority, changed
certificate identity, concrete sigma or implementation of a new rule.

Extending ISC W1 to EC, loading an arbitrary prefilled EC policy, assuming
`legal_origin`/public success, choosing a convenient quorum after the event,
or rejecting every nonempty EC history would not close the required obligation.
There is no demonstrated production-reachable forged history or whole-profile
counterexample here, and no assertion that the other open dependencies are
already sufficient. R1/R2.1/R2.2 retain their original closed domains.

Both ordinary graph process reviews must inspect this exact source-bound
checkpoint. Approval of an accurate boundary report is not substantive R2.3
closure or an independent formal attestation. Dependent full-state composition
and the named recovery theorem remain stopped at this edge.

## Gate state

The preceding exact-source baseline at `4dea988b` passed its model checks and
mandatory Lean build, but its proof gate failed 44/45 conjuncts because
`DeltaReduce.nativeArithmeticRecoveryRefines` and its axiom audit are missing.
Those historical results are unchanged. The new component receipt is additional
evidence, not a reclassification of that FAIL. No new mandatory-project,
production model, protocol, registry, C++/ABI/Java or frozen contract change is
made here. Downstream mutant/refinement/compatibility/GO qualification is still
required after substantive R2.3 and recovery proof closure; it is not reported
as passing on the strength of this source conjunct.

The same three frozen R2.3 residuals remain: independently produced full source,
complete source/state collection relation, and initial/incomplete/ABORT
applicability with retained lineage. No D01 GO or D01-to-Q01 advancement follows.
