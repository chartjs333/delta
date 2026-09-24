# PO-AB1 typed graph proof boundary

Candidate amendment 0001, T044/T048/T049/T057/T060. This is a partial proof
checkpoint, not Formal GO or permission to change the runtime arithmetic guard.

`formal/proofs/DeltaReduce/ArithmeticBinding.lean` contains the mandatory
`DeltaReduce.nativeArithmeticGraphUnique` theorem. Two complete graphs anchored
to the same independently supplied authority must have exactly the same ordered
path domain and exact bytes/typed payload at every path, even when supplied by
different stores. Authority, current model, optimizer and profile are equal.
Schema, eligibility lists, plan tickets, ordered contributions, domain/shard
metadata and referenced Q shards are inside those recursively equal payloads.
The theorem establishes identity, not that every such graph satisfies arithmetic
or admission preconditions.

The proof first derives byte equality from the explicit collision premise and
the checked content IDs, then payload equality from deterministic decoding.
Induction over `Walk` proves equal endpoints. A second induction transfers every
path into the independently complete other graph. That converse completeness
step prevents accepting a graph containing only a subset of referenced inputs.
No result-equality or graph-uniqueness assumption is introduced. Unrelated cache
entries may differ. Shared children are allowed; cyclic graphs have no finite
`Complete` witness. Multiplicity and field/list ordering remain observable.

## Explicit premises and remaining instantiation

- `Codec` supplies content hashing, canonical-byte recognition, typed decoding
  and current-vector hashing. `Resolves` binds store lookup, full content ID,
  length, canonicality, decoded kind and typed outgoing edges.
- `CollisionFree` is a named cryptographic premise on accepted canonical bytes.
  It is not a proof of SHA-256. Content IDs here are byte lists; the native
  `sha256:hex` spelling and domain-separated hash adapter need refinement.
- `Trust` names independent native-anchor authentication, durable recovery and
  certificate authentication. `Binding` carries those premises explicitly.
  Their production predicates cannot be supplied by the untrusted command.
- The anchor's context and authority root bind the model/optimizer/schema and
  profile. Current value hashes and quanta are checked against that anchor and
  profile. An optional authenticated aggregate root binds the authority ID.
- The typed graph context covers round/height/view/epoch/deadline/parent. Actual
  role, logical-time admission, durable sequence/state-root production, parent
  QC validation, all parser ranges and arithmetic cross-field coverage checks
  remain in the concrete native/admission/refinement obligations. They are not
  silently discharged by equal graphs or assumed to follow from equal hashes.

The theorem is general over graph size and independent stores, but conditional
on those premises. The production native decoder/exporter/WAL relation is still
unproved. PARAMETER conversion, APPLY and recovery conjuncts remain missing.
Self-review is not an independent attestation.

## Source-linked finite witnesses

`formal/scripts/generate_native_graph_vectors.py` reads the pinned synthetic
`formal/fixtures/traces/native/normal-apply.json`. It checks draft canonical
bytes, domain-separated artifact digests and the native-oracle anchor, and maps
every payload field into Lean. The generated `NativeGraphVectors.lean` contains
the original artifact bytes as numeric `UInt8` lists: twelve nodes covering all
eleven artifact kinds, including two Q shards. Kernel `decide` checks each
resolution and every recursively required edge. A full `Binding` is constructed,
and collision freedom is checked over the finite codec's twelve accepted byte
strings. Thus the combined premises have a concrete finite witness rather than
only implications. This finite check says nothing about collisions outside the
table or production SHA-256.

The finite codec uses lookup tables, and the example's trust predicates are
explicitly `True`. This is non-vacuity/source-correspondence evidence, not a
general parser/hash proof or real signature/native execution. Separate kernel
proofs reject a missing Q node, an authority graph transitively missing that Q,
a wrong artifact kind, and substituted Q bytes under the original identity.
These are not TLC production-mutant executions. Five Python tests additionally
check byte-exact generation and rejection before output of corrupt, missing,
noncanonical or stale-anchor inputs.

Run from the repository root:

```text
python formal/scripts/generate_native_graph_vectors.py
python formal/scripts/generate_trace_fixtures.py
python formal/scripts/generate_native_graph_vectors.py
```

The Lean output must remain byte-exact after trace regeneration: it consumes
artifact bytes and native anchor values, never the public semantics-ID header.
Then run `lake --no-cache build DeltaReduce` in `formal/proofs`, followed by
`python formal/scripts/check_lean_evidence.py` from the repository root. The audit
must still fail overall while any mandatory PO-AB1 target is missing. A successful
project build alone must never upgrade the report to GO.
