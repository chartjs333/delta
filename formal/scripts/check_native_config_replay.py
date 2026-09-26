"""Fresh native CONFIG/command WAL checks; strict policy subdomain, not full recovery."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

import generate_native_policy_wal_vectors as source
import native_config_replay as mixed
from formal_artifacts import load_json_strict, write_canonical_json
from native_admission_snapshot import require

ROOT = source.ROOT

FOLDER = ROOT / "formal/proposals/evidence/native-config-replay"
HARNESS = (
    '\n#include "vote_fixture.hpp"\n#include "wal.hpp"\n#include <de'
    "lta/core/transition.hpp>\n#include <delta/runtime/runtime.hpp"
    ">\n#include <delta/runtime/vote_codec.hpp>\n#include <filesyst"
    "em>\n#include <fstream>\n#include <iomanip>\n#include <iostream"
    ">\nusing namespace delta::test::vote_fixture;\nusing namespace"
    " delta::core::consensus;\nnamespace rt=delta::runtime; namesp"
    "ace dt=rt::detail;\nnamespace ca=delta::core::canonical; name"
    "space pr=delta::core::protocol;\nusing Bytes=ca::Bytes;\nstd::"
    "filesystem::path root;\nvoid q(const std::string& s){std::cou"
    "t<<std::quoted(s);}\nstd::string hex(const Bytes& b){constexp"
    'r char d[]="0123456789abcdef";std::string s;\n for(auto c:b){'
    "auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);s."
    "push_back(d[n&15U]);}\n return s;}\nBytes file(const std::file"
    "system::path& p){if(!std::filesystem::exists(p))return {};\n "
    "std::ifstream in(p,std::ios::binary);Bytes b;char c;\n while("
    "in.get(c))b.push_back(static_cast<std::byte>(static_cast<uns"
    'igned char>(c)));\n if(!in.eof())throw std::runtime_error("ha'
    'rness read");return b;}\nstd::filesystem::path dir(const std:'
    ":string& n){auto p=root/n;\n if(std::filesystem::exists(p))th"
    'row std::runtime_error("not fresh");\n std::filesystem::creat'
    "e_directories(p);return p;}\npr::Command command(const std::s"
    "tring& kind,std::uint64_t tick,const std::string& request,\n "
    "std::uint64_t view=0U){return {\"validator-1\",id('a'),kind,1U"
    ',tick,request,"round-vote-fixture",view};}\nrt::Config config'
    "(const std::filesystem::path& p,const Fixture& f,bool policy"
    "){\n rt::Config c;c.directory=p;c.initial_state_bytes=pr::enc"
    "ode(f.state);\n if(policy)c.vote_policy=rt::parse_vote_policy"
    "_v1(rt::encode_vote_policy_v1(f.policy));return c;}\nvoid rec"
    'eipt(const rt::SubmitReceipt& r){\n std::cout<<"{\\"state_hex\\'
    '":";q(hex(r.next_state_bytes));std::cout<<",\\"effects_hex\\":'
    '";\n q(hex(r.effect_batch_bytes));std::cout<<",\\"record_hex\\"'
    ':";q(hex(r.wal_record_bytes));\n std::cout<<",\\"next_id\\":";q'
    '(r.next_state_id);std::cout<<",\\"effects_id\\":";q(r.effect_b'
    'atch_id);\n std::cout<<",\\"record_id\\":";q(r.wal_record_id);s'
    'td::cout<<",\\"sequence\\":"<<r.journal_sequence;\n std::cout<<'
    '",\\"replay\\":"<<(r.replay?"true":"false")<<\'}\';}\nstruct Resu'
    'lt {std::string status="ACCEPT",code="",message="";Bytes sta'
    "te;\n std::uint64_t seq=0U;std::optional<rt::SubmitReceipt> r"
    "eceipt;std::optional<rt::VoteReceipt> vote;};\ntemplate<class"
    " F> Result capture(F f){Result r;try{f(r);}\n catch(const rt:"
    ':RuntimeError& e){r.status="REJECT";r.code=std::to_string(st'
    "atic_cast<int>(e.code()));r.message=e.what();}\n catch(const "
    'std::exception& e){r.status="REJECT";r.code="core";r.message'
    "=e.what();}return r;}\nvoid emit(const std::string& name,cons"
    "t std::string& operation,const std::filesystem::path& p,\n co"
    "nst Fixture& f,bool policy,const Bytes& input,const Result& "
    'r){\n std::cout<<"{\\"name\\":";q(name);std::cout<<",\\"operatio'
    'n\\":";q(operation);\n std::cout<<",\\"status\\":";q(r.status);s'
    'td::cout<<",\\"code\\":";q(r.code);\n std::cout<<",\\"message\\":'
    '";q(r.message);std::cout<<",\\"initial_hex\\":";q(hex(pr::enco'
    'de(f.state)));\n std::cout<<",\\"policy_hex\\":";q(policy?hex(r'
    't::encode_vote_policy_v1(f.policy)):"");\n std::cout<<",\\"clo'
    'ck\\":";if(policy)std::cout<<f.policy.initial_logical_tick;el'
    'se std::cout<<"null";\n std::cout<<",\\"command_hex\\":";q(hex('
    'input));std::cout<<",\\"wal_hex\\":";q(hex(file(p/"runtime.wal'
    '")));\n std::cout<<",\\"snapshot_hex\\":";q(hex(file(p/"runtime'
    '.snapshot")));\n std::cout<<",\\"state_hex\\":";q(hex(r.state))'
    ';std::cout<<",\\"sequence\\":"<<r.seq;\n std::cout<<",\\"receipt'
    '\\":";if(r.receipt)receipt(*r.receipt);else std::cout<<"null"'
    ';std::cout<<",\\"vote_receipt_hex\\":";q(r.vote?hex(rt::encode'
    '_vote_receipt_v1(*r.vote)):"");std::cout<<",\\"vote_replay\\":'
    '"<<(r.vote&&r.vote->replay?"true":"false");std::cout<<"}\\n";'
    "}\nvoid openCase(const std::string& name,const Fixture& f,boo"
    "l policy,\n const std::vector<dt::JournalEntry>& entries,std:"
    ":optional<dt::Snapshot> snap={}){\n auto p=dir(name);{dt::Wal"
    ' wal(p/"runtime.wal");for(const auto& e:entries)wal.append_a'
    'nd_sync(e,false);\n if(snap)wal.write_snapshot(p/"runtime.sna'
    'pshot",*snap);}\n auto r=capture([&](auto& o){rt::Runtime run'
    "time(config(p,f,policy));\n o.state=runtime.state_bytes();o.s"
    'eq=runtime.journal_sequence();});emit(name,"recover",p,f,pol'
    "icy,{},r);}\n\nint main(int argc,char** argv){if(argc!=2)throw"
    ' std::runtime_error("isolated directory required");\n root=ar'
    'gv[1];auto f=full(VoteAction::round_config);auto p=dir("live'
    '");\n auto vote=pr::encode(f.vote);auto c0=command("FINALIZE_'
    'ROUND_CONFIG",11U,"config");\n auto b0=pr::encode(c0);auto c1'
    '=command("ADVANCE_VIEW",12U,"view",1U);\n auto c2=command("CE'
    'RTIFY_ABORT",13U,"abort",1U);Bytes mid;\n {rt::Runtime runtim'
    "e(config(p,f,true));\n auto r=capture([&](auto& o){o.vote=run"
    "time.record_vote(vote);o.state=runtime.state_bytes();o.seq=r"
    'untime.journal_sequence();});\n runtime.snapshot();emit("live'
    '-vote","vote",p,f,true,vote,r);\n for(const auto& c:{c0,c1,c2'
    "}){auto b=pr::encode(c);r=capture([&](auto& o){o.receipt=run"
    "time.submit(b);o.state=runtime.state_bytes();o.seq=runtime.j"
    'ournal_sequence();});\n if(c.request_id=="view")mid=runtime.s'
    'tate_bytes();emit("live-"+c.request_id,"live",p,f,true,b,r);'
    "}\n r=capture([&](auto& o){o.vote=runtime.record_vote(vote);o"
    ".state=runtime.state_bytes();o.seq=runtime.journal_sequence("
    ');});emit("historical-vote","vote-retry",p,f,true,vote,r);\n '
    "r=capture([&](auto& o){o.receipt=runtime.submit(b0);o.state="
    "runtime.state_bytes();o.seq=runtime.journal_sequence();});em"
    'it("historical-command","retry",p,f,true,b0,r);\n auto altere'
    "d=f.vote;altered.signature_id=id('a');auto vb=pr::encode(alt"
    "ered);\n r=capture([&](auto& o){o.vote=runtime.record_vote(vb"
    ');});emit("vote-conflict","vote-retry",p,f,true,vb,r);\n auto'
    " wrong=c0;wrong.body_hash=id('b');auto cb=pr::encode(wrong);"
    "\n r=capture([&](auto& o){o.receipt=runtime.submit(cb);});emi"
    't("command-conflict","retry",p,f,true,cb,r);\n auto fresh=f.v'
    "ote;fresh.context_id=id('a');fresh.durable_sequence=5U;vb=pr"
    "::encode(fresh);\n r=capture([&](auto& o){o.vote=runtime.reco"
    'rd_vote(vb);});emit("fresh-after-command","fresh-vote",p,f,t'
    "rue,vb,r);\n }\n {rt::Runtime runtime(config(p,f,true));auto r"
    "=capture([&](auto& o){o.vote=runtime.record_vote(vote);o.sta"
    "te=runtime.state_bytes();o.seq=runtime.journal_sequence();})"
    ';emit("reopened-vote","vote-retry",p,f,true,vote,r);\n r=capt'
    "ure([&](auto& o){o.receipt=runtime.submit(b0);o.state=runtim"
    'e.state_bytes();o.seq=runtime.journal_sequence();});emit("re'
    'opened-command","retry",p,f,true,b0,r);}\n std::vector<dt::Jo'
    'urnalEntry> entries;{dt::Wal wal(p/"runtime.wal");entries=wa'
    'l.recover().entries;}\n openCase("no-snapshot",f,true,entries'
    ');openCase("snapshot-at-vote",f,true,entries,dt::Snapshot{1U'
    ',pr::encode(f.state)});\n openCase("snapshot-at-command",f,tr'
    'ue,entries,dt::Snapshot{3U,mid});\n openCase("wrong-vote-snap'
    'shot",f,true,entries,dt::Snapshot{1U,mid});\n openCase("wrong'
    '-command-snapshot",f,true,entries,dt::Snapshot{3U,pr::encode'
    '(f.state)});\n openCase("zero-different-snapshot",f,true,entr'
    'ies,dt::Snapshot{0U,mid});\n openCase("ahead-snapshot",f,true'
    ',entries,dt::Snapshot{5U,mid});\n openCase("vote-only",f,true'
    ",{entries[0]},dt::Snapshot{1U,pr::encode(f.state)});\n openCa"
    'se("empty",f,true,{});\n auto changed=entries;changed[0].wal_'
    "record_bytes[0]=std::byte{'0'};openCase(\"wrong-policy-id\",f,"
    "true,changed);\n changed=entries;changed[0].sequence=2U;openC"
    'ase("outer-gap",f,true,changed);\n auto vv=f.vote;vv.durable_'
    "sequence=2U;changed=entries;changed[0].command_or_vote_bytes"
    '=pr::encode(vv);openCase("vote-sequence",f,true,changed);\n c'
    'hanged=entries;std::swap(changed[0],changed[1]);openCase("re'
    'ordered",f,true,changed);\n auto dup=entries[0];dup.sequence='
    '2U;dup.command_or_vote_bytes=pr::encode(vv);openCase("duplic'
    'ate-vote",f,true,{entries[0],dup});\n dup=entries[1];dup.sequ'
    'ence=3U;openCase("duplicate-command",f,true,{entries[0],entr'
    "ies[1],dup});\n vv.durable_sequence=3U;dup=entries[0];dup.seq"
    'uence=3U;dup.command_or_vote_bytes=pr::encode(vv);openCase("'
    'vote-after-command",f,true,{entries[0],entries[1],dup});\n ch'
    "anged=entries;changed[2].next_state_bytes=entries[1].next_st"
    'ate_bytes;openCase("changed-state",f,true,changed);\n changed'
    "=entries;changed[2].effect_batch_bytes=entries[1].effect_bat"
    'ch_bytes;openCase("changed-effects",f,true,changed);\n change'
    "d=entries;changed[2].wal_record_bytes=entries[1].wal_record_"
    'bytes;openCase("changed-record",f,true,changed);\n auto alter'
    "edPolicy=f;alteredPolicy.policy.initial_logical_tick=9U;open"
    'Case("changed-startup-policy",alteredPolicy,true,entries);\n '
    "auto low=c0;low.logical_tick=9U;auto lr=delta::core::transit"
    "ion::apply(pr::encode(f.state),pr::encode(low));\n auto lowEn"
    "try=entries[1];lowEntry.command_or_vote_bytes=pr::encode(low"
    ");lowEntry.next_state_bytes=lr.next_state_bytes;lowEntry.eff"
    "ect_batch_bytes=lr.effect_batch_bytes;lowEntry.wal_record_by"
    'tes=lr.wal_record_bytes;\n openCase("backwards-clock",f,true,'
    "{entries[0],lowEntry});\n}\n"
)


def cross_check(vcvars):
    blobs = source.sources()
    build = ROOT / "formal/build/native-config-replay"
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
    (build / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    cmd = (
        '@echo off\ncall "'
        + str(vcvars)
        + '" >nul\nif errorlevel 1 exit /b 1\ncl '
        + source.FLAGS
        + " /Iinclude harness.cpp "
        + " ".join(Path(p).name for p in source.UNITS)
        + " /Fe:config-replay.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    result = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (result.stdout + result.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(line.rstrip() for line in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    require(result.returncode == 0, "native compile; see log")
    run = (build / ("run-" + uuid.uuid4().hex)).resolve()
    require(build.resolve() in run.parents, "fresh isolated path")
    run.mkdir()
    raw = subprocess.check_output(
        [str(build / "config-replay.exe"), str(run)], cwd=build, timeout=180
    )
    (build / "draft-output.jsonl").write_bytes(raw)
    rows = validate(
        [json.loads(line, object_pairs_hook=source.admission.unique) for line in raw.splitlines()]
    )
    (FOLDER / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    doc = dict(
        status="PASS_CONFIG_COMMAND_RUNTIME_REPLAY_SUBDOMAIN",
        source_commit=source.SOURCE,
        source_sha256={p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        compiler=re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        compiler_flags=source.FLAGS,
        unmodified_translation_units=source.UNITS,
        harness_sha256=hashlib.sha256(HARNESS.encode()).hexdigest(),
        observed=rows,
        native_runtime_execution=True,
        native_wal_execution=True,
        physical_power_loss=False,
        arithmetic_execution=False,
        native_export_authenticated=False,
        mixed_vote_command_recovery=True,
        gate_eligible=False,
    )
    write_canonical_json(FOLDER / "cpp-cross-check.json", doc)
    return doc


NAMES = [
    "live-vote",
    "live-config",
    "live-view",
    "live-abort",
    "historical-vote",
    "historical-command",
    "vote-conflict",
    "command-conflict",
    "fresh-after-command",
    "reopened-vote",
    "reopened-command",
    "no-snapshot",
    "snapshot-at-vote",
    "snapshot-at-command",
    "wrong-vote-snapshot",
    "wrong-command-snapshot",
    "zero-different-snapshot",
    "ahead-snapshot",
    "vote-only",
    "empty",
    "wrong-policy-id",
    "outer-gap",
    "vote-sequence",
    "reordered",
    "duplicate-vote",
    "duplicate-command",
    "vote-after-command",
    "changed-state",
    "changed-effects",
    "changed-record",
    "changed-startup-policy",
    "backwards-clock",
]
REJECTIONS = {
    "vote-conflict": "core",
    "command-conflict": "7",
    "fresh-after-command": "core",
    "wrong-vote-snapshot": "5",
    "wrong-command-snapshot": "5",
    "ahead-snapshot": "5",
    "wrong-policy-id": "8",
    "outer-gap": "6",
    "vote-sequence": "8",
    "reordered": "6",
    "duplicate-vote": "core",
    "duplicate-command": "8",
    "vote-after-command": "8",
    "changed-state": "8",
    "changed-effects": "8",
    "changed-record": "8",
    "changed-startup-policy": "8",
    "backwards-clock": "8",
}


def validate(rows):
    names = [r["name"] for r in rows]
    require(names == NAMES, "exact native case order")
    for row in rows:
        require(
            set(row)
            == {
                "operation",
                "command_hex",
                "vote_replay",
                "snapshot_hex",
                "wal_hex",
                "message",
                "vote_receipt_hex",
                "clock",
                "code",
                "policy_hex",
                "receipt",
                "state_hex",
                "name",
                "status",
                "sequence",
                "initial_hex",
            },
            "diagnostic schema",
        )
        require(
            row["status"] == ("REJECT" if row["name"] in REJECTIONS else "ACCEPT"),
            "expected outcome",
        )
        require(row["code"] == REJECTIONS.get(row["name"], ""), "native error category")
        require(type(row["vote_replay"]) is bool, "replay flag")
        if row["status"] == "REJECT":
            require(
                row["receipt"] is None and row["vote_receipt_hex"] == "" and not row["vote_replay"],
                "failure has no returned receipt",
            )
        try:
            m = mixed.replay(
                bytes.fromhex(row["policy_hex"]),
                bytes.fromhex(row["initial_hex"]),
                bytes.fromhex(row["wal_hex"]),
                bytes.fromhex(row["snapshot_hex"]),
            )
            op = row["operation"]
            raw = bytes.fromhex(row["command_hex"])
            if op == "vote-retry":
                value = mixed.retry_vote(m, raw)
                if row["status"] == "ACCEPT":
                    require(
                        value["receipt_hex"] == row["vote_receipt_hex"] and row["vote_replay"],
                        "vote retry bytes",
                    )
            elif op == "retry":
                value = mixed.retry_command(m, raw)
                if row["status"] == "ACCEPT":
                    require(value == row["receipt"], "command retry fields")
            elif op == "fresh-vote":
                import native_config_admission as admission

                admission.check(
                    bytes.fromhex(row["policy_hex"]),
                    bytes.fromhex(m["state_hex"]),
                    raw,
                    dict(
                        tick=m["tick"],
                        ready=True,
                        invalidated=m["invalidated"],
                        recovery=False,
                        expected=m["sequence"] + 1,
                    ),
                )
            if row["status"] == "ACCEPT":
                require(
                    m["state_hex"] == row["state_hex"] and m["sequence"] == row["sequence"],
                    "exact recovered state/sequence",
                )
                if op == "vote":
                    value = mixed.retry_vote(m, raw)
                    require(
                        value["receipt_hex"] == row["vote_receipt_hex"] and not row["vote_replay"],
                        "original vote bytes",
                    )
                if op == "live":
                    value = mixed.retry_command(m, raw)
                    value["replay"] = False
                    require(value == row["receipt"], "original command receipt")
            matched = "ACCEPT"
        except ValueError:
            matched = "REJECT"
        require(row["status"] == matched, "computed/native outcome: " + row["name"])
    return rows


def verify_document(doc):
    require(doc["status"] == "PASS_CONFIG_COMMAND_RUNTIME_REPLAY_SUBDOMAIN", "status")
    require(doc["source_commit"] == source.SOURCE, "source commit")
    require(
        doc["source_sha256"]
        == {p: hashlib.sha256(b).hexdigest() for p, b in source.sources().items()},
        "source pins",
    )
    require(doc["harness_sha256"] == hashlib.sha256(HARNESS.encode()).hexdigest(), "harness pin")
    require(
        doc["compiler_flags"] == source.FLAGS
        and doc["unmodified_translation_units"] == source.UNITS,
        "compiler pins",
    )
    require(doc["compiler"] == "19.29.30146", "compiler version")
    require(
        all(
            doc[k] is True
            for k in [
                "native_runtime_execution",
                "native_wal_execution",
                "mixed_vote_command_recovery",
            ]
        ),
        "execution",
    )
    require(
        all(
            doc[k] is False
            for k in [
                "physical_power_loss",
                "arithmetic_execution",
                "native_export_authenticated",
                "gate_eligible",
            ]
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
