# Original shard-plan bytes and derived exact partition (candidate)

T044/T048/T053/T054/T056/T057. Formal proposal only; **NO_GO**.
Evidence: `formal/proposals/evidence/native-shard-plan.json`.

`NativeShardPartition` computes the original004 greedy partition directly from
the preceding decoded schema's included segments. The target must be even and
between 2 and 1048576 bytes. Each segment starts at offset zero; each next count
is `min(target/2, remaining)`, its global start is segment start plus offset,
its payload is twice its count, and its ordinal follows all preceding shards.
The executable fuel limit is 4096 across the complete plan. Exhaustion fails;
it never returns a partially covered plan. Zero width cannot make progress.

General kernel proofs derive exact total, full coordinate coverage, positive
counts, ordered nonoverlapping intervals and strictly increasing ordinals.
They derive count <=524288, payload <=target<=1048576 and source segment
name/offset placement. These are general relations over the executable planner,
not a finite expected-result table or a native C++ execution proof. The source
contract is independently pinned `delta-core-cpp__src__shards__plan.cpp` in the
existing native-source boundary; runtime code is unchanged.

`NativeShardPlanBytes` parses the entire original canonical plan: its nine top
level fields and ordered six-field entry records. Numeric fields are unsigned
canonical decimals; metadata and segment names use the existing unescaped ASCII
grammar. It rejects extra/trailing bytes by checking the complete computed
canonical preimage. Generic sequence, roundtrip and encoding uniqueness lemmas
are reused. Limits are 4096 entries and 4 MiB; these list-level guards do not
establish native allocation, stack or execution-time equivalence.

`NativeShardPlanBinding` actually decodes schema, scale and plan bytes, parses
every numeric entry, computes the partition from the schema and decoded target,
and compares the entire ordered list. Each record's original decimal fields,
name and position are retained. Metadata binds historical semantics/profile,
schema ID, scale ID, version/type and exact total. No supplied expected plan,
translated body or arithmetic approval Boolean is accepted.

The per-Q composition decodes the original full DRQ1 block and requires its
ordinal to select the exact plan entry, including count, start, name, offset
and derived payload byte count. It also binds the complete decoded scale table
and exact plan-hash preimage. This proves a complete **plan** and membership of
each checked block; it does not establish that an arbitrary supplied corpus or
manifest contains every planned block exactly once.

## Source identities and retained gaps

The original plan has 1079 canonical bytes and ID
`sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1`.
Its hash preimage is ASCII `deltareduce.004.shard-plan.v1`, NUL, then those bytes.
Schema and scale retain their separate original hash conventions. The general
hash function remains an UNVERIFIED adapter. The fixture recognizes three
preimages and is explicitly SYNTHETIC, not verified SHA, source/exporter
authentication or current formal authority. Python independently recomputes
real hashes; it does not discharge that Lean/native obligation.

The original five shards and all 36 coordinates compose through existing byte
and schema component proofs. Twenty-three small cases distinguish parser,
typed metadata, computed partition and remaining SHA scopes. Missing, extra,
reordered, resized, shifted, renamed and relabelled records disagree with the
computed plan. Partial final chunks, zero/odd/oversized targets and exhausted
fuel are checked. Typed component checks are not advertised as full decoder
negatives. Changed Q with its old payload hash **still passes** this Lean join
and is rejected by the existing Python resolver. Original bytes are preserved.
Python partition mutation tests deliberately replace only the resolved plan
document to reach the arithmetic relation after the hash boundary; they do not
claim that those replacements have authenticated content IDs. A separate test
rejects changed original bytes under their old ID before generation.

Still open: complete manifest/leaf/header/config/proof/availability authority,
verified payload/leaf/manifest/SHA and independently authenticated source
boundary; actual source-to-draft `LoadedRow`/`RowsBound`/`DerivedParameter`
composition; current model/optimizer/APPLY and full public/native
phase/QC/journal/send/current/unknown/torn/repair recovery. The separate native
certificate decimal canonicality failure, contract freeze, clean offline
reproduction and independent review remain unresolved. No native execution,
runtime guard change, local PASS, GO or independent attestation is claimed.

## Reproduction

```text
python formal/scripts/generate_native_shard_plan.py
python -m unittest discover -s formal/tests -p test_native_shard_plan.py -v
```

From `formal/proofs`, with the pinned Lean toolchain:

```text
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeShardPartition.lean
lake --no-cache env lean DeltaReduce/NativeShardPlanBytes.lean
lake --no-cache env lean DeltaReduce/NativeShardPlanBinding.lean
lake --no-cache env lean DeltaReduce/NativeShardPlanVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Scoped checks do not claim aggregate `make formal-check` while make is absent.
