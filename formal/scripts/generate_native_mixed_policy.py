"""Original two-candidate policy using existing checked byte components."""

import hashlib
import re
from pathlib import Path

import native_policy_codec as codec
from check_native_proposal_replay import verify_document
from formal_artifacts import load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_policy_wal import wal_entries

ROOT = Path(__file__).resolve().parents[2]


def generate():
    doc = load_json_strict(
        ROOT / "formal/proposals/evidence/native-proposal-replay/cpp-cross-check.json"
    )
    verify_document(doc)
    row = next(r for r in doc["observed"] if r["name"] == "no-snapshot")
    raw = bytes.fromhex(row["policy_hex"])
    p = codec.decode(raw)
    entries = wal_entries(bytes.fromhex(row["wal_hex"]))
    reuse = {}
    for module in ["NativeIscAdmissionVectors", "NativeConfigAdmissionVectors"]:
        source = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
        for name, expression in re.findall(
            r"^theorem (encoding\d+) : NativePolicyCodec.encode (.*?) = some", source, re.M
        ):
            reuse[expression] = module + "." + name
    out = [
        "import DeltaReduce.NativeProposalAdmissionVectors",
        "import DeltaReduce.NativeTransitionVectors",
        "",
        "/-! Original mixed policy, component byte proofs and ten finite SHA samples.",
        "These samples are not SHA correctness or authenticated exporter provenance. -/",
        "namespace DeltaReduce.NativeMixedPolicyVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema "
        "NativeStateBytes NativeTransition",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 2000000",
        "def tree : Value := " + lean_value("policy", p),
        "def policy : NativePolicyBytes.Policy := "
        "{NativeProposalAdmissionVectors.policy with source := tree}",
        "theorem extracted : NativePolicyBytes.extract tree = some policy := by rfl",
    ]
    cache = {}

    def encode(kind, value):
        expr = f"({format_of(kind)}) ({lean_value(kind, value)})"
        if expr in reuse:
            return reuse[expr]
        if expr in cache:
            return cache[expr]
        vec = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            proof = "(by rfl)"
            for k, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[k])} {proof})"
        elif vec:
            proof = "(by rfl)"
            for item in reversed(value):
                proof = f"(encodedCons {encode(vec[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[expr] = name
        out.append(
            f"theorem {name} : NativePolicyCodec.encode {expr} = "
            f"some {lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    name = encode("policy", p)
    out += [
        "def policyBody : Bytes := " + lit(raw[16:]),
        "def policyRaw : Bytes := NativePolicyBytes.header ++ policyBody",
        f"theorem encoded : NativePolicyCodec.encode fmtPolicy tree = some policyBody := {name}",
        "theorem canonical : NativePolicyBytes.Canonical policy := by decide",
        "theorem parsed : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy) :=",
        "  NativePolicyBytes.encoded encoded extracted canonical (by decide)",
        "theorem originalPolicyBytes : policyRaw = NativeWalVectors.policy2 := by rfl",
    ]
    # Preserve native domain preimages exactly. No label root or invented digest.
    from check_native_isc_admission import original

    single, _, _ = original()
    body = single["snapshot"]["input_set_bodies"][0]
    import native_isc_body as isc

    values = [
        ("policyRaw", raw),
        (
            "NativeVoteBytes.votePreimage NativeReceiptVectors.frame2",
            b"deltareduce:003:vote:v1\0" + entries[0]["command"],
        ),
    ]
    # The existing Python helpers define the exact original context domains.
    epoch = p["validator_epoch_id"].encode("ascii")
    round_id = p["round_id"].encode("ascii")

    values += [
        (
            "NativeConfigAdmission.configPreimage 1 policy.epoch",
            b"deltareduce.vote-context.config.v1\0"
            + (1).to_bytes(8, "big")
            + len(epoch).to_bytes(8, "big")
            + epoch,
        ),
        (
            "NativeIscAdmission.iscPreimage policy.round",
            b"deltareduce.vote-context.isc.v1\0" + len(round_id).to_bytes(8, "big") + round_id,
        ),
        (
            "contentPreimage NativeInputSetBody.bodyDomain NativeIscAdmissionVectors.inputRaw",
            isc.DOMAIN + isc.from_fields(body).encode(),
        ),
    ]
    for domain, expression, value in [
        ("state", "NativeStateCodecVectors.raw3", bytes.fromhex(row["initial_hex"])),
        ("command", "NativeWalVectors.command3", entries[1]["command"]),
        ("state", "NativeWalVectors.state3", entries[1]["state"]),
        ("effect", "NativeWalVectors.effects3", entries[1]["effects"]),
        ("wal", "NativeWalVectors.record3", entries[1]["record"]),
    ]:
        spelling = {"state": "round-state", "effect": "effect-batch", "wal": "wal-record"}.get(
            domain, domain
        )
        values.append(
            (
                f"contentPreimage {domain}Domain {expression}",
                b"deltareduce:003:" + spelling.encode() + b":v1\0" + value,
            )
        )
    digests = [hashlib.sha256(value).hexdigest() for _, value in values]
    assert digests[0].encode() == entries[0]["record"]
    assert "sha256:" + digests[2] == p["candidates"][0]["context_id"]
    assert "sha256:" + digests[3] == p["candidates"][1]["context_id"]
    assert "sha256:" + digests[4] == p["candidates"][1]["body_hash"]
    assert "sha256:" + digests[5] == p["snapshot"]["state_id"]
    for i, (expr, _) in enumerate(values):
        out.append(f"def preimage{i} : Bytes := {expr}")
    out.append("def sha (raw : Bytes) : Bytes :=")
    for i, (_, value) in enumerate(values):
        out.append(
            f"  {'if' if i == 0 else 'else if'} raw = preimage{i} "
            f"then {lit(hashlib.sha256(value).digest())}"
        )
    out.append("  else []")
    for i, (_, value) in enumerate(values):
        out.append(
            f"theorem hash{i} : sha preimage{i} = {lit(hashlib.sha256(value).digest())} := by"
        )
        out.append("  unfold sha")
        for j in range(i):
            out.append(f"  rw [if_neg (by decide : preimage{i} ≠ preimage{j})]")
        out.append("  rw [if_pos rfl]")
    out.append("end DeltaReduce.NativeMixedPolicyVectors")
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    (ROOT / "formal/proofs/DeltaReduce/NativeMixedPolicyVectors.lean").write_text(
        generate(), encoding="utf-8", newline="\n"
    )
