# Storage Availability Source Binding v1

**PROPOSED — specification only; exact semantic approval required.**
6 October 2026. T047/T053. R2.3 OPEN / Formal NO_GO.

## 1. Authority for this document and decision boundary

The existing sprint's human decision
`scope-decision-344bf1b51a2dd860e4fd57e20f3a9b84` applied scope revision 6,
amendment `scope-human-34ecf7d8f4066df5e56e757096619411`, to coordinator
assignment `6a4e2acb-444f-45dd-aa08-8b4c4741a39c`. Exact ACK
`scope-ack-cc85140300f70cddfca87cc7527e9807` was confirmed by role GET. Its source
is `2edc9298a3e041ff32772289ba1d3b881821cfc5:orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-STORAGE-AUTHORITY-DECISION.json`.
It authorizes this document, **not the mechanisms proposed below**.

No operator supplied a previously qualified storage codec or immutable storage
enrollment artifact with that decision. The existing permissioned storage role
is specified, but its concrete key binding is missing. The proposal below uses
the **same independent offline deployment provisioning authority** already
selected by Snapshot Provenance Profile v1. It does not use validator signatures
as storage authority. It needs an explicit new binding from that authority's
pinned initial configuration to the existing storage identities and their own
keys. That binding is **not present or implicitly approved today**.

The decision is whether to approve that precise configuration/codec binding for
a future isolated source generation, or supply an existing applicable contract.
If binding storage enrollment through `initial_config_ref` is not accepted, stop:
there is no permitted fallback authority. This document does not select a new
CA, storage super-certificate, trust server or producer rule. No new deployment
scope (epoch change, unenrolled node, network bootstrap, compromised T or backup
format) is proposed. No concrete `sigma_next` is assigned.

## 2. What exists, and what does not

Immutable pins: `N=60c692f6e391f839829dfc64e93380db54cd507b`,
`P=26eb02d0632435c9aa0d8ef44eb496b6fa73dd13`.

| Existing source | Reused obligation / limitation |
|---|---|
| N `.specify/memory/constitution.md` IX; `specs/008-certificates-and-consensus/spec.md` FR-037/039/040 | Enrolled storage peers, role-bound keys, append-only content identities, offline verification. These are requirements, not a concrete key registry or signed-byte format |
| N `specs/003-bft-round-state-machine/spec.md` FR-001/012–019 | RoundConfig availability policy; commitment binds immutable ticket/context; exact shard IDs, lengths, retention epoch, per-shard coverage, close/late/repair rules |
| N `delta-core-cpp/include/delta/core/consensus.hpp`, `AvailabilityProof`; `src/consensus.cpp`, `InputLedger::record_availability` | Six fields: ticket, commitment, certificate ID, covered leaf IDs, attester IDs, threshold. Checks membership/coverage/conflict; no key, signature, length or retention authentication |
| N `delta-protocol/schemas/004/encoded-contribution-manifest-v1.json`; `delta-core-cpp/include/delta/shards/envelope.hpp` | Original leaf IDs and `envelope_bytes`, not just payload length. Original manifest, shard encoding and commitment verification remain authoritative |
| N `formal/tla/DeltaReduceAvailability.tla` | Per-(storage,ticket,content,shard) `AttestAvailability`; per-shard threshold; `FinalizeAvailability` additionally checks actual available-artifact state |
| P `docs/adr/0013-snapshot-provenance-profile-v1.md` §§2–5 | Independent initial configuration/codec pins and faithful original history; imported bytes cannot enroll their own signer. Bootstrap's explicit key table currently covers validators, not storage |
| `bb9fce957dae329701a8cd473a7148e198e1ca12:docs/adr/0015-non-isc-authority-binding-v1.md` §§3/5 | Eight validator kinds only; storage authority explicitly remains separate |

The reviewed source audit and identical-six-fields diagnostic pair are at
`e766ef98748504779a9a88d06ee3760594c4184d:formal/proposals/non-isc-source-checkpoint.md`
and `formal/proposals/evidence/non-isc-source-v1/availability-boundary.json`.
They establish missing source information, not a production-reachable forgery.
An opaque Java Authenticator, TLS tag, syntactic certificate ID, local T copy or
three validator signatures does not supply that information.

## 3. Proposed enrollment binding — the explicit architectural choice

Reuse Profile v1's independently pinned `initial_config_ref`, `signature_codec_id`
and source/build/schema pins; add **no bootstrap envelope field**. In the future
qualified initial configuration, resolve one closed `storage_authority` object:

```text
storage_authority = {storage_epoch_id, storage_registry_id}
RoundConfig.availability_policy.storage_binding =
  {retention_epoch_id, storage_epoch_id, storage_registry_id, threshold}
```

These are **new concrete field layouts**, proposed here for the existing
configuration/availability-policy concepts, not fields discovered in N. The
storage_binding is additive: original close, repair, deadline and other policy
fields remain required and are not replaced by these four fields. Their
exact enclosing future configuration encoding must be qualified before use;
no old closed schema gains these fields and no old config hash is reused.
RoundConfig must resolve the same independently pinned registry and storage
epoch. Its own existing validator/config authority and membership checks still
apply. Snapshot-supplied configuration can only match the independent pin.

Storage key object `Ks` has exactly `algorithm="Ed25519"`,
`public_key_hex` (64 lowercase hex digits), `schema_version="1.0.0"`.
`ks=ID("deltareduce.storage-ed25519-key.v1",J(Ks))`.
Registry `Rs` has exactly:

```text
formal_semantics_id, members, origin_id, schema_version, signature_profile,
storage_epoch_id, type_name
```

`schema_version="1.0.0"`, `type_name="STORAGE_EPOCH_REGISTRY"`,
`signature_profile="SIG-STORAGE-ED25519-v1"`, semantics is symbolic future sigma.
`members` is a nonempty array sorted by original `storage_id`, each with exactly
`key_id`, `roles=["storage"]`, `storage_id`. Original storage IDs and keys are
unique within Rs. K references resolve to exact validated original public keys;
the independent provisioning must bind those keys to those enrolled storage
identities. There is no key inference from an artifact's claimed issuer.
`rs=ID("deltareduce.storage-epoch-registry.v1",J(Rs))`.

Rs has no authority signature and is not a new QC: its authority is the existing
independent bootstrap/config pin. It neither extends the validator registry R
nor assigns R's validator keys to storage peers. Common host ownership, if any,
does not combine the roles' signing power. Threshold comes from the exact
RoundConfig availability policy, **not validator q=3 by analogy**; require
`1 <= threshold <= |Rs.members|` and the original configured storage threshold.

`retention_epoch_id` names the exact immutable storage retention obligation
selected by that policy. It is not inferred from a wall clock, numerical maximum,
validator epoch or snapshot timestamp. Equality to that original policy is
mandatory. This codec does not define a new retention duration/extension rule:
the original retention policy and producing history must be available to the
source verifier, otherwise it fails closed. Signature verification does not
establish that a storage peer actually retained bytes.

The selected proposal is conditional on human approval of this storage-specific
config/key binding. Alternative 1 is an already normative exact storage
enrollment/codec with an immutable evidence path. Alternative 2 would introduce
a different trust root or authority; that is outside this request and requires
its own explicit architecture decision. Neither alternative is implemented.

## 4. Exact proposed attestation bytes

`J` uses the existing Profile-v1 canonical ASCII JSON subset: sorted keys,
no whitespace/BOM/trailing newline, no escapes, duplicate/unknown/missing keys
rejected **before** constructing a typed object, decode/re-encode equality.
Numeric values below are decimal strings, no sign/leading zero except `0`.
No JSON numeric value, null or first/last-wins parser is allowed.
`ID(d,x)="sha256:"||lowerhex(SHA256(ASCII(d)||00||x))`;
`U16/U32` are unsigned big-endian and `L(x)=U32(len(x))||x`.

One attestation `A` covers **one original committed leaf**; it is not a validator
vote and has no consensus durable sequence. Its exact closed field set is:

```text
commitment_id, envelope_bytes, formal_semantics_id, height, key_id, leaf_id,
origin_id, parent_checkpoint_id, retention_epoch_id, round_config_id, round_id,
schema_version, storage_epoch_id, storage_id, storage_registry_id, ticket_id,
type_name
```

Constants: `schema_version="1.0.0"`, `type_name="STORAGE_AVAILABILITY_ATTESTATION"`.
`formal_semantics_id=sigma`; height is U64; envelope_bytes is positive U64.
Content/config/parent/key/registry/origin/semantics IDs are exact lowercase
71-byte `sha256:` IDs. Round/storage/epoch/retention labels retain the native
1–128 `[A-Za-z0-9._:-]` grammar. The attestation decoder admits ticket labels of
1–255 ASCII characters from `[A-Za-z0-9._:/-]`, covering the original native and
feature-004 lexical forms. This is a lexical envelope only: the resolved original
ticket's applicable grammar and source rules still must pass. It neither truncates
a feature-004 ticket to 128 characters nor admits an invalid native ticket through
the wider envelope. Source/schema pins select the original type; lexical overlap
is not source authority or permission to change its bounds.

`leaf_id` is the original committed encoded-shard identity, not a recomputed
root under the ISC Merkle profile. `envelope_bytes` is the length of that **full
original shard envelope**, checked against its original manifest and verified
bytes, not payload bytes, element count or aggregate total. The original shard
ordinal/range/schema/profile/commitment associations must also validate; no
new coordinate-level shard identity is created.

```text
a  = ID("deltareduce.storage-attestation-body.v1", J(A))
Ms = ASCII("deltareduce.storage-attestation.ed25519.v1") || 00 || L(J(A))
ss = Ed25519.Sign(original_storage_secret_key, Ms)              // 64 raw bytes
Gs = ASCII("SAG1") || U16(1) || U16(0) || L(J(A)) || ss
gs = ID("deltareduce.storage-attestation-signature.v1", Gs)
```

A already binds rs, ks and storage_id; they are not unsigned outer claims.
Reuse the exact strict pure Ed25519 primitive selected in P ADR0014 §5, including
canonical nonidentity prime-subgroup points and S<L. Reusing its mathematical
primitive does **not** reuse ISC/NSG1 domains, registry roles or authorization.
No prehash, TLS, opaque callback or signature-ID-only fallback. Length overflow,
unknown version/magic, trailing data or inconsistent IDs rejects the object.
Neither A nor Gs contains its own ID, so there is no signature/hash cycle.

Original replay of the same A/key gives the same a/Gs/gs. Distinct deliveries
remain distinct history events. Another leaf or retention/context is not silently
normalized into the old attestation. Existing conflicting-attestation/source
legality rules apply; this document invents no storage vote journal or new
consensus WAL kind to enforce them.

## 5. Exact proposed AC witness and native association

Future AC `D` has exactly these fields:

```text
attestation_ids, commitment_id, formal_semantics_id, height, origin_id,
parent_checkpoint_id, retention_epoch_id, round_config_id, round_id,
schema_version, storage_epoch_id, storage_registry_id, threshold, ticket_id,
type_name
```

`schema_version="1.0.0"`, `type_name="STORAGE_AVAILABILITY_CERTIFICATE"`;
common fields have the same types/meaning as A; threshold is positive U32.
`attestation_ids` contains the original gs references of this **actual witness**,
ordered by resolved `(leaf_id,storage_id)` ASCII pair. Duplicate pairs, unknown
leaves and mismatch to common context reject; do not sort/rewrite received
noncanonical bytes. Every referenced Gs must authenticate. A certificate cannot
refer to a convenient different valid witness after the fact.

`ac=ID("deltareduce.storage-availability-certificate.v1",J(D))`.
No aggregate validator signature or new certificate protocol is introduced.
For every original required leaf, at least the configured number of distinct
enrolled storage IDs must attest that exact leaf/length/retention/context.
The certificate covers exactly the original committed leaf set; no missing or
extra leaf. **The signer subsets may differ by leaf.** Requiring the same quorum
for every leaf, taking the first q signers, or accepting only a union-wide q
would change the existing per-shard contract and is not proposed.

Only after authentication, source-cut/producer verification and full per-leaf
coverage checks can D supply the existing six-field AvailabilityProof:
original ticket and commitment; certificate_id=ac; sorted exact covered leaf
IDs; sorted union of the witness's original storage IDs; original threshold.
The full per-leaf witnesses stay retained. The six fields alone are still not
authentication evidence and cannot be the input that proves its own validity.

Two different witness sets yield different ac, even if their covered body is
equal. Preserve the actual first accepted original AC and InputLedger's existing
conflict/late behavior; another witness does not replace it. Replays allocate no
new vote/slot. Retained alternate witnesses and deliveries are not erased, nor
are their existence or equality declared to be new accepted protocol events.

## 6. Verification and remaining producer boundary

The finite source verification order, after a separate approval, would be:

1. Resolve the independent bootstrap/config/codec pins, then Rs/Ks and the
   exact original RoundConfig availability policy. Unknown/missing authority
   rejects; importing Rs alongside its own claimed ID cannot establish trust.
2. Verify original ticket/lease/commitment and complete manifest/shard preimages
   through the existing source rules. Derive required leaves and lengths from
   those objects, not from observed attestations or the claimed AC.
3. Decode and authenticate each original Gs, bind its storage key/role/epoch,
   whole A, exact bytes and content ID. Retain the complete delivery inventory.
4. Reconstruct the original source cut and validate its existing upload,
   attestation, availability/loss/corruption/repair, close and finalization
   prerequisites. A signature authenticates a statement; it does **not prove**
   `ArtifactLocation(storage,content,shard) in availableArtifacts` at that cut.
   Faithful T bytes do not prove that fact either. Required independent native
   producer evidence must exist; no trusted boolean or public-success premise.
5. Verify D's exact witness, context and per-leaf quorum; check its original
   finalization/admission event; then compare the derived six-field projection
   and native state with the original source snapshot. Apply original late,
   freeze, repair and no-substitution rules. Continue existing R2.3 composition
   only when all its other premises are also discharged.

This document supplies a proposed **source authentication binding**, not a new
Upload/Attest/Finalize producer or a proof that those native producers are
complete. A counterexample needing a new producer rule, changed TLA Init/Next
or a stronger storage honesty/observation assumption is an architecture STOP.
No claim is made that approving bytes alone closes every upstream dependency.

The target actions remain `UploadArtifact`, `AttestAvailability`,
`FinalizeAvailability`, pre/post-freeze loss, corruption, repair and late reject.
`HasCompleteAvailability` at finalization is stronger than having historical
signatures. Later loss does not erase an AC/ISC: the existing repair/abort rules
still apply. The codec makes no new liveness guarantee or everlasting-retention
claim and never manufactures a current availability fact from an old signature.

## 7. Compatibility, bounds and required qualification

| Surface | Consequence |
|---|---|
| Storage authority | Existing storage role and offline provisioning owner reused; **new explicit config-to-storage-key binding needs approval**. No validator-key substitution/new root |
| Signed bytes/AC | New Ms/SAG1 and content-addressed D for a future generation. They cannot authenticate old ID-only proofs; no signing, migration or relabeling of old objects |
| ISC B/b, C/c and downstream QCs | New ac and config references change future ordered tuples/root/B/b, witness C/c and dependent EC/APC/Parameter/Root/Apply bytes/IDs. I-B meanings remain intact; equality of an abstract ticket/content pair is not equality of AC artifacts |
| WAL and S-RANK | Original validator vote records, physical s and public V_a(s) unchanged; storage artifacts create no consensus vote slot. Preserve original history order/counts and mixed 1→2→3→2 behavior |
| W1 | Existing layout still retains original source references/inventory. Recompute exact complete W1/P0/P1/output sizes; no deletion of a storage witness to fit. This document does not enlarge approved caps |
| Production Init/Next and producer behavior | No edit or new action proposed/authorized. Existing availability guards and exact native producer relation must be qualified; if impossible, STOP |
| Formal results | Existing arithmetic/quorum results retain their statements and old evidence. New authority/codec/source composition is not covered by those results or earlier signature-only tests |

Use the existing fixed deployment bundle/event/ref bounds and source-specific
shard/parser bounds. U32 framing is checked before allocation. No new global
event cap, invented storage committee size, common-quorum condition or hidden
source-domain restriction is introduced to make this proposal pass. Exact
retained objects must fit the already approved domain; a discovered mismatch
must be reported, never repaired by dropping lineage.

After exact semantic approval, qualification within the existing R2.3 includes
closed registry/config dispatch and canonical signature vectors; wrong key,
role, epoch, context, length, retention and duplicate-key negatives; per-leaf
mixed-quorum witnesses and same-body/different-witness identities; source-cut
legality and full retained-history/native/public composition. Applicable
schema/checker, TLA-refinement, Lean, mutant, axiom and formal/review gates remain
mandatory. No acceptance of this document substitutes for those gates.

## 8. Requested decision and STOP

The precise choice is approval (or rejection/edit) of §§3–7 for a future isolated
formal/reference generation, including the explicit storage-authority linkage
through the independently pinned initial configuration and its RoundConfig
availability policy. It is **not** a finding that that binding already exists,
nor permission for production code, a new producer, changed trust assumptions,
full R3, sigma assignment or guard removal. An already qualified alternative
must be supplied as an exact immutable contract; it cannot be inferred from IDs.

After this document, **STOP for the human decision in nginx-qa**. No RESUME
outcome solely to move the waiting graph. The current assignment remains active;
ordinary process reviewers must still review any subsequent submitted result.
This document has not itself passed independent review or formal qualification.
R1/R2.1/R2.2 remain CLOSED in their original domain; R2.3 remains OPEN.
