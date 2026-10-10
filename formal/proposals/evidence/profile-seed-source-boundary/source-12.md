# Non-ISC Validator Authority Binding v1

**Status: PROPOSED — semantic decision required, specification only.**
T047/T053. 2026-10-06. R2.3 OPEN / Formal NO_GO.

## 1. Decision boundary

Scope revision 4 of the existing Delta sprint authorizes this single document,
not its implementation or proofs that assume it. Human decision
`scope-decision-3a596d361b5328e1acaf48e2ac4699d1` approved the request at
`4cb065008d2f50bf02b83c7177bc53a4acd8aeff:orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-NON-ISC-AUTHORITY-DECISION.json`.
Coordinator assignment `e34133ee-83e7-4b4c-959f-913dc109cbf0` acknowledged
that exact scope with `scope-ack-591dddd4aac8c7b6a55e0d6a577c7262`.

The proposed choice is **SIG-NON-ISC-ED25519-v1**, explicitly selected alongside
SIG-ISC by the independently pinned bootstrap codec. It binds the eight existing
non-ISC validator vote kinds to their original typed bodies and certificate
witnesses. It does not authenticate arbitrary worker/storage/beacon messages.
There is no new validator role, threshold, authority, certificate type or
producer transition. The fixed enrolled four-validator, threshold-three epoch
of Snapshot Provenance Profile v1 is unchanged.

This is a **future source generation** contract. The old profile's prohibition
on replacing the original signing codec still applies to old snapshots. Approval
would specify a codec for newly produced objects, not authorize resigning,
upgrading, relabeling or importing old unauthenticated objects as the new version.
No concrete `sigma_next`, schema implementation, runtime change, fixture, proof,
new producer rule, R2.3 closure or GO is created here.

## 2. Reusable contracts and the actual gap

References below are immutable Git blobs, not the possibly older coordinator
working-copy implementation. `N = 60c692f6e391f839829dfc64e93380db54cd507b`;
`P = 26eb02d0632435c9aa0d8ef44eb496b6fa73dd13`.

| Reference | Exact reused material | Git-blob SHA-256 |
|---|---|---|
| `P:docs/adr/0013-snapshot-provenance-profile-v1.md` | Independent bootstrap, fixed epoch/roles, original history, floor and activation boundary | `7cd4170171d554e8f3b34f0a76e28643dfa9650dc49e06ff42526e6236063e4a` |
| `P:docs/adr/0014-isc-production-contract-amendment-v1.md` | Selected ISC bytes, K/R/E, strict Ed25519 primitive, original slot and evidence ordering | `214ca238fde93ebe2e6e08b25a6ea366b93d735333125f651398c0d0daad58fd` |
| `N:delta-core-cpp/src/consensus.cpp` | Closed kind enumeration, context IDs and non-ISC binary body hashes | `1ef9e1add61d7ce2d4de6c0bb5a00c83d34696cf8e968ce192c088f14bb201e8` |
| `N:delta-core-cpp/src/certificates/contracts.cpp` | Typed canonical certificate/candidate JSON, IDs, order and bounds | `46c0983aa3a61cc3ab510ee351d25345e6a72baf90a83f76e46ca6f29bf3d8b8` |
| `N:delta-core-cpp/src/certificates/vote_admission.cpp` | `validate_candidate_authority`, typed body and parent associations | `655b74601e163c62242a6ede4f93b2749ef32eb7828caaef9d32e7e63b8ce1ef` |
| `N:delta-core-cpp/src/certificates/verifier.cpp` | Existing structural `ChainVerifier`, including `verify_apply` | `99b0ca04e90d947b73c1409cbc046baa27dd584b1cb969e4ec7416fbe34ad879` |

The corresponding headers at N are `include/delta/core/{protocol,consensus}.hpp`
and `include/delta/certificates/contracts.hpp`. The single closed
`ValidatorRole::validator` explicitly excludes adding action-specific roles.
`VoteJournal` keys original votes by `(validator_id, validator_epoch_id, context_id)`.

The reviewed boundary at `4c99272e9e9f4640ed51cf34bef81516630329a5` is
`orchestration/sprints/isc-s16-continuous/handoffs/ISC-S16-R23-NON-ISC-AUTHORITY-BOUNDARY.md`.
`verify_apply` receives typed ApplyQC/candidate/profile/root objects and signer
IDs, but no signature bytes, keys or signable preimage. `signature_id` grammar
and typed quorum validation cannot distinguish real from absent signatures.
ADR0014 section 3 explicitly leaves other kinds outside SIG-ISC. No approved
applicable non-ISC byte contract was found in these pinned sources. This is an
authentication gap, not a demonstrated production-reachable forged snapshot.

Alternatives considered: (a) treating structural success or SIG-ISC as implicit
non-ISC authority is rejected; (b) signing a new super-certificate or snapshot
with a new custodian is rejected because it replaces original vote authority;
(c) the selected proposal signs the existing vote intent in a distinct domain,
retaining its original certificate association and independently enrolled keys.

## 3. Closed key/role selection

Reuse the exact K and R encodings, derivation and IDs from ADR0014 sections 4–5.
K contains `algorithm="Ed25519"`, `public_key_hex`, `schema_version="1.0.0"`;
`key_id=ID("deltareduce.isc-ed25519-key.v1",J(K))`. R binds `origin_id`, fixed
epoch, ordered original validator IDs/keys/`roles=["validator"]`, q=3, symbolic
future semantics `sigma`, and the existing ISC budget reference. Its ID remains
`r=ID("deltareduce.isc-epoch-registry.v1",J(R))`.

**R.signature_profile remains `SIG-ISC-ED25519-v1`.** It is not silently changed
or treated as authority for non-ISC. The independently provisioned bootstrap's
existing `signature_codec_id` must resolve to one qualified codec manifest whose
closed dispatch is exactly:

| Original vote kind | Authorized encoding/verifier |
|---|---|
| `ISC` | Exact approved ADR0014 SIG-ISC, `ISG1` |
| `ROUND_CONFIG`, `EC`, `APC`, `PARAMETER`, `AGGREGATE_ROOT`, `APPLY`, `VIEW_CHANGE`, `ABORT` | This proposed SIG-NON-ISC profile, `NSG1` |
| Anything else | Reject; no plugin, generic fallback or profile inferred from input bytes |

That independently selected codec explicitly permits the second verifier to
reuse **only the same epoch/key/validator table** in R. A previously provisioned
ISC-only codec rejects NSG1; R alone cannot enable it. The manifest uses the
existing source/build/codec qualification mechanism; no new registry or bootstrap
wire field is introduced. Its future qualified ID is not assigned here.
The issuer role for every row is the existing `validator`, not a newly invented
apply/parameter authority. Key ownership is an exact mapping from the original
validator ID; an artifact cannot supply a different public key or epoch.

K/R derivation from the independent bootstrap, unique original validator IDs
and unique keys, epoch/q equality, strict point/key checks and fixed deployment
restrictions remain mandatory. No key rotation, new node enrollment or new
epoch is implied. R's ISC budgets do not become non-ISC admission budgets.

## 4. Exact proposed signed bytes and detached artifact

`U16/U32/U64` are unsigned big-endian; `L(x)=U32(byte_length(x)) || x`;
`T4(x)=L(ASCII(x))`; `ID(d,x)="sha256:" || lowerhex(SHA256(ASCII(d)||00||x))`.
No host encoding, floating point, JSON member duplication, parser normalization,
trailing bytes or implicit default is accepted. Canonical decimal integers have
no sign or leading zero, except the single character `0` where allowed.

The non-ISC signable vote `Vn` reuses the approved future twelve-field DRC1 shape:

```text
body_hash, context_id, durable_sequence, formal_semantics_id, height, kind,
round_id, schema_version, type_name, validator_epoch_id, validator_id, view
```

Keys occur exactly once in this ASCII order. Every value is DRC1 text.
`schema_version="2.0.0"`, `type_name="VOTE"`, `formal_semantics_id=sigma`;
`kind` is exactly one of the eight non-ISC strings above. Body/semantics/epoch
IDs are exact 71-byte lowercase content IDs. Existing round/context/validator
labels retain their 1–128 ASCII `[A-Za-z0-9._:-]` grammar. Height, view and original
`durable_sequence=s` are canonical U64 decimal; s is positive. Existing source
admission restrictions still apply. No new context or slot can be invented to
make an old vote fit. The original sequence is the sender's slot, not a receiver
delivery index and not `V_a(s)`.

```text
Txt(x) = 21 || U32(len(ASCII(x))) || ASCII(x)
P = 31 || U32(12) || concat(Txt(key) || Txt(value))
Vn = ASCII("DRC1") || 01 || 00 || U16(3) || U32(len(P)) || P
vn = ID("deltareduce:003:vote:v2", Vn)

Mn = ASCII("deltareduce.non-isc-vote.ed25519.v1") || 00
     || T4(r) || T4(key_id) || L(Vn)
sig = Ed25519.Sign(original_validator_secret, Mn)       // 64 raw bytes
Gn = ASCII("NSG1") || U16(1) || U16(0)
     || T4(r) || T4(key_id) || L(Vn) || sig
gn = ID("deltareduce.non-isc-signature.v1", Gn)
```

`21`, `31`, `01`, `00` above denote individual hexadecimal bytes. There is no
`signature_id` in Vn: signing an object containing the hash of its own signature
would be circular. The source association is original vote `vn` → detached
artifact `gn`; a retained signature reference must resolve to these exact bytes.
This is the same separation already chosen for future ISC votes, explicitly
extended here rather than applied to legacy Vote bytes.

Use the **exact strict pure Ed25519 primitive and rejection rules already selected
in ADR0014 section 5** (qualified libsodium 1.0.22 single-part deterministic API,
canonical nonidentity prime-subgroup A/R points and S<L). No prehash, Ed25519ph,
Ed25519ctx, TLS, authenticationTag, structural-success flag or opaque verifier
callback is an alternative. We do not claim cryptographic security has been
proved by the formal model.

Framing lengths are checked before allocation. From the existing grammars, the
largest Vn is 946 bytes: `12+5+sum(10+key_length+max_value_length)` over the twelve
fields, with U64 values ≤20 decimal bytes and longest kind length 14. Thus
`len(Mn)=190+len(Vn)` and `len(Gn)=226+len(Vn)`, bounded by 1136 and 1172 bytes.
These are derived per-object bounds, **not new limits on source events, votes,
deliveries or history**. Original Profile-v1 bundle/control/ref limits still
apply; no retained lineage is truncated to fit ISC's event budget.

## 5. Exact body/context association and finite lineage inventory

Signing Vn binds all twelve fields. Successful crypto verification alone is not
sufficient: resolve the original body, recompute the existing body identity and
check the original typed context/parents using the immutable definitions below.
In the following table `Ctx` means the original ordered seven-field Context
`arithmetic_profile_id,height,parameter_schema_id,round_config_id,round_id,validator_epoch_id,view`.
Binary body/context layouts and hash domains refer exactly to N's
`consensus.cpp`; they are reused without adding a signature, signer set or new
field to those preimages. Their dependent future IDs are resolved exactly.

| Kind | Original signed body binding | Original context and certificate association |
|---|---|---|
| ROUND_CONFIG | Original `candidate.body_hash` from `proposed_round_config_ids`; resolve the original immutable full RoundConfig/source configuration, not an unrelated public trace hash | `deltareduce.vote-context.config.v1` over U64(height), T8(epoch); same height/epoch/current native state. Existing RoundConfig QC must retain that exact body/context/vote inventory |
| EC | `vote_eligibility_body_id(VoteEligibilityBody)`: Ctx, entries, ISC reference, norm evidence, robust profile, **seed transcript** | EC context hash domain `.ec.v1` over original ISC parent; future I-B means b here. Reconstruct exact body from EC plus retained `VoteFinalizedEligibility.seed_transcript_id`, never discard this sidecar because wire EC lacks it |
| APC | `vote_aggregation_plan_body_id(VoteAggregationPlanBody)`: Ctx, accumulator proof, bucket assignments, EC/ISC references, iteration count, seed, transcript root, weights | `.apc.v1` over original EC certificate ID. Certificate retains all original body fields and its signer set |
| PARAMETER | `vote_parameter_body_id(VoteParameterBody)`: Ctx, APC, denominator, domain, EC, input leaf IDs, ISC, result numerators, shard | Exact immutable assignment `vote_context_id`; it is separately signed in Vn and is **not** a body-hash field. Preserve original domain/shard/coordinates and complete vector, not coordinate protocol votes |
| AGGREGATE_ROOT | `vote_aggregate_root_body_id(VoteAggregateRootBody)`: Ctx, APC/EC/ISC, ordered leaves with original Parameter QC IDs, Merkle root, required keys | `.root.v1` over original APC ID; use existing aggregate Merkle construction, not ISC duplicate-last rules |
| APPLY | **Content ID of original ApplyCandidate**, not ApplyQC ID | `.apply.v1` over original AggregateRootQC ID; ApplyQC must agree with candidate/root/profile/parent/result IDs and exact Ctx |
| VIEW_CHANGE | `vote_view_change_body_id(VoteViewChangeBody)`: round, height, from/to view, observed soft-deadline tick | `.view.v1` over round/from_view; existing next-view/deadline rules. Retain original timeout and delivered vote history even outside the final successful certificate chain |
| ABORT | `vote_abort_body_id(VoteAbortBody)`: round, epoch, height/view/hard tick, parent, reason and all seven original certificate-ID collections | `.abort.v1` over round; retained RoundConfig/ISC/EC/APC/Parameter/Root/Apply collections are not emptied. Existing no-finalized-Apply/reason rules remain; no new public ABORT-body layer is introduced |

`T8(x)=U64(len(ASCII(x)))||ASCII(x)`. Context ID domains in the table all have
prefix `deltareduce.vote-context`; `authority_content_id` hashes domain||00||body
with **no hidden semantics header**. Original body hash domains/order are those
of the named `vote_*_body_id` functions at N. This proposal changes neither their binary
field ordering nor their context key. Future Vn/R bind sigma independently.

For typed canonical certificate/candidate/support objects, the proposed future
generation uses the exact N JSON layouts, ordering, integer encodings and
`deltareduce.008.*.v1` content-ID domains, replacing only their existing
`formal_semantics_id` value by sigma and `schema_version` by `2.0.0`, and resolving
dependent IDs to that same future generation. ISC B/C additionally use the
already selected explicit-parent/I-B contract. No added non-ISC body field,
new certificate envelope or in-place legacy conversion is proposed. The future
schema_set must describe these variants; old schema1/semantics bytes remain old.

The complete ApplyCandidate retains root QC, apply arithmetic profile, model
and optimizer **hashes and vectors**, parent checkpoint **and parent optimizer
hash**, plus Ctx. Its canonical candidate ID is the signed APPLY body_hash.
ApplyQC repeats candidate/root/profile/parent/result hashes and Ctx; comparison
to that exact candidate prevents swapping an unsigned optimizer/parent sidecar.
CurrentPointerCommand still names the original ApplyQC and expected parent;
it does not acquire a new validator signature or become authority itself.

The minimum anchor traversal is finite:

```text
trusted epoch/keys -> original APPLY votes -> original ApplyQC
  -> ApplyCandidate + AggregateRootQC + arithmetic profile
  -> original PARAMETER QCs/leaves -> APC -> EC -> ISC B/C
  -> original RoundConfig, tickets, commitments, availability, seed/norm inputs
```

Every non-ISC vote in the retained history is checked, including config/view/abort
events not reachable merely by following final ApplyQC parents. Ordered input
artifacts, original source events and nonempty downstream collections survive.
The eight-row inventory is closed because N has exactly nine VoteActions and
ISC is covered by the separate approved profile.

The last row of the traversal does **not** acquire authority by inference:

| Other existing dependency | Preserved verification boundary |
|---|---|
| RoundConfig bytes, normalized configuration, schema/assignment aliases, units | Original immutable source/configuration binding. N's proposal-ID membership test alone does not prove byte origin. Do not substitute the formal fixture `content_id(config_payload)` for a different original config ID |
| Tickets, commitments, Q/model/optimizer/shard bytes | Existing lease/owner, canonical commitment and value/hash rules; validators' signatures attest their vote, not arbitrary worker training correctness |
| Availability certificates/attesters | Existing availability authority, threshold and shard-coverage checks. Storage attesters are not silently assigned validator keys/roles by this profile |
| Seed shares/transcript, norm and arithmetic evidence | Existing selected seed/producer and deterministic verification rules, with original ISC/seed references. No new beacon/reveal signing protocol is introduced |
| WAL, delivery inventory, full snapshot and trusted floor | Existing Profile-v1 source/producer/continuity checks, not a consequence of having three valid signatures |

An absent applicable original verifier or source binding at any of these edges
fails closed. This document does not certify those implementations complete or
grant a trusted-boolean substitute. Their existing R2 obligations remain; a
future concrete incompatibility is a reported blocker, not permission to invent
another authority or silently restrict the admitted source domain.

## 6. Certificate witness, replay and verification procedure

For an existing generic `QuorumCertificate`, retain all original `vote_ids`,
`signer_ids`, body/context, epoch/round/height/view, kind and q. For typed
certificates whose wire format has signer IDs but no vote-ID list, use their
retained original finalization/delivery evidence to identify the exact votes.
That association is checked; neither the snapshot nor the checker may choose
an arbitrary convenient quorum after the fact.

Each original signer has an authenticated vote for the **same whole original
body/context** and certificate coordinates. Distinct original validator IDs
count once; require exact retained signer-set equality and q=3 in the fixed set
of four. Keep a valid original witness with four signers as four, not its first
three. Different valid witnesses for one body remain distinct witnesses with
their original downstream references. Duplicate deliveries/signature copies
never add quorum power; they remain in the delivery inventory. Different body,
sequence or context in an occupied original journal key is not normalized into
an idempotent replay. Existing Byzantine evidence/conflict rules still apply.

The finite source-side verification procedure is:

1. Resolve independent bootstrap/codec/build/schema/sigma pins and derive/check
   R/K from its original fixed epoch and keys. Do not obtain trust from the
   imported snapshot. Reject an ISC-only or unknown codec for non-ISC input.
2. Traverse original finite retained objects by identity with cycle/missing-edge
   detection and existing Profile-v1 bounds. Decode exact canonical bytes;
   recompute object IDs and preserve original counts, order and multiplicity.
3. For each Gn, check complete framing, gn/vn if referenced, closed kind dispatch,
   exact Vn fields, sigma/epoch/r/key ownership and strict Ed25519 verification
   of Mn. Reject GN/ISG cross-dispatch, unknown or duplicate fields, trailing
   bytes and key/signature/context substitutions before quorum use.
4. Recompute each vote's body/context association under section 5 and original
   native admission/producer dependencies. Check original source position and
   prior state. A valid signature on an invalid candidate does not authorize it.
5. Check the original certificate witness and finalization cut: exact body,
   required coordinates, original delivered votes, distinct signers and q.
   Authenticate ApplyQC this way even when it appears in `initial_anchor`.
   Operator provisioning alone does not replace its quorum authority.
6. Continue the existing full-history reconstruction, floor/WAL/current and
   source-to-R2.1/R2.2 composition checks. No step here alone returns READY or
   proves public/native refinement. Unknown/corrupt/incomplete source stays
   rejected or incomplete according to the existing profile, never repaired
   by deleting lineage or inventing a genesis state.

Order at a future vote producer remains the existing FR-003 intent-before-sign
and persist-before-expose discipline: validate exact original command/candidate,
append original kind-2 Vn intent, barrier, sign/retain Gn and required original
source artifacts, barrier, commit/expose. Gn is an artifact, **not** a new vote or
new consensus WAL kind. No production implementation of these steps is part of
this document. Unknown append requires existing recovery; a retry cannot sign
a changed intent or allocate an additional vote slot. Recovered exact original
Vn yields the same vn/Gn/gn with the selected deterministic primitive.

W1 remains an ISC finalization capsule. This proposal neither wraps every QC in
W1 nor defines new non-ISC capsule types. Existing I-B/S-RANK are unchanged:
ISC b is consensus body identity; c is certificate witness identity; s is physical
slot; `V_a(s)` counts original vote records in the prefix. An ISC kind-3 record
does not gain vote power. Mixed `1 -> 2 -> 3 -> 2` still has two original votes,
with distinct original s and ordinals; detached signatures allocate no slot.

## 7. Compatibility and liveness consequences

| Surface | Consequence of approving this proposal, before any implementation |
|---|---|
| Authority and certificate semantics | Explicit future authentication of existing original votes; no new cert/quorum/role/producer semantics. The new accepted byte language and codec dispatch are a semantic compatibility change and require qualification |
| Signed bytes and IDs | Non-ISC Vn omits legacy signature_id; vn uses the selected v2 vote-ID rule; Mn/Gn/gn are newly specified. Legacy signatures cannot verify as these objects and are not migrated |
| ISC B/b and C/c | No additional change to their already selected future definitions. Their witnesses and b/c distinction remain exact. No automatic application of the non-ISC domain to ISC |
| Generic QC | Its original vote-ID references must name future vn; therefore future QC bytes/IDs may change. Never promise unchanged IDs when referenced vote IDs change |
| Typed candidate/QC and downstream IDs | Future sigma/schema and parent/vote dependencies change canonical bytes and IDs transitively. An equal signer-independent binary body hash is not a compatibility certificate: signed Vn/R still bind the future generation |
| WAL | No changes to old records, slots, original vote multiplicity or S-RANK. A future Vn has different intent bytes and must be produced under the newly qualified generation; old kind-2 bytes are not relabeled |
| Production Init/Next | No edit is proposed here. Existing vote/delivery/finalization/crash actions and guards remain the target. A reference binding proof must demonstrate refinement; a need to alter those actions is a new STOP, not authorized implicitly |
| Different arrival cuts | No fixed first-three or canonical signer-subset requirement. Any original quorum allowed by existing producer rules may be verified, preserving its actual witness. This avoids adding an arrival-order liveness restriction; liveness is not proved by the signature document |
| Bounds | Derived finite per-vote framing, no added event/history cap or borrowed ISC budget. Existing source limits and complete retained inventory remain mandatory |

No crypto verification substitutes for honest-validator/quorum assumptions,
hash abstraction, scheduling fairness, producer legality or actual durability.
The original cryptographic abstraction remains named; no theorem may assume
that a source is public-refining because its signatures pass.

## 8. Finite qualification obligations after a separate approval

These are acceptance criteria for this proposed binding within the existing R2.3
residual, not added DoD items or implemented proof layers:

1. **Bytes/dispatch/key binding:** one reference codec for the exact two-profile
   dispatch; positive cross-language byte/signature vectors and rejection of
   wrong kind/domain/key/epoch/sigma, stale ISC-only manifest, malformed encodings,
   invalid points/scalars, trailing data and duplicate JSON member names.
2. **Original body/certificate binding:** all eight table rows, Apply candidate
   parent/optimizer/value binding, EC seed sidecar, Parameter assignment context,
   exact generic/typed signer-vote association and original producer cuts. A
   valid signature over a wrong body/parent, swapped witness or unproduced
   certificate must not become source authority.
3. **History preservation:** identical replay is one original vote, repeated
   deliveries remain separate evidence, two original votes cannot collapse,
   mixed WAL mapping remains S-RANK and incomplete/crashed sources do not acquire
   invented authority. No mandatory full public ABORT-body gate is added.
4. **Composition/qualification:** prove concrete success supplies the existing
   independent authority premise and preserves the full Profile-v1 source;
   then compose with the already required R2.3 relation, with explicit audited
   crypto assumptions. No conditional public-success or source-validity axiom.

Future source/schema/checker work is confined to the existing successor-source
proposal family, not production. Existing review surfaces at worker commit
`4c99272e9e9f4640ed51cf34bef81516630329a5` are
`formal/reference/isc_source/{authentication.py,policy.py,policy-layout.json}`,
`formal/proposals/isc-source-generation/{check.py,audit_authority.py,SourcePolicy.lean,SourceBudget.lean}`,
the existing `DeltaReduce.NativeVoteBytes`/`NativePolicySchema`/`NativePolicyCodec`
modules and `formal/proposals/evidence/isc-source-v2/`. Any required sibling
non-ISC reference module belongs to the same finite binding work, after approval;
it must not change the proven ISC dispatch implicitly. The production definitions
at N are source references, not edit authorization.

Existing Lean arithmetic/quorum results retain their original statements.
Existing evidence for their old source/semantics remains historical evidence;
it is not qualification of Vn/Gn. The new codec/body/source composition, the
applicable TLA signature/context/AllQCVotesPersisted/finalization refinement,
mutants, axiom audit and exact semantics/report compatibility must be qualified
for the future generation. The scope3 ISC-only components remain reusable within
their exact demonstrated domain. Neither this document nor its review closes
R2.3 or the recovery theorem; full R3 remains excluded.

## 9. Decision requested and STOP

Approve or reject the exact proposed non-ISC signed-byte/artifact/codec-dispatch
contract in sections 3–7 for **isolated future formal/reference work within the
already authorized R2.3**, preserving all retained restrictions. This is not a
request to reauthorize R2.3 generally, approve a new trust model, assign sigma,
deploy a codec or waive any review/qualification gate.

After this document, STOP for the semantic decision through nginx-qa Pending
decisions. Do not send RESUME solely to escape the waiting assignment. After a
real applied decision, the actual role must fetch and ACK its fresh exact scope
before ordinary graph/review execution. **No new byte contract is considered
approved merely because this document was authorized or committed.**
