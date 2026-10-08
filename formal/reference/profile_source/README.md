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

`journals.py` scans the complete original DRW1 kind 1/2/3 sequence and W1
preceding-prefix binding. `votes.py` binds original own kind-2 payloads to
public vote rank rather than physical slot. Unsigned durable-but-unexposed
intents remain present, with no invented signature. Original detached signing
artifacts are checked when present. Producer/admission legality is still
required; structural WAL acceptance alone is insufficient.

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
