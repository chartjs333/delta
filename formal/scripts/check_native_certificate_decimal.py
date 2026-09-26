"""Pinned native decimal counterchecks; no runtime repair or admission authority."""

import argparse
import copy
import hashlib
import re
import subprocess
from pathlib import Path

import generate_native_certificate_chain as native
from formal_artifacts import canonical_json_bytes, load_json_strict, write_canonical_json

ROOT = native.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-certificate-decimal"
RESULT = FOLDER / "cpp-cross-check.json"
# Expected results are explicit cases, not an alternate native parser.
# (original bytes, native nonnegative acceptance, native signed acceptance)
CASES = [
    (b"0", True, True),
    (b"1", True, True),
    (b"-1", False, True),
    (b"-0", False, False),
    (b"-00", True, True),
    (b"-000", True, True),
    (b"-" + b"0" * 64, True, True),
    (b"00", False, False),
    (b"01", False, False),
    (b"-01", False, True),
    (b"-0001", False, True),
    (b"9223372036854775807", True, True),
    (b"9223372036854775808", False, False),
    (b"-9223372036854775808", False, True),
    (b"-9223372036854775809", False, False),
    (b"-09223372036854775808", False, True),
    (b"-09223372036854775809", False, False),
    (b"", False, False),
    (b"-", False, False),
    (b"+0", False, False),
    (b"+1", False, False),
    (b" 0", False, False),
    (b"0 ", False, False),
    (b"1\n", False, False),
    (b"1\x00", False, False),
    (b"-00\x00", False, False),
    (b"1.0", False, False),
    (b"1e0", False, False),
    (b"0x1", False, False),
    (b"--1", False, False),
    (b"\xff", False, False),
]


def sources():
    blobs = native.blobs()
    pinned = load_json_strict(
        ROOT / "formal/proposals/evidence/native-certificate-chain/cpp-cross-check.json"
    )
    hashes = {p: hashlib.sha256(raw).hexdigest() for p, raw in blobs.items()}
    if pinned["source_commit"] != native.SOURCE or hashes != pinned["source_sha256"]:
        raise ValueError("native source identity changed")
    return blobs


def canonical_decimal(raw, nonnegative):
    """Strict spelling required by the existing separate Python proposal profile."""
    if re.fullmatch(rb"0|-?[1-9][0-9]*", raw) is None:
        return False
    number = int(raw)
    return (0 if nonnegative else -(2**63)) <= number < 2**63


def expected_rows():
    docs = native.fixture()[0]
    rows = []
    for kind, column, doc_name, domain in [
        ("NORM", 1, "NORM", b"deltareduce.008.norm-evidence.v1"),
        ("PARAMETER", 2, "PARAMETER", b"deltareduce.008.parameter-shard-qc.v1"),
    ]:
        for index, case in enumerate(CASES):
            raw, accepted = case[0], case[column]
            doc = copy.deepcopy(docs[doc_name])
            if accepted:
                if kind == "NORM":
                    doc["entries"][0]["squared_norm"] = raw.decode("ascii")
                else:
                    doc["result_numerators"] = [raw.decode("ascii")]
                payload = canonical_json_bytes(doc)
                cid = "sha256:" + hashlib.sha256(domain + b"\0" + payload).hexdigest()
            else:
                payload, cid = b"", ""
            rows.append(
                {
                    "kind": kind,
                    "index": index,
                    "input_hex": raw.hex(),
                    "accepted": accepted,
                    "error_code": None if accepted else 8,
                    "json_hex": payload.hex(),
                    "content_id": cid,
                    "strict_proposal_accepts": canonical_decimal(raw, kind == "NORM"),
                }
            )
    return rows


def harness():
    values = ",".join('"' + case[0].hex() + '"' for case in CASES)
    # All validation, serialization and hashing below call unchanged native TUs.
    return (
        r"""#include <delta/certificates/contracts.hpp>
#include <iostream>
#include <string>
#include <vector>
using namespace delta::certificates;
std::string id(char c){return "sha256:"+std::string(64,c);}
std::string hex(const delta::core::canonical::Bytes& bs){
 const char* digits="0123456789abcdef";std::string out;
 for(auto byte:bs){const auto b=std::to_integer<unsigned>(byte);
 out.push_back(digits[b>>4]);out.push_back(digits[b&15]);}return out;}
std::string unhex(const std::string& raw){std::string out;
 for(std::size_t i=0;i<raw.size();i+=2){
 out.push_back(static_cast<char>(std::stoul(raw.substr(i,2),nullptr,16)));}return out;}
template<typename T> void emit(const char* kind,std::size_t i,const std::string& input,const T& v){
 try{const auto bytes=canonical_json(v);const auto key=content_id(v);
 std::cout<<kind<<'\t'<<i<<'\t'<<input<<"\tACCEPT\t"<<hex(bytes)<<'\t'<<key<<'\n';}
 catch(const CertificateError& e){std::cout<<kind<<'\t'<<i<<'\t'<<input
 <<"\tREJECT\t"<<static_cast<int>(e.code())<<"\t-\n";}}
int main(){
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const SeedTranscript seed{c,isc,id('9'),id('a'),{id('b')}};const auto sid=content_id(seed);
 const NormEvidence norm{c,{{1,"1","ticket-a"}},isc,id('c')};const auto nid=content_id(norm);
 const EligibilityCertificate ec{c,{{true,"domain-a",{1,1},"ACCEPTED","ticket-a"}},
 isc,nid,3,id('e'),signers};const auto eid=content_id(ec);
 const AggregationPlanCertificate plan{c,id('f'),{{"bucket-a","ticket-a"}},
 eid,isc,1,3,sid,signers,id('0'),{{{1,1},"ticket-a"}}};const auto pid=content_id(plan);
 const ParameterShardQc parameter{c,pid,1,"domain-a",eid,{id('1')},isc,3,
 {"1"},"shard-a",signers};
 const std::vector<std::string> cases{"""
        + values
        + r"""};
 for(std::size_t i=0;i<cases.size();++i){auto n=norm;n.entries[0].squared_norm=unhex(cases[i]);
 emit("NORM",i,cases[i],n);}
 for(std::size_t i=0;i<cases.size();++i){auto p=parameter;p.result_numerators={unhex(cases[i])};
 emit("PARAMETER",i,cases[i],p);}
}
"""
    )


def parse_output(output):
    lines = output.splitlines()
    expected = expected_rows()
    if len(lines) != len(expected):
        raise ValueError("incomplete or extra native decimal rows")
    for line, row in zip(lines, expected, strict=True):
        parts = line.split("\t")
        wanted = [row["kind"], str(row["index"]), row["input_hex"]]
        if row["accepted"]:
            wanted += ["ACCEPT", row["json_hex"], row["content_id"]]
        else:
            wanted += ["REJECT", str(row["error_code"]), "-"]
        if parts != wanted:
            raise ValueError("native decimal outcome/bytes/identity mismatch")
    return expected


def verify_document(document):
    expected_hashes = {p: hashlib.sha256(raw).hexdigest() for p, raw in sources().items()}
    if (
        document["source_commit"] != native.SOURCE
        or document["source_sha256"] != expected_hashes
        or document["harness_sha256"] != hashlib.sha256(harness().encode()).hexdigest()
        or document["rows"] != expected_rows()
        or document["status"] != "CONFIRMED_NATIVE_DECIMAL_CANONICALITY_GAP"
        or document["native_runtime_execution"] is not False
        or document["native_export_authenticated"] is not False
        or document["gate_eligible"] is not False
    ):
        raise ValueError("substituted native decimal evidence")
    return document


def cross_check(vcvars):
    blobs = sources()
    build = ROOT / "formal/build/native-certificate-decimal"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path in [
        "delta-core-cpp/include/delta/core/canonical.hpp",
        "delta-core-cpp/include/delta/certificates/contracts.hpp",
    ]:
        target = build / "include" / path.split("/include/")[1]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blobs[path])
    for name in ["canonical.cpp", "sha256.cpp", "sha256.hpp", "certificates/contracts.cpp"]:
        (build / Path(name).name).write_bytes(blobs["delta-core-cpp/src/" + name])
    code = harness()
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX /Iinclude "
        "harness.cpp canonical.cpp sha256.cpp contracts.cpp /Fe:decimal.exe\n"
        "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    run = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (run.stdout + run.stderr).replace(b"\r\n", b"\n")
    if run.returncode:
        raise RuntimeError(log.decode("utf-8", errors="replace"))
    output = (
        subprocess.check_output([str(build / "decimal.exe")], cwd=build)
        .decode("ascii")
        .replace("\r\n", "\n")
    )
    observed = parse_output(output)
    compiler = re.search(rb"Optimizing Compiler Version ([0-9.]+) for x64", log)
    if not compiler:
        raise ValueError("compiler identity missing")
    (FOLDER / "compile.txt").write_bytes(
        b"\n".join(line.rstrip() for line in log.splitlines()).rstrip() + b"\n"
    )
    (FOLDER / "native-output.txt").write_text(output, encoding="ascii", newline="\n")
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = {
        "status": "CONFIRMED_NATIVE_DECIMAL_CANONICALITY_GAP",
        "source_commit": native.SOURCE,
        "source_sha256": {p: hashlib.sha256(raw).hexdigest() for p, raw in blobs.items()},
        "unmodified_translation_units": ["canonical.cpp", "sha256.cpp", "contracts.cpp"],
        "compiler": compiler[1].decode(),
        "compiler_flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "rows": observed,
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    verify_document(result)
    write_canonical_json(RESULT, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    if args.vcvars:
        print(cross_check(args.vcvars)["status"])
    else:
        verify_document(load_json_strict(RESULT))
        parse_output((FOLDER / "native-output.txt").read_text("ascii"))
        print("PASS_RETAINED_DECIMAL_COUNTERCHECKS_NOT_NATIVE_AUTHORITY")
