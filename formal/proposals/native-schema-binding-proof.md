# Original parameter-schema bytes and exact scale coverage (candidate)

T044/T048/T053/T054/T056/T057. Formal proposal only; **NO_GO**.
Evidence: `formal/proposals/evidence/native-schema-binding.json`.

## Actual byte and shape relation

`NativeJsonSequence` provides bounded fixed-grammar comma-separated sequences,
quoted ASCII text and unsigned decimal scanning. General lemmas prove sequence
roundtrip and count bounds. This is not a general JSON or native allocation/stack
safety proof. `NativeSchemaBytes` uses it to parse all four original schema fields:
omission policy, every ordered parameter (dtype, name, shape and Boolean trainable),
version and every alias/owner pair. Arrays and alias maps retain order and
multiplicity until interpretation; duplicates are not silently collapsed.
The decoder checks the complete canonical preimage and trailing bytes. General
component roundtrip/uniqueness proofs consume actual bytes, not a supplied
decoded schema or translated body.

`NativeSchemaBinding` parses every dimension, checks the four original logical
dtypes, positive dimensions, rank at most32 and shape product at most2^30. Scalars
have empty shape and product1. Names obey the original ASCII256-character rule;
included native segment names additionally obey the original004255-character
token limit. These resource/representability restrictions are explicit proposal
guards, not a claim that all native/worker admission limits are identical.

Every original parameter remains in the parsed source. `OMIT_FROZEN` filters only
the derived segment sequence; `INCLUDE_ALL` retains frozen parameters there too.
Parameters are ordered and unique. Alias keys are ordered and unique, obey the
name rule, cannot collide with parameters, and must name an existing parameter
owner (including an omitted owner where the original schema permits it).
Empty included schemas and total size above2^30 reject.

The checker derives each segment's exact name, ordinal, product count and prefix
offset from the included parameters. It compares the **entire ordered segment
list** and total with the actually decoded scale table. General lemmas retain
all original parameter records/dimensions, included order, count and every
indexed prefix placement. No expected segment list is supplied as authority.

`bindQ` composes this source schema/scale relation with the preceding actual
scale/header/vector byte decoder. It proves the selected scale segment is in the
schema-derived rows, retains shape-source provenance and each Q coordinate's
range. It does not yet parse or check the original shard plan or manifest, so it
cannot establish complete/nonoverlapping coverage by an arbitrary set of Q blocks.

## Identity and provenance remain separate

The schema content ID hashes its exact canonical JSON bytes directly, with **no
domain prefix or NUL**. The scale table uses its original004 domain plus NUL. The
general checker retains these different preimages under an explicitly supplied,
UNVERIFIED `Bytes -> Bytes` adapter. Its two-preimage fixture adapter is synthetic,
not a Lean SHA256 implementation, cryptographic proof or producer authentication.
The existing Python resolver independently computes actual SHA; this does not
discharge the kernel/native hash/exporter obligations. Original schema IDs are
not silently equated with draft arithmetic SCHEMA/Q_SHARD IDs.

The reused independent fixture boundary is
`formal/proposals/evidence/native-source-artifacts/native-source-boundary.json`.
The original schema preimage has376bytes and ID
`sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239`.
The preserved source fixture file includes a terminal LF; it is excluded from
the fingerprint exactly as the original `ParameterSchema.fingerprint` contract
requires. No source file, original Q artifact, receipt or sequence is rewritten.

## Examples, counterchecks and remaining work

The generated module proves actual schema decoding, all three original parameter
records, the omitted frozen scalar, alias preservation, both included segments
and the composed relation for all five previous original Q blocks/36coordinates.
Thirty-five small cases distinguish byte grammar failures, typed shape/name/
policy/alias/coverage guards and the retained payload-hash countercheck. They are
not all end-to-end decoder negatives. Substituting a same-sized name, changing
the shape, including the previously omitted frozen parameter or appending a
scale segment fails the appropriate whole-list relation. Name256 is valid at
the schema layer but rejects as an included native token; name257 rejects.

Changing the first Q with its old SHA header still passes this composed Lean
schema relation and fails the existing Python `PAYLOAD_HASH` check. Therefore
this stage does not authenticate Q bytes or complete native admission. Still
required: verified SHA, original plan/manifest/config/proof/APC/availability
graph, source-to-draft identity and actual `LoadedRow`/`RowsBound`/
`DerivedParameter` composition, current model/optimizer/APPLY identity and the
full phase/QC/current/journal/unknown/torn/repair recovery relation. The separate
native certificate decimal canonicality failure remains unchanged. Contract
freeze, clean offline reproduction and independent review also remain open.

No `nativeArithmeticRecoveryRefines`, native execution, runtime guard change,
local PASS, GO or independent attestation is claimed.

## Reproduction

At repository root:

```text
python formal/scripts/generate_native_schema_binding.py
python -m unittest discover -s formal/tests -p test_native_schema_binding.py -v
```

From `formal/proofs`, with the pinned Lean toolchain:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeJsonSequence.lean
lake --no-cache env lean DeltaReduce/NativeSchemaBytes.lean
lake --no-cache env lean DeltaReduce/NativeSchemaBinding.lean
lake --no-cache env lean DeltaReduce/NativeSchemaVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Mandatory root imports and the axiom audit include every new named declaration,
including dotted helper definitions. Reproduction evidence compares all retained
generated files byte-for-byte. Scoped checks do not claim aggregate
`make formal-check` while GNU make is unavailable.
