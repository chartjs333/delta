# Source-bound finalized APPLY and current-pointer composition

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-certified-current.json`.

NativeCertifiedCurrent reuses the actual original complete APPLY snapshot and
selects a finalized ApplyQC using the original CurrentPointerCommand QC ID.
It recomputes NativeApply from the source-derived Binding and compares the entire
original ROOT certificate plus ROOT ID and the exact source-selected profile.
The prior certified PARAMETER corpus checker supplies every original finalized
leaf with full Q coverage, exact parents, values and decimal spelling. A general
lemma derives equality of the original ROOT source representations from actual
checked decoders. Whole-body translations or caller arithmetic approvals are
not inputs. fromSource composes the constructed raw authority, original current
history, certified corpus and computed aggregate under the common HashAdapter.
Both raw-source entry points take the complete pre-advance current tuple from
that executed history, including its original QC and height; they do not accept
an independently supplied current tuple with merely matching numerical hashes.
Both also refuse a retained torn suffix in that preceding history. A prior
successful value reconstruction alone does not authorize a new pointer advance.

The checker retains the full candidate model/optimizer decimal vectors, exact
native output and parent hashes, canonical original command/QC hash preimages
and the selected finalized QC ID. Draft artifact IDs do not replace native
certificate/command IDs. Fresh current advancement checks both parent model and
optimizer against the admitted anchor, plus the original CAS/height decision.
The exact original five-field pointer-WAL record is derived from that preparation.
Successful record replay reaches the computed next tuple; exact retry uses the
historical preparation and allocates no second record. It does not incorrectly
apply first-advance freshness to an already advanced pointer.

The observation API parses the actual pointer-WAL bytes and compares the complete
observed record list to the one selected next record. It rejects missing, extra,
duplicated or substituted records, wrong parent/height and corrupt checksums.
Unknown remains incomplete. A torn suffix is preserved as evidence; the separate
completeObservation/resumable gate rejects it. This restricted single-next-record
API is not an arbitrary journal-prefix recovery proof, physical fsync/observation
authentication, or authorization to truncate or resume native writes. The earlier
native WAL scanner still accepts rehashed uncertified IDs; its counterexample is
retained and the added exact-record comparison rejects that substituted record.

Tests reuse original008 certificate/command components and the already retained
synthetic pointer-WAL fixture with finite SHA samples. They are not a new full
source-graph execution, native capture, authenticated quorum or SHA proof.
The golden current tuple hash convention is independently checked in Python.
No missing original008 proof/base/current vectors are invented. Native decimal
compatibility and full signed-boundary differences remain unresolved.

All Binding anchor/recovery/certificate premises, UnitSource/configured profile,
initial/current custody, cryptographic signer authority and physical observation
remain independently required. Reading finalized membership and checking signer
shape does not authenticate those premises. The fresh/current/recovery wrappers
are conditional formal proposal APIs only. Native runtime and arithmetic guards
are unchanged. No local acceptance PASS or nativeArithmeticRecoveryRefines.

Next: source-bound original arithmetic vote metadata/admission and pre-WAL record
composition with the mixed journal. Full phase/QC/send/delivery/current/crash,
unknown/torn/repair and arbitrary initial snapshots, bounded concrete codecs/hash/
exporter resources, compatibility, amendment freeze, clean offline reproduction
and independent review remain mandatory before exact merged Formal GO.
