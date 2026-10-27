# Seed set agreement and release — selected reference contract

T047/T053, standing scope 3. **Selected for implementation; NOT yet qualified.
R2.3 OPEN / Formal NO_GO.** Extends the existing-key PVSS component selected in
`995994bf` / clarified in `18bf3307`, with its implementation at `6aab9d16`.
All artifacts stay in isolated feature000 formal/reference. This selects an
internal seed-purpose protocol, not a production transition or a new authority.

## Why agreement is necessary

Opening before fixing the dealer set permits a last selector to choose among
different sums. A single irrevocable first-vote quorum can split and lose
progress. Waiting for all four contributions lets one Byzantine actor stop
progress. Therefore use one PBFT-style agreement instance for the encrypted
dealer set, before honest opening. The independently provisioned four validator
identities/keys and fault bound f=1 are unchanged. There is no new group key,
coordinator authority, independently trusted setup or entropy source.

The prepare/commit/view-change structure follows the authenticated
[Castro–Liskov protocol, section 4](https://static.usenix.org/events/osdi99/full_papers/castro/castro_html/node4.html).
This reference defines a single instance with no log truncation. It uses three
distinct PREPAREs (including the primary's separate PREPARE) and three distinct
COMMITs. The implementation and its proof must qualify this choice explicitly;
citing PBFT is not a substitute for those checks. Repeated messages and all
invalid/conflicting attempts remain distinct retained source occurrences.

## Instance, values and signed statements

The instance is the complete PVSS context EXCEPT `source_cut_id`. In particular
it includes original ISC consensus b, parent, round, original ISC view, height,
epoch, configuration, schema/arithmetic profile, registry and origin. It never
contains an ISC certificate witness c. Individual original anchor cuts remain
inside the signed DEAL and in the enclosing source event inventory. Different
lawful witnesses/cuts of one b do not create another agreement instance.

A proposal is an ordered list of three or four exact original valid DEAL
artifact IDs, with distinct enrolled dealers and matching instance. Order is by
original dealer identity. It retains all four encrypted recipient shares in
each DEAL. It is a selected candidate, not a replacement for the full retained
delivery inventory. A DEAL ID, actor or share may not be invented by a successful
downstream seed observation. Every reference resolves to earlier original bytes.

Signed agreement bodies have `profile="SEED-SET-PBFT-REFERENCE-v1"`, `kind`,
`instance`, `actor`, `agreement_view` (canonical uint64 string), and the following
kind-specific fields:

* PROPOSE: `deals` and `new_view` (empty for view zero, otherwise the exact three
  STATUS artifact IDs supporting this view).
* PREPARE: exact `proposal_id`.
* COMMIT: exact `proposal_id` and `prepares` (three matching original PREPARE IDs).
* STATUS: `prepared_proposal` (empty when none) and `prepares` (empty or the exact
  three matching PREPARE IDs for the highest locally prepared prior view).

Arrays above are canonical signer order; this is witness order, never deletion
of original delivery occurrences. The envelope has `body` hex and `signature`
hex as in the PVSS component. Ordinary Ed25519 signs exactly
`deltareduce.seed-agreement.statement.v1 || 00 || len(body)_BE64 || SHA512(body)`.
Artifact IDs use `deltareduce.seed-agreement.artifact.v1 || 00 || envelope`.
No historical NSG1/ISC signature is reused. These are seed-purpose statements,
not new native Vote/QC kinds or physical WAL records.

## Producer guards and view changes

Leader of agreement view v is registry position v mod 4. At view zero it can
propose any valid candidate from the original delivered encrypted offers.
Each honest actor prepares at most one proposal per view. It commits only after
three matching valid PREPAREs; the prepared proposal and proofs are durable
before signing/exposure. It never signs another prepare/commit for an old view
after durably entering a later view. No surviving signed intent can be forgotten
by crash/replay. Every exact retry retains its original statement identity.

A STATUS for view v>0 reports the highest prepared prior view and its original
quorum evidence from that actor's complete prefix. Entering the new view must be
associated with existing approved logical timeout/view progress evidence in the
enclosing source fold; this contract creates no clock, duration or expiry rule.
Its safety guards also hold for arbitrary monotone view entry. A new leader
supplies three valid STATUSes for v. If any contains a prepared value, the
proposal preserves the value from the highest reported prepared view. Equal
highest prepared views must agree; conflicting evidence fails closed. If none
is prepared, it may propose any valid encrypted set. Recipients recompute this
rule from the original evidence, never from the leader's claimed safe flag.

A COMMIT certificate is three matching COMMITs in one view for one proposal.
Only after checking such a certificate may an honest receiver open the PVSS
shares for those dealers. All original certificate/proof witnesses are retained.
The final *value* is the ordered dealer/content selection, independent of the
COMMIT witness subset. A later view cannot select a conflicting value after a
commit quorum; this requires the cross-view induction, not just same-view quorum
intersection. Stable-view progress requires eventual delivery, a correct leader,
three responsive honest validators and the existing phase/deadline policy.
Missing/malformed/withheld evidence leaves an incomplete state; it does not
erase inputs, create a seed fallback or fabricate AbortQC.

## Coins, output and remaining joins

Honest contributions are generated once per semantic instance from the original
existing Ed25519 private seed k matching the independently enrolled public key.
No new key or random service is introduced. For j=0,1,2, the coefficient is
`LE(HMAC-SHA512(k, coefficient_domain || frame(J(instance)) || j_BE8)) mod L`,
where coefficient_domain is `deltareduce.seed-pvss.coefficient.v1` plus NUL.
The three pseudorandom function inputs are distinct. The original source cut,
certificate witness, arrival order and opening/commit witness do not enter this
coefficient derivation. Different original cuts of the same instance preserve
the polynomial, while remaining different signed artifacts/occurrences.

DEAL proof nonce at recipient i is
`1 + LE(HMAC-SHA512(k, deal_nonce_domain || frame(J(DEAL_core)) || i_BE8)) mod (L-1)`;
OPEN uses the identical formula on OPEN_core with a separate open_nonce_domain.
The domains are `deltareduce.seed-pvss.nonce.deal.v1` and
`deltareduce.seed-pvss.nonce.open.v1`, each plus NUL. No nonce is zero; no nonce
is deliberately reused across different statements or purposes: the KDF inputs
are distinct, with residual output-collision probability covered by the stated
computational assumptions. Ed25519 signing keeps its
existing algorithm and does not consume these proof nonces. Exact retries
derive identical bytes. The scalar used to open shares is the standard clamped
first half of SHA512(k), reduced modulo L, and must reproduce the enrolled key.

Security explicitly additionally assumes HMAC-SHA512 pseudorandomness for the
secret enrolled seed in the presence of its Ed25519 public key/signatures and
domain-separated proof uses. This is a computational assumption about the SAME
existing key authority, not a new independently trusted source. Modulo reduction
has negligible statistical bias bounded by L/2^512 < 2^-259 per coefficient;
we do not claim exact information-theoretic uniformity. Public verification does
not prove honest private generation; the existing honest-validator/fault bound
and specified producer algorithm are essential to the bias-resistance claim.
Qualification must state this premise, not replace it by a `coins_valid` flag.
Private seeds never enter a snapshot, public evidence or repository; executable
generation tests use explicitly public synthetic seeds only.

After a committed selection, any three valid OPENs for each selected dealer
recover its unique point. Sum these points in canonical dealer order. `seed_id`
is SHA256 under `deltareduce.seed-output.v1` plus NUL of the length-framed
canonical instance and resulting compressed point. It excludes opening/commit
witnesses, source cut, randomized proof bytes, signature bytes and arrival order.
The required transcript separately retains exact original evidence IDs and all
occurrences. The existing native transcript/EC source join must establish which
original transcript is persisted; equal seed values do not merge original objects.

The native schema-2 `SEED_TRANSCRIPT` uses the existing field names. Its context
is decoded from the original B preimage; `input_set_certificate_id` is computed
as b, never copied from an untyped c reference. Its `share_ids` are the sorted
exact DEAL artifact IDs in the committed selection, NOT the reconstruction or
COMMIT witness subset. All OPEN/COMMIT occurrences remain in the source inventory.
`seed_profile_id` is the domain-separated content ID of the closed reference
algorithm descriptor implemented by `seed_source.native.profile_descriptor`.
The installed producer/codec pins bind this descriptor as part of the selected
future reference rules. An imported descriptor never elects its own authority.
This algorithm-content ID is not a production sigma or permission to deploy.
The constructor checks the original native body and independent epoch/registry;
it cannot prove that the ISC was finalized or the seed was durably released.

Required qualification inside the existing R2.3 residual: same/cross-view safety,
release-after-commit, preservation of all events across invalid attempts/retries,
durable honest producer guards and crash recovery, stable-view progress under
the existing failure policy, private coin derivation, and original-index joins.
No component or conditional primitive theorem closes those obligations. The
complete source/configuration/units, public collections/current/environment and
initial/incomplete/ABORT relation remain the three frozen R2.3 obligations.
