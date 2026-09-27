# Original vector layout and exact draft artifact join in Lean

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-vector-artifacts-lean.json`.

`NativeVectorLayout.construct` derives all flat coordinates from the original
included schema rows, using `<parameter>:<ten-digit-offset>` and original shard
ordinals `s<ten-digit-ordinal>`. It checks complete global coordinate order,
strict label order, original local/global ranges, positive ordered shard coverage
and identifier representability. It never sorts values or renames conflicts.
The complete original schema/plan structures remain in the result, including
dimensions, dtype, frozen omission and tied aliases. The draft schema alone does
not encode all that metadata and is not claimed to be injective over it.

Names longer than117 characters and conflicts such as `a`/`a.b` are rejected by
this projection profile, not declared invalid at native admission. Original
parameter-name bytes must roundtrip through the checked ASCII spelling. General
theorems retain every coordinate's parameter and local/global offset, exact shard
partition and complete source metadata. Small guards precede coordinate expansion;
the generic typed helper is not a replacement for the original source loader.

`NativeVectorArtifacts` encodes the entire canonical draft SCHEMA and Q_SHARD
objects, including wrapper kind, all fields, reference kind/length, exact quantum
and every original vector element. The draft domain-separated hash preimage is
explicit and distinct from the original raw schema/DRQ1 preimages. Hash functions
remain parameters, not an implementation proof of SHA. Artifact payload and byte
constructors are low-level helpers; they are not authenticated object registries.

`loadImage` constructs the Q bytes/ref/contribution from an original slice, calls
the actual draft `loadRow` against the separate store and then checks both entire
raw-byte and typed-payload equality to the computed image. The usual committed-Q,
ticket/domain/shard/schema/quantum/width checks still run. Missing objects and
substituted raw bytes reject by general theorems. `loadImages` retains every
position and constructs real `RowsBound` for the exact original vector rows and
final APC weights, including zeros and original within-domain order.

`NativeVectorJoin.run` first calls the complete original `NativeVectorContext.bind`.
It constructs the layout/schema itself, invokes real draft `deriveParameter` and
original full-vector `reduce`, and checks complete frame coordinates/shards,
schema identity AND exact stored schema bytes, ordered contributions, loaded
rows, specific proof denominator and accumulator width. It loads every computed
Q image into the checked row relation. No supplied translated body, expected
numerators or approval Boolean provides the join. The numerator identity follows
from the two actual checked computations over the same derived rows; the existing
original-coefficient coordinate theorem then composes through that identity.
The returned derivation retains its actual `deriveParameter` equation.

The entry joins one selected domain/shard. It checks4096 coordinate/shard limits,
65536 coordinate-times-member cells,4096 assignment keys,4MiB per emitted artifact
and8MiB for the schema plus this selected assignment's Q images. It does **not**
yet enforce the Python profile's8MiB total across all domain/shard assignments or
prove native allocation/stack/time equivalence. Several final size checks occur
after construction. Narrow signed fraction/quantum/denominator/width restrictions
remain draft representability conditions, not native admission changes.

## Checked components and remaining boundaries

Examples reuse the actual original schema/shard/DRQ1 components:36 coordinates,
five shards, widths4/8/8/8/8 and their actual quanta/values. Complete1338-byte SCHEMA
and all five Q_SHARD byte arrays match the independent Python projection. Schema
assembly uses small field byte lemmas. Row membership metadata in these examples
is explicitly constructed component data, not authenticated historical source.
There is no new complete raw-source `run` kernel execution, native capture, source
attestation, recovery theorem, TLA/TLC run or production mutant in this stage.

Layout negatives cover missing/duplicate/reversed coordinates, wrong offsets,
shard ordering, name conflicts/length/ASCII; Q negatives cover schema kind/hash
length, missing vectors, out-of-range values and changed body bytes. The proof
inventory is mandatory and every new named declaration is axiom-audited.

This closes a conditional original-vector-to-draft-byte/input/parameter relation,
not native authority or the remaining `nativeArithmeticRecoveryRefines`.
The draft Binding's authenticated anchor/recovery/certificates remain explicit
external premises; `run` does not establish that those authorities represent the
original native current state. Full original context/ISC/EC/APC mapping, vote
contexts/deadlines, current model/optimizer and APPLY profile/quantum remain open.
Matching a parent string is not current-vector provenance. Typed primitive
availability observations, EC-seed/configuration provenance, producer/build/run
identity and missing original008proof/base/current preimages are not repaired.
ManifestID, commitmentID, Merkle root and ACID are still different identities.

General draft decoding/encoding injectivity, hash/exporter authentication, full
phase/QC/send/delivery/journal/current/crash/unknown/torn/repair/physical-WAL
composition, arbitrary initial snapshots and full-batch resource bounds remain.
The existing native certificate decimal `-00`/`-01` incompatibility, contract
freeze, clean offline reproduction and independent review also remain. Unknown
observations stay incomplete. No native guard, local acceptance PASS, qualifying
GO/BenchmarkResultQC or independent attestation is authorized by this work.
