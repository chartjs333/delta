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
