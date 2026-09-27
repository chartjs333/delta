"""Exact Q coverage and unchanged native InputLedger component observations."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from dataclasses import asdict
from pathlib import Path

import generate_native_plan_weights as plan_gen
from formal_artifacts import write_canonical_json
from generate_native_source_artifacts import fixture_store
from native_available_q import (
    SOURCE,
    VERSION,
    ledger_inputs,
    observation_bytes,
    resolve_available_q,
    resolve_plan_available_q,
)
from native_source_artifacts import SourceError, require

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "formal/proposals/evidence/native-available-q"
TARGET = ROOT / "formal/proposals/native-available-q-vectors.json"
BOUNDARY_PIN = "fdb8c8c4af1dfeefc50ce019c8165516a4a3ad369e14f1901107559ed96c3036"


def source_blobs():
    raw = (FOLDER / "native-source-boundary.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == BOUNDARY_PIN, "BOUNDARY_SUBSTITUTED")
    sources = {}
    for row in json.loads(raw)["files"]:
        raw = (ROOT / row["retained_path"]).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == row["sha256"], "SOURCE_SUBSTITUTED")
        sources[row["path"]] = raw
    return sources


def fixture():
    store, golden, _ = fixture_store()
    m = golden["manifest"]["value"]
    leaves = sorted(s["leaf_id"] for s in m["shards"])
    obs = {
        "version": VERSION,
        "source_commit": SOURCE,
        "provenance": "UNAUTHENTICATED_COMPONENT_INPUT",
        "manifest_id": golden["manifest"]["content_id"],
        "permitted_ticket_ids": [m["ticket_id"]],
        "commitment": {"ticket_id": m["ticket_id"], "commitment_id": "sha256:" + "8" * 64},
        "availability": {
            "ticket_id": m["ticket_id"],
            "commitment_id": "sha256:" + "8" * 64,
            "certificate_id": "sha256:" + "7" * 64,
            "covered_leaf_ids": list(leaves),
            "attester_ids": ["attester-a", "attester-b"],
            "threshold": 2,
        },
        "required_leaf_ids": leaves,
        "permitted_attester_ids": ["attester-a", "attester-b", "attester-c"],
        "required_threshold": 2,
    }
    return store, golden, obs


def cases():
    _, _, base = fixture()
    result = {"actual-004-leaf-coverage-synthetic-ledger-input": base}

    def add(name, fn):
        obs = copy.deepcopy(base)
        fn(obs)
        result[name] = obs

    add("missing-covered-leaf", lambda o: o["availability"]["covered_leaf_ids"].pop())
    add("reversed-covered", lambda o: o["availability"]["covered_leaf_ids"].reverse())
    add(
        "duplicate-covered",
        lambda o: o["availability"]["covered_leaf_ids"].append(o["required_leaf_ids"][-1]),
    )
    add("wrong-commitment", lambda o: o["availability"].update(commitment_id="sha256:" + "9" * 64))
    add("unknown-ticket", lambda o: o.update(permitted_ticket_ids=["not-the-ticket"]))
    add(
        "proof-without-ticket-commitment",
        lambda o: o["availability"].update(ticket_id="not-the-ticket"),
    )
    add(
        "unknown-attester",
        lambda o: o["availability"].update(attester_ids=["attester-a", "unknown"]),
    )
    add(
        "duplicate-attester",
        lambda o: o["availability"].update(attester_ids=["attester-a", "attester-a"]),
    )
    add("insufficient-attesters", lambda o: o["availability"].update(attester_ids=["attester-a"]))
    add("threshold-mismatch", lambda o: o["availability"].update(threshold=1))
    add("zero-threshold", lambda o: o.update(required_threshold=0))
    add("invalid-ac-id", lambda o: o["availability"].update(certificate_id="not-a-content-id"))

    def wrong_required(o):
        o["required_leaf_ids"] = o["required_leaf_ids"][:-1]
        o["availability"]["covered_leaf_ids"] = list(o["required_leaf_ids"])

    add("native-accepts-incomplete-caller-leaf-set", wrong_required)
    add(
        "empty-caller-leaf-set",
        lambda o: (o.update(required_leaf_ids=[]), o["availability"].update(covered_leaf_ids=[])),
    )
    add(
        "native-accepts-unrelated-opaque-ac-id",
        lambda o: o["availability"].update(certificate_id="sha256:" + "a" * 64),
    )
    add(
        "native-accepts-unrelated-opaque-commitment",
        lambda o: (
            o["commitment"].update(commitment_id="sha256:" + "b" * 64),
            o["availability"].update(commitment_id="sha256:" + "b" * 64),
        ),
    )
    return result


def joined_fixture():
    store, golden, obs = fixture()
    _, _, _, original = plan_gen.original_store()
    docs = {k: copy.deepcopy(original[k]) for k in ("ISC", "SEED", "NORM", "EC", "APC")}
    m, config = golden["manifest"]["value"], golden["fixedpoint_config"]["value"]
    t, d = m["ticket_id"], m["domain_id"]
    for doc in docs.values():
        doc["parameter_schema_id"] = m["parameter_schema_id"]
        doc["round_config_id"] = config["base_round_config_id"]
    docs["ISC"]["tuples"] = [
        {
            "ticket_id": t,
            "domain_id": d,
            "commitment_id": obs["commitment"]["commitment_id"],
            "availability_certificate_id": obs["availability"]["certificate_id"],
        }
    ]
    docs["EC"]["entries"][0].update(ticket_id=t, domain_id=d)
    docs["NORM"]["entries"][0]["ticket_id"] = t
    docs["APC"]["accumulator_proof_id"] = m["proof_instance_id"]
    docs["APC"]["weights"] = [{"ticket_id": t, "alpha": {"numerator": "1", "denominator": 1}}]
    docs["APC"]["bucket_assignments"] = [{"ticket_id": t, "bucket_id": "bucket-a"}]
    plan_id, edges = plan_gen.put_graph(store, docs)
    oid, raw = observation_bytes(obs)
    store[oid] = raw
    return store, plan_id, edges, [oid], docs, obs


def generate():
    source_blobs()
    store, golden, _ = fixture()
    records = {}
    for name, obs in cases().items():
        oid, raw = observation_bytes(obs)
        store[oid] = raw
        try:
            frozen = ledger_inputs(obs)
            native = "ACCEPT"
        except SourceError:
            frozen, native = None, "REJECT"
        try:
            q = resolve_available_q(store, oid)
            source = {
                "status": "ACCEPT",
                "manifest_id": q.source.q.manifest_id,
                "coordinates": sum(len(r["values"]) for r in q.source.q.rows),
            }
        except SourceError as exc:
            source = {"status": "REJECT", "reason": str(exc)}
        records[name] = {
            "observation_id": oid,
            "observation": obs,
            "bytes_hex": raw.hex(),
            "expected_native_component": native,
            "frozen_input": frozen,
            "checked_source_relation": source,
        }
    joined, plan, edges, observations, _, _ = joined_fixture()
    result = resolve_plan_available_q(joined, plan, edges, observations)
    return {
        "version": VERSION,
        "status": "EXACT_Q_COVERAGE_AND_ELIGIBLE_APC_INPUTS_CONTENT_ONLY",
        "source_commit": SOURCE,
        "boundary_sha256": BOUNDARY_PIN,
        "cases": records,
        "original004_manifest": golden["manifest"]["content_id"],
        "synthetic_join": json.loads(json.dumps(asdict(result))),
        "native_export_authenticated": False,
        "commitment_preimage_bound": False,
        "availability_signatures_verified": False,
        "complete_frozen_history_verified": False,
        "original008_history_upgraded": False,
        "gate_eligible": False,
        "scope": "ORIGINAL004_Q_PREIMAGES_WITH_SEPARATE_SYNTHETIC_NATIVE_INPUTS_AND_APC",
    }


def harness():
    def lit(value):
        return json.dumps(value, ensure_ascii=True)

    def strings(values):
        return "{" + ",".join(lit(v) for v in values) + "}"

    code = (
        "#include <delta/core/consensus.hpp>\n#include <iostream>\n"
        "using namespace delta::core::consensus;\nint main(){\n"
    )
    for name, obs in cases().items():
        c, p = obs["commitment"], obs["availability"]
        code += "try { InputLedger ledger(" + strings(obs["permitted_ticket_ids"]) + ");\n"
        code += (
            "static_cast<void>(ledger.record_commitment({"
            + lit(c["ticket_id"])
            + ","
            + lit(c["commitment_id"])
            + "}));\n"
        )
        code += (
            "static_cast<void>(ledger.record_availability({"
            + ",".join(
                [
                    lit(p["ticket_id"]),
                    lit(p["commitment_id"]),
                    lit(p["certificate_id"]),
                    strings(p["covered_leaf_ids"]),
                    strings(p["attester_ids"]),
                    str(p["threshold"]) + "U",
                ]
            )
            + "},"
            + strings(obs["required_leaf_ids"])
            + ","
            + strings(obs["permitted_attester_ids"])
            + ","
            + str(obs["required_threshold"])
            + "U));\n"
        )
        code += "const auto& frozen=ledger.freeze(); if(frozen.size()!=1U) return 2;\n"
        code += (
            "std::cout<<"
            + lit(name + "\tACCEPT\t")
            + '<<frozen[0].ticket_id<<"\\t"<<frozen[0].commitment_id<<"\\t"'
            '<<frozen[0].availability_certificate_id<<"\\n";\n'
        )
        code += (
            "} catch(const ConsensusError& error) { std::cout<<"
            + lit(name + "\tREJECT\t")
            + '<<static_cast<int>(error.code())<<"\\n"; }\n'
        )
    code += "return 0; }\n"
    return code


def cross_check(vcvars: Path):
    sources = source_blobs()
    build = ROOT / "formal/build/native-available-q"
    for path, raw in sources.items():
        dest = build / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    code = harness()
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX /I delta-core-cpp/include harness.cpp "
        "delta-core-cpp/src/consensus.cpp delta-core-cpp/src/canonical.cpp "
        "delta-core-cpp/src/sha256.cpp delta-core-cpp/src/certificates/contracts.cpp "
        "/Fe:available-q.exe\n"
        "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    compiled = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (compiled.stdout + compiled.stderr).replace(b"\r\n", b"\n")
    (FOLDER / "compile.txt").write_bytes(log)
    require(compiled.returncode == 0, "NATIVE_COMPONENT_COMPILE_FAILED")
    compiler = re.search(rb"Optimizing Compiler Version ([0-9.]+) for x64", log)
    require(compiler is not None, "COMPILER_IDENTITY")
    output = subprocess.check_output([str(build / "available-q.exe")], cwd=build)
    expected = generate()["cases"]
    observed = {}
    for line in output.decode("ascii").splitlines():
        name, status, *fields = line.split("\t")
        require(name in expected and name not in observed, "UNEXPECTED_NATIVE_CASE")
        require(status == expected[name]["expected_native_component"], "NATIVE_RESULT_MISMATCH")
        if status == "ACCEPT":
            require(
                fields == list(expected[name]["frozen_input"].values()), "FROZEN_INPUT_MISMATCH"
            )
        else:
            require(len(fields) == 1 and fields[0].isdigit(), "NATIVE_ERROR_CODE")
        observed[name] = {"status": status, "fields": fields}
    require(set(observed) == set(expected), "NATIVE_CASE_COVERAGE")
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    (FOLDER / "compile.cmd").write_bytes((build / "compile.cmd").read_bytes())
    result = {
        "status": "PASS_UNMODIFIED_NATIVE_INPUT_LEDGER_COMPONENT",
        "source_commit": SOURCE,
        "source_sha256": {p: hashlib.sha256(v).hexdigest() for p, v in sources.items()},
        "compiler": "MSVC " + compiler[1].decode(),
        "flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "observed": observed,
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "unmodified_translation_units": [
            p for p in sources if p.endswith(".cpp") and "/tests/" not in p
        ],
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, generate())
    if args.vcvars:
        print(cross_check(args.vcvars)["status"])
    else:
        print("GENERATED_EXACT_SOURCE_COVERAGE_NOT_AUTHENTICATION")
