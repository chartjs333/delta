# Canonical formal evidence contracts

## Canonical JSON profile

Formal traces, source manifests and verification reports use UTF-8 JSON with:

- NFC-normalized strings and object keys;
- integers only (no floating point, `NaN` or infinities);
- no duplicate object keys;
- object keys sorted by Unicode code point;
- no insignificant whitespace and no trailing newline.

`formal/scripts/formal_artifacts.py` is the independent standard-library
implementation. Arrays retain protocol-defined order. Sets represented as arrays
(for example `parent_hashes`, `artifact_refs`, IDs and manifest paths) must be
sorted by ordinal value before encoding when their contract declares set
semantics.

## Formal semantics compatibility ID

The compatibility input is the complete sorted list of:

1. non-mutant `formal/tla/**/*.tla` modules;
2. `formal/proofs/DeltaReduce.lean` and `formal/proofs/DeltaReduce/**/*.lean`;
3. `formal/schemas/formal-trace.schema.json`.

Each entry is `{kind,path,sha256}`. The ID is:

```text
sha256:<SHA-256(canonical-json({
  "artifacts": entries,
  "domain": "deltareduce.formal-semantics.v1",
  "formal_semantics_version": version
}))>
```

Before each artifact hash is computed, CRLF and lone CR line endings are
canonicalized to LF; no other byte transformation is applied. This is the same
text profile used by the phase-0 input bundle and makes the compatibility ID
independent of Git checkout EOL conversion while preserving every non-EOL byte.

Renaming, adding, removing or changing any compatibility input changes the ID.
Mutants, finite TLC configuration bounds, evidence and the report schema are
bound separately by the report and do not silently change protocol semantics.

## Deterministic report decision

`formal_artifacts.determine_report_decision` returns `GO` only when all of the
following independently verify:

- a clean, content-addressed source manifest and exact compatible semantics ID;
- the frozen baseline input bundle;
- all four pinned toolchain records;
- every registered TLC config and proof obligation;
- all mandatory mutant classes and the complete refinement fixture boundary;
- coverage of `FR-001` through `FR-046` with no unresolved item;
- two distinct, independent technical reviews covering model, liveness, proofs
  and coverage;
- every referenced evidence node and graph edge;
- non-empty assumptions, abstractions and limitations.

Any missing, failed, duplicate, incompatible or hash-invalid mandatory item adds
a stable reason code and returns `NO_GO`. The offline verifier rejects a report
whose stored decision or reason list differs from the recomputed result. A
consistent `NO_GO` report is valid evidence, but `--require-go` rejects it for the
branch gate.

The report content address printed by the verifier is the SHA-256 of its exact
canonical bytes. It is kept outside the report payload to avoid a self-hash
cycle.

## Commands

```text
python -m unittest discover -s formal/tests -p "test_*.py"
python formal/scripts/verify_formal_report.py REPORT --root REPOSITORY
python formal/scripts/verify_formal_report.py REPORT --root REPOSITORY --require-go
```

The verifier performs no network access and imports no production package.

Candidate amendment 0001 adds `arithmetic_witness` to every trace event and
public `nativeSnapshot`/`nativeAnchor` definitions. This changes the semantic
compatibility ID even though the TLA transition relation is unchanged in this
checkpoint. For an implementation trace containing accepted PARAMETER/APPLY votes:

```text
python formal/scripts/check-refinement.py TRACE --native-evidence SNAPSHOTS --native-evidence-sha256 HEX
```

`HEX` must be obtained independently of the trace/command. Native evidence is
canonical ASCII JSON version `1.2.0` with `schema_version`, `snapshots`,
`artifacts` and `operations`; the
whole file is bounded to 4 MiB in this candidate. Each snapshot and artifact is
resolved and rehashed. See the refinement contract for the trust premise and
the remaining receipt/recovery/schema-projection obligations. The synthetic
fixture manifest is not an attestation of native provenance.

The candidate parameter-schema hash also covers the exact sorted `coordinates`
and per-obligation `ranges`. The checker derives native SCHEMA bytes solely from
this immutable contract, then compares the complete resolved native schema.
Per-domain coverage is exact; shard IDs cannot alias different intervals across
domains. See the candidate coordinate projection in the refinement contract for
the bounded flattened-vector profile and the remaining proof/adapter obligations.

Candidate durability observations add the required nullable `durability_witness`
event field and thus change the semantic compatibility ID. The referenced,
separately pinned operation records bind canonical projected receipt/effect bytes,
ordered persist stages and reconstructed per-actor journal prefixes. Exact retry
uses the original admitted record even after current advance/recovery; conflict
stutters without an append or sendable effect. The draft evidence encoding is
not a native ABI/WAL/receipt serialization or physical durability proof. See the
refinement contract for empty-journal scope, mapping and remaining crash cuts.

Evidence v1.2 adds persisted-but-unexposed prefixes, including complete records
surviving unacknowledged append or barrier failure. The public accepted vote
projects a durable internal action; null receipt/effect fields mean no output
was exposed. Exact replay after verified recovery exposes the original bytes
without another append. Unexposed votes cannot supply QC signer power. Complete
unacknowledged records require later verified recovery; absent/torn/unknown
write outcomes and rejected first admission are still unsupported by this
public witness extension. Native WAL decoding, fsync and provenance are not
established by these synthetic, separately pinned projections.
