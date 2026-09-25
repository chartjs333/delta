"""Execute pinned native admission, keeping snapshot provenance explicitly unresolved."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_input_ledger_vectors as ledger
from formal_artifacts import write_canonical_json
from native_admission_snapshot import decode_flat, state_id
from native_isc_body import from_fields

ROOT, SOURCE = ledger.ROOT, ledger.SOURCE
TARGET = ROOT / "formal/proposals/native-admission-snapshot-vectors.json"
FOLDER = ROOT / "formal/proposals/evidence/native-admission-snapshot"
UNITS = [
    "delta-core-cpp/src/consensus.cpp",
    "delta-core-cpp/src/canonical.cpp",
    "delta-core-cpp/src/sha256.cpp",
    "delta-core-cpp/src/protocol.cpp",
    "delta-core-cpp/src/certificates/contracts.cpp",
    "delta-core-cpp/src/certificates/verifier.cpp",
    "delta-core-cpp/src/certificates/vote_admission.cpp",
    "delta-core-cpp/tests/vote_fixture.cpp",
]


def sources():
    result = ledger.sources()
    for path in [
        *UNITS,
        "delta-core-cpp/include/delta/certificates/verifier.hpp",
        "delta-core-cpp/tests/vote_fixture.hpp",
        "delta-runtime-cpp/src/runtime.cpp",
        "delta-runtime-cpp/src/vote_codec.cpp",
    ]:
        result[path] = subprocess.check_output(["git", "show", SOURCE + ":" + path], cwd=ROOT)
    return result


def cases():
    rows = []

    def add(name, code="", policy="ACCEPT", vote="ACCEPT", action="input_set", recovery=False):
        rows.append(
            dict(name=name, action=action, code=code, policy=policy, vote=vote, recovery=recovery)
        )

    for action in [
        "round_config",
        "input_set",
        "eligibility",
        "aggregation_plan",
        "aggregate_root",
        "view_change",
        "abort",
    ]:
        add("original-" + action, action=action)
    add("apply-guard-live", action="apply", vote="REJECT")
    add("apply-guard-recovery", action="apply", vote="REJECT", recovery=True)
    add("parameter-guard-live", action="parameter", vote="REJECT")
    add("parameter-guard-recovery", action="parameter", vote="REJECT", recovery=True)
    changes = {
        "available_ticket_count": "0U",
        "committed_ticket_count": "0U",
        "config_id": "id('f')",
        "durable_sequence": "4U",
        "height": "2U",
        "parent_checkpoint_id": "id('f')",
        "phase": "delta::core::protocol::RoundPhase::eligible",
        "round_id": '"different-round"',
        "state_root": "id('f')",
        "ticket_count": "2U",
        "view": "1U",
    }
    for field, value in changes.items():
        code = f"f.state.{field}={value};"
        if field == "committed_ticket_count":
            code += "f.state.available_ticket_count=0U;"
        add("stale-state-" + field, code, "REJECT", "REJECT")
    for name, code in [
        ("snapshot-state-id", "f.policy.snapshot.state_id=id('f');"),
        ("closed-membership", "f.policy.snapshot.closed_input_set_ids.clear();"),
        ("closed-typed-body", "f.policy.snapshot.input_set_bodies.clear();"),
        ("closed-duplicate", "f.policy.snapshot.closed_input_set_ids.push_back(f.vote.body_hash);"),
        ("closed-foreign", "f.policy.snapshot.closed_input_set_ids={id('f')};"),
        ("body-root-unrebound", "f.policy.snapshot.input_set_bodies[0].input_root=id('f');"),
        (
            "body-commitment-unrebound",
            "f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');",
        ),
        (
            "body-ac-unrebound",
            "f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');",
        ),
        (
            "body-domain-unrebound",
            'f.policy.snapshot.input_set_bodies[0].tuples[0].domain_id="other-domain";',
        ),
        (
            "body-ticket-unrebound",
            'f.policy.snapshot.input_set_bodies[0].tuples[0].ticket_id="other-ticket";',
        ),
        ("body-context", "f.policy.snapshot.input_set_bodies[0].context.view=1U;"),
        ("candidate-context", "f.policy.candidates[0].context_id=id('f');"),
        ("candidate-body", "f.policy.candidates[0].body_hash=id('f');"),
        ("config-foreign-finalized", "f.policy.snapshot.finalized_round_config_ids={id('f')};"),
        ("config-policy", "f.policy.round_config_id=id('f');"),
        ("epoch-policy", "f.policy.validator_epoch_id=id('f');"),
        ("committee-order", "std::swap(f.policy.validator_ids[0],f.policy.validator_ids[1]);"),
        ("committee-duplicate", "f.policy.validator_ids[1]=f.policy.validator_ids[0];"),
        ("schema-policy", "f.policy.snapshot.parameter_schema_id=id('f');"),
        ("arithmetic-profile-policy", "f.policy.snapshot.arithmetic_profile_id=id('f');"),
        ("deadline-policy", "f.policy.soft_deadline_tick=f.policy.hard_deadline_tick;"),
    ]:
        add(name, code, "REJECT", "REJECT")
    for name, code in [
        ("vote-body", "f.vote.body_hash=id('f');"),
        ("vote-context", "f.vote.context_id=id('f');"),
        ("vote-actor", 'f.vote.validator_id="validator-2";'),
        ("vote-epoch", "f.vote.validator_epoch_id=id('f');"),
        ("vote-sequence", "f.vote.durable_sequence=2U;"),
        ("expected-sequence", "expected=2U;"),
        ("vote-height", "f.vote.height=2U;"),
        ("vote-view", "f.vote.view=1U;"),
        ("vote-round", 'f.vote.round_id="other-round";'),
        ("current-parent", "f.policy.candidates[0].parents.parent_checkpoint_id=id('f');"),
        ("not-ready-live", "a.recovery_ready=false;"),
        ("authority-invalidated-live", "a.authority_invalidated=true;"),
        ("at-hard-deadline", "a.logical_tick=f.policy.hard_deadline_tick;"),
        (
            "abort-request",
            'f.policy.snapshot.abort_requests={{f.state.round_id,"INCOMPLETE_INPUT"}};',
        ),
    ]:
        add(name, code, vote="REJECT")
    add("not-ready-recovery", "a.recovery_ready=false;", recovery=True)
    add("invalidated-recovery", "a.authority_invalidated=true;", vote="REJECT", recovery=True)
    add("before-hard-deadline", "a.logical_tick=f.policy.hard_deadline_tick-1U;")
    # These accept at this component boundary. They do NOT authenticate snapshot production.
    add("no-finalized-config-assertion", "f.policy.snapshot.finalized_round_config_ids.clear();")
    add("rebound-summary-root", "f.state.state_root=id('f');bindState(f);")
    add("rebound-summary-counts", "f.state.ticket_count=9U;bindState(f);")
    add(
        "rebound-input-root",
        "f.policy.snapshot.input_set_bodies[0].input_root=id('f');bindBody(f);",
    )
    add(
        "rebound-input-commitment",
        "f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');bindBody(f);",
    )
    add(
        "rebound-input-ac",
        "f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');bindBody(f);",
    )
    return rows


HARNESS = r"""
#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <algorithm>
#include <iomanip>
#include <iostream>
using namespace delta::core::consensus;
using namespace delta::test::vote_fixture;
namespace canonical=delta::core::canonical;
namespace protocol=delta::core::protocol;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string hex(const canonical::Bytes& b){
 constexpr char digits[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned int>(c);
 s.push_back(digits[n>>4U]);s.push_back(digits[n&15U]);}
 return s;}
void strings(const std::vector<std::string>& values){
 std::cout<<'[';bool first=true;for(const auto& v:values){if(!first)std::cout<<',';
 first=false;q(v);}std::cout<<']';}
void contextFields(const delta::certificates::Context& c){
 std::cout<<"{\"arithmetic_profile_id\":";q(c.arithmetic_profile_id);
 std::cout<<",\"height\":"<<c.height<<",\"parameter_schema_id\":";q(c.parameter_schema_id);
 std::cout<<",\"round_config_id\":";q(c.round_config_id);std::cout<<",\"round_id\":";q(c.round_id);
 std::cout<<",\"validator_epoch_id\":";q(c.validator_epoch_id);
 std::cout<<",\"view\":"<<c.view<<'}';}
void bindState(Fixture& f){
 f.policy.snapshot.state_id=canonical::content_id(canonical::Type::round_state,protocol::encode(f.state));}
void bindBody(Fixture& f){
 auto idBody=vote_input_set_body_id(f.policy.snapshot.input_set_bodies[0]);
 f.policy.snapshot.closed_input_set_ids={idBody};
 f.policy.candidates[0].body_hash=idBody;f.vote.body_hash=idBody;}
struct Outcome{std::string status;std::string code;std::string message;};
template<class F> Outcome capture(F operation){
 try{operation();return {"ACCEPT","",""};}
 catch(const ConsensusError& e){
 return {"REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
}
void outcome(const Outcome& o){
 std::cout<<"{\"status\":";q(o.status);std::cout<<",\"code\":";q(o.code);
 std::cout<<",\"message\":";q(o.message);std::cout<<'}';}
template<class F> void run(const char* name,VoteAction action,bool recovery,F mutation){
 auto f=full(action);VoteAdmissionState a{f.policy.initial_logical_tick,true,false};
 std::uint64_t expected=1U;mutation(f,a,expected);
 auto policy=capture([&]{validate_vote_admission_policy(f.policy,f.state);});
 std::string formalAction,context;
 auto vote=capture([&]{auto result=validate_vote_admission(f.policy,f.state,a,f.vote,expected,
   recovery?VoteAdmissionMode::recovery:VoteAdmissionMode::live);
   formalAction=result.formal_action_id;context=result.context_id;});
 std::cout<<"{\"name\":";q(name);std::cout<<",\"policy\":";outcome(policy);
 std::cout<<",\"vote\":";outcome(vote);std::cout<<",\"formal_action\":";q(formalAction);
 std::cout<<",\"returned_context\":";q(context);
 std::cout<<",\"state_hex\":";q(hex(protocol::encode(f.state)));
 std::cout<<",\"snapshot_state_id\":";q(f.policy.snapshot.state_id);
 std::cout<<",\"closed_ids\":";strings(f.policy.snapshot.closed_input_set_ids);
 std::cout<<",\"finalized_config_ids\":";strings(f.policy.snapshot.finalized_round_config_ids);
 std::cout<<",\"input_bodies\":[";
 bool first=true;for(const auto& b:f.policy.snapshot.input_set_bodies){
  if(!first)std::cout<<',';first=false;
  std::cout<<"{\"body_id\":";q(vote_input_set_body_id(b));std::cout<<",\"input_root\":";q(b.input_root);
  std::cout<<",\"context\":";contextFields(b.context);
  std::cout<<",\"tuples\":[";
  bool tfirst=true;for(const auto& t:b.tuples){if(!tfirst)std::cout<<',';tfirst=false;
   std::cout<<"{\"ticket_id\":";q(t.ticket_id);std::cout<<",\"domain_id\":";q(t.domain_id);
   std::cout<<",\"commitment_id\":";q(t.commitment_id);
   std::cout<<",\"availability_certificate_id\":";q(t.availability_certificate_id);std::cout<<'}';}
  std::cout<<"]}";}
 std::cout<<"],\"vote_hex\":";q(hex(protocol::encode(f.vote)));std::cout<<"}\n";
}
"""


def harness():
    body = []
    for row in cases():
        code = row["code"]
        # Unused mutation parameters are explicitly consumed under /WX.
        body.append(
            f"run({json.dumps(row['name'])},VoteAction::{row['action']},"
            + ("true" if row["recovery"] else "false")
            + ",[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;"
            + code
            + "});"
        )
    return HARNESS + "\nint main(){\n" + "\n".join(body) + "\n}\n"


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate diagnostic field")
        result[key] = value
    return result


def parse_output(output):
    rows = [json.loads(line, object_pairs_hook=unique) for line in output.splitlines()]
    if len(rows) != len(cases()):
        raise ValueError("incomplete native diagnostic list")
    for row, case in zip(rows, cases(), strict=True):
        if set(row) != set(
            (
                "name",
                "policy",
                "vote",
                "formal_action",
                "returned_context",
                "state_hex",
                "snapshot_state_id",
                "closed_ids",
                "finalized_config_ids",
                "input_bodies",
                "vote_hex",
            )
        ):
            raise ValueError("diagnostic keys")
        if row["name"] != case["name"]:
            raise ValueError("diagnostic order")
        for kind in ["policy", "vote"]:
            result = row[kind]
            if set(result) != {"status", "code", "message"} or result["status"] != case[kind]:
                raise ValueError(f"native {row['name']} {kind} mismatch: {result}")
            if (result["status"] == "ACCEPT") != (result["code"] == result["message"] == ""):
                raise ValueError("diagnostic outcome fields")
        for field, kind in [("state_hex", 5), ("vote_hex", 3)]:
            raw = bytes.fromhex(row[field])
            if raw.hex() != row[field]:
                raise ValueError("noncanonical hexadecimal")
            decode_flat(raw, kind)
        body_ids = []
        for body in row["input_bodies"]:
            if set(body) != {"body_id", "context", "input_root", "tuples"}:
                raise ValueError("input body diagnostic fields")
            derived = from_fields({k: body[k] for k in ["context", "input_root", "tuples"]})
            if derived.content_id() != body["body_id"]:
                raise ValueError("input body diagnostic identity")
            body_ids.append(body["body_id"])
        if row["policy"]["status"] == "ACCEPT":
            if state_id(bytes.fromhex(row["state_hex"])) != row["snapshot_state_id"]:
                raise ValueError("native state preimage")
            if any(key not in body_ids for key in row["closed_ids"]):
                raise ValueError("closed input diagnostic membership")
        if row["vote"]["status"] == "ACCEPT":
            vote = decode_flat(bytes.fromhex(row["vote_hex"]), 3)
            if row["returned_context"] != vote["context_id"] or not row["formal_action"]:
                raise ValueError("native returned context/action")
        elif row["returned_context"] or row["formal_action"]:
            raise ValueError("rejected vote returned admission")
    return rows


def document():
    return {
        "version": "deltareduce.native-admission-snapshot.v1-candidate",
        "source_commit": SOURCE,
        "source_sha256": {p: hashlib.sha256(b).hexdigest() for p, b in sources().items()},
        "cases": cases(),
        "scope": "SYNTHETIC_NATIVE_ADMISSION_COMPONENT_NOT_AUTHENTICATED_PUBLIC_STATE",
        "native_export_authenticated": False,
        "full_public_state_relation": False,
        "gate_eligible": False,
    }


def cross_check(vcvars):
    blobs = sources()
    build = ROOT / "formal/build/native-admission-snapshot"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path, raw in blobs.items():
        if "/include/" in path:
            target = build / "include" / path.split("/include/")[1]
        else:
            target = build / Path(path).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    code = harness()
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "' + str(vcvars) + '" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX /Iinclude harness.cpp "
        + " ".join(Path(p).name for p in UNITS)
        + " /Fe:admission.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    process = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (process.stdout + process.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if process.returncode:
        raise RuntimeError("native admission compilation failed; see compile.txt")
    output = subprocess.check_output([str(build / "admission.exe")], cwd=build).decode("ascii")
    rows = parse_output(output)
    compiler = re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)
    if not compiler:
        raise ValueError("compiler identity absent")
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS_NATIVE_ADMISSION_COMPONENT_NOT_PUBLIC_REFINEMENT",
        "source_commit": SOURCE,
        "source_sha256": document()["source_sha256"],
        "unmodified_translation_units": UNITS,
        "compiler": compiler[1],
        "compiler_flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "observed": rows,
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "full_public_state_relation": False,
        "gate_eligible": False,
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, document())
    print(cross_check(args.vcvars)["status"] if args.vcvars else "GENERATED_ADMISSION_CASES")
