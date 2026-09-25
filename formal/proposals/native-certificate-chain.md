# Exact native certificate chain and voted-body projection

T044/T048/T049/T053/T057/T060; amendment 0001 proposal. Formal GO and local
acceptance remain absent. No runtime source, admission guard, legacy witness,
receipt, sequence or state root is changed.

## Pinned components and distinct identities

The source is PR50 commit `60c692f6e391f839829dfc64e93380db54cd507b`.
Ten exact Git blob hashes are retained. The harness compiles the complete,
unchanged native `canonical.cpp`, `sha256.cpp` and certificate `contracts.cpp`,
their exact headers, four extracted voted-body structs and twenty extracted
consensus projection/hash functions. Extraction records exact line/span hashes.
MSVC 19.29.30146 x64, C++20, /EHsc /W4 /WX compiles these components. The harness
constructs values and emits outputs; it does not implement replacement native
SHA, certificate encoding or Merkle logic. Binaries remain ignored.

Seven independent Python canonical encodings/content IDs match C++: ISC, seed
transcript, norm evidence, EC, APC, PARAMETER QC and aggregate-root QC. Four
pre-quorum voted-body IDs (ISC, EC, APC, ROOT) also match. Four one/two/three/four
leaf cases check native Merkle domain separation and odd-leaf promotion. Five
actual native shape rejections cover empty ISC tuples, duplicate signer, invalid
input-root spelling, wrong Merkle root and duplicate leaf. Three identity variants
show that changed signers change the QC ID but not its voted-body ID, and changed
EC seed metadata changes the EC voted body.

The certificate JSON contains the **original native semantics**
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
Its content ID hashes `deltareduce.008.<kind>.v1`, NUL and exact JSON bytes.
The voted-body ID hashes the separate native binary payload with its own domain;
it does not silently acquire certificate signer/quorum fields or the candidate
semantic ID. This is pinned component compatibility, not authority for amendment
0001. The fixture uses source-level primitive values and synthetic signers, not
an authenticated exporter or a full execution of the native fixture constructor.
Its PARAMETER QC scalar `1` serves this certificate-chain check only; it does not
replace the separate candidate vector-arithmetic corpus or prove recomputation.

## Checked structural relation

`native_certificate_chain.py` loads original canonical bytes by exact content ID
from a separately supplied store. The root anchor and EC-to-seed binding require
independent provenance; supplying this store does not establish that provenance.
It checks all seven Context fields, original schema/semantic version, exact known
fields, canonical JSON, hashes, supported shape, parent edges and complete ordered
ROOT leaf/required-key coverage. Each loaded PARAMETER leaf must match its key and
the same ISC/EC/APC parents. It recomputes Merkle roots from actual leaf preimages.
Unknown, missing, substituted, reordered and duplicate records fail these checks.
Unreferenced store entries are allowed; they cannot supply an unresolved parent.

EC's canonical certificate has **no seed-transcript field**. The native
`project_eligibility_vote_body` takes the seed ID separately, and native
`VoteFinalizedEligibility` retains it beside the certificate. The checker requires
the independently supplied mapping keyed by the exact EC content ID and checks
that it equals the APC's seed parent. Adding a seed field to EC JSON rejects.
The relationship is explicit metadata, not an invented certificate field.

The proposal accepts ASCII strings <=128 bytes, lists/store <=4096 entries,
payloads <=4 MiB, tree depth <=16 and <=100000 tree nodes. These are tooling
restrictions, not native parser/admission equivalence. Native shape checks and
proposal shape checks are compared on the retained cases; no universal equality
of their accepted languages is claimed. The proposal does not decode a native
wire frame, C ABI, snapshot or WAL record.

## Deliberate limits and countercheck

The ISC `input_root`, availability/commitment IDs, seed/norm/transcript roots and
profile/configuration IDs remain primitive values. Neither byte/hash equality nor
the native certificate shape validator proves their source preimages, availability
freeze, mathematical correctness, signer authentication or committee membership.
An explicit test rebuilds the entire valid structural chain around another
well-spelled ISC root: it rejects against the original root anchor, but passes
when the caller supplies the rebuilt root as a NEW anchor. That passing structural
check still returns `native_admission_verified=false` and
`native_export_authenticated=false`. It demonstrates the missing independent
anchor/root provenance; it is not a production-admission success.

Likewise the norm values, eligibility/weight coverage and PARAMETER result are
not recomputed from worker inputs here. Threshold/list shape is not a verified
cryptographic quorum. Primitive fixture signatures are not independently held.
There is no native reactor, immutable admission snapshot, physical WAL, recovery,
public TLA action, authenticated snapshot/exporter or Lean history execution.
One MSVC component build is not GCC/Clang/sanitizer/native-runtime qualification.
All artifacts say `gate_eligible=false`; no BenchmarkResultQC or GO is produced.

The prior legacy ISC/EC/APC/ROOT label hashes, minimal arithmetic graph and this
complete native certificate representation remain distinct. The stronger Lean
mixed-prefix gate still rejects the incomplete legacy history. The new IDs cannot
be substituted under original receipts, journal roots or sequences 5/6/8.

Next bind the complete native configuration/commitment/availability and closed
input-set snapshot to these original primitives, with field-level public
projection. Then derive non-arithmetic source bodies in the Lean prefix bridge
and compose phase/send/delivery/QC/current/crash/unknown relations. CONFIG/VIEW/
ABORT, native arithmetic admission/recovery, bounded adapters/WAL, arbitrary
snapshots/failures/repair, contract freeze, clean reproduction and independent
reviews remain open. `nativeArithmeticRecoveryRefines` is still missing.

## Reproduction and retained evidence

Run `python formal/scripts/generate_native_certificate_chain.py` to regenerate
`native-certificate-chain-vectors.json`. Add `--vcvars <VS2019 vcvars64.bat>` to
compile and compare the exact local Git blobs in ignored
`formal/build/native-certificate-chain`. No branch-head substitution is allowed.
Run `python -m unittest discover -s formal/tests -p test_native_certificate_chain.py -v`.

Sixteen tests cover exact source/span/fixture reproduction and component outputs;
every missing/substituted certificate; rehashed context/parent/leaf substitutions;
seed metadata; signer/body separation; Merkle ordering; native shape countercases;
strict types/fractions/versions; noncanonical/deep/resource-invalid JSON; fixed
versus substituted anchors; and malformed/duplicate/missing C++ result rows.
The output parser requires the entire expected result set before reporting PASS.
Evidence is `formal/proposals/evidence/native-certificate-chain.json` plus its
sibling directory. The new fixture, harness and component result regenerate byte
exactly. The archived compiler transcript normalizes line endings and trailing
whitespace; native byte/hash results are retained separately without alteration.
All earlier generated/native/public fixtures stay unchanged. Lean/TLA
inputs are unchanged: no fresh Lean/TLC result or production mutant is claimed.
