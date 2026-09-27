# Original Q-source preimages and the unresolved certificate identity bridge

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
This formal-tooling stage changes no native implementation, TLA module, Lean
source or public trace schema. The existing semantic identity is unchanged.

`native_source_artifacts.py` defines the proposed
`deltareduce.original-q-source.v1-candidate` relation. It accepts a separately
chosen original contribution-manifest content ID and a byte store. It resolves
the exact original manifest, configuration, fixed-point profile, parameter schema,
scale table, shard plan, accumulator-proof record and every ordered DRQ1 leaf.
Every resolution rechecks its kind-specific hash domain and exact preimage. The
schema fingerprint uses raw canonical JSON SHA; the 004 artifact domains insert
NUL before the payload. These identities are never equated to the differently
encoded draft arithmetic graph's IDs.

The resolver derives included tensor segments from the complete schema, shapes,
trainable flags and omission policy. It retains frozen parameters and aliases in
the original source bytes; it does not invent another coordinate naming scheme.
Included segment names obey native004's255-character token bound even though
the earlier worker schema permits256 characters. That boundary is checked.
It computes the full shard partition from those segments and the source-bound
target payload size. It checks the scale table's exact segment positions and
positive reduced uint32 quanta, all shared configuration/profile/schema/scale/proof
links, exact ordered manifest coverage, byte totals and the original Merkle root.
No caller supplies an expected complete shard header or expected Q vector.

DRQ1 parsing checks the actual 16-byte little-endian prefix, version, inclusive
64KiB header and 1MiB payload bounds, exact total length, nonempty even payload,
canonical ASCII JSON, duplicate keys, payload SHA and signed little-endian INT16
coordinates. The forbidden -32768 value rejects. Expected headers are constructed
from the independently resolved manifest/configuration and computed full plan;
all fields must match byte-for-byte, including original ticket, ordinal, segment
offset, schema, proof and complete source links. No receipt, envelope or artifact
is rewritten or normalized to obtain acceptance.

The stricter proposal resource profile additionally limits each JSON source to
4MiB, depth32, 250000 items, schema rank32 and total resolved bytes to8MiB. These
are tooling/representability limits, not newly asserted native admission limits.
The low-level `read_drq1` only decodes an envelope; `resolve_q_source` is the
source/context composition. Native `validate_opaque_shard` is weaker than native
`read_shard`; no equivalence to either C++ entry point is proved here. Python
JSON/int/struct/SHA execution is tested, not kernel-proved native decoding.

## What was resolved, and what was not

Seventeen source/fixture files are retained byte-exact from native commit
`60c692f6e391f839829dfc64e93380db54cd507b`, with a separately pinned boundary
manifest. Original004 golden fixtures contain twelve resolvable original objects:
seven JSON objects (including the separate parameter schema) and five DRQ1 leaves.
Their 36 decoded coordinates equal the original fixture's complete Q list.
The schema fixture's terminal file newline is excluded from its published
canonical JSON preimage, following `ParameterSchema.fingerprint`; the file itself
is preserved unchanged. No actual native execution/export is newly claimed.

The original008 golden certificates do **not** refer to this source graph:

- parameter schema, arithmetic profile and RoundConfig use different placeholder
  IDs; the APPLY profile references an absent accumulator-proof ID;
- all twelve `input_leaf_ids` are SHA of descriptive fixture labels, as confirmed
  against the original generator, with no DRQ1 preimages in the retained store;
- original004's base RoundConfig and parent checkpoint still lack preimages in
  that store. Their content-ID syntax cannot authenticate either authority.

The generated evidence records each original ID and exact label provenance.
Absence is scoped to the retained fixtures, not a claim that a preimage could not
exist elsewhere. Neither original fixture is modified. Supplying the valid004
objects under008's IDs fails hash resolution. Replacing008 IDs and rehashing all
certificates would construct a new synthetic history, not recover the original.

The resolver retains accumulator proof bytes and checks its configuration input
links/selected width. It does **not** validate declared product/prefix bounds,
headroom, theorem names, proof result or referenced Lean authority. In particular,
`result=PASS` is never used as approval. A content-only countercheck retains an
untrusted result string; that does not pass native proof-instance admission.
Worker quantization's ties-to-even and reduce/apply's half-toward-positive rounding
are different stages; they must not be silently conflated or treated as a defect
solely because their names differ.

## Required independent source boundary

A future original-to-draft bridge must bind a versioned source manifest outside
the candidate command. That manifest needs the immutable producer/build/source,
environment/run/position, original native snapshot and configuration identity,
exact complete original object IDs/lengths/preimages and the independently held
current model/optimizer. Its source must authenticate how those values were
obtained. This tooling version supplies **none** of that authentication.

For each committed native leaf the bridge must resolve the actual immutable
ticket/commitment/AC/ISC/EC/APC chain, derive domain/shard/range/quantum and Q values
from the original preimages, and bind the draft graph by explicitly checked keyed
primitive relationships. No whole-body translator, arbitrary aliases or finite
approval table may supply the missing relation. Schema coordinate names, original
segment/shard IDs and draft symbols have not yet been related. PARAMETER admission
must remain possible before a later aggregate; no later result may define its
input authority. APPLY must retain all leaves and exact model/optimizer parents.

A test deliberately rehashes a changed Q vector into a different valid manifest.
Content validation accepts that **new** source identity. It cannot establish that
the new identity was authorized by the original recovered snapshot. This keeps
the authentication gap visible instead of hiding it behind a checksum.

## Reproduction and limits

Run `python formal/scripts/generate_native_source_artifacts.py` and
`python -m unittest discover -s formal/tests -p test_native_source_artifacts.py -v`.
Evidence: `formal/proposals/evidence/native-source-artifacts.json`; generated
original byte/ID/coordinate inventory: `formal/proposals/native-source-artifact-vectors.json`.

The mandatory Lean audit remains44/45, with `nativeArithmeticRecoveryRefines`
missing. No Lean theorem, native run, TLC path or production mutant is newly
claimed. Full proof-bound/authority/graph identity, original phase/QC/current and
public state composition, physical WAL/unknown/repair, exporter/SHA/codec proofs,
arbitrary snapshots, freeze, offline reproduction and independent reviews remain
required. This stage grants no local acceptance PASS, BenchmarkResultQC or GO.
