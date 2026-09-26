"""Complete original EC certificate/body and checked parent components; synthetic SHA only."""

import hashlib
import json
from pathlib import Path

import generate_native_norm_evidence as normgen
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id, voted_body

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeEligibilityVectors.lean"


def source():
    norm, _, isc, committee, observed = normgen.source()
    docs, _, _, _ = normgen.isc.native.fixture()
    doc = docs["EC"]
    policy_doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(policy_doc)).hexdigest() != (
        "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    policies = {}
    for name in ["codec-EC", "codec-APC"]:
        row = next(r for r in policy_doc["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        policies[name] = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", policies[name]) != raw:
            raise ValueError("original policy wire changed")
    proposed = policies["codec-EC"]["snapshot"]["eligibility_bodies"][0]
    final = policies["codec-APC"]["snapshot"]["eligibility_certificates"][0]
    tree = final["certificate"]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": doc["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "ELIGIBILITY_CERTIFICATE",
    }
    projected["entries"] = [
        dict(e, gamma=dict(e["gamma"], numerator=str(e["gamma"]["numerator"])))
        for e in tree["entries"]
    ]
    body_expected = {k: v for k, v in tree.items() if k not in ["quorum_threshold", "signer_ids"]}
    body_expected["seed_transcript_id"] = content_id(docs["SEED"])
    if (
        projected != doc
        or proposed != body_expected
        or final["seed_transcript_id"] != content_id(docs["SEED"])
        or canonical_json_bytes(doc).hex() != observed["certificates"]["EC"]["json_hex"]
        or doc["input_set_certificate_id"] != content_id(isc)
        or doc["norm_evidence_id"] != content_id(norm)
        or content_id(doc) != policies["codec-APC"]["snapshot"]["finalized_eligibility_ids"][0]
    ):
        raise ValueError("original EC section/JSON/parent edge changed")
    return doc, tree, proposed, final, docs, committee, observed


def generate():
    doc, tree, proposed, final, docs, _committee, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    c = doc
    entries = ",".join(
        "⟨"
        + str(int(e["accepted"]))
        + ","
        + asc(e["domain_id"])
        + ","
        + str(e["gamma"]["numerator"])
        + ","
        + str(e["gamma"]["denominator"])
        + ","
        + asc(e["reason_code"])
        + ","
        + asc(e["ticket_id"])
        + "⟩"
        for e in c["entries"]
    )
    out = [
        "import DeltaReduce.NativeEligibilitySection",
        "import DeltaReduce.NativeNormEvidenceVectors",
        "import DeltaReduce.NativeSeedTranscriptVectors",
        "",
        "/-! Original native components; finite synthetic SHA, not exporter authentication. -/",
        "namespace DeltaReduce.NativeEligibilityVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeEligibility",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def certificate : Certificate := ⟨⟨NativeIscAdmissionVectors.inputContext,["
        + entries
        + "],"
        + asc(c["input_set_certificate_id"])
        + ","
        + asc(c["norm_evidence_id"])
        + ","
        + asc(c["robust_profile_id"])
        + "⟩,"
        + str(c["quorum_threshold"])
        + ",["
        + ",".join(asc(v) for v in c["signer_ids"])
        + "]⟩",
        "def tree : Value := " + lean_value("eligibility", tree),
        "def body : Body := ⟨certificate.common," + asc(proposed["seed_transcript_id"]) + "⟩",
        "def bodyTree : Value := " + lean_value("eligibility_body", proposed),
        "def finalTree : Value := " + lean_value("finalized_eligibility", final),
        "theorem parsed : read tree = some certificate := by rfl",
        "theorem bodyParsed : readBody bodyTree = some body := by rfl",
        "theorem finalParsed : NativeEligibilityLineage.decode .finalized "
        "NativeIscCertificateVectors.committee finalTree = some (certificate,body.seed) := by rfl",
        "theorem valid : Valid certificate.common.context "
        "NativeIscCertificateVectors.committee certificate := by decide",
        "theorem member : Membership certificate.common "
        "NativeIscCertificateVectors.checked := by decide",
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

    encoded = encode("eligibility", tree)
    body_encoded = encode("eligibility_body", proposed)
    final_encoded = encode("finalized_eligibility", final)
    out += [
        "def wire : Bytes := " + lit(codec.encode_value("eligibility", tree)),
        f"theorem encoded : encode fmtEligibility tree = some wire := {encoded}",
        "theorem decoded : NativePolicyCodec.decode fmtEligibility wire = "
        "some tree := NativePolicyCodec.encoded encoded",
        "def bodyWire : Bytes := " + lit(codec.encode_value("eligibility_body", proposed)),
        f"theorem bodyEncoded : encode fmtEligibilityBody bodyTree = some "
        f"bodyWire := {body_encoded}",
        "def finalWire : Bytes := " + lit(codec.encode_value("finalized_eligibility", final)),
        f"theorem finalEncoded : encode fmtFinalizedEligibility finalTree = "
        f"some finalWire := {final_encoded}",
    ]
    # Independently pinned native observations, including the separate seed edge.
    body_result = voted_body(doc, content_id(docs["SEED"]))
    domain = body_result["domain"]
    raw = bytes.fromhex(body_result["payload_hex"])
    body_id = body_result["body_id"]
    if body_id != observed["bodies"]["EC"]:
        raise ValueError("native EC body ID changed")
    out += [
        "def originalBodyBytes : Bytes := " + lit(raw),
        "theorem exactBodyBytes : bodyBytes body = originalBodyBytes := by rfl",
    ]
    iscbody = normgen.isc.native.isc.cases()["pinned-vote-fixture"]
    pres = [
        b"deltareduce.008.input-set-certificate.v1\0" + canonical_json_bytes(docs["ISC"]),
        normgen.isc.native_isc_body.DOMAIN + iscbody.encode(),
        b"deltareduce.008.norm-evidence.v1\0" + canonical_json_bytes(docs["NORM"]),
        b"deltareduce.008.seed-transcript.v1\0" + canonical_json_bytes(docs["SEED"]),
        b"deltareduce.008.eligibility-certificate.v1\0" + canonical_json_bytes(doc),
        domain.encode("ascii") + b"\0" + raw,
    ]
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := {lit(pre)}")
    expr = "[]"
    for i in reversed(range(len(pres))):
        expr = f"if raw = preimage{i} then {lit(hashlib.sha256(pres[i]).digest())} else {expr}"
    out.append("def sha (raw : Bytes) : Bytes := " + expr)
    for i, pre in enumerate(pres):
        out.append(
            f"theorem hash{i} : sha preimage{i} = {lit(hashlib.sha256(pre).digest())} := by decide"
        )
    out += [
        "theorem contentFromHash {domain raw pre digest expected} (preimage "
        ": domain ++ [0] ++ raw = pre)"
        " (hashed : sha pre = digest) (size : digest.length = 32) "
        '(spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) : "
        "NativeStateBytes.contentId sha domain raw = some expected := by simp only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,hashed,size,ite_true,spelling]",
        "theorem iscHash : NativeIscCertificate.id sha "
        "NativeIscCertificateVectors.certificate = some "
        "NativeIscCertificateVectors.qc := contentFromHash rfl hash0 rfl rfl",
        "theorem iscBodyHash : NativeInputSetBody.bodyId sha "
        "NativeIscCertificateVectors.certificate.body = some "
        "NativeIscCertificateVectors.bodyId := contentFromHash rfl hash1 rfl rfl",
        "theorem normHash : NativeNormEvidence.id sha NativeNormEvidenceVectors.evidence = some "
        "NativeNormEvidenceVectors.evidenceId := contentFromHash rfl hash2 rfl rfl",
        "theorem seedHash : NativeSeedTranscript.id sha "
        "NativeSeedTranscriptVectors.transcript = some "
        "NativeSeedTranscriptVectors.transcriptId := contentFromHash rfl hash3 rfl rfl",
        "def qc : Bytes := " + asc(content_id(doc)),
        "def bid : Bytes := " + asc(body_id),
        "theorem qcComputed : id sha certificate = some qc := contentFromHash rfl hash4 rfl rfl",
        "theorem bodyComputed : bodyId sha body = some bid := contentFromHash rfl hash5 rfl rfl",
        "def checked : Checked := ⟨certificate,tree,qc⟩",
        "theorem nativeCertificateChecked : check sha "
        "certificate.common.context NativeIscCertificateVectors.committee "
        "NativeIscCertificateVectors.checked "
        "NativeNormEvidenceVectors.evidenceId tree = some checked := "
        "fromComponents parsed valid member rfl qcComputed",
        "theorem originalIscChecked : NativeIscCertificate.check sha certificate.common.context "
        "NativeIscCertificateVectors.committee NativeIscCertificateVectors.tree = some "
        "NativeIscCertificateVectors.checked := NativeIscCertificate.fromComponents "
        "NativeIscCertificateVectors.parsed NativeIscCertificateVectors.valid iscHash iscBodyHash",
        "theorem originalNormChecked : NativeNormEvidence.check sha certificate.common.context "
        "[NativeIscCertificateVectors.qc] NativeNormEvidenceVectors.tree = "
        "some NativeNormEvidenceVectors.checked := "
        "NativeNormEvidence.fromComponents NativeNormEvidenceVectors.parsed "
        "NativeNormEvidenceVectors.valid "
        "(by decide) normHash",
        "theorem originalSeedChecked : NativeSeedTranscript.check sha certificate.common.context "
        "[NativeIscCertificateVectors.qc] NativeSeedTranscriptVectors.tree ="
        " some NativeSeedTranscriptVectors.checked := "
        "NativeSeedTranscript.fromComponents "
        "NativeSeedTranscriptVectors.parsed "
        "NativeSeedTranscriptVectors.valid "
        "(by decide) seedHash",
        "def finalEdge : NativeEligibilityLineage.Edge := ⟨certificate,body.seed,finalTree,qc,"
        "NativeIscCertificateVectors.checked,NativeNormEvidenceVectors.checked,NativeSeedTranscriptVectors.checked⟩",
        "def proposal : Certificate := proposedCertificate "
        "NativeIscCertificateVectors.committee body",
        "def proposedEdge : NativeEligibilityLineage.Edge := ⟨proposal,body.seed,bodyTree,bid,"
        "NativeIscCertificateVectors.checked,NativeNormEvidenceVectors.checked,NativeSeedTranscriptVectors.checked⟩",
        "theorem parentFound : [NativeIscCertificateVectors.checked].find? "
        "(fun p => p.qcId == certificate.common.isc) = some "
        "NativeIscCertificateVectors.checked := by rfl",
        "theorem normFound : [NativeNormEvidenceVectors.checked].find? "
        "(fun n => n.id == certificate.common.norm) = some "
        "NativeNormEvidenceVectors.checked := by rfl",
        "theorem seedFound : [NativeSeedTranscriptVectors.checked].find? "
        "(fun s => s.id == body.seed) = some "
        "NativeSeedTranscriptVectors.checked := by rfl",
        "theorem proposalValid : Valid certificate.common.context "
        "NativeIscCertificateVectors.committee proposal := by decide",
        "theorem proposalParsed : NativeEligibilityLineage.decode .proposed "
        "NativeIscCertificateVectors.committee bodyTree = some "
        "(proposal,body.seed) := by rfl",
        "theorem proposalParents : NativeEligibilityLineage.NativeParentChecks "
        ".proposed [NativeIscCertificateVectors.qc] proposal "
        "NativeIscCertificateVectors.checked NativeNormEvidenceVectors.checked "
        "NativeSeedTranscriptVectors.checked := by decide",
        "theorem finalParents : NativeEligibilityLineage.NativeParentChecks "
        ".finalized [NativeIscCertificateVectors.qc] certificate "
        "NativeIscCertificateVectors.checked NativeNormEvidenceVectors.checked "
        "NativeSeedTranscriptVectors.checked := by decide",
        "theorem finalEdgeSource : NativeEligibilityLineage.Source sha "
        ".finalized certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] "
        "[NativeIscCertificateVectors.qc] "
        "[NativeNormEvidenceVectors.checked] "
        "[NativeSeedTranscriptVectors.checked] finalTree finalEdge := "
        "⟨rfl,finalParsed,parentFound,normFound,seedFound,valid,finalParents,qcComputed⟩",
        "theorem proposalEdgeSource : NativeEligibilityLineage.Source sha "
        ".proposed certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] "
        "[NativeIscCertificateVectors.qc] "
        "[NativeNormEvidenceVectors.checked] "
        "[NativeSeedTranscriptVectors.checked] bodyTree proposedEdge := "
        "⟨rfl,proposalParsed,parentFound,normFound,seedFound,proposalValid,proposalParents,bodyComputed⟩",
        "theorem finalEdgeChecked : NativeEligibilityLineage.check sha "
        ".finalized certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] "
        "[NativeIscCertificateVectors.qc] "
        "[NativeNormEvidenceVectors.checked] "
        "[NativeSeedTranscriptVectors.checked] finalTree = some finalEdge :="
        " "
        "NativeEligibilityLineage.fromComponents finalEdgeSource",
        "theorem proposedEdgeChecked : NativeEligibilityLineage.check sha "
        ".proposed certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] "
        "[NativeIscCertificateVectors.qc] "
        "[NativeNormEvidenceVectors.checked] "
        "[NativeSeedTranscriptVectors.checked] bodyTree = some proposedEdge "
        ":= "
        "NativeEligibilityLineage.fromComponents proposalEdgeSource",
        "theorem distinctIdentities : qc ≠ bid ∧ body.seed ≠ "
        "NativeSeedTranscriptVectors.transcript.seed := by decide",
        "theorem nativeMemberCount : checked.certificate.common.entries.length = "
        "NativeIscCertificateVectors.checked.certificate.body.tuples.length "
        ":= exactMemberCount nativeCertificateChecked",
        "theorem missingMembers : ¬ Membership {certificate.common with entries := []} "
        "NativeIscCertificateVectors.checked := by decide",
        "theorem duplicatedMembers : ¬ Membership {certificate.common with entries := "
        "certificate.common.entries ++ certificate.common.entries} "
        "NativeIscCertificateVectors.checked := by decide",
        "def entry : Entry := "
        + ("⟨1," + asc("domain-a") + ",1,1," + asc("ACCEPTED") + "," + asc("ticket-a") + "⟩"),
    ]
    negatives = {
        "negativeGammaBits": "{entry with numerator := 2^64-1}",
        "minSignedGammaBits": "{entry with numerator := 2^63}",
        "overflowBits": "{entry with numerator := 2^64}",
        "zeroDenominator": "{entry with denominator := 0}",
        "overflowDenominator": "{entry with denominator := 2^64}",
        "unreducedGamma": "{entry with numerator := 2, denominator := 2}",
        "unreducedZero": "{entry with numerator := 0, denominator := 2}",
        "invalidBoolean": "{entry with accepted := 2}",
        "emptyReason": "{entry with reason := []}",
        "emptyDomain": "{entry with domain := []}",
        "emptyTicket": "{entry with ticket := []}",
    }
    for name, value in negatives.items():
        out.append(f"theorem {name} : ¬ EntryValid ({value}) := by decide")
    for name, value in {
        "zeroGamma": "{entry with numerator := 0}",
        "maxGamma": "{entry with numerator := 2^63-1}",
        "maxDenominator": "{entry with denominator := 2^64-1}",
        "decisionsNotDerived": (
            '{entry with accepted := 0, reason := NativeVoteBytes.ascii "ACCEPTED"}'
        ),
    }.items():
        out.append(f"theorem {name} : EntryValid ({value}) := by decide")
    for name, field, value in [
        ("changedTicket", "ticket", asc("ticket-z")),
        ("changedDomain", "domain", asc("domain-z")),
    ]:
        out.append(
            f"theorem {name} : ¬ Membership {{certificate.common with entries := "
            f"[{{entry with {field} := {value}}}]}} "
            f"NativeIscCertificateVectors.checked := by decide"
        )
    out += [
        "theorem wrongContext : ¬ Valid {certificate.common.context with view := 1} "
        "NativeIscCertificateVectors.committee certificate := by decide",
        "theorem missingSigners : ¬ Valid certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "{certificate with signers := []} := by decide",
        "theorem wrongThreshold : ¬ Valid certificate.common.context "
        "NativeIscCertificateVectors.committee "
        "{certificate with threshold := 2} := by decide",
        "theorem bodyIsNotIscQc : ¬ Membership {certificate.common with isc "
        ":= NativeIscCertificateVectors.bodyId} "
        "NativeIscCertificateVectors.checked := by decide",
        "theorem noFinalizedIsc : ¬ "
        "NativeEligibilityLineage.NativeParentChecks .finalized [] "
        "certificate "
        "NativeIscCertificateVectors.checked "
        "NativeNormEvidenceVectors.checked "
        "NativeSeedTranscriptVectors.checked := by decide",
        "def changedNorm : NativeNormEvidence.Checked := {NativeNormEvidenceVectors.checked with "
        "evidence := {NativeNormEvidenceVectors.evidence with isc := bid}}",
        "theorem proposedNormEqualityRequired : ¬ "
        "NativeEligibilityLineage.NativeParentChecks .proposed "
        "[NativeIscCertificateVectors.qc] certificate "
        "NativeIscCertificateVectors.checked changedNorm "
        "NativeSeedTranscriptVectors.checked := by decide",
        "theorem finalizedDoesNotRepeatNormEquality : "
        "NativeEligibilityLineage.NativeParentChecks .finalized "
        "[NativeIscCertificateVectors.qc] certificate "
        "NativeIscCertificateVectors.checked changedNorm "
        "NativeSeedTranscriptVectors.checked := by decide",
        "theorem changedSeedIscRejected : ¬ NativeEligibilityLineage.NativeParentChecks .finalized "
        "[NativeIscCertificateVectors.qc] certificate "
        "NativeIscCertificateVectors.checked "
        "NativeNormEvidenceVectors.checked "
        "{NativeSeedTranscriptVectors.checked with transcript := "
        "{NativeSeedTranscriptVectors.transcript with isc := bid}} := by "
        "decide",
        "end DeltaReduce.NativeEligibilityVectors",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print("exact native EC components and parent proofs generated")
