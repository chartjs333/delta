# Future source-generation components — ISC-S16-D01

T047/T053. Isolated feature-000 reference work authorized by nginx-qa effective
scope revision 3, human decision `scope-decision-440f81e578f29a53a34a33be3ebc21aa`.
The exact approved amendment is Git blob
`26eb02d0632435c9aa0d8ef44eb496b6fa73dd13:docs/adr/0014-isc-production-contract-amendment-v1.md`,
SHA-256 `214ca238fde93ebe2e6e08b25a6ea366b93d735333125f651398c0d0daad58fd`.
Its historical DRAFT heading is preserved; the later human decision authorizes
this isolated successor qualification, not production deployment.

`identity.py` implements the exact successor B preimage and C JSON with explicit
parent, approved FR-004 tuple/tree bytes, and separate b/c lookups. It rejects
duplicate JSON members before typed parsing, including escaped duplicate names.
The existing round-scoped ISC anti-equivocation context stays round-scoped.
Distinct original C witnesses for one B remain distinct; no c/b fallback exists.

`policy.py` implements DVPOL002 with the two parent insertions specified by the
amendment. `policy-layout.json` retains the complete 35-record structural grammar,
including all 33 snapshot fields. Every other original field, order and bound
is preserved. Unknown/missing fields, wrong headers and trailing bytes reject.
This is a separate codec, not a legacy object migration or authority check.

`authentication.py` reconstructs fixed R/E/K from independent primitive bootstrap
inputs and checks exact V/G with the pinned strict libsodium 1.0.22 verifier.
It binds full B bytes, original validator/key/epoch, signed physical slot and the
duplicate material retained in W1. Signer grouping uses full body bytes and all
matching original validators. Repeated/conflicting evidence is not erased.
This function proves neither remote fsync nor legality of producing history.
The reference signing adapter accepts public synthetic seeds only.

`budget.py` checks the fixed admission limits against the complete retained
inventory, including repeated deliveries across views. It measures exact W1 and
result bytes before any append; it does not truncate history or establish public
state bounds. Full source-history linkage must ensure the supplied inventory is
the complete original cut for the actor/origin/epoch/round.

`finalization.py` composes exact authenticated deliveries, complete matching
signers and the W1 P0-to-P1 membership delta. Prior certificate variants and all
other policy/snapshot fields survive. A finalized round requires its original
replay receipt instead of reassembling a witness from later arrivals. `Cut` is
primitive source input, not provenance authority. This component does not
establish phase, complete delivery occurrence, the frozen ledger's origin or
the full producer transition. No append, durability or exposure is implemented.

`formal/proposals/isc-source-generation/SourcePolicy.lean` proves typed source
round trips, exact parent extraction, complete structural field preservation
and injectivity of the full successor policy encoding. It imports no public
relation. `SourceBudget.lean` proves the approved W1/output size implications
from the already selected admission caps. Neither theorem assumes public success.
These are source-binding components, not a general producer-origin theorem.
The additional field-update lemmas prove retention of every snapshot field
outside the two W1 memberships and every policy field outside its snapshot,
without an empty-lineage premise. They do not establish validity of the original
contents. The synthetic composition fixture keeps opaque nonempty sentinel
collections; it is deliberately not a qualified source snapshot.

Reproduce with the previously authenticated local backend (no download required):

```powershell
$env:ISC_SODIUM_DLL = 'D:/delta/.cache/isc-s16-libsodium-1.0.22/x64-release-v143-libsodium.dll'
D:/delta-main-demo/.venv/Scripts/python.exe formal/proposals/isc-source-generation/check.py
D:/delta-main-demo/.venv/Scripts/ruff.exe check formal/reference/isc_source formal/proposals/isc-source-generation/check.py
```

The checker verifies the exact approved Git blob, rebuilds the complete Lean
dependency closure, audits theorem axioms and records source hashes and local
reference results in `formal/proposals/evidence/isc-source-v2/`. Source-file
identity uses tracked UTF-8 text normalized from CRLF to LF, matching
Git blobs; the receipt states that rule explicitly. Protocol/signed/binary bytes
are never normalized. The receipt at `7dc4b546` had one working-tree CRLF digest
for `policy-layout.json`; evidence review rejected that mismatch. The subsequent
receipt repairs the source fingerprint, not the old result or protocol objects.
The only reported Lean axioms are standard foundations; no `sorryAx` or custom
oracle is accepted.
Public synthetic fixtures test byte and crypto composition, not authenticated
production histories or independent attestations.

**R2.3 OPEN; Formal NO_GO.** The frozen residual remains: independently produced
full source/configuration/aliases/units, complete remaining collections/public
state constraints, and initial/incomplete/sufficient ABORT correspondence with
nonempty lineage. These modules supply concrete components for that same residual;
they do not close it or create a new gate. Complete producer/history origin,
Profile-v1 applicability and the full public family must still be derived.
Legacy R2.1/R2.2 evidence is unchanged. No recovery theorem/full R3, concrete
sigma assignment, production integration or guard removal is performed.
