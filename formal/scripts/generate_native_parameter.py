"""Pinned original PARAMETER components; computed body bytes, finite synthetic SHA."""

import hashlib
import json
from pathlib import Path

import generate_native_plan as plangen
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id
from native_isc_body import Context, text, u64

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeParameterVectors.lean"


def source():
    _, _, _, docs, committee, observed = plangen.source()
    doc = docs["PARAMETER"]
    policies_doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(policies_doc)).hexdigest() != (
        "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    policies = {}
    for name in ["codec-PARAMETER", "codec-AGGREGATE_ROOT"]:
        row = next(r for r in policies_doc["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        policies[name] = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", policies[name]) != raw:
            raise ValueError("original policy wire changed")
    proposed = policies["codec-PARAMETER"]["snapshot"]["parameter_bodies"][0]
    snapshot = policies["codec-AGGREGATE_ROOT"]["snapshot"]
    tree = snapshot["parameter_qcs"][0]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": doc["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "PARAMETER_SHARD_QC",
    }
    expected = {k: v for k, v in tree.items() if k not in ["quorum_threshold", "signer_ids"]}
    key = {k: doc[k] for k in ["domain_id", "shard_id"]}
    if (
        projected != doc
        or {k: v for k, v in proposed.items() if k != "vote_context_id"} != expected
        or proposed["vote_context_id"] != "PARAMETER:domain-a:shard-a"
        or canonical_json_bytes(doc).hex() != observed["certificates"]["PARAMETER"]["json_hex"]
        or content_id(doc) != observed["certificates"]["PARAMETER"]["id"]
        or snapshot["finalized_parameter_ids"] != [content_id(doc)]
        or snapshot["required_parameter_keys"] != [key]
        or doc["input_set_certificate_id"] != content_id(docs["ISC"])
        or doc["eligibility_certificate_id"] != content_id(docs["EC"])
        or doc["aggregation_plan_certificate_id"] != content_id(docs["APC"])
    ):
        raise ValueError("original PARAMETER section/JSON/parent edge changed")
    return doc, tree, proposed, docs, committee, observed


def body_bytes(doc):
    """Source-derived consensus.cpp hash projection, not a new native observation."""

    def texts(xs):
        return u64(len(xs)) + b"".join(text(x) for x in xs)

    return (
        Context(**{key: doc[key] for key in Context.__annotations__}).encode()
        + text(doc["aggregation_plan_certificate_id"])
        + u64(doc["denominator"])
        + text(doc["domain_id"])
        + text(doc["eligibility_certificate_id"])
        + texts(doc["input_leaf_ids"])
        + text(doc["input_set_certificate_id"])
        + texts(doc["result_numerators"])
        + text(doc["shard_id"])
    )


def generate():
    doc, tree, proposed, _, _, _ = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    def strings(xs):
        return "[" + ",".join(map(asc, xs)) + "]"

    common = (
        "⟨NativeIscAdmissionVectors.inputContext,"
        + asc(doc["aggregation_plan_certificate_id"])
        + ","
        + str(doc["denominator"])
        + ","
        + asc(doc["domain_id"])
        + ","
        + asc(doc["eligibility_certificate_id"])
        + ","
        + strings(doc["input_leaf_ids"])
        + ","
        + asc(doc["input_set_certificate_id"])
        + ","
        + strings(doc["result_numerators"])
        + ","
        + asc(doc["shard_id"])
        + "⟩"
    )
    out = [
        "import DeltaReduce.NativeParameterSection",
        "import DeltaReduce.NativePlanVectors",
        "",
        "/-! Original typed certificate/policy components. No new native run or "
        "whole policy acceptance. -/",
        "namespace DeltaReduce.NativeParameterVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeParameter",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def certificate : Certificate := ⟨"
        + common
        + ","
        + str(doc["quorum_threshold"])
        + ","
        + strings(doc["signer_ids"])
        + "⟩",
        "def body : Body := ⟨certificate.common," + asc(proposed["vote_context_id"]) + "⟩",
        "def tree : Value := " + lean_value("parameter", tree),
        "def bodyTree : Value := " + lean_value("parameter_body", proposed),
        "theorem treeValue : tree = value certificate := by rfl",
        "theorem parsed : read tree = some certificate := treeValue ▸ valueRead certificate",
        "theorem bodyTreeValue : bodyTree = bodyValue body := by rfl",
        "theorem bodyParsed : readBody bodyTree = some body := bodyTreeValue ▸ bodyRead body",
        "theorem commonValid : CommonValid certificate.common.context certificate.common := "
        "⟨NativeIscCertificateVectors.valid.2.1.1,rfl," + ",".join(["by decide"] * 14) + "⟩",
        "theorem valid : Valid certificate.common.context "
        "NativeIscCertificateVectors.committee certificate := "
        "⟨commonValid,NativeIscCertificateVectors.valid.1,NativeIscCertificateVectors.valid.2.2⟩",
        "def originalJSON : Bytes := " + lit(canonical_json_bytes(doc)),
        "theorem exactJSON : json certificate = originalJSON := by rfl",
    ]
    cache = {}

    def encode(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        vector = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            proof = "(by rfl)"
            for field, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[field])} {proof})"
        elif vector:
            proof = "(by rfl)"
            for item in reversed(value):
                proof = f"(encodedCons {encode(vector[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[key] = name
        out.append(
            f"theorem {name} : encode ({format_of(kind)}) ({lean_value(kind, value)}) "
            f"= some {lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    for kind, name, fmt, var in [
        ("parameter", "wire", "fmtParameter", "tree"),
        ("parameter_body", "bodyWire", "fmtParameterBody", "bodyTree"),
    ]:
        obj = tree if kind == "parameter" else proposed
        proof = encode(kind, obj)
        out += [
            "def " + name + " : Bytes := " + lit(codec.encode_value(kind, obj)),
            f"theorem {name}Encoded : encode {fmt} {var} = some {name} := {proof}",
            f"theorem {name}Decoded : NativePolicyCodec.decode {fmt} {name} = some {var} := "
            f"NativePolicyCodec.encoded {name}Encoded",
        ]
    raw = body_bytes(doc)
    pres = [
        b"deltareduce.008.parameter-shard-qc.v1\0" + canonical_json_bytes(doc),
        b"deltareduce.vote.parameter-body.v1\0" + raw,
    ]
    bid = "sha256:" + hashlib.sha256(pres[1]).hexdigest()
    out += [
        "def computedBodyBytes : Bytes := " + lit(raw),
        "theorem exactBodyBytes : bodyBytes body = computedBodyBytes := by rfl",
    ]
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := {lit(pre)}")
    expr = "NativePlanVectors.sha raw"
    for i in reversed(range(2)):
        expr = f"if raw = preimage{i} then {lit(hashlib.sha256(pres[i]).digest())} else {expr}"
    out.append("def sha (raw : Bytes) : Bytes := " + expr)
    for i, pre in enumerate(pres):
        proof = (
            "by unfold sha; rw [if_pos rfl]"
            if i == 0
            else "by unfold sha; rw [if_neg (by decide),if_pos rfl]"
        )
        out.append(
            f"theorem hash{i} : sha preimage{i} = {lit(hashlib.sha256(pre).digest())} := {proof}"
        )
    out.append(
        "theorem shaFallback {raw} (h0 : raw ≠ preimage0) (h1 : raw ≠ preimage1) : "
        "sha raw = NativePlanVectors.sha raw := by simp only [sha,if_neg h0,if_neg h1]"
    )
    for i in range(8):
        var = (
            f"NativeEligibilityVectors.preimage{i}"
            if i < 6
            else f"NativePlanVectors.preimage{i - 6}"
        )
        out.append(
            f"theorem oldHash{i} : sha {var} = NativePlanVectors.sha {var} := "
            f"shaFallback (by decide) (by decide)"
        )
    out.append(
        "theorem contentFromHash {domain raw pre digest expected} (preimage : "
        "domain ++ [0] ++ raw = pre) (hashed : sha pre = digest) (size : "
        'digest.length = 32) (spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) : NativeStateBytes.contentId "
        "sha domain raw = some expected := by simp only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,"
        "hashed,size,ite_true,spelling]"
    )
    prior_ids = [
        (
            "iscHash",
            "NativeIscCertificate.id",
            "NativeIscCertificateVectors.certificate",
            "NativeIscCertificateVectors.qc",
            0,
        ),
        (
            "iscBodyHash",
            "NativeInputSetBody.bodyId",
            "NativeIscCertificateVectors.certificate.body",
            "NativeIscCertificateVectors.bodyId",
            1,
        ),
        (
            "normHash",
            "NativeNormEvidence.id",
            "NativeNormEvidenceVectors.evidence",
            "NativeNormEvidenceVectors.evidenceId",
            2,
        ),
        (
            "seedHash",
            "NativeSeedTranscript.id",
            "NativeSeedTranscriptVectors.transcript",
            "NativeSeedTranscriptVectors.transcriptId",
            3,
        ),
        (
            "ecHash",
            "NativeEligibility.id",
            "NativeEligibilityVectors.certificate",
            "NativeEligibilityVectors.qc",
            4,
        ),
        ("planHash", "NativePlan.id", "NativePlanVectors.certificate", "NativePlanVectors.qc", 6),
    ]
    for name, fn, value, result, i in prior_ids:
        old = (
            f"(NativePlanVectors.oldHash{i}.trans NativeEligibilityVectors.hash{i})"
            if i < 6
            else "NativePlanVectors.hash0"
        )
        out.append(
            f"theorem {name} : {fn} sha {value} = some {result} := "
            f"contentFromHash rfl (oldHash{i}.trans {old}) rfl rfl"
        )
    # Reuse the already checked component proofs, substituting only the six hash lemmas above.
    prior = (ROOT / "formal/proofs/DeltaReduce/NativePlanVectors.lean").read_text("utf-8")
    for name in ["originalIscChecked", "originalNormChecked", "originalSeedChecked", "ecChecked"]:
        line = next(x for x in prior.splitlines() if x.startswith("theorem " + name + " "))
        out.append(line)
    out += [
        "theorem planChecked : NativePlanLineage.check sha .finalized certificate.common.context "
        "NativeIscCertificateVectors.committee [NativeIscCertificateVectors.checked] "
        "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
        "NativePlanVectors.certificate.common.accumulator [NativeEligibilityVectors.finalEdge] "
        "[NativeSeedTranscriptVectors.checked] NativePlanVectors.tree = some "
        "NativePlanVectors.finalEdge := "
        "NativePlanLineage.fromComponents ⟨rfl,NativePlanVectors.parsed,"
        "NativePlanVectors.parentFound,"
        "NativePlanVectors.ecFound,NativePlanVectors.seedFound,"
        "NativePlanVectors.valid,NativePlanVectors.parentsValid,planHash⟩",
        "def qc : Bytes := " + asc(content_id(doc)),
        "def bid : Bytes := " + asc(bid),
        "theorem qcComputed : id sha certificate = some qc := contentFromHash rfl hash0 rfl rfl",
        "theorem bodyComputed : bodyId sha body = some bid := contentFromHash rfl hash1 rfl rfl",
        "theorem distinctIdentities : qc ≠ bid := by decide",
        "def keys : List Key := [⟨certificate.common.domain,certificate.common.shard⟩]",
        "def proposal : Certificate := proposedCertificate "
        "NativeIscCertificateVectors.committee body",
        "theorem proposalValid : Valid certificate.common.context "
        "NativeIscCertificateVectors.committee proposal := "
        "⟨commonValid,NativeIscCertificateVectors.valid.1,by decide⟩",
        "theorem proposalParsed : NativeParameterLineage.decode .proposed "
        "NativeIscCertificateVectors.committee "
        "bodyTree = some (proposal,body.voteContext) := by "
        "simp only [NativeParameterLineage.decode,bodyParsed,bind,Option.bind]; rfl",
        "theorem finalParsed : NativeParameterLineage.decode .finalized "
        "NativeIscCertificateVectors.committee "
        "tree = some (certificate,[]) := by simp only "
        "[NativeParameterLineage.decode,parsed,bind,Option.bind]",
    ]
    for name, collection, eqfield, target in [
        ("parentFound", "[NativeIscCertificateVectors.checked]", "qcId", "isc"),
        ("ecFound", "[NativeEligibilityVectors.finalEdge]", "id", "ec"),
        ("planFound", "[NativePlanVectors.finalEdge]", "id", "plan"),
    ]:
        out.append(
            f"theorem {name} : {collection}.find? (fun e => e.{eqfield} == "
            f"certificate.common.{target}) = some {collection[1:-1]} := by rfl"
        )
    guard_args = (
        "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] [NativePlanVectors.qc] keys"
    )
    parents = (
        "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
        "NativePlanVectors.finalEdge"
    )
    args = (
        "certificate.common.context NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] "
        + guard_args
        + " [NativeEligibilityVectors.finalEdge] [NativePlanVectors.finalEdge]"
    )
    for mode, cert, ctx, var, parse, valid, hashed in [
        ("finalized", "certificate", "[]", "tree", "finalParsed", "valid", "qcComputed"),
        (
            "proposed",
            "proposal",
            "body.voteContext",
            "bodyTree",
            "proposalParsed",
            "proposalValid",
            "bodyComputed",
        ),
    ]:
        out += [
            f"def {mode}Edge : NativeParameterLineage.Edge := ⟨{cert},{ctx},{var},"
            + ("qc" if mode == "finalized" else "bid")
            + ",NativeIscCertificateVectors.checked,NativeEligibilityVectors.finalEdge,"
            "NativePlanVectors.finalEdge⟩",
            f"theorem {mode}Parents : NativeParameterLineage.NativeParentChecks "
            f".{mode} {guard_args} {cert} {ctx} {parents} := by decide",
            f"theorem {mode}Source : NativeParameterLineage.Source sha .{mode} "
            f"{args} {var} {mode}Edge := "
            f"⟨rfl,{parse},parentFound,ecFound,planFound,{valid},{mode}Parents,{hashed}⟩",
            f"theorem {mode}Checked : NativeParameterLineage.check sha .{mode} "
            f"{args} {var} = some {mode}Edge := "
            f"NativeParameterLineage.fromComponents {mode}Source",
        ]
    out += negative_vectors()
    return "\n".join([*out, "end DeltaReduce.NativeParameterVectors", ""])


def negative_vectors():
    return [
        'def otherBody : Body := {body with voteContext := NativeVoteBytes.ascii "other-context"}',
        "theorem sameHashDifferentContext : bodyId sha otherBody = bodyId sha "
        "body := contextNotInBodyHash sha body _",
        "theorem contextPolicyDifferent : bodyValue otherBody ≠ bodyValue body "
        ":= contextRetained _ _ _ (by decide)",
        "theorem firstAssignment : assignments [] [body] = true := by decide",
        "theorem duplicateContext : assignments [] [body,body] = false := by decide",
        "theorem conflictingAssignment : assignments [] [body,otherBody] = false := by decide",
        "def secondBody : Body := "
        '{otherBody with common := {body.common with shard := NativeVoteBytes.ascii "shard-b"}}',
        "theorem distinctAssignments : assignments [] [body,secondBody] = true := by decide",
        "theorem differentKeySameContext : assignments [] [body,"
        "{secondBody with voteContext := body.voteContext}] = false := by decide",
        "theorem emptyAssignment : assignments [] "
        "[{body with voteContext := []}] = false := by decide",
        "theorem nativeContextOnlyNonempty : AssignmentStep [] "
        "{body with voteContext := [0,255]} := by decide",
        "theorem keyOrder : NativePolicyBytes.strictly keyLT [assignmentKey body "
        "|>.2,assignmentKey secondBody |>.2] = true := by decide",
        "theorem reversedKeys : NativePolicyBytes.strictly keyLT [assignmentKey "
        "secondBody |>.2,assignmentKey body |>.2] = false := by decide",
        "theorem duplicateKeys : NativePolicyBytes.strictly keyLT (keys ++ keys) "
        "= false := by decide",
        "theorem zeroDenominator : ¬ CommonValid certificate.common.context "
        "{certificate.common with denominator := 0} := "
        "by intro h; have bad := denominatorPositive h; contradiction",
        "theorem overflowDenominator : ¬ CommonValid certificate.common.context "
        "{certificate.common with denominator := 2^64} := "
        "by intro h; have bad := denominatorBound h; contradiction",
        "theorem emptyLeaves : ¬ CommonValid certificate.common.context "
        "{certificate.common with leaves := []} := "
        "by intro h; have bad := leavesNonempty h; contradiction",
        "theorem duplicateLeaves : ¬ CommonValid certificate.common.context "
        "{certificate.common with leaves := certificate.common.leaves ++ "
        "certificate.common.leaves} := "
        "by intro h; have bad := leavesOrdered h; contradiction",
        "theorem emptyResults : ¬ CommonValid certificate.common.context "
        "{certificate.common with numerators := []} := "
        "by intro h; have bad := resultsNonempty h; contradiction",
        "theorem originalNegativeSpelling : NativeCertificateDecimal.Valid false "
        '(NativeVoteBytes.ascii "-01") := by decide',
        "theorem notCanonicalNegativeSpelling : ¬ "
        'NativeCertificateDecimal.Canonical (NativeVoteBytes.ascii "-01") := by decide',
        "theorem negativeOverflow : ¬ NativeCertificateDecimal.Valid false "
        '(NativeVoteBytes.ascii "-9223372036854775809") := by decide',
        "theorem positiveOverflow : ¬ NativeCertificateDecimal.Valid false "
        '(NativeVoteBytes.ascii "9223372036854775808") := by decide',
        "theorem stringResultsNotDerived : CommonValid "
        "certificate.common.context "
        '{certificate.common with numerators := [NativeVoteBytes.ascii "-01"],'
        "denominator := 17} := "
        "⟨commonValid.1,commonValid.2.1,commonValid.2.2.1,commonValid.2.2.2.1,"
        "commonValid.2.2.2.2.1," + ",".join(["by decide"] * 11) + "⟩",
        "theorem emptyRequiredRejectsProposal : ¬ "
        "NativeParameterLineage.ProposedChecks [] certificate.common body.voteContext "
        "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
        "NativePlanVectors.finalEdge := by decide",
        "theorem finalizedDoesNotCheckAssignment : "
        "NativeParameterLineage.NativeParentChecks .finalized "
        "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
        "[NativePlanVectors.qc] [] certificate [] "
        "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
        "NativePlanVectors.finalEdge := by decide",
        "theorem unfinalizedPlan : ¬ NativeParameterLineage.NativeParentChecks .finalized "
        "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] [] keys certificate [] "
        "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
        "NativePlanVectors.finalEdge := by decide",
    ]


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
