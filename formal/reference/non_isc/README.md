# Non-ISC signature reference — scope revision 5

T047/T053, ISC-S16-D01. This separate reference implements the exact Vn/Mn/Gn
contract in approved immutable ADR0015 sections 3–7:
`bb9fce957dae329701a8cd473a7148e198e1ca12:docs/adr/0015-non-isc-authority-binding-v1.md`.
Human decision `scope-decision-dff5cf14af975d7da34f29cfdc4a55c1` selected it;
the document's historical PROPOSED heading is not rewritten.

`codec.py` has exactly eight non-ISC kinds. It reuses common DRC1 field/framing
grammar without extending the ISC parser or signing domain. `authentication.py`
requires an independent exact codec-contract selection and derives original
registry/key/validator/epoch bindings from Bootstrap. Verification uses the
already pinned strict libsodium 1.0.22 primitive, never a success callback.
The selected source contract is a reference qualification input, not a claim of
an installed production codec manifest or an instantiated future semantics ID.

The return value contains exact original bytes/IDs and a verified signature.
It does **not** assert body legality, certificate finality, quorum, delivery
occurrence, durable producer origin or R2 refinement. No body/source admission
has been replaced with a signature-success assumption. No original object,
signature, QC or WAL is migrated. Public synthetic keys/vectors are test inputs.
The derived 946/1136/1172-byte bounds are framing bounds, not source-history caps.

The reference checks cover closed dispatch, byte-exact framing, all signed-field
mutations, original key/epoch/sigma, wrong signature domains, strict scalar/signature
rejection, sequence identity and exact replay. Pinned C Ed25519 calls are exercised
from Python; this is not complete cross-language codec or Formal GO qualification.

Before extending this component into full source composition, the source audit
found another unresolved original dependency: the six-field native
`AvailabilityProof` does not authenticate the storage attestations required by
feature003 FR-014/015. See
[`non-isc-source-checkpoint.md`](../../proposals/non-isc-source-checkpoint.md).
No storage signature protocol, key registry or producer rule is introduced here.

Reproduce local checks and the immutable-source audit:

```powershell
$env:ISC_SODIUM_DLL = 'D:/delta/.cache/isc-s16-libsodium-1.0.22/x64-release-v143-libsodium.dll'
D:/delta-main-demo/.venv/Scripts/python.exe formal/proposals/isc-source-generation/check_non_isc.py
```

**R2.3 OPEN; Formal NO_GO.** Body/certificate/producer-cut association and full
source composition remain unfinished. R1/R2.1/R2.2 and their old evidence stay
unchanged. No new Lean theorem, production code, recovery theorem or R3 is added.
