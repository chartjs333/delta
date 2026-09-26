# Original native APPLY profiles, candidates, certificates and checked ROOT join

T044/T048/T049/T053/T057/T060; amendment0001. **NO_GO remains.**

The source is contracts.cpp, verifier.cpp, vote_admission.cpp and vote_codec.cpp
at native commit60c692f6e391f839829dfc64e93380db54cd507b. Runtime files are
unchanged. This extends the formal proposal's typed snapshot relation through
all APPLY profile/proposal/finalized lists, not the complete admission entry point.

NativeApplyProfile retains the exact rational uint64 wire bit patterns. The
nonnegative native profile rule admits numerator below2^63, positive uint64
denominator and reduced gcd1; negative signed bit patterns reject. All ordered
nonempty domain weights, accumulator ID, learning rate, momentum, weight decay,
nesterov=true and HALF_TOWARD_POSITIVE are checked. The full ten-field JSON,
including quoted rational numerators, is derived from those original inputs.
The actual source does not require weights sum to one at this layer; none is
invented. The raw JSON/hash helper alone is not the validating entry point.

NativeApplyCertificate preserves every field of the original candidate and QC,
with exact18-field canonical JSON for each. Candidate vectors retain their full
signed-decimal BYTE STRINGS. Each passes the existing native lexical/int64 relation,
with nonempty≤100000 model count and equal optimizer count. The confirmed native
-00/-01 spelling defect is retained, not normalized or repaired. Full JSON IDs
for profile, candidate and QC use the inclusive4MiB NativeContractSize wrapper.
APPLY vote-body identity is the actual candidate content ID, unlike the separate
consensus-body encodings of earlier phases. No additional vote-body hash is invented.

NativeApplyLineage parses original proposed or finalized payloads. Proposed mode
computes candidate ID and builds the exact full-committee synthetic certificate
used by native as_apply_certificate. Finalized mode reads BOTH its original
candidate and certificate; neither is supplied as an expected translated equality.
It resolves root/profile by the certificate IDs and checks both candidate and
certificate root/profile links, exact finalized ROOT membership, candidate parent
checkpoint against the actual native state parent, both expected contexts,
structural committee/signers, candidate hash and all matching certified next
model/optimizer/parent fields. Original candidate, QC, profile and source trees
remain in successful witnesses. General lemmas derive actual memberships,
canonical payload bounds, exact source reconstruction and certified identities.

NativeApplySection executes NativeAggregateSection.bindSection, then reads all
four actual APPLY lists from the original snapshot. It checks all profile and
candidate/QC bodies, strict computed ID order and finalized subset. Original lists,
counts and exact checked ROOT/profile provenance follow from executable results.
The preceding nine bounded groups and checked complete ROOT coverage are retained.
No caller supplies an admission Boolean, whole-body translator or recovered-state
identity. Successful preparation gives actual decoded original policy/state
witnesses. This is not error-order, allocation-cost or general native equivalence.

The native snapshot/ChainVerifier structural checks do NOT derive the next values
from the arithmetic, check their hash preimages, or compare parent_optimizer_hash
with the current optimizer. Explicit kernel counterchecks preserve these limits:
changing the model coordinate to999 passes candidate structural validity, and a
changed parent optimizer leaves the structural link check true. These are partial
checker counterexamples, not new accepted full-runtime exploits. The native
arithmetic guard remains in place. Actual NativeApply/NativeReplay/public-body
arithmetic and current-pointer checks still require a substantive source-bound join.

Examples use original codec-APPLY and guard-APPLY policies from the pinned complete
observation (SHA d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea),
reproducing original profile/candidate wire bytes and their actual ROOT/profile
identity links. The original observation contains NO finalized APPLY QC. The final
mode example is explicitly synthetic, using the native proposed-certificate rule;
its JSON/hash are source-derived Python computations, not a native observation.
Three finite SHA preimages extend the previous fixture function. Kernel proofs
compose original components in both modes; no complete policy/native runtime,
new C++ run, production mutant, TLC or authenticated exporter is claimed.

Kernel cases cover nonreduced/zero/negative rationals, uint64 denominator endpoint,
missing/duplicate weights, rounding/nesterov, int64 coordinates, empty/mismatched
vectors, old negative-zero spellings, wrong current parent, unfinalized ROOT,
wrong certified candidate/model/optimizer and profile. Python tests check original
pins, every canonical field, source substitutions and exact regeneration. All
named declarations are axiom-audited with only the existing allowed Lean axioms.

Remaining: timeout/view/abort sections and actual CurrentPointerCommand, complete
shared snapshot/admission/replay, separate proposedISC size path, general codecs,
stdlib/JSON/SHA, physical WAL/unknown scans/repair, original arithmetic/source
binding, complete64-variable public relation and nativeArithmeticRecoveryRefines.
Native authentication, contract freeze, clean offline reproduction and independent
review remain required. Mandatory44/45 and Phase0 still fail; no new local PASS,
GO, independent attestation or runtime guard change. Retained finite TLA/mutant
results keep their previous scope; make formal-check is not claimed when unavailable.

Reproduction: generate_native_apply_certificate.py; lake build DeltaReduce;
lake env lean DeltaReduce/AxiomAudit.lean; test_native_apply_certificate.py;
check-refinement.py --all-fixtures. Exact final commands/logs/counts/source hashes
are retained in evidence/native-apply-certificate.json and its sibling directory.
