"""Original APC components and parent composition; finite synthetic SHA only."""

import hashlib
import json
from pathlib import Path

import generate_native_eligibility as ecgen
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id, voted_body

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativePlanVectors.lean"


def source():
    _, _, _, _, docs, committee, observed = ecgen.source()
    doc = docs["APC"]
    policy_doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if (
        hashlib.sha256(canonical_json_bytes(policy_doc)).hexdigest()
        != "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    policies = {}
    for name in ["codec-APC", "codec-PARAMETER"]:
        row = next(r for r in policy_doc["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        policies[name] = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", policies[name]) != raw:
            raise ValueError("original policy wire changed")
    proposed = policies["codec-APC"]["snapshot"]["aggregation_plan_bodies"][0]
    tree = policies["codec-PARAMETER"]["snapshot"]["aggregation_plan_certificates"][0]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": doc["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "AGGREGATION_PLAN_CERTIFICATE",
    }
    projected["weights"] = [
        dict(e, alpha=dict(e["alpha"], numerator=str(e["alpha"]["numerator"])))
        for e in tree["weights"]
    ]
    expected_body = {k: v for k, v in tree.items() if k not in ["quorum_threshold", "signer_ids"]}
    accepted = [e["ticket_id"] for e in docs["EC"]["entries"] if e["accepted"]]
    if (
        projected != doc
        or proposed != expected_body
        or canonical_json_bytes(doc).hex() != observed["certificates"]["APC"]["json_hex"]
        or doc["input_set_certificate_id"] != content_id(docs["ISC"])
        or doc["eligibility_certificate_id"] != content_id(docs["EC"])
        or doc["seed_transcript_id"] != content_id(docs["SEED"])
        or doc["accumulator_proof_id"]
        != policies["codec-APC"]["snapshot"]["required_accumulator_proof_id"]
        or doc["accumulator_proof_id"]
        != policies["codec-PARAMETER"]["snapshot"]["required_accumulator_proof_id"]
        or accepted != [e["ticket_id"] for e in tree["bucket_assignments"]]
        or accepted != [e["ticket_id"] for e in tree["weights"]]
        or content_id(doc)
        != policies["codec-PARAMETER"]["snapshot"]["finalized_aggregation_plan_ids"][0]
    ):
        raise ValueError("original APC section/JSON/parent edge changed")
    return doc, tree, proposed, docs, committee, observed


def generate():
    doc, tree, proposed, _docs, _committee, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    buckets = ",".join(
        "⟨" + asc(e["bucket_id"]) + "," + asc(e["ticket_id"]) + "⟩"
        for e in doc["bucket_assignments"]
    )
    weights = ",".join(
        "⟨"
        + e["alpha"]["numerator"]
        + ","
        + str(e["alpha"]["denominator"])
        + ","
        + asc(e["ticket_id"])
        + "⟩"
        for e in doc["weights"]
    )
    common = (
        "⟨NativeIscAdmissionVectors.inputContext,"
        + asc(doc["accumulator_proof_id"])
        + ",["
        + buckets
        + "],"
        + asc(doc["eligibility_certificate_id"])
        + ","
        + asc(doc["input_set_certificate_id"])
        + ","
        + str(doc["iteration_count"])
        + ","
        + asc(doc["seed_transcript_id"])
        + ","
        + asc(doc["transcript_root"])
        + ",["
        + weights
        + "]⟩"
    )
    out = [
        "import DeltaReduce.NativePlanSection",
        "import DeltaReduce.NativeEligibilityVectors",
        "",
        ("/-! Original native components; no new native run or exporter authentication. -/"),
        "namespace DeltaReduce.NativePlanVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativePlan",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def certificate : Certificate := ⟨"
        + common
        + ","
        + str(doc["quorum_threshold"])
        + ",["
        + ",".join(asc(v) for v in doc["signer_ids"])
        + "]⟩",
        "def tree : Value := " + lean_value("plan", tree),
        "def bodyTree : Value := " + lean_value("plan_body", proposed),
        "theorem treeValue : tree = value certificate := by rfl",
        "theorem parsed : read tree = some certificate := treeValue ▸ valueRead certificate",
        "theorem bodyTreeValue : bodyTree = bodyValue certificate.common := by rfl",
        "theorem bodyParsed : readBody bodyTree = some certificate.common := "
        "bodyTreeValue ▸ bodyRead certificate.common",
        "theorem commonValid : CommonValid certificate.common.context certificate.common := "
        "⟨NativeIscCertificateVectors.valid.2.1.1,rfl," + ",".join(["by decide"] * 15) + "⟩",
        "theorem valid : Valid certificate.common.context "
        "NativeIscCertificateVectors.committee certificate := "
        "⟨commonValid,NativeIscCertificateVectors.valid.1,NativeIscCertificateVectors.valid.2.2⟩",
        (
            "theorem covered : Coverage certificate.common "
            "NativeEligibilityVectors.certificate := by decide"
        ),
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

    encoded = encode("plan", tree)
    body_encoded = encode("plan_body", proposed)
    out += [
        "def wire : Bytes := " + lit(codec.encode_value("plan", tree)),
        f"theorem encoded : encode fmtPlan tree = some wire := {encoded}",
        (
            "theorem decoded : NativePolicyCodec.decode fmtPlan wire = some tree := "
            "NativePolicyCodec.encoded encoded"
        ),
        "def bodyWire : Bytes := " + lit(codec.encode_value("plan_body", proposed)),
        f"theorem bodyEncoded : encode fmtPlanBody bodyTree = some bodyWire := {body_encoded}",
    ]
    voted = voted_body(doc)
    raw = bytes.fromhex(voted["payload_hex"])
    if voted["body_id"] != observed["bodies"]["APC"]:
        raise ValueError("native APC body ID changed")
    out += [
        "def originalBodyBytes : Bytes := " + lit(raw),
        ("theorem exactBodyBytes : bodyBytes certificate.common = originalBodyBytes := by rfl"),
    ]
    pres = [
        b"deltareduce.008.aggregation-plan-certificate.v1\0" + canonical_json_bytes(doc),
        voted["domain"].encode("ascii") + b"\0" + raw,
    ]
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := {lit(pre)}")
    expr = "NativeEligibilityVectors.sha raw"
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
        "sha raw = NativeEligibilityVectors.sha raw := by simp only [sha,if_neg h0,if_neg h1]"
    )
    for i in range(6):
        out.append(
            f"theorem oldHash{i} : sha NativeEligibilityVectors.preimage{i} = "
            f"NativeEligibilityVectors.sha NativeEligibilityVectors.preimage{i} := "
            "shaFallback (by decide) (by decide)"
        )
    out += [
        (
            "theorem contentFromHash {domain raw pre digest expected} (preimage : "
            "domain ++ [0] ++ raw = pre) (hashed : sha pre = digest) (size : "
            'digest.length = 32) (spelling : NativeVoteBytes.ascii "sha256:" ++ '
            "NativeVoteBytes.hexBytes digest = expected) : NativeStateBytes.contentId "
            "sha domain raw = some expected := by simp only "
            "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,hashed,size,ite_true,spelling]"
        ).replace('\\"', '"')
    ]
    out += [
        "theorem iscHash : NativeIscCertificate.id sha "
        "NativeIscCertificateVectors.certificate = some "
        + (
            "NativeIscCertificateVectors.qc := contentFromHash rfl (oldHash0.trans "
            "NativeEligibilityVectors.hash0) rfl rfl"
        ),
        "theorem iscBodyHash : NativeInputSetBody.bodyId sha "
        "NativeIscCertificateVectors.certificate.body = some "
        + (
            "NativeIscCertificateVectors.bodyId := contentFromHash rfl (oldHash1.trans "
            "NativeEligibilityVectors.hash1) rfl rfl"
        ),
        ("theorem normHash : NativeNormEvidence.id sha NativeNormEvidenceVectors.evidence = some ")
        + (
            "NativeNormEvidenceVectors.evidenceId := contentFromHash rfl "
            "(oldHash2.trans NativeEligibilityVectors.hash2) rfl rfl"
        ),
        "theorem seedHash : NativeSeedTranscript.id sha "
        "NativeSeedTranscriptVectors.transcript = some "
        + (
            "NativeSeedTranscriptVectors.transcriptId := contentFromHash rfl "
            "(oldHash3.trans NativeEligibilityVectors.hash3) rfl rfl"
        ),
    ]
    out += [
        ("theorem originalIscChecked : NativeIscCertificate.check sha certificate.common.context ")
        + ("NativeIscCertificateVectors.committee NativeIscCertificateVectors.tree = some ")
        + "NativeIscCertificateVectors.checked := NativeIscCertificate.fromComponents "
        + (
            "NativeIscCertificateVectors.parsed NativeIscCertificateVectors.valid "
            "iscHash iscBodyHash"
        ),
        ("theorem originalNormChecked : NativeNormEvidence.check sha certificate.common.context ")
        + "[NativeIscCertificateVectors.qc] NativeNormEvidenceVectors.tree = "
        "some NativeNormEvidenceVectors.checked := "
        "NativeNormEvidence.fromComponents NativeNormEvidenceVectors.parsed "
        "NativeNormEvidenceVectors.valid "
        "(by decide) normHash",
        ("theorem originalSeedChecked : NativeSeedTranscript.check sha certificate.common.context ")
        + "[NativeIscCertificateVectors.qc] NativeSeedTranscriptVectors.tree ="
        " some NativeSeedTranscriptVectors.checked := "
        "NativeSeedTranscript.fromComponents "
        "NativeSeedTranscriptVectors.parsed "
        "NativeSeedTranscriptVectors.valid "
        "(by decide) seedHash",
    ]
    out += [
        (
            "theorem ecHash : NativeEligibility.id sha "
            "NativeEligibilityVectors.certificate = some NativeEligibilityVectors.qc "
            ":= contentFromHash rfl (oldHash4.trans NativeEligibilityVectors.hash4) "
            "rfl rfl"
        ),
        (
            "theorem ecChecked : NativeEligibilityLineage.check sha .finalized "
            "certificate.common.context NativeIscCertificateVectors.committee "
            "[NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc] "
            "[NativeNormEvidenceVectors.checked] [NativeSeedTranscriptVectors.checked] "
            "NativeEligibilityVectors.finalTree = some "
            "NativeEligibilityVectors.finalEdge := "
            "NativeEligibilityLineage.fromComponents "
            "⟨rfl,NativeEligibilityVectors.finalParsed,NativeEligibilityVectors.parentFound,NativeEligibilityVectors.normFound,NativeEligibilityVectors.seedFound,NativeEligibilityVectors.valid,NativeEligibilityVectors.finalParents,ecHash⟩"
        ),
        "def qc : Bytes := " + asc(content_id(doc)),
        "def bid : Bytes := " + asc(voted["body_id"]),
        ("theorem qcComputed : id sha certificate = some qc := contentFromHash rfl hash0 rfl rfl"),
        (
            "theorem bodyComputed : bodyId sha certificate.common = some bid := "
            "contentFromHash rfl hash1 rfl rfl"
        ),
        (
            "def proposal : Certificate := proposedCertificate "
            "NativeIscCertificateVectors.committee certificate.common"
        ),
        (
            "theorem proposalValid : Valid certificate.common.context "
            "NativeIscCertificateVectors.committee proposal := "
            "⟨commonValid,NativeIscCertificateVectors.valid.1,by decide⟩"
        ),
        (
            "theorem proposalParsed : NativePlanLineage.decode .proposed "
            "NativeIscCertificateVectors.committee bodyTree = some proposal := by rfl"
        ),
        (
            "def finalEdge : NativePlanLineage.Edge := "
            "⟨certificate,tree,qc,NativeIscCertificateVectors.checked,NativeEligibilityVectors.finalEdge,NativeSeedTranscriptVectors.checked⟩"
        ),
        (
            "def proposedEdge : NativePlanLineage.Edge := "
            "⟨proposal,bodyTree,bid,NativeIscCertificateVectors.checked,NativeEligibilityVectors.finalEdge,NativeSeedTranscriptVectors.checked⟩"
        ),
        (
            "theorem parentFound : [NativeIscCertificateVectors.checked].find? (fun p "
            "=> p.qcId == certificate.common.isc) = some "
            "NativeIscCertificateVectors.checked := by rfl"
        ),
        (
            "theorem ecFound : [NativeEligibilityVectors.finalEdge].find? (fun e => "
            "e.id == certificate.common.ec) = some NativeEligibilityVectors.finalEdge "
            ":= by rfl"
        ),
        (
            "theorem seedFound : [NativeSeedTranscriptVectors.checked].find? (fun s => "
            "s.id == certificate.common.seed) = some "
            "NativeSeedTranscriptVectors.checked := by rfl"
        ),
        (
            "theorem parentsValid : NativePlanLineage.NativeParentChecks "
            "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
            "certificate.common.accumulator certificate "
            "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
            "NativeSeedTranscriptVectors.checked := by decide"
        ),
        (
            "theorem proposalParents : NativePlanLineage.NativeParentChecks "
            "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
            "certificate.common.accumulator proposal "
            "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
            "NativeSeedTranscriptVectors.checked := parentsValid"
        ),
    ]
    args = (
        "certificate.common.context NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc] "
        "[NativeEligibilityVectors.qc] certificate.common.accumulator "
        "[NativeEligibilityVectors.finalEdge] [NativeSeedTranscriptVectors.checked]"
    )
    for mode, tree_name, edge, parse, valid, parents, hashed in [
        ("finalized", "tree", "finalEdge", "parsed", "valid", "parentsValid", "qcComputed"),
        (
            "proposed",
            "bodyTree",
            "proposedEdge",
            "proposalParsed",
            "proposalValid",
            "proposalParents",
            "bodyComputed",
        ),
    ]:
        out += [
            (
                f"theorem {edge}Source : NativePlanLineage.Source sha .{mode} "
                f"{args} {tree_name} {edge} := "
                f"⟨rfl,{parse},parentFound,ecFound,seedFound,{valid},{parents},{hashed}⟩"
            ),
            (
                f"theorem {edge}Checked : NativePlanLineage.check sha .{mode} "
                f"{args} {tree_name} = some {edge} := "
                f"NativePlanLineage.fromComponents {edge}Source"
            ),
        ]
    out += [
        "theorem distinctIdentities : qc ≠ bid := by decide",
        (
            "theorem originalCoverage : Coverage finalEdge.certificate.common "
            "finalEdge.ec.certificate := NativePlanLineage.exactCoverage "
            "finalEdgeChecked"
        ),
        'def weight : Weight := ⟨1,1,NativeVoteBytes.ascii "ticket-a"⟩'.replace('\\"', '"'),
        (
            "def bucket : Bucket := ⟨NativeVoteBytes.ascii "
            '"bucket-a",NativeVoteBytes.ascii "ticket-a"⟩'
        ).replace('\\"', '"'),
    ]
    for name, value in {
        "negativeAlphaBits": "{weight with numerator := 2^64-1}",
        "signedMinimum": "{weight with numerator := 2^63}",
        "overflowNumerator": "{weight with numerator := 2^64}",
        "zeroDenominator": "{weight with denominator := 0}",
        "overflowDenominator": "{weight with denominator := 2^64}",
        "unreduced": "{weight with numerator := 2,denominator := 2}",
        "unreducedZero": "{weight with numerator := 0,denominator := 2}",
        "emptyTicket": "{weight with ticket := []}",
    }.items():
        out.append(f"theorem {name} : ¬ WeightValid ({value}) := by decide")
    for name, value in {
        "zeroAlpha": "{weight with numerator := 0}",
        "maxNumerator": "{weight with numerator := 2^63-1}",
        "maxDenominator": "{weight with denominator := 2^64-1}",
    }.items():
        out.append(f"theorem {name} : WeightValid ({value}) := by decide")
    for name, value, index in [
        ("zeroIterations", "{certificate.common with iterations := 0}", 8),
        ("overflowIterations", "{certificate.common with iterations := 2^32}", 9),
        ("emptyAssignments", "{certificate.common with buckets := []}", 10),
        ("duplicateAssignments", "{certificate.common with buckets := [bucket,bucket]}", 12),
        ("emptyWeights", "{certificate.common with weights := []}", 14),
        ("duplicateWeights", "{certificate.common with weights := [weight,weight]}", 16),
    ]:
        proj = {
            8: "iterationPositive",
            9: "iterationBound",
            10: "bucketsNonempty",
            12: "bucketsOrdered",
            14: "weightsNonempty",
            16: "weightsOrdered",
        }[index]
        out.append(
            f"theorem {name} : ¬ CommonValid certificate.common.context ({value}) := "
            f"by intro h; have bad := {proj} h; contradiction"
        )
    for name, value in {
        "missingWeights": "{certificate.common with weights := []}",
        "extraAssignment": "{certificate.common with buckets := [bucket,bucket]}",
        "wrongTicket": (
            '{certificate.common with weights := [⟨1,1,NativeVoteBytes.ascii "ticket-z"⟩]}'
        ),
    }.items():
        out.append(
            (
                f"theorem {name} : ¬ Coverage ({value}) "
                f"NativeEligibilityVectors.certificate := by decide"
            ).replace('\\"', '"')
        )
    out += [
        "def changedIsc : Bytes := certificate.common.accumulator",
        (
            "def otherIsc : NativeIscCertificate.Checked := "
            "{NativeIscCertificateVectors.checked with qcId := changedIsc}"
        ),
        (
            "def crossIscPlan : Certificate := {certificate with common := "
            "{certificate.common with isc := changedIsc}}"
        ),
        (
            "theorem noRepeatedCrossIscCheck : NativePlanLineage.NativeParentChecks "
            "[changedIsc] [NativeEligibilityVectors.qc] certificate.common.accumulator "
            "crossIscPlan otherIsc NativeEligibilityVectors.finalEdge "
            "NativeSeedTranscriptVectors.checked := by decide"
        ),
        (
            "theorem crossIscActuallyDifferent : crossIscPlan.common.isc ≠ "
            "NativeEligibilityVectors.certificate.common.isc := by decide"
        ),
        (
            "theorem wrongAccumulator : ¬ NativePlanLineage.NativeParentChecks "
            "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] [] "
            "certificate NativeIscCertificateVectors.checked "
            "NativeEligibilityVectors.finalEdge NativeSeedTranscriptVectors.checked := "
            "by decide"
        ),
        (
            "theorem unfinalizedEc : ¬ NativePlanLineage.NativeParentChecks "
            "[NativeIscCertificateVectors.qc] [] certificate.common.accumulator "
            "certificate NativeIscCertificateVectors.checked "
            "NativeEligibilityVectors.finalEdge NativeSeedTranscriptVectors.checked := "
            "by decide"
        ),
        (
            "theorem unfinalizedIsc : ¬ NativePlanLineage.NativeParentChecks [] "
            "[NativeEligibilityVectors.qc] certificate.common.accumulator certificate "
            "NativeIscCertificateVectors.checked NativeEligibilityVectors.finalEdge "
            "NativeSeedTranscriptVectors.checked := by decide"
        ),
        (
            "theorem bucketAndAlphaNotDerived : CommonValid certificate.common.context "
            "{certificate.common with buckets := [⟨NativeVoteBytes.ascii "
            '"different-bucket",bucket.ticket⟩],weights := [{weight with numerator := '
            "5}]} := by decide"
        ).replace('\\"', '"'),
        (
            "def entryA : NativeEligibility.Entry := ⟨1,NativeVoteBytes.ascii "
            '"domain-a",1,1,NativeVoteBytes.ascii "ACCEPTED",NativeVoteBytes.ascii '
            '"ticket-a"⟩'
        ),
        (
            "def entryB : NativeEligibility.Entry := {entryA with accepted := 0,ticket "
            ':= NativeVoteBytes.ascii "ticket-b"}'
        ),
        (
            "def entryC : NativeEligibility.Entry := {entryA with ticket := "
            'NativeVoteBytes.ascii "ticket-c"}'
        ),
        (
            "def severalEc : NativeEligibility.Certificate := "
            "{NativeEligibilityVectors.certificate with common := "
            "{NativeEligibilityVectors.certificate.common with entries := "
            "[entryA,entryB,entryC]}}"
        ),
        (
            "def severalPlan : Common := {certificate.common with buckets := "
            "[bucket,{bucket with ticket := entryC.ticket}],weights := [weight,{weight "
            "with ticket := entryC.ticket}]}"
        ),
        "theorem selectedCoverage : Coverage severalPlan severalEc := by decide",
        ("theorem severalValid : CommonValid certificate.common.context severalPlan := by decide"),
        (
            "theorem excludesRejectedTicket : ¬ Coverage {severalPlan with weights := "
            "[weight,{weight with ticket := entryB.ticket},{weight with ticket := "
            "entryC.ticket}]} severalEc := by decide"
        ),
        (
            "theorem reversedWeightsReject : ¬ Coverage {severalPlan with weights := "
            "severalPlan.weights.reverse} severalEc := by decide"
        ),
        (
            "theorem sortedAssignmentCoverage : Coverage {severalPlan with buckets := "
            "severalPlan.buckets.reverse} severalEc := by decide"
        ),
        (
            "theorem reversedAssignmentsInvalid : ¬ CommonValid "
            "certificate.common.context {severalPlan with buckets := "
            "severalPlan.buckets.reverse} := by decide"
        ),
        (
            "def allRejected : NativeEligibility.Certificate := "
            "{NativeEligibilityVectors.certificate with common := "
            "{NativeEligibilityVectors.certificate.common with entries := [{entryA "
            "with accepted := 0}]}}"
        ),
        (
            "theorem emptyCoverageOnly : Coverage {certificate.common with buckets := "
            "[],weights := []} allRejected := by decide"
        ),
        (
            "theorem rejectedCannotBuildPlan : ¬ Coverage certificate.common "
            "allRejected := emptyAcceptedImpossible valid.1 (by decide)"
        ),
        (
            "theorem maxIterations : CommonValid certificate.common.context "
            "{certificate.common with iterations := 2^32-1} := by decide"
        ),
        "end DeltaReduce.NativePlanVectors",
        "",
    ]
    for index, line in enumerate(out):
        if any(
            line.startswith("theorem " + name + " :")
            for name in ["severalValid", "bucketAndAlphaNotDerived", "maxIterations"]
        ):
            frame = ["commonValid" + ".2" * i + ".1" for i in range(7)]
            proof = "⟨" + ",".join(frame + ["by decide"] * 10) + "⟩"
            out[index] = line.replace("by decide", proof)
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
