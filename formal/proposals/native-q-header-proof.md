# Original DRQ1 canonical header interpretation in Lean

T044/T048/T053/T054/T056/T057. Feature000 proposal only; **NO_GO** remains.
`NativeQJson`, `NativeQHeader` and the generated original examples are mandatory
Lean imports and axiom-audited. This is not `nativeArithmeticRecoveryRefines`.

## Actual byte input and general relation

The decoder receives bytes, consumes the exact ordered sixteen native-004 JSON
keys, parses canonical unsigned decimal numbers and unescaped ASCII strings,
then derives all header fields. It has no caller-supplied header, whole-body
translation or approval flag. The fixed schema rejects duplicate, extra, missing
and out-of-order fields, whitespace, wrong punctuation, wrong primitive types,
string escapes and unsupported schema/type constants. The whole computed
canonical header encoding must equal the original bytes.

This is a fixed-schema parser, not a general JSON implementation. Its string
subset follows the original native content-ID/token header contract. Generic
`readObject` takes contract-selected keys; it does not validate arbitrary keys
as a JSON schema. Native token validation uses ASCII alphanumeric plus `._/-`;
Lean uses that explicit class, with no claim about C++ locale/stdlib execution.
Numbers reject signs, leading zeros, fractions, exponents and values >=2^64.
Header size is bounded by 65536 bytes. These are list-level bounds, not a proof
of native allocation, stack or execution-time limits.

General proofs retain exact ordered field bytes, compute the four numeric
fields, establish parse/encode roundtrip and uniqueness, and derive the checked
count 1..524288, ordinal <4096 and element_start+count <=2^30. Segment offset is
uint64; offset+count is not checked by this header layer. Eight identifiers have
exact lowercase `sha256:` syntax; semantics/profile equal the original native-004
constants. These historical identities do not grant current formal authority.
Ticket and segment names have length 1..255 and exact token syntax.

`join` runs the existing DRQ1 frame/payload decoder and the new header decoder
and compares parsed count to actual decoded vector length. General lemmas retain
the payload byte relation, header preimage and two bytes per coordinate, and put
each global coordinate within the header's checked range. Source-schema segment
intervals, plan coverage and offset addition remain separate obligations.

## Original source and kernel checks

Reference commit `60c692f6e391f839829dfc64e93380db54cd507b` supplies the original
`canonical_header_json`/`read_shard` contract. The existing native-source boundary
pins the writer, reader and fixtures; an additional exact copy of
`delta-core-cpp/include/delta/shards/envelope.hpp` pins native integer field widths
(SHA256 `1d0466d5729c6a47dcea5a52fdf5b7e2de77f9e3a838e97096f1fb97f8640ec3`).
No source file or original receipt/envelope is rewritten.

All five original blocks keep their exact header/frame bytes and all 36 original
coordinates. Generated primitive byte proofs are shared across headers, then
composed with the general parser and frame lemmas. The kernel checks the source
encoding and complete joined decoding for every block. Twenty-eight small cases
cover malformed numbers/text/keys, numeric endpoints, constants/token/content-ID
syntax, and the remaining SHA gap. There is no native_decide or new axiom.

The framing-only non-JSON counterexample now rejects in the composed header API.
Changing the first Q coordinate while retaining its old header **still passes**
the Lean join: payload SHA is not verified here. That deliberate kernel
countercheck is paired with the existing Python `read_drq1` rejection
`PAYLOAD_HASH`. A content-ID spelling check is not hashing or authentication.

## Unresolved scope

Native `read_shard` checks a separately expected header, recomputes payload SHA
and derives a leaf identity. None of those source-authority steps is established
by this decoder. Pinned files authenticate fixture selection within the repo,
not an independent native producer/exporter. Domain-separated leaf/manifest
identity, SHA implementation, original schema/plan/quantum/APC weights and the
source-to-`LoadedRow`/`RowsBound`/`DerivedParameter` composition remain open.
The Python original-to-draft projection is not that kernel composition.

Full public/native reachable phase/QC/send/current and unknown/torn/repair/WAL
recovery, arbitrary snapshots, original current/model/optimizer/APPLY profile,
contract freeze, clean offline reproduction and independent review remain
mandatory. The existing native certificate decimal -00/-01 canonicality failure
is a different codec and is not fixed by this unsigned-header parser.
No native/TLC/mutant execution, runtime change, local PASS, GO or attestation is
claimed. Retained bounded checks keep their earlier scope.

## Reproduce

Use the repository-pinned toolchain and Python dependencies:

```text
python formal/scripts/generate_native_q_header.py
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeQJson.lean
lake --no-cache env lean DeltaReduce/NativeQHeader.lean
lake --no-cache env lean DeltaReduce/NativeQHeaderVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
cd ../..
python -m unittest discover -s formal/tests -p test_native_q_header.py -v
python formal/scripts/check_lean_evidence.py
```

The last command still fails for the missing general recovery conjunct, 44/45.
Machine evidence: `formal/proposals/evidence/native-q-header.json`. Scoped checks
do not substitute for aggregate `make formal-check` when make is unavailable.
