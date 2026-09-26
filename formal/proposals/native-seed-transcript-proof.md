# Exact native seed transcript and finalized ISC edge

T044/T048/T049/T053/T057/T060; amendment0001 proposal. Formal/native authority
remains **NO_GO**. This stage does not widen CONFIG/proposed-ISC admission modes.

## Checked relation

`NativeSeedTranscript` parses all fields of the original DVPOL `fmtSeed` tree:
full context, ISC certificate ID, primitive seed ID, seed profile ID, ordered share
IDs. Its byte entry uses the exact bounded decoder and proves reencoding of the
entire original wire. It checks original context, content-ID spellings and a
nonempty, bounded, strictly ordered share vector. Every share is retained.

All 14 canonical native JSON fields are computed, including original native
semantics/schema/type. The transcript ID hashes the existing native
`deltareduce.008.seed-transcript.v1`, NUL and those exact bytes. Digest length
must be 32. The primitive `seed_id` field and computed transcript ID are different
identities; neither is the ISC QC ID or the ISC voted-body ID. The parent must
be the exact ISC **QC** ID. These distinctions are checked in actual examples.
Pure serializers and low-level shape checks establish no cryptographic authority.

The low-level `check` takes a finalized-ID vector; alone that argument has no
provenance. `linked` additionally computes the actual ISC certificate result and
checks the exact seed edge to its QC ID, but does not prove its finalization.
The composed `NativeSeedSection.bindSection` first runs the actual
`NativeFinalizedIscSection.bindSection`, then extracts and checks the entire
original seed vector against that result's finalized IDs. It rejects duplicate
or unordered computed transcript IDs. No caller-supplied whole translation,
arithmetic/admission Boolean or assumed recovered-state equality is used.

General lemmas derive original seed list/order/count, exact context and a checked
original ISC certificate witness for **every** seed's finalized parent. `prepare`
composes original full policy/state byte readers with these two section checks.
Their acceptance does not establish the later graph, whole-policy admission,
production finalization provenance, current-state behavior or recovery.

## Retained original components and tests

Read-only native reference is `60c692f6e391f839829dfc64e93380db54cd507b`.
The existing ISC generator verifies source/harness/extraction/native observations;
this generator separately pins the complete native-policy observation. It decodes
the unchanged `codec-EC` policy, requires exact section occurrence/reencoding,
and checks the complete seed JSON against independent retained native output.
Its ISC parent must equal the computed original certificate ID and occur in the
original policy's finalized set. Rehashed substitutions cannot inherit these pins.
This is fixture consistency, not an authenticated native exporter.

Generated kernel proofs retain actual original seed JSON/wire and compose both
computed sides of the original ISC-to-seed edge. Three finite SHA samples cover
ISC QC, ISC voted body and seed transcript; the previous certificate/SHA function
is not accepted as a new generalized hash implementation. Component lemmas avoid
reducing a whole native/public state graph. Negative cases cover missing/unfinalized
parent, substituted body/transcript IDs, altered parent/context/profile/seed,
empty/duplicate/malformed shares, duplicate transcript IDs and failed hashing.
The full section has general proofs but no new whole-policy/state acceptance
fixture in this stage. The original component pair is not an event/phase history.

A deliberate countercheck changes the primitive seed to another well-spelled ID
and still passes the shape predicate. That predicate does not authenticate seed
randomness, beacon shares, signatures, ledger freeze or root preimages. Hashing
would bind changed bytes to another transcript; it does not supply missing trust.

## Limits and next work

The seed/share/profile IDs remain primitive inputs. Native payloads contain share
IDs, not a randomness reconstruction proof or cryptographic signatures. Configured
committee, finalization flags, initialization and snapshot/export origin retain
prior unresolved provenance. No seed finalization event, network delivery, arithmetic
execution or physical WAL recovery is added. The 4 MiB byte entry and 100000-share
vector bound are explicit profiles; general JSON/native language equality and
SHA are unproved. Existing candidate modes still reject finalized/later graphs.

Next bind original norm evidence and complete EC membership with exact finalized
ISC/seed parents, then APC coverage and all admission/replay sections. EC's
certificate JSON omits the seed edge; native finalized metadata supplies it
separately. Preserve this distinction. General DRS1 decoding, arbitrary snapshots,
unknown outcomes/repair, physical scan completeness, public/native refinement,
`nativeArithmeticRecoveryRefines`, contract freeze, offline reproduction and
independent review remain mandatory. Missing response never proves absence.

No runtime/guard/demo/frozen-ref edits, new native execution, TLC or production
mutants are claimed. Retained finite scopes remain unchanged. Full/local GO and
BenchmarkResultQC are absent. GNU make is unavailable; scoped checks are not
aggregate `make formal-check`.

## Reproduce

```text
python -X utf8 formal/scripts/generate_native_seed_transcript.py
python -X utf8 -m unittest discover -s formal/tests -p test_native_seed_transcript.py -v
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeSeedTranscript.lean
lake --no-cache env lean DeltaReduce/NativeSeedSection.lean
lake --no-cache env lean DeltaReduce/NativeSeedTranscriptVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
```

Final counts, source hashes and outputs are in `evidence/native-seed-transcript.json`.
Mandatory check remains 44/45 with the full recovery theorem missing.
