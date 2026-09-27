# Original Q preimages checked against native availability inputs

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
This stage adds `native_available_q.py` in the formal proposal layer and executes
an isolated unchanged native `InputLedger` component. It changes no runtime,
public schema, TLA or Lean source. It does not claim a native exporter, WAL run,
signature verification, complete frozen history or general recovery proof.

## What native InputLedger checks

At pinned native commit `60c692f6e391f839829dfc64e93380db54cd507b`,
`Commitment` contains only ticket and opaque commitment ID. `AvailabilityProof`
contains ticket, commitment ID, certificate ID, covered leaf IDs, attester IDs
and threshold. Neither structure contains a manifest ID or a commitment preimage.

For a fresh ledger, `record_commitment` checks configured ticket membership and
ID syntax. `record_availability` checks a matching recorded commitment, nonempty
strictly ordered ID sets, exact equality of covered and caller-required leaves,
configured threshold, enough distinct permitted attester IDs and certificate-ID
syntax. `freeze` returns original ticket/commitment/certificate triples. The
component does not derive required leaves from a manifest, recompute a commitment
hash, decode an AC preimage or verify attester signatures. Calling code must
establish those independent relationships. This is a boundary, not evidence that
an untrusted command can bypass the complete runtime admission policy.

## Bounded original-preimage relation

The NEW tooling envelope `deltareduce.available-q-observation.v1-candidate`
retains the native primitive inputs and a selected manifest content ID. Its
own NUL-separated hash domain is explicitly a formal proposal domain, not an
existing native wire format, snapshot ID or authenticated exporter record.
The only supported provenance value is `UNAUTHENTICATED_COMPONENT_INPUT`.
Unknown fields and claims of authenticated export reject. The root ID must be
supplied separately from its bytes, but source hashes alone do not authenticate
who selected that root, the recorded inputs or their original time/position.

`resolve_available_q` loads the entire original004 manifest/schema/scale/plan/
config/profile/proof graph and every DRQ1 preimage using the existing checked
source/accumulator relation. Native commitment/proof ticket IDs must equal the
manifest's original ticket. It derives the complete required leaf set from the
manifest. Schema/range order is retained in the original manifest and Q rows;
lexicographic content-ID order is derived separately for native coverage.
Missing, extra, repeated or reordered native leaves reject even if the caller's
required list and availability covered list agree with each other.

The observation profile inherits bounded canonical ASCII JSON, exact fields,
uint32 thresholds, positive quorum and the source limits; it additionally bounds
IDs to255 characters and lists to4096 entries. Native ID validation itself only
requires nonempty ordinary IDs. These are deliberately narrower tooling limits,
not proof of native parser completeness or all failure ordering. Empty sets
reject natively and in the helper. The API models a fresh commitment/availability
insertion followed by freeze, not replay/late/conflict history or physical WAL.

`resolve_plan_available_q` composes actual checked APC weights with every
eligible input observation in original ticket order. It compares each derived
native triple to the original APC/ISC source row and checks original domain,
schema, actual proof and configuration identities. It retains all source bytes,
rejects missing/extra/reordered/duplicated inputs and bounds the total distinct
resolved bytes. Rejected ISC members remain in their full original certificate
preimages but their Q payloads are outside this accepted arithmetic corpus.
No later PARAMETER/aggregate/APPLY is required. The separate APPLY profile edge,
parent/current authority, cross-ticket source compatibility and the draft graph
projection are not silently supplied by this helper.

## The commitment/provenance gap remains visible

There is deliberately **no invented equality** between native commitment ID,
manifest ID and manifest Merkle root. In the native reference those identities
are different input fields without the required serialized source binding.
The relation retains both the opaque native commitment and exact manifest root.
A countercheck replaces the native commitment and AC IDs consistently and still
passes the primitive/content relation. The APC-composed API rejects a replacement
against an unchanged original ISC tuple, but a wholly new rehashed synthetic
history is not thereby authenticated. This is not a newly accepted original run.

The example uses all twelve original004 source objects, five original DRQ1 leaves
and36 coordinates. The component input and APC are separately synthetic; their
context/ticket fields are constructed from that source explicitly. The original
native008 policy/certificates/envelopes and sequences5/6/8 are untouched. Their
missing source/proof IDs remain missing; none is replaced with this new example.
A second two-ticket test constructs separately named source bytes solely to
exercise complete corpus ordering and rejects duplicated/reversed observations.

## Fresh native component evidence

Ten exact native files are pinned, including headers, the original consensus
test source and four unmodified translation units: `consensus.cpp`,
`canonical.cpp`, `sha256.cpp`, `contracts.cpp`. The generator compiles those
whole source files with MSVC and a separate retained harness; no native function
is extracted, patched or stubbed. No generated binary is committed.

Seventeen cases compare accept/reject and exact frozen ticket/commitment/AC
triples with the bounded primitive checker. They include missing/reversed/
duplicate leaves, wrong commitment/ticket, invalid AC ID, unknown/duplicate/
insufficient attesters, threshold mismatch/zero and empty leaf sets. The actual
native component accepts a consistent **nonempty incomplete caller-required
leaf set**. The new original-Q resolver rejects it against complete source
coverage. Both native and helper accept arbitrary well-shaped opaque commitment
and AC IDs when the remaining primitives agree; no authentication is claimed.

An initial draft wrongly allowed empty native ID lists. The fresh C++ comparison
caught it; the helper and case name were corrected before final verification.
Self-review also found shared list storage in one negative-case constructor;
required and covered lists are now independent, with a regression test. The
final native run rejects removal from covered leaves alone and separately
accepts a mutually consistent nonempty incomplete required/covered pair.
The final result is the corrected comparison, not the superseded mismatch.
These are component counterchecks, not new production-source mutants or runtime
acceptance/recovery/availability-under-WAN measurements.

Reproduce:

```text
python formal/scripts/generate_native_available_q.py
python formal/scripts/generate_native_available_q.py --vcvars <vcvars64.bat>
python -m unittest discover -s formal/tests -p test_native_available_q.py -v
```

The exact compiler command, harness, source manifest, observations and logs are
retained under `formal/proposals/evidence/native-available-q`. The original MSVC
stdout log retains its trailing spaces and final blank line; only that raw log
is excluded from implementation whitespace lint. Python tests also
cover all observation/record fields, forged provenance, original source failures,
extra/incomplete matched lists, content hash/canonicality, manifest ticket,
APC source edges/domain/proof/count and two-ticket order. Semantics remains
unchanged because semantic inputs did not change. No new Lean proof/build or
TLC run is claimed; retained proofs/traces keep their earlier bounded scopes.

Next required work is a source-authenticated commitment/manifest/AC/config/current
boundary and an explicit original-schema/Q/weight-to-draft relation, then kernel
composition with actual admission and full public phase/QC/current/recovery.
The old native `InputLedger` has no missing serialization to infer by aliases.
Any new normative binding requires a versioned Feature000 proposal and review;
it cannot retroactively authenticate old captured IDs. General bounded codecs,
SHA/exporter/physical WAL/unknown/torn repair, arbitrary snapshots and failures,
`nativeArithmeticRecoveryRefines`, contract freeze, clean offline reproduction
and independent reviews remain required. Native arithmetic STOP is unchanged.
