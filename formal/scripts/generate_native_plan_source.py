"""Compose the retained original008 raw policy/state; never repair its missing proof."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict, write_canonical_json
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_admission_snapshot import decode_flat, state_id

ROOT = Path(__file__).resolve().parents[2]
POLICY = "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
STATE = "formal/proposals/evidence/native-admission-snapshot/cpp-cross-check.json"
POLICY_PIN = "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
STATE_PIN = "45e6a49f7af1a15efb01d15cbf5401f9e560fa86d91befed892f892b8285a10d"
MODULES = [
    "NativeIscAdmissionVectors",
    "NativeConfigAdmissionVectors",
    "NativeIscCertificateVectors",
    "NativeNormEvidenceVectors",
    "NativeSeedTranscriptVectors",
    "NativeEligibilityVectors",
    "NativePlanVectors",
    "NativeParameterVectors",
]


def source():
    original = load_json_strict(ROOT / POLICY)
    if hashlib.sha256(canonical_json_bytes(original)).hexdigest() != POLICY_PIN:
        raise ValueError("original policy observation changed")
    row = next(r for r in original["observed"] if r["name"] == "codec-PARAMETER")
    policy_raw = bytes.fromhex(row["policy_hex"])
    p = codec.decode(policy_raw)
    if codec.HEADER + codec.encode_value("policy", p) != policy_raw:
        raise ValueError("original policy encoding changed")
    states = load_json_strict(ROOT / STATE)
    if hashlib.sha256(canonical_json_bytes(states)).hexdigest() != STATE_PIN:
        raise ValueError("original state observation changed")
    state_row = next(r for r in states["observed"] if r["name"] == "original-aggregation_plan")
    raw = bytes.fromhex(state_row["state_hex"])
    s = decode_flat(raw, 5)
    if state_id(raw) != p["snapshot"]["state_id"]:
        raise ValueError("original state preimage does not match policy")
    if (s["round_id"], s["config_id"]) != (p["round_id"], p["round_config_id"]):
        raise ValueError("original policy/state context mismatch")
    return p, policy_raw, s, raw


def generate():
    p, policy_raw, s, raw = source()
    reuse = {}
    for module in MODULES:
        text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
        for name, expression in re.findall(
            r"^theorem (encoding\d+) : (?:NativePolicyCodec\.)?encode (.*?) = some", text, re.M
        ):
            reuse[expression] = module + "." + name
    out = [
        "import DeltaReduce.NativeSourceRefusal",
        "import DeltaReduce.NativePlanCoefficientVectors",
        "import DeltaReduce.NativeParameterVectors",
        "import DeltaReduce.NativeAccumulatorVectors",
        "import DeltaReduce.NativeConfigAdmissionVectors",
        "",
        "/-! Retained original008 policy/state, composed through all parent sections.",
        "Finite pinned SHA samples remain synthetic. Missing proof is not repaired. -/",
        "namespace DeltaReduce.NativePlanSourceVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 200000",
        "def tree : Value := " + lean_value("policy", p),
        "def snapshot : Value := " + lean_value("snapshot", p["snapshot"]),
    ]
    candidates = []
    for i, c in enumerate(p["candidates"]):
        out += [
            f"def candidate{i} : NativePolicyBytes.Candidate := "
            + "⟨"
            + ",".join(
                [
                    str(c["action"]),
                    lit(c["body_hash"].encode()),
                    lit(c["context_id"].encode()),
                    str(c["height"]),
                    str(c["view"]),
                    lean_value("parents", c["parents"]),
                    lean_value("candidate", c),
                ]
            )
            + "⟩"
        ]
        candidates.append(f"candidate{i}")
    fields = [
        lit(p["local_validator_id"].encode()),
        lit(p["validator_epoch_id"].encode()),
        "[" + ",".join(lit(v.encode()) for v in p["validator_ids"]) + "]",
        str(p["role"]),
        lit(p["round_id"].encode()),
        lit(p["round_config_id"].encode()),
        lit(p["configured_abort_reason"].encode()),
        str(p["initial_logical_tick"]),
        str(p["soft_deadline_tick"]),
        str(p["hard_deadline_tick"]),
        "snapshot",
        "[" + ",".join(candidates) + "]",
        "tree",
    ]
    out += [
        "def policy : NativePolicyBytes.Policy := ⟨" + ",".join(fields) + "⟩",
        "theorem extracted : NativePolicyBytes.extract tree = some policy := by rfl",
    ]
    cache = {}

    def encode(kind, value):
        expression = f"({format_of(kind)}) ({lean_value(kind, value)})"
        if expression in reuse:
            return reuse[expression]
        if expression in cache:
            return cache[expression]
        vector = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            proof = "(by rfl)"
            for key, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[key])} {proof})"
        elif vector:
            proof = "(by rfl)"
            for item in reversed(value):
                proof = f"(encodedCons {encode(vector[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[expression] = name
        out.append(
            f"theorem {name} : encode {expression} = some "
            f"{lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    encoded = encode("policy", p)
    out += [
        "def policyBody : Bytes := " + lit(policy_raw[16:]),
        "def policyRaw : Bytes := NativePolicyBytes.header ++ policyBody",
        f"theorem encoded : encode fmtPolicy tree = some policyBody := {encoded}",
        "theorem canonical : NativePolicyBytes.Canonical policy := by decide",
        "set_option maxRecDepth 65536 in",
        f"theorem policyLength : policyRaw.length = {len(policy_raw)} := by decide",
        "theorem policyParsed : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy) :=",
        "  NativePolicyBytes.encoded encoded extracted canonical "
        "(by change policyRaw.length ≤ _; rw [policyLength]; decide)",
    ]
    fields = []
    for key in [
        "available_ticket_count",
        "committed_ticket_count",
        "config_id",
        "durable_sequence",
        "height",
        "parent_checkpoint_id",
        "phase",
        "round_id",
        "state_root",
        "ticket_count",
        "view",
    ]:
        fields.append(str(s[key]) if type(s[key]) is int else lit(s[key].encode()))
    out += [
        "def stateWire : NativeStateBytes.WireState := ⟨" + ",".join(fields) + "⟩",
        "def state : NativeStateBytes.State := "
        f"⟨stateWire,{s['durable_sequence']},{s['height']},{s['view']}⟩",
        "def stateRaw : Bytes := " + lit(raw),
        "theorem stateValid : NativeStateBytes.StateValid state := by decide",
        "theorem stateEncoded : NativeStateBytes.encodeState stateWire = stateRaw := by rfl",
        "theorem stateParsed : NativeStateBytes.decodeState stateRaw = some state :=",
        "  stateEncoded ▸ NativeStateBytes.stateEncoded state stateValid",
        "def statePreimage : Bytes := "
        "NativeStateBytes.contentPreimage NativeStateBytes.stateDomain stateRaw",
        "def stateDigest : Bytes := "
        + lit(hashlib.sha256(b"deltareduce:003:round-state:v1\0" + raw).digest()),
        "def snapshotId : Bytes := " + lit(p["snapshot"]["state_id"].encode()),
        "def proofPreimage : Bytes := "
        "NativeAccumulatorBinding.proofInput NativeAccumulatorVectors.proofOriginal",
        "def sha (raw : Bytes) : Bytes := if raw = statePreimage then stateDigest else",
        "  if raw = proofPreimage then proofDigest else NativePlanVectors.sha raw",
        "theorem stateHash : NativeStateBytes.contentId sha NativeStateBytes.stateDomain "
        "stateRaw = some snapshotId := by",
        "  unfold NativeStateBytes.contentId sha; rfl",
        "theorem fallback {raw} (h : raw ≠ statePreimage) (hp : raw ≠ proofPreimage) : "
        "sha raw = NativePlanVectors.sha raw := by",
        "  simp only [sha,if_neg h,if_neg hp]",
    ]
    # Small SHA-domain inequalities, not evaluation of whole dependent graphs.
    for name, module, method, value, theorem in [
        (
            "iscHash",
            "NativeIscCertificate",
            "id",
            "NativeIscCertificateVectors.certificate",
            "iscHash",
        ),
        (
            "iscBodyHash",
            "NativeInputSetBody",
            "bodyId",
            "NativeIscCertificateVectors.certificate.body",
            "iscBodyHash",
        ),
        ("normHash", "NativeNormEvidence", "id", "NativeNormEvidenceVectors.evidence", "normHash"),
        (
            "seedHash",
            "NativeSeedTranscript",
            "id",
            "NativeSeedTranscriptVectors.transcript",
            "seedHash",
        ),
        ("ecHash", "NativeEligibility", "id", "NativeEligibilityVectors.certificate", "ecHash"),
        ("apcHash", "NativePlan", "id", "NativePlanVectors.certificate", "qcComputed"),
    ]:
        target = {
            "iscHash": "NativeIscCertificateVectors.qc",
            "iscBodyHash": "NativeIscCertificateVectors.bodyId",
            "normHash": "NativeNormEvidenceVectors.evidenceId",
            "seedHash": "NativeSeedTranscriptVectors.transcriptId",
            "ecHash": "NativeEligibilityVectors.qc",
            "apcHash": "NativePlanVectors.qc",
        }[name]
        out += [
            f"theorem {name} : {module}.{method} sha {value} = some {target} := by",
            f"  unfold {module}.{method} NativeStateBytes.contentId",
            "  rw [fallback (by decide) (by decide)]",
            f"  exact NativePlanVectors.{theorem}",
        ]
    # Insert the actual004 digest before the registry; the required008 ID stays different.
    from generate_native_source_artifacts import fixture_store
    from native_source_artifacts import DOMAINS

    _, golden, _ = fixture_store()
    proof_raw = canonical_json_bytes(golden["proof_instance"]["value"])
    digest = hashlib.sha256(DOMAINS["proof"].encode("ascii") + b"\0" + proof_raw).digest()
    at = out.index(
        "def proofPreimage : Bytes := "
        "NativeAccumulatorBinding.proofInput NativeAccumulatorVectors.proofOriginal"
    )
    out.insert(at, "def proofDigest : Bytes := " + lit(digest))
    out += [TAIL, "end DeltaReduce.NativePlanSourceVectors"]
    summary = {
        "status": "RAW_ORIGINAL008_PLAN_MEMBERS_WITH_EXPLICIT_ARITHMETIC_REFUSAL",
        "scope": "RETAINED_NATIVE_COMPONENT_BYTES_FINITE_SYNTHETIC_SHA",
        "formal_go": False,
        "gate_eligible": False,
        "native_export_authenticated": False,
        "complete_vector_join": False,
        "new_native_execution": False,
        "policy_source": POLICY,
        "state_source": STATE,
        "source_sha256": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in [POLICY, STATE]
        },
        "policy_sha256": hashlib.sha256(policy_raw).hexdigest(),
        "policy_bytes": len(policy_raw),
        "state_sha256": hashlib.sha256(raw).hexdigest(),
        "state_bytes": len(raw),
        "snapshot_id": p["snapshot"]["state_id"],
        "required_proof": p["snapshot"]["required_accumulator_proof_id"],
        "encoding_lemmas": len(cache),
    }
    return "\n\n".join(out) + "\n", summary


TAIL = r"""
def context := NativePlanVectors.certificate.common.context
def committee := NativeIscCertificateVectors.committee

theorem iscChecked : NativeIscCertificate.check sha context committee
    NativeIscCertificateVectors.tree = some NativeIscCertificateVectors.checked :=
  NativeIscCertificate.fromComponents NativeIscCertificateVectors.parsed
    NativeIscCertificateVectors.valid iscHash iscBodyHash
theorem normChecked : NativeNormEvidence.check sha context [NativeIscCertificateVectors.qc]
    NativeNormEvidenceVectors.tree = some NativeNormEvidenceVectors.checked :=
  NativeNormEvidence.fromComponents NativeNormEvidenceVectors.parsed
    NativeNormEvidenceVectors.valid (by decide) normHash
theorem seedChecked : NativeSeedTranscript.check sha context [NativeIscCertificateVectors.qc]
    NativeSeedTranscriptVectors.tree = some NativeSeedTranscriptVectors.checked :=
  NativeSeedTranscript.fromComponents NativeSeedTranscriptVectors.parsed
    NativeSeedTranscriptVectors.valid (by decide) seedHash
theorem ecChecked : NativeEligibilityLineage.check sha .finalized context committee
    [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc]
    [NativeNormEvidenceVectors.checked] [NativeSeedTranscriptVectors.checked]
    NativeEligibilityVectors.finalTree = some NativeEligibilityVectors.finalEdge :=
  NativeEligibilityLineage.fromComponents ⟨rfl,NativeEligibilityVectors.finalParsed,
    NativeEligibilityVectors.parentFound,NativeEligibilityVectors.normFound,
    NativeEligibilityVectors.seedFound,NativeEligibilityVectors.valid,
    NativeEligibilityVectors.finalParents,ecHash⟩
theorem apcChecked : NativePlanLineage.check sha .finalized context committee
    [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc]
    [NativeEligibilityVectors.qc] NativePlanVectors.certificate.common.accumulator
    [NativeEligibilityVectors.finalEdge] [NativeSeedTranscriptVectors.checked]
    NativePlanVectors.tree = some NativePlanVectors.finalEdge :=
  NativePlanLineage.fromComponents ⟨rfl,NativePlanVectors.parsed,
    NativePlanVectors.parentFound,NativePlanVectors.ecFound,NativePlanVectors.seedFound,
    NativePlanVectors.valid,NativePlanVectors.parentsValid,apcHash⟩

def iscSection : NativeFinalizedIscSection.Bound :=
  ⟨policy,state,context.schema,context.arithmetic,snapshotId,
    [NativeIscCertificateVectors.tree],[NativeIscCertificateVectors.checked],
    [NativeIscCertificateVectors.qc]⟩
theorem iscSectionChecked :
    NativeFinalizedIscSection.bindSection sha policy state = some iscSection := by
  apply NativeFinalizedIscSection.fromComponents
  refine ⟨rfl,rfl,rfl,?_,rfl,rfl,rfl,?_,rfl,?_,?_,?_,?_,?_⟩
  · change NativeStateBytes.contentId sha NativeStateBytes.stateDomain
      (NativeStateBytes.encodeState stateWire) = some snapshotId
    rw [stateEncoded]; exact stateHash
  · exact NativeIscCertificate.listFromComponents iscChecked rfl
  · decide
  · exact NativeIscCertificateVectors.valid.1
  · decide
  · decide
  · decide

def normSection : NativeNormSection.Bound :=
  ⟨iscSection,[NativeNormEvidenceVectors.tree],[NativeNormEvidenceVectors.checked]⟩
theorem normSectionChecked : NativeNormSection.bindSection sha policy state = some normSection :=
  NativeNormSection.fromComponents ⟨iscSectionChecked,rfl,
    NativeNormEvidence.listFromComponents normChecked rfl,by decide⟩
def eligibilitySection : NativeEligibilitySection.Bound :=
  ⟨normSection,[NativeSeedTranscriptVectors.tree],[NativeSeedTranscriptVectors.checked],[],[],
    [NativeEligibilityVectors.finalTree],[NativeEligibilityVectors.finalEdge],[NativeEligibilityVectors.qc]⟩
theorem eligibilitySectionChecked :
    NativeEligibilitySection.bindSection sha policy state = some eligibilitySection :=
  NativeEligibilitySection.fromComponents ⟨normSectionChecked,rfl,
    NativeSeedTranscript.listFromComponents seedChecked rfl,rfl,rfl,rfl,
    by
      change NativeEligibilityLineage.checkAll sha .finalized context committee
        [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc]
        [NativeNormEvidenceVectors.checked] [NativeSeedTranscriptVectors.checked]
        [NativeEligibilityVectors.finalTree] = some [NativeEligibilityVectors.finalEdge]
      simp only [NativeEligibilityLineage.checkAll,ecChecked,Bind.bind,Option.bind],rfl,by decide⟩
def planSection : NativePlanSection.Bound :=
  ⟨eligibilitySection,NativePlanVectors.certificate.common.accumulator,[],[],
    [NativePlanVectors.tree],[NativePlanVectors.finalEdge],[NativePlanVectors.qc]⟩
theorem planSectionChecked : NativePlanSection.bindSection sha policy state = some planSection :=
  NativePlanSection.fromComponents ⟨eligibilitySectionChecked,rfl,rfl,rfl,rfl,
    by
      change NativePlanLineage.checkAll sha .finalized context committee
        [NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc]
        [NativeEligibilityVectors.qc] NativePlanVectors.certificate.common.accumulator
        [NativeEligibilityVectors.finalEdge] [NativeSeedTranscriptVectors.checked]
        [NativePlanVectors.tree] = some [NativePlanVectors.finalEdge]
      simp only [NativePlanLineage.checkAll,apcChecked,Bind.bind,Option.bind],rfl,by decide⟩
theorem rawPlanPrepared : NativePlanSection.prepare sha policyRaw stateRaw = some planSection :=
  NativeSourceRefusal.sectionFromSources policyParsed stateParsed planSectionChecked

def originalRow : NativePlanMembers.Row :=
  ⟨⟨NativeIscCertificateVectors.certificate.body.tuples.head (by decide),
    NativeEligibilityVectors.certificate.common.entries.head (by decide)⟩,
    NativePlanVectors.weight,NativePlanVectors.bucket⟩
def members : NativePlanMembers.Bound := ⟨planSection,NativePlanVectors.finalEdge,[originalRow]⟩
theorem originalRows :
    NativePlanMembers.derive NativePlanVectors.finalEdge = some [originalRow] := by decide
theorem rawMembersPrepared :
    NativePlanMembers.prepare sha policyRaw stateRaw NativePlanVectors.qc = some members :=
  NativePlanMembers.prepareFromSource ⟨rawPlanPrepared,by rfl,by decide,originalRows⟩
theorem originalCoverage : members.rows.map NativePlanMembers.Row.weight =
    NativePlanVectors.certificate.common.weights :=
  (NativePlanMembers.fullOriginalCoverage originalRows).1
theorem requiredProofRetained : members.edge.certificate.common.accumulator =
    NativeVoteBytes.ascii
      "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" := rfl

theorem supplied004ProofHash : NativePlanCoefficients.contentHash sha proofPreimage =
    NativeAccumulatorVectors.id1 := by
  unfold NativePlanCoefficients.contentHash sha
  rw [if_neg (by decide : proofPreimage ≠ statePreimage),if_pos rfl]
  rfl
theorem supplied004IsNotRequired : NativePlanCoefficients.contentHash sha proofPreimage ≠
    members.edge.certificate.common.accumulator := by
  rw [supplied004ProofHash]; decide
theorem substitutedProofRejected (configRaw profileRaw : Bytes) :
    NativeAccumulatorBinding.load (NativePlanCoefficients.contentHash sha) configRaw
      NativeAccumulatorVectors.proofOriginal profileRaw
      members.edge.certificate.common.accumulator = none :=
  NativeSourceRefusal.accumulatorIdentityUnavailable supplied004IsNotRequired
theorem originalCannotUse004Proof (configRaw profileRaw : Bytes) :
    NativePlanCoefficients.bind sha policyRaw stateRaw NativePlanVectors.qc configRaw
      NativeAccumulatorVectors.proofOriginal profileRaw = none :=
  NativeSourceRefusal.coefficientsUnavailable rawMembersPrepared
    (substitutedProofRejected configRaw profileRaw)
theorem rawJoinRejectsSubstitution {codec store trust anchor}
    (binding : NativeBinding.Binding codec trust anchor store)
    (configRaw profileRaw : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) (domain : Bytes) (index : Nat) :
    NativeVectorJoin.run binding sha policyRaw stateRaw NativePlanVectors.qc configRaw
      NativeAccumulatorVectors.proofOriginal profileRaw permission inputs domain index = none :=
  NativeSourceRefusal.runUnavailable binding (originalCannotUse004Proof configRaw profileRaw)

theorem missingProofRejected (configRaw profileRaw : Bytes) :
    NativePlanCoefficients.bind sha policyRaw stateRaw NativePlanVectors.qc
      configRaw [] profileRaw = none :=
  NativeSourceRefusal.coefficientsUnavailable rawMembersPrepared
    (NativeSourceRefusal.proofBytesUnavailable (by rfl))
theorem rawJoinRejectsMissing {codec store trust anchor}
    (binding : NativeBinding.Binding codec trust anchor store)
    (configRaw profileRaw : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs : List NativeAvailableQ.Input) (domain : Bytes) (index : Nat) :
    NativeVectorJoin.run binding sha policyRaw stateRaw NativePlanVectors.qc
      configRaw [] profileRaw permission inputs domain index = none :=
  NativeSourceRefusal.runUnavailable binding (missingProofRejected configRaw profileRaw)
"""


if __name__ == "__main__":
    lean, data = generate()
    (ROOT / "formal/proofs/DeltaReduce/NativePlanSourceVectors.lean").write_text(
        lean, encoding="utf-8", newline="\n"
    )
    write_canonical_json(ROOT / "formal/proposals/native-plan-source-vectors.json", data)
    print(json.dumps(data))
