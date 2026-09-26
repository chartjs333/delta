"""Fresh native CONFIG/ISC/command WAL checks; strict policy subdomain, not full recovery."""

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from pathlib import Path

import check_native_config_replay as base
import generate_native_policy_wal_vectors as source
import native_config_replay as mixed
from formal_artifacts import load_json_strict, write_canonical_json
from native_admission_snapshot import require

ROOT = source.ROOT

FOLDER = ROOT / "formal/proposals/evidence/native-proposal-replay"
HARNESS = (
    base.HARNESS.replace(
        "auto f=full(VoteAction::round_config);auto p=dir",
        "auto f=full(VoteAction::input_set);"
        "auto other=full(VoteAction::round_config,f.state);"
        "f.policy.candidates.insert(f.policy.candidates.begin(),other.candidate);auto p=dir",
    )
    .replace(
        'command("FINALIZE_ROUND_CONFIG",11U,"config")',
        'command("FINALIZE_INPUT_FREEZE",11U,"freeze-after-isc")',
    )
    .replace("id('a'),kind,1U", "id('c'),kind,1U")
)


def cross_check(vcvars):
    blobs = source.sources()
    build = ROOT / "formal/build/native-proposal-replay"
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
        + " /Fe:proposal-replay.exe\nexit /b %errorlevel%\n"
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
        [str(build / "proposal-replay.exe"), str(run)], cwd=build, timeout=180
    )
    (build / "draft-output.jsonl").write_bytes(raw)
    rows = validate(
        [json.loads(line, object_pairs_hook=source.admission.unique) for line in raw.splitlines()]
    )
    (FOLDER / "harness.cpp").write_text(HARNESS, encoding="utf-8", newline="\n")
    doc = dict(
        status="PASS_CONFIG_ISC_COMMAND_RUNTIME_REPLAY_SUBDOMAIN",
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
    "live-freeze-after-isc",
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
    # Repeated freeze fails its AVAILABLE guard before the cache-duplicate check.
    "duplicate-command": "core",
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
            m = mixed.replay_proposals(
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
                import native_proposal_admission as admission

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
    require(doc["status"] == "PASS_CONFIG_ISC_COMMAND_RUNTIME_REPLAY_SUBDOMAIN", "status")
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
