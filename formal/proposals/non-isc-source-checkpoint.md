# ISC-S16-D01 — scope-5 source checkpoint

T047/T053. 6 October 2026. **NEED_DECISION / Formal NO_GO / R2.3 OPEN.**

The approved non-ISC byte/signature reference is now implemented separately from
ISC. It verifies eight original validator-vote kinds, exact Vn/Mn/Gn, independent
codec selection, original key/epoch/sigma and the strict pinned primitive. This
removes the earlier *undefined non-ISC signing-byte contract* obstacle within
the approved future reference generation. It does not close ADR0015's complete
body/certificate/history/composition acceptance criteria.

## New concrete boundary in an existing obligation

Native source N=`60c692f6e391f839829dfc64e93380db54cd507b`:

- `specs/003-bft-round-state-machine/spec.md`, FR-014 requires storage peers to
  attest exact shard IDs, lengths and retention epoch with unique-attester
  quorum; FR-015 prohibits an input without a valid AC from entering freeze.
- `delta-core-cpp/include/delta/core/consensus.hpp:397` exposes
  `AvailabilityProof{ticket_id, commitment_id, certificate_id,
  covered_leaf_ids, attester_ids, threshold}`.
- `delta-core-cpp/src/consensus.cpp:626`, `InputLedger::record_availability`,
  checks exact leaf-ID coverage, permitted distinct attester IDs/threshold and
  commitment equality. It checks certificate-ID syntax. It receives neither
  attestation bytes/keys nor shard lengths/retention epoch and does not derive
  the certificate ID from an authenticated original AC.
- Existing `consensus_test.cpp` calls this API with constructed IDs/lists.
  Those tests establish structural admission/replay, not storage authentication.
- The original protocol registry has transport AVAILABILITY dispatch and ISC AC
  references, but no identified canonical storage-attestation/AC signing codec
  or attester-key binding. Searches covered the pinned core/runtime/FFI, Java,
  worker and protocol registry/schema source. Benchmark governance attestations
  explicitly concern another authority and cannot be borrowed.
- The pinned Java `AuthenticatedCertificateTransport.Authenticator` is an
  opaque `(peerId, bytes, tag) -> boolean` boundary, not a concrete storage AC
  decoder/verifier. It supplies no missing attestation schema or role/key binding.

Minimal diagnostic pair: one ticket, one leaf, three permitted storage IDs,
threshold three, one syntactically valid commitment ID and AC ID. Keep all six
API fields equal. In one external history the original attestations authenticate
the correct leaf lengths/retention epoch; in the other they are absent or stale.
The API sees the same input and cannot distinguish them. This is an exact source
interface insufficiency, **not a demonstrated production-reachable attack**.
The audit creates no new AC encoding and executes no modified native code.

The public target is not empty: `DeltaReduceAvailability.tla` uses original
`UploadArtifact`, `AttestAvailability`, `HasCompleteAvailability` and
`FinalizeAvailability`, with per-storage/per-shard available-artifact membership.
Assigning those facts from the six-field aggregate or from an arbitrary success
callback would assume missing provenance. We do not change these actions.

## Why this needs a semantic decision

Approved Snapshot Provenance Profile v1 requires original native producing
history and complete source preimages from pinned genesis. Its trusted volume
attests faithful observation of original bytes, not the truth of an arbitrary
prepared policy. A missing storage source binding cannot be replaced by the
local volume, an ApplyQC signature, or newly authenticated validator votes.

Approved ADR0015 section 5 expressly preserves the storage authority boundary;
section 3's table authorizes only original validator votes. Extending NSG1 or
SIG-ISC to storage attestations, assigning validator keys to storage IDs, choosing
new signed fields/domains, or declaring every recorded proof authoritative would
be an unapproved semantic choice. No such choice is implemented.

Required resolution: identify an already normative exact original storage
AvailabilityAttestation/AC source-authority/codec contract and its evidence, or
make the separate semantic decision that defines that missing binding for the
future isolated generation. This checkpoint does not select an algorithm,
storage trust root, new producer rule or migration. There is no blanket claim
that every other upstream dependency is already qualified.

## Residual and retained work

The residual remains the frozen R2.3 source/configuration/collections and
initial/incomplete/ABORT correspondence with complete lineage. Non-ISC body and
certificate associations, original producer cuts, and full Profile-to-public
composition are not yet closed. The new storage gap is a dependency of those
existing obligations, not a fourth DoD item or a new proof layer.

Implementation stops at the source boundary. Preserve the checked signature
component, send this exact commit through both normal process reviews, and let
the coordinator register the necessary semantic decision through Pending
decisions. Sequential reviews remain process checks, not independent Formal GO
attestations. No recovery theorem or production integration follows this result.

Evidence: `formal/proposals/evidence/non-isc-source-v1/receipt.json` and
`availability-boundary.json`. Source hashes use Git-compatible LF text only;
original binary/signature/vector bytes are never normalized.
The initial regression runner omitted the legacy crypto tests' local import
path; its ImportError log is retained. Supplying their existing module path
fixed the invocation. Final local component/regression checks pass; no protocol,
proof or gate failure was relabeled. Full formal qualification remains pending.
