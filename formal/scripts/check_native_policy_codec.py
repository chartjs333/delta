"""Compare every decoded primitive with unchanged native DVPOL001 parsing."""

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_policy_wal_vectors as source
import native_policy_codec as codec
from formal_artifacts import load_json_strict, write_canonical_json
from native_admission_snapshot import require

ROOT = source.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-policy-codec"


def specimen(kind, path="p", dense=True):
    if kind == "text":
        return path
    if kind == "bool":
        return True
    if kind in {"u32", "u64", "i64"}:
        n = int.from_bytes(hashlib.sha256(path.encode()).digest()[:8], "big")
        return n % 2**32 if kind == "u32" else -(n % 2**63) if kind == "i64" else n
    vector = codec.vector_shape(kind)
    if vector:
        return [specimen(vector[0], path + "[0]", dense)] if dense else []
    return {key: specimen(t, path + "." + key, dense) for key, t in codec.SCHEMAS[kind]}


def dense_policy():
    p = specimen("policy")
    p["validator_ids"] = ["a", "b"]
    p["role"] = 1
    p["configured_abort_reason"] = "HARD_DEADLINE"
    p["candidates"][0]["action"] = 1
    return p


def cases():
    prior = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    rows = [
        (r["name"], bytes.fromhex(r["policy_hex"]))
        for r in prior["observed"]
        if r["name"].startswith("codec-")
    ]
    p = dense_policy()
    raw = codec.encode(p)
    rows.append(("all-nested-fields", raw))

    def changed(name, edit):
        v = copy.deepcopy(p)
        edit(v)
        rows.append((name, codec.HEADER + codec.encode_value("policy", v)))

    changed("empty-local-codec-allowed", lambda v: v.update(local_validator_id=""))
    changed(
        "unordered-deadlines-codec-allowed",
        lambda v: v.update(soft_deadline_tick=10, hard_deadline_tick=1),
    )
    changed("empty-validator-name-codec-allowed", lambda v: v.update(validator_ids=["", "b"]))
    changed("empty-candidate-body-codec-allowed", lambda v: v["candidates"][0].update(body_hash=""))
    changed(
        "snapshot-duplicate-retained",
        lambda v: v["snapshot"].update(finalized_apply_ids=["z", "z"]),
    )
    changed(
        "snapshot-order-retained", lambda v: v["snapshot"].update(finalized_apply_ids=["z", "a"])
    )
    changed(
        "rational-zero-codec-allowed",
        lambda v: v["snapshot"]["apply_profiles"][0]["momentum"].update(denominator=0),
    )
    changed(
        "rational-positive-max",
        lambda v: v["snapshot"]["apply_profiles"][0]["momentum"].update(numerator=2**63 - 1),
    )
    changed(
        "rational-negative-min",
        lambda v: v["snapshot"]["apply_profiles"][0]["momentum"].update(numerator=-(2**63)),
    )
    changed("uint64-max", lambda v: v.update(initial_logical_tick=2**64 - 1))
    changed(
        "uint32-max",
        lambda v: v["snapshot"]["input_set_certificates"][0].update(quorum_threshold=2**32 - 1),
    )
    changed("quoted-text", lambda v: v.update(local_validator_id='a"\\b'))
    changed("validator-order", lambda v: v.update(validator_ids=["b", "a"]))
    changed("validator-duplicate", lambda v: v.update(validator_ids=["a", "a"]))
    changed("no-validators", lambda v: v.update(validator_ids=[]))
    changed("role", lambda v: v.update(role=2))
    changed("abort-reason", lambda v: v.update(configured_abort_reason="NO_ABORT"))
    changed("no-candidates", lambda v: v.update(candidates=[]))
    changed("action-zero", lambda v: v["candidates"][0].update(action=0))
    changed("action-ten", lambda v: v["candidates"][0].update(action=10))

    def duplicate(v):
        c = copy.deepcopy(v["candidates"][0])
        c["action"] = 2
        v["candidates"].append(c)

    changed("context-global-duplicate", duplicate)

    def order(v):
        c = copy.deepcopy(v["candidates"][0])
        c.update(context_id="a", height=0)
        v["candidates"].append(c)

    changed("candidate-order", order)
    for offset in [0, 7, 9, 10, 15]:
        b = bytearray(raw)
        b[offset] ^= 1
        rows.append((f"header-{offset}", bytes(b)))
    rows += [
        ("trailing", raw + b"x"),
        ("oversized", b"x" * (codec.MAX_BYTES + 1)),
        ("text-count-overflow", raw[:16] + b"\xff" * 4 + raw[20:]),
        ("text-control", raw[:20] + b"\x1f" + raw[21:]),
        ("text-high", raw[:20] + b"\x80" + raw[21:]),
    ]
    for size in [0, 15, 16, 19, 20, len(raw) // 2, len(raw) - 1]:
        rows.append((f"truncated-{size}", raw[:size]))
    # Locate two variable-size count/boolean cells through exact preceding encoding.
    prefix = (
        codec.HEADER
        + codec.encode_value("text", p["local_validator_id"])
        + codec.encode_value("text", p["validator_epoch_id"])
    )
    at = len(prefix)
    rows.append(("validator-count-bound", raw[:at] + (4097).to_bytes(4, "big") + raw[at + 4 :]))
    snap = p["snapshot"]
    before = codec.HEADER + b"".join(
        codec.encode_value(t, p[k])
        for k, t in codec.SCHEMAS["policy"]
        if k not in {"snapshot", "candidates"}
    )
    entry = snap["eligibility_bodies"][0]
    before += b"".join(codec.encode_value(t, snap[k]) for k, t in codec.SCHEMAS["snapshot"][:12])
    before += (
        (1).to_bytes(4, "big")
        + codec.encode_value("context", entry["context"])
        + (1).to_bytes(4, "big")
    )
    at = len(before)
    require(raw[:at] == before and raw[at] == 1, "boolean mutation offset")
    rows.append(("boolean-two", raw[:at] + b"\x02" + raw[at + 1 :]))
    return rows


def harness():
    lines = [
        (
            "#include <delta/runtime/vote_codec.hpp>\n#include <iostream>\n"
            "#include <iomanip>\n#include <string>\n#include <cstdint>\nusin"
            "g Bytes=delta::core::canonical::Bytes;\nvoid text(const std::"
            "string& s){std::cout<<std::quoted(s);}\nstd::string hex(const"
            ' Bytes& b){constexpr char d[]="0123456789abcdef";std::string'
            " s;\n for(auto c:b){auto n=std::to_integer<unsigned>(c);s.pus"
            "h_back(d[n>>4U]);s.push_back(d[n&15U]);}return s;}\nBytes unh"
            "ex(const std::string& s){Bytes b;for(std::size_t i=0;i<s.siz"
            "e();i+=2)\n b.push_back(static_cast<std::byte>(std::stoul(s.s"
            "ubstr(i,2),nullptr,16)));return b;}\ntemplate<class T,class F"
            ">void list(const T& v,F emit){std::cout<<'[';bool first=true"
            ";\n for(const auto& x:v){if(!first)std::cout<<',';first=false"
            ";emit(x);}std::cout<<']';}\n"
        )
    ]

    def emit(kind, value):
        if kind == "text":
            return f"text({value});"
        if kind == "bool":
            return f'std::cout<<({value}?"true":"false");'
        if kind in {"u32", "u64", "i64"}:
            cast = "std::int64_t" if kind == "i64" else "std::uint64_t"
            return f"std::cout<<static_cast<{cast}>({value});"
        vector = codec.vector_shape(kind)
        if vector:
            return f"list({value},[](const auto& e){{{emit(vector[0], 'e')}}});"
        return f"dump_{kind}({value});"

    for key, fields in codec.SCHEMAS.items():
        lines.append(f"template<class T>void dump_{key}(const T& x){{std::cout<<'{{';")
        for i, (field, kind) in enumerate(fields):
            if i:
                lines.append("std::cout<<',';")
            lines.append(f"text(\"{field}\");std::cout<<':';" + emit(kind, "x." + field))
        lines.append("std::cout<<'}';}")
    lines.append(
        "int main(){std::string s;while(std::getline(std::cin,s)){try"
        "{\n auto p=delta::runtime::parse_vote_policy_v1(unhex(s));aut"
        'o b=delta::runtime::encode_vote_policy_v1(p);\n std::cout<<"{'
        '\\"status\\":\\"ACCEPT\\",\\"reencoded_hex\\":";text(hex(b));\n std'
        '::cout<<",\\"value\\":";dump_policy(p);std::cout<<"}\\n";\n }cat'
        'ch(const std::exception&){std::cout<<"{\\"status\\":\\"REJECT\\"'
        '}\\n";}}}\n'
    )
    return "\n".join(lines)


def validate(rows):
    inputs = cases()
    require(len(rows) == len(inputs), "case count")
    for row, (name, raw) in zip(rows, inputs, strict=True):
        require(
            row["name"] == name and row["input_sha256"] == hashlib.sha256(raw).hexdigest(),
            "case identity",
        )
        try:
            value = codec.decode(raw)
        except ValueError:
            require(
                row
                == dict(name=name, input_sha256=hashlib.sha256(raw).hexdigest(), status="REJECT"),
                "native rejection",
            )
            continue
        require(
            row["status"] == "ACCEPT" and row["reencoded_hex"] == raw.hex(), "native byte inverse"
        )
        require(row["value"] == value, "every native primitive/ordered vector")
    return rows


def cross_check(vcvars):
    blobs = source.sources()
    build = ROOT / "formal/build/native-policy-codec"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path, raw in blobs.items():
        p = (
            build / "include" / path.split("/include/")[1]
            if "/include/" in path
            else build / Path(path).name
        )
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    code = harness()
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    cmd = (
        f'@echo off\ncall "{vcvars}" >nul\nif errorlevel 1 exit /b 1\n'
        f"cl {source.FLAGS} /Iinclude harness.cpp "
    )
    cmd += (
        " ".join(Path(p).name for p in source.UNITS)
        + " /Fe:policy-codec.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    result = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (result.stdout + result.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()) + "\n", encoding="utf-8", newline="\n"
    )
    require(result.returncode == 0, "native compilation; inspect log")
    inputs = cases()
    raw = subprocess.check_output(
        [str(build / "policy-codec.exe")],
        input=("\n".join(b.hex() for _, b in inputs) + "\n").encode(),
        timeout=180,
    )
    parsed = [
        json.loads(line, object_pairs_hook=source.admission.unique) for line in raw.splitlines()
    ]
    require(len(parsed) == len(inputs), "native output count")
    rows = validate(
        [
            dict(name=name, input_sha256=hashlib.sha256(b).hexdigest(), **row)
            for (name, b), row in zip(inputs, parsed, strict=True)
        ]
    )
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    doc = dict(
        status="PASS_NATIVE_POLICY_CODEC_NOT_ADMISSION",
        source_commit=source.SOURCE,
        source_sha256={p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        compiler=re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        compiler_flags=source.FLAGS,
        unmodified_translation_units=source.UNITS,
        harness_sha256=hashlib.sha256(code.encode()).hexdigest(),
        observed=rows,
        native_codec_execution=True,
        native_admission_proved=False,
        native_export_authenticated=False,
        gate_eligible=False,
    )
    write_canonical_json(FOLDER / "cpp-cross-check.json", doc)
    return doc


def verify_document(doc):
    require(doc["status"] == "PASS_NATIVE_POLICY_CODEC_NOT_ADMISSION", "status")
    require(doc["source_commit"] == source.SOURCE, "source commit")
    require(
        doc["source_sha256"]
        == {p: hashlib.sha256(b).hexdigest() for p, b in source.sources().items()},
        "source blobs",
    )
    require(doc["harness_sha256"] == hashlib.sha256(harness().encode()).hexdigest(), "harness")
    require(
        doc["compiler"] == "19.29.30146"
        and doc["compiler_flags"] == source.FLAGS
        and doc["unmodified_translation_units"] == source.UNITS,
        "build",
    )
    require(
        doc["native_codec_execution"] is True
        and all(
            doc[k] is False
            for k in ["native_admission_proved", "native_export_authenticated", "gate_eligible"]
        ),
        "scope",
    )
    validate(doc["observed"])
    return doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    doc = (
        cross_check(args.vcvars)
        if args.vcvars
        else verify_document(load_json_strict(FOLDER / "cpp-cross-check.json"))
    )
    print(doc["status"], len(doc["observed"]))
