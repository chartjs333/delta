"""DVREC001 kernel vectors from pinned unchanged native operational codec."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_policy_wal_vectors as wal
from formal_artifacts import write_canonical_json
from native_policy_wal import decode_flat, receipt

ROOT, SOURCE = wal.ROOT, wal.SOURCE
FOLDER = ROOT / "formal/proposals/evidence/native-receipt-codec"
TARGET = ROOT / "formal/proposals/native-receipt-vectors.json"
LEAN = ROOT / "formal/proofs/DeltaReduce/NativeReceiptVectors.lean"
UNITS = [*wal.admission.UNITS, "delta-runtime-cpp/src/vote_codec.cpp"]
HARNESS = r"""
#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <iomanip>
#include <iostream>
using namespace delta::core::consensus;
namespace ca=delta::core::canonical;
namespace pr=delta::core::protocol;
namespace rt=delta::runtime;
using Bytes=ca::Bytes;
std::string hex(const Bytes& b){constexpr char d[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);
 s.push_back(d[n&15U]);}return s;}
int main(){
 for(unsigned action=1;action<=9;++action){
  const auto a=static_cast<VoteAction>(action);
  const auto f=delta::test::vote_fixture::full(a);
  const auto frame=pr::encode(f.vote);
  rt::VoteReceipt r{frame,ca::content_id(ca::Type::vote,frame),f.vote.durable_sequence,
   a,std::string(vote_formal_action_id(a)),f.vote.context_id,f.policy.candidates[0].parents,false};
  const auto bytes=rt::encode_vote_receipt_v1(r);
  r.replay=true;
  if(rt::encode_vote_receipt_v1(r)!=bytes)throw std::runtime_error("replay changed bytes");
  const auto decoded=rt::parse_vote_receipt_v1(bytes);
  if(decoded.frame!=frame || decoded.replay || decoded.action!=a ||
    decoded.journal_sequence!=r.journal_sequence || decoded.vote_id!=r.vote_id ||
    decoded.context_id!=r.context_id)throw std::runtime_error("native codec roundtrip");
  unsigned rejected=0;
  auto changed=bytes;changed[20]=std::byte{1};
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){++rejected;}
  changed=bytes;changed.push_back(std::byte{0});
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){++rejected;}
  // Structural receipt fields remain valid, but native ID-to-frame validation fails.
  changed=bytes;changed[36+frame.size()+4+7]=std::byte{'0'};
  if(changed==bytes)changed[36+frame.size()+4+7]=std::byte{'1'};
  bool hashRejected=false;
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){hashRejected=true;}
  if(rejected!=2 || !hashRejected)throw std::runtime_error("native invalid receipt accepted");
  std::cout<<"{\"action\":"<<action<<",\"receipt_hex\":"<<std::quoted(hex(bytes))
    <<",\"frame_hex\":"<<std::quoted(hex(frame))<<",\"replay_equal\":true,\"rejected\":"<<rejected
    <<",\"hash_mismatch_hex\":"<<std::quoted(hex(changed))<<",\"hash_mismatch_rejected\":true}\n";
 }
}
""".lstrip()


def validate(rows):
    if len(rows) != 9 or [r["action"] for r in rows] != list(range(1, 10)):
        raise ValueError("native receipt action coverage")
    for r in rows:
        if set(r) != {
            "action",
            "receipt_hex",
            "frame_hex",
            "replay_equal",
            "rejected",
            "hash_mismatch_hex",
            "hash_mismatch_rejected",
        }:
            raise ValueError("native receipt row shape")
        if (
            type(r["action"]) is not int
            or type(r["rejected"]) is not int
            or r["rejected"] != 2
            or r["replay_equal"] is not True
            or r["hash_mismatch_rejected"] is not True
        ):
            raise ValueError("native receipt checks")
        raw, frame = bytes.fromhex(r["receipt_hex"]), bytes.fromhex(r["frame_hex"])
        parsed = receipt(raw)
        if parsed["frame"] != frame or int.from_bytes(raw[16:20], "big") != r["action"]:
            raise ValueError("native frame/action")
        altered = bytes.fromhex(r["hash_mismatch_hex"])
        if altered == raw or len(altered) != len(raw):
            raise ValueError("hash countercheck")
        try:
            receipt(altered)
        except ValueError as error:
            if "receipt vote ID" not in str(error):
                raise
        else:
            raise ValueError("incorrect ID accepted")
    return rows


def cross_check(vcvars):
    blobs = wal.sources()
    build = ROOT / "formal/build/native-receipt-codec"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name, raw in blobs.items():
        p = build / (
            "include/" + name.split("/include/")[1] if "/include/" in name else Path(name).name
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    (build / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    cmd = (
        '@echo off\ncall "'
        + str(vcvars)
        + '" >nul\nif errorlevel 1 exit /b 1\ncl '
        + wal.FLAGS
        + " /Iinclude harness.cpp "
        + " ".join(Path(p).name for p in UNITS)
        + " /Fe:receipt.exe\nexit /b %errorlevel%\n"
    )
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
        raise RuntimeError("native receipt compile failed")
    output = subprocess.check_output([str(build / "receipt.exe")], cwd=build, timeout=90).decode(
        "ascii"
    )
    rows = validate([json.loads(line) for line in output.splitlines()])
    (FOLDER / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS_NATIVE_RECEIPT_CODEC_NOT_ADMISSION",
        "source_commit": SOURCE,
        "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        "compiler": re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        "compiler_flags": wal.FLAGS,
        "unmodified_translation_units": UNITS,
        "observed": rows,
        "native_codec_execution": True,
        "native_runtime_execution": False,
        "arithmetic_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


def lb(raw):
    return "[" + ",".join(map(str, raw)) + "]"


def generate():
    result = json.loads((FOLDER / "cpp-cross-check.json").read_bytes())
    rows = validate(result["observed"])
    lines = [
        "import DeltaReduce.NativeReceiptBytes",
        "",
        "/-! Exact native codec bytes, not vote admission or arithmetic execution. -/",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 1000000",
        "namespace DeltaReduce.NativeReceiptVectors",
        "open NativeReceiptBytes",
        "",
    ]
    for r in rows:
        n = r["action"]
        raw = bytes.fromhex(r["receipt_hex"])
        parsed = receipt(raw)
        fields = decode_flat(parsed["frame"], 3)
        context = fields["context_id"].encode()
        vid = parsed["vote_id"].encode()
        # Retain the exact native bytes split around the unchanged opaque frame.
        assert raw[36 : 36 + len(parsed["frame"])] == parsed["frame"]
        lead, tail = raw[:36], raw[36 + len(parsed["frame"]) :]
        lines += [
            f"def frame{n} : Bytes := {lb(parsed['frame'])}",
            f"def receipt{n} : Receipt := ⟨{n}, {parsed['sequence']}, frame{n},"
            f" {lb(vid)}, {lb(context)}⟩",
            f"def nativeBytes{n} : Bytes := {lb(lead)} ++ frame{n} ++ {lb(tail)}",
            f"theorem valid{n} : Valid receipt{n} := by decide",
            f"theorem exactBytes{n} : encode receipt{n} = nativeBytes{n} := by rfl",
            f"theorem readBack{n} : decode nativeBytes{n} = some receipt{n} := by",
            f"  rw [← exactBytes{n}]; exact decodeEncoded _ valid{n}",
            f"theorem retryBytes{n} : returnedBytes ⟨receipt{n}, true⟩ = nativeBytes{n}"
            f" := exactBytes{n}",
            f"theorem reservedReject{n} : decode "
            f"({lb(lead[:20] + bytes([1]) + lead[21:])} ++ frame{n} ++ {lb(tail)}) = none := by",
            f"  exact reservedMismatch {n} (be 8 {parsed['sequence']} ++ sizedBytes frame{n} ++"
            f" sizedBytes {lb(vid)} ++ sizedBytes {lb(context)}) (by decide)",
            "",
        ]
    # Small structural countercheck: shape cannot authenticate a vote hash.
    lines += [
        "def unauthenticated : Receipt := ⟨1, 1, [1,2,3], [120], [99]⟩",
        "theorem structuralDoesNotAuthenticate : decode (encode unauthenticated) = some"
        " unauthenticated := by",
        "  exact decodeEncoded _ (by decide)",
        "theorem sequenceZeroReject : decode (encode {unauthenticated with sequence :="
        " 0}) = none := by decide",
        "theorem actionOutsideReject : decode (encode {unauthenticated with action :="
        " 10}) = none := by decide",
        "theorem nonprintableReject : decode (encode {unauthenticated with context :="
        " [0]}) = none := by decide",
        "theorem sectionTruncatedReject : readSection 4096 [0,0,0,2,1] = none := by decide",
        "theorem sectionOverlimitReject : readSection 1 [0,0,0,2,1,2] = none := by decide",
        "theorem sequenceEndpoint : readNat 8 (be 8 18446744073709551615) = some"
        " (18446744073709551615, []) := by",
        "  simpa using readNatEncoded 8 18446744073709551615 [] (by decide)",
        "end DeltaReduce.NativeReceiptVectors",
        "",
    ]
    LEAN.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    doc = {
        "version": "deltareduce.native-receipt-codec.v1-candidate",
        "native_source": SOURCE,
        "native_evidence_sha256": hashlib.sha256(
            (FOLDER / "cpp-cross-check.json").read_bytes()
        ).hexdigest(),
        "lean_sha256": hashlib.sha256(LEAN.read_bytes()).hexdigest(),
        "native_codec_cases": 9,
        "native_rejection_checks": 27,
        "native_admission": False,
        "structural_codec_only": True,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    write_canonical_json(TARGET, doc)
    return doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    if args.vcvars:
        cross_check(args.vcvars)
    print(json.dumps(generate(), sort_keys=True))
