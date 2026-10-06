# R2.3 checkpoint — non-ISC authority binding needs a semantic decision

T047/T053; assignment `6a3718d7-25b3-4f2e-802c-9688fe931b4d`, role 2753,
`agent/isc-s16-formal-linkage`, effective scope revision 3.
**R2.3 OPEN; Formal NO_GO. No production change or R3.**

## Decision boundary

The approved future ISC source contract supplies exact B/C/V/G/R/K/E bytes and
the strict ISC Ed25519 verifier. It expressly does **not** select a signing
profile for other protocol vote kinds. Snapshot Provenance Profile v1 requires
authenticated ApplyQC even for the independently provisioned initial anchor.
The existing native ApplyQC verifier cannot discharge that requirement: its
inputs contain no original signature evidence or independent key registry.

This is a concrete binding required by the already frozen R2.3 provenance
obligation, not a new requirement or reopening of R2.1/R2.2. Extending ISC signed
bytes to Apply or accepting structural signer-list success as authentication
would exceed the exact approved contract. Neither has been implemented.

## Evidence and smallest missing premise

1. `specs/008-certificates-and-consensus/spec.md`, FR-002, FR-033 and NFR-004:
   Apply authority requires unique valid signatures in the exact epoch, with
   fail-closed handling of insufficient signatures or uncertain parentage.
2. `docs/adr/0013-snapshot-provenance-profile-v1.md`, sections 2–4: even the
   provisioned initial anchor requires valid ApplyQC. Original signatures and
   source history must be checked; known floor/consistent hashes do not waive it.
3. Exact approved source
   `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13:docs/adr/0014-isc-production-contract-amendment-v1.md`,
   section 3: V is ISC; other kinds do not automatically receive its new signing
   profile. EC/APC/Apply preimages are explicitly not designed there. Section 4
   binds the ISC registry/profile, not an arbitrary codec plugin.
4. Native pin `60c692f6e391f839829dfc64e93380db54cd507b`:
   `delta-core-cpp/include/delta/certificates/verifier.hpp` defines ValidatorPolicy
   as epoch/IDs/threshold. `ChainVerifier::verify_apply` in
   `delta-core-cpp/src/certificates/verifier.cpp` takes ApplyQc, ApplyCandidate,
   aggregate-root ID and arithmetic-profile ID; it checks context/parents/body,
   calls `validate_signers`, then returns the content ID. No signature bytes,
   signing preimage, keys or crypto verifier are arguments. `make_vote` checks
   grammar of `signature_id`; pinned
   `delta-core-cpp/src/certificates/vote_admission.cpp` similarly uses
   `require_content_id(vote.signature_id)`.
5. At the same pin, `CurrentPointerStore::advance` in
   `delta-runtime-cpp/src/certificate_runtime.cpp` checks command/QC identity,
   parent, target and replay. It does not supply signature verification. Java
   peer/transport authentication is not original-voter authority.
6. The reviewed concrete `formal/reference/isc_crypto/codec.py` rejects other
   vote kinds. Relabeling an APPLY_QC vote as ISC or selecting a new preimage
   cannot reuse this qualification unchanged.

The smallest unresolved implication is:

```text
original ApplyQc + ApplyCandidate + original vote/signature artifacts
+ independently provisioned epoch/keys
  → three distinct eligible validators signed the exact voted Apply body/context
```

The non-ISC signed payload, artifact association and key/role dispatch needed to
compute this binding are not selected by the approved ISC contract. A supplied
manifest ID without its qualified codec is insufficient.

Minimal insufficiency argument: use identical well-formed ApplyQc/ApplyCandidate,
parent/profile IDs and signer-ID list in two environments, one with genuine
original signature artifacts and one with those artifacts missing. Existing
`verify_apply` has identical arguments in both, so it cannot distinguish them.
The profile must reject the second. This proves insufficiency of this component,
**not** production reachability of a fabricated full history or acceptance by a
properly composed importer. The importer must remain closed.

An Ed25519 security assumption is different from assuming the entire missing
Apply authority check succeeded. The latter would bypass concrete applicability.

## Residual reduction and limits

- Exact successor ISC body/witness separation, explicit parent, complete DVPOL002
  structural inventory, strict original ISC signatures and exact W1/output size
  implications are implemented as isolated reference/proof components.
- Candidate composition uses all matching original signers, retains original
  deliveries and certificate variants, and preserves every other policy field.
  General Lean field-retention lemmas have no empty-downstream-lineage premise.
- Full producing origin, Profile-v1 admission and public-state applicability are
  still unproved. All three frozen R2.3 residuals remain OPEN as one composition
  obligation. R2.1/R2.2 stay CLOSED. Activation/recovery are not implemented.
- Public-state expansion is an investigated risk, **not a proven admissible
  source counterexample**. No hidden cap or new architecture finding is inferred
  from a synthetic oversized state; its existing applicability obligation remains.
- Legacy objects/signatures/QC/WAL IDs, production Init/Next/runtime and accepted
  evidence are unchanged. Sigma is symbolic. No production capture or producer
  is claimed. Component checks are not the complete formal/recovery gate.

## Requested decision through Pending decisions

Keep the sprint, assignments, reviews and scope lineage. Request authorization
for **one consolidated specification-only non-ISC authority-binding decision
document for the existing Profile-v1 source chain**, using the same independent
epoch/validators and existing voted-body/certificate lineage. ApplyQC is the
minimum anchor; inventory the other existing non-ISC dependencies together so
this is finite, not one approval per helper.

Identify reusable exact contracts, minimally missing signed-byte/artifact/key-role
bindings and compatibility effects. Do not introduce a trust root, migrate old
signatures/IDs, weaken provenance or silently generalize SIG-ISC. No non-ISC
implementation or proof assuming new bindings is authorized by this request.
The document's actual semantic choice then requires approval before implementation.
An externally existing, already approved exact applicable contract may instead
be supplied by immutable reference; do not invent such authority.

This does **not** request full R2.3 permission again. That permission remains.
It requests the next semantic contract decision exposed by the source audit.
Production integration, guard removal, new trust, full R3, profile expansion and
legacy changes remain prohibited. No human approval is recorded by the executor.
