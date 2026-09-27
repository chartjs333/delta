"""Pinned original 008 contracts; synthetic source-derived pointer WAL examples.

No native execution, physical persistence, certificate authentication or GO.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "formal/proposals/evidence/native-current-pointer"
GOLDEN = EVIDENCE / "delta-protocol__fixtures__008__cross-language__golden-v1.json"
PIN = "adb42ccc2619007913cb4cacb8587a42d3a699b115fc20666db78436b685b108"


def inputs() -> dict:
    if sha256_file(GOLDEN) != PIN:
        raise ValueError("original 008 golden substituted")
    return load_json_strict(GOLDEN)


def ascii_lean(value: str) -> str:
    return "[" + ",".join(map(str, value.encode("ascii"))) + "]"


def context(value: dict) -> str:
    return (
        "⟨"
        + ",".join(
            str(value[key]) if key in ("height", "view") else ascii_lean(value[key])
            for key in (
                "arithmetic_profile_id",
                "height",
                "parameter_schema_id",
                "round_config_id",
                "round_id",
                "validator_epoch_id",
                "view",
            )
        )
        + "⟩"
    )


def generate() -> tuple[str, dict]:
    original = inputs()
    c = original["current_pointer_command"]["value"]
    q = original["apply_qc"]["value"]
    samples: list[tuple[bytes, bytes]] = []
    for key, domain in (
        ("current_pointer_command", "deltareduce.008.current-pointer-command.v1"),
        ("apply_qc", "deltareduce.008.apply-qc.v1"),
    ):
        raw = json.dumps(original[key]["value"], sort_keys=True, separators=(",", ":")).encode()
        assert raw.hex() == original[key]["bytes_hex"]
        pre = domain.encode() + b"\0" + raw
        digest = hashlib.sha256(pre).digest()
        assert "sha256:" + digest.hex() == original[key]["content_id"]
        samples.append((pre, digest))
    payload = "|".join(
        str(c[key])
        for key in (
            "height",
            "expected_parent_checkpoint_id",
            "next_checkpoint_id",
            "next_optimizer_hash",
            "apply_qc_id",
        )
    ).encode()
    samples.append((payload, hashlib.sha256(payload).digest()))
    # Rehashed, structurally well-formed unauthenticated stored IDs are accepted
    # by the low-level recovery checker. This is an explicit scope countercheck.
    fake = "|".join(
        (
            "9",
            c["expected_parent_checkpoint_id"],
            "sha256:" + "1" * 64,
            "sha256:" + "2" * 64,
            "sha256:" + "3" * 64,
        )
    ).encode()
    samples.append((fake, hashlib.sha256(fake).digest()))
    out = [
        "import DeltaReduce.NativePointerWal",
        "\n/-! Original 008 golden contracts; generated WAL is synthetic, not a native capture. -/",
        "namespace DeltaReduce.NativeCurrentPointerVectors",
        "open NativeReceiptBytes NativeCurrentPointer NativePointerWal",
        "set_option maxRecDepth 10000",
        "set_option maxHeartbeats 2000000",
        f"def command : Command := ⟨{context(c)},"
        + ",".join(
            ascii_lean(c[k])
            for k in (
                "apply_qc_id",
                "expected_parent_checkpoint_id",
                "next_checkpoint_id",
                "next_optimizer_hash",
            )
        )
        + "⟩",
        "def certificate : NativeApplyCertificate.Certificate := ⟨"
        + context(q)
        + ","
        + ",".join(
            ascii_lean(q[k])
            for k in (
                "aggregate_root_qc_id",
                "apply_arithmetic_profile_id",
                "apply_candidate_id",
                "next_model_hash",
                "next_optimizer_hash",
                "parent_checkpoint_id",
            )
        )
        + f",{q['quorum_threshold']},["
        + ",".join(map(ascii_lean, q["signer_ids"]))
        + "]⟩",
        f"def cid : Bytes := {ascii_lean(original['current_pointer_command']['content_id'])}",
        f"def qid : Bytes := {ascii_lean(original['apply_qc']['content_id'])}",
    ]
    for index, (pre, digest) in enumerate(samples):
        # NUL-containing preimages are composed explicitly, not Lean string escapes.
        parts = pre.split(b"\0")
        expr = " ++ [0] ++ ".join(ascii_lean(part.decode()) for part in parts)
        out += [f"def pre{index} : Bytes := {expr}", f"def digest{index} : Bytes := {list(digest)}"]
    out += ["def sha (raw : Bytes) : Bytes :="]
    out += [f"  if raw = pre{i} then digest{i} else" for i in range(len(samples))]
    out += ["  []"]
    for i in range(len(samples)):
        steps = ",".join([f"if_neg (by decide : pre{i} ≠ pre{j})" for j in range(i)] + ["ite_true"])
        out += [f"theorem hash{i} : sha pre{i} = digest{i} := by simp only [sha,{steps}]"]
    out += [
        "theorem commandValid : CommandValid command := by decide",
        "theorem qcValid : QcShape certificate := by decide",
        (
            "theorem commandPreimage : NativeStateBytes.contentPreimage domai"
            "n (json command) = pre0 := by rfl"
        ),
        (
            "theorem qcPreimage : NativeStateBytes.contentPreimage NativeAppl"
            "yCertificate.certificateDomain (NativeApplyCertificate.certifica"
            "teJSON certificate) = pre1 := by rfl"
        ),
        "theorem commandHash : commandId sha command = some cid := by",
        "  rw [commandId,if_pos commandValid]",
        "  apply NativeContractSize.fromComponents (by decide)",
        "  simp only [NativeStateBytes.contentId,commandPreimage,hash0]",
        "  rfl",
        "theorem certificateHash : qcId sha certificate = some qid := by",
        "  rw [qcId,if_pos qcValid]",
        "  apply NativeContractSize.fromComponents (by decide)",
        "  simp only [NativeStateBytes.contentId,qcPreimage,hash1]",
        "  rfl",
        "def prepared : Prepared := ⟨command,certificate,cid,qid⟩",
        "theorem preparedExact : prepare sha command certificate = some prepared :=",
        "  fromComponents ⟨rfl,rfl,commandHash,certificateHash,by decide⟩",
        (
            'def initial : State := ⟨command.parent,NativeVoteBytes.ascii "sh'
            "a256:77777777777777777777777777777777777777777777777777777777777"
            '77777",[],7⟩'
        ),
        "theorem initialValid : StateValid initial := by decide",
        "theorem firstAdvance : choose initial prepared = some .advanced := by decide",
        "theorem payloadExact : payload (record prepared) = pre2 := by rfl",
        "def lineBytes : Bytes := pre2 ++ [124] ++ NativeVoteBytes.hexBytes digest2 ++ [10]",
        "theorem lineExact : line sha (record prepared) = some lineBytes := by",
        "  simp only [line,checksum,payloadExact,hash2]; rfl",
        (
            "theorem originalLineParsed : readLine sha (pre2 ++ [124] ++ Nati"
            "veVoteBytes.hexBytes digest2) = some (record prepared) := by dec"
            "ide"
        ),
        (
            "theorem exactRecovery : recover sha initial (.bytes lineBytes) ="
            " some ⟨next prepared,[record prepared],[]⟩ := by decide"
        ),
        (
            "theorem replayRecovered : choose (next prepared) prepared = some"
            " .replay := replayAfterAdvance prepared"
        ),
        "theorem replayDoesNotExtend : ¬ Extends (next prepared) prepared := by decide",
        (
            "theorem afterDurabilityExact : execute sha initial command certi"
            "ficate .afterDurability = some ⟨initial,lineBytes,none⟩ := by"
        ),
        "  simp only [execute,preparedExact,firstAdvance,lineExact,bind,Option.bind,commitCut]",
        (
            "theorem returnedExact : execute sha initial command certificate "
            ".returned = some ⟨next prepared,lineBytes,some .advanced⟩ := by"
        ),
        "  simp only [execute,preparedExact,firstAdvance,lineExact,bind,Option.bind,commitCut]",
        (
            "theorem replayHasNoWrite : execute sha (next prepared) command c"
            "ertificate .duringAppend = some ⟨next prepared,[],some .replay⟩ "
            ":="
        ),
        "  exactReplayNoAppend preparedExact replayRecovered",
        "theorem unknownFresh : execute sha initial command certificate .unknown = none := by",
        "  simp only [execute,preparedExact,firstAdvance,lineExact,bind,Option.bind,commitCut]",
        (
            "theorem tornRetained : recover sha initial (.bytes (lineBytes ++"
            ' NativeVoteBytes.ascii "truncated")) = some ⟨next prepared,[reco'
            'rd prepared],NativeVoteBytes.ascii "truncated"⟩ := by decide'
        ),
        (
            "theorem onlyTornNoAdvance : recover sha initial (.bytes (NativeV"
            'oteBytes.ascii "truncated")) = some ⟨initial,[],NativeVoteBytes.'
            'ascii "truncated"⟩ := by decide'
        ),
        "theorem emptyKnown : recover sha initial (.bytes []) = some ⟨initial,[],[]⟩ := by decide",
        "theorem unknownNotEmpty : recover sha initial .unknown = none := rfl",
        (
            "theorem checksumSubstitution : recover sha initial (.bytes (pre2"
            ' ++ [124] ++ NativeVoteBytes.ascii "wrong\\n")) = none := by deci'
            "de"
        ),
        (
            "theorem doubleRecord : recover sha initial (.bytes (lineBytes ++"
            " lineBytes)) = none := by decide"
        ),
        "theorem emptyCompleteLine : recover sha initial (.bytes [10]) = none := by decide",
        (
            "theorem crlfRejected : recover sha initial (.bytes (pre2 ++ [124"
            "] ++ NativeVoteBytes.hexBytes digest2 ++ [13,10])) = none := by "
            "decide"
        ),
        (
            "theorem parentMismatch : recover sha {initial with checkpoint :="
            " command.checkpoint} (.bytes lineBytes) = none := by decide"
        ),
        (
            "theorem nonIncreasingHeight : recover sha {initial with height :"
            "= 8} (.bytes lineBytes) = none := by decide"
        ),
        (
            "theorem badReplayState : choose {next prepared with optimizer :="
            " command.parent} prepared = none := by decide"
        ),
        (
            "theorem wrongQcLink : ¬ Links {command with qc := command.parent"
            "} certificate qid := by decide"
        ),
        (
            "theorem wrongContext : ¬ Links {command with context := {command"
            ".context with view := 1}} certificate qid := by decide"
        ),
        (
            "theorem wrongModel : ¬ Links {command with checkpoint := command"
            ".parent} certificate qid := by decide"
        ),
        (
            "theorem wrongOptimizer : ¬ Links {command with optimizer := comm"
            "and.parent} certificate qid := by decide"
        ),
        (
            "theorem wrongParent : ¬ Links {command with parent := command.ch"
            "eckpoint} certificate qid := by decide"
        ),
        "theorem noSigners : ¬ QcShape {certificate with signers := []} := by decide",
        (
            "theorem duplicateSigners : ¬ QcShape {certificate with signers :"
            "= certificate.signers ++ certificate.signers} := by decide"
        ),
        (
            "theorem heightOverflow : ¬ CommandValid {command with context :="
            " {command.context with height := 256^8}} := by decide"
        ),
        (
            "theorem heightLeadingZero : NativeVoteBytes.parseDecimal (Native"
            'VoteBytes.ascii "08") = none := by decide'
        ),
        (
            "theorem unconfiguredSignerShape : QcShape {certificate with thre"
            'shold := 1,signers := [NativeVoteBytes.ascii "unconfigured"]} :='
            " by decide"
        ),
        "-- No QC body or signature is an input to recovery: rehashed stored IDs pass.",
        "def fakeLine : Bytes := pre3 ++ [124] ++ NativeVoteBytes.hexBytes digest3 ++ [10]",
        (
            "theorem rehashedUncertifiedRecovery : (recover sha initial (.byt"
            "es fakeLine)).isSome = true := by decide"
        ),
        "end DeltaReduce.NativeCurrentPointerVectors",
    ]
    return "\n".join(out) + "\n", {
        "scope": "ORIGINAL_008_GOLDEN_AND_SYNTHETIC_SOURCE_DERIVED_POINTER_WAL",
        "native_execution": False,
        "native_export_authenticated": False,
        "golden_sha256": PIN,
        "hash_samples": [
            {"preimage_hex": pre.hex(), "sha256": digest.hex()} for pre, digest in samples
        ],
        "line_hex": (payload + b"|" + samples[2][1].hex().encode() + b"\n").hex(),
        "command_id": original["current_pointer_command"]["content_id"],
        "qc_id": original["apply_qc"]["content_id"],
        "gate_eligible": False,
    }


def main() -> None:
    lean, evidence = generate()
    (ROOT / "formal/proofs/DeltaReduce/NativeCurrentPointerVectors.lean").write_text(
        lean, encoding="utf-8", newline="\n"
    )
    write_canonical_json(ROOT / "formal/proposals/native-current-pointer-vectors.json", evidence)
    print("current-pointer original golden and synthetic WAL regenerated")


if __name__ == "__main__":
    main()
