# Authenticated availability contract v1

**PROPOSED for semantic approval. Specification only.** 7 October 2026.
T047/T053. **R2.3 OPEN / Formal NO_GO.**

Scope10 selects direction O and authorizes this single contract, followed by
STOP and a Pending decision. It does not approve these guards or authorize
model, proof, schema or runtime changes. F is forbidden. This proposal changes
the availability claim explicitly; it does not claim to prove the old physical
availability condition from signatures.

## 1. Selected contract and exact change in claim

An AC certifies **a complete, authenticated, context-bound set of storage
statements accepted at the original protocol cut**. It does not certify that
a quorum of remote disks actually held those bytes at that instant. A data-using
operation independently requires the exact committed input bytes and successful
verification/recomputation at its own admission. Neither AC nor ISC supplies
those bytes by implication.

The selected combination is therefore:

1. strict ADR0016 statement authentication and per-leaf AC witness verification;
2. deterministic close over accepted ACs in the original authoritative protocol
   prefix, without a hidden physical-availability oracle;
3. exact byte consumption before each data-dependent computation/first vote;
4. identity-preserving repair, existing deadlines and certified abort on failure
   to complete; immutable finalized lineage throughout.

This deliberately admits certification in a case forbidden by the old physical
guard: valid statements were accepted, but a location was lost before AC
finalization or close. It does **not** admit computing with absent/wrong bytes,
fabricating votes, replacing members, extending deadlines, or advancing current
without ApplyQC. If that narrower AC claim is unacceptable, reject this proposal;
there is no claim that O preserves the former physical-cut theorem.

## 2. Authority and unchanged objects

Human decision `scope-decision-c78a662f4607e470ed1a39d7d4238821` applied scope10
to coordinator assignment `4824b8d9-2e13-4a6f-89d1-917696ff8a43`.
Exact ACK `scope-ack-eae23110c6f1a397a5af1a3988b9c0d2` is role-GET confirmed.
The effective instruction expressly selects O despite the historical menu
appended below it. No F permission follows from that menu.

Immutable references used here:

- **N** `60c692f6e391f839829dfc64e93380db54cd507b`: native ownership and original
  `DeltaReduceAvailability.tla` / `DeltaReduceCertificates.tla` guards.
- **P** `26eb02d0632435c9aa0d8ef44eb496b6fa73dd13`:
  `docs/adr/0013-snapshot-provenance-profile-v1.md`, independent bootstrap,
  original finite source prefix, trusted floor and journal continuity.
- **S** `1438fa3d78ec99291475cf4660fd8c190ac01bb3`:
  `docs/adr/0016-storage-availability-source-binding-v1.md` §§3–7, bytes/keys
  approved by `scope-decision-614a7db8512f59e36720131917827d4c`.
- **C** `4555479c65161a901dd6582dea80ebd2521bb025`: current coordinator source
  for pending arithmetic/public-state/Lean dependencies. C is not a production
  deployment pin. Availability and certificate module bytes equal N; arithmetic,
  type and public-state modules must not be silently substituted for N.
- E audit `08e86bad8be9b5af3c61e29a2e5f77a4e970374b` and complete post-disk-full
  recheck `3ee3db8cd7ea9af944f41e34c0fc609ad3f250ce`: no applicable original
  physical-history contract was found in that recorded corpus. This proposal
  does not reopen that search or deny the earlier disk interruption.

Reuse S's independent initial-config → Rs/Ks binding, exact A/Ms/SAG1/D/ac,
storage IDs, retention epoch, committed leaf IDs and full envelope lengths.
Reuse the existing validator registry/quorums, full signed parent/context,
ISC `b` consensus-body and `c` witness distinction, physical WAL slot `s` and
public vote rank `V_a(s)`. No new root, observer service, availability QC type,
key substitution, wire field, signing domain or consensus WAL kind is proposed.

S's §§6–7 physical-source requirement is **not** silently deemed satisfied:
for a separately approved successor generation it would be replaced exactly
by the protocol-observation and byte-consumption obligations below. S's byte,
key, per-leaf, duplicate, identity and retention-binding rules stay intact.

## 3. Domain and observations

Keep the enrolled fixed epoch, independently provisioned bootstrap, one native
owner, faithful/nonrollback T, original finite source bundle and the existing
resource bounds of Profile v1. No enrollment, epoch, network-bootstrap,
trusted-volume-compromise or backup-format extension is proposed.

For this specification, `p` denotes the exact original prefix before a native
event, as reconstructed from P's independently retained source index, raw inputs
and own journals. It is **not** a wall-clock timestamp, a receiver-selected
ordering, a sorted set of convenient messages or a successful public projection.
The verifier must replay the independently specified native producer/admission
rules from pinned genesis. O does not make those rules already implemented.

There are two kinds of relevant observation, using existing source-index
actor/event references rather than new protocol identities:

- **Statement delivery/admission:** exact original Gs bytes delivered to the
  relevant producer before its admission event; role/signature/context checks
  are recomputed. Repeated deliveries retain their original events and count
  once for the same `(leaf_id,storage_id)` witness pair.
- **Data consumption:** the exact original byte values opened for an operation,
  their committed manifest/leaf IDs, lengths and dependency links to that
  operation. Hash, canonical decoding, shape and arithmetic are recomputed from
  those values. A recorded `success=true`, path, old signature, digest without
  preimage or peer assertion is insufficient.

P's trusted custody authenticates the original local records/bytes and their
association, as before; it does not observe every remote disk event. Missing
required local records still reject the source. Undelivered remote messages are
not invented; hidden remote private WAL is not required. All retained deliveries,
local failures, alternate witnesses and downstream lineage remain in the source
inventory. Loss/corruption that no actor observed is **permitted environment
behavior**, not a reason to fabricate an original observation.

## 4. Exact AC and close guards

The following are proposed mathematical specifications, not installed predicates.
Every ordinary protocol step below also requires the existing composed
`OrdinaryProgressOpen`: `phase = ACTIVE`, logical time strictly below the
original hard deadline, and no abort request. Leaf-action shorthand never
bypasses that outer gate; retry/transport/failure actions retain their own
existing conditions.

`AuthenticatedWitness(p,D)` means all of these checks succeed:

1. P's independent origin/config pins and S's storage authority resolve; D's
   semantics generation, original round/height/parent/config, storage registry,
   storage epoch, retention epoch and threshold equal that policy exactly.
2. The original ticket/lease/commitment and complete manifest/shard bindings
   validate. Required leaves and full envelope lengths come from that commitment,
   not from D's observed subset. Their original source dependencies precede D.
3. D and every referenced Gs use S's exact canonical decoding, domains and strict
   Ed25519 checks with the enrolled **storage** key. Unknown/duplicate JSON
   members, wrong role/key/context/epoch, wrong leaf/length and trailing bytes
   reject. Every referenced Gs is present in the original accepted input prefix;
   a signature in a later bundle cannot be moved before the original event.
4. D retains its actual sorted `(leaf_id,storage_id)` witness list. No duplicate
   pair, extra/missing leaf, substitution or rewritten witness is allowed. For
   every required leaf, distinct signers in that leaf's witness are at least the
   independently configured storage threshold. Different leaves may have
   different signer subsets. Union-wide counts and the six aggregate native
   AvailabilityProof fields alone are insufficient.
5. The original retention policy is resolved, not inferred from an epoch label
   or clock. Exact policy/epoch binding proves the **obligation being asserted**,
   not its physical fulfillment. Missing policy is rejection. This contract adds
   no lease duration, promise of fault-free disks or expiry extension.

`FinalizeAvailability_O(p,D)` requires `AuthenticatedWitness(p,D)`, finalized
matching RoundConfig, original accepted commitment, enabled availability action,
`CertificateProgressOpen`, and the existing first-admission/conflict checks.
It admits the exact D/ac once and adds its ticket to the certified-ticket view.
Exact retry returns the original identity without a new vote or slot. Another
valid witness for the same already accepted ticket/commitment does not replace
the original AC; it is retained as alternate/conflict evidence. No independent
replica receipt can elect a global arrival-order winner: the original native
admission and BFT close/ISC rules remain the ordering authority.

**There is no conjunct asserting remote physical presence at finalization.**
An enrolled storage signer may lie or cease responding. Authentication proves
who made the statement; all storage peers may be faulty for the safety claim.
An honest storage producer checks its own exact bytes before attesting, but the
accepting protocol does not assume the signer was honest or that those bytes
remain present. This is why a new omniscient producer is unnecessary for O.

At the existing canonical close cut, define:

`Eligible_O(p) = { original accepted AC entries for RequiredTickets in p }`.

Each entry must already have passed the guard above in the same round/context;
the exact retained witness remains resolvable. `CloseInput` otherwise retains its
existing finalized-config, progress, canonical ordering and uniqueness rules:

- `OMIT_UNAVAILABLE` omits tickets lacking an accepted complete authenticated AC
  at that cut, and includes **all** such accepted AC entries allowed by the
  original policy. Here the old label means *missing certified input evidence*;
  it no longer means a measured quorum of live disks. This is an explicit
  successor-generation semantic change, not a relabel of old objects.
- `ABORT_ON_INCOMPLETE` requires an accepted complete AC for every original
  required ticket; otherwise only the existing incomplete-input abort path is
  enabled. Its existing quorum/deadline rules are unchanged.

A local retrieval failure never silently removes a certified ticket from this
set, even before close. Validators cannot each derive different ISC membership
from their local read outcome. At/after close, late valid evidence is retained
under existing late-evidence rules but changes neither the body nor membership.
VoteISC, delivered quorum, FinalizeISC and seed-after-durable-ISC rules remain.

## 5. Exact byte use and retrieval failure

For a data-using operation `op`, derive `RequiredBytes(op)` from its original
authenticated ticket, immutable schema/manifest, certified parents and existing
arithmetic algorithm. It is never inferred from files that happened to arrive.

`UsableBytes(op)` holds only when **every** member resolves to the exact original
bytes, expected length/content ID, canonical encoding, schema/range and context,
and all required checked computations on these very values succeed. An immutable
validated buffer may be reused while owned by the operation. A discarded buffer,
restart, path replacement or newly opened file requires validation again. A
previous successful read is not a standing remote availability flag.

Required application points are finite and tied to existing operations:

| Operation | Required verification before an honest first vote/result |
|---|---|
| EC eligibility/norm computation | Exact original ISC input bytes needed by the normative norm/eligibility computation; missing data cannot be reclassified as statistical exclusion |
| APC plan validation | Exact certified parents, membership and coefficient/bound inputs needed by the existing deterministic plan checks |
| PARAMETER | Complete original required input Q/schema/scale/assignment values and full checked ordered result; current-parent check repeated at persistence |
| AggregateRoot | Complete original parameter QC/body table with existing exact domain×shard coverage and matching parents; no requirement to invent a new raw-Q copy at a metadata-only step |
| APPLY/current preparation | Exact required aggregate/domain values, current model/optimizer and profiles; whole-body recomputation, output bounds and certified current CAS as already required |

An AC claim or an injected true callback never substitutes for any row. The
pending arithmetic amendment already requires complete bytes and recomputation;
O neither claims that guard implemented everywhere nor waives its qualification.
Finite TLA constant inputs alone cannot serve as evidence that a native actor
actually resolved its required bytes. The future O model must expose the relevant
operation-input/observation guard alongside its existing arithmetic checks.

Retrieval has three outcomes: exact verified bytes; received bytes failing
verification; or no bytes obtained by the configured attempt/deadline. The latter
two disable the data-dependent operation. A timeout is a local failure to obtain
bytes, **not** proof that every remote replica is absent. Wrong bytes never become
a new committed content ID. The round may retry/repair only under the original
content-specific attempt and immutable deadline budgets. Duplicate responses do
not add attempts or signing power; attempts are accounted by the existing native
single-writer ordering, not by counting packets. No new cap is chosen here.

Repair verifies original bytes and atomically restores the same content identity
at its target. It certifies neither perpetual target retention nor the source's
physical state at an earlier/later cut. No AC/ISC, signer or QC is regenerated by
repair. Local inability to proceed leaves current unchanged. Soft view change,
the existing canonical failure/abort proposal and hard-deadline rules apply;
no local timeout/error or AC shortfall manufactures AbortQC. Once the existing
abort condition is certified/enabled, non-abort progress is fenced. `ABORTED`
requires its matching delivered validator quorum; without it the system stays
BLOCKED. O adds no new reason code, failure terminal or deadline extension.

Exact durable vote replay does not demand a fresh read of data merely to resend
the **already legal** original vote. It must restore and validate its original
admission/receipt/sequence and cannot become a first vote with a stale parent.
Corrupt, incomplete or ambiguous recovery remains non-READY. Snapshot/current
recovery still requires P's exact anchor/floor and original journals; O does not
implement or bypass that procedure.

## 6. Loss ordering and claimed behavior

| History | Proposed behavior |
|---|---|
| Missing/invalid statement or missing per-leaf quorum | No accepted AC; close omits or follows incomplete-input abort policy |
| Enrolled peers sign without retaining bytes | Statements may authenticate; AC may form if all witness guards hold. No claim of physical presence follows; data-dependent work cannot succeed without its actual exact inputs |
| Valid statements, then physical loss before AC finalization | AC may finalize. This is the intentional difference from the old guard; it grants no arithmetic shortcut |
| Accepted AC, then loss before close | Entry remains in the certified close set. No discretionary omission; unavailable required input blocks later data use and triggers only existing repair/deadline/abort paths |
| Loss after close but before ISC finalization | Frozen body remains exact; quorum/durability still govern ISC. A later data-use failure cannot rewrite that body |
| Lawful AC/ISC, then loss after finalization | Original AC/ISC and all downstream lineage remain; exact-ID repair or certified abort/blocking, without certificate deletion |
| Old read succeeded, then copy lost before use | Reuse only an actually retained validated buffer; otherwise resolve/validate again. The old read receipt is insufficient |
| Hidden loss or false storage statement with no local observation | Permitted physical behavior; no fabricated event enters source replay and no absence-of-fault conclusion follows |
| Crash after durable vote before exposure | Original recovery/replay ordering and identities; no second vote, receipt or WAL sequence |

At the old threshold-3 example, losing storage-3 before finalization leaves
three valid statements but only two available attesters. O allows the AC claim
while the old `HasCompleteAvailability` forbids it. If the consumer can still
obtain each exact required input from any permitted original source, its checked
computation may proceed; otherwise it cannot. This is a proposed behavior table,
not a new executed trace, production attack or formal result.

## 7. State, Init and Next changes required by this proposal

O is **SEMANTIC**, not refinement-only against the old public model.
It requires a separately approved successor formal generation. This ADR changes
none of the following files and assigns no concrete semantics ID.

The public protocol state must distinguish authenticated statement/witness
inventory, accepted ACs, and actor-local observed operation inputs/failures.
The inventories retain original IDs and event multiplicity through the existing
lossless source mapping; they do not create coordinate-level objects. A byte-use
observation consists of original actor/event, original input references and the
derived validation outcome. No independent signed observation certificate is
introduced. A success outcome without its actual inputs is unrepresentable as
successful data use.

Physical `materializedArtifacts`, `availableArtifacts` and `corruptArtifacts`
remain **environment** state for fault exploration, allowed to vary independently
of signed statements. They are not copied from a supplied `available=true` flag
into a proved native state. The revised refinement claim covers the complete O
protocol/observed state and retains every reported native event/field, not a
reconstruction of every unobserved physical location. Two histories differing
only by an unobserved physical loss can have the same protocol observation;
two different original witnesses, votes or deliveries cannot be collapsed.
This is an explicit change of claimed abstraction, not a restricted no-loss
source domain or an asserted injective map to the old full physical state.

The composed fault model must still contain unconstrained permitted loss,
corruption, failed reads, dishonest storage statements, partitions and crashes.
An environment projection is not permission to delete the fault actions or
check safety only on successful observations. Physical effects have local
observable consequences when a read/repair occurs, rather than silently setting
replicated certificate state. All formerly recorded physical-event evidence is
retained as evidence; it is not rewritten into a successful observation.

| Existing module or action | Exact prospective delta |
|---|---|
| `DeltaReduceTypes.tla`, `AvailabilityInit/TypeOK`, `ProtocolVariables` | Separate protocol observations from environment facts; empty statement/read inventories at real Init; typed original actor/event/input association and accepted AC witness identity. Requalify complete state preimages; do not reuse the old 64-field meaning under an old hash |
| `AttestAvailability` | Distinguish producer assertion from recipient authentication. Honest producer may check its local bytes; safety exploration admits authenticated but false claims by enrolled storage identities. No global physical-presence guard on acceptance and no assumed bound on dishonest storage peers |
| `FinalizeAvailability` | Replace physical available-attester guard with the full §4 authenticated original-prefix witness guard; preserve native first-admission/conflict/late rules and exact D |
| `ObserveACShortfall` | Evidence/quorum shortfall in the accepted protocol prefix, not global physical absence. Local failed fetch stays a local observation; it cannot certify an abort on its own |
| `CanonicalEligibleEntries`, `RequiredInputComplete`, `CloseInput`, `RequestIncompleteInputAbort` | Use §4 accepted-AC completeness. This is the second physical-oracle dependency, in addition to finalization |
| `UploadArtifact`, pre/post-freeze loss, `CorruptArtifact`, `RepairArtifact` | Retain physical fault/transfer semantics in the environment and exact observed outcomes at the protocol boundary. Repair consumes verified original bytes/budget and preserves lineage; no complete global history premise |
| EC/APC and `ProposeParameterResult`/`VoteParameter`, `ComputeApplyCandidate`/`VoteApply` | Preserve existing parent/round/arith/current guards; materialize §5 data-use preconditions in the successor model so immutable fixture values cannot bypass failed retrieval |
| `VoteISC`, send/deliver, `FinalizeISC`, `GenerateSeed` | Requalify against changed admitted close sets, preserving quorum, `b`/`c`, exact signers, durable sequence and seed ordering |
| `SoftTimeout`, `VoteHardAbort`, `HardAbort`, crash/restart/recovery | Same authority, body/lineage, deadlines and terminal rules; extend state framing for observations, requalify failure paths and retain nonempty lineage |
| `DeltaReduce.Init/Next`, refinement/public-state module, liveness harnesses | Compose the changed observation/environment actions and state; no assertion that unchanged production Init/Next already represents O. Positive liveness must start at real empty Init and traverse data acquisition, without abort as progress |

## 8. Safety, liveness and theorem claims

Safety continues to require the existing cryptographic, honest-validator
durability and at-most-f Byzantine-validator assumptions. O adds **no** storage
honesty threshold, globally accurate clock, fault-free retention interval,
omniscient observer or new custody authority. Up to all enrolled storage peers
may lie, withhold or lose data for the safety cases. Their dishonesty can stop
progress, but must not enable unverified arithmetic/current changes.

Required safety claims are: exact authenticated AC witness coverage; canonical
close/ISC immutability; no seed before durable ISC; no first data-dependent vote
without its exact inputs and successful checked computation; original quorum,
parentage, no-double-vote, arithmetic/current uniqueness; unchanged lineage on
loss/repair/abort; and fail-closed recovery. **Physical available-attester quorum
at the original AC/close cut is removed from the claim**, not proved differently.

Liveness remains conditional on the original synchrony/quorum/fairness and
computation assumptions, plus delivery of the required valid statements before
close and access to every required exact byte value for its consuming operation
within the original attempt/deadline budgets. A signed retention obligation
does not imply that condition. No assumption of physically available q copies
is needed for safety; successful retrieval from a permitted original source is
still needed for progress. These conditions must be stated in the positive
models, with counterchecks when they fail. With no abort quorum, BLOCKED is
permitted; `APPLIED` cannot be guaranteed under total data loss.

The future R2.3 claim would be: independently anchored, fully checked original
native **O protocol history**, trusted floor and provenance metadata derive the
complete admitted O source state and a lossless relation to the revised public
protocol state; the existing R2.1/R2.2 arithmetic/constructor results are then
used only on their unchanged checked inputs. The independent native replay and
producer rules must be established without assuming public acceptance or R2.
The conclusion no longer reconstructs unobserved physical cuts. No theorem is
proved by this wording, and legacy native histories do not automatically qualify.

The named recovery theorem would inherit this exact O source claim after
reviewed R2.3 closure; it must still prove original journal/current/replay
preservation. It is not started here. Article/report wording must say
**authenticated certificate evidence and verified byte consumption, with
availability-dependent liveness**, not verified physical quorum at the cut or
unconditional retrieval. That claim change requires semantic approval.

## 9. Compatibility and finite qualification obligations

S's closed A/Gs/D formats and signing domains remain unchanged. The future
approved semantics/configuration pins must identify the changed interpretation
before new objects are produced. Consequently their hashes, ac, ISC B/b/C/c and
dependent QC IDs can differ for the **future** generation even without a new
field. Existing objects/signatures/QC/WAL retain their original bytes, IDs and
interpretation; they are neither imported as O by relabeling nor migrated.
No concrete `sigma_next` is assigned. W1 local storage identity and S-RANK rules
remain; full retained evidence must still fit the approved budgets.

The bounded qualification set for this proposal is:

1. **Source and authentication:** qualify S's exact registry/signature/context
   checks, full per-leaf witness and original-prefix/native-admission binding;
   local byte-use evidence is checked from actual inputs, not a success oracle.
   The existing worker audit/source modules at
   `a2fd17259240be0a7721512e7a12fe972587f3bf:formal/proposals/isc-source-generation/`
   (`check.py`, `check_non_isc.py`, `audit_availability.py`,
   `audit_storage_producer.py`, `SourcePolicy.lean`, `SourceBudget.lean`) remain
   source references, not evidence that these new obligations passed.
2. **TLA and behavior:** requalify §7 modules and their type/state/frame checks,
   `AvailabilityCertificateSound`, `AvailabilityBeforeISC`,
   `AvailableTicketCertified`, `RepairPreservesCertifiedLineage`, ISC/seed,
   parameter/apply/no-overflow/current/abort and recovery invariants. Exercise
   both physical loss orderings, authenticated false claims, full loss, local
   failure vs global absence, late/different witnesses and crash cuts. Relevant
   existing configs include `ticket-lease-availability`,
   `availability-loss-repair`, `input-freeze-seed`, `native-arithmetic-binding`,
   `native-arithmetic-liveness`, `current-binding-recovery`, `apply-recovery`,
   `safety-f1`, split-brain and affected vote-lifecycle/liveness configs.
3. **Lean and source relation:** retain `NativeAvailableQ.exactCoveredLeaves` /
   `noMissingLeaf` / `fullOriginalCorpus` only at their stated component-input
   scope; they do not prove S authentication or the new observation origin.
   Requalify `NativeIscAdmission.bindSource/fromBytesSource`,
   `NativeEarlySource.iscWholeBody/iscNoTupleErasure`,
   `PublicEarlyHistory.exactNativeSource/completePublicVote`, complete
   `PublicState`/input/early-body constructors and the joined source relation.
   `NativeReplayAdmission.wholeStartupSource` still does not establish genesis
   provenance. `PublicAbortAncestors.originalSevenLists/originalCounts` and
   `PublicFailureHistory.completePublicVote` must retain downstream lineage.
   `NativeCurrentHistory.currentStateDerived` remains a conditional component;
   full O replay/current composition and the subsequent
   `DeltaReduce.nativeArithmeticRecoveryRefines` are not supplied by it.
4. **Refinement and negative evidence:** revise versioned complete public state
   meaning/projection and the affected `public_state_projection.py`,
   `public_native_projection.py`, `check_public_state_replay.py`,
   `native_available_q.py`, `native_input_ledger.py`, source and trace checkers,
   corresponding schemas and fixture generators. No old physical-state root or
   synthetic fixture becomes new provenance. Preserve all original vectors,
   4/8/8/8/8 shard identities, full delivery inventory and W1 size checks.
   Required discrimination: valid signature but wrong key-role/context/leaf;
   union-only quorum; duplicate signer inflation; late witness backdating;
   AC-as-byte-substitute; missing/wrong inputs with otherwise valid QC parents;
   stale successful read; freeze rewrite after loss; repair substitution;
   unsigned abort; erased lineage; vote/slot duplication on replay. Model mutants
   must remove the **new actual safeguards**, not expect the intentionally
   removed physical AC guard to reject O's newly admitted case.
5. **Qualification:** rerun affected parametric composition/axiom audit, exact
   source/bytes compatibility, formal models/refinement/mutants and required
   reviews/reproduction. `make formal-check` belongs after an approved semantic
   implementation, not to this unimplemented ADR. All old results keep their
   historical statements; none grants compatible GO for O. R1/R2.1/R2.2 remain
   CLOSED for original domains; reuse in O is not a new closure claim.

The compatibility/claim mapping for constitution IX/X and ADR0000 must be
rechecked; their permissioned, BFT, current and safe-abort requirements remain
unchanged. Feature000 FR017/018/024, failure-semantics pre-close loss/AC wording
and S's physical-source paragraphs need explicit successor-generation wording
aligned with §§4–8. Any required change to the retained constitutional
boundaries is a separate STOP, not implicit in this proposal.

## 10. Decision requested and STOP

Approve or reject **this complete combination** of authenticated AC claim,
certified close set, exact data-use guards, observation/environment separation,
unchanged authority/lineage and conditional liveness. It is not approval of a
single `HasAttestationCoverage` substitution. No open choice between F and O,
unspecified storage honesty threshold or later choice of physical oracle is
hidden inside the proposed contract.

Approval would select the exact successor semantic contract; it alone is not
production implementation authority, a formal result, R2.3 closure or permission
to bypass ordinary assignment/review gates. Until that decision, STOP. If its
formalization reveals a need for another trust root, hidden source restriction,
changed forbidden identity/boundary or failed safety gate, preserve NO_GO and
raise that exact issue; do not weaken the stated obligations to make R2 pass.
