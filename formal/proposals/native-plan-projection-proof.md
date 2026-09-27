# Complete PLAN/APC construction from original prepared assignments

T044/T048/T053/T054/T056/T057; amendment0001. **NO_GO remains.**
Evidence: `formal/proposals/evidence/native-plan-projection.json`.

`NativePlanAssignments` derives every contribution from the original finalized
APC rational weight and eligible member, retaining the whole member/manifest
identity and the exact computed Q artifact at the original shard position.
It does not replace the rational weight with the scaled accumulator coefficient.
Each assignment retains every eligible original row in its domain and requires
the same full schema segment/offset/width/quantum shape. Its denominator is the
actual checked original proof denominator; its quantum is the actual decoded
original Q quantum. Vector widths are retained.

The assignment context comes from the original prepared PARAMETER body, loaded
through `NativeSizedParameterSection.bindSection`. The native preparation
contract takes this context separately from the certificate; APC alone does not
contain it. Exact original body context/APC/ISC/EC edges are checked. No later
aggregate, conversion or successful APPLY result is required. All existing
expanded-certificate size checks apply, including the original 4 MiB bound.
The prepared body is retained in full; no caller supplies its translation.

`NativePlanProjection` requires the entire original required-key matrix to equal
the computed domain/shard matrix, then compares all selected original prepared
bodies by full multiset equality. Duplicate, missing or extra original entries
cannot be hidden by matching only counts. Assignments preserve computed order;
the original prepared body enumeration may differ in order, explicitly through
`List.Perm`. Original section checks retain key/context uniqueness. Ordinal shard
labels and ASCII identifier checks are **projection restrictions**, not new
native admission rules or proofs of authenticated label equivalence.

The complete PLAN contains the computed schema reference, eligible tickets,
every computed assignment, and an explicit primitive APPLY-profile reference.
The complete APC contains the computed EC and PLAN references. Canonical JSON
encoders produce all fields; the actual store must resolve the computed bytes,
hashes, lengths and typed payloads. Existing Q/SCHEMA/ISC/EC checks are reused.
Each computed artifact retains the 4 MiB bound. This does not prove full-batch
resource bounds or an executable native SHA/decoder implementation.

The joined checker runs the previous `NativeVectorAuthority.verify` and compares
the same complete frame with the computed graph. `joinedFrameOrigin` constructs
all five actual `FrameOrigin` resolve relations: SCHEMA, PLAN, ISC, EC and APC.
This is a conditional source-correspondence theorem. A caller still supplies an
already checked `Binding`, codec/store/hash and trust premises. This stage does
not construct a complete independent Binding or authenticate the input sources.

The profile reference receives only kind/hash-length/byte-length validation.
It is not a derived profile preimage or proof of profile authority. A kernel case
explicitly accepts the shape of an all-zero 32-byte reference. The original004
worker quantization profile is not an APPLY optimizer profile; checkpoint labels
are not model/optimizer vectors. Current model/optimizer/APPLY profile preimages,
unavailable original008 proof/base/current captures and primitive commitment/
availability authority remain open. No dummy replacements are introduced.

Kernel cases reuse actual existing rational-weight, ticket, quantum and original
Q-byte components. The partial member image intentionally has fewer leaves than
the full original manifest and is not a complete source-checker example. Tiny
PLAN/APC encodings deliberately use invalid short IDs. Their byte arrays are
compared with independent Python canonical JSON expectations. No new successful
full original/draft Binding, joined PARAMETER execution, native run or exporter
authentication is instantiated. Failed draft proofs are superseded by the final
frozen-source run.

Full native phase/QC/send/delivery/journal/current/crash/unknown/torn/repair/WAL
refinement, decimal -00/-01 compatibility, general bounded codec/hash/exporter,
contract freeze, clean offline reproduction and independent review remain
mandatory. `nativeArithmeticRecoveryRefines` is still missing. No runtime guard,
local PASS, qualifying GO, BenchmarkResultQC or independent attestation follows.
