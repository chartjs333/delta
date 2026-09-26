"""Pinned native ISC JSON and DVPOL section; finite SHA samples, no authentication."""

import hashlib
import json
from pathlib import Path

import generate_native_certificate_chain as native
import native_isc_body
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeIscCertificateVectors.lean"


def source():
    doc = load_json_strict(native.FOLDER / "cpp-cross-check.json")
    blobs = native.blobs()
    code, spans = native.harness(blobs)
    expected = native.expected_components()
    if (
        doc["observed"] != expected
        or doc["source_commit"] != native.SOURCE
        or doc["source_sha256"] != {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()}
        or doc["harness_sha256"] != hashlib.sha256(code.encode()).hexdigest()
        or doc["extracted_definitions"] != spans
        or doc["native_export_authenticated"] is not False
        or doc["gate_eligible"] is not False
    ):
        raise ValueError("pinned native certificate evidence changed")
    policy_doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if (
        hashlib.sha256(canonical_json_bytes(policy_doc)).hexdigest()
        != "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    rows = policy_doc["observed"]
    row = next(r for r in rows if r["name"] == "codec-EC")
    raw = bytes.fromhex(row["policy_hex"])
    p = codec.decode(raw)
    if codec.HEADER + codec.encode_value("policy", p) != raw:
        raise ValueError("original native policy does not reencode")
    cert = p["snapshot"]["input_set_certificates"][0]
    docs, _, _, _ = native.fixture()
    c = docs["ISC"]
    projected = {
        **cert["context"],
        **{k: v for k, v in cert.items() if k != "context"},
        "formal_semantics_id": c["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "INPUT_SET_CERTIFICATE",
    }
    wire = codec.encode_value("input_set", cert)
    if (
        projected != c
        or raw.count(wire) != 1
        or canonical_json_bytes(c).hex() != expected["certificates"]["ISC"]["json_hex"]
    ):
        raise ValueError("original policy section/certificate bytes differ")
    return c, cert, p["validator_ids"], expected


def generate():
    c, tree, committee, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    def texts(xs):
        return "[" + ",".join(asc(x) for x in xs) + "]"

    out = [
        "import DeltaReduce.NativeFinalizedIscSection",
        "import DeltaReduce.NativeIscAdmissionVectors",
        "",
        "/-! Original native ISC JSON and policy section. Synthetic "
        "committee/SHA; no exporter authentication. -/",
        "namespace DeltaReduce.NativeIscCertificateVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeIscCertificate",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def certificate : Certificate := ⟨NativeIscAdmissionVectors.inputBody,"
        + str(c["quorum_threshold"])
        + ","
        + texts(c["signer_ids"])
        + "⟩",
        "def committee : List Bytes := " + texts(committee),
        "def tree : Value := " + lean_value("input_set", tree),
        "theorem parsed : read tree = some certificate := by rfl",
        "theorem valid : Valid certificate.body.context committee certificate := by decide",
        "def originalJSON : Bytes := " + lit(canonical_json_bytes(c)),
        "theorem exactJSON : json certificate = originalJSON := by rfl",
    ]
    cache = {}

    def encode(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        vec = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            proof = "(by rfl)"
            for field, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[field])} {proof})"
        elif vec:
            proof = "(by rfl)"
            for item in reversed(value):
                proof = f"(encodedCons {encode(vec[0], item)} {proof})"
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

    encoded = encode("input_set", tree)
    wire = codec.encode_value("input_set", tree)
    out += [
        "def wire : Bytes := " + lit(wire),
        f"theorem encoded : encode fmtInputSet tree = some wire := {encoded}",
        "theorem decoded : decode fmtInputSet wire = some tree := "
        "NativePolicyCodec.encoded encoded",
    ]
    alternate = {**c, "signer_ids": ["validator-1", "validator-2", "validator-4"]}
    qcpre = b"deltareduce.008.input-set-certificate.v1\0" + canonical_json_bytes(c)
    qcpre2 = b"deltareduce.008.input-set-certificate.v1\0" + canonical_json_bytes(alternate)
    # Original binary body preimage, separate from certificate JSON.
    body = native.isc.cases()["pinned-vote-fixture"]
    bodypre = native_isc_body.DOMAIN + body.encode()
    pres = [qcpre, bodypre, qcpre2]
    if (
        "sha256:" + hashlib.sha256(bodypre).hexdigest() != observed["bodies"]["ISC"]
        or content_id(alternate) != observed["alternate_signer_qc"]
    ):
        raise ValueError("native identity/preimage mismatch")
    out += [
        "def alternative : Certificate := {certificate with signers := "
        + texts(alternate["signer_ids"])
        + "}"
    ]
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
    for n, doc in [("qc", c), ("alternativeQc", alternate)]:
        out.append(f"def {n} : Bytes := " + asc(content_id(doc)))
    out.append("def bodyId : Bytes := " + asc(observed["bodies"]["ISC"]))
    out += [
        "theorem contentFromHash {domain raw pre digest expected} (preimage :"
        " domain ++ [0] ++ raw = pre) (hashed : sha pre = digest) (size : "
        'digest.length = 32) (spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) : "
        "NativeStateBytes.contentId sha domain raw = some expected := by simp"
        " only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,hashed,size,ite_true,spelling]",
        "theorem qcComputed : id sha certificate = some qc := contentFromHash rfl hash0 rfl rfl",
        "theorem bodyComputed : NativeInputSetBody.bodyId sha "
        "certificate.body = some bodyId := contentFromHash rfl hash1 rfl rfl",
        "theorem alternativeComputed : id sha alternative = some "
        "alternativeQc := contentFromHash rfl hash2 rfl rfl",
        "def checked : Checked := ⟨certificate,tree,qc,bodyId⟩",
        "theorem originalChecked : check sha certificate.body.context "
        "committee tree = some checked := fromComponents parsed valid "
        "qcComputed bodyComputed",
        "theorem originalByteChecked : fromBytes sha certificate.body.context"
        " committee wire = some checked := bytesFromComponents (by decide) "
        "decoded originalChecked",
        "theorem distinctIds : qc ≠ bodyId := by decide",
        "theorem changedSignersChangeQc : qc ≠ alternativeQc := by decide",
        "theorem changedSignersKeepBody : alternative.body = certificate.body := rfl",
        "theorem unknownSigner : ¬ Valid certificate.body.context committee "
        "{certificate with signers := [NativeVoteBytes.ascii "
        '"validator-1",NativeVoteBytes.ascii '
        '"validator-2",NativeVoteBytes.ascii "validator-9"]} := by decide',
        "theorem duplicateSigner : ¬ Valid certificate.body.context committee"
        " {certificate with signers := [NativeVoteBytes.ascii "
        '"validator-1",NativeVoteBytes.ascii '
        '"validator-1",NativeVoteBytes.ascii "validator-2"]} := by decide',
        "theorem reversedSigners : ¬ Valid certificate.body.context committee"
        " {certificate with signers := certificate.signers.reverse} := by "
        "decide",
        "theorem belowQuorum : ¬ Valid certificate.body.context committee "
        "{certificate with signers := certificate.signers.take 2} := by "
        "decide",
        "theorem wrongThreshold : ¬ Valid certificate.body.context committee "
        "{certificate with threshold := 2} := by decide",
        "theorem wrongContext : ¬ Valid {certificate.body.context with view "
        ":= 1} committee certificate := by decide",
        "theorem emptyTuples : ¬ Valid certificate.body.context committee "
        "{certificate with body := {certificate.body with tuples := []}} := "
        "by decide",
        "theorem duplicateTuples : ¬ Valid certificate.body.context committee"
        " {certificate with body := {certificate.body with tuples := "
        "certificate.body.tuples ++ certificate.body.tuples}} := by decide",
        "theorem malformedRoot : ¬ Valid certificate.body.context committee "
        "{certificate with body := {certificate.body with root := []}} := by "
        "decide",
        "theorem emptyCommittee : ¬ Valid certificate.body.context [] certificate := by decide",
        "theorem wrongCommitteeSize : ¬ Valid certificate.body.context "
        "(committee.take 3) certificate := by decide",
        "theorem duplicateCommittee : ¬ Valid certificate.body.context "
        "(committee ++ committee) certificate := by decide",
        "theorem hashFailure : check (fun _ => []) certificate.body.context "
        "committee tree = none := missingHashRejected _ _ _",
        "theorem singletonList : checkAll sha certificate.body.context "
        "committee [tree] = some [checked] := listFromComponents "
        "originalChecked rfl",
        "-- These set cases use arbitrary headers: no full-policy section acceptance is claimed.",
        "def sectionFixture (p : NativePolicyBytes.Policy) (s : "
        "NativeStateBytes.State) : NativeFinalizedIscSection.Bound := "
        "⟨p,s,[],[],[],[tree],[checked],[qc]⟩",
        "theorem sectionSets (p s) : NativeFinalizedIscSection.SetChecks "
        "(sectionFixture p s) := by decide",
        "theorem missingCertificate (p s) : ¬ "
        "NativeFinalizedIscSection.SetChecks {(sectionFixture p s) with "
        "certificates := []} := by decide",
        "theorem duplicateCertificate (p s) : ¬ "
        "NativeFinalizedIscSection.SetChecks {(sectionFixture p s) with "
        "certificates := [checked,checked]} := by decide",
        "theorem duplicateFinalized (p s) : ¬ "
        "NativeFinalizedIscSection.SetChecks {(sectionFixture p s) with "
        "finalized := [qc,qc]} := by decide",
        "theorem bodyIdIsNotFinalizedQc (p s) : ¬ "
        "NativeFinalizedIscSection.SetChecks {(sectionFixture p s) with "
        "finalized := [bodyId]} := by decide",
        "end DeltaReduce.NativeIscCertificateVectors",
        "",
    ]
    out = [
        line.replace(
            " := by decide",
            " := by dsimp only [NativeFinalizedIscSection.SetChecks,sectionFixture]; decide",
        )
        if line.startswith("theorem ") and "(p s)" in line
        else line
        for line in out
    ]
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print("GENERATED_PINNED_ISC_CERTIFICATE_COMPONENTS")
