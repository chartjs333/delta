"""Unchanged native policy codec and isolated Windows runtime/WAL executions."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

import generate_native_admission_vectors as admission
from formal_artifacts import write_canonical_json
from native_policy_wal import (
    bind_vote_entry,
    decode_flat,
    policy_digest,
    receipt,
    snapshot,
    wal_entries,
)

ROOT, SOURCE = admission.ROOT, admission.SOURCE
TARGET = ROOT / "formal/proposals/native-policy-wal-vectors.json"
FOLDER = ROOT / "formal/proposals/evidence/native-policy-wal"
UNITS = [
    *admission.UNITS,
    "delta-core-cpp/src/transition.cpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/src/vote_codec.cpp",
    "delta-runtime-cpp/src/wal.cpp",
]
FLAGS = "/Bv /std:c++20 /EHsc /W4 /WX /permissive- /fp:strict /DNOMINMAX"


def sources():
    result = admission.sources()
    for path in [
        *UNITS,
        "delta-runtime-cpp/src/wal.hpp",
        "delta-core-cpp/include/delta/core/transition.hpp",
        "delta-runtime-cpp/include/delta/runtime/runtime.hpp",
        "delta-runtime-cpp/include/delta/runtime/bounded_mpsc.hpp",
        "delta-runtime-cpp/include/delta/runtime/vote_codec.hpp",
        "delta-ffi/src/delta_abi.cpp",
        "delta-runtime-cpp/src/sidecar_server.cpp",
        "delta-runtime-cpp/tests/vote_fixture_exporter.cpp",
        "delta-node-java/src/main/java/io/deltareduce/node/sidecar/SidecarSupervisor.java",
    ]:
        result[path] = subprocess.check_output(["git", "show", SOURCE + ":" + path], cwd=ROOT)
    return result


def snapshot_inventory(blobs):
    header = blobs["delta-core-cpp/include/delta/core/consensus.hpp"].decode()
    codec = blobs["delta-runtime-cpp/src/vote_codec.cpp"].decode()
    struct = header.split("struct VoteAdmissionSnapshot {")[1].split("\n};")[0]
    declared = re.findall(r"\b(\w+);", struct.split("bool operator")[0])
    append = codec.split("void append_snapshot(")[1].split("read_snapshot(")[0]
    read = codec.split("read_snapshot(Reader& reader)")[1].split("return snapshot;")[0]
    written = list(dict.fromkeys(re.findall(r"snapshot\.(\w+)", append)))
    loaded = re.findall(r"snapshot\.(\w+)\s*=", read)
    if declared != written or declared != loaded:
        raise ValueError("native snapshot serialization field inventory")
    return declared


MUTATIONS = [
    ("soft-deadline", "f.policy.soft_deadline_tick=51U;"),
    ("hard-deadline", "f.policy.hard_deadline_tick=101U;"),
    ("initial-time", "f.policy.initial_logical_tick=11U;"),
    ("finalized-config", "f.policy.snapshot.finalized_round_config_ids.clear();"),
    ("closed-root", "f.policy.snapshot.input_set_bodies[0].input_root=id('f');bindBody(f);"),
    (
        "closed-commitment",
        "f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');bindBody(f);",
    ),
    (
        "closed-ac",
        "f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');bindBody(f);",
    ),
    ("state-root", "f.state.state_root=id('f');bindState(f);"),
]
CRASHES = [
    ("before", "before_wal_append", 0),
    ("partial", "during_wal_append", 0),
    ("named-before-barrier", "after_wal_append_before_durability", 0),
    ("durable-uncommitted", "after_durability_before_commit", 1),
    ("committed-unreturned", "after_commit_before_effect_return", 1),
    ("copied-unreturned", "after_effect_copy_before_return", 1),
]

HARNESS = r"""
#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
using namespace delta::test::vote_fixture;
using namespace delta::core::consensus;
namespace rt=delta::runtime;
namespace ca=delta::core::canonical;
namespace pr=delta::core::protocol;
using Bytes=ca::Bytes;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string hex(const Bytes& b){constexpr char d[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);s.push_back(d[n&15U]);}
 return s;}
Bytes file(const std::filesystem::path& p){
 if(!std::filesystem::exists(p))return {};
 std::ifstream in(p,std::ios::binary);Bytes b;char c;
 while(in.get(c))b.push_back(static_cast<std::byte>(static_cast<unsigned char>(c)));
 if(!in.eof())throw std::runtime_error("harness file read");return b;}
void bindState(Fixture& f){
 f.policy.snapshot.state_id=ca::content_id(ca::Type::round_state,pr::encode(f.state));}
void bindBody(Fixture& f){
 const auto body=vote_input_set_body_id(f.policy.snapshot.input_set_bodies[0]);
 f.policy.snapshot.closed_input_set_ids={body};f.policy.candidates[0].body_hash=body;
 f.vote.body_hash=body;}
rt::Config config(const std::filesystem::path& p,const Fixture& f){
 rt::Config c;c.directory=p;c.initial_state_bytes=pr::encode(f.state);
 // Exercise the actual operational decoder at every open.
 c.vote_policy=rt::parse_vote_policy_v1(rt::encode_vote_policy_v1(f.policy));return c;}
struct Outcome{std::string type,code,message;};
template<class F> Outcome capture(F f){
 try{f();return {"ACCEPT","",""};}
 catch(const rt::RuntimeError& e){
 return {"RUNTIME_REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
 catch(const ConsensusError& e){
 return {"ADMISSION_REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
 catch(const std::invalid_argument& e){return {"CODEC_REJECT","",e.what()};}
}
void out(const Outcome& o){std::cout<<"{\"status\":";q(o.type);std::cout<<",\"code\":";
 q(o.code);std::cout<<",\"message\":";q(o.message);std::cout<<'}';}
void emit(const std::string& name,const std::filesystem::path& dir,const Fixture& f,
 const Outcome& o,const Bytes& proof={},std::uint64_t seq=0U,
 std::size_t count=0U,bool replay=false){
 std::cout<<"{\"name\":";q(name);std::cout<<",\"outcome\":";out(o);
 std::cout<<",\"policy_hex\":";q(hex(rt::encode_vote_policy_v1(f.policy)));
 std::cout<<",\"initial_state_hex\":";q(hex(pr::encode(f.state)));
 std::cout<<",\"receipt_hex\":";q(hex(proof));std::cout<<",\"sequence\":"<<seq;
 std::cout<<",\"recovered_votes\":"<<count<<",\"replay\":"<<(replay?"true":"false");
 std::cout<<",\"wal_hex\":";q(hex(file(dir/"runtime.wal")));
 std::cout<<",\"snapshot_hex\":";q(hex(file(dir/"runtime.snapshot")));std::cout<<"}\n";
}
Bytes checkedReceipt(const rt::VoteReceipt& r){
 auto b=rt::encode_vote_receipt_v1(r);auto parsed=rt::parse_vote_receipt_v1(b);
 if(parsed.frame!=r.frame||parsed.vote_id!=r.vote_id||parsed.journal_sequence!=r.journal_sequence
 ||parsed.context_id!=r.context_id||parsed.action!=r.action||parsed.replay)
 throw std::runtime_error("receipt codec mismatch");return b;}
void codec(VoteAction action){
 auto f=full(action);auto b=rt::encode_vote_policy_v1(f.policy);
 auto p=rt::parse_vote_policy_v1(b);
 if(rt::encode_vote_policy_v1(p)!=b)throw std::runtime_error("policy reencode");
 std::size_t truncated=0U;
 if(action==VoteAction::input_set){for(std::size_t n=0;n<b.size();++n){
 auto status=capture([&]{static_cast<void>(rt::parse_vote_policy_v1(
 std::span<const std::byte>(b).first(n)));});
 if(status.type!="CODEC_REJECT")throw std::runtime_error("truncated policy accepted");++truncated;}}
 std::cout<<"{\"name\":";q("codec-"+std::string(vote_kind_name(action)));
 std::cout<<",\"policy_hex\":";q(hex(b));std::cout<<",\"sha256\":";q(ca::sha256_hex(b));
 std::cout<<",\"roundtrip\":true,\"truncated_rejections\":"<<truncated<<"}\n";
}
void malformed(){
 auto f=full(VoteAction::input_set);auto raw=rt::encode_vote_policy_v1(f.policy);
 std::vector<Bytes> cases;
 auto b=raw;b[0]=std::byte{'X'};cases.push_back(b);
 b=raw;b[9]=std::byte{2};cases.push_back(b);
 b=raw;b[15]=std::byte{1};cases.push_back(b);
 b=raw;b.push_back(std::byte{0});cases.push_back(b);
 b=Bytes(rt::max_vote_policy_v1_bytes+1U);cases.push_back(b);
 std::size_t i=0;
 for(const auto& item:cases){
 auto o=capture([&]{static_cast<void>(rt::parse_vote_policy_v1(item));});
 std::cout<<"{\"name\":";q("malformed-"+std::to_string(i++));std::cout<<",\"outcome\":";
 out(o);std::cout<<"}\n";}
}
void basic(const std::filesystem::path& dir){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 {
 auto c=config(dir,f);rt::Runtime runtime(c);
 // Caller mutation after construction cannot alter the by-value runtime policy.
 c.vote_policy->hard_deadline_tick=0U;
 rt::VoteReceipt result{};
 auto o=capture([&]{result=runtime.record_vote(vote);});
 emit("record",dir,f,o,checkedReceipt(result),runtime.journal_sequence(),
 runtime.recovered_vote_count(),result.replay);
 o=capture([&]{result=runtime.record_vote(vote);});
 emit("retry",dir,f,o,checkedReceipt(result),runtime.journal_sequence(),
 runtime.recovered_vote_count(),result.replay);
 auto conflict=f.vote;conflict.body_hash=id('f');conflict.durable_sequence=2U;
 o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(conflict)));});
 emit("conflict",dir,f,o,{},runtime.journal_sequence(),runtime.recovered_vote_count());
 runtime.snapshot();
 emit("snapshot",dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),runtime.recovered_vote_count());
 }
 {
 rt::Runtime runtime(config(dir,f));
 emit("reopen",dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),runtime.recovered_vote_count());
 auto r=runtime.record_vote(vote);
 emit("reopen-retry",dir,f,{"ACCEPT","",""},checkedReceipt(r),runtime.journal_sequence(),
 runtime.recovered_vote_count(),r.replay);
 }
 auto c=config(dir,f);c.vote_policy.reset();
 auto o=capture([&]{rt::Runtime runtime(c);});
 emit("reopen-no-policy",dir,f,o);
}
template<class F> void changed(const std::string& name,const std::filesystem::path& base,
 const std::filesystem::path& empty,F change){
 auto f=full(VoteAction::input_set);change(f);
 validate_vote_admission_policy(f.policy,f.state);
 auto o=capture([&]{rt::Runtime runtime(config(base,f));});
 emit("changed-reopen-"+name,base,f,o);
 o=capture([&]{rt::Runtime runtime(config(empty,f));});
 emit("changed-empty-"+name,empty,f,o);
}
void crash(const std::string& name,const std::filesystem::path& dir,rt::CrashPoint point){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 {
 rt::Runtime runtime(config(dir,f));
 auto o=capture([&]{static_cast<void>(runtime.record_vote(vote,point));});
 runtime.close();emit("crash-"+name,dir,f,o,{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 }
 {
 rt::Runtime runtime(config(dir,f));
 emit("recover-"+name,dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 auto r=runtime.record_vote(vote);
 emit("retry-"+name,dir,f,{"ACCEPT","",""},checkedReceipt(r),runtime.journal_sequence(),
 runtime.recovered_vote_count(),r.replay);
 }
}
void guard(const std::filesystem::path& dir,VoteAction action){
 auto f=full(action);rt::Runtime runtime(config(dir,f));
 auto o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(f.vote)));});
 emit("guard-"+std::string(vote_kind_name(action)),dir,f,o,{},
 runtime.journal_sequence(),runtime.recovered_vote_count());
}
void advance(const std::filesystem::path& dir){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 auto other=full(VoteAction::round_config,f.state);
 f.policy.candidates.insert(f.policy.candidates.begin(),other.candidate);
 rt::Runtime runtime(config(dir,f));auto original=runtime.record_vote(vote);
 pr::Command command{"validator-1",id('c'),"FINALIZE_INPUT_FREEZE",1U,11U,
 "freeze-after-isc",f.state.round_id,0U};
 static_cast<void>(runtime.submit(pr::encode(command)));
 auto r=runtime.record_vote(vote);
 emit("after-state-command-retry",dir,f,{"ACCEPT","",""},checkedReceipt(r),
 runtime.journal_sequence(),runtime.recovered_vote_count(),r.replay);
 other.vote.durable_sequence=3U;
 auto o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(other.vote)));});
 emit("after-state-command-fresh",dir,f,o,{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 runtime.close();
 rt::Runtime reopened(config(dir,f));auto again=reopened.record_vote(vote);
 emit("after-state-command-reopen-retry",dir,f,{"ACCEPT","",""},checkedReceipt(again),
 reopened.journal_sequence(),reopened.recovered_vote_count(),again.replay);
}
void corrupt(const std::filesystem::path& base,const std::filesystem::path& dir,bool snap){
 auto f=full(VoteAction::input_set);
 auto write=[&](const std::filesystem::path& path,const Bytes& b){
 std::ofstream out(path,std::ios::binary);
 for(auto c:b)out.put(static_cast<char>(c));
 if(!out)throw std::runtime_error("harness corrupt fixture write");};
 auto wal=file(base/"runtime.wal");
 if(!snap)wal.back()^=std::byte{1};
 write(dir/"runtime.wal",wal);
 if(snap){auto b=file(base/"runtime.snapshot");b.back()^=std::byte{1};
 write(dir/"runtime.snapshot",b);}
 auto o=capture([&]{rt::Runtime runtime(config(dir,f));});
 emit(snap?"corrupt-snapshot":"corrupt-wal",dir,f,o);
}
int main(int argc,char** argv){
 if(argc!=2)throw std::runtime_error("isolated directory required");
 std::filesystem::path root(argv[1]);
 auto dir=[&](const std::string& name){auto p=root/name;
 if(std::filesystem::exists(p))throw std::runtime_error("directory is not fresh");
 std::filesystem::create_directories(p);return p;};
 for(auto a:{VoteAction::round_config,VoteAction::input_set,VoteAction::eligibility,
 VoteAction::aggregation_plan,VoteAction::parameter,VoteAction::aggregate_root,
 VoteAction::apply,VoteAction::view_change,VoteAction::abort})codec(a);
 malformed();auto base=dir("baseline");basic(base);
"""


def harness():
    body = []
    for name, code in MUTATIONS:
        body.append(f'changed("{name}",base,dir("{name}"),[](auto& f){{{code}}});')
    for name, point, _ in CRASHES:
        body.append(f'crash("{name}",dir("crash-{name}"),rt::CrashPoint::{point});')
    body += [
        'guard(dir("parameter"),VoteAction::parameter);',
        'guard(dir("apply"),VoteAction::apply);',
        'advance(dir("advance"));',
        'corrupt(base,dir("corrupt-wal"),false);',
        'corrupt(base,dir("corrupt-snapshot"),true);',
        "}\n",
    ]
    return HARNESS + "\n".join(body)


def parse_output(output):
    rows = [json.loads(line, object_pairs_hook=admission.unique) for line in output.splitlines()]
    by = {r["name"]: r for r in rows}
    expected = [
        *(
            f"codec-{x}"
            for x in [
                "ROUND_CONFIG",
                "ISC",
                "EC",
                "APC",
                "PARAMETER",
                "AGGREGATE_ROOT",
                "APPLY",
                "VIEW_CHANGE",
                "ABORT",
            ]
        ),
        *(f"malformed-{i}" for i in range(5)),
        "record",
        "retry",
        "conflict",
        "snapshot",
        "reopen",
        "reopen-retry",
        "reopen-no-policy",
        *(
            f"{prefix}-{name}"
            for name, _ in MUTATIONS
            for prefix in ["changed-reopen", "changed-empty"]
        ),
        *(f"{prefix}-{name}" for name, _, _ in CRASHES for prefix in ["crash", "recover", "retry"]),
        "guard-PARAMETER",
        "guard-APPLY",
        "after-state-command-retry",
        "after-state-command-fresh",
        "after-state-command-reopen-retry",
        "corrupt-wal",
        "corrupt-snapshot",
    ]
    if list(by) != expected or len(rows) != len(expected):
        raise ValueError("native policy/WAL diagnostic completeness/order")
    for row in rows:
        name = row["name"]
        if name.startswith("codec-"):
            if set(row) != {"name", "policy_hex", "sha256", "roundtrip", "truncated_rejections"}:
                raise ValueError("codec diagnostic fields")
            if type(row["truncated_rejections"]) is not int:
                raise ValueError("codec diagnostic count")
            raw = bytes.fromhex(row["policy_hex"])
            if policy_digest(raw).decode() != row["sha256"] or row["roundtrip"] is not True:
                raise ValueError("native full policy codec/hash")
            if name == "codec-ISC" and row["truncated_rejections"] != len(raw):
                raise ValueError("native policy truncated coverage")
            continue
        if name.startswith("malformed-"):
            if set(row) != {"name", "outcome"}:
                raise ValueError("malformed diagnostic fields")
            if row["outcome"]["status"] != "CODEC_REJECT":
                raise ValueError("native codec accepted malformed policy")
            continue
        if set(row) != {
            "name",
            "outcome",
            "policy_hex",
            "initial_state_hex",
            "receipt_hex",
            "sequence",
            "recovered_votes",
            "replay",
            "wal_hex",
            "snapshot_hex",
        }:
            raise ValueError("runtime diagnostic fields")
        if set(row["outcome"]) != {"status", "code", "message"} or not all(
            type(v) is str for v in row["outcome"].values()
        ):
            raise ValueError("runtime diagnostic outcome")
        if type(row["replay"]) is not bool or any(
            type(row[k]) is not int or row[k] < 0 for k in ["sequence", "recovered_votes"]
        ):
            raise ValueError("runtime diagnostic count/replay")
        for key in ["policy_hex", "initial_state_hex", "receipt_hex", "wal_hex", "snapshot_hex"]:
            if type(row[key]) is not str or bytes.fromhex(row[key]).hex() != row[key]:
                raise ValueError("noncanonical diagnostic hex")
        policy_digest(bytes.fromhex(row["policy_hex"]))
        decode_flat(bytes.fromhex(row["initial_state_hex"]), 5)
        failure = name.startswith(("changed-reopen-", "crash-", "guard-", "corrupt-")) or name in {
            "conflict",
            "reopen-no-policy",
            "after-state-command-fresh",
        }
        if (row["outcome"]["status"] == "ACCEPT") == failure:
            raise ValueError(f"unexpected native result: {name}: {row['outcome']}")
        if failure and row["receipt_hex"]:
            raise ValueError("rejected/crashed call exposed receipt")
        if name.startswith("corrupt-"):
            expected_code = "4" if name == "corrupt-wal" else "5"
            if (
                row["outcome"]["status"] != "RUNTIME_REJECT"
                or row["outcome"]["code"] != expected_code
            ):
                raise ValueError("corrupt durable bytes accepted")
            continue
        if name.startswith("changed-reopen-"):
            if (
                row["outcome"]["message"]
                != "durable vote admission-policy identity differs from startup policy"
            ):
                raise ValueError("changed policy not rejected at identity boundary")
        if (
            name.startswith("guard-")
            and row["outcome"]["message"]
            != "arithmetic vote lacks authoritative native recomputation inputs"
        ):
            raise ValueError("arithmetic guard absent")
        if name.startswith("crash-"):
            if row["outcome"]["code"] != "10":
                raise ValueError("expected injected native crash")
            # A partial append is not a complete WAL observation.
            if name == "crash-partial":
                continue
        wal = bytes.fromhex(row["wal_hex"])
        entries = wal_entries(wal)
        policy = bytes.fromhex(row["policy_hex"])
        if not name.startswith("changed-reopen-"):
            for entry in entries:
                if entry["kind"] == 2:
                    bind_vote_entry(entry, policy)
        if row["receipt_hex"]:
            parsed = receipt(bytes.fromhex(row["receipt_hex"]))
            if entries[parsed["sequence"] - 1]["command"] != parsed["frame"]:
                raise ValueError("receipt is not original durable frame")
        if row["snapshot_hex"]:
            snap = snapshot(bytes.fromhex(row["snapshot_hex"]))
            if snap["state"] != bytes.fromhex(row["initial_state_hex"]) and not name.startswith(
                "changed-reopen-"
            ):
                raise ValueError("snapshot state mismatch")
    original = by["record"]
    for name in [
        "retry",
        "reopen-retry",
        "after-state-command-retry",
        "after-state-command-reopen-retry",
    ]:
        if by[name]["receipt_hex"] != original["receipt_hex"] or by[name]["replay"] is not True:
            raise ValueError("historical receipt identity/replay")
    for name, _, survivors in CRASHES:
        recovered, retried = by["recover-" + name], by["retry-" + name]
        if recovered["sequence"] != survivors or recovered["recovered_votes"] != survivors:
            raise ValueError("native recovery durable cut")
        if (
            retried["replay"] is not bool(survivors)
            or retried["receipt_hex"] != original["receipt_hex"]
        ):
            raise ValueError("post-recovery receipt")
    return rows


def document():
    blobs = sources()
    return dict(
        version="deltareduce.native-policy-wal.v1-candidate",
        source_commit=SOURCE,
        source_sha256={p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        snapshot_fields=snapshot_inventory(blobs),
        policy_mutations=list(map(list, MUTATIONS)),
        injected_crash_cases=list(map(list, CRASHES)),
        native_export_authenticated=False,
        arithmetic_execution=False,
        full_public_recovery_relation=False,
        gate_eligible=False,
    )


def cross_check(vcvars):
    blobs, code = sources(), harness()
    build = ROOT / "formal/build/native-policy-wal"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path, raw in blobs.items():
        target = (
            build / "include" / path.split("/include/")[1]
            if "/include/" in path
            else build / Path(path).name
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    command = (
        '@echo off\ncall "'
        + str(vcvars)
        + '" >nul\nif errorlevel 1 exit /b 1\ncl '
        + FLAGS
        + " /Iinclude harness.cpp "
        + " ".join(Path(p).name for p in UNITS)
        + " /Fe:policy-wal.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    compiled = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (compiled.stdout + compiled.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(line.rstrip() for line in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if compiled.returncode:
        raise RuntimeError("native runtime compile failed; see compile.txt")
    # No removal/move: each execution has a fresh directory beneath the checked build root.
    run = (build / ("run-" + uuid.uuid4().hex)).resolve()
    if build.resolve() not in run.parents:
        raise ValueError("isolated runtime path escaped build root")
    run.mkdir()
    output = subprocess.check_output(
        [str(build / "policy-wal.exe"), str(run)], cwd=build, timeout=180
    ).decode("ascii")
    rows = parse_output(output)
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = dict(
        status="PASS_PINNED_NATIVE_POLICY_WAL_CASES_NOT_FULL_REFINEMENT",
        source_commit=SOURCE,
        source_sha256=document()["source_sha256"],
        unmodified_translation_units=UNITS,
        compiler=re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        compiler_flags=FLAGS,
        observed=rows,
        harness_sha256=hashlib.sha256(code.encode()).hexdigest(),
        native_runtime_execution=True,
        native_wal_execution=True,
        execution_platform="WINDOWS_MSVC_LOCAL_FILESYSTEM",
        crash_mode="IN_PROCESS_INJECTED_EXCEPTIONS_NOT_OS_POWER_LOSS",
        native_export_authenticated=False,
        full_public_recovery_relation=False,
        arithmetic_execution=False,
        gate_eligible=False,
    )
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, document())
    print(cross_check(args.vcvars)["status"] if args.vcvars else "GENERATED_NATIVE_POLICY_WAL")
