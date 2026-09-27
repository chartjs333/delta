# Original scale-table bytes and Q quantum binding (candidate)

T044/T048/T053/T054/T056/T057. Formal proposal only. NO_GO.
Evidence: `formal/proposals/evidence/native-scale-binding.json`.

## Relation established

`NativeScaleBytes.lean` parses the original004 canonical scale-table JSON bytes,
including the ordered array of nested segment/quantum records. It consumes exact
keys and punctuation; numerator is a decimal string, denominator a JSON number.
No decoded table, caller-supplied quantum or approval Boolean is an input to the
byte decoder. General component lemmas establish parsing/encoding roundtrip,
exact complete canonical preimage, encoding uniqueness and retention of the
entire ordered segment list. Parsing is bounded to 65536 segments and 4 MiB.
These are proposal bounds, not a native allocation/stack safety theorem or
equivalence with all native admission bounds. The grammar uses unescaped ASCII
text from the existing header decoder; it is not a general JSON implementation.

`NativeScaleBinding.lean` interprets actual parsed decimal fields. Every segment
has a positive count, bounded start/end/ordinal, token name and positive reduced
uint32 numerator/denominator. Table checks require historical source semantics
and profile, version/type, schema content-ID syntax, unique names, consecutive
ordinal/start layout and the exact total. General lemmas preserve every original
segment and derive the total from the list. These internal layout checks do not
decode or validate the referenced parameter schema, its shapes/omissions/aliases,
or a shard plan. The table could still be internally consistent but incompatible
with that source graph.

`bind` actually decodes scale bytes and invokes the preceding complete DRQ1
header/vector decoder. It selects a segment by the parsed header's exact name,
checks shared semantics/profile/schema, offset+count within that segment and
global start = segment start + offset. Its quantum comes from this selected
original segment. General lemmas prove the exact parsed numerator/denominator,
positive reduced fraction, original list membership, every coordinate's segment
range/placement and preservation of the complete signed INT16 payload relation.
This adds the offset+count check which the previous header layer left open.

## Explicit hash and authority boundary

The scale ID check evaluates a supplied `Bytes -> Bytes` hash adapter on
`ASCII("deltareduce.004.scale-table.v1") || 00 || original canonical bytes`.
Its output is the header's `sha256:hex` spelling. The general theorem retains
this exact preimage/equality; it does **not** prove SHA256, collision resistance,
adapter correctness, source selection or native exporter authentication. The
fixture adapter recognizes one pinned preimage and returns its pinned ID. That
finite synthetic function cannot authenticate any producer or arbitrary input.
The separately run Python source resolver recomputes real SHA256, but it is not
a Lean SHA implementation proof. Historical semantics/profile constants do not
authorize the candidate runtime.

The original input boundary is reused without rewriting native artifacts:
`formal/proposals/evidence/native-source-artifacts/native-source-boundary.json`.
The pinned scale table has 643 bytes, ID
`sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205`.
It has decoder.bias (4 elements, 1/4) and embedding.weight (32 elements, 1/16).
Five existing original DRQ1 blocks retain every one of the 36 coordinates.

## Kernel examples and limits

`NativeScaleVectors.lean` is generated from the independently pinned original
source bundle after the existing full Python resolver checks it. Component
lemmas establish the actual scale byte decode and compose it with all five
previous actual Q byte/header decodes, selected segments and ranges. There is
no large new fixture corpus or whole native-state reduction.

Thirty-two small cases include malformed nested JSON/key/number cases, typed
quantum/range/layout guard failures, empty-list bounds and the retained hash
counterexample. Not all of these are end-to-end byte-to-bind negatives: their
theorem statements expose the component being tested. A changed first Q value
with the old payload-SHA header still passes the composed Lean scale binding;
the actual Python `read_drq1` rejects `PAYLOAD_HASH`. Quantum parsing therefore
does not establish payload authentication or native shard admission.

Still required: verified payload/leaf/manifest/scale hashing; original schema,
plan, manifest, proof/configuration and APC/availability source graph; full
source-to-draft canonical artifact/identity projection and actual
`LoadedRow`/`RowsBound`/`DerivedParameter` composition. Original vector widths,
ordering and zero/duplicate coordinate values cannot be collapsed to scalars.
Model/optimizer/APPLY profile, phase/QC/current/send/recovery, arbitrary initial
snapshots and authenticated unknown/torn/repair observations remain separate.
No `nativeArithmeticRecoveryRefines`, native execution, local acceptance PASS,
GO, independent attestation or runtime guard change is claimed here.

## Reproduction

From the candidate repository root, with the pinned toolchain:

```text
python formal/scripts/generate_native_scale_binding.py
python -m unittest discover -s formal/tests -p test_native_scale_binding.py -v
```

From `formal/proofs`:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeScaleBytes.lean
lake --no-cache env lean DeltaReduce/NativeScaleBinding.lean
lake --no-cache env lean DeltaReduce/NativeScaleVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

All new named declarations, including `Bound.quantum`, are audited in the
mandatory root; only standard kernel axioms are allowed. Regeneration evidence
compares every retained generated artifact byte-for-byte. The final report
binds the new semantic sources but remains NO_GO. Missing GNU make means these
scoped runs do not claim the aggregate `make formal-check` gate.
