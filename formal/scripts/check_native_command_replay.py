"""Fresh, isolated, unchanged native runtime command-recovery counterchecks."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

import generate_native_policy_wal_vectors as source
from formal_artifacts import load_json_strict, write_canonical_json
from native_admission_snapshot import require
from native_command_replay import replay, retry

ROOT = source.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-command-replay"
HARNESS = (
    '\n#include "vote_fixture.hpp"\n#include "wal.hpp"\n#i'
    "nclude <delta/core/transition.hpp>\n#include <delta"
    "/runtime/runtime.hpp>\n#include <delta/runtime/vote"
    "_codec.hpp>\n#include <filesystem>\n#include <fstrea"
    "m>\n#include <iomanip>\n#include <iostream>\nusing na"
    "mespace delta::test::vote_fixture;\nusing namespace"
    " delta::core::consensus;\nnamespace rt=delta::runti"
    "me; namespace dt=rt::detail;\nnamespace ca=delta::c"
    "ore::canonical; namespace pr=delta::core::protocol"
    ";\nusing Bytes=ca::Bytes;\nstd::filesystem::path roo"
    "t;\nvoid q(const std::string& s){std::cout<<std::qu"
    "oted(s);}\nstd::string hex(const Bytes& b){constexp"
    'r char d[]="0123456789abcdef";std::string s;\n for('
    "auto c:b){auto n=std::to_integer<unsigned>(c);s.pu"
    "sh_back(d[n>>4U]);s.push_back(d[n&15U]);}\n return "
    "s;}\nBytes file(const std::filesystem::path& p){if("
    "!std::filesystem::exists(p))return {};\n std::ifstr"
    "eam in(p,std::ios::binary);Bytes b;char c;\n while("
    "in.get(c))b.push_back(static_cast<std::byte>(stati"
    "c_cast<unsigned char>(c)));\n if(!in.eof())throw st"
    'd::runtime_error("harness read");return b;}\nstd::f'
    "ilesystem::path dir(const std::string& n){auto p=r"
    "oot/n;\n if(std::filesystem::exists(p))throw std::r"
    'untime_error("not fresh");\n std::filesystem::creat'
    "e_directories(p);return p;}\npr::Command command(co"
    "nst std::string& kind,std::uint64_t tick,const std"
    "::string& request,\n std::uint64_t view=0U){return "
    '{"validator-1",id(\'a\'),kind,1U,tick,request,"round'
    '-vote-fixture",view};}\nrt::Config config(const std'
    "::filesystem::path& p,const Fixture& f,bool policy"
    "){\n rt::Config c;c.directory=p;c.initial_state_byt"
    "es=pr::encode(f.state);\n if(policy)c.vote_policy=r"
    "t::parse_vote_policy_v1(rt::encode_vote_policy_v1("
    "f.policy));return c;}\nvoid receipt(const rt::Submi"
    'tReceipt& r){\n std::cout<<"{\\"state_hex\\":";q(hex('
    'r.next_state_bytes));std::cout<<",\\"effects_hex\\":'
    '";\n q(hex(r.effect_batch_bytes));std::cout<<",\\"re'
    'cord_hex\\":";q(hex(r.wal_record_bytes));\n std::cou'
    't<<",\\"next_id\\":";q(r.next_state_id);std::cout<<"'
    ',\\"effects_id\\":";q(r.effect_batch_id);\n std::cout'
    '<<",\\"record_id\\":";q(r.wal_record_id);std::cout<<'
    '",\\"sequence\\":"<<r.journal_sequence;\n std::cout<<'
    '",\\"replay\\":"<<(r.replay?"true":"false")<<\'}\';}\ns'
    'truct Result {std::string status="ACCEPT",code="",'
    'message="";Bytes state;\n std::uint64_t seq=0U;std:'
    ":optional<rt::SubmitReceipt> receipt;};\ntemplate<c"
    "lass F> Result capture(F f){Result r;try{f(r);}\n c"
    'atch(const rt::RuntimeError& e){r.status="REJECT";'
    "r.code=std::to_string(static_cast<int>(e.code()));"
    "r.message=e.what();}\n catch(const std::exception& "
    'e){r.status="REJECT";r.code="core";r.message=e.wha'
    "t();}return r;}\nvoid emit(const std::string& name,"
    "const std::string& operation,const std::filesystem"
    "::path& p,\n const Fixture& f,bool policy,const Byt"
    'es& input,const Result& r){\n std::cout<<"{\\"name\\"'
    ':";q(name);std::cout<<",\\"operation\\":";q(operatio'
    'n);\n std::cout<<",\\"status\\":";q(r.status);std::co'
    'ut<<",\\"code\\":";q(r.code);\n std::cout<<",\\"messag'
    'e\\":";q(r.message);std::cout<<",\\"initial_hex\\":";'
    'q(hex(pr::encode(f.state)));\n std::cout<<",\\"polic'
    'y_hex\\":";q(policy?hex(rt::encode_vote_policy_v1(f'
    '.policy)):"");\n std::cout<<",\\"clock\\":";if(policy'
    ")std::cout<<f.policy.initial_logical_tick;else std"
    '::cout<<"null";\n std::cout<<",\\"command_hex\\":";q('
    'hex(input));std::cout<<",\\"wal_hex\\":";q(hex(file('
    'p/"runtime.wal")));\n std::cout<<",\\"snapshot_hex\\"'
    ':";q(hex(file(p/"runtime.snapshot")));\n std::cout<'
    '<",\\"state_hex\\":";q(hex(r.state));std::cout<<",\\"'
    'sequence\\":"<<r.seq;\n std::cout<<",\\"receipt\\":";i'
    'f(r.receipt)receipt(*r.receipt);else std::cout<<"n'
    'ull";std::cout<<"}\\n";}\nvoid openCase(const std::s'
    "tring& name,const Fixture& f,bool policy,\n const s"
    "td::vector<dt::JournalEntry>& entries,std::optiona"
    "l<dt::Snapshot> snap={}){\n auto p=dir(name);{dt::W"
    'al wal(p/"runtime.wal");for(const auto& e:entries)'
    "wal.append_and_sync(e,false);\n if(snap)wal.write_s"
    'napshot(p/"runtime.snapshot",*snap);}\n auto r=capt'
    "ure([&](auto& o){rt::Runtime runtime(config(p,f,po"
    "licy));\n o.state=runtime.state_bytes();o.seq=runti"
    'me.journal_sequence();});emit(name,"recover",p,f,p'
    "olicy,{},r);}\nint main(int argc,char** argv){if(ar"
    'gc!=2)throw std::runtime_error("isolated directory'
    ' required");\n root=argv[1];auto f=full(VoteAction:'
    ':input_set);auto p=dir("live");\n auto c0=command("'
    'FINALIZE_INPUT_FREEZE",11U,"freeze");auto b0=pr::e'
    'ncode(c0);\n auto c1=command("ADVANCE_VIEW",12U,"vi'
    'ew",1U);\n auto c2=command("CERTIFY_ABORT",13U,"abo'
    'rt",1U);\n Bytes middle;{rt::Runtime runtime(config'
    "(p,f,true));\n for(const auto& c:{c0,c1,c2}){auto b"
    "=pr::encode(c);auto r=capture([&](auto& o){\n o.rec"
    "eipt=runtime.submit(b);o.state=runtime.state_bytes"
    "();o.seq=runtime.journal_sequence();});\n if(c.requ"
    'est_id=="view"){runtime.snapshot();middle=runtime.'
    'state_bytes();}\n emit("live-"+c.request_id,"live",'
    "p,f,true,b,r);}\n auto r=capture([&](auto& o){o.rec"
    "eipt=runtime.submit(b0);o.state=runtime.state_byte"
    's();o.seq=runtime.journal_sequence();});\n emit("hi'
    'storical-retry","retry",p,f,true,b0,r);\n auto wron'
    "g=c0;wrong.body_hash=id('b');auto b=pr::encode(wro"
    "ng);\n r=capture([&](auto& o){o.receipt=runtime.sub"
    'mit(b);});emit("request-conflict","retry",p,f,true'
    ',b,r);\n auto old=command("ADVANCE_VIEW",10U,"old",'
    "2U);b=pr::encode(old);\n r=capture([&](auto& o){o.r"
    'eceipt=runtime.submit(b);});emit("fresh-old-clock"'
    ',"fresh",p,f,true,b,r);}\n {rt::Runtime runtime(con'
    "fig(p,f,true));auto r=capture([&](auto& o){o.recei"
    "pt=runtime.submit(b0);\n o.state=runtime.state_byte"
    's();o.seq=runtime.journal_sequence();});emit("reop'
    'ened-retry","retry",p,f,true,b0,r);}\n std::vector<'
    'dt::JournalEntry> entries;{dt::Wal wal(p/"runtime.'
    'wal");entries=wal.recover().entries;}\n openCase("n'
    'o-snapshot",f,true,entries);openCase("matching-mid'
    'dle",f,true,entries,dt::Snapshot{2U,middle});\n ope'
    'nCase("wrong-middle",f,true,entries,dt::Snapshot{2'
    'U,pr::encode(f.state)});\n openCase("ahead-snapshot'
    '",f,true,entries,dt::Snapshot{4U,middle});\n openCa'
    'se("zero-different-snapshot",f,true,entries,dt::Sn'
    'apshot{0U,middle});\n openCase("zero-empty-journal"'
    ",f,true,{},dt::Snapshot{0U,middle});\n for(int k=0;"
    "k<3;++k){auto changed=entries;if(k==0)changed[1].n"
    "ext_state_bytes=entries[0].next_state_bytes;\n if(k"
    "==1)changed[1].effect_batch_bytes.clear();if(k==2)"
    'changed[1].wal_record_bytes.clear();\n openCase("ch'
    'anged-output-"+std::to_string(k),f,true,changed);}'
    "\n auto changed=entries;std::swap(changed[0],change"
    'd[1]);openCase("reordered",f,true,changed);\n chang'
    'ed=entries;changed[1].sequence=3U;openCase("sequen'
    'ce-gap",f,true,changed);\n auto low=c0;low.logical_'
    "tick=9U;auto result=delta::core::transition::apply"
    "(pr::encode(f.state),pr::encode(low));\n std::vecto"
    "r<dt::JournalEntry> old{{1U,dt::JournalKind::trans"
    "ition,pr::encode(low),result.next_state_bytes,\n re"
    "sult.effect_batch_bytes,result.wal_record_bytes}};"
    '\n openCase("old-clock-policy",f,true,old);openCase'
    '("old-clock-submit-only",f,false,old);\n auto confi'
    "gFixture=full(VoteAction::round_config);\n auto cc="
    'command("FINALIZE_ROUND_CONFIG",11U,"same");auto c'
    "b=pr::encode(cc);\n auto cr=delta::core::transition"
    "::apply(pr::encode(configFixture.state),cb);\n std:"
    ":vector<dt::JournalEntry> dup{{1U,dt::JournalKind:"
    ":transition,cb,cr.next_state_bytes,cr.effect_batch"
    "_bytes,cr.wal_record_bytes},\n {2U,dt::JournalKind:"
    ":transition,cb,cr.next_state_bytes,cr.effect_batch"
    '_bytes,cr.wal_record_bytes}};\n openCase("duplicate'
    '-request",configFixture,false,dup);\n openCase("emp'
    'ty",f,true,{});\n}\n'
)

NAMES = [
    "live-freeze",
    "live-view",
    "live-abort",
    "historical-retry",
    "request-conflict",
    "fresh-old-clock",
    "reopened-retry",
    "no-snapshot",
    "matching-middle",
    "wrong-middle",
    "ahead-snapshot",
    "zero-different-snapshot",
    "zero-empty-journal",
    "changed-output-0",
    "changed-output-1",
    "changed-output-2",
    "reordered",
    "sequence-gap",
    "old-clock-policy",
    "old-clock-submit-only",
    "duplicate-request",
    "empty",
]

REJECTIONS = {
    "request-conflict": "7",
    "fresh-old-clock": "7",
    "wrong-middle": "5",
    "ahead-snapshot": "5",
    "changed-output-0": "8",
    "changed-output-1": "4",
    "changed-output-2": "4",
    "reordered": "6",
    "sequence-gap": "6",
    "old-clock-policy": "8",
    "duplicate-request": "8",
}


def validate(rows):
    require([r["name"] for r in rows] == NAMES, "complete native command case order")
    for row in rows:
        require(
            set(row)
            == {
                "name",
                "operation",
                "status",
                "code",
                "message",
                "initial_hex",
                "policy_hex",
                "clock",
                "command_hex",
                "wal_hex",
                "snapshot_hex",
                "state_hex",
                "sequence",
                "receipt",
            },
            "diagnostic fields",
        )
        require(
            row["status"] == ("REJECT" if row["name"] in REJECTIONS else "ACCEPT"),
            "native case outcome",
        )
        require(row["code"] == REJECTIONS.get(row["name"], ""), "native error category")
        require(row["operation"] in {"live", "retry", "fresh", "recover"}, "operation")
        require(
            type(row["sequence"]) is int and 0 <= row["sequence"] < 2**64, "sequence type/bound"
        )
        try:
            m = replay(
                bytes.fromhex(row["initial_hex"]),
                bytes.fromhex(row["wal_hex"]),
                bytes.fromhex(row["snapshot_hex"]),
                row["clock"],
            )
            expected = None
            if row["operation"] == "retry":
                expected = retry(m, bytes.fromhex(row["command_hex"]))
            elif row["operation"] == "fresh":
                from generate_native_state_vectors import decode_command

                c = decode_command(bytes.fromhex(row["command_hex"]))
                require(row["clock"] is None or int(c["logical_tick"]) >= m["tick"], "fresh clock")
                raise ValueError("unmodeled fresh result")
            elif row["operation"] == "live":
                expected = {**retry(m, bytes.fromhex(row["command_hex"])), "replay": False}
        except ValueError:
            require(row["status"] == "REJECT", "native accepted rejected replay")
            require(
                row["receipt"] is None and row["state_hex"] == "" and row["sequence"] == 0,
                "rejected output",
            )
            continue
        require(row["status"] == "ACCEPT", "native rejected computed replay")
        require(
            row["state_hex"] == m["state_hex"] and row["sequence"] == m["sequence"],
            "final state/sequence",
        )
        require(row["receipt"] == expected, "exact original receipt")
    return rows


def cross_check(vcvars):
    blobs = source.sources()
    build = ROOT / "formal/build/native-command-replay"
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
        + " /Fe:command-replay.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    result = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (result.stdout + result.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(log.splitlines()) + "\n", encoding="utf-8", newline="\n"
    )
    require(result.returncode == 0, "native compile; see log")
    run = (build / ("run-" + uuid.uuid4().hex)).resolve()
    require(build.resolve() in run.parents, "fresh isolated path")
    run.mkdir()
    raw = subprocess.check_output(
        [str(build / "command-replay.exe"), str(run)], cwd=build, timeout=180
    )
    (build / "draft-output.jsonl").write_bytes(raw)
    rows = validate(
        [json.loads(line, object_pairs_hook=source.admission.unique) for line in raw.splitlines()]
    )
    (FOLDER / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    doc = dict(
        status="PASS_COMMAND_RUNTIME_REPLAY_NOT_MIXED_RECOVERY",
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
        mixed_vote_command_recovery=False,
        gate_eligible=False,
    )
    write_canonical_json(FOLDER / "cpp-cross-check.json", doc)
    return doc


def verify_document(doc):
    require(doc["status"] == "PASS_COMMAND_RUNTIME_REPLAY_NOT_MIXED_RECOVERY", "status")
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
        "build pins",
    )
    require(
        doc["compiler"] == "19.29.30146"
        and doc["native_runtime_execution"] is True
        and doc["native_wal_execution"] is True,
        "execution scope",
    )
    require(
        all(
            doc[k] is False
            for k in [
                "arithmetic_execution",
                "native_export_authenticated",
                "mixed_vote_command_recovery",
                "gate_eligible",
                "physical_power_loss",
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
