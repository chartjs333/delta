"""Exact retained native seed wire/JSON and computed ISC edge, not randomness proof."""

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
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeSeedTranscriptVectors.lean"


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
    seed = docs["SEED"]
    tree = policy["snapshot"]["seed_transcripts"][0]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": seed["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "SEED_TRANSCRIPT",
    }
    if (
        projected != seed
        or raw.count(codec.encode_value("seed", tree)) != 1
        or codec.HEADER + codec.encode_value("policy", policy) != raw
        or canonical_json_bytes(seed).hex() != observed["certificates"]["SEED"]["json_hex"]
        or seed["input_set_certificate_id"] != content_id(certificate)
        or seed["input_set_certificate_id"] not in policy["snapshot"]["finalized_input_set_ids"]
    ):
        raise ValueError("original seed section/JSON/finalized ISC edge changed")
    return seed, tree, certificate, committee, observed


def generate():
    seed, tree, certificate, _, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    def texts(xs):
        return "[" + ",".join(asc(x) for x in xs) + "]"

    out = [
        "import DeltaReduce.NativeSeedSection",
        "import DeltaReduce.NativeIscCertificateVectors",
        "",
        "/-! Original seed/ISC component bytes. Synthetic SHA and metadata, "
        "no randomness authentication. -/",
        "namespace DeltaReduce.NativeSeedTranscriptVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeSeedTranscript",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 100000",
        "def transcript : Transcript := ⟨NativeIscAdmissionVectors.inputContext,"
        + asc(seed["input_set_certificate_id"])
        + ","
        + asc(seed["seed_id"])
        + ","
        + asc(seed["seed_profile_id"])
        + ","
        + texts(seed["share_ids"])
        + "⟩",
        "def tree : Value := " + lean_value("seed", tree),
        "theorem parsed : read tree = some transcript := by rfl",
        "theorem valid : Valid transcript.context transcript := by decide",
        "def originalJSON : Bytes := " + lit(canonical_json_bytes(seed)),
        "theorem exactJSON : json transcript = originalJSON := by rfl",
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

    encoded = encode("seed", tree)
    wire = codec.encode_value("seed", tree)
    out += [
        "def wire : Bytes := " + lit(wire),
        f"theorem encoded : encode fmtSeed tree = some wire := {encoded}",
        "theorem decoded : decode fmtSeed wire = some tree := NativePolicyCodec.encoded encoded",
    ]
    body = isc.native.isc.cases()["pinned-vote-fixture"]
    pres = [
        b"deltareduce.008.input-set-certificate.v1\0" + canonical_json_bytes(certificate),
        isc.native_isc_body.DOMAIN + body.encode(),
        b"deltareduce.008.seed-transcript.v1\0" + canonical_json_bytes(seed),
    ]
    assert "sha256:" + hashlib.sha256(pres[2]).hexdigest() == observed["certificates"]["SEED"]["id"]
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
    out.append("def transcriptId : Bytes := " + asc(content_id(seed)))
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
        "theorem transcriptComputed : id sha transcript = some transcriptId "
        ":= contentFromHash rfl hash2 rfl rfl",
        "def checked : Checked := ⟨transcript,tree,transcriptId⟩",
        "theorem parentIdentity : transcript.isc = NativeIscCertificateVectors.qc := rfl",
        "theorem certificateChecked : NativeIscCertificate.check sha "
        "transcript.context NativeIscCertificateVectors.committee "
        "NativeIscCertificateVectors.tree = some "
        "NativeIscCertificateVectors.checked := "
        "NativeIscCertificate.fromComponents "
        "NativeIscCertificateVectors.parsed NativeIscCertificateVectors.valid"
        " qcComputed bodyComputed",
        "theorem seedChecked : check sha transcript.context "
        "[NativeIscCertificateVectors.qc] tree = some checked := "
        "fromComponents parsed valid (by simp only "
        "[parentIdentity,List.mem_singleton]) transcriptComputed",
        "theorem originalEdge : linked sha transcript.context "
        "NativeIscCertificateVectors.committee "
        "NativeIscCertificateVectors.tree tree = some "
        "(NativeIscCertificateVectors.checked,checked) := "
        "linkedFromComponents certificateChecked seedChecked",
        "theorem originalByteChecked : fromBytes sha transcript.context "
        "[NativeIscCertificateVectors.qc] wire = some checked := "
        "bytesFromComponents (by decide) decoded seedChecked",
        "theorem primitiveIsNotTranscript : transcript.seed ≠ transcriptId := by decide",
        "theorem missingFinalizedParent : check sha transcript.context [] "
        "tree = none := wrongParentRejected parsed (by simp)",
        "theorem bodyIsNotQcParent : check sha transcript.context "
        "[NativeIscCertificateVectors.bodyId] tree = none := "
        "wrongParentRejected parsed (by decide)",
        "theorem transcriptIsNotQcParent : check sha transcript.context "
        "[transcriptId] tree = none := wrongParentRejected parsed (by decide)",
        "theorem changedIscParent : check sha transcript.context "
        "[NativeIscCertificateVectors.qc] (value {transcript with isc := "
        "transcriptId}) = none := wrongParentRejected (valueRead _) (by "
        "decide)",
        "theorem emptyShares : ¬ Valid transcript.context {transcript with "
        "shares := []} := by decide",
        "theorem duplicateShares : ¬ Valid transcript.context {transcript "
        "with shares := transcript.shares ++ transcript.shares} := by decide",
        "theorem invalidShare : ¬ Valid transcript.context {transcript with "
        'shares := [NativeVoteBytes.ascii "bad"]} := by decide',
        "theorem wrongContext : ¬ Valid {transcript.context with view := 1} "
        "transcript := by decide",
        "theorem wrongSeedShape : ¬ Valid transcript.context {transcript with"
        " seed := []} := by decide",
        "theorem wrongProfileShape : ¬ Valid transcript.context {transcript "
        "with profile := []} := by decide",
        "theorem failedHash : check (fun _ => []) transcript.context "
        "[NativeIscCertificateVectors.qc] tree = none := missingHashRejected "
        "_ _ _",
        "theorem singletonSeeds : checkAll sha transcript.context "
        "[NativeIscCertificateVectors.qc] [tree] = some [checked] := "
        "listFromComponents seedChecked rfl",
        "theorem uniqueTranscriptSet : NativeSeedSection.Ordered [checked] := by decide",
        "theorem duplicateTranscriptSet : ¬ NativeSeedSection.Ordered "
        "[checked,checked] := by decide",
        "-- A reconfigured primitive seed remains structurally valid: "
        "randomness is not authenticated.",
        "theorem alternateSeedStillShapeValid : Valid transcript.context "
        "{transcript with seed := NativeIscCertificateVectors.qc} := by "
        "decide",
        "end DeltaReduce.NativeSeedTranscriptVectors",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print("GENERATED_PINNED_SEED_TRANSCRIPT_COMPONENTS")
