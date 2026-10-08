# R2.3 original profile source components

T047/T053 / ISC-S16-D01; effective scope 13. This is formal/reference work in
the approved fixed-epoch Snapshot Provenance Profile v1 and successor O lane.
No production implementation, concrete semantics ID, migration or READY claim.

The independent inputs are raw bootstrap/source-index custody, original own
journals and latest trust log, plus separately provisioned approved verifier
pins. Neither imported metadata nor a caller-supplied success result selects
authority. The checker preserves original artifacts, source occurrences and
all control bytes. Content descriptor hashes are raw byte references; they do
not replace domain-separated protocol or certificate identities.

`metadata.py` checks the four closed control document types, exact references,
finite budgets and trusted floor. Manifest journals contain separate `cut`
and `target` descriptors. Trusted anchor journal cuts need only be exact
prefixes of the retained own tip: later votes can leave current F unchanged.
Actual record boundaries and source state equality require the subsequent
journal/producer join. A missing journal is not an empty journal.

`authority.py` resolves validator key objects from the independent bootstrap
and storage registry/keys from its pinned original initial configuration's
approved `storage_authority` field. It preserves the other initial fields
without claiming their source legality. `configuration.py` uses the existing
DRC1 typed canonical encoding and all original 22 RoundConfig fields plus the
approved mandatory storage binding and the existing immutable close policy.
Its separate future schema version 2.0.0
does not assign sigma or accept/relabel legacy configuration bytes.

`configuration_qc.py` preserves the existing QC bytes and supplied original
`qc_id`; it does not invent a self-referential hash equation. The join checks
actual strict signatures and all matching original delivered signers at the
given cut, preserving repetitions, unrelated votes and exact vote IDs. This
establishes the certificate conjunct, not the delivery's occurrence, proposal
legality, durability or FinalizeRoundConfig history.
An original CONFIG receive is carried with its original event index and bytes;
the receiving actor is not substituted as a transport peer. Missing proposal
inputs leave the failed attempt in the complete event inventory.

`configuration_history.py` now folds original proposal/delivery/finalization
occurrences from an empty CONFIG collection. It preserves the first finalized
witness and does not backdate it using later deliveries. `source_prefix.py`
materializes every original source event and ordered input reference, keeps
cut/target as exact original prefix positions, and joins the CONFIG facet.
Other actions remain explicitly uncovered; phase/transport/local durability
are still obligations of the enclosing native producing history.

`journals.py` scans the complete original DRW1 kind 1/2/3 sequence and W1
preceding-prefix binding. `votes.py` retains original own kind-2 payloads at
physical slots and derives separate public vote ranks. Unsigned durable-but-unexposed
intents remain present, with no invented signature. Original detached signing
artifacts are checked when present. Producer/admission legality is still
required; structural WAL acceptance alone is insufficient.
Original signed `Vote.durable_sequence` is checked against its physical slot s;
`Intent.public_ordinal` separately exposes V_a(s). Neither rank nor any other
projection rewrites the signed Vote bytes. The earlier reference comparison
to vote count was a checker defect, corrected before R2.3 qualification.
The anti-equivocation key is exactly the native `(validator, epoch, context)`;
changing round/view/height/kind cannot create another local slot for that key.

`commands.py` derives the coarse state at every mixed WAL position by applying
the original N command rules and checking all original state/effect/inner-WAL
outputs. It retains original request IDs, idempotent cached responses, logical
time and policy invalidation. Physical slots stay separate from the coarse
state counter. The original N C++ command capture is compared byte for byte;
this is reuse of retained execution, not a new native run. Future-generation
bytes use the independently selected semantics ID without legacy fallback.
Kind-2/3 records remain explicit pending obligations of the complete producer
fold; the kind-3 prior coarse state is already joined to this original command
prefix. This component cannot establish initial-state authority, vote legality,
durable finalization or an externally visible effect by itself.

`ProfileSource.lean` proves general exact-reference, ordered position and
multiplicity results and S-RANK annotation preservation/injectivity. It uses
`NativeWalBytes.Entry` as a carrier, not the legacy kind-1/2 validity predicate
as a purported kind-3 proof. These lemmas contain no public-state/refinement
premise. They are not yet the complete profile source-to-family theorem.

`ProfileControl.lean` binds whole canonical control-document bytes and exact
closed root fields. Kernel vectors retain complete synthetic original bytes,
including negatives for duplicate members/trailing bytes and wrong profile.
This is not yet the complete nested semantic/control decoder equivalence.

`manifest_context.py` derives the full storage Context from the original complete
manifest/schema/scale/plan/profile/fixed-point config and enclosing RoundConfig.
The commitment is the ordered Merkle root specified in feature003 §3/US2 and
feature004 FR008-014, never the separately hashed manifest identity. It needs
no physical Q bytes at AC verification; `read_q` requires the actual exact
original envelope at data use. Schema/units and ordered unsplit leaves are
retained. Legacy schemas/fixtures are read only; the isolated future reference
uses the independently selected symbolic semantics and never rewrites old IDs.

`availability_ledger.py` replays the native InputLedger facet from empty, with
the approved O authenticated guard and complete original delivery inventory.
The source path derives Context from the retained commitment and byte inputs;
late evidence cannot backdate acceptance, exact repeats retain the first AC,
and rejected/alternate/lost-data observations remain in the event prefix.
This facet still requires the outer producing history to establish original
ticket issuance, commitment occurrence and ordinary-progress/close guards.

`ProfileManifest.lean` separates metadata resolution from actual complete corpus
use. Its general forward/converse lemmas connect that join to the existing
`NativeManifestBinding.bind` premise used by R2.1/R2.2, retaining original bytes,
ordered references, Merkle root and complete partition. It does not authenticate
hashes, assert remote physical facts or derive a producer history from a hash.

`observed_inputs.py` and `ProfileManifest.Observations` fold actual input reads,
failures, release, process loss and unrelated original source events from empty
volatile memory. A complete successful read preserves all five original vector
shards; bad/missing suffixes never insert a valid prefix. No AC or read receipt
creates owned bytes. External loss does not mutate an already retained immutable
buffer; release/crash prevents its reuse. General kernel lemmas derive original
source position and existing full `NativeManifestBinding.bind` for every selected
buffer, with a converse for the original accepted binding domain. This is the O
byte-use conjunct; full operation/phase/certificate production is still needed.

The existing `ISCSourceV2.SourcePolicy` component now binds the complete original
successor C bytes to their original policy-tree value, explicit parent, every
ordered unique tuple, all signer identities and separate computed b/c identities.
Its duplicate-last Merkle recurrence has a general fuel-completeness proof for
the existing 100000-tuple bound; the independent manifest's 4096-leaf cap is
not imposed on ISC. Exact canonical-byte comparison rejects duplicate JSON
members/alternate encodings. These shape/quorum-count checks do not establish
signature authenticity, original delivery occurrence or durable finalization.
Kernel examples use the approved FR004 roots and two original C witnesses for
one B, with an explicit finite table of actual SHA256 preimages/digests. This
table is cross-language byte evidence, never a proof or oracle for SHA256.

`scheduling.py` reconstructs original007 policy/plan/ticket/initial-lease/timer
bytes and the existing durable lease producer's DSJ1 records. The complete
native five-record expire/same-worker-reassign capture matches exactly. Original
worker/epoch/ticket identity and records remain; successful native commit leaves
the native lease bytes ACTIVE, while the static public active-set projection
excludes the committed ticket. General `ProfileSource.Ticket` lemmas preserve
ticket bytes, original history and commitment owner/epoch over arbitrary finite
action lists. They are static projection lemmas, not full deadline/command-byte
decoder or forward-transition simulation proofs. In particular, same-worker
reassignment is permitted natively but does not match the old TLA ReassignTicket
guard. That forward diagnostic is not a demonstrated static R2 counterexample
or a full authenticated Profile snapshot. No production code or action changed.
Original capability/decision/configuration provenance and full source invocation
binding still belong to the enclosing source checker; dataclasses are not trust.

`capsule_binding.py` checks all W1 sections against an independently supplied
predecessor: exact own WAL prefix and next physical slot, original source cut,
whole S0/P0 and full retained deliveries, computed P1/C, one witness publication
with unchanged coarse state, and exact receipt IDs. Recomputed checksums cannot
hide a b/c substitution, lineage deletion, resequencing or another effect. The
enclosing producer fold must still derive this predecessor; the dataclass or a
successful byte join is not origin authority, append success or a durability
barrier. Synthetic W1 tests intentionally retain opaque invalid lineage markers
and do not claim to be complete legal histories.

`bind_indexed` derives the coarse predecessor and received inventory from the
original own WAL and an independently retained pre-finalization source index.
W1 references that earlier index, as required by its approved contract, rather
than the later snapshot index containing the capsule itself. Inclusive W1 cuts
and profile prefix lengths remain distinct. `ProfileSource.Cut` proves exact
prefix/position preservation and exclusion of future source bytes.

Every ISC delivery is tied to its original receiver, relay peer, exact V/G and
original body input, using the independent epoch registry and strict signature
verification. Earlier dependencies may supply original inputs; later events
cannot. Repeats/conflicts keep their positions. Missing valid signed artifacts,
unknown delivery layouts and position mismatches remain unresolved source
inputs rather than being silently dropped as rejected votes. Invalid signatures
and failed budget attempts remain in the original event inventory. This closes
the received-byte/cut join, not transport origin or honest send durability.
Initial-state authority, full P0, frozen ledger, clock/control, other native
producer checks and durability barriers are still required by the whole fold.

`input_history.py` now composes the existing original byte carriers from an
empty input ledger: local CONFIG proposals/deliveries/QC, exact native007 plan
and issued tickets, complete004 manifest/root, original received Storage Gs,
authenticated AC and first freeze. It computes the entire closed B, retaining
all original tuples and source events. Other receiver deliveries cannot supply
the local CONFIG or AC quorum. Closed disjoint NSG1/SAG1 containers remain in
the source prefix with their own handlers; they receive no ISC quorum credit.
Unknown/missing input carriers remain unresolved rather than silently omitted.

`bind_input_indexed` re-resolves original validator/storage keys through profile
authority, reconstructs this input facet at W1's original retained cut, and
passes its computed B/tuples into the existing exact W1 join. No caller-provided
frozen tuples or body are accepted on that path. This is not a complete producing
history: initial plan/configuration authority,
lease/phase/time/transport/control, full P0 and barriers remain outer obligations.
`producer_edges` explicitly retains successful facet events for those checks;
absence of byte-resolution errors is not full source validity. Combined fixtures
still include unqualified initial policy/current/anchor fields and assert no READY.

The input-close selector now comes from the original signed configuration, not
a free `close_policy` argument. This implements the already frozen requirement
in `failure-semantics.md` section5 that RoundConfig selects exactly one immutable
policy; S section3 expressly preserves that field while adding storage_binding.
The future reference grammar spells it `availability_policy.close_policy` with
the two existing exact enum strings. It selects neither policy for deployment,
changes neither close guard nor the required-ticket domain, and introduces no
new source authority or default. All old production objects and frozen fixtures
remain unchanged. Fresh synthetic configurations and dependent signatures/IDs
are recomputed; old bytes are never reinterpreted under the completed grammar.

`ProfileConfiguration.lean` parses the complete typed DRC1 tree with fixed keys,
tags, original U32/U64/text/vector bounds and nested storage/retention objects.
General round-trip and injectivity proofs cover every encodable value, not only
fixtures. Exact frame decode/re-encode equality rules out alternate typed
descriptors for the same bytes. The selected close policy is a function of those
original bytes. Remaining semantic validation, independent CONFIG provenance
and the full state relation are still required; byte decoding is not finality.
Kernel vectors check both policies against complete Python-generated original
bytes. The partial two-ticket diagnostic retains all original events and AC
lineage; it is component evidence, not a complete production snapshot or ABORT QC.

`ProfileNativeHeader.lean` joins original CONFIG/S0/P0 bytes through the full
typed codecs. It checks parent/height/count, epoch/validator membership, original
soft/hard deadlines, round/configuration identity, schema and complete coarse
state ID. The current view and physical sequence remain exactly as captured;
neither is reset to the CONFIG voting view. Policy encoding injectivity covers
every field, including unprojected downstream collections. This is not initial
state authority or a proof that those collections arose legally. The input/W1
reference path applies this join using its source-derived finalized CONFIG.
Kernel vectors use finite SHA tables of explicit original preimages, with no
hash axiom or native-evaluation proof axiom, and are synthetic partial inputs.

Run `formal/proposals/b-family-transfer/check_profile_components.py` with the
pinned `ISC_SODIUM_DLL`; it rebuilds the involved Lean sources, audits axioms,
checks the reference components and records exact source/log hashes. All
fixtures here are synthetic component evidence, including deliberately
invalid opaque QC/history placeholders in metadata-only fixtures. They are
not authenticated production captures or evidence for R2.3 closure.

`SourceVote.lean` binds the approved twelve-field successor Vote grammar and
all nine existing kinds to exact original bytes, with general inverse and
injectivity results. It reuses primitive byte lemmas, never the legacy Vote
decoder or legacy semantics ID. Original registry/key/V/signature descriptors
must reproduce the entire detached artifact and signable preimage. Artifact
size follows from the existing field bounds. A structural zero-signature vector
does not establish authentication; the pinned strict verifier remains required.
Own-journal binding preserves signed physical sequence; composition with S-RANK
keeps two distinct original votes distinct without rewriting their bytes.
The indexed W1 path now also checks every original kind-2 predecessor's exact
bytes, actor, epoch, physical slot and native context uniqueness. It records
unsigned intents without inventing signatures; producer admission and original
signature/barrier events remain separately required in the full source fold.

The input facet now checks the four complete P0 input collections against the
original CONFIG and close occurrences. Adding, removing or duplicating a list
element cannot be hidden by a correct header or a recomputed policy hash. Every
original event and non-selected configuration occurrence remains in the source
prefix. This still requires enclosing producer, initial-state and full-history
qualification; the facet is not asserted complete for every policy/source cut.

`ProfileConfigurationQC.lean` joins the complete original CONFIG and QC bytes
to original delivered V/G records. Independent enrollment, the full CONFIG
context, exact signer/vote pairing and all matching signers are checked; it
does not select the first quorum or replace a witness on a later arrival cut.
Original duplicate deliveries and multiple remote votes from one signer remain
distinct occurrences. A same body/context group with inconsistent full context
is rejected rather than filtered away. Kernel vectors retain two original QC
witnesses over the same received inventory, with signatures independently
checked by the pinned reference verifier on synthetic keys. The general Lean
byte relation does not assume that structurally bound G has a valid signature:
authentication, actual delivery, first-finalization permission and the complete
producer prefix remain obligations of the enclosing source checker.

`ProfileSourceIndex.lean` now materializes complete ordered event and artifact
inventories from the original source-index descriptor and exact canonical bytes.
Every original reference retains all fields, resolves against the same declared
inventory, and matches its original length/content ID. Actors, actions, ordered
inputs (including repeats), original positions and strict backward dependencies
are source-bound. The general soundness/completeness results cover this byte
materialization, and its delivery adapter retains the original G/actor/position
used by the CONFIG QC join. They do not prove that a recorded event was legally
produced or authenticated. Independent bootstrap selection, journal-range/floor
composition and the full native producer remain required. Synthetic vectors
deliberately retain malformed protocol payloads: materialization cannot erase
them or turn them into a valid native history.

**Residual remains the same R2.3:** complete independent producing prefix and
source/configuration/aliases/units; complete O collections/current/environment
relation and totality; initial/incomplete and sufficient ABORT with all
downstream lineage. These components reduce the byte/authority/journal joins
inside that work but do not discharge those complete obligations. The named
recovery theorem must follow substantive reviewed R2.3 closure.
