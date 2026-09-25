"""Run unchanged native InputLedger and retain exact component operation snapshots."""

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_certificate_chain as chain
from formal_artifacts import canonical_json_bytes, write_canonical_json
from native_certificate_chain import content_id, voted_body
from native_input_ledger import bind_frozen_isc, check_required_ticket_coverage

ROOT, SOURCE = chain.ROOT, chain.SOURCE
TARGET = ROOT / "formal/proposals/native-input-ledger-vectors.json"
FOLDER = ROOT / "formal/proposals/evidence/native-input-ledger"


def cid(digit):
    return "sha256:" + digit * 64


def proof(ticket, commitment, certificate):
    return {
        "ticket_id": ticket,
        "commitment_id": cid(commitment),
        "certificate_id": cid(certificate),
        "covered_leaf_ids": [cid("1"), cid("2")],
        "attester_ids": ["storage-1", "storage-2", "storage-3"],
        "threshold": 3,
    }


def scenarios():
    """Hand-authored expected component frames; not a Python implementation of Next."""
    cases = []
    state = {
        "commitments": [],
        "availability": [],
        "frozen_inputs": [],
        "frozen": False,
        "late_commitments": 0,
        "late_availability": 0,
    }

    def step(name, operation, disposition, **changes):
        before = copy.deepcopy(state)
        state.update(copy.deepcopy(changes))
        cases.append(
            {
                "name": name,
                "operation": operation,
                "expected_disposition": disposition,
                "before": before,
                "after": copy.deepcopy(state),
            }
        )

    def commitment(ticket, value):
        return {"ticket_id": ticket, "commitment_id": cid(value)}

    def commit(row):
        return {"kind": "commit", "value": row}

    def available(row, **overrides):
        return {
            "kind": "available",
            "value": row,
            "required_leaves": [cid("1"), cid("2")],
            "permitted_attesters": ["storage-1", "storage-2", "storage-3", "storage-4"],
            "required_threshold": 3,
            **overrides,
        }

    ca, cb, cc, cd = [commitment("ticket-" + t, v) for t, v in zip("abcd", "89ab", strict=True)]
    pa, pb, pc = (
        proof("ticket-a", "8", "7"),
        proof("ticket-b", "9", "6"),
        proof("ticket-c", "a", "5"),
    )
    step("empty-freeze", {"kind": "freeze"}, "ERROR:input_set_empty")
    step("commit-b", commit(cb), "recorded", commitments=[cb])
    step("commit-a-reverse-arrival", commit(ca), "recorded", commitments=[ca, cb])
    step("commit-c-unavailable", commit(cc), "recorded", commitments=[ca, cb, cc])
    step("commit-a-identical", commit(ca), "replay")
    step("commit-a-conflict", commit(commitment("ticket-a", "f")), "ERROR:commitment_equivocation")
    step("commit-unknown", commit(commitment("ticket-z", "f")), "ERROR:unknown_ticket")
    step(
        "commit-invalid-id", commit({**ca, "commitment_id": "invalid"}), "ERROR:identifier_invalid"
    )
    step(
        "availability-no-commitment",
        available(proof("ticket-d", "b", "4")),
        "ERROR:commitment_missing",
    )
    step(
        "availability-wrong-commitment",
        available({**pa, "commitment_id": cid("f")}),
        "ERROR:availability_commitment_mismatch",
    )
    for name, leaves in [
        ("missing", [cid("1")]),
        ("extra", [cid("1"), cid("2"), cid("3")]),
        ("duplicate", [cid("1"), cid("1")]),
        ("reversed", [cid("2"), cid("1")]),
    ]:
        step(
            "coverage-" + name,
            available({**pa, "covered_leaf_ids": leaves}),
            "ERROR:availability_coverage_incomplete",
        )
    for name, attesters in [
        ("short", ["storage-1", "storage-2"]),
        ("duplicate", ["storage-1"] * 3),
        ("foreign", ["storage-1", "storage-2", "storage-z"]),
        ("reversed", ["storage-3", "storage-2", "storage-1"]),
    ]:
        step(
            "attesters-" + name,
            available({**pa, "attester_ids": attesters}),
            "ERROR:availability_attesters_invalid",
        )
    step(
        "threshold-mismatch",
        available({**pa, "threshold": 2}),
        "ERROR:availability_attesters_invalid",
    )
    step(
        "threshold-zero",
        available({**pa, "threshold": 0}, required_threshold=0),
        "ERROR:availability_attesters_invalid",
    )
    step("available-b", available(pb), "recorded", availability=[pb])
    step("available-a-reverse-arrival", available(pa), "recorded", availability=[pa, pb])
    step("available-a-identical", available(pa), "replay")
    step(
        "available-a-conflict",
        available({**pa, "certificate_id": cid("f")}),
        "ERROR:availability_conflict",
    )
    frozen = [
        {
            "ticket_id": p["ticket_id"],
            "commitment_id": p["commitment_id"],
            "availability_certificate_id": p["certificate_id"],
        }
        for p in [pa, pb]
    ]
    step(
        "freeze-partial-permitted-set",
        {"kind": "freeze"},
        "frozen",
        frozen=True,
        frozen_inputs=frozen,
    )
    step("freeze-identical", {"kind": "freeze"}, "frozen")
    step("historical-commit-retry", commit(ca), "replay")
    step("historical-availability-retry", available(pa), "replay")
    step("late-commit-d", commit(cd), "late", late_commitments=1)
    step("late-commit-d-identical", commit(cd), "late")
    step(
        "late-commit-d-conflict",
        commit(commitment("ticket-d", "e")),
        "ERROR:commitment_equivocation",
    )
    step(
        "late-availability-d-with-only-late-commitment",
        available(proof("ticket-d", "b", "4")),
        "ERROR:commitment_missing",
    )
    step("late-availability-c", available(pc), "late", late_availability=1)
    step("late-availability-c-identical", available(pc), "late")
    step(
        "late-availability-c-conflict",
        available({**pc, "certificate_id": cid("e")}),
        "ERROR:availability_conflict",
    )
    step("freeze-remains-original", {"kind": "freeze"}, "frozen")
    return cases


def sources():
    result = chain.blobs()
    for path in [
        "delta-core-cpp/include/delta/core/protocol.hpp",
        "delta-core-cpp/src/certificates/vote_admission.cpp",
    ]:
        result[path] = subprocess.check_output(["git", "show", SOURCE + ":" + path], cwd=ROOT)
    return result


def cpp(value):
    if type(value) is str:
        return json.dumps(value, ensure_ascii=True)
    if type(value) is int:
        return str(value) + "U"
    if type(value) is list:
        return "{" + ",".join(cpp(item) for item in value) + "}"
    if type(value) is dict:
        return "{" + ",".join(cpp(item) for item in value.values()) + "}"
    raise ValueError("unsupported harness literal")


def harness():
    operations = []
    for case in scenarios():
        op = case["operation"]
        if op["kind"] == "commit":
            call = "status(ledger.record_commitment(" + cpp(op["value"]) + "))"
        elif op["kind"] == "available":
            call = (
                "status(ledger.record_availability("
                + ",".join(
                    cpp(op[key])
                    for key in [
                        "value",
                        "required_leaves",
                        "permitted_attesters",
                        "required_threshold",
                    ]
                )
                + "))"
            )
        else:
            call = '(static_cast<void>(ledger.freeze()), std::string("frozen"))'
        operations.append("step(" + cpp(case["name"]) + ",ledger,[&]{return " + call + ";});")
    return (
        HARNESS
        + '\nint main(){InputLedger ledger({"ticket-a","ticket-b","ticket-c","ticket-d"});\n'
        + "\n".join(operations)
        + "\nemitClosure(ledger);\n}\n"
    )


HARNESS = r"""
#include <delta/core/consensus.hpp>
#include <iostream>
#include <iomanip>
using namespace delta::core::consensus;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string id(char c){return "sha256:"+std::string(64,c);}
template<class T,class F> void array(const std::vector<T>& rows,F emit){
 std::cout<<'[';bool first=true;for(const auto& row:rows){if(!first)std::cout<<',';
 first=false;emit(row);}std::cout<<']';}
void strings(const std::vector<std::string>& rows){array(rows,[](const auto& s){q(s);});}
void state(const InputLedger& ledger){
 std::cout<<"{\"commitments\":";
 array(ledger.commitments(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<'}';});
 std::cout<<",\"availability\":";
 array(ledger.availabilities(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<",\"certificate_id\":";
 q(r.certificate_id);std::cout<<",\"covered_leaf_ids\":";strings(r.covered_leaf_ids);
 std::cout<<",\"attester_ids\":";strings(r.attester_ids);
 std::cout<<",\"threshold\":"<<r.threshold<<'}';});
 std::cout<<",\"frozen_inputs\":";
 array(ledger.frozen_inputs(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<",\"availability_certificate_id\":";
 q(r.availability_certificate_id);std::cout<<'}';});
 std::cout<<",\"frozen\":"<<(ledger.frozen()?"true":"false");
 std::cout<<",\"late_commitments\":"<<ledger.late_commitment_count();
 std::cout<<",\"late_availability\":"<<ledger.late_availability_count()<<'}';}
std::string status(Disposition d){switch(d){
 case Disposition::recorded:return "recorded";case Disposition::replay:return "replay";
 case Disposition::late:return "late";}throw std::runtime_error("unknown disposition");}
std::string error(ErrorCode code){switch(code){
 case ErrorCode::identifier_invalid:return "ERROR:identifier_invalid";
 case ErrorCode::unknown_ticket:return "ERROR:unknown_ticket";
 case ErrorCode::commitment_equivocation:return "ERROR:commitment_equivocation";
 case ErrorCode::commitment_missing:return "ERROR:commitment_missing";
 case ErrorCode::availability_commitment_mismatch:return "ERROR:availability_commitment_mismatch";
 case ErrorCode::availability_coverage_incomplete:return "ERROR:availability_coverage_incomplete";
 case ErrorCode::availability_attesters_invalid:return "ERROR:availability_attesters_invalid";
 case ErrorCode::availability_conflict:return "ERROR:availability_conflict";
 case ErrorCode::input_set_empty:return "ERROR:input_set_empty";
 default:throw std::runtime_error("unexpected error");}}
template<class F> void step(const char* name,InputLedger& ledger,F call){
 std::cout<<"{\"name\":";q(name);std::cout<<",\"before\":";state(ledger);
 std::string result;try{result=call();}catch(const ConsensusError& e){result=error(e.code());}
 std::cout<<",\"disposition\":";q(result);std::cout<<",\"after\":";state(ledger);std::cout<<"}\n";}
void emitClosure(const InputLedger& ledger){
 using namespace delta::certificates;
 const Context context{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 std::vector<InputTuple> tuples;
 for(const auto& row:ledger.frozen_inputs()){
 std::string domain;
 if(row.ticket_id=="ticket-a")domain="domain-a";
 else if(row.ticket_id=="ticket-b")domain="domain-b";
 else throw std::runtime_error("missing domain metadata");
 tuples.push_back({row.availability_certificate_id,row.commitment_id,domain,row.ticket_id});}
 const InputSetCertificate certificate{context,id('6'),3,
 {"validator-1","validator-2","validator-3"},tuples};
 const auto raw=canonical_json(certificate);
 const std::string ascii(reinterpret_cast<const char*>(raw.data()),raw.size());
 std::cout<<"{\"name\":\"complete-frozen-isc\",\"certificate_ascii\":";q(ascii);
 std::cout<<",\"certificate_id\":";q(content_id(certificate));
 std::cout<<",\"voted_body_id\":";q(vote_input_set_body_id(project_input_set_vote_body(certificate)));
 std::cout<<"}\n";}
"""


def closure_certificate():
    doc = copy.deepcopy(chain.fixture()[0]["ISC"])
    domains = {"ticket-a": "domain-a", "ticket-b": "domain-b"}
    doc["tuples"] = [
        {**row, "domain_id": domains[row["ticket_id"]]}
        for row in scenarios()[-1]["after"]["frozen_inputs"]
    ]
    return doc


def expected():
    operations = [
        {
            "name": c["name"],
            "before": c["before"],
            "after": c["after"],
            "disposition": c["expected_disposition"],
        }
        for c in scenarios()
    ]
    doc = closure_certificate()
    return [
        *operations,
        {
            "name": "complete-frozen-isc",
            "certificate_ascii": canonical_json_bytes(doc).decode("ascii"),
            "certificate_id": content_id(doc),
            "voted_body_id": voted_body(doc)["body_id"],
        },
    ]


def parse_output(output):
    def unique(pairs):
        doc = {}
        for key, value in pairs:
            if key in doc:
                raise ValueError("duplicate native output field")
            doc[key] = value
        return doc

    observed = [json.loads(line, object_pairs_hook=unique) for line in output.splitlines()]
    if canonical_json_bytes(observed) != canonical_json_bytes(expected()):
        raise ValueError("native operation/state mismatch")
    return observed


def boundary_checks():
    # A row retains the previous pinned ISC tuple's original IDs.
    rows = scenarios()[-1]["after"]["frozen_inputs"]
    isc = chain.fixture()[0]["ISC"]
    complete = closure_certificate()
    whole = bind_frozen_isc(
        canonical_json_bytes(complete),
        content_id(complete),
        rows,
        {"ticket-a": "domain-a", "ticket-b": "domain-b"},
    )
    # The old singleton certificate is not rewritten to this new certificate.
    try:
        bind_frozen_isc(
            canonical_json_bytes(isc),
            content_id(isc),
            rows,
            {"ticket-a": "domain-a", "ticket-b": "domain-b"},
        )
    except ValueError:
        mismatch = "REJECT_FULL_FROZEN_LIST_NOT_SINGLETON_ISC"
    else:
        raise ValueError("omitted frozen row accepted")
    required = ["ticket-" + t for t in "abcd"]
    check_required_ticket_coverage(rows, required, "OMIT_UNAVAILABLE")
    try:
        check_required_ticket_coverage(rows, required, "ABORT_ON_INCOMPLETE")
    except ValueError:
        incomplete = "REJECT_ABORT_ON_INCOMPLETE_COVERAGE"
    else:
        raise ValueError("incomplete required set accepted")
    return {
        "complete_frozen_to_new_isc": whole,
        "complete_ledger_to_prior_isc": mismatch,
        "native_freeze_is_not_abort_policy": incomplete,
        "root_preimage_verified": False,
        "full_public_close_relation": False,
    }


def document():
    blobs = sources()
    return {
        "version": "deltareduce.native-input-ledger.v1-candidate",
        "source_commit": SOURCE,
        "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        "permitted_tickets": ["ticket-" + t for t in "abcd"],
        "cases": scenarios(),
        "boundaries": boundary_checks(),
        "native_export_authenticated": False,
        "gate_eligible": False,
        "scope": "NATIVE_INPUT_LEDGER_COMPONENT_NOT_PUBLIC_CLOSE",
    }


def cross_check(vcvars):
    blobs = sources()
    build = ROOT / "formal/build/native-input-ledger"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path in [
        "delta-core-cpp/include/delta/core/consensus.hpp",
        "delta-core-cpp/include/delta/core/protocol.hpp",
        "delta-core-cpp/include/delta/core/canonical.hpp",
        "delta-core-cpp/include/delta/certificates/contracts.hpp",
    ]:
        target = build / "include" / path.split("/include/")[1]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blobs[path])
    units = ["consensus.cpp", "canonical.cpp", "sha256.cpp", "contracts.cpp"]
    for name in [*units, "sha256.hpp"]:
        source = "delta-core-cpp/src/" + ("certificates/" if name == "contracts.cpp" else "") + name
        (build / name).write_bytes(blobs[source])
    code = harness()
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX /Iinclude harness.cpp "
        "consensus.cpp canonical.cpp sha256.cpp contracts.cpp /Fe:ledger.exe\n"
        "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    compiled = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (compiled.stdout + compiled.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if compiled.returncode:
        raise RuntimeError("native InputLedger compile failed")
    output = subprocess.check_output([str(build / "ledger.exe")], cwd=build).decode("ascii")
    observed = parse_output(output)
    compiler = re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)
    if not compiler:
        raise ValueError("compiler identity absent")
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS_NATIVE_INPUT_LEDGER_COMPONENT_NOT_CLOSE_REFINEMENT",
        "source_commit": SOURCE,
        "source_sha256": document()["source_sha256"],
        "unmodified_translation_units": units,
        "compiler": compiler[1],
        "compiler_flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "observed": observed,
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, document())
    print(cross_check(args.vcvars)["status"] if args.vcvars else "GENERATED_NATIVE_INPUT_LEDGER")
