# Original DRQ1 byte framing and INT16 vectors in Lean

T044/T048/T053/T054/T056/T057. Feature000 proposal only. **NO_GO** remains.
`NativeQBytes.lean` and its generated examples belong to the mandatory Lean
build and axiom inventory. They do not discharge `nativeArithmeticRecoveryRefines`.

## What is computed and proved

The decoder receives the original byte list. It consumes the eight-byte
`DRQ1`, major1/minor0 prefix and two four-byte little-endian lengths; splits the
opaque header and payload; and consumes successive low/high byte pairs as
signed INT16 coordinates. It never receives an expected vector or approval flag.
The `0x8000` encoding (-32768) rejects. Zero and repeated values are retained.

The general proofs establish little-endian read/encode roundtrip, the exact
low/high-byte formula, soundness and completeness of the ordered payload
relation, uniqueness for the same bytes, two bytes per coordinate, every
coordinate's byte position, and the inclusive [-32767,32767] range. An odd byte
count and a forbidden pair reject. The payload relation composes across adjacent
byte blocks without sorting or losing coordinates.

Framing permits 1..65536 header bytes and 1..1048576 payload bytes, checks the
exact total length, and rejects trailing/truncated data. Accepted frames preserve
the complete canonical *binary framing preimage*: prefix, encoded lengths,
opaque header and payload. General frame roundtrip follows compositionally from
the actual payload decoder, positive bounded lengths and little-endian lemmas.
Accepted payloads are nonempty and even, with exact total frame size and indexed
coordinate extraction. These are representation/resource checks, not a proof of
the complete native `read_shard` validator or its machine-memory behavior.

## Original bytes and kernel examples

`generate_native_q_bytes.py` uses the existing independently pinned source-file
inventory (`generate_native_source_artifacts.originals`), native reference commit
`60c692f6e391f839829dfc64e93380db54cd507b`. All five original004 envelope/header/
payload preimages and their original leaf IDs remain intact. Their 36 coordinates
have shard lengths 4,8,8,8,8. Python independently verifies the original full
preimages and JSON/payload-hash relationship before generating component proofs.
That source pin authenticates fixture selection within this repository; it is
not an authenticated native producer/exporter.

The generated Lean module proves header/payload lengths, actual payload results,
the original binary framing identity, and full frame decoding for each block.
It uses compositional lemmas instead of a large reduction of combined native and
public states. Small kernel examples cover signed endpoints, byte order,
zero/duplicate retention, odd/missing/truncated/trailing bytes, magic/version and
resource bounds. There is no `native_decide` or new axiom.

Two positive counterchecks deliberately delimit the result: non-JSON header
bytes pass the framing decoder; changing the first original Q coordinate while
retaining its original header also passes this layer. The existing Python
`read_drq1` rejects that second input with `PAYLOAD_HASH`. Thus this Lean layer
cannot be used as source admission, SHA validation or a replacement for the
existing Python source relation.

## Remaining boundaries

The header remains opaque in Lean. Canonical JSON decoding, duplicate/unknown
field rejection, header field interpretation, payload SHA and domain-separated
leaf/manifest identities still need a substantive checked relation. No claim is
made about native code equivalence, signed producer data, configuration authority,
worker quantization, schema/partition/quantum metadata, APC weights or accumulator
proofs. The connection from these decoded vectors to `NativeBinding.LoadedRow`,
`RowsBound`, `DerivedParameter` and actual reachable admission/recovery remains
open. The previous Python original-to-draft projection is not a kernel proof of
that connection.

All phase/QC/current and unknown/torn/repair obligations, original model/optimizer
and full APPLY-profile provenance, general native codecs/hash/exporter/WAL,
arbitrary initial snapshots, contract freeze, clean offline reproduction and
independent review remain required. No runtime source, native arithmetic guard,
frozen demo ref, qualifying BenchmarkResultQC or GO checkpoint changes here.

## Reproduce

Use the repository-pinned Lean toolchain and Python dependencies:

```text
python formal/scripts/generate_native_q_bytes.py
cd formal/proofs
lake --no-cache build DeltaReduce
lake --no-cache env lean DeltaReduce/NativeQBytes.lean
lake --no-cache env lean DeltaReduce/NativeQBytesVectors.lean
lake --no-cache env lean DeltaReduce/AxiomAudit.lean
cd ../..
python -m unittest discover -s formal/tests -p test_native_q_bytes.py -v
python formal/scripts/check_lean_evidence.py
```

The last command is expected to fail on the existing missing general recovery
conjunct (44/45). It must not be represented as a full formal PASS. Evidence:
`formal/proposals/evidence/native-q-bytes.json`. No fresh TLC, native runtime,
production mutant, independent attestation or aggregate `make formal-check` is
claimed by this stage.
