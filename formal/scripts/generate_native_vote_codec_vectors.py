"""Exact DRC1/receipt semantic codec, distinct from vote admission and SHA proof."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_receipt_vectors as previous
from formal_artifacts import write_canonical_json
from native_admission_snapshot import decode_flat

ROOT, SOURCE = previous.ROOT, previous.SOURCE
FOLDER = ROOT / "formal/proposals/evidence/native-vote-codec"
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeVoteCodecVectors.lean"
TARGET = ROOT / "formal/proposals/native-vote-codec-vectors.json"


def original():
    return previous.validate(
        json.loads((previous.FOLDER / "cpp-cross-check.json").read_bytes())["observed"]
    )


def text(value):
    raw = value.encode("ascii") if isinstance(value, str) else value
    return b"\x21" + len(raw).to_bytes(4, "big") + raw


def envelope(pairs):
    payload = b"\x31" + len(pairs).to_bytes(4, "big")
    payload += b"".join(text(key) + text(value) for key, value in pairs)
    return b"DRC1\x01\x00\x00\x03" + len(payload).to_bytes(4, "big") + payload


def cases():
    rows = original()
    result = [
        ("original-" + str(row["action"]), bytes.fromhex(row["frame_hex"]), True) for row in rows
    ]
    fields = decode_flat(result[0][1], 3)
    pairs = sorted(fields.items())
    changes = [
        ("durable_sequence", "0", False),
        ("durable_sequence", "01", False),
        ("durable_sequence", "", False),
        ("durable_sequence", "18446744073709551615", True),
        ("durable_sequence", "18446744073709551616", False),
        ("height", "+1", False),
        ("height", "-1", False),
        ("height", "1x", False),
        ("height", "00", False),
        ("height", "18446744073709551615", True),
        ("view", "18446744073709551616", False),
        ("view", " 1", False),
        ("view", "1 ", False),
        ("formal_semantics_id", "sha256:" + "0" * 64, False),
        ("schema_version", "1.0.1", False),
        ("type_name", "vote", False),
        ("body_hash", "sha256:" + "A" * 64, False),
        ("signature_id", "sha256:" + "0" * 63, False),
        ("validator_epoch_id", "sha257:" + "0" * 64, False),
        ("context_id", "", False),
        ("kind", "", False),
        ("round_id", "", False),
        ("validator_id", "", False),
        ("context_id", b"a\x00b", False),
        ("round_id", b"\x7f", False),
        ("validator_id", b"\x80", False),
        # Native protocol parser does NOT restrict kind to the nine receipt actions.
        ("kind", "UNREGISTERED", True),
    ]
    for n, (key, value, accepted) in enumerate(changes):
        changed = dict(pairs)
        changed[key] = value
        result.append((f"field-{n}-{key}", envelope(sorted(changed.items())), accepted))
    result += [
        ("missing-field", envelope(pairs[:-1]), False),
        ("extra-field", envelope([*pairs, ("zzz", "x")]), False),
        ("duplicate-field", envelope(pairs[:1] + pairs), False),
        ("reordered-field", envelope([pairs[1], pairs[0], *pairs[2:]]), False),
    ]
    raw = result[0][1]
    result += [("trailing-byte", raw + b"\0", False), ("truncated", raw[:-1], False)]
    for name, offset, value in [
        ("magic", 0, 0),
        ("major", 4, 2),
        ("minor", 5, 1),
        ("type", 7, 4),
        ("root-tag", 12, 0x30),
        ("field-count", 16, 12),
        ("key-tag", 17, 0x20),
    ]:
        mutated = bytearray(raw)
        mutated[offset] = value
        result.append((name, bytes(mutated), False))
    return result


def harness():
    # The test adapter passes exact byte mutations into the unchanged native parser.
    entries = ",\n".join('{"' + name + '","' + raw.hex() + '"}' for name, raw, _ in cases())
    return (
        r"""#include <delta/core/protocol.hpp>
#include <delta/core/canonical.hpp>
#include <iostream>
#include <iomanip>
#include <string>
#include <utility>
namespace ca=delta::core::canonical;
namespace pr=delta::core::protocol;
ca::Bytes unhex(const std::string& s){ca::Bytes b;
 for(std::size_t i=0;i<s.size();i+=2)
  b.push_back(static_cast<std::byte>(std::stoul(s.substr(i,2),nullptr,16)));
 return b;}
int main(){const std::pair<const char*,const char*> cases[]={
"""
        + entries
        + r"""
};for(const auto& [name,hex]:cases){const auto raw=unhex(hex);bool accepted=false;
 std::string id;try{const auto v=pr::parse_vote(raw);
 if(pr::encode(v)!=raw)throw std::runtime_error("native canonical mismatch");
 id=ca::content_id(ca::Type::vote,raw);accepted=true;
 }catch(const ca::DecodeError&){}catch(const pr::ProtocolError&){}
 std::cout<<"{\"name\":"<<std::quoted(name)<<",\"accepted\":"<<(accepted?"true":"false")
 <<",\"vote_id\":"<<std::quoted(id)<<"}\n";}}
"""
    )


def validate(result):
    observations = result["observed"]
    expected = cases()
    if len(observations) != len(expected):
        raise ValueError("native vote case count")
    for row, (name, raw, accepted) in zip(observations, expected, strict=True):
        content_id = "sha256:" + hashlib.sha256(b"deltareduce:003:vote:v1\0" + raw).hexdigest()
        if row != {"name": name, "accepted": accepted, "vote_id": content_id if accepted else ""}:
            raise ValueError("native vote observation mismatch: " + name)
        if type(row["accepted"]) is not bool:
            raise ValueError("native vote status type")
    return observations


def cross_check(vcvars):
    blobs = previous.wal.sources()
    build = ROOT / "formal/build/native-vote-codec"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, raw in blobs.items():
        p = build / (
            "include/" + name.split("/include/")[1] if "/include/" in name else Path(name).name
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    source = harness()
    (build / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    units = [
        "delta-core-cpp/src/canonical.cpp",
        "delta-core-cpp/src/sha256.cpp",
        "delta-core-cpp/src/protocol.cpp",
    ]
    cmd = '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\ncl '
    cmd += previous.wal.FLAGS + " /Iinclude harness.cpp " + " ".join(Path(p).name for p in units)
    cmd += " /Fe:vote.exe\nexit /b %errorlevel%\n"
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    r = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (r.stdout + r.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if r.returncode:
        raise RuntimeError("native vote compile failed")
    output = subprocess.check_output([str(build / "vote.exe")], cwd=build, timeout=90).decode(
        "ascii"
    )
    result = {
        "source_commit": SOURCE,
        "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        "compiler": re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        "compiler_flags": previous.wal.FLAGS,
        "unmodified_translation_units": units,
        "observed": [json.loads(line) for line in output.splitlines()],
        "native_codec_execution": True,
        "native_runtime_execution": False,
        "arithmetic_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    validate(result)
    (FOLDER / "harness.cpp").write_text(source, encoding="utf-8", newline="\n")
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)


def generate():
    observed = validate(json.loads((FOLDER / "cpp-cross-check.json").read_bytes()))
    lines = [
        "import DeltaReduce.NativeVoteBytes",
        "import DeltaReduce.NativeReceiptVectors",
        "",
        "/-! Finite native codec/hash samples; no admission or general SHA proof. -/",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 1000000",
        "namespace DeltaReduce.NativeVoteCodecVectors",
        "open NativeReceiptBytes NativeVoteBytes",
        "",
    ]
    all_texts = sorted(
        {
            value
            for row in original()
            for pair in decode_flat(bytes.fromhex(row["frame_hex"]), 3).items()
            for value in pair
        }
    )
    text_names = {}
    for index, value in enumerate(all_texts):
        text_names[value] = f"encodedText{index}"
        lines += [
            f"theorem encodedText{index} : textBytes (ascii {json.dumps(value)}) = "
            f"{previous.lb(text(value))} := by decide"
        ]
    for row in original():
        n = row["action"]
        raw = bytes.fromhex(row["frame_hex"])
        fields = decode_flat(raw, 3)
        values = [
            fields[k]
            for k in [
                "body_hash",
                "context_id",
                "durable_sequence",
                "height",
                "kind",
                "round_id",
                "signature_id",
                "validator_epoch_id",
                "validator_id",
                "view",
            ]
        ]
        chunks = " ++ ".join(previous.lb(raw[i : i + 32]) for i in range(12, len(raw), 32))
        digest = hashlib.sha256(b"deltareduce:003:vote:v1\0" + raw).digest()
        lines += [
            f"def wire{n} : WireVote := ⟨"
            + ", ".join("ascii " + json.dumps(v) for v in values)
            + "⟩",
            f"def vote{n} : Vote := ⟨wire{n}, {fields['durable_sequence']}, "
            f"{fields['height']}, {fields['view']}⟩",
            f"theorem payloadBytes{n} : payload wire{n} = {chunks} := by",
            f"  simp only [payload, fields, wire{n}, encodeFields, nativeSemantics, "
            + ", ".join(text_names[v] for v in sorted({v for pair in fields.items() for v in pair}))
            + "]",
            "  rfl",
            f"theorem nativeFrame{n} : encodeFrame wire{n} = NativeReceiptVectors.frame{n} := by",
            f"  unfold encodeFrame; rw [payloadBytes{n}]; rfl",
            f"theorem frameValid{n} : FrameValid wire{n} := by",
            "  constructor; · decide",
            f"  rw [nativeFrame{n}]; decide",
            f"theorem valid{n} : VoteValid vote{n} := by",
            f"  exact ⟨frameValid{n}, by decide, by decide, by decide, by decide, by decide⟩",
            f"theorem parsed{n} : decodeFrame NativeReceiptVectors.frame{n} = some vote{n} := by",
            f"  exact decodeFrameFromEncoding vote{n} NativeReceiptVectors.frame{n} "
            f"valid{n} nativeFrame{n}",
            # Each local lookup names the exact original SHA input; outside it returns no digest.
            f"def fixtureSHA{n} (b : Bytes) : Bytes := if b = votePreimage "
            f"NativeReceiptVectors.frame{n} then {previous.lb(digest)} else []",
            f"theorem hashBinding{n} : voteId fixtureSHA{n} "
            f"NativeReceiptVectors.frame{n} = some NativeReceiptVectors.receipt{n}.voteId := by",
            f"  simp only [voteId, fixtureSHA{n}, ↓reduceIte]; rfl",
            f"theorem linked{n} : ReceiptLinked fixtureSHA{n} "
            f"NativeReceiptVectors.receipt{n} vote{n} := by",
            f"  exact ⟨rfl, rfl, rfl, hashBinding{n}⟩",
            f"theorem bound{n} : bindReceipt fixtureSHA{n} "
            f"NativeReceiptVectors.receipt{n} = some vote{n} :=",
            f"  bindingFromComponents fixtureSHA{n} NativeReceiptVectors.receipt{n} "
            f"vote{n} parsed{n} linked{n}",
            f"theorem fullReceipt{n} : decodeReceipt fixtureSHA{n} "
            f"NativeReceiptVectors.nativeBytes{n} = some "
            f"(NativeReceiptVectors.receipt{n},vote{n}) := by",
            f"  exact receiptFromNativeBytes fixtureSHA{n} NativeReceiptVectors.receipt{n} vote{n} "
            f"NativeReceiptVectors.nativeBytes{n} NativeReceiptVectors.valid{n} "
            f"bound{n} NativeReceiptVectors.exactBytes{n}",
            f"theorem sequenceMismatch{n} : bindReceipt fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with sequence := 0}} = none := by",
            f"  apply bindingRejectsMismatch fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with sequence := 0}} vote{n} parsed{n}",
            f"  intro h; have : (0:Nat) = {fields['durable_sequence']} := h.1; contradiction",
            f"theorem contextMismatch{n} : bindReceipt fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with context := []}} = none := by",
            f"  apply bindingRejectsMismatch fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with context := []}} vote{n} parsed{n}",
            "  intro h; have wrong := h.2.1",
            f"  have different : ([]:Bytes) ≠ vote{n}.wire.context := by decide",
            "  exact different wrong",
            f"theorem actionMismatch{n} : bindReceipt fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with action := 0}} = none := by",
            f"  apply bindingRejectsMismatch fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with action := 0}} vote{n} parsed{n}",
            "  intro h; have wrong := h.2.2.1",
            f"  have different : actionName 0 ≠ vote{n}.wire.kind := by decide",
            "  exact different wrong",
            f"theorem idMismatch{n} : bindReceipt fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with voteId := []}} = none := by",
            f"  apply bindingRejectsMismatch fixtureSHA{n} "
            f"{{NativeReceiptVectors.receipt{n} with voteId := []}} vote{n} parsed{n}",
            "  intro h; have wrong := h.2.2.2",
            f"  change voteId fixtureSHA{n} NativeReceiptVectors.frame{n} = some [] at wrong",
            f"  rw [hashBinding{n}] at wrong",
            f"  have different : NativeReceiptVectors.receipt{n}.voteId ≠ [] := by decide",
            "  exact different (Option.some.inj wrong)",
            "",
        ]
    for name, value, expected in [
        ("zero", "0", "some 0"),
        ("maximum", "18446744073709551615", "some 18446744073709551615"),
        ("overflow", "18446744073709551616", "none"),
        ("empty", "", "none"),
        ("leadingZero", "01", "none"),
        ("twoZeros", "00", "none"),
        ("sign", "+1", "none"),
        ("negative", "-1", "none"),
        ("space", "1 ", "none"),
        ("nondigit", "1x", "none"),
    ]:
        lines += [
            f"theorem decimal_{name} : parseDecimal (ascii {json.dumps(value)}) = "
            f"{expected} := by decide"
        ]
    lines += [
        "theorem badHashWidth : voteId (fun _ => [0]) [] = none := by decide",
        "theorem printableBoundary : readText (textBytes [32,126]) = some "
        "([32,126],[]) := by decide",
        "theorem textControlReject : readText (textBytes [31]) = none := by decide",
        "theorem textDeleteReject : readText (textBytes [127]) = none := by decide",
        "theorem textTagReject : readText [32,0,0,0,0] = none := by decide",
        "theorem structuralCountercheckNowRejects : decodeReceipt (fun _ => []) "
        "(encode NativeReceiptVectors.unauthenticated) = none := by",
        "  simp only [decodeReceipt, "
        "NativeReceiptVectors.structuralDoesNotAuthenticate, bind, Option.bind]",
        "  decide",
        "end DeltaReduce.NativeVoteCodecVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    result = {
        "version": "deltareduce.native-vote-codec.v1-candidate",
        "native_source": SOURCE,
        "native_evidence_sha256": hashlib.sha256(
            (FOLDER / "cpp-cross-check.json").read_bytes()
        ).hexdigest(),
        "lean_sha256": hashlib.sha256(LEAN.read_bytes()).hexdigest(),
        "native_cases": len(observed),
        "native_accepted": sum(r["accepted"] for r in observed),
        "native_rejected": sum(not r["accepted"] for r in observed),
        "original_receipts": 9,
        "hash_adapter": "FINITE_EXACT_PREIMAGE_LOOKUP_NOT_SHA_PROOF",
        "native_admission": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    write_canonical_json(TARGET, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    if args.vcvars:
        cross_check(args.vcvars)
    print(json.dumps(generate(), sort_keys=True))
