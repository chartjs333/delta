"""Separate PR50 ISC body witnesses and exact-source C++ encoder cross-check.

Only encoder/SHA components are compiled; no runtime, admission, WAL or exporter
is run. No legacy trace, ID, receipt or journal is rewritten.
"""

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path

from formal_artifacts import canonical_json_bytes, write_canonical_json
from native_isc_body import Body, Context, InputTuple, witness

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "60c692f6e391f839829dfc64e93380db54cd507b"
PATHS = [
    "delta-core-cpp/include/delta/core/consensus.hpp",
    "delta-core-cpp/include/delta/certificates/contracts.hpp",
    "delta-core-cpp/src/consensus.cpp",
    "delta-core-cpp/src/canonical.cpp",
    "delta-core-cpp/src/sha256.hpp",
    "delta-core-cpp/src/sha256.cpp",
    "delta-core-cpp/tests/vote_fixture.cpp",
    "delta-core-cpp/tests/vote_fixture.hpp",
]
TARGET = ROOT / "formal/proposals/native-isc-body-vectors.json"
FOLDER = ROOT / "formal/proposals/evidence/native-isc-body"


def source_blobs():
    # Git verifies these blobs through the independently fixed commit object.
    resolved = subprocess.check_output(["git", "rev-parse", SOURCE + "^{commit}"], cwd=ROOT)
    if resolved.decode().strip() != SOURCE:
        raise ValueError("source commit mismatch")
    return {
        path: subprocess.check_output(["git", "show", SOURCE + ":" + path], cwd=ROOT)
        for path in PATHS
    }


def cases():
    def cid(digit):
        return "sha256:" + digit * 64

    # The base primitive values are the pinned vote_fixture.cpp/.hpp values.
    # Signers/quorum belong to the finalized QC, not to this voted body.
    base = Body(
        Context(cid("4"), 1, cid("5"), cid("1"), "round-vote-fixture", cid("d"), 0),
        cid("6"),
        (InputTuple(cid("7"), cid("8"), "domain-a", "ticket-a"),),
    )
    result = {"pinned-vote-fixture": base}
    for field in Context.__annotations__:
        original = getattr(base.context, field)
        changed = original + 1 if type(original) is int else original + "x"
        result["changed-context-" + field] = replace(
            base, context=replace(base.context, **{field: changed})
        )
    for field in InputTuple.__annotations__:
        row = replace(base.tuples[0], **{field: getattr(base.tuples[0], field) + "x"})
        result["changed-tuple-" + field] = replace(base, tuples=(row,))
    result["changed-root"] = replace(base, input_root=cid("9"))
    result["empty-tuples-encoding-not-admission"] = replace(base, tuples=())
    second = replace(base.tuples[0], ticket_id="ticket-b")
    result["two-tuples"] = replace(base, tuples=(*base.tuples, second))
    result["reversed-tuples-preserved"] = replace(base, tuples=(second, *base.tuples))
    result["duplicate-tuples-preserved"] = replace(base, tuples=base.tuples * 2)
    result["uint64-endpoints"] = replace(
        base, context=replace(base.context, height=0, view=2**64 - 1)
    )
    result["ascii-nul-not-admission"] = replace(base, input_root="a\0b")
    result["max-text"] = replace(base, input_root="x" * 128)
    result["empty-text-not-admission"] = replace(base, input_root="")
    return result


def document():
    blobs = source_blobs()
    return {
        "version": "deltareduce.native-voted-body-fixture.v1-candidate",
        "source_commit": SOURCE,
        "source_sha256": {path: hashlib.sha256(raw).hexdigest() for path, raw in blobs.items()},
        "provenance": "SYNTHETIC_PINNED_SOURCE_FIXTURE_NOT_NATIVE_EXPORT",
        "native_export_authenticated": False,
        "gate_eligible": False,
        "cases": {name: witness(body) for name, body in cases().items()},
        "limits": [
            "Only the base case uses original fixture primitives; "
            "others are codec boundary/mutation cases.",
            "Typed hash encoding is not admission; "
            "invalid IDs, duplicates and order are not certified.",
            "ASCII<=128, 4096 tuples and 4MiB are proposal tooling bounds, "
            "not native admission bounds.",
            "Native input_root is retained as a primitive; "
            "its availability/Merkle provenance is unproved.",
            "No signer list or finalized InputSetCertificate/QC ID "
            "is substituted for the voted body.",
            "Full public config/policy/content projection, phase/QC admission "
            "and journal/recovery remain open.",
            "Legacy diagnostic envelopes, receipts, sequences and roots are unchanged.",
        ],
    }


def definition(raw, name, structure=False):
    text = raw.decode("utf-8")
    pattern = (
        (r"^struct " + re.escape(name) + r" \{")
        if structure
        else (r"^(?:\[\[nodiscard\]\] )?(?:void|std::string) " + re.escape(name) + r"\(")
    )
    matches = list(re.finditer(pattern, text, re.M))
    if len(matches) != 1:
        raise ValueError("source definition not unique: " + name)
    start = matches[0].start()
    brace = text.index("{", matches[0].end() - 1)
    depth, end = 1, brace + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    if structure:
        if text[end] != ";":
            raise ValueError("struct terminator")
        end += 1
    code = text[start:end]
    return code, {
        "name": name,
        "first_line": text.count("\n", 0, start) + 1,
        "last_line": text.count("\n", 0, end) + 1,
        "sha256": hashlib.sha256(code.encode()).hexdigest(),
    }


def cpp_text(value):
    raw = value.encode("ascii")
    return 'std::string("' + "".join(f"\\x{byte:02x}" for byte in raw) + '", ' + str(len(raw)) + ")"


def cpp_body(body):
    context = ",".join(
        str(value) + "ULL" if type(value) is int else cpp_text(value)
        for value in vars(body.context).values()
    )
    rows = ",".join(
        "{" + ",".join(cpp_text(v) for v in vars(row).values()) + "}" for row in body.tuples
    )
    return "{{" + context + "}," + cpp_text(body.input_root) + ",{" + rows + "}}"


def harness(blobs):
    spans = []

    def part(path, name, structure=False):
        code, span = definition(blobs[path], name, structure)
        spans.append({"path": path, **span})
        return code + "\n"

    consensus = "delta-core-cpp/src/consensus.cpp"
    contracts = "delta-core-cpp/include/delta/certificates/contracts.hpp"
    code = '#include "sha256.hpp"\n#include <iostream>\n#include <string>\n#include <vector>\n'
    code += "namespace delta::certificates {\n"
    code += part(contracts, "Context", True) + part(contracts, "InputTuple", True) + "}\n"
    code += "namespace delta::core::canonical { using Bytes=std::vector<std::byte>;\n"
    code += part("delta-core-cpp/src/canonical.cpp", "sha256_hex") + "}\n"
    code += "namespace delta::core::consensus {\n"
    code += part("delta-core-cpp/include/delta/core/consensus.hpp", "VoteInputSetBody", True)
    for name in [
        "append_hash_text",
        "append_hash_u64",
        "append_hash_context",
        "append_hash_input_tuples",
        "authority_content_id",
        "vote_input_set_body_id",
    ]:
        code += part(consensus, name)
    code += "}\n"
    code += "void emit(const char* name, const delta::core::consensus::VoteInputSetBody& b) {\n"
    code += "using namespace delta::core::consensus; delta::core::canonical::Bytes raw;\n"
    code += "append_hash_context(raw,b.context); append_hash_text(raw,b.input_root);\n"
    code += 'append_hash_input_tuples(raw,b.tuples); const char* hex="0123456789abcdef";\n'
    code += "std::cout<<name<<'\\t'; for(auto x:raw) {auto c=std::to_integer<unsigned>(x);"
    code += (
        "std::cout<<hex[c>>4]<<hex[c&15];} std::cout<<'\\t'<<vote_input_set_body_id(b)<<'\\n';}\n"
    )
    code += "int main() {\n"
    for name, body in cases().items():
        code += (
            'emit("' + name + '",delta::core::consensus::VoteInputSetBody' + cpp_body(body) + ");\n"
        )
    code += "}\n"
    return code, spans


def cross_check(vcvars):
    blobs = source_blobs()
    build = ROOT / "formal/build/native-isc-codec"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for name in ["sha256.hpp", "sha256.cpp"]:
        (build / name).write_bytes(blobs["delta-core-cpp/src/" + name])
    code, spans = harness(blobs)
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX harness.cpp sha256.cpp /Fe:isc-codec.exe\n"
        "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    compiled = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    (FOLDER / "compile.txt").write_bytes(
        (compiled.stdout + compiled.stderr).replace(b"\r\n", b"\n")
    )
    if compiled.returncode:
        raise RuntimeError("C++ component compile failed; see compile.txt")
    compiler_match = re.search(
        rb"Optimizing Compiler Version ([0-9.]+) for x64", compiled.stdout + compiled.stderr
    )
    if not compiler_match:
        raise RuntimeError("measured compiler identity missing")
    output = subprocess.check_output([str(build / "isc-codec.exe")], cwd=build)
    observed = {}
    for line in output.decode("ascii").splitlines():
        name, encoded, body_id = line.split("\t")
        if name in observed:
            raise ValueError("duplicate C++ case")
        observed[name] = {"body_bytes_hex": encoded, "body_id": body_id}
    expected = {
        name: {"body_bytes_hex": b.encode().hex(), "body_id": b.content_id()}
        for name, b in cases().items()
    }
    if observed != expected:
        raise ValueError("C++/Python encoder or SHA mismatch")
    # Retain the exact executable *source*, not generated binaries/private data.
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS_EXACT_SOURCE_ENCODER_SHA_COMPONENTS_ONLY",
        "source_commit": SOURCE,
        "cases": len(observed),
        "source_sha256": {path: hashlib.sha256(raw).hexdigest() for path, raw in blobs.items()},
        "extracted_definitions": spans,
        "unmodified_translation_unit": "delta-core-cpp/src/sha256.cpp",
        "compiler": "MSVC " + compiler_match[1].decode("ascii") + " x64",
        "compiler_flags": "/std:c++20 /EHsc /W4 /WX",
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "result_sha256": hashlib.sha256(canonical_json_bytes(observed)).hexdigest(),
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "observed": observed,
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, document())
    if args.vcvars:
        result = cross_check(args.vcvars)
        print(result["status"], result["cases"])
    else:
        print(json.dumps({"status": "GENERATED_SYNTHETIC_BODY_WITNESSES", "cases": len(cases())}))
