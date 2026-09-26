# Complete native ISC certificate and finalized section (conditional)

T044/T048/T049/T053/T057/T060; amendment 0001. This is a formal proposal.
Formal/native authority remains **NO_GO**. The existing CONFIG/proposed-ISC
replay admission modes are unchanged and still reject finalized/later graphs.

## Executable relation

`NativeIscCertificate` reads the actual `fmtInputSet` DVPOL typed tree, preserving
all context fields, the complete ordered tuple list, threshold and signer list.
Its bounded byte entry uses the existing exact `NativePolicyCodec.decode` and
checks the original wire reencoding; no supplied whole-body translation is used.
A successful result retains its exact original tree and wire encoding.

The checker derives all 14 ordered native JSON fields (including the original
native semantics ID, schema and type), then two separate domain-separated
content IDs:

- certificate QC ID: canonical JSON with threshold and signer list, domain
  `deltareduce.008.input-set-certificate.v1`;
- voted-body ID: original binary ISC body without threshold/signers, domain
  `deltareduce.vote.input-set-body.v1`.

Both domains have the existing NUL separator. SHA is an explicit function;
a digest must have 32 bytes, otherwise checking fails. Pure JSON/value/ID
constructors do not imply guarded admission. Only `check`/`fromBytes` establish
shape/context/quorum checks. Numeric JSON uses Lean natural decimal rendering;
there is no claimed general cross-language JSON or SHA theorem.

The configured committee must be nonempty, sorted, unique, label-valid, at most
4096, and of size 3f+1. Certificate signers must be ordered unique configured
members with count at least 2f+1 and an exact matching threshold. The native
context, full tuple pair ordering, nonempty tuple coverage and ID/label shape
checks are retained from `NativeInputSetBody`. The tuple/signature vectors use
the original 100000 limit and the byte entry has a 4 MiB diagnostic limit.
These are explicit input-profile bounds, not a native admission generalization.

`NativeFinalizedIscSection` extracts the *whole* original certificate vector and
finalized-ID vector from the policy snapshot, recomputes its linked native state
ID, checks the original policy/state header, and uses that header's configured
context and committee for every certificate. QC IDs and finalized IDs must be
strictly ordered; every finalized ID must name an actually checked certificate.
General lemmas retain the entire original list, position/count and certificate
source/context/quorum/identities. `prepare` uses actual policy/state byte readers.
No assumed recovered-state equality, finite admission table or approval callback
is used. Missing/duplicated/invented finalized certificates fail these checks.

This module intentionally validates **only the ISC section**. It is not a full
snapshot validator: later vectors, proposed-body membership, seed/EC/APC edges,
current-state transitions and fresh vote admission are not checked here. The
pinned native validator also does not require a finalized certificate body to
occur in its proposed-body set; no invented rule is added. A successful isolated
section must never be used as a successful whole graph/admission result.

## Source and finite evidence

Read-only native reference commit:
`60c692f6e391f839829dfc64e93380db54cd507b`. The generator verifies source blobs,
extracted definitions, harness hash and retained native certificate observations
from `native-certificate-chain/cpp-cross-check.json`. It separately pins the
entire original `native-policy-wal/cpp-cross-check.json` and decodes the unchanged
`codec-EC` policy. Its complete ISC wire section must occur exactly once in those
original policy bytes and must equal the independently pinned native certificate.
This is cross-source fixture consistency, not exporter authentication.

Generated kernel proofs check the original complete certificate JSON, original
policy-section wire, its decoder and computed QC/body IDs. Three finite SHA
samples include an alternative signer set. That finite example has the same
voted body and a different QC ID; general hash injectivity is not asserted.
Cases reject missing/unknown/duplicate/reversed signers, wrong quorum/context,
malformed root/empty/duplicate tuples and invalid committees. Separate small set
cases reject absent/duplicate certificates, duplicate finalization and substitution
of the voted-body ID for the QC ID. Those set cases have arbitrary headers and
are **not** a new complete policy/state-section acceptance fixture.

There is no new native C++ execution, physical WAL scan, arithmetic execution,
TLC run or production mutant in this stage. Prior native component runs remain
retained finite evidence. Existing original arithmetic records/sequences 5/6/8,
all native witnesses, TLA and runtime sources remain unchanged.

## Open boundaries

Signer identifiers and a threshold are not authenticated cryptographic signatures.
The configured committee, snapshot origin, input-root preimage, ticket/availability
ledger, unique ticket membership and actual close/finalization provenance are not
authenticated by this layer. Same-ticket/different-commitment cases retain their
previous native scope. Three SHA samples do not implement general SHA. General
JSON byte correspondence/injectivity and arbitrary production size profiles remain
open. The independently pinned native semantics constant is not a new GO authority.

Next: construct original seed transcripts and exact finalized ISC parent edges,
then EC membership/norm/seed links and APC partition coverage using actual payloads;
join the resulting closed checked graph to shared admission/replay only when every
required section is checked. General DRS1 decoding, initialization/export/physical
scan provenance, unknown outcomes, repair, all public-state/action/refinement,
`nativeArithmeticRecoveryRefines`, contract freeze, offline reproduction and
independent review remain required. Missing response never proves absence.
No native guard, runtime/demo service, frozen ref or acceptance classification changes.

## Reproduction

Run in the candidate checkout with pinned Lean/toolchain dependencies:

```text
python -X utf8 formal/scripts/generate_native_isc_certificate.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_isc_certificate.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeIscCertificate.lean
lake --no-cache env lean DeltaReduce/NativeFinalizedIscSection.lean
lake --no-cache env lean DeltaReduce/NativeIscCertificateVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final exact counts, source hashes, retained outputs and constraints are recorded in
`evidence/native-isc-certificate.json`. `check_lean_evidence.py` must still report
44/45 and the missing recovery theorem. GNU make is unavailable on this host;
scoped checks do not constitute aggregate `make formal-check`.
