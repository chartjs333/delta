# Native aggregate ROOT identity, coverage and Merkle computation

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO remains.**

This layer reads the original contracts.cpp, verifier.cpp, vote_admission.cpp,
vote_codec.cpp and consensus.cpp at pinned native source
60c692f6e391f839829dfc64e93380db54cd507b. Runtime sources are unchanged.
It advances the formal proposal's original native snapshot admission through
both ROOT proposal and certificate lists. APPLY/current and the complete
snapshot entry point remain open; closed admission modes are not widened.

NativeAggregateMerkle constructs the exact three-field canonical leaf JSON
(domain_id, parameter_shard_qc_id, shard_id), hashes it under
`deltareduce.008.aggregate-leaf.v1`, decodes the two generated 32-byte digests,
and hashes their concatenation under `deltareduce.008.aggregate-node.v1`.
Odd final elements carry unchanged; they are not duplicated or rehashed alone.
A singleton tree returns its one leaf hash. Empty and above100000 leaf inputs
reject. The earlier Python helper's4096 tool-profile cap is not substituted for
the native100000 bound. Parent-level lengths and strict decrease establish
termination for arbitrary finite admitted lengths, not just fixture sizes.

The strict hexadecimal helper is deliberately scoped to generated lowercase
SHA IDs. General byte/hex round-trip lemmas, including all256 UInt8 values in
the actual native nibble/shift/or formula, show that these generated inputs
use the native decoded bytes. Native digest_bytes itself checks only length
and prefix and is weaker on malformed input; no equivalence for arbitrary
malformed IDs or non-ASCII signed-char behavior is claimed. SHA is still an
explicit function whose successful outputs must have32 bytes, not a verified
cryptographic implementation. No caller supplies a complete Merkle result
or approval table to the generic checker.

NativeAggregateRoot preserves the complete original typed ROOT body/QC,
all18 canonical JSON fields, exact context, parents, full ordered leaves,
required keys, signers and threshold. Policy parsing and body encoding retain
all original bytes. Its identity computation recomputes the Merkle tree,
compares the stored root and applies the inclusive4MiB canonical certificate
JSON bound. The enclosing lineage checker supplies the shape/context/committee
checks; the raw identity helper alone is not a full validator. The distinct
vote-body hash retains context/APC/EC/ISC/leaves/Merkle/required keys and excludes
certificate signers according to the original consensus.cpp contract.

NativeAggregateLineage looks up the actual original ISC/EC/APC records and
requires their exact finalized IDs. It resolves EVERY leaf against the actual
finalized PARAMETER corpus, retaining original records, order and count.
Every selected shard is rechecked against the original expected context,
committee and exact root parent IDs; its complete bounded canonical JSON is
hashed again and must equal the leaf QC ID. Full required-key equality and the
per-position leaf/key/shard identities reject missing, extra, substituted,
duplicated or reordered coverage. No whole-body translation or arithmetic
approval Boolean is accepted. This is structural certificate validation, not
newly established signer authentication or arithmetic derivation.

Both proposed and finalized ROOT use the same coverage/parent checks. Proposed
ROOT uses the configured full committee synthetic certificate view already
used by native verify_root. Its certificate hash is distinct from the stored
vote-body hash. Finalized ROOT retains its actual signers and QC identity.
The source does not add stronger plan/EC internal-parent equality here; the
checked preceding sections and exact selected edges retain their original
mode-specific rules instead of silently inventing stricter native admission.

NativeAggregateSection executes NativeSizedParameterSection.bindSection,
retaining the checked prior payload witness and the full Bound.prior. It then
reads and checks all aggregate_root_bodies, aggregate_root_qcs and finalized
IDs; enforces strict computed identity order and the finalized subset; and
derives original lists, counts and checked PARAMETER provenance from successful
execution. The existing nine-group certificate bounds are preserved. Successful
preparation has actual decoded policy/state witnesses, not supplied accepted
state equality. Error ordering, allocation cost and whole native execution
are not proved by this pure relation.

Examples reuse the pinned original codec-AGGREGATE_ROOT and codec-APPLY records,
original ROOT canonical JSON/QC/body hashes, original PARAMETER and parent
records, and four retained native Merkle component observations for counts1..4.
The3-leaf observation tests odd carry. The generator first validates the entire
pinned original observation and byte-exact policies, then constructs finite SHA
samples for these actual preimages. Proposed synthetic certificate SHA is a
Python calculation and is explicitly distinct from a fresh native observation.
There is no new C++ run, full snapshot execution, TLC run or production mutant.
Component proofs compose actual ROOT checks in both modes, not a new full
native runtime/recovery trace. Native original arithmetic sequences5/6/8 and
all native witness bytes remain unchanged.

Independent native exporter/provenance, cryptographic signer/committee authority,
norm/Q/root/robust/coefficient derivation, and PARAMETER arithmetic/body binding
remain unresolved. The confirmed original native decimal-spelling defect remains;
this stage does not normalize or repair it. APPLY/current, separate proposedISC
size integration, general codec/JSON/SHA/stdlib equivalence, DRS1 decoding,
physical WAL/scan completeness, unknown outcomes/repair, full public64-state
refinement and nativeArithmeticRecoveryRefines still require completion.
Contract freeze, clean offline reproduction, independent review and exact merged
formal authority are required before runtime guard changes and qualification.
There is no local PASS or formal GO.

Reproduce the vectors with `python formal/scripts/generate_native_aggregate.py`;
run `python -m unittest discover -s formal/tests -p test_native_aggregate.py -v`.
The tests check byte regeneration, all18 source fields, original native identities,
source/policy substitution, exact matrix, odd-carry alternatives and mandatory
sized composition. `lake --no-cache build DeltaReduce` includes all five modules;
AxiomAudit names every new definition and theorem. Scoped checks are not claimed
as aggregate make formal-check while GNU make is unavailable and Phase0 is unfrozen.
