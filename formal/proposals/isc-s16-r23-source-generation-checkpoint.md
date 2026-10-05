# ISC-S16-D01: R2.3 source-generation checkpoint

T047/T053. Source base `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13`.
Assignment `8d6f2d2c-d217-470b-94e0-1eee15b39a1b`, effective scope revision 2.
R2.3 is fully authorized. The old permission blocker has been removed through
nginx-qa v2; it is not the reason for this checkpoint. R1/R2.1/R2.2 remain CLOSED.

**NEED_DECISION: source-generation join remains unqualified. Formal NO_GO;
R2.3 OPEN.** This is a contract-generation compatibility audit, not an assertion
that a lawful production execution violates safety or that R2.3 is impossible.
No new protocol predicate, model action, certificate format or authority is defined.

## Exact obstacle

The frozen Profile v1 requires independent native producing history, complete
collections and original identities. Its observed native source is PR50
`60c692f6e391f839829dfc64e93380db54cd507b`. Existing R2 source components bind
that source's legacy certificate semantics. The separately approved I-B/S-RANK/W1
contracts describe a **future** generation, explicitly prohibit relabeling legacy
objects, and require qualification of its changed ISC lookups.

The first finalized ISC already separates these contracts:

| Contract | Certificates | Finalized membership | Identity consumed downstream |
|---|---|---|---|
| Pinned native admission / current Lean source | original C | c = ID(C) | c |
| Approved future W1 Section 2 | original C of that generation | b = ID(B) | b |

Pinned C++ `delta-core-cpp/src/certificates/vote_admission.cpp:465-479` requires
`finalized_input_set_ids` to be a subset of `input_qc_id` over original certificates.
The seed check immediately following it looks up the same c. Lean mirrors it in
`NativeFinalizedIscSection.SetChecks`, `finalizedCertificate` and
`noInventedFinalized`. Existing `NativeIscCertificateVectors.bodyIdIsNotFinalizedQc`
already proves rejection when b is substituted into this legacy section.

`0014-isc-finalization-wal-capsule-v1.md`, Section 2, instead mandates b membership,
says P0/P1 already belong to independently selected future semantics, and explicitly
states that the legacy c validator is insufficient. The approved I-B decision is
not being reopened; its distinction is precisely why direct reuse is unsound.

The existing pinned synthetic codec fixture gives:

- c = `sha256:2534a9ccd9ecc93bc121a75e47c94b1b5c484735bfe24144faeec50fe72b7e14`;
- b = `sha256:33e327fe50bd52a92e0675c846fe2ee53671dde65350152380c82a99af21c27d`;
- one original C, three original signers, one finalized member;
- `[c]` is a subset of `[ID(C)]`; `[b]` is not.

These are **legacy fixture IDs**, not instantiated future W1 IDs. This is a
minimal counterexample to direct cross-generation predicate reuse, not a valid
import bundle, authenticated native capture, production-reachability result or
counterexample to source-domain totality. No body/certificate/root is relabeled.
The earlier ISC@1/EC@2/EC@3 API witness is not used as production evidence.

There is a second composition boundary, not a new residual: the existing native
runtime and `NativeConfigReplay.step/run/History` bind every kind-2 record to one
startup policy ID. Kind 1 changes only coarse state; kind 2 appends votes. W1
requires source-derived policy generations P0 to P1 and kind 3. Restarting with
P1 cannot make old records refer to P1: native recovery checks the original
policy identity and Lean `wrongPolicyRejected` rejects its substitution. A
version-aware future fold can preserve old bytes, but it is a new qualified
source model, not an application of the existing fixed-policy theorem.

## What is engineering and what requires a semantic decision

Ordinary reference implementation, independent source checks, full collection
construction, schemas and helper proofs remain authorized. Their absence alone
does not require another permission request. The old stage-1 producer gap is not
being resubmitted as an unchanged permission question.

What cannot be selected silently is **which exact native generation becomes the
source contract for the claimed R2.3 closure**. The pinned source has no complete
policy-producing transition. The future producer specification remedies that,
but its full parent/signature/budget byte closure remains `DRAFT_EXACT_DETAILS`
in the accepted A01 freeze. The consolidated amendment itself classifies it as
`SEMANTIC_CHANGE`. It includes changed contexts/bytes and admission guards; merely
implementing it in a reference directory does not approve that source contract.

Available routes and their limits:

1. Completing codec/metadata helpers for the old pin is authorized but cannot
   manufacture its missing independent finalization origin.
2. Inserting c into future W1 would violate already approved I-B/W1. Inserting b
   into old policy violates the actual pinned predicate above. Neither is a fix.
3. Using public `Next`, a supplied snapshot, a successful R2 check or a trusted
   `legal_origin` flag as the missing producer violates Profile v1's independence.
4. A quarantined future producer/source/refinement lane is technically plausible.
   It needs an explicit source-generation decision and approval of the exact
   parent/signature/budget source contract it uses. It must retain legacy results
   as legacy, requalify changed bindings, and never claim that PR50 already
   implements the new rules. This checkpoint does not implement or pre-approve it.

The semantic decision therefore concerns the future source contract and its
qualification boundary, **not permission to work on R2.3 again**. The coordinator
must first review whether an existing exact approval already resolves it. If none
does, use Pending decisions to present a concrete source-bound proposal, preserving
all production/guard/trust/history restrictions. Do not apply it as prior human
authorization: the current R2.3 grant does not approve previously draft semantics.

## Verification and residual

Reproducer: `formal/proposals/isc-s16-source-generation-audit.py`.
It reads exact Git blobs, recomputes the existing canonical b/c IDs, checks the
native membership source, and rebuilds the original 17-module Lean dependency
closure using Lean 4.32.1 in an isolated ignored build. It audits the existing
three named declarations. Logs and exact source hashes are in
`formal/proposals/evidence/isc-s16-source-generation/`.

There is no new theorem, changed production source, schema, fixture, formal
report or semantics ID. Existing Lean results remain valid for their old domain.
The diagnostic is not a full native admission run. Hash/signature provenance and
full profile reachability are not inferred from synthetic bytes. Process reviews
by this same sequential executor are not independent Formal GO attestations.

Residual remains the frozen R2.3: independently produced full source snapshot,
all remaining collections/state constraints, and initial/incomplete/sufficient
ABORT mapping without lineage loss. Full-document bounds remain unproved; the
resource caps alone are not presented as an overflow counterexample. R2.1/R2.2
are not reopened. No recovery theorem, full R3 or production integration started.

Resume criterion: a source-bound generation decision resolves the old-pin versus
future-producer qualification boundary; then implement the authorized complete
source bridge and rerun its substantive reviews before the named recovery theorem.
No numeric claim of remaining closure time is justified by this compatibility audit.
