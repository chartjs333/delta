# Arithmetic Unit Source Binding v1

**PROPOSED — exact contract for a separate semantic decision, not implementation authority.**
9 October 2026. T047/T053, ISC-S16-D01. **R2.3 OPEN / Formal NO_GO.**

## 1. Authority and scope

Human decision `scope-decision-b9dda15006982227b7149678f72d2b9d` applied
scope revision 14 to assignment `13069d7e-a148-475a-bd49-9885bf2f283d`.
Role 2753's exact ACK `scope-ack-ff71d5b0de24fc9b147e3abd03ad37cc` was
confirmed by effective-scope GET. That decision authorizes this specification
only. It does not approve its new fields, select a numeric quantum, or authorize
code, schema, proof or runtime changes using the proposed rule.

The missing obligation is already part of frozen R2.3: independent source
selection of apply/model/optimizer units. Feature 008 section 3 and FR-026/032,
and amendment 0001's authority graph and conversion rule, require it. The audit
at `f9092d046c117b8d2fcf139eca1834281c0c0c28` is retained unchanged. The scope-14
decision supplies no additional immutable original selector or original unit
artifact. This proposal therefore uses the existing initial/configuration
authority for a **future generation**; it does not claim to recover a missing
fact about historical native objects.

Exact source references and byte hashes are in
[`evidence/unit-source-binding/source-index.json`](evidence/unit-source-binding/source-index.json).
Important distinctions from those sources:

- N (`60c692f6e391f839829dfc64e93380db54cd507b`) defines the native numeric
  `ApplyArithmeticProfile` and its hash, but no quantum field.
- The native `apply_profiles` snapshot collection is an inventory. Finding an
  ID in that list alone is not proof that the original RoundConfig selected it.
- At `0246277a29fb8477112d4b6f5e900417d46fe167`,
  `ProfileConfiguration.configuration` has no apply-profile source selector.
  Its `integer_profile.profile_id` is the existing fixed-point/input profile;
  it must not be silently redefined as an apply-profile ID.
- The candidate `PROFILE.apply_quantum` and `MODEL/OPTIMIZER.quantum` already
  represent a common positive reduced rational. Their hashes do not provide
  independent authority for choosing that rational.
- Profile-v1's independently pinned `initial_config_ref` and `genesis_ref`,
  then the original configuration votes/QCs and full native history, supply the
  authority path. The published origin/import component does not yet prove a
  complete genesis/producer/public-state relation.

No claim of a complete admissible-history counterexample or absence of every
possible external contract is made. If an applicable immutable original selector
is provided, it must be examined before accepting a replacement contract.

## 2. Minimal selected proposal: three explicit source bindings

Use one common quantum `q = x/y` for apply, model and optimizer, as the existing
amendment-0001 relation already requires. Do not add three independently variable
units, a new certificate, registry, signature, observer or mutable lookup service.

| Source surface | Exact proposed addition/change | Authority |
|---|---|---|
| Independently pinned initial configuration | One mandatory member `arithmetic_units`, the closed object U below | Existing provisioning of the complete initial configuration **together with** the pinned genesis, origin, epoch and schema/producer pins |
| Native `APPLY_ARITHMETIC_PROFILE` P | One mandatory member `apply_quantum`; `schema_version` becomes `"2.0.0"` | Exact P bytes selected by the original authorized configuration; P is not self-authorizing |
| RoundConfig | One mandatory text member `apply_arithmetic_profile_source`, containing the canonical numeric source R below; `schema_version` becomes `"3.0.0"` | Existing configuration proposal/vote/delivery/quorum/finalization rules |

These are proposed canonical-source changes, not fields already implemented or
covered by old qualification. All other fields, the approved storage/retention
bindings, signature contracts, context fields and original ordered collections
remain required. An independently pinned future schema set dispatches these
grammars; source-supplied version strings do not select a verifier. No concrete
`formal_semantics_id` is assigned here.

Why all three bindings: initial units must exist before a first ApplyQC; the
apply profile must define its representation under FR-026; and a profile in an
untrusted inventory must be selected by configuration authority before an
arithmetic vote. A quantum-bearing profile alone leaves genesis units and profile
selection unresolved. An initial-only default leaves the configured profile's
representation implicit. A separate unit certificate introduces unnecessary
authority and a second consensus path. Those alternatives are not selected.

## 3. Exact canonical fields and bytes

### 3.1 Initial object U

`initial_configuration.arithmetic_units` has exactly these members:

```text
parameter_schema_id, quantum, schema_version, type_name
```

- `type_name = "INITIAL_ARITHMETIC_UNITS"`.
- `schema_version = "1.0.0"`.
- `parameter_schema_id` is the existing `sha256:` plus 64 lowercase-hex
  content ID of the exact independently selected parameter schema.
- `quantum` has exactly `denominator` and `numerator`. Both are positive
  canonical decimal **strings**, respectively `y` and `x`, with no sign,
  leading zero or whitespace. `1 <= x,y <= 9223372036854775807` and
  `gcd(x,y)=1`.

Use the existing initial/control ASCII canonical JSON grammar: sorted keys,
no whitespace/BOM/trailing bytes/escapes; reject duplicate, unknown or missing
members before typed construction; require decode/re-encode byte equality.
For symbolic `S`, `x`, `y`, U's complete byte expression is:

```text
ASCII('{"parameter_schema_id":"') || ASCII(S) ||
ASCII('","quantum":{"denominator":"') || dec(y) ||
ASCII('","numerator":"') || dec(x) ||
ASCII('"},"schema_version":"1.0.0","type_name":"INITIAL_ARITHMETIC_UNITS"}')
```

Here `dec` is the unpadded positive ASCII decimal spelling, not a JSON number
or a host floating-point conversion. These expressions are a specification,
not literal production input with placeholder values.

U is embedded in the complete original initial configuration bytes. There is
no separate U signature, new U content-ID namespace or reference supplied by
the import. The existing bootstrap `initial_config_ref` binds the whole changed
configuration; its independently provisioned `genesis_ref` binds the original
genesis/vector preimages. That pair binds U to genesis without a self-hash cycle.
U does not contain its own configuration/bootstrap/manifest ID. The full initial
configuration's other fields and native validity checks are retained; this does
not invent a complete genesis parser by treating U as a valid initial state.

### 3.2 Quantum-bearing native apply profile P

Reuse the native certificate JSON serializer, with keys in this exact order:

```text
accumulator_proof_id, apply_quantum, domain_weights, formal_semantics_id,
learning_rate, momentum, nesterov, rounding, schema_version, type_name,
weight_decay
```

All ten old members retain their existing types and validity conditions, except
the explicitly changed schema version. `type_name` remains
`"APPLY_ARITHMETIC_PROFILE"`. `formal_semantics_id` must equal the independently
selected, eventually qualified future generation, never the old accepted ID
substituted into new bytes. No example generation ID is made authoritative here.

`apply_quantum` reuses native `Rational` JSON:

```text
ASCII('{"denominator":') || dec(y) || ASCII(',"numerator":"') ||
dec(x) || ASCII('"}')
```

Thus its denominator is an exact JSON integer token and its numerator a decimal
string, as in N's `rational_json`. This is deliberately different from the
control-document spelling in U, and from candidate `[x,y]`; a typed exact-integer
conversion joins them. Never hash a normalized replacement for the original
source bytes. Reject fractions such as 2/8 instead of reducing them during
admission; reject 0, negative values, exponent/float/bool tokens, duplicate keys
and noncanonical decimal forms. The bounds above reuse the existing
`NativeBinding.positiveQuantum` domain. They do not narrow the old coefficient
fields' U64 denominators or claim that every native rational is a quantum.

Retain the existing hash construction and domain:

```text
pid = ID("deltareduce.008.apply-arithmetic-profile.v1", canonical_native_JSON(P))
ID(d,b) = "sha256:" || lowerhex(SHA256(ASCII(d) || 00 || b))
```

Keeping the domain preserves the hash algorithm's existing namespace, not byte
compatibility. P has a new mandatory field, schema version and future semantics
pin, so its actual ID differs. Old P bytes/IDs never acquire an implicit quantum.

### 3.3 Exact configuration selection without a hash cycle

RoundConfig's new `apply_arithmetic_profile_source` is a **text** field containing
one exact canonical native-JSON object R, with these seven keys in this order:

```text
apply_quantum, domain_weights, learning_rate, momentum, nesterov, rounding,
weight_decay
```

Each value uses precisely the corresponding P encoding and validation in section
3.2, including native rational spellings and the existing ordered domain-weight
rows. No defaults, alternative profiles, extra fields, accumulator ID, config ID,
QC ID or source-supplied executable code are present in R. Its type/version is
selected by the independently pinned configuration grammar and this field path;
R has no standalone certificate, signature or ID. Its complete JSON text is
retained, decoded strictly and re-encoded byte-for-byte. A JSON display may escape
this text; those display escapes are not bytes of the DRC1 field value.

In the existing DRC1 ordered object this field sorts before `availability_policy`.
The complete configuration has schema version `"3.0.0"`; all other fields are
retained, including scope-13 retention and the original integer profile. Reuse
DRC1's header `44 52 43 31 01 00 00 01`, BE32 payload length, object tag `31`/BE32
member count and sorted encoded members. The new member is
`T("apply_arithmetic_profile_source") || T(ASCII(canonical_native_JSON(R)))`,
where `T(s) = 21 || BE32(len(s)) || s` for printable ASCII bytes (tags in hex).
Recompute the actual member count/lengths. Existing scalar, array and nested
encodings are unchanged. The configuration ID remains
`ID("deltareduce:003:round-config:v1", exact_DRC1_frame)`.

The existing CONFIG vote/authentication contract binds that exact configuration
body ID and full context. At config admission, validate all seven numeric fields,
original domain/weight constraints and q/parent continuity; do not require a
future APC or ApplyQC to establish configuration authority. Preserve existing
coefficient, Nesterov and rounding checks. This changes the declared source
selection/admission contract, not the signature algorithm or quorum threshold.

**Why no full P ID inside RoundConfig:** the existing accumulator proof names
its fixed-point configuration, whose `base_round_config_id` must equal the
original RoundConfig ID (`NativeAccumulatorBinding.load`,
`NativePlanCoefficients.ConfigLinks`). P already contains that proof's ID.
Putting P's ID back into RoundConfig would therefore create a hash cycle.
This proposal does not cut that existing binding or invent a fixed point.

After the existing original APC/proof chain is available, construct the unique
expected P from R's seven exact typed values, the **original APC's**
`accumulator_proof_id`, and the fixed P metadata in section 3.2. Independently
verify the complete original proof/configuration bytes and all existing APC
context/accumulator/bounds relations. Recompute `pid` from that P. The native
`apply_profiles` inventory must resolve exactly that P/ID when required by an
arithmetic action, with its existing ordering/uniqueness and original-preimage
checks; unrelated profiles remain retained. Original ApplyCandidate/ApplyQC
`apply_arithmetic_profile_id` must equal this derived pid. These existing fields
are not renamed. A vote command, later QC, result value or inventory iteration
order cannot choose another P or accumulator proof.

The acyclic dependency order is:

```text
independent initial/genesis units + chosen numeric R
  → RoundConfig
  → original fixed-point config / accumulator proof / existing APC linkage
  → full P and pid
  → parameter/apply input graph and ApplyCandidate/ApplyQC
```

Before APC there need not be a full P/UnitKey. That is an incomplete state, not
permission to fabricate one. R already fixes q and the numeric choices; when the
original APC exists it supplies the remaining existing proof reference. Original
APC/EC/ISC authority and all producer rules still have to be verified. This is
neither an extra APC constructor nor a claim that a policy snapshot alone proves
lawful production.

## 4. Source selection and parent/current continuity

The following is the proposed finite verification algorithm, not a new proof.

1. Verify Profile-v1's independent bootstrap digest, enrolled identity, fixed
   epoch, initial/genesis refs and approved schema/producer/signature pins.
   Resolve the complete original initial configuration and original genesis
   and vector bytes. Decode U strictly. Establish that U's schema is the same
   exact schema of the independently selected genesis model and optimizer.
   Assign their common unit `q0 = U.quantum` from those independent bytes.
   Still verify genesis lawfulness, native vector hashes/order/ranges and every
   other initial field; U cannot certify an arbitrary nonempty initial snapshot.
2. Fold the complete original native history from that origin. For each
   original round, obtain its actual configuration and exact R bytes at
   that event prefix; resolve P only when the original APC/proof is available.
   Verify the existing configuration authority, signatures,
   delivered quorum, parent, epoch, schema, accumulator and full context.
   Derive P and `pid` by section 3.3; no new/forked/later configuration may
   supply an earlier event's R or P. Configuration votes validate R and its
   parent continuity; the later arithmetic boundary also validates the full
   original APC/proof/P join. Finalized membership alone is not those checks.
3. Obtain the prior model/optimizer units from genesis or the preceding verified
   **accepted current transition** in the full original history, never from an
   import claim or the candidate's desired output. Require
   `R.apply_quantum = parent.model_quantum = parent.optimizer_quantum` and exact
   same parameter schema. When P exists, also require
   `P.apply_quantum = R.apply_quantum`.
   Config admission does not demand P or APC before their original producer stage.
   Existing candidate/current hash, height, parent optimizer, aggregate/APC and
   accumulator bindings remain necessary. This
   makes the first arithmetic input constructor independent of a later APPLY
   success or selected expected result.
4. Construct the existing candidate `PROFILE` using P's numeric fields and
   this checked q. Construct `MODEL`/`OPTIMIZER` from the exact prior vectors,
   schema and q. Their existing candidate field sets, `[x,y]` encoding and
   draft artifact hash domains remain unchanged. These derived artifact IDs
   are not native `pid`, native model value hashes, or independent authorities.
   Continue all existing R2.1/R2.2 constructor and arithmetic guards. No result
   comparison is used to discover q.
5. For a successful ApplyQC/current advance, check the complete original
   candidate/QC/parent path and computed next values. Next model and optimizer
   retain the selected q and schema. Only the existing lawful current transition
   makes them current. An unfinalized candidate supplies no new current unit.
   Other actions, reject/stutter, crash and certified abort preserve the current
   unit association and all original lineage. A verified surviving original
   record/retry uses its historical configuration/R/P/q; it does not select a
   current-time replacement or allocate another vote/sequence.
6. Check the complete imported state against this derived source state and
   Profile-v1's trusted floor/WAL cuts. This procedure supplies the unit-source
   component only; it cannot replace the remaining full producer/state relation
   or the later named recovery theorem.

The unit association is indexed by the full original origin/epoch/schema and
current tuple `(height, checkpoint_id, optimizer_id, apply_qc_id)`, with its
history prefix. A bare model hash is not a unit key: the existing native value
hash does not include q and can repeat. For a round, additionally check every
field of the existing `UnitKey` (full context, APC, source-derived apply-profile ID,
accumulator and current state). Those are source associations, not new protocol
identities or fields injected into old QC/WAL.

The ordinary apply operation has no rescaling branch. Common-unit continuity is
the existing amendment-0001 equality obligation, now sourced independently. A
different q cannot silently reinterpret an unchanged parent vector. This draft
adds no requirement that a different independent deployment choose the same q,
no default q=1, and no restriction to the illustrative quanta in old tests.
An explicit rescale, schema conversion, new origin/epoch or imported standalone
unit witness is not approved by this proposal.

### Initial, incomplete and failed histories

Before the first round/ApplyQC, q0 is derived from U and the original genesis;
no fictitious certificate is created. With no finalized RoundConfig yet, the
relation preserves that incomplete state without inventing a selected round
source; with a config but no APC, it preserves R without inventing full P.
A proposed configuration still undergoes the existing proposal/vote
rules before finality. Missing P disables the dependent successful action; it
does not delete that attempted input, delivery or original failure event.

After lawful finalization, loss of a profile/model byte artifact is represented
as the actual unavailable state, with existing repair/deadline/abort behavior.
It does not erase prior CONFIG/ISC/APC/ApplyQC lineage or retroactively unfinalize
it. Retained original evidence used to verify historical authority must not be
mistaken for present physical availability. Conversely, missing required original
source evidence prevents successful import/refinement checking; it cannot be
replaced by a callback or an assertion that public construction succeeded.

## 5. Bounds, termination and source independence

Reuse the existing per-object limits: 4 MiB native profile/candidate artifacts,
16 MiB DRC1 frame with existing text/item/depth limits, and Profile-v1's control
document and full bundle/event/journal budgets. U and the added profile/config
fields count in **actual final encoded bytes**; no digest stands in for required
preimages. Account for all existing W1/P0/P1/output representations when affected.
No lineage/delivery truncation, smaller source cap or hidden fixture-only domain
is permitted. Boundary qualification must demonstrate that the intended source
domain fits; this documentary proposal does not prove universal sufficiency.

Resolution visits a finite supplied original inventory and ordered history.
Existing backward dependencies and exact-ID resolution apply. No network lookup,
operator callback, retry-until-success or public-state search is used. Bad bytes,
duplicate association, unknown generation, missing authority, unsafe arithmetic
or a conflicting parent unit cannot yield a successful derived association.

The intended local result is uniqueness of selected source P and q from the
independent origin and lawful original configuration/current history, followed
by the existing constructor relation. Its premises name source bytes, original
authentication, original producer transitions and checked numeric bounds. They
do not include `passes_R2`, existence of a successful public projection, desired
next values or recovered-state equality. Proving that statement and integrating
all remaining source collections are still work; they are not assumptions that
this document labels as established.

## 6. Compatibility and qualification consequences

| Surface | Consequence of separately approving this exact proposal |
|---|---|
| Trust/deployment | Existing independent initial/genesis provisioning and configuration validator authority. No new key/root/signature/certificate/observer, no F, no expanded Profile-v1 deployment case |
| Admissible source histories | Future configurations fix R; the existing APC/proof join selects P and enforces unit continuity. This is a new source/admission contract closing a missing rule, **not** proof that all legacy API-admitted snapshots had those bindings |
| Certificate semantics | Quorum, signer identity, vote uniqueness, parent edges and QC formation rules are preserved. The authenticated configuration/profile content and admission guards change; claiming completely unchanged protocol semantics would be incorrect |
| Signed bytes and IDs | Initial-config/bootstrap/import IDs change. Future P and RoundConfig bytes/IDs change. CONFIG votes/signatures/QCs and downstream context-bound objects, ISC B/b and C/c, EC/APC/ROOT/APPLY IDs and actual signatures require new-generation qualification. Unchanged field names do not imply unchanged bytes |
| Model/optimizer identity | Native integer value hash algorithm stays unchanged; q comes from origin and original config/current lineage. Candidate PROFILE/MODEL/OPTIMIZER artifacts retain their existing q-bearing format. Never equate a value hash with a q-bearing artifact ID |
| WAL/replay | No new record kind, physical slot s, public ordinal V_a(s), signer or vote identity rule. New-generation original vote payloads contain their new actual IDs. Existing original histories/receipts/sequences remain immutable; no migration/relabel/resign |
| TLA | The action inventory and production Init/Next composition need no new action by design. Future configuration/source type and validity/continuity guards must be reflected in existing config and arithmetic actions/invariants and refinement. Old Init/Next/type evidence alone does not cover the changed predicates. If an additional action or trust expansion is necessary, STOP |
| Lean and public relation | Reuse original-domain R2.1/R2.2 arithmetic/constructor results. Replace the unresolved UnitSource premise by a source-derived checked association; bind configuration R, derived pid and parent units, then compose into R2.3. Do not reopen accepted components without a concrete counterexample or claim that their old instantiations cover new source bytes |
| Evidence | Requalify affected configuration/profile codecs, original authority and history bindings, unit/alias negatives, TLA model/production-mutant/refinement gates, Lean dependencies/axioms and compatibility/reviews. Old results stay valid only for their exact old artifacts |

Production integration, production recovery, guard removal, full R3 and a
concrete future semantics ID remain excluded. New source predicates cannot be
silently installed into the deployed generation. A future compatible merged
FormalVerificationReport(GO) and separate runtime authority are still required.

### Finite acceptance for the unit-binding portion after approval

1. Strict source codecs implement exactly U, R, P and the acyclic pid derivation;
   literal
   round trips, duplicate members, range/fraction aliases and missing-field
   cases distinguish the three canonical representations without normalization.
2. Original authority derives the same q/P before PARAMETER/APPLY admission.
   Inventory-only, cyclic config/P dependencies, wrong original configuration/
   epoch/schema/parent, later-profile substitution and candidate-selected pid
   cannot authorize it. Same R with a substituted APC proof and same proof with
   substituted R fail the complete original join; neither is a profile retry.
3. Genesis, each accepted current edge, retries after current advancement,
   initial/incomplete snapshots and loss/ABORT cases retain the full original
   history and unit association. Equal value hashes in different source contexts
   cannot collapse unit identity. No output-derived or public-success premise.
4. The source-derived result instantiates existing constructor/domain proofs;
   affected formal/axiom/mutant/compatibility and ordinary two-review gates pass
   for their exact new artifacts before any closure claim.

These criteria cover this one missing binding. They do not replace R2.3's
remaining complete initial/producer, all collections/full-state and incomplete/
ABORT obligations or certify those obligations in advance.

## 7. Decision and STOP

Approve/reject/edit this exact future-generation contract: U in the pinned initial
configuration, q in the native apply profile, the explicit numeric source R and
APC/proof-derived pid,
specified bytes/versions/bounds and history-derived common-unit continuity.
The approval request separately proposes resuming the already authorized
formal/reference R2.3 work under these bindings; it grants no runtime authority.
The legitimate production value of q remains a deployment input, not selected
by this document or by the desired arithmetic output.

**STOP after this specification and its Pending decision.** No implementation,
schema, proof, fixture or runtime change is part of this commit. No graph result
or review is fabricated, and no R2.3 closure or independent attestation is claimed.
