# ISC-S16-D01 — storage producing-history boundary

T047/T053, 6 October 2026. **NEED_DECISION / R2.3 OPEN / Formal NO_GO.**

Scope revision 7 is active for assignment
`b52fcd71-2a71-456e-86a0-f5c1691f58c9`; exact ACK
`scope-ack-9946f552dad9e7696d4b29ea5d9d240f` was GET-confirmed. Human decision
`scope-decision-614a7db8512f59e36720131917827d4c` approves ADR0016 §§3–7 at
`1438fa3d78ec99291475cf4660fd8c190ac01bb3`. That byte/authority decision is
settled. It is not being reopened and full R2.3 permission is not requested again.

Before implementing that component, its explicit §6 prerequisite was checked:
is the original availability-producing history independently defined and bound
to the supplied source? The immutable source audit below finds a missing link.
Scope7 expressly requires STOP at this boundary; signature implementation cannot
remedy it. No storage codec, new producer or additional proof layer was started.

## Exact residual

Let N be `60c692f6e391f839829dfc64e93380db54cd507b`, the approved profile's
native source pin. The missing item is **original native storage
producer/observation-to-history binding at the attestation/finalization cut**.
It is not merely an unimplemented signature verifier or a request for more tests.

| Existing boundary at N | What it actually supplies | Missing link |
|---|---|---|
| `DeltaReduceAvailability.tla`: `UploadArtifact`, `AttestAvailability`, `LoseArtifactPreFreeze`, `FinalizeAvailability` | Exact public guards over `availableArtifacts`; finalization uses per-shard `AvailableAttestersFor` | Public actions cannot serve as the independent native source evidence being refined |
| C++ `InputLedger::record_availability`, `consensus.cpp:626` | Six-field aggregate admission, leaf/attester membership, conflict/replay/late handling | No original upload/loss/corruption/repair event or state at the producing cut. All callers in the pinned code inventory are tests; no complete storage producer is wired here |
| C++ `transition.cpp`, `ACCEPT_AVAILABILITY` | Phase and count guard, then count increment; native WAL can retain that command | No AC/source-cut validation in this transition; its opaque body hash is not evidence of an available storage location |
| Native runtime `submit` / `record_vote`, certificate runtime | Durable commands/votes and existing replay identities | Persistence of supplied commands does not establish missing storage event origin/completeness |
| Java `ArtifactEffectAdapter` / `AuthenticatedCertificateTransport` | Local WRITE/REPAIR execution; opaque delivery with injected authenticator | No bound remote per-storage/per-shard history or independent original finalization cut |
| Python `FilesystemArtifactStore` | Local immutable publish/read with byte hash and length verification | No enrolled remote storage identity, retention/finalization event history, or source-cut completeness |
| ADR0016 A/Gs/D and independent Rs/Ks | Approved exact future statement authentication and per-leaf witness association | The document explicitly does not produce or prove physical availability/source legality |

The inventory is scoped to N and the approved source contracts. It does not
assert that an external producer cannot exist. Providing an applicable immutable
producer contract and original event/evidence path would resolve the missing
input for review. No such artifact is supplied by these boundaries. The current
formal worker checkout is not relabeled as N or as a deployed successor runtime.

## Minimal distinction that signatures cannot decide

Take one original committed leaf and the original configured threshold 3.
After uploads and attestations from storage-1, storage-2 and storage-3:

1. At cut A all three locations are available: `HasCompleteAvailability` holds.
2. Before finalization at cut B, `LoseArtifactPreFreeze(storage-3,content,leaf)`
   removes one location. The same original attestation statements and signatures
   still exist. Attestation coverage is 3, but available-attester coverage is 2.
   `FinalizeAvailability` is disabled by its existing guard.

All other original leaves can retain full coverage in both cuts. Candidate
AC witness bytes/IDs and the ledger's six fields need not differ. Neither valid
SAG1 signatures nor a faithful copy of those bytes on T distinguishes the cuts
without the original producing/observation history. Replacing the missing
membership fact with `signature_valid`, public-check success or a supplied
`available=true` would assume what the source relation must establish.

This is a guard/source-information diagnostic, **not** an end-to-end production
attack, a TLC trace, or a valid imported snapshot counterexample. Cut B's proposed
finalization is specifically *not* a legal public step. It does not establish
that such a bad snapshot passes the full profile, whose verifier remains open.

Order matters: finalizing at A and losing the shard afterwards is different.
The original AC/ISC lineage remains valid and retained; existing repair/abort
rules apply. This audit requires neither perpetual availability nor deletion of
existing certificates. Original votes, signers, delivery multiplicity and WAL
sequences remain unchanged.

## Decision boundary and retained progress

The required resolution is an existing immutable storage producer/observation
contract and its original source evidence, or a separate architectural decision
about that absent contract. We do not select a new observer, stronger storage
honesty assumption, new admission rule, source-domain restriction or changed
`Init/Next`. Reusing TLA `Next` as the source authority is not a repair.

The architectural choices for keys and canonical A/Ms/SAG1/D/ac are retained.
This checkpoint does not claim their reference implementation or qualification
is complete. The existing ISC and non-ISC components are preserved. R1/R2.1/R2.2
remain CLOSED in their original domain; the frozen R2.3 source/config/collections
and incomplete/ABORT residual remains OPEN. Full bounds/composition and the named
recovery theorem have not been reached; no full R3 or production integration.

Reproduce `python formal/proposals/isc-source-generation/audit_storage_producer.py`.
Its JSON evidence records exact Git blob hashes, pinned production/test call-site
inventory and the guard cardinalities. It is source inspection and a diagnostic,
not a new acceptance checker. No formal gate failure is relabeled as PASS and
no existing evidence is promoted to new qualification. Process reviews by this
same executor are not independent Formal GO attestations.

Send this exact result through both ordinary reviews. The coordinator must
register the unresolved semantic boundary through Pending decisions, preserving
the active sprint and all histories. Do not advance to qualification or continue
implementation merely because byte-level scope7 is approved.
