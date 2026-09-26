"""Original candidate/context examples and explicitly synthetic mixed snapshot components."""

import hashlib
from pathlib import Path

import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_snapshot_base import PIN
from generate_native_wal_lean import lit

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeCandidateAuthorityVectors.lean"
FIELDS = [
    "round_config_id",
    "parent_checkpoint_id",
    "input_set_certificate_id",
    "seed_transcript_id",
    "norm_evidence_id",
    "eligibility_certificate_id",
    "aggregation_plan_certificate_id",
    "parameter_matrix_root",
    "aggregate_root_certificate_id",
    "apply_profile_id",
    "apply_candidate_id",
    "last_finalized_certificate_id",
    "domain_id",
    "shard_id",
    "reason_code",
]


def sources():
    doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(doc)).hexdigest() != PIN:
        raise ValueError("original candidate observation changed")
    rows = [r for r in doc["observed"] if r["name"].startswith("codec-")]
    policies = [codec.decode(bytes.fromhex(r["policy_hex"])) for r in rows]
    if len(rows) != 9:
        raise ValueError("nine original candidate policies required")
    for action, (r, p) in enumerate(zip(rows, policies, strict=True), 1):
        if (codec.HEADER + codec.encode_value("policy", p)).hex() != r["policy_hex"]:
            raise ValueError("original policy does not reproduce")
        if len(p["candidates"]) != 1 or p["candidates"][0]["action"] != action:
            raise ValueError("original candidate order changed")
    return policies


def text(value):
    return '(ascii "' + value + '")'


def parent(value):
    return "⟨" + ",".join(text(value[k]) for k in FIELDS) + "⟩"


def generate():
    ps = sources()
    out = [
        r"""import DeltaReduce.NativeCandidateAuthority
import DeltaReduce.NativeSnapshotBaseVectors
import DeltaReduce.NativeApplyCertificateVectors
import DeltaReduce.NativeFailureAuthorityVectors

/-! One whole original CONFIG policy example; other candidate checks use
original individual rows in an explicitly synthetic mixed component snapshot.
No whole mixed-native run, authentication, arithmetic admission or recovery. -/
namespace DeltaReduce.NativeCandidateAuthorityVectors
open NativeReceiptBytes NativePolicyCodec
open NativeCandidateAuthority
open NativeCandidateShape (Parents)
open NativeVoteBytes (ascii)
set_option maxRecDepth 16384
set_option maxHeartbeats 800000

def policy := NativeConfigAdmissionVectors.policy
def state := NativeConfigAdmissionVectors.state
"""
    ]
    # This finite adapter recomputes eight exact original context preimages.
    cases = []
    domains = {
        1: "config",
        2: "isc",
        3: "ec",
        4: "apc",
        6: "root",
        7: "apply",
        8: "view",
        9: "abort",
    }
    keys = {
        3: "input_set_certificate_id",
        4: "eligibility_certificate_id",
        6: "aggregation_plan_certificate_id",
        7: "aggregate_root_certificate_id",
    }
    for i, p in enumerate(ps, 1):
        c = p["candidates"][0]
        out += [
            f"def parents{i} : Parents := {parent(c['parents'])}\n",
            f"def candidate{i} : NativePolicyBytes.Candidate := "
            f"⟨{i},{text(c['body_hash'])},{text(c['context_id'])},{c['height']},{c['view']},"
            f"NativeCandidateShape.value parents{i},"
            f".pair (.number {i}) (.pair (.text {text(c['body_hash'])})"
            f" (.pair (.text {text(c['context_id'])}) (.pair (.number {c['height']})"
            f" (.pair (.number {c['view']}) "
            f"(.pair (NativeCandidateShape.value parents{i}) .end)))))⟩\n",
        ]
        if i == 5:
            if c["context_id"] != p["snapshot"]["parameter_bodies"][0]["vote_context_id"]:
                raise ValueError("parameter assignment context mismatch")
            continue
        data = (
            p["validator_epoch_id"]
            if i == 1
            else c["parents"][keys[i]]
            if i in keys
            else p["round_id"]
        ).encode()
        payload = len(data).to_bytes(8, "big") + data
        if i == 1:
            payload = c["height"].to_bytes(8, "big") + payload
        elif i == 8:
            payload += c["view"].to_bytes(8, "big")
        pre = f"deltareduce.vote-context.{domains[i]}.v1".encode() + b"\0" + payload
        digest = hashlib.sha256(pre).digest()
        if "sha256:" + digest.hex() != c["context_id"]:
            raise ValueError("original context hash mismatch")
        cases.append((i, pre, digest))
        out += [
            f"def contextPre{i} : Bytes := {lit(pre)}\n",
            f"def contextHash{i} : Bytes := {lit(digest)}\n",
        ]
    out.append(
        "def sha (raw : Bytes) : Bytes :=\n  "
        + " else\n  ".join(f"if raw = contextPre{i} then contextHash{i}" for i, _, _ in cases)
        + " else NativeFailureAuthorityVectors.hash raw\n"
    )
    out.append(r"""
-- These rows reuse earlier individually kernel-checked original fixture bodies.
-- Their simultaneous assembly is mathematical, not an original native snapshot.
def isc : NativeFinalizedIscSection.Bound :=
  ⟨policy,state,NativeSnapshotBaseVectors.base.schema,NativeSnapshotBaseVectors.base.arithmetic,
    [],[NativeIscCertificateVectors.tree],[NativeIscCertificateVectors.checked],
    [NativeIscCertificateVectors.qc]⟩
def norms : NativeNormSection.Bound :=
  ⟨isc,[NativeNormEvidenceVectors.tree],[NativeNormEvidenceVectors.checked]⟩
def ecs : NativeEligibilitySection.Bound :=
  ⟨norms,[NativeSeedTranscriptVectors.tree],[NativeSeedTranscriptVectors.checked],
    [NativeEligibilityVectors.bodyTree],[NativeEligibilityVectors.proposedEdge],
    [NativeEligibilityVectors.finalTree],[NativeEligibilityVectors.finalEdge],
    [NativeEligibilityVectors.qc]⟩
def plans : NativePlanSection.Bound :=
  ⟨ecs,NativeSnapshotBaseVectors.base.accumulator,[NativePlanVectors.bodyTree],
    [NativePlanVectors.proposedEdge],[NativePlanVectors.tree],[NativePlanVectors.finalEdge],
    [NativePlanVectors.qc]⟩
def parameters : NativeParameterSection.Bound :=
  ⟨plans,[],NativeParameterVectors.keys,[NativeParameterVectors.bodyTree],
    [NativeParameterVectors.proposedEdge],[NativeParameterVectors.tree],
    [NativeParameterVectors.finalizedEdge],[NativeParameterVectors.qc]⟩
def roots : NativeAggregateSection.Bound :=
  ⟨⟨parameters,[]⟩,[NativeAggregateVectors.bodyTree],[NativeAggregateVectors.proposedEdge],
    [NativeAggregateVectors.tree],[NativeAggregateVectors.finalizedEdge],[NativeAggregateVectors.qc]⟩
def applies : NativeApplySection.Bound :=
  ⟨roots,[NativeApplyCertificateVectors.profileTree],[NativeApplyCertificateVectors.checkedProfile],
    [NativeApplyCertificateVectors.candidateTree],[NativeApplyCertificateVectors.proposedEdge],
    [],[],[]⟩
def mixed : NativeSnapshotBase.Bound :=
  ⟨⟨applies,NativeFailureVectors.viewTail⟩,NativeSnapshotBaseVectors.base⟩
def abortMixed : NativeSnapshotBase.Bound :=
  {mixed with prior := {mixed.prior with tail := NativeFailureVectors.abortTail}}
""")
    for i in range(1, 10):
        snap = "abortMixed" if i == 9 else "mixed"
        out.append(f"""
theorem originalCandidate{i} : NativePolicyBytes.candidate candidate{i}.source =
    some candidate{i} := rfl
theorem shape{i} : NativeCandidateShape.check policy candidate{i} = some parents{i} := by decide
theorem authority{i} : Authority sha policy state {snap} candidate{i} parents{i} := by decide
theorem accepted{i} : check sha policy state {snap} candidate{i} = some ⟨candidate{i},parents{i}⟩ :=
  fromComponents shape{i} rfl rfl authority{i}
theorem wrongHeight{i} :
    (check sha policy state {snap} {{candidate{i} with height := 2}}).isNone = true := by decide
theorem wrongContext{i} : ¬ Authority sha policy state {snap}
    {{candidate{i} with context := ascii "other"}} parents{i} := by decide
""")
    out.append(r"""
theorem wholeOriginalConfig :
    (bindPolicy NativeConfigAdmissionVectors.sha policy state).isSome = true := by decide
theorem wholeOriginalConfigBytes :
    (prepare NativeConfigAdmissionVectors.sha NativeConfigAdmissionVectors.policyRaw
      NativeConfigAdmissionVectors.stateRaw).isSome = true := by
  unfold prepare
  rw [NativeConfigAdmissionVectors.policyDecoded,NativeConfigAdmissionVectors.stateDecoded]
  exact wholeOriginalConfig
theorem authorityDoesNotPrematurelyRequireCurrent :
    NativeCandidateShape.Checks policy candidate1
      {parents1 with checkpoint := NativeSnapshotBaseVectors.base.schema} ∧
    Authority sha policy state mixed candidate1
      {parents1 with checkpoint := NativeSnapshotBaseVectors.base.schema} := by decide
theorem parameterContextIsOriginalAssignment :
    candidate5.context = NativeParameterVectors.body.voteContext := by decide
theorem missingBody :
    ¬ Authority sha policy state {mixed with prior := {mixed.prior with prior :=
      {applies with roots := {roots with bodies := []}}}} candidate6 parents6 := by decide
theorem missingFinalizedRoot :
    ¬ Authority sha policy state {mixed with prior := {mixed.prior with prior :=
      {applies with roots := {roots with finalized := []}}}} candidate7 parents7 := by decide
theorem changedNormParent : ¬ Authority sha policy state mixed candidate4
    {parents4 with norm := parents4.isc} := by decide
theorem changedSeedParent : ¬ Authority sha policy state mixed candidate5
    {parents5 with seed := parents5.plan} := by decide
theorem changedMatrix : ¬ Authority sha policy state mixed candidate6
    {parents6 with matrix := parents6.plan} := by decide
theorem changedApplyIdentity : ¬ Authority sha policy state mixed candidate7
    {parents7 with apply := parents7.root} := by decide
theorem changedCurrent : ¬ Authority sha policy
    {state with wire := {state.wire with parent := parents7.root}}
    mixed candidate7 parents7 := by decide
theorem missingClosed :
    ¬ Authority sha policy state {mixed with base := {mixed.base with closed := []}}
      candidate2 parents2 := by decide
theorem missingConfig :
    ¬ Authority sha policy state {mixed with base := {mixed.base with proposedConfigs := []}}
      candidate1 parents1 := by decide
theorem badAction : ¬ Authority sha policy state mixed
    {candidate1 with action := 0} parents1 := by decide
theorem missingTimeout : ¬ Authority sha policy state
    {mixed with prior := {mixed.prior with tail := {mixed.prior.tail with timeouts := []}}}
    candidate8 parents8 := by decide
theorem abortAfterApply : ¬ Authority sha policy state
    {abortMixed with prior := {abortMixed.prior with tail := {abortMixed.prior.tail with
      lineage := {abortMixed.prior.tail.lineage with applies := [candidate7.body]}}}}
    candidate9 parents9 := by decide
""")
    # Every parent slot is exercised independently with missing/extra fields.
    lean_fields = [
        "config",
        "checkpoint",
        "isc",
        "seed",
        "norm",
        "ec",
        "plan",
        "matrix",
        "root",
        "profile",
        "apply",
        "last",
        "domain",
        "shard",
        "reason",
    ]
    actions = [1, 1, 3, 3, 3, 4, 5, 6, 7, 7, 7, 1, 5, 5, 9]
    for field, a in zip(lean_fields, actions, strict=True):
        value = "policy.config" if field == "last" else "[]"
        out.append(f"""theorem rejectParent_{field} : ¬ NativeCandidateShape.Checks policy
    candidate{a} {{parents{a} with {field} := {value}}} := by decide
""")
    out.append(r"""
theorem originalPairList :
    (checkAll sha policy state mixed [candidate1,candidate2]).isSome = true := by decide
theorem badSecondCannotBeSkipped :
    (checkAll sha policy state mixed [candidate1,{candidate2 with context := []}]).isNone = true :=
  by decide
theorem duplicateContextRejected :
    ¬ NativePolicyBytes.Canonical {policy with candidates := [candidate1,candidate1]} := by decide
theorem reversedOrderRejected :
    ¬ NativePolicyBytes.Canonical {policy with candidates := [candidate2,candidate1]} := by decide
end DeltaReduce.NativeCandidateAuthorityVectors
""")
    return "".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
