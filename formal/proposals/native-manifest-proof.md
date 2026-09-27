# Complete original manifest and corpus binding (candidate)

T044/T048/T053/T054/T056/T057. Formal proposal only; **NO_GO**.
Evidence: `formal/proposals/evidence/native-manifest.json`.

`NativeManifestBytes` decodes all eighteen original manifest fields and every
ordered eight-field shard reference. Canonical natural numbers, unescaped ASCII,
exact key order, full preimage equality, 4096 references and a 4 MiB document
limit are checked. Roundtrip, complete-preimage and encoding-uniqueness results
reuse the preceding byte/sequence lemmas. This is a bounded Lean list parser;
native stack/allocation/time equivalence is not claimed.

`NativeManifestBinding` loads the actual schema, scale and plan bytes and derives
the complete partition with the preceding planner. It interprets every reference
and compares the entire ordered entry list with that plan. Its corpus traversal
consumes exactly one actual block per reference; either unmatched tail rejects.
Each block is decoded by the existing framing/header/scale checker. Its complete
expected header is constructed from the manifest context, original reference
fields and the hash of the actual payload, with fixed version/type. The entire
header, numeric range, payload length, original envelope length and domain-bound
leaf identity must agree. All original fields remain in the checked preimage;
no expected body, translated state or arithmetic approval Boolean is supplied.

General inductive proofs retain each raw block and interpreted result at its
original position, exact list lengths, coordinate counts and both byte totals.
The whole corpus inherits full coordinate coverage from the actual schema plan.
Missing, additional and reordered references cannot be hidden by an equal count.
Leaf IDs must be distinct. Manifest identity is checked against the full original
manifest domain preimage; the caller's chosen ID still requires independent trust.

`NativeManifestMerkle` parses lowercase content-ID hex into exactly 32 raw bytes.
Each node hashes the original004 Merkle domain, NUL, then the two raw digests in
order. The last node is duplicated at odd levels; a singleton retains its digest;
an empty tree rejects. Thirteen fuel steps suffice for the intended <=4096 leaf
shape; exhaustion rejects. General Layer/Tree relations retain every executed
pair and level, with proved output-count halving and pair digest sizes. This is
an exact executable recurrence under the hash adapter, not a collision-resistance
or SHA implementation proof. The singleton and odd-tail conventions are preserved.

## Source and authentication boundary

Original manifest: 2198 bytes, five blocks, 36 coordinates, 72 payload bytes and
4798 envelope bytes. Native fixture bytes, receipts and original sequences stay
unchanged. The generator independently runs the pinned Python resolver and real
Python SHA before emitting fixtures. Neither this nor a synthetic exact-preimage
Lean hash adapter authenticates a native exporter, producer, execution or source.
The hash adapter remains UNVERIFIED. In particular, a function returning expected
IDs is not a proved SHA implementation; no native cryptographic identity is claimed.

The manifest's original parent checkpoint preimage is absent. The domain, ticket,
aggregation count, parent, configuration and proof fields are retained and checked
for local shape/link consistency; their independent authorization is NOT derived.
Actual configuration/proof bodies and parent/commitment/AC/ISC/EC/APC/availability
trust must still be joined. A complete locally supplied corpus is not remote
availability or a durability receipt. The Python resolver's aggregate 8 MiB limit
is not silently advertised as a Lean/native aggregate allocation bound.

The prior per-block changed-payload counterexample remains valid for that older
API. This new corpus API additionally compares payload/leaf hash results, but
those checks only have cryptographic meaning under a verified hash implementation.
Negatives distinguish typed component relations from full byte decoding. Python
mutation tests explicitly bypass document resolution only to reach structural
checks; separate old-ID byte substitutions fail before any generator output.

Still open: verified SHA and authenticated source/configuration/proof/availability;
source-to-draft vector `LoadedRow`/`RowsBound`/`DerivedParameter`, complete current
model/optimizer/APPLY inputs; general public/native phase/QC/journal/send/current/
unknown/torn/repair recovery and `nativeArithmeticRecoveryRefines`; contract
freeze, clean offline reproduction and independent review. The separate native
certificate decimal canonicality failure remains unresolved. No native execution,
runtime guard change, local acceptance PASS, GO or independent attestation.

## Reproduction

```text
python formal/scripts/generate_native_manifest.py
python -m unittest discover -s formal/tests -p test_native_manifest.py -v
```

From `formal/proofs`, with the pinned toolchain:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeManifestBytes.lean
lake --no-cache env lean DeltaReduce/NativeManifestMerkle.lean
lake --no-cache env lean DeltaReduce/NativeManifestBinding.lean
lake --no-cache env lean DeltaReduce/NativeManifestVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Scoped checks do not claim aggregate `make formal-check` while make is absent.
