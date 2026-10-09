# First EC Producer Source Contract v1

**PROPOSED; specification only; R2.3 OPEN; Formal NO_GO.**
9 October 2026. T047/T053, ISC-S16-D01. No implementation or proof is supplied.

## 1. Authority and the decision to be made

Scope 16, decision `scope-decision-b27fceadfac527a03e40eea001457515`, permits
this bounded proposal and an exact source-bound Pending request, then STOP.
Coordinator assignment `f14e1fce-76fe-4cc0-91b0-96e5d22961b0` acknowledged it
with `scope-ack-baaefdb170635084a400908b14bbd979`; a subsequent GET confirmed
the exact context. This permission does not select the producer rule below.

The proposed choice is **EC-SOURCE-STEP-v1**: an independently executable
first-finalization rule over the existing native source state and original
received-vote prefix. It constructs one original EC and its exact policy delta.
It reuses the Profile-v1 source-index event container and native body/certificate
bytes. It creates neither a certificate protocol nor a storage capsule.

Approval would select a new, future native-source producer rule for isolated
feature000 formal/reference work. It would NOT certify that an old runtime
produced these events, install recovery, close R2.3, assign a concrete semantics
ID, or approve a production WAL encoding. Other source producers still require
their own existing, independently checked origin; they are not assumed correct
because this EC step succeeds. The frozen three residuals are unchanged.

## 2. Existing contracts: exact applicability, not inferred authority

The accompanying `first-ec-producer-source/source-index.json` records complete
commit/path/raw-SHA256 references. Abbreviations here expand there:

- **N** = `60c692f6e391f839829dfc64e93380db54cd507b` (native contracts).
- **P** = `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` (Profile v1/W1).
- **A** = `bb9fce957dae329701a8cd473a7148e198e1ca12` (SIG-NON-ISC).
- **L** = `e389e1869ddac63c7d529a1e83d3b153d1669f36` (reviewed EC boundary).

| Exact source | Reused fact; limit |
|---|---|
| N:`delta-core-cpp/include/delta/core/consensus.hpp` | `VoteEligibilityBody`, `VoteFinalizedEligibility`, full `VoteAdmissionSnapshot/Policy`; carriers are not a producer |
| N:`delta-core-cpp/src/consensus.cpp` | `vote_eligibility_body_id`, EC context hashing, `project_eligibility_vote_body`, `VoteJournal`, `validate_quorum`; no P0-to-P1 first-EC operation |
| N:`delta-core-cpp/src/certificates/contracts.cpp` | Exact EC fields/order, full signer list, content-ID domain; no witness selection from a received cut |
| N:`delta-core-cpp/src/certificates/{vote_admission,verifier}.cpp` | Full typed context/parent/quorum/membership checks; supplied valid EC is not its first producing event |
| N:`delta-core-cpp/src/robust/plan.cpp` | `build_plan` computes norm/EC/APC arithmetic from contributions and a caller-supplied signer list. It has no first-finalization state guard, authenticated delivery selection or durable policy update. Its `PlanResult` is not the missing producer |
| N:`delta-runtime-cpp/{src/runtime.cpp,src/vote_codec.cpp,include/delta/runtime/runtime.hpp}` | Immutable startup policy; policy codec and existing journal replay. Reusing kind 1 without an EC command/policy replay contract would be an unapproved extension |
| P:`docs/adr/0013-snapshot-provenance-profile-v1.md`, §§3–6 | Independently selected producer rules, complete source prefix and original journal continuity; no public-success substitute |
| P:`docs/adr/0014-isc-finalization-wal-capsule-v1.md` | W1 is ISC-only; it is not an EC persistence format |
| A:`docs/adr/0015-non-isc-authority-binding-v1.md`, §§5–7 | Original NSG1/Vn, exact seed sidecar, actual finalization cut and unchanged non-ISC certificate identities; explicitly no producer |
| L:`formal/proposals/b-family-transfer/ProfileCertificateVotes.lean` | `matching`, `GroupCompatible`, `Quorum`, `originalFinalizationCut`; bind an original supplied witness, not its production |
| L:`formal/proposals/b-family-transfer/ProfileSourceIndex.lean` | Original events, backward dependencies, exact artifact resolution and multiplicity; byte materialization alone grants no legality |
| L:`formal/tla/DeltaReduceCertificates.tla:303–374` | `VoteEC` / `FinalizeEC` target, including all delivered signers and first EC for an ISC. This is the refinement target, never a native-origin oracle |

The L boundary audit already inventories 92 native source/header files and 98
immutable sources. Those hashes are rechecked with this proposal. No newly
supplied applicable original producer contract was found in the selected sources
or approved decisions. This is not a new global absence theorem and not evidence
of an impossible or forged production history. In particular `build_plan` does
not resolve the audited missing state edge merely because it returns an EC.

Alternatives rejected: assume validity of a supplied certificate/policy; call
public `FinalizeEC` as the native checker; select a convenient quorum later;
canonicalize all EC witnesses to a new body ID; extend W1/kind 1 silently.
The proposal instead makes the missing state-edge rule explicit for selection.

## 3. Complete inputs and independent source interpretation

For event position j and original receiver a, the source fold supplies:

1. The complete previously reconstructed native state: RoundState, full policy
   P0 and all snapshot collections, current tuple, source configuration/aliases/
   units, admitted-delivery inventory D0, original journals and recovery status.
   Their origin is derived from the pinned genesis and earlier native steps.
   P0 is not an arbitrary caller-selected initial policy or a public snapshot.
2. The independently pinned epoch registry/codec/producer/schema/build profile,
   four original validators with q=3, and unchanged fixed-epoch Profile v1.
3. The original `VoteEligibilityBody` already present in P0's
   `eligibility_bodies`; its full seven-field Context, ISC consensus body b,
   seed transcript, norm evidence, robust profile and all ordered entries.
   It must have its earlier source-producing dependency. Existence in P0 alone
   is not the proof of that dependency.
4. Original ISC witness C/c resolving b under approved I-B, seed and norm bytes,
   original robust/configuration references and their checked backward origin.
   No C/c may occupy an ISC b position. The EC seed sidecar remains mandatory.
5. Every original admitted receive occurrence at a before j, with exact Vn/Gn,
   sender/receiver, original source position, context and sender physical slot s.
   Earlier rejects, duplicate deliveries, faults/losses and unrelated events
   remain in the whole source history. An admitted inventory is computed by the
   selected authentication/admission rules, not by trusting an `accepted` flag.

All input objects resolve through the complete original artifact inventory.
Missing provenance is a failed premise to be established by the enclosing source
fold, not a new trust assumption or permission to drop the history. This step
neither generates a seed/norm nor chooses a new robust algorithm. An unresolved
upstream producing rule remains an explicit residual, not certified sufficient
by this document. No public state, projection result or R2 success is an input.

## 4. Proposed first-finalization rule

The source receiver must be the original local validator for the reconstructed
policy. Its original round/epoch/config/current context must match the supplied
native objects. The fold must show a recovered, ordinary active state at the
original logical tick, before the immutable hard deadline, with no existing
round abort requirement/terminal. These are native checks of the existing
failure contract, not a call to `Next` or a supplied Boolean `can_finalize`.

Resolve b to an already finalized original ISC; check seed and norm refer to b,
the selected robust profile and Context are unchanged, and every EC entry has
the exact original ticket/domain placement and valid arithmetic evidence. Reuse
the native full-membership, ordering, rational and bound checks, together with
the existing source/body computation requirements. Do not turn structural
`verify_eligibility` success into proof of norm/entry production.

The **new selected producer guard** would be:

> No certificate referenced by `P0.finalized_eligibility_ids` has this ISC
> consensus body b. Resolve each ID to its original complete EC; a missing
> object is an error, not evidence that no EC exists.

This key intentionally uses b, not (b, seed), (b, view), c, an arbitrary body ID
or receiver arrival order. It corresponds to the existing public first-EC key.
It does not rewrite the signed EC context hash or any old certificate identity.
Initial/recovered nonempty state reaches this guard through the same full native
history fold; it receives no exemption and is not erased to force acceptance.

Let h be `vote_eligibility_body_id(B)` and k the existing
`deltareduce.vote-context.ec.v1` hash over b. Select from D0 **all** occurrences
at receiver a, before j, matching EC kind, symbolic future semantics, h, k and
the whole original round/height/view/epoch. A row in this h/k group with different
coordinates must not disappear through filtering; its original admitted status
must be rejected as inconsistent. Invalid network attempts remain classified
and retained outside the admitted set.

Let S be the ASCII-sorted distinct original validator IDs of these rows. Require
S is a subset of the independently provisioned four-validator set and |S|>=3.
Each counted row must already have the selected strict NSG1 signature check,
exact source/journal association and original native vote admission. Duplicate
delivery of one vote does not add power. A different original sequence/intent
for an occupied journal key cannot be normalized into that vote. Existing
Byzantine conflict evidence remains retained; this rule adds no quorum power.

Construct E by copying B's Context/entries/ISC/norm/robust fields, setting
`quorum_threshold=3` and **signer_ids=S**. Serialize the existing EC shape under
the selected future non-ISC generation (schema 2, symbolic semantics), then use
the unchanged domain `deltareduce.008.eligibility-certificate.v1` for e.
Retain `VoteFinalizedEligibility{certificate=E,seed_transcript_id=B.seed}`.
Neither seed nor signer IDs are dropped from their original signed association.

The event's original E bytes, seed and e must equal this computation exactly.
No witness is reconstructed from a later snapshot cut. Three matching signers
produce the original three-signer E; four already present produce four. There
is no wait for a particular validator or a canonical first-three subset.

Compute P1 from the **whole** P0:

- insert the exact E/seed pair into `eligibility_certificates` in existing e
  order; an existing equal e must contain exactly the same pair, otherwise fail;
- insert e into `finalized_eligibility_ids` in existing order;
- preserve every other snapshot/policy field, original RoundState/current,
  candidate, other certificate, source occurrence and journal byte unchanged.

An identical retained but not-yet-finalized witness is reused, not duplicated.
Unrelated nonempty downstream/history collections are not cleared. Every full
P1 validity and cross-collection constraint must still hold; the two-field
footprint is not a waiver. Its canonical policy bytes are computed and compared
with the next source pre-state and any materialized cut. The source event does
not get to supply arbitrary P1 or assert P1 is public-representable.

## 5. Source bytes and journal association: no new capsule

Use the existing Profile-v1 source event descriptor with exactly
`action_id,actor_id,dependencies,input_refs,original_ref`, canonical control JSON
as specified in P §3. Proposed action interpretation is `ACT-EC-FINALIZE` for the
first-finalization event. The label is not proof of its legality.

`original_ref` resolves the exact canonical EC E bytes, with both the Profile
artifact raw SHA-256/length check and the independently recomputed native e.
These hashes have different preimages; neither replaces the other.
`input_refs` is the following exact ordered list of original artifact refs:

```text
complete P0 policy; prior native RoundState; VoteEligibilityBody B;
original ISC witness C; seed transcript; norm evidence
```

Those objects must equal the objects already derived at this event by the fold.
The body artifact is the exact binary hash preimage of N's
`vote_eligibility_body_id`, represented by L's
`DeltaReduce.NativeEligibility.bodyBytes`: big-endian Context/entry encoding,
u64 entry count and length-prefixed ISC/norm/robust/seed IDs. It is not the
different embedded runtime policy codec fragment or ad-hoc JSON. Its decoded
body must equal P0's original typed proposal. All further referenced
robust/config/Q and cryptographic artifacts resolve
through the same original inventory and earlier dependencies. The selected
schema set fixes these six formats; an imported object cannot select a parser.

The event's backward dependency indices are exactly the sorted unique union of
the prior native state-producing event, those original prerequisite-producing
events, and every matching admitted delivery occurrence before j. The immutable
genesis is resolved from the existing root, not a fabricated event -1. Full D0 is
derived by scanning the whole prefix, **not** by trusting this dependency list;
recompute and compare the list so omitted fourth signers/duplicates are detected.
Every source event outside this list remains in the original complete prefix.
This is a proposed interpretation of the existing container, no new wire field,
source certificate, signing preimage or producer authenticity credential.

The P0 journal prefix is linked through the existing `original_journal_refs`,
manifest cuts and independently retained T journals. Every counted local vote
must retain its original kind-2 intent/signature association, slot s and
persist-before-sign/expose ordering. Remote votes retain original signed s and
observed deliveries; no remote private journal is synthesized or required anew.
The EC source event itself is **not** assigned a fictitious WAL slot or vote
ordinal. S-RANK and every existing kind-1/2/3 record remain unchanged. No new
vote, signature, receipt or WAL append is manufactured by verification.

This source rule computes a logical native finalization. It is deliberately not
a new native durable storage implementation. Actual append/barrier/commit/expose
evidence, wherever claimed by a source, must still use an independently selected
storage contract and original records. W1 cannot establish EC durability; neither
can an EC/source hash. An absent concrete EC commit encoding cannot be replaced
by a `durable=true` assumption. Selecting that production encoding is outside
this proposal; no claim that the historical N runtime supports it is made.
Source-level construction can be proved independently, but alone is insufficient
to close full snapshot/journal recovery or declare READY. This limitation must
remain visible in the composed R2 evidence, not be moved into a hidden axiom.

## 6. Retry, conflict, incomplete sources and failure

| Original event/cut | Required behavior |
|---|---|
| First admissible EC, all checks pass | Construct E/e and the exact two-collection P1 delta above |
| Exact re-observation/retry of the prior finalized E/seed | Resolve the original producing event and witness; no second finalization, vote, ID or slot; current policy/other lineage stutters |
| Same b, same body, different signer witness after first finalization | Keep both original artifacts/arrival occurrences; do not replace E, append a second finalized ID or relabel witnesses. This is not an identical replay. Any separate receive/cache action must use its existing rule |
| Same b, different body/seed/view/context after first finalization | Fail first-finalization guard; preserve conflict/source evidence and original state; no partial P1 |
| Original quorum not yet delivered, incomplete prerequisites | No EC step; preserve incomplete prefix and existing attempts. Import cannot certify a materialized finalized EC at this cut |
| Unknown/corrupt required source bytes or journal continuity | Fail closed; no truncation, invented empty history or interpretation as verified absence |
| Crash before source finalization commit | No externally exposed durable finalization may be inferred. Preserve original pending/unknown evidence; restart requires existing recovery verification |
| Complete original finalization survives crash | Reconstruct the same original E/seed and P1 from its original cut; do not rebuild S from later deliveries |
| Loss/corruption after lawful EC, or subsequent ABORT | Retain E/e and downstream lineage. Availability/recovery/abort follows the selected existing rules; do not erase the EC to restore an earlier state |

These are source verification outcomes, not new ABI status codes or new public
failure terminals. An exposed-without-required-durability history is not repaired
by choosing a smaller cut. Unknown storage cuts remain unknown until verified.
No claim of faithful physical availability is added; the selected O semantics
and rejection of factual-history trust F remain unchanged.

Different admissible arrival cuts may yield different signer-dependent EC IDs.
They are distinct original histories/witnesses, not evidence of byte-identical
certificates. This proposal neither merges them nor applies ISC I-B to EC.
Later APC/QC references continue to name the exact original e. It does not prove
cross-node convergence of downstream witnesses: the complete source/refinement
and existing quorum/liveness gates must check that obligation without assuming
it. Failure there is a STOP, not permission to add an EC body-identity rule.

## 7. Compatibility and finite qualification boundary

| Surface | Consequence of selection |
|---|---|
| Native producer semantics | NEW independent first-EC state-edge contract; not mere authentication. It excludes histories with a second first-finalization for the same b, missing cut provenance or retrospectively changed witnesses |
| Certificate/signature semantics | EC fields, original Context/body preimages, signer semantics, NSG1 and seed sidecar unchanged. The source guard is new; it must be qualified, not described as legacy runtime behavior |
| Signed bytes / EC and downstream QC IDs | No additional byte change relative to the already approved future generation. Original signers/parents imply the same e; different cuts can imply different e. Nothing migrates, resigns or relabels old objects |
| ISC b/c | Unchanged approved distinction; neither is redefined as EC e |
| WAL | No changed kind, byte format, s, S-RANK or existing receipt. Concrete EC durability is not supplied by this source interpretation |
| Production TLA Init/Next | No edit selected. Existing VoteEC, delivery, FinalizeEC, replay/failure actions are targets. If the rule cannot refine them with all original state retained, STOP before any change |
| Liveness | All eligible signers at the original cut, q>=3; no fixed signer subset/wait-for-four. Full fair-scheduling/downstream liveness is still an obligation, not proved here |
| Formal identity/evidence | Future producer/schema interpretation pins must be qualified; no concrete sigma. Old evidence keeps its old scope; it does not cover this new native-source rule |

No new event/byte caps are selected. Use existing Profile-v1 limits and stricter
native per-object limits, check exact source-index and policy sizes. Do not borrow
W1 ISC budgets or delete input refs/events to fit. Universal representability
and complete domain coverage remain to be proved; a new cap would require STOP.

If selected, the bounded implementation surface is:

1. `formal/reference/profile_source/ec_finalization.py` and the corresponding
   existing source-event dispatch/validation: the six-reference interpretation,
   computed whole P0/P1, prior delivered group, unchanged original IDs.
2. `formal/proposals/b-family-transfer/ProfileEcFinalization.lean`, composed with
   existing `ProfileCertificateVotes`, `ProfileEligibility`, `ProfileSourceIndex`
   and `ProfileInstalledState`; only necessary integration edits there.
   Required conclusions: computed original witness/all-cut signers; first-key
   exclusivity; exact two-field delta and preservation of all remaining fields;
   original-event/journal multiplicity; exact retry; rejection of altered cuts.
3. Focused source vectors/checker and `formal/proposals/evidence/profile-ec-finalization/`
   receipt, added to existing profile-source regression. They must distinguish
   three/four signers, duplicate receive vs duplicate vote, wrong seed/b/c/epoch,
   earlier/later cuts, missing body origin, competing witness after finalization,
   nonempty unrelated lineage and incomplete/ABORT/crash prefixes.

The proof must derive producer success from those independent native inputs;
`producer_valid`, successful public `FinalizeEC`, whole-state equality or accepted
R2 cannot be assumptions that hide this obligation. Induction over the full
source history still has to establish P0 and admitted deliveries at every step.
These concrete conclusions are acceptance criteria within the existing residual,
not a new hierarchy of independent proof gates or a declaration of total closure.

Requalify affected source/schema/bytes and full profile regressions, Lean kernel
and axiom audit, certificate state/effect refinement, safety/liveness scenarios,
production mutants and formal compatibility under the existing mandatory gate.
R1/R2.1/R2.2 remain closed for their original domains. The reviewed L boundary
report remains accurate. No earlier failing recovery theorem/gate becomes PASS
because this proposal or a helper is accepted. Ordinary two-process reviews
remain necessary; the same sequential executor is not independent attestation.

Planning estimate, not an execution budget or GO promise: 10–18 active hours for
the source rule/checker, Lean composition and focused qualification above. Whole
R2.3 closure and concrete EC durability/recovery are excluded from this estimate;
their sufficiency is not established. No EC producer code/proof/schema is changed
in this specification pass. After the exact Pending request, STOP for selection.
