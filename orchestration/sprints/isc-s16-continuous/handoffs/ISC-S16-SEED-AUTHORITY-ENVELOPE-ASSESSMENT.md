# Seed authority applicability under standing R2.3 delegation

27 October 2026. T047/T053, ISC-S16-CONTINUITY.
**R2.3 OPEN / Formal NO_GO. No implementation or seed contract selected.**

## Authority applied, not requested again

The current 18030 sprint is `sprint-0001-fada895e`. Coordinator 2750 retains
assignment `37cefaae-25f1-4bef-9d55-9089274e0fe4` and branch
`agent/isc-s16-continuous-sprint`. Human decision
`scope-decision-581aa08f7ae0755215e752fbdac26527` edited the earlier request into
standing R2.3 delegation. Effective revision 2 is authoritative; exact ACK
`scope-ack-0694bb30c9417d08cb364cb34548e9be` was persisted and independently
confirmed by GET. The effective-core SHA-256 is
`8323af1d7759b1166dd68c7499cbb8be5db40548b6a36152071f9f565f64fc04`.

This supersedes the old generic requirement to stop after specifying every
missing seed verifier/binding. Algorithm, byte layout, deterministic derivation,
history association and ordinary proof engineering do not need another decision.
The new delegation nevertheless expressly excludes a signing/entropy authority
whose approved purpose does not cover the use. A registered public key and
authorization to sign a particular validator vote are different facts.

This assessment reuses the checkpoint `46f5acff0f8f35b542a140162fd4dd6771b721d1`
seed audit. It does not repeat that corpus search. The adjacent
`ISC-S16-SEED-AUTHORITY-ENVELOPE-EVIDENCE.json` pins the effective instruction,
ACK, prior audit and exact source blobs used below. Hash verification of those
blobs is not new formal qualification.

## The remaining authority edge

The relation needs independently verified **original reveal/beacon evidence**
for a seed bound to the original epoch, round, ISC consensus body `b` and cut.
The output must retain the existing bias-resistant, post-ISC randomness claim,
not merely be a deterministic label that can be computed from public input.
No proof of cryptographic primitives from first principles is requested.

Existing authority applicability is as follows (full references and hashes are
in the evidence file):

| Existing authority | Covered use | Uncovered use needed by the candidate |
|---|---|---|
| Profile v1, `26eb02d0…`, §2–3 | Independently provisioned epoch/key/config pins and faithful custody of original bytes; legality is checked by producing rules | Custody does not certify that a captured arbitrary value is a lawful seed share or bias-resistant entropy |
| SIG-ISC and I-B, `26eb02d0…:docs/adr/0014-isc-identity-sequence-amendment.md`, §1 | An authenticated quorum witness C establishes the same consensus body B | Seed selection/identity must not depend on which C or signer set witnesses B |
| SIG-NON-ISC, `bb9fce95…:docs/adr/0015-non-isc-authority-binding-v1.md`, §§1,3,5 | Closed dispatch for ROUND_CONFIG, EC, APC, PARAMETER, AGGREGATE_ROOT, APPLY, VIEW_CHANGE, ABORT; exact original body/context | Arbitrary worker/storage/beacon messages are expressly excluded; the seed row retains a separate selected producer/verifier obligation |
| Native contract N=`60c692f6…`, 008 spec FR-006/007 and plan | Required order, seed profile and all accepted reveal/beacon evidence; named adapter port | No concrete share-generation/authentication authority is instantiated by naming the port |
| N `ChainVerifier::verify_seed` | Context, supplied ISC parent, shape and transcript content ID | It does not receive or authenticate original reveal/beacon bytes or derive the primitive seed |

The normative randomness requirement is not inferred from the word "seed":
N's 008 spec §2 **Randomized Bucketing** and US1 explicitly require a
bias-resistant seed after ISC. I-B §1 separately prohibits choosing it from
witness c/signers. These existing obligations cannot be dropped to fit a
hash-only implementation.

## Concrete constructions assessed against the new permission

1. **Hash B / public config / known checkpoint.** This needs no new signing
   key and can be encoded and proved deterministic. It supplies no new hidden
   post-freeze entropy: anyone holding those public inputs can compute the
   same value beforehand. Delaying the API call does not establish the
   required randomness property. Selecting this as the original seed source
   would change the claim, not just implement a missing verifier.

2. **Hash the available ISC signatures, C or its signer set.** Authentication
   of the votes is already available. But witnesses for the same B can retain
   different original signers at different arrival cuts. Derivation from the
   selected witness violates the accepted I-B independence requirement.
   Sorting the received signatures or choosing the first three does not remove
   dependence on the available set. Waiting for all four introduces an
   additional availability requirement; it is not justified by a threshold of
   three. This is a design distinction, not a newly executed attack or TLC run.

3. **Commit/reveal bound through RoundConfig.** An authenticated config can bind
   an algorithm and commitments, and a reveal checker can verify their exact
   preimages without a new per-reveal signature. This is the strongest candidate
   for reusing existing authority. However, config authenticity alone says
   neither who supplied independent hidden contributions nor which selected
   generation/withholding rule provides the required bias resistance. Letting
   the config proposer choose and know all preimages is not that property.
   Assuming honest entropy contribution or accepting a convenient surviving
   subset would supply an unapproved seed-producer premise. A commitment hash
   is not evidence for that premise. No such applicable source rule is supplied
   by the already selected contracts. This candidate is not declared
   mathematically impossible; its additional authority/purpose must be explicit.

4. **Seed-specific signatures or a threshold/VRF beacon.** A precise scheme
   could make evidence checking concrete. Existing K/R can identify the same
   enrolled validators, but NSG1's closed dispatch does not authorize a new
   seed message or prove a threshold key's setup. Defining a new seed signing
   purpose/entropy role, or adding a threshold public-key authority, crosses
   the express authority boundary even if no additional operator or network
   service is installed. It cannot be hidden inside a codec helper.

5. **Use later EC signatures, public ExpectedSeedValue or trusted custody.**
   These respectively use downstream success, the refinement target or faithful
   bytes as the missing origin fact. The current scope explicitly forbids all
   three. Rejecting every seed-bearing history instead would narrow the domain.

## Decision needed and bounded next step

**SEED_ENTROPY_AUTHORITY_USE_NOT_COVERED**: no qualifying construction using
only the examined already-approved authority has been established. This is
not a theorem that every possible cryptographic construction is impossible and
not a new global search for absent contracts. The distinction from the earlier
blocker is precise: routine verifier/derivation selection is now delegated;
the missing independently justified seed-contribution purpose is not.

The new Pending request concerns **one additional authority purpose**: permit
the already enrolled, fixed-epoch validator set to act as the explicit seed
contribution/signing authority in the isolated future-generation formal/reference
model. This would add a seed purpose to those same independently authenticated
identities; it would not assert that NSG1 already permits it. No new deployment
operator, independently trusted public key, external beacon or factual-history
observer is proposed.

If approved, the standing delegation would cover selecting, recording,
implementing and qualifying a minimal concrete protocol for that new purpose:
exact evidence generation/verification and seed derivation, canonical domains,
pre/post-ISC ordering, quorum/withholding/duplicate/incomplete behavior and
history binding. A new seed signature purpose must be separately specified;
it cannot relabel existing NSG1/ISC signatures. Any internal key/setup material
must be derived and completely verified through the approved authority and
original authenticated transcript, not independently trusted because a file
contains it. An independently trusted setup/key remains outside this proposal.

The original bias-resistance, witness-independence, failure/liveness and full
source-domain obligations stay mandatory. If they cannot be met within that
authority, the exact remaining boundary must be reported rather than a weaker
claim substituted. The concrete algorithm and compatibility consequences must
be recorded immutably and pass ordinary proofs, qualification and reviews before
use in the enclosing relation. A separate specification-only STOP for ordinary
choices within the newly approved purpose is **not** proposed.

No seed signing purpose, cryptographic scheme, new key/root, entropy authority,
source-domain restriction or weaker claim has been selected by this memo.

All existing R2.3 permission remains valid. This does not ask to reauthorize
R2.3, deterministic bindings or ordinary formal work. Existing schemas,
production Init/Next, runtime/WAL, original objects, signatures and identities
remain unchanged. R1/R2.1/R2.2 remain CLOSED in their original domains.

No `RESUME_FORMAL` is submitted just to route around this unresolved semantic
condition. The coordinator remains active while the Pending decision is
outstanding; graph/review history is preserved. This memo has not received
graph reviews and is not qualification evidence. After a selected contract is
actually implemented and qualified, the normal two-process review gates still
apply. Same-executor process reviews are not independent Formal GO attestations.

## Residual and compatibility

R2.3 is **OPEN**: original seed origin remains an input to complete producing
history, artifact-namespace durability, full initial/incomplete/ABORT state
composition. No one of those obligations is closed by this assessment. The
already qualified EC-companion conjunct is preserved and not overclaimed.
`nativeArithmeticRecoveryRefines` is not started. Recorded mandatory proof
FAIL and unrun dependent gates are unchanged; Formal NO_GO remains.

Any eventual seed contract must identify its future-generation effect on
seed/profile/transcript and downstream identifiers and qualify the affected
source, Lean, TLA, refinement, mutant, compatibility and review gates. Old
objects are not migrated, resigned or relabelled; no concrete sigma is assigned.
