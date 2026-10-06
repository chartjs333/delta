# Storage Producing History Binding

**DECISION MEMO — PROPOSED alternatives; no producer or trust change adopted.**
6 October 2026. T047/T053. **R2.3 OPEN / Formal NO_GO.**

## 1. Mandate and result

Scope revision 8, human decision
`scope-decision-67a9a689e49b4cc1dcc98d70e5087373`, authorizes this one document.
Coordinator assignment `4824b8d9-2e13-4a6f-89d1-917696ff8a43` remains active;
exact ACK `scope-ack-190ebfac12e88037b509574a5f79c8b0` was confirmed by GET.
Source: `c531870eb9af25a25c70b4e7347e0e235a48933f:`
`orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-STORAGE-PRODUCER-DECISION.json`.

**The missing contract is factual, complete storage history at the original
attestation and finalization cuts.** Existing components assign responsibilities
and authenticate statements, but do not establish that history. No applicable
immutable external producer contract/evidence was supplied with this approval.
This memo does not assume that no such external implementation can exist.

The narrow decision is whether to supply that existing evidence, explicitly add
a factual-history trust assumption, or change the availability claim/model.
The latter two are semantic choices, not ordinary implementation details. None
is adopted here. Approval of storage signature bytes remains effective; general
R2.3 authorization is not being requested again.

Pins used below:

- **N:** `60c692f6e391f839829dfc64e93380db54cd507b` — inspected native/model source.
- **P:** `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13` — Snapshot Provenance Profile v1.
- **S:** `1438fa3d78ec99291475cf4660fd8c190ac01bb3` — ADR0016 §§3–7,
  subsequently approved by `scope-decision-614a7db8512f59e36720131917827d4c`.
- **E:** `a2fd17259240be0a7721512e7a12fe972587f3bf` — reviewed producer audit,
  `formal/proposals/storage-producer-checkpoint.md` and its source-hash evidence.

The current checkout is not silently substituted for N. Exact Git blob hashes
and symbol locations for this memo are in
`evidence/0017-storage-producing-history-binding-audit.json`. This is a documentary
source audit, not a new source verifier, TLC run, Lean result or production test.

## 2. Production ownership: required boundary versus implemented path

| Owner | Existing responsibility and evidence | What is still absent at N |
|---|---|---|
| Worker/contribution producer | Original ticket, commitment, manifest and shard bytes; feature003 FR-012–014, feature004 encoding | Local publication alone does not enroll a storage peer or establish remote availability |
| Enrolled storage role | Retain the original shards, attest exact IDs/lengths/retention epoch; constitution IX, feature003 FR-014; S binds its own Rs/Ks and A/Ms/SAG1 | A complete authenticated producer/observation contract for original upload, loss, corruption, repair and source cuts |
| C++ consensus core | Deterministic commitment/AC admission and per-leaf eligibility, freeze and conflict rules; `InputLedger` | `record_availability` consumes six aggregate fields. The inspected call inventory has no non-test caller beyond declaration/definition. The coarse `ACCEPT_AVAILABILITY` phase/count transition is not a physical-availability verifier |
| Native runtime | Sole consensus WAL/state/vote/artifact-state journal owner, persist-before-expose; ADR0010 and AGENTS | Persisting an input command/body hash does not establish its missing storage origin or truth |
| Java boundary | Opaque authenticated transport and assigned artifact I/O effects | `ArtifactEffectAdapter` performs local write/repair; an injected transport authenticator is not storage-history completeness or quorum/finalization logic |
| Python local artifact adapter | `FilesystemArtifactStore` verifies hash/length and publishes immutable local bytes | No remote storage identity, original retention cut or loss/finalization ordering follows from that local write |
| Profile-v1 importer / independently retained T | Pins, exact original bytes, own journal continuity, floor and finite source replay from genesis | Faithfully retaining bytes is not observing every physical storage event or certifying its truth |

This division reuses existing owners. It does not introduce a new storage
super-certificate, observer service, validator role, consensus WAL kind or
permission for Java to reconstruct consensus. Wiring these responsibilities
into a qualified producer is still work, and is not authorized by this memo.

**Who already observes completeness? No inspected component has that contract.**
Offline provisioning authenticates enrolled storage keys, not every later disk
event. A storage peer can report its local observations; the receiver sees
delivered messages. Neither fact supplies a complete cross-peer physical cut.
The validator fault threshold must not be reused as an assumed storage fault
threshold. Constitution X explicitly separates safety and conditional liveness;
storage enrollment alone is not an assumption of truthful, omniscient peers.

## 3. Original events and required cut binding

The following is a map to **unchanged** N `DeltaReduceAvailability.tla`, not a
new event schema or executable predicate. Common context remains the original
ticket/commitment, parent/round/configuration, storage epoch/registry, leaf and
full envelope length, original retention policy and S witness identities.
No coordinate-level storage or shard object is created.
The table highlights the relevant guards; the full unchanged action definitions
at N, including enable/type/unchanged clauses, remain the source of truth.

| Original event / existing action | Fact used by the existing action | Identity, ordering and retention consequence |
|---|---|---|
| Upload / `UploadArtifact` | Committed content, progress open, location not previously materialized; adds materialized and available location | Original storage/content/leaf and original write evidence must precede its use. A local write on another actor is not this event. A lost previously materialized location cannot be repaired by pretending it is a first upload |
| Attest / `AttestAvailability` | That exact location is available at this cut; commitment/progress guards; attestation not already present | Original A/Gs binds the statement and signer. Preserve the original signing/production event and all deliveries separately; a signature does not prove the location fact |
| Loss / `LoseArtifactPreFreeze`, `LoseArtifactPostFreeze` | Available location becomes unavailable; pre/post variant depends on original frozen-content state | Retain the actual event and its position relative to attestation/finalization/freeze. Loss leaves historical attestations, materialization and certificates intact |
| Corruption / `CorruptArtifact` | Available location becomes unavailable and corrupt | Bind the same original location; discovery time must not silently replace actual fault time when evaluating a physical cut |
| Repair / `RepairArtifact` | Distinct available source, unavailable target, committed content, no abort request, original repair budget not exhausted | Retain original source/target, read/write/content checks and attempt order. Adds target availability and clears target corruption; does not create a new attestation or replace an existing AC |
| Shortfall / `ObserveACShortfall` | Progress open, committed content, complete available quorum absent | Preserve original observation/cut; do not turn a timeout into an authenticated proof that all remote physical copies are absent |
| Finalize / `FinalizeAvailability` | Progress open, no existing certificate, **per-leaf available attesters meet threshold at this cut** | Original D/ac and its exact per-leaf witnesses plus the actual finalization/admission event. Candidate bytes are not a finalized certificate. Preserve native commit/exposure order and original witness identities |
| Close/freeze and late evidence / existing ticket/freeze rules, `RejectLateAvailability` | InputClosed and original close/progress/late bounds | Preserve original close/config authority, frozen tuples and downstream lineage. Late evidence does not rewrite the cut or add a late attester to the accepted witness |

In the model, `ArtifactLocation` is `(storage,content,shard)`, an attestation is
`(storage,ticket,content,shard)`, and an abstract AC is `(ticket,content)`.
These are not wire encodings or replacements for S's original a/gs/D/ac.
S permits different signer subsets for different leaves. No common-q or
union-only shortcut is introduced.

Profile P §4 already requires an ordered original source prefix and backward
dependencies. Its source index identifies an original actor/action, original
event/record reference and exact inputs. It is an index, not an authority that
may invent events. For this binding the order must justify which original
location changes precede each attestation/finalization/close cut. Receiver
arrival order, a newly assigned timestamp, a sorted list or a candidate state's
successful public projection cannot manufacture that order. An unresolved race
must remain unresolved and fail source verification, not be sorted in its favor.

There is no complete original storage record format at N to point those index
entries at. This memo does not fill that absence with invented signed fields,
new storage journals or consensus sequence numbers. It also does not require
remote validators to disclose private vote journals. Original delivery
multiplicity, original QC/WAL identities and source inventories remain intact.

## 4. The smallest distinction the source must resolve

Use an original configured storage threshold of 3 and one original committed
leaf; all other leaves have complete coverage. Assume the unchanged other
guards (progress open, faults/actions enabled, content not frozen, no AC yet).
Upload and attest from storage-1, storage-2, storage-3. Then compare:

| Cut | Historical attesters | Currently available attesters | Existing finalization guard |
|---|---|---|---|
| A: before loss | 3 | 3 | Enabled |
| B: `LoseArtifactPreFreeze(storage-3,content,leaf)` before finalization | Same 3 | 2 | Disabled |

The same authentic statement bytes, candidate D/ac and six-field ledger input
can occur in both descriptions. `HasAttestationCoverage` remains true at B;
`HasCompleteAvailability` does not. The distinction is one missing location
change and its order, not a signature algorithm defect.

This is evaluation of existing guards from E, not a production-reachable attack,
a verified complete Profile-v1 snapshot counterexample, or an impossibility
theorem for every conceivable producer. A model action is not independent
evidence that the corresponding native producer executed.

**Opposite order:** finalize legally at A, then lose that shard. The accepted
AC and any later frozen ISC stay in lineage. N's `AvailabilityCertificateSound`
and `AvailabilityBeforeISC` require historical attestation coverage, not eternal
physical availability. `RepairPreservesCertifiedLineage` retains the original
commitment/certificate associations. Repair, omission before freeze or the
existing abort behavior must not be replaced with deletion of accepted history.

## 5. What authentication can and cannot close

Three different facts must remain separate:

1. **Local I/O completed:** the named adapter wrote/read verified bytes at its
   local observation. This does not assert all storage locations at a later cut.
2. **An enrolled peer signed A:** Rs/Ks and SAG1 authenticate that exact statement.
   A's retention epoch is the original obligation, not proof it was fulfilled.
3. **The required locations were available at the original cut:** this is the
   stronger fact needed by `AttestAvailability` and `FinalizeAvailability`.

A signed log/hash chain can authenticate records and ordering within its
supplied prefix. Without an independent completeness/truth contract it does
not prove that an unreported loss did not happen, that a later prefix was not
withheld, or that a signed assertion was physically true. Retaining those logs
on faithful T does not add that contract. ApplyQC authority certifies its own
protocol object; it must not be treated as independent proof that every upstream
physical storage event occurred lawfully—that is part of the source obligation.

A fresh read/probe shows bytes at its observation. With modeled loss between
that observation and finalization, it does not alone prove the latter cut.
A lock/lease only solves this if its **physical fault and ordering guarantees**
are separately established; an ordinary logical lock or signed retention promise
does not prevent disk corruption. No such guarantee is present in the pins.
No new timing, synchrony, lease, honesty or globally complete observer assumption
is hidden in the word "producer" here.

## 6. Exact decision alternatives — none selected

**E — supply an existing contract/evidence.** Provide an immutable applicable
native producer and original event evidence, including the independent basis
for factual correctness, completeness and the cuts in §3. Review against the
already frozen profile/model; do not define validity as passing R2. If it really
supplies this existing obligation without changing those contracts, no semantic
amendment is needed. A source pointer alone is not a proof of sufficiency.

**F — preserve the physical model, add an explicit factual-history assumption.**
The minimum *additional* trust claim would be:

> For the original storage locations used in the source bundle, the independently
> designated observation boundary truthfully records every materialization,
> attestation-producing observation, physical loss, corruption and repair relevant
> to each original attestation/finalization cut; its bound order/cut contains no
> omitted or fabricated location change. Supplied location facts correspond to
> actual retrievability of the original committed bytes at those cuts, not merely
> delivered claims. This guarantee is independent of certificate acceptance,
> public state construction and the success of R2.

This is a **new assumption**, not a discovered capability of T, Rs or ApplyQC.
It does not contain the refinement conclusion, but its truth is not discharged
by hashing/signing the history. Extending T's responsibility to certify this
would expand Profile v1's trust model. No concrete observer satisfying it is
identified in the supplied production evidence. Adopting F only as an external
premise permits at most a **conditional** source/refinement claim; it does not
establish production history legality or close the selected production GO.
It must never be packaged as a hidden axiom or a callback returning true.

**O — change the claim to authenticated/observed availability.** Deliberately
separate what the protocol has certified/observed from actual physical
availability; then specify the conditions under which that evidence licenses
finalization and what retrieval failures imply. Merely replacing
`HasCompleteAvailability` by `HasAttestationCoverage` would enable the cut-B
finalization forbidden today. Therefore O is a protocol/model decision, not
renaming an abstraction or adding a codec. This memo does **not** propose that
single replacement as a finished safe protocol. Exact new guards, storage fault
assumptions and safety/liveness claims would need a separate approved decision
before any model or implementation work.

**Recommendation:** retain STOP rather than silently select F or O. E is the
only route compatible with every currently frozen premise. If E cannot be
supplied, the operator must choose whether to change the trust/qualification
claim (F) or the protocol/model claim (O). Neither is covered by the byte-level
approval or by general R2.3 permission. This is the existing source-origin
obligation, not a new DoD item.

## 7. Compatibility and qualification consequences

| Surface | E: genuinely sufficient existing evidence | F: additional factual-history trust | O: changed observed/certified semantics |
|---|---|---|---|
| Rs/Ks, A/Ms/SAG1, D/ac; original storage IDs and retention policy | Reuse exact approved objects; no relabel | No byte change is inherently needed, but bytes cannot discharge the new trust claim | No byte change is assumed sufficient; depends on the later exact semantics; never reinterpret old objects under the new claim |
| Native producer/source index | Qualify actual original rules, cuts and complete inventory | Producer binding still needed; qualify trust boundary separately or explicitly leave theorem conditional | New producer/model correspondence needed; source history may not be normalized to hide physical faults |
| Production `Init/Next` | Unchanged only if evidence meets current guards | Physical action definitions can remain unchanged; additional environment assumption changes admitted/qualified histories | `AvailabilityNext` action/guard/state interpretation and its composition into `Next` need requalification; `Init` impact depends on exact state split |
| QC/WAL/signers and delivery counts | Preserve originals | Preserve originals; no trust-metadata event becomes a consensus vote/slot | No migration/relabel; any changed downstream identity/context requires separate compatibility treatment |
| TLA results | Existing pins remain historical evidence; future source refinement must still be proved | Old proofs do not prove the new environment assumption or unrestricted production refinement | Requalify availability invariants, finalization, freeze/lineage, repair/abort and dependent safety/liveness models/mutants |
| Lean / R2 | Existing R2.1/R2.2 retained for their original domain; R2.3 source composition remains work | Explicit assumption would change the theorem/domain claim; cannot count it as proved R2.3 production closure | Affected public-state validity/refinement constructors and dependent theorems must be revisited; no automatic reuse for changed guards |
| Article / Formal GO claim | Physical availability at lawful original cut, subject to original fault model | "Refines given a truthful complete physical history" is weaker than verified production provenance | Certified/observed availability replaces the stronger physical-cut statement; consequences cannot be hidden in a footnote |
| Liveness | Original conditional liveness, not a new timing guarantee | Complete evidence may be unavailable; no progress guarantee follows from assuming its truth | Must be separately established; authenticated statements alone do not guarantee retrieval |

No old proof/result becomes false merely because this memo exists. None proves
the missing binding. No new source domain/caps, production TLA, Lean proof,
schema, runtime, certificate bytes or semantics ID is changed. R2.1/R2.2 are not
reopened; full R3 and `DeltaReduce.nativeArithmeticRecoveryRefines` do not start.

## 8. Checkpoint

The document fulfills scope8; the production blocker remains
**MISSING_STORAGE_PRODUCING_HISTORY_BINDING**. The finite residual is the
source-origin/cut obligation above, not a request for another collection of
proof layers. Source replay, signatures and bounds are not reported closed.

No honest integration-hour estimate can be narrowed before E is supplied or
the explicit trust/model choice is made. Earlier estimates are not execution
budgets and do not imply an ETA for GO.

**STOP after this memo.** An unchanged approval of the document does not select
F, O or an unknown observer. Record the exact next semantic choice through the
existing sprint's Pending decisions; retain the current assignment/history and
all normal reviewer gates. No RESUME outcome is sent merely to make this
document advance the graph. No process review is represented as independent
Formal GO attestation.
