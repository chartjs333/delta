# EC durable binding v1 — isolated feature000 selection

T047/T053 / ISC-S16-D01 / ISC-S16-CONTINUITY. 10 October 2026.
Selected under scope 18, not a production storage deployment or Formal GO.
R2.3 remains OPEN. Full R3 is excluded.

## Authority and immutable inputs

Official operator edit `scope-decision-351641e848148e36894d472a92df4424`
applied `scope-human-b45e7c9e11db84448ad3368973788add`, revision 18, to
assignment `93868961-a78f-41db-93ec-06d4d6d3167d`. It expressly supersedes
the specification-only STOP for minimal isolated formal/reference persistence
bindings, including this EC binding. It also permits implementation, proof,
qualification and technical correction within the retained boundaries. The
original request at `9690a05296fb129012d6d03f3636abb2c365a09b` is not the
operator-edited effective instruction. The evidence file beside this document
records the official decision/context and source/core hash checks.

Inputs remain:

- Selected EC-SOURCE-STEP-v1 at `f1a9963eabb5cb61f936ad1ad41f45e870acd43e`,
  `orchestration/sprints/isc-s16-continuous/handoffs/ISC-S16-FIRST-EC-PRODUCER-SOURCE-v1.md`.
- Its qualified computation at `47d75279d23441f5c10ed523bdea172b257e8bef`,
  `formal/proposals/b-family-transfer/ProfileEcFinalization.lean` and
  `formal/reference/profile_source/ec_finalization.py`, with scoped evidence
  in `formal/proposals/evidence/profile-ec-finalization/`.
- At that same worker commit, `ProfileOrigin.lean`, `ProfileImport.lean`,
  `ProfileSourceIndex.lean`, `formal/reference/profile_source/metadata.py`,
  `source_prefix.py` and `journals.py`: the existing independent Profile-v1
  bootstrap/custody, original index, floor, artifact and journal contracts.
- Existing native N `60c692f6e391f839829dfc64e93380db54cd507b` and ISC W1
  P `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` remain immutable. Neither is
  retrospectively claimed to implement this EC binding.

## Minimal selection and compatibility

Use one local **formal/reference companion journal**, journal identifier
`PROFILE-EC-COMMIT-V1`, under the already selected trusted T custody and
single-writer/barrier assumptions. This is not a consensus message, QC,
signature, production WAL kind, W1 extension, physical-availability observer,
trust anchor, or additional certificate authority. It records the computed
EC update; it does not authorize that update merely by existing.

Rejected alternatives are reinterpretation of legacy kind 1/2, treating EC as
ISC-only kind 3, or a supplied durable flag. They either change excluded legacy
semantics or do not provide the missing binding. A second signed certificate
would introduce unnecessary authority. Inline copies of every policy/history
would duplicate already retained original artifacts and distort their budgets.

The companion binds complete bytes by hashes recomputed from the independently
interpreted original source. Hash equality alone is never proof of lawful
origin or a completed barrier. No new artifact per hashed field is required:
the original source index resolves the original bytes, and P1 is computed.
Original source occurrences, descriptor bytes, ordering, duplicates, signers,
E/e, seed identity, native slots `s` and vote ordinals `V_a(s)` stay unchanged.
Companion ordinals are a separate namespace, never substituted for s or V.

No old object is migrated, re-signed, relabeled or accepted as if this journal
had existed. New formal/reference generation pins must be requalified; no
concrete production `sigma_next` is assigned. Production Init/Next and storage
adapters are unchanged. This selection is not a measured filesystem guarantee.

## Exact record and source binding

Reuse Profile-v1 canonical ASCII JSON: sorted member names, no whitespace,
BOM/newline, duplicate names, escapes, unknown members, numeric JSON or null;
integers are canonical unsigned decimal strings. Let H(x) be the existing
raw-byte identifier `sha256:` plus 64 lowercase hex digits. Protocol IDs e,
seed IDs, ISC b/c are not interchangeable with H(x).

Each body has exactly these members:

| Member | Value |
|---|---|
| `type_name`, `schema_version` | `EC_COMMIT`, `1` |
| `profile_id` | `snapshot-provenance-linux-single-epoch-v1` |
| `bootstrap_id` | existing independently provisioned Profile BOOTSTRAP document ID |
| `actor_id` | enrolled original actor; same as the original EC event |
| `ordinal` | 1-based contiguous companion ordinal |
| `previous_record_id` | `GENESIS` at ordinal 1, otherwise preceding record ID |
| `event_index` | original EC event index n, not a WAL slot; n = original inclusive cut + 1 |
| `source_prefix_id` | prefix digest defined below for ALL events before n |
| `event_raw_id` | H(exact canonical original event descriptor at n) |
| `prior_policy_raw_id`, `next_policy_raw_id` | H(full original P0), H(full computed P1) |
| `round_state_raw_id` | H(full original S0), unchanged by this EC policy step |
| `certificate_raw_id`, `seed_raw_id` | H(exact computed E), H(exact original seed transcript bytes) |
| `journal_prefix_id` | digest below of the complete original journal-prefix inventory at this cut |

The profile_id is the exact pinned codec literal, not an alternate new profile.

Record ID is `sha256:` + hex(SHA256(ASCII
`deltareduce.profile.ec-commit.record.v1` || NUL || body)). A frame is
u32BE(body byte length) || body || raw32(record digest). This reuses the Profile
local-log framing primitive with a distinct dispatch/domain; it is not a
TRUST_RECORD/INIT/ACTIVATE/ANCHOR and cannot advance the trusted floor.

For canonical descriptor D_i of each original source event, prefix digest is
`sha256:` + hex(SHA256(ASCII `deltareduce.profile.ec-commit.source.v1` || NUL
|| ASCII(bootstrap_id) || u64BE(n)
|| concatenation over i=0..n-1 of [u64BE(i)||u32BE(len(D_i))||D_i])).
The enclosing source index resolves every descriptor reference to its exact
original bytes and checks the complete inventory. The event at n references
E and its six original ordered inputs from EC-SOURCE-STEP-v1. It does not
reference this companion record, so there is no hash cycle.

For the complete ordered original journal cuts J at the predecessor (including
the earlier companion prefix when present), journal digest is `sha256:` +
hex(SHA256(ASCII `deltareduce.profile.ec-commit.journals.v1` || NUL ||
canonicalJSON(J))). Reuse existing actor/journal/ref/count/first/last cut fields
and ordering. Decode and verify the referenced full original prefixes; the
digest is not a replacement for them. The new frame never hashes a successor
source index or its own containing journal. The enclosing successor inventory
retains the frame normally; preceding source/journal cuts are acyclic.

Validate by replaying the independently pinned native producing prefix to n,
including CONFIG, native phase/time, original authenticated admission, full
delivery inventory and norm/seed prerequisites. Then invoke the existing full
EC computation and six-ref/dependency checks. Recompute EVERY record field
from that result and the complete original cut; compare exact canonical body
and frame. Supplied P1, public success, `durable=true`, successful metadata
parsing or an arbitrary well-typed candidate cannot supply the source fold.

Bounds remain the already selected Profile budgets and native per-object
bounds. The fixed-size hash record avoids a new source-event/delivery cap;
payload length is checked against the existing 4 MiB control bound and actual
total source bytes/refs/journal records against existing aggregate budgets.
Count the companion bytes/records, never delete an original event to make it
fit. Exhaustion/incomplete evidence remains explicitly represented and cannot
be promoted to a committed EC. Qualification must cover boundary accounting;
no claim is made that adding bytes to an already full legacy inventory works,
or that bounds alone prove all-action totality. A proof failure is not repaired
by narrowing the approved source domain.

## Transition, failures and recovery

1. Validate and compute from the original full prefix. No state/effect changes.
   Serialize exact frame and retain all required original source bytes.
2. Append to the companion at its next original ordinal. Native WAL remains
   byte-for-byte unchanged. One in-flight candidate per single writer.
3. Complete the existing T durability barrier over the frame and every source
   artifact required to interpret it (including namespace persistence when a
   new object is created). A frame digest is not evidence of this barrier.
4. Commit the computed P1 in the local formal/reference state. Full S0 and
   unrelated lineage are preserved. Only then may the exact E be exposed or
   used as a finalized prerequisite. This does not loosen seed-release rules.

Crash before append leaves no new durable update. An unacknowledged append or
failed barrier may leave absent, complete or incomplete bytes; do not assume
absence. A complete surviving frame is only a recovery candidate until the
full original prefix is verified and a recovery barrier succeeds. Recovery
then commits the same P1 before exposing the same E. If the frame was already
durable/committed, replay derives that identical update without another frame,
vote, effect identity, physical slot or companion ordinal. No liveness claim
promises progress through unavailable storage or missing source artifacts.

A torn/unknown/conflicting frame or missing required original source blocks
activation/exposure. Preserve bytes and provenance; do not truncate, reset,
replace a missing journal by empty, manufacture a successful history, or fall
back below the trusted floor. A complete durable prefix can be inspected while
the suffix remains blocked; this is not READY or permission to expose through
the unresolved suffix. Ambiguous outcomes are recovered/verified before retry.

Re-observation of an existing original finalization recomputes its original
cut and exact E/seed, checks they remain retained, and stutters the FULL current
state (including later ABORT/downstream lineage). It never recomputes quorum
from later arrivals. A different first-finalization body/seed/E for the same
original b conflicts, fails closed before append, and creates no partial write.
Two different arrival cuts may produce distinct signer-dependent e on different
nodes as already selected; this contract does not assert witness convergence.

## Finite implementation and qualification handoff

Continue through the normal RESUME_FORMAL/two-review route. Minimum worker
files: a `profile_source/ec_durability.py` codec/interpreter and focused tests;
`ProfileEcDurability.lean` composed with `ProfileEcFinalization`, original
source/journal modules; scoped qualifier/vectors/evidence; source-fold wiring
where required. Names can be adjusted within the delegated technical scope.
No production C++/ABI/Java/schema adapter edits are authorized.

Acceptance requires exact codec/framing round trips and malformed rejection;
field substitution/cut mismatch detection; every original delivery and physical
journal sequence retained; deterministic same-original retry; no exposure
before successful barrier and commit; every crash cut including complete
unacknowledged/torn frames; all-cut EC computation and full P0/P1 binding;
general Lean preservation/composition and axiom audit; relevant mutants,
reference and formal gates. Synthetic examples remain synthetic. Receipt
hashes must bind current sources and failing gates remain FAIL/NO_GO.

The enclosing lawful-source fold and complete public relation still have to be
proved and reviewed. This contract does not close R2.3 by stipulating them.
Proceed with ordinary delegated R2.3 composition after this binding; do not
request another human choice for the same class of isolated technical details.
The named recovery theorem follows substantive reviewed R2.3 closure only.
Same-executor process reviews are not independent Formal GO attestations.
