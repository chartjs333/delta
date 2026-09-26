"""Native certificate byte-bound counterchecks; unchanged native source only."""

import argparse
import copy
import hashlib
import re
import subprocess
from functools import lru_cache
from pathlib import Path

import check_native_certificate_decimal as pinned
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict, write_canonical_json

ROOT = pinned.ROOT
LIMIT = 4 * 1024 * 1024
DOMAIN = b"deltareduce.008.norm-evidence.v1"
FOLDER = ROOT / "formal/proposals/evidence/native-contract-size"
RESULT = FOLDER / "cpp-cross-check.json"


def document(count, padding):
    doc = copy.deepcopy(pinned.native.fixture()[0]["NORM"])
    doc["entries"] = [
        {"scale_denominator": 1, "squared_norm": "0", "ticket_id": f"t{i:05d}"}
        for i in range(count)
    ]
    if count:
        doc["entries"][-1]["ticket_id"] += "z" * padding
    return doc


@lru_cache(maxsize=1)
def cases():
    # Fixed-width unique tickets keep the size formula independent of count.
    base = len(canonical_json_bytes(document(0, 0)))
    unit = len(canonical_json_bytes(document(1, 0))) - base + 1
    count = (LIMIT - base + 1) // unit
    padding = LIMIT - (base + count * unit - 1)
    assert 1 < count < 100000 and 1 <= padding < 4090
    return [(1, 0), (count, padding - 1), (count, padding), (count, padding + 1)]


@lru_cache(maxsize=1)
def expected_rows():
    rows = []
    context_keys = [key for key, _ in codec.SCHEMAS["context"]]
    for count, padding in cases():
        doc = document(count, padding)
        raw = canonical_json_bytes(doc)
        tree = {
            "context": {k: doc[k] for k in context_keys},
            "entries": doc["entries"],
            "input_set_certificate_id": doc["input_set_certificate_id"],
            "norm_root": doc["norm_root"],
        }
        wire = codec.encode_value("norm", tree)
        accepted = len(raw) <= LIMIT
        rows.append(
            {
                "count": count,
                "padding": padding,
                "canonical_json_bytes": len(raw),
                "canonical_json_sha256": hashlib.sha256(raw).hexdigest(),
                "component_policy_wire_bytes": len(wire),
                "component_policy_wire_sha256": hashlib.sha256(wire).hexdigest(),
                "canonical_json_accepted": True,
                "content_id_accepted": accepted,
                "content_id": (
                    "sha256:" + hashlib.sha256(DOMAIN + b"\0" + raw).hexdigest()
                    if accepted
                    else None
                ),
                "error_code": None if accepted else 16,
            }
        )
    assert [r["canonical_json_bytes"] for r in rows[1:]] == [LIMIT - 1, LIMIT, LIMIT + 1]
    assert all(r["component_policy_wire_bytes"] < LIMIT for r in rows)
    return rows


def harness():
    inputs = ",".join("{" + f"{n}U,{p}U" + "}" for n, p in cases())
    return (
        r"""#include <delta/certificates/contracts.hpp>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>
using namespace delta::certificates;
std::string id(char c){return "sha256:"+std::string(64,c);}
int main(){
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const std::vector<std::pair<unsigned,unsigned>> cases{"""
        + inputs
        + r"""};
 for(const auto& [count,padding]:cases){
  NormEvidence norm{c,{},isc,id('c')};
  for(unsigned i=0;i<count;++i){std::ostringstream name;
   name<<'t'<<std::setw(5)<<std::setfill('0')<<i;
   norm.entries.push_back({1,"0",name.str()});}
  norm.entries.back().ticket_id+=std::string(padding,'z');
  const auto bytes=canonical_json(norm);
  std::cout<<count<<'\t'<<padding<<'\t'<<bytes.size()<<'\t'
   <<delta::core::canonical::sha256_hex(bytes)<<'\t';
  try{const auto key=content_id(norm);std::cout<<"ACCEPT\t"<<key<<'\n';}
  catch(const CertificateError& e){std::cout<<"REJECT\t"<<static_cast<int>(e.code())<<'\n';}
 }
}
"""
    )


def parse_output(output):
    expected = expected_rows()
    lines = output.splitlines()
    if len(lines) != len(expected):
        raise ValueError("incomplete or extra native contract-size rows")
    for line, row in zip(lines, expected, strict=True):
        wanted = [
            str(row["count"]),
            str(row["padding"]),
            str(row["canonical_json_bytes"]),
            row["canonical_json_sha256"],
            "ACCEPT" if row["content_id_accepted"] else "REJECT",
            row["content_id"] if row["content_id_accepted"] else str(row["error_code"]),
        ]
        if line.split("\t") != wanted:
            raise ValueError("native contract-size outcome/bytes/identity mismatch")
    return expected


def verify_document(doc):
    hashes = {p: hashlib.sha256(raw).hexdigest() for p, raw in pinned.sources().items()}
    if (
        doc["source_commit"] != pinned.native.SOURCE
        or doc["source_sha256"] != hashes
        or doc["harness_sha256"] != hashlib.sha256(harness().encode()).hexdigest()
        or doc["rows"] != expected_rows()
        or doc["status"] != "CONFIRMED_CERTIFICATE_JSON_BOUND_SEPARATE_FROM_WIRE_BOUND"
        or doc["native_component_execution"] is not True
        or doc["native_runtime_execution"] is not False
        or doc["native_export_authenticated"] is not False
        or doc["gate_eligible"] is not False
    ):
        raise ValueError("substituted native contract-size evidence")
    return doc


def cross_check(vcvars):
    blobs = pinned.sources()
    build = ROOT / "formal/build/native-contract-size"
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
        "harness.cpp canonical.cpp sha256.cpp contracts.cpp /Fe:size.exe\n"
        "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    run = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (run.stdout + run.stderr).replace(b"\r\n", b"\n")
    if run.returncode:
        raise RuntimeError(log.decode("utf-8", errors="replace"))
    output = subprocess.check_output([str(build / "size.exe")], cwd=build).decode("ascii")
    output = output.replace("\r\n", "\n")
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
        "status": "CONFIRMED_CERTIFICATE_JSON_BOUND_SEPARATE_FROM_WIRE_BOUND",
        "source_commit": pinned.native.SOURCE,
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
        print("PASS_RETAINED_CONTRACT_SIZE_CHECKS_NOT_NATIVE_AUTHORITY")
