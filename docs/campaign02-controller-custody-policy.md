# Campaign 02 controller trust and key custody policy

**Policy version**: 1.0.0

**Status**: PROPOSED — requires explicit governance adoption before use

**Scope**: Campaign 02 bootstrap mapping and zero-execution registration

**Formal impact**: NONE — governance documentation; no protocol or signed-schema change

**Related work**: T009, T051, HR010-018; C2-037 and C2-040

This policy makes the organizational meaning of an independent bootstrap controller
reviewable. Its requirements apply after governance adopts an exact revision and
approves the completed controller register. Committing this policy, filling a
template or obtaining a verifier PASS does not itself appoint controllers or
authorize execution.

Use the [appointment register template](templates/campaign02-controller-register.template.json)
and [appointment and signing procedure](campaign02-controller-onboarding.md).

## Contract boundary

The authoritative implementation is
[`campaign02_bootstrap.py`](../delta-worker-python/src/deltatorrent/benchmark/campaign02_bootstrap.py):
`BootstrapValidatorSet.from_dict`, `verify_bootstrap_mapping` and
`verify_registration_receipt`. The
[validator-set schema](../delta-protocol/schemas/010/campaign-02/workflow-bootstrap-validator-set-v1.json)
remains unchanged.

| Machine-enforced property | Campaign 02 bootstrap profile |
| --- | --- |
| Validator set size | `3*f_b+1`; four entries for `f_b=1` |
| Quorum | `2*f_b+1`; exactly three mapping votes and exactly three registration votes |
| Identity uniqueness | Distinct nonempty `signer_id` and `controller_id` in the set |
| Public keys | Distinct 32-byte raw Ed25519 keys in canonical Base64 |
| Vote verification | Correct signature, signer membership, object IDs and validator-set ID; three distinct controllers per quorum |
| Registration binding | Exact mapping, receipt, API evidence and signed run/artifact time context |

The implementation supports other `f_b` values under its existing formula. This
policy's appointment procedure uses the four-validator profile requested for the
current package; it does not hard-code a new restriction in the verifier.

The verifier cannot infer ownership, administrative independence, private-key
custody, honest review or actual signing time from labels and signatures. It
checks the signed timestamp fields, not an independent trusted clock. The custody
register and review records are separate governance evidence and are not covered
by the existing mapping or registration signatures. A policy/register hash must
not be added to those signed documents: their field sets are exact. Machine
enforcement or cryptographic binding of custody metadata would require a separately
versioned contract, impact review and renewed qualification.

## Who can be a controller

A controller is an accountable signing authority within one independently
administered custody boundary. It may be a person, service, HSM/KMS-backed identity
or bot. A service still needs an identified accountable owner and administrators.
Four people are not required. Four independently controlled authorities are.

`controller_id` identifies the real administrative authority, not a process number
or a convenient alias. `signer_id` identifies an enrolled signing identity/key
generation within that authority. IDs must be stable, auditable and never reassigned
to unrelated owners or keys. GitHub reviewers, contributors, repository owners and
service accounts are not implicitly bootstrap controllers.

| Configuration | Governance disposition |
| --- | --- |
| Four people, each controlling an isolated key and recovery path | Eligible after review |
| Four independently administered services or HSM/KMS identities | Eligible after review |
| A mixture of people and independent services | Eligible after review |
| Four bots sharing a signing-capable GitHub token, repository secret or signing process | Reject |
| Four keys generated or controlled by one owner | Reject, even if cryptographic verification passes |
| Separate keys with a common root administrator or recovery credential able to take over several keys | Reject |

## Mandatory independence and custody requirements

1. **Accountable ownership.** Record each controller's owner, administrative domain
   and all roles able to sign, export, restore, replace or grant access to the key.
   Different account names alone do not establish independence. Different owners
   or independently controlled administrative domains must be supported by evidence.
2. **Independent key creation.** Each custodian generates its own fresh key inside
   its own approved boundary. A coordinator must not generate, import, distribute
   or retain all four private keys. Fixtures, sample seeds and prior campaign keys
   cannot supply this fresh bootstrap set.
3. **Separate signing authority.** No person, shared service account, credential,
   repository/organization secret, CI runner or signing process may exercise signing
   authority for more than one controller. Include deployment administrators who
   could replace signing or evidence-verification code in this assessment.
4. **Isolated recovery.** Backups, export privileges, break-glass access, identity
   provider administration and account recovery must preserve the same separation.
   Compromise of one controller must neither disclose another key nor enable its
   use, replacement or recovery. Separate HSM slots or cloud accounts under a common
   unrestricted administrator are insufficient.
5. **Supported signing mode.** A hardware-backed service must support the existing
   raw Ed25519 message/signature interface. Do not substitute Ed25519ph, another
   algorithm, a prehashed payload or a provider-specific wrapper. Document export
   policy and the tested public-key/signature encoding. Software custody is allowed
   if it meets the same independence requirements.
6. **Independent evidence review.** Each voting controller retrieves the frozen
   package, recomputes its IDs, checks provenance and time bounds, and decides
   independently whether to sign. A bot must run its owner's approved verification
   logic; a coordinator's Boolean approval or supplied opaque hash is insufficient.
   Controllers must be able to refuse signing and record discrepancies.
7. **Auditable key binding.** Publish only the public key, its SHA-256 fingerprint
   over the decoded raw 32 bytes, stable IDs and sanitized evidence references.
   Authenticate the public-key submission with the named owner through a separately
   verified channel. Retain the owner acceptance and key-binding evidence.
8. **Recorded decisions.** Keep the exact policy revision, register revision,
   evidence references, approvals, timestamps and signing audit references. Missing,
   ambiguous or inaccessible evidence blocks governance admission.

Public artifact collection may use a common repository. That collector must have
no controller private key or delegated signing power. Never put private keys,
seeds, passphrases, access tokens, recovery codes, secret-bearing key locators or
sensitive infrastructure details into the register, repository, CI logs or chat.
Restricted evidence stays in its approved access-controlled system; the register
contains a sanitized immutable reference and digest that authorized reviewers can
resolve. A digest alone does not establish the truth of a custody claim.

## Appointment and governance admission

The appointing governance authority and an independent custody reviewer must be
explicitly identified. Do not infer these roles from repository access. The reviewer
must not hold signing, recovery or deployment control over any candidate controller.

The register must contain exactly four completed controller entries. Each owner
accepts the role and confirms the recorded key and custody boundary. Review all six
pairs of controllers for overlapping signing, administration, deployment and
recovery authority; record the evidence and conclusion for each pair. Four owner
acceptances are appointment records, not a requirement for four protocol votes.

Governance admission requires all of the following:

- adoption of this exact policy revision by the named governance authority;
- four authenticated owner/key bindings and complete custody evidence;
- a PASS conclusion for every pair, signed off by the independent reviewer;
- a canonical validator set with `f_b=1`, quorum `3`, validated by the existing
  `BootstrapValidatorSet.from_dict` and matched to every register entry;
- an approval record referencing the exact policy/register Git revisions or
  file-byte SHA-256 digests, the validator-set ID and the allowed mapping/receipt/API
  evidence IDs, with a bounded validity window;
- explicit permission to collect the bootstrap mapping/registration signatures.

Freeze the register and set before collecting votes. Keep the approval record
separate so it can refer to their exact revisions without a self-referential hash.
The template's nulls are unknown facts, never defaults or approvals. Its
`BLOCKED_PENDING_APPOINTMENT` status must not be presented as a live controller set.

Cryptographic PASS and governance admission are separate requirements. Record both
before promoting a signed package to independent review. Bootstrap admission does
not authorize a Definition vote, C2-023, C2-024, `EXECUTE_STAGE_A`, Stage A/B/C,
real-WAN execution, `BenchmarkResultQC`, Feature 010 GO or Feature 011. Existing
governance STOPs and exact-head review requirements continue to apply.

## Signing and audit

Each signer checks its own ID/key, the entire frozen validator set, the exact
mapping, receipt and raw API evidence, the approved source/tree and caller workflow,
the zero-execution marker and artifact archive digest, and all signed run/artifact
times. Sign the existing vote object's `.message` bytes. Signing only an ID string,
JSON file digest or coordinator-supplied prehash does not satisfy this contract.

Use the actual timezone-aware `submitted_at` and retain an independently attributable
audit event. Registration votes must meet the existing verifier's
`submitted_at >= receipt.checked_at` and
`submitted_at < registration_artifact_expires_at` bounds as well as any stricter
governance window. The operator also checks real current time and current artifact
availability before signing/admission: an offline snapshot cannot prove ongoing
availability, and backdating cannot repair expiry.

Collect exactly three valid mapping votes and exactly three valid registration
votes under the same frozen four-member set. Each quorum needs three different
controllers; the verifier does not require the same trio for both objects. Preserve
all submissions for audit and document which exact quorums were verified.

## Rotation, revocation and loss of independence

Suspected compromise, unexplained signature, lost key, changed administrative
control or a broken custody boundary immediately suspends governance admission and
new signing for the affected package. Record when, why, affected IDs and the scope
of uncertainty. Stop promotion; do not lower the quorum or create substitute votes.
Reassess shared administration/recovery paths for all four controllers.

A replacement key requires a new `signer_id`, fresh owner/key authentication,
custody review, a new immutable validator-set ID and new complete mapping and
registration quorums for that set before future admission. Keep `controller_id`
only if the same accountable administrative authority remains; a replacement
authority gets a new ID. Update governance approval and validity explicitly.
Custody changes without a key change still require a new register revision and
renewed governance review before signing resumes.

Preserve old sets, signatures and revocation/supersession decisions as audit
history. The existing offline verifier has no custody revocation feed; its ability
to verify an old signature does not reinstate governance approval. Do not edit old
signed bytes or retroactively claim that rotation repaired compromised history.
