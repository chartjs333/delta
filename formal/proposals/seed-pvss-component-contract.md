# Existing-key seed PVSS component (T047/T053)

**Selected isolated formal/reference component, 27 October 2026. R2.3 OPEN;
Formal NO_GO.** This is not a complete seed producer or an admissible-source
predicate. Scope revision 3 of assignment
`20451db6-b10f-4613-96fa-f1fa2e3c4d37` explicitly authorizes this additional
purpose of the existing enrolled validator keys. Its core hash is
`9b7dd90ad3ddaa6ab6ad79f26dea32ab4be401038ec4ea266ba5deb3bdfd47f7`.
Coordinator activation is `a950c2c82b44c716fee127a05f036615072af5cc`.
Neither the ACK nor the two process reviews authenticates protocol evidence.

## Selection and boundary

Select publicly verifiable encrypted polynomial shares on the prime-order
Edwards25519 subgroup, using the SAME independently enrolled Ed25519 public
keys. This follows the distribution/decryption construction in
[Schoenmakers, CRYPTO 1999, sections 3.1–3.2](https://berry.win.tue.nl/papers/crypto99.pdf).
It needs neither a new recipient key nor a private-channel authority. The
existing pinned libsodium 1.0.22 arithmetic supplies canonical subgroup checks,
addition, unclamped multiplication and Elligator2 mapping; see its
[official point API](https://libsodium.gitbook.io/doc/advanced/point-arithmetic).
These references motivate the construction, not a claim that this composition
has inherited a proof of a complete distributed beacon.

Rejected alternatives: public hashes/signatures as entropy (no hidden
contribution); plain commit/reveal (last-revealer withholding); Feldman
commitments on the output generator (publish the secret point); a new threshold
key or independently trusted beacon (unnecessary additional setup/authority).

The fixed profile has four existing validators, threshold three and at most
one Byzantine validator. It is not generalized to a new membership or epoch.
The component returns a verified DEAL/OPEN object or a reconstructed **single
dealer point**, never an authorized seed. A whole producer must additionally
prove a unique qualified dealer-set lock BEFORE honest opening, at least one
honest hidden contribution, quorum progress under the existing failure policy,
durable source/cut association and complete retained-occurrence interpretation.
In particular, `quorum signatures exist` is NOT assumed to prove agreement
liveness. Split locks, view changes and selective publication remain producer
obligations; they may not be hidden in a successful verifier callback. These
are within the existing R2.3 residual, not a new Pending decision.

## Algebra and exact primitive rules

Let L be the existing Ed25519 prime subgroup order, G its standard base point,
and A_i=x_i G the existing validator public key at canonical registry position
i=1..4. Keys must be distinct canonical nonidentity prime-subgroup points.
Existing signature verification and independent bootstrap/registry resolution
are reused. The registry and original key objects are unchanged.

The secondary generator H is the first nonidentity `from_uniform` output for
`SHA256("deltareduce.seed-pvss.generator.v1" || 00 || counter_BE32)`, starting at
zero. H is public deterministic setup, not a key. H is NOT HashToScalar(...)G;
its discrete logarithm relative to G must be unknown. Commitments and shares
may be the identity; zero polynomial coefficients/evaluations are lawful.
Reject noncanonical, off-curve and mixed-order encodings. Scalars are exactly
32-byte little endian integers in [0,L); never silently reduce supplied scalars.

A dealer chooses p(z)=a0+a1*z+a2*z^2 in F_L. It publishes C_j=a_j H for j=0..2
and encrypted E_i=p(i) A_i for all four enrolled recipients, with a DLEQ proof
for (H, sum_j i^j C_j) and (A_i,E_i). A recipient opens D_i=x_i^(-1) E_i,
with DLEQ for (G,A_i) and (D_i,E_i). Any three distinct correct openings
reconstruct S=p(0)G by Lagrange interpolation. Reconstruction must be identical
for all four three-recipient subsets and must not depend on DLEQ randomness,
signature bytes, arrival order or which subset is available.

For DLEQ (g1,y1,g2,y2), witness x: choose fresh w, R1=w*g1, R2=w*g2;
c=LE(SHA512(domain || 00 || frame(binding) || g1 || y1 || g2 || y2 || R1 || R2))
mod L, r=w-c*x mod L. Proof is c_LE32 || r_LE32. Verification reconstructs
R1=r*g1+c*y1 and R2=r*g2+c*y2 and recomputes c. `frame` is byte length BE64
followed by exact bytes. Distribution and opening use separate domains
`deltareduce.seed-pvss.deal-proof.v1` and
`deltareduce.seed-pvss.open-proof.v1`. The binding includes exact canonical
unsigned statement core and recipient position. It includes ALL encrypted
shares/commitments for DEAL and exact signed DEAL content ID for OPEN.

Honest generation uses independent uniform polynomial coefficients and proof
nonces. Synthetic qualification uses explicitly supplied public test scalars;
it does not certify entropy or production key custody. A later producer must
derive/generate and bind honest coins without a new independent authority and
must qualify that rule. No secret production key is read or written here.

## Statement bytes and source boundary

Canonical ASCII JSON: sorted object keys, no whitespace, no duplicate member
names, no extra fields, strings and arrays only; binary values are lowercase
hex. The decoder requires reconstruction byte equality. Existing native
objects are neither migrated nor relabelled.

Context fields are `formal_semantics_id`, `origin_id`, `validator_epoch_id`,
`registry_id`, `round_id`, `round_config_id`, `parent_checkpoint_id`,
`isc_body_id`, `arithmetic_profile_id`, `parameter_schema_id`, `height`, `view`,
`source_cut_id`. Heights/views are canonical uint64 decimal strings; height is
positive, as in the existing native Context. Content IDs use the existing sha256 grammar. Round
labels use the existing label grammar. No certificate witness c may replace
the consensus body b. Context equality is checked against the independently
supplied expected context; its source legality remains the producing-fold join.
Here `source_cut_id` denotes the shared original finalized-ISC anchor cut,
not the sending actor's later delivery position. Each DEAL/OPEN occurrence
retains its separate actor, original event bytes/index and local durable cut in
the enclosing original source inventory. Recipients do not manufacture equal
local journal prefixes. A replay keeps the signed anchor while retaining each
distinct later delivery occurrence.

DEAL core has `kind="DEAL"`, `profile="SEED-PVSS-ED25519-COMPONENT-v1"`,
`context`, `actor`, three `commitments`, and four `encrypted_shares` in exact
registry order. Add four `proofs`. OPEN core has the same profile/context,
`kind="OPEN"`, `actor`, `deal_id`, `share`; add one `proof`. OPEN does not by
itself establish that the dealer set was locked or that release was permitted.

The signed envelope has exactly `body` (lowercase hex of original canonical
statement bytes) and `signature` (64-byte lowercase hex). The exact Ed25519
signable message is
`"deltareduce.seed-pvss.statement.v1" || 00 || len(body)_BE64 || SHA512(body)`.
This is ordinary Ed25519 over the stated domain-separated message, not implicit
reuse of ISC/NSG1 and not Ed25519ph. Content ID hashes the exact original signed
envelope under `deltareduce.seed-pvss.artifact.v1` plus NUL. Such witness IDs
identify evidence, not the eventual consensus seed identity. The combined seed
must not include a reconstruction witness subset or randomized proof/signature.

Cryptographic premises are explicit: prime subgroup arithmetic, strict Ed25519
unforgeability for the new domain, hash collision resistance/Fiat–Shamir random
oracle security, DDH/discrete-log hardness for the two generators and secrecy
of honest enrolled keys/coins within the existing fault bound. Lean algebra
and transcript checks do not prove these computational premises. A decoded
statement, valid signature, custody record or correct polynomial is not a
substitute for honest-origin/source-prefix verification.

## Compatibility and required qualification

Only new `formal/reference/seed_source` and isolated proof/evidence artifacts
are introduced. No deployed Init/Next, QC, WAL, native sequence, old signature,
existing key object, runtime or production semantics ID changes. Old seed
shape fixtures retain their historical meaning and are not relabelled valid
PVSS evidence. The eventual full future-generation binding needs new qualified
hashes; none are assigned here as production sigma.

Acceptance for this COMPONENT: exact signature/context/whole-array binding;
malformed scalar/point and replay/domain negatives; all reconstruction subsets;
zero evaluations; corrupt and duplicate openings; byte round-trip and retained
originals; algebraic interpolation and DLEQ completeness theorems with axiom
audit. Even all of these passing leaves the full producer/retention/durability
join and complete R2.3 relation OPEN. No seed is released through this module.
