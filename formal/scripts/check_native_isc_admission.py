"""Fresh unchanged C++ ISC proposal comparisons; finite evidence, not equivalence."""

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

import generate_native_policy_wal_vectors as source
import native_isc_admission as checker
import native_policy_codec as codec
from formal_artifacts import load_json_strict, write_canonical_json
from generate_native_state_vectors import envelope
from native_admission_snapshot import decode_flat, require, state_id

ROOT = source.ROOT
FOLDER = ROOT / "formal/proposals/evidence/native-isc-admission"


def original():
    rows = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )["observed"]
    policy = codec.decode(
        bytes.fromhex(next(r for r in rows if r["name"] == "codec-ISC")["policy_hex"])
    )
    rows = load_json_strict(
        ROOT / "formal/proposals/evidence/native-admission-snapshot/cpp-cross-check.json"
    )["observed"]
    row = next(r for r in rows if r["name"] == "original-input_set")
    return (
        policy,
        decode_flat(bytes.fromhex(row["state_hex"]), 5),
        decode_flat(bytes.fromhex(row["vote_hex"]), 3),
    )


def cases():
    p, s, v = original()
    facts = dict(tick=10, expected=1, ready=True, invalidated=False, recovery=False)
    rows = []

    def add(name, edit=lambda p, s, v, r: None, rebind=False, supported=True):
        pp, ss, vv, rr = copy.deepcopy((p, s, v, facts))
        edit(pp, ss, vv, rr)
        state = envelope(5, sorted(ss.items()))
        if rebind:
            pp["snapshot"]["state_id"] = state_id(state)
        rows.append(
            dict(
                name=name,
                policy_hex=(codec.HEADER + codec.encode_value("policy", pp)).hex(),
                state_hex=state.hex(),
                vote_hex=envelope(3, sorted(vv.items())).hex(),
                facts=rr,
                supported=supported,
            )
        )

    def rebound(p, s, v, r, edit):
        body = p["snapshot"]["input_set_bodies"][0]
        edit(body)
        body_id = checker.isc.from_fields(body).content_id()
        p["snapshot"]["closed_input_set_ids"] = [body_id]
        p["candidates"][0]["body_hash"] = body_id
        v["body_hash"] = body_id

    add("original")
    add("missing-body", lambda p, s, v, r: p["snapshot"].update(input_set_bodies=[]))
    add("missing-closed", lambda p, s, v, r: p["snapshot"].update(closed_input_set_ids=[]))
    add(
        "duplicated-closed",
        lambda p, s, v, r: p["snapshot"]["closed_input_set_ids"].extend(
            p["snapshot"]["closed_input_set_ids"]
        ),
    )
    add(
        "duplicated-body",
        lambda p, s, v, r: p["snapshot"]["input_set_bodies"].extend(
            copy.deepcopy(p["snapshot"]["input_set_bodies"])
        ),
    )
    for key in [
        "arithmetic_profile_id",
        "parameter_schema_id",
        "round_config_id",
        "validator_epoch_id",
        "round_id",
        "height",
        "view",
    ]:
        add(
            "context-" + key,
            lambda p, s, v, r, k=key: rebound(
                p,
                s,
                v,
                r,
                lambda b: b["context"].update(
                    {k: 2 if k in ["height", "view"] else "sha256:" + "e" * 64}
                ),
            ),
        )
    for key in ["availability_certificate_id", "commitment_id", "domain_id", "ticket_id"]:
        add(
            "invalid-tuple-" + key,
            lambda p, s, v, r, k=key: rebound(
                p, s, v, r, lambda b: b["tuples"][0].update({k: "bad space"})
            ),
        )
        add(
            "rebound-primitive-" + key,
            lambda p, s, v, r, k=key: rebound(
                p, s, v, r, lambda b: b["tuples"][0].update({k: "sha256:" + "e" * 64})
            ),
        )
    add(
        "unbound-root",
        lambda p, s, v, r: p["snapshot"]["input_set_bodies"][0].update(
            input_root="sha256:" + "e" * 64
        ),
    )
    add(
        "rebound-root",
        lambda p, s, v, r: rebound(p, s, v, r, lambda b: b.update(input_root="sha256:" + "e" * 64)),
    )
    add(
        "invalid-root", lambda p, s, v, r: rebound(p, s, v, r, lambda b: b.update(input_root="bad"))
    )
    add("empty-tuples", lambda p, s, v, r: rebound(p, s, v, r, lambda b: b.update(tuples=[])))
    add(
        "duplicate-tuples",
        lambda p, s, v, r: rebound(
            p, s, v, r, lambda b: b["tuples"].extend(copy.deepcopy(b["tuples"]))
        ),
    )

    def two(b, reverse=False, same_ticket=False):
        row = copy.deepcopy(b["tuples"][0])
        row["commitment_id"] = "sha256:" + "e" * 64
        if not same_ticket:
            row["ticket_id"] = "ticket-z"
        b["tuples"].append(row)
        b["tuples"].sort(key=lambda x: (x["ticket_id"], x["commitment_id"]), reverse=reverse)

    add("two-tuples", lambda p, s, v, r: rebound(p, s, v, r, two))
    add(
        "same-ticket-different-commitment",
        lambda p, s, v, r: rebound(p, s, v, r, lambda b: two(b, same_ticket=True)),
    )
    add("reverse-tuples", lambda p, s, v, r: rebound(p, s, v, r, lambda b: two(b, reverse=True)))

    def extra(p, s, v, r, reverse=False, invalid=False):
        b = copy.deepcopy(p["snapshot"]["input_set_bodies"][0])
        b["input_root"] = "sha256:" + "e" * 64
        if invalid:
            b["tuples"] = []
        p["snapshot"]["input_set_bodies"].append(b)
        p["snapshot"]["input_set_bodies"].sort(
            key=lambda b: checker.isc.from_fields(b).content_id(), reverse=reverse
        )

    add("extra-unclosed-valid-body", extra)
    add("reverse-bodies", lambda p, s, v, r: extra(p, s, v, r, reverse=True))
    add("extra-unclosed-invalid-body", lambda p, s, v, r: extra(p, s, v, r, invalid=True))
    add(
        "no-finalized-config",
        lambda p, s, v, r: p["snapshot"].update(finalized_round_config_ids=[]),
    )
    add("no-proposed-config", lambda p, s, v, r: p["snapshot"].update(proposed_round_config_ids=[]))
    for key, value in [
        ("state_id", "sha256:" + "e" * 64),
        ("parameter_schema_id", "bad"),
        ("arithmetic_profile_id", "bad"),
        ("required_accumulator_proof_id", "bad"),
    ]:
        add("snapshot-" + key, lambda p, s, v, r, k=key, x=value: p["snapshot"].update({k: x}))
    add("rehashed-state-root", lambda p, s, v, r: s.update(state_root="sha256:" + "e" * 64), True)
    for key, value in [
        ("body_hash", "sha256:" + "e" * 64),
        ("context_id", "sha256:" + "e" * 64),
        ("height", 2),
        ("view", 1),
        ("action", 1),
    ]:
        add(
            "candidate-" + key, lambda p, s, v, r, k=key, x=value: p["candidates"][0].update({k: x})
        )
    add(
        "foreign-parent",
        lambda p, s, v, r: p["candidates"][0]["parents"].update(
            input_set_certificate_id="sha256:" + "e" * 64
        ),
    )
    add(
        "different-checkpoint",
        lambda p, s, v, r: p["candidates"][0]["parents"].update(
            parent_checkpoint_id="sha256:" + "e" * 64
        ),
    )
    add(
        "committee-label",
        lambda p, s, v, r: p.update(
            validator_ids=["!bad", "validator-1", "validator-2", "validator-3"]
        ),
    )
    add("committee-size", lambda p, s, v, r: p.update(validator_ids=["validator-1", "validator-2"]))
    for key, value in [
        ("kind", "APPLY"),
        ("validator_id", "other"),
        ("context_id", "sha256:" + "e" * 64),
        ("body_hash", "sha256:" + "e" * 64),
        ("durable_sequence", "2"),
    ]:
        add("vote-" + key, lambda p, s, v, r, k=key, x=value: v.update({k: x}))
    add("not-ready", lambda p, s, v, r: r.update(ready=False))
    add("recovery-not-ready", lambda p, s, v, r: r.update(ready=False, recovery=True))
    add("invalidated", lambda p, s, v, r: r.update(invalidated=True))
    add(
        "recovery-invalidated",
        lambda p, s, v, r: r.update(ready=False, recovery=True, invalidated=True),
    )
    add("deadline", lambda p, s, v, r: r.update(tick=100))
    add("before-deadline", lambda p, s, v, r: r.update(tick=99))
    add("wrong-phase", lambda p, s, v, r: s.update(phase="TICKETING_OPEN"), True)
    add(
        "nonempty-abort-graph-unsupported",
        lambda p, s, v, r: p["snapshot"].update(
            abort_requests=[dict(round_id=s["round_id"], reason_code="INCOMPLETE_INPUT")]
        ),
        supported=False,
    )
    return rows


def outcome(row):
    p, s, v = (bytes.fromhex(row[k]) for k in ["policy_hex", "state_hex", "vote_hex"])
    try:
        checker.prepare(p, s)
        startup = True
    except ValueError:
        startup = False
    try:
        checker.check(p, s, v, row["facts"])
        admitted = True
    except ValueError:
        admitted = False
    return dict(startup=startup, admitted=admitted)


HARNESS = r"""
#include <delta/core/consensus.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <iostream>
#include <string>
#include <sstream>
using namespace delta::core::consensus;
namespace pr=delta::core::protocol;
using Bytes=delta::core::canonical::Bytes;
Bytes unhex(const std::string& s){Bytes b;for(std::size_t i=0;i<s.size();i+=2)
 b.push_back(static_cast<std::byte>(std::stoul(s.substr(i,2),nullptr,16)));return b;}
int main(){std::string line;while(std::getline(std::cin,line)){
 std::istringstream in(line);std::string p,s,v;std::uint64_t tick=0,seq=0;
 bool ready=false,invalid=false,recovery=false;
 in>>p>>s>>v>>tick>>seq>>ready>>invalid>>recovery;bool startup=false,admitted=false;
 try{auto policy=delta::runtime::parse_vote_policy_v1(unhex(p));
 auto state=pr::parse_round_state(unhex(s));
 validate_vote_admission_policy(policy,state);startup=true;
 auto vote=pr::parse_vote(unhex(v));
 static_cast<void>(validate_vote_admission(policy,state,VoteAdmissionState{tick,ready,invalid},vote,seq,
 recovery?VoteAdmissionMode::recovery:VoteAdmissionMode::live));admitted=true;
 }catch(const std::exception&){}
 std::cout<<"{\"startup\":"<<(startup?"true":"false")<<",\"admitted\":"<<(admitted?"true":"false")<<"}\n";
}}
"""


def validate(rows):
    originals = cases()
    require(len(rows) == len(originals), "case count")
    for row, original in zip(rows, originals, strict=True):
        require(all(row[k] == v for k, v in original.items()), "exact source case")
        computed = outcome(original)
        require(row["computed"] == computed, "recomputed admission")
        if original["supported"]:
            require(row["native"] == computed, "native disagreement " + row["name"])
        else:
            require(computed == dict(startup=False, admitted=False), "unsupported fails closed")
    return rows


def cross_check(vcvars):
    build = ROOT / "formal/build/native-isc-admission"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    blobs = source.sources()
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
        f'@echo off\ncall "{vcvars}" >nul\nif errorlevel 1 exit /b 1\n'
        f"cl {source.FLAGS} /Iinclude harness.cpp "
    )
    cmd += (
        " ".join(Path(p).name for p in source.UNITS)
        + " /Fe:isc-admission.exe\nexit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    proc = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (proc.stdout + proc.stderr).decode("utf-8")
    (FOLDER / "compile.txt").write_text(
        "\n".join(x.rstrip() for x in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    require(proc.returncode == 0, "native compile")
    rows = cases()
    lines = []
    for row in rows:
        r = row["facts"]
        lines.append(
            " ".join(
                [
                    row["policy_hex"],
                    row["state_hex"],
                    row["vote_hex"],
                    str(r["tick"]),
                    str(r["expected"]),
                    str(int(r["ready"])),
                    str(int(r["invalidated"])),
                    str(int(r["recovery"])),
                ]
            )
        )
    raw = subprocess.check_output(
        [str(build / "isc-admission.exe")], input=("\n".join(lines) + "\n").encode(), timeout=60
    )
    observations = [json.loads(line) for line in raw.splitlines()]
    rows = validate(
        [
            dict(row, computed=outcome(row), native=n)
            for row, n in zip(rows, observations, strict=True)
        ]
    )
    (FOLDER / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    doc = dict(
        status="PASS_FINITE_ISC_PROPOSAL_ADMISSION",
        source_commit=source.SOURCE,
        source_sha256={p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        compiler=re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)[1],
        compiler_flags=source.FLAGS,
        unmodified_translation_units=source.UNITS,
        harness_sha256=hashlib.sha256(HARNESS.encode()).hexdigest(),
        observed=rows,
        native_admission_execution=True,
        runtime_wal_execution=False,
        general_native_equivalence=False,
        native_export_authenticated=False,
        gate_eligible=False,
    )
    write_canonical_json(FOLDER / "cpp-cross-check.json", doc)
    return doc


def verify_document(doc):
    require(
        doc["status"] == "PASS_FINITE_ISC_PROPOSAL_ADMISSION"
        and doc["source_commit"] == source.SOURCE,
        "scope/source",
    )
    require(
        doc["source_sha256"]
        == {p: hashlib.sha256(b).hexdigest() for p, b in source.sources().items()},
        "source hashes",
    )
    require(doc["harness_sha256"] == hashlib.sha256(HARNESS.encode()).hexdigest(), "harness")
    require(
        doc["compiler"] == "19.29.30146"
        and doc["compiler_flags"] == source.FLAGS
        and doc["unmodified_translation_units"] == source.UNITS,
        "build",
    )
    require(
        doc["native_admission_execution"] is True
        and all(
            doc[k] is False
            for k in [
                "runtime_wal_execution",
                "general_native_equivalence",
                "native_export_authenticated",
                "gate_eligible",
            ]
        ),
        "claims",
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
