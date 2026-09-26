"""Exact retained native norm wire/JSON and computed ISC edge, not norm recomputation proof."""

import hashlib
import json
from pathlib import Path

import generate_native_isc_certificate as isc
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeNormEvidenceVectors.lean"


def source():
    certificate, _, committee, observed = isc.source()
    policy_doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(policy_doc)).hexdigest() != (
        "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    row = next(r for r in policy_doc["observed"] if r["name"] == "codec-EC")
    raw = bytes.fromhex(row["policy_hex"])
    policy = codec.decode(raw)
    docs, _, _, _ = isc.native.fixture()
    norm = docs["NORM"]
    tree = policy["snapshot"]["norm_evidence"][0]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": norm["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "NORM_EVIDENCE",
    }
    if (
        projected != norm
        or raw.count(codec.encode_value("norm", tree)) != 1
        or codec.HEADER + codec.encode_value("policy", policy) != raw
        or canonical_json_bytes(norm).hex() != observed["certificates"]["NORM"]["json_hex"]
        or norm["input_set_certificate_id"] != content_id(certificate)
        or norm["input_set_certificate_id"] not in policy["snapshot"]["finalized_input_set_ids"]
    ):
        raise ValueError("original norm section/JSON/finalized ISC edge changed")
    return norm, tree, certificate, committee, observed


def generate():
    norm, tree, certificate, _, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    out = [
        "import DeltaReduce.NativeNormSection",
        "import DeltaReduce.NativeIscCertificateVectors",
        "",
        "/-! Original norm/ISC component bytes. Synthetic SHA and metadata, "
        "no norm recomputation. -/",
        "namespace DeltaReduce.NativeNormEvidenceVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeNormEvidence",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def evidence : Evidence := ⟨NativeIscAdmissionVectors.inputContext,["
        + ",".join(
            "⟨"
            + str(e["scale_denominator"])
            + ","
            + asc(e["squared_norm"])
            + ","
            + asc(e["ticket_id"])
            + "⟩"
            for e in norm["entries"]
        )
        + "],"
        + asc(norm["input_set_certificate_id"])
        + ","
        + asc(norm["norm_root"])
        + "⟩",
        "def tree : Value := " + lean_value("norm", tree),
        "theorem parsed : read tree = some evidence := by rfl",
        "theorem valid : Valid evidence.context evidence := by decide",
        "def originalJSON : Bytes := " + lit(canonical_json_bytes(norm)),
        "theorem exactJSON : json evidence = originalJSON := by rfl",
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

    encoded = encode("norm", tree)
    wire = codec.encode_value("norm", tree)
    out += [
        "def wire : Bytes := " + lit(wire),
        f"theorem encoded : encode fmtNorm tree = some wire := {encoded}",
        "theorem decoded : decode fmtNorm wire = some tree := NativePolicyCodec.encoded encoded",
    ]
    body = isc.native.isc.cases()["pinned-vote-fixture"]
    pres = [
        b"deltareduce.008.input-set-certificate.v1\0" + canonical_json_bytes(certificate),
        isc.native_isc_body.DOMAIN + body.encode(),
        b"deltareduce.008.norm-evidence.v1\0" + canonical_json_bytes(norm),
    ]
    assert "sha256:" + hashlib.sha256(pres[2]).hexdigest() == observed["certificates"]["NORM"]["id"]
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := {lit(pre)}")
    expr = "[]"
    for i in reversed(range(3)):
        expr = f"if raw = preimage{i} then {lit(hashlib.sha256(pres[i]).digest())} else {expr}"
    out.append("def sha (raw : Bytes) : Bytes := " + expr)
    for i in range(3):
        out.append(
            f"theorem hash{i} : sha preimage{i} = "
            f"{lit(hashlib.sha256(pres[i]).digest())} := by decide"
        )
    out.append("def evidenceId : Bytes := " + asc(content_id(norm)))
    out += [
        "theorem contentFromHash {domain raw pre digest expected} (preimage :"
        " domain ++ [0] ++ raw = pre) (hashed : sha pre = digest) (size : "
        'digest.length = 32) (spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) : "
        "NativeStateBytes.contentId sha domain raw = some expected := by simp"
        " only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,hashed,size,ite_true,spelling]",
        "theorem qcComputed : NativeIscCertificate.id sha "
        "NativeIscCertificateVectors.certificate = some "
        "NativeIscCertificateVectors.qc := contentFromHash rfl hash0 rfl rfl",
        "theorem bodyComputed : NativeInputSetBody.bodyId sha "
        "NativeIscCertificateVectors.certificate.body = some "
        "NativeIscCertificateVectors.bodyId := contentFromHash rfl hash1 rfl "
        "rfl",
        "theorem evidenceComputed : id sha evidence = some evidenceId "
        ":= contentFromHash rfl hash2 rfl rfl",
        "def checked : Checked := ⟨evidence,tree,evidenceId⟩",
        "theorem parentIdentity : evidence.isc = NativeIscCertificateVectors.qc := rfl",
        "theorem certificateChecked : NativeIscCertificate.check sha "
        "evidence.context NativeIscCertificateVectors.committee "
        "NativeIscCertificateVectors.tree = some "
        "NativeIscCertificateVectors.checked := "
        "NativeIscCertificate.fromComponents "
        "NativeIscCertificateVectors.parsed NativeIscCertificateVectors.valid"
        " qcComputed bodyComputed",
        "theorem normChecked : check sha evidence.context "
        "[NativeIscCertificateVectors.qc] tree = some checked := "
        "fromComponents parsed valid (by simp only "
        "[parentIdentity,List.mem_singleton]) evidenceComputed",
        "theorem originalEdge : linked sha evidence.context "
        "NativeIscCertificateVectors.committee "
        "NativeIscCertificateVectors.tree tree = some "
        "(NativeIscCertificateVectors.checked,checked) := "
        "linkedFromComponents certificateChecked normChecked",
        "theorem originalByteChecked : fromBytes sha evidence.context "
        "[NativeIscCertificateVectors.qc] wire = some checked := "
        "bytesFromComponents (by decide) decoded normChecked",
        "theorem primitiveRootIsNotEvidence : evidence.root ≠ evidenceId := by decide",
        "theorem missingFinalizedParent : check sha evidence.context [] "
        "tree = none := wrongParentRejected parsed (by simp)",
        "theorem bodyIsNotQcParent : check sha evidence.context "
        "[NativeIscCertificateVectors.bodyId] tree = none := "
        "wrongParentRejected parsed (by decide)",
        "theorem evidenceIsNotQcParent : check sha evidence.context "
        "[evidenceId] tree = none := wrongParentRejected parsed (by decide)",
        "theorem changedIscParent : check sha evidence.context "
        "[NativeIscCertificateVectors.qc] (value {evidence with isc := "
        "evidenceId}) = none := wrongParentRejected (valueRead _) (by "
        "decide)",
        "theorem emptyEntries : ¬ Valid evidence.context {evidence with entries := "
        "[]} := by decide",
        "theorem duplicateEntries : ¬ Valid evidence.context {evidence with entries "
        ":= evidence.entries ++ evidence.entries} := by decide",
        "theorem zeroScale : ¬ EntryValid ⟨0,NativeVoteBytes.ascii "
        '"1",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem scaleOverflow : ¬ EntryValid ⟨2^64,NativeVoteBytes.ascii "
        '"1",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem maxScale : EntryValid ⟨2^64-1,NativeVoteBytes.ascii "
        '"1",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem maxNorm : EntryValid ⟨1,NativeVoteBytes.ascii "
        '"9223372036854775807",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem overflowNorm : ¬ EntryValid ⟨1,NativeVoteBytes.ascii "
        '"9223372036854775808",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem negativeNorm : ¬ EntryValid ⟨1,NativeVoteBytes.ascii "
        '"-1",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem negativeSingleZero : ¬ EntryValid ⟨1,NativeVoteBytes.ascii "
        '"-0",NativeVoteBytes.ascii "ticket-a"⟩ := by decide',
        "theorem wrongContext : ¬ Valid {evidence.context with view := 1} evidence := by decide",
        "theorem wrongRootShape : ¬ Valid evidence.context {evidence with root := []} := by decide",
        'theorem invalidTicket : ¬ EntryValid ⟨1,NativeVoteBytes.ascii "1",[]⟩ := by decide',
        'def zero : Entry := ⟨1,NativeVoteBytes.ascii "0",NativeVoteBytes.ascii "ticket-a"⟩',
        'def negativeZero : Entry := {zero with squared := NativeVoteBytes.ascii "-00"}',
        "theorem noncanonicalAccepted : EntryValid negativeZero := by decide",
        "theorem noncanonicalEvidenceAcceptedShape : Valid evidence.context "
        "{evidence with entries := [negativeZero]} := by decide",
        "theorem equalNumbers : NativeCertificateDecimal.number zero.squared = "
        "NativeCertificateDecimal.number negativeZero.squared := by decide",
        "theorem distinctOriginalJSON : entryJSON zero ≠ entryJSON negativeZero := by decide",
        "theorem originalNegativeZeroBytes : readEntry (entryValue negativeZero) = "
        "some negativeZero := entryRead _",
        "theorem normalizedWholeJSONDiffers : json {evidence with entries := [zero]}"
        " ≠ json {evidence with entries := [negativeZero]} := by decide",
        "theorem failedHash : check (fun _ => []) evidence.context "
        "[NativeIscCertificateVectors.qc] tree = none := missingHashRejected "
        "_ _ _",
        "theorem singletonNorms : checkAll sha evidence.context "
        "[NativeIscCertificateVectors.qc] [tree] = some [checked] := "
        "listFromComponents normChecked rfl",
        "theorem uniqueEvidenceSet : NativeNormSection.Ordered [checked] := by decide",
        "theorem duplicateEvidenceSet : ¬ NativeNormSection.Ordered [checked,checked] := by decide",
        "-- Native verify_norms does not establish root preimages or ISC ticket membership.",
        "theorem alternateRootStillShapeValid : Valid evidence.context {evidence "
        "with root := NativeIscCertificateVectors.qc} := by decide",
        "theorem unrelatedTicketStillShapeValid : Valid evidence.context {evidence "
        "with entries := [{zero with ticket := NativeVoteBytes.ascii "
        '"ticket-not-in-isc"}]} := by decide',
        "theorem reorderedEntries : ¬ Valid evidence.context {evidence with entries "
        ':= [{zero with ticket := NativeVoteBytes.ascii "z"},zero]} := by decide',
        "end DeltaReduce.NativeNormEvidenceVectors",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print("GENERATED_PINNED_NORM_EVIDENCE_COMPONENTS")
