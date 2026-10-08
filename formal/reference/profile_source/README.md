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
approved mandatory storage binding. Its separate future schema version 2.0.0
does not assign sigma or accept/relabel legacy configuration bytes.

`configuration_qc.py` preserves the existing QC bytes and supplied original
`qc_id`; it does not invent a self-referential hash equation. The join checks
actual strict signatures and all matching original delivered signers at the
given cut, preserving repetitions, unrelated votes and exact vote IDs. This
establishes the certificate conjunct, not the delivery's occurrence, proposal
legality, durability or FinalizeRoundConfig history.

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

Run `formal/proposals/b-family-transfer/check_profile_components.py` with the
pinned `ISC_SODIUM_DLL`; it rebuilds the involved Lean sources, audits axioms,
checks the reference components and records exact source/log hashes. All
fixtures here are synthetic component evidence, including deliberately
invalid opaque QC/history placeholders in metadata-only fixtures. They are
not authenticated production captures or evidence for R2.3 closure.

**Residual remains the same R2.3:** complete independent producing prefix and
source/configuration/aliases/units; complete O collections/current/environment
relation and totality; initial/incomplete and sufficient ABORT with all
downstream lineage. These components reduce the byte/authority/journal joins
inside that work but do not discharge those complete obligations. The named
recovery theorem must follow substantive reviewed R2.3 closure.
