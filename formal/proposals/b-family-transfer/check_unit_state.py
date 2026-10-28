"""T047/T053: qualify exact unit/config/policy/current source composition.

This is not the complete producing-history/public-state relation or Formal GO.
Fresh transitive builds, exact source pins and kernel byte cases are mandatory.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-unit-state-qualified"
OUT = ROOT / "formal/proposals/evidence/profile-unit-state"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_digest(path):
    return digest(path.read_bytes().replace(b"\r\n", b"\n"))


def main():
    source, objects = BUILD / "source", BUILD / "objects"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").unlink(missing_ok=True)
    pins, order, checks = {}, [], []

    def visit(name):
        if name in order or name in {"Init", "Std"}:
            return
        if name.startswith("DeltaReduce."):
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        elif name in {"SourcePolicy", "SourceVote"}:
            path = ROOT / "formal/proposals/isc-source-generation" / (name + ".lean")
        elif re.fullmatch(r"Profile[A-Za-z]+", name):
            path = Path(__file__).with_name(name + ".lean")
        else:
            raise RuntimeError("Unexpected proof dependency " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        pins[path.relative_to(ROOT).as_posix()] = digest(raw)
        if re.search(
            r"\b(sorry|axiom)\b", re.sub(r"/-.*?-/|--[^\n]*", "", raw.decode(), flags=re.S)
        ):
            raise RuntimeError("Unproved source " + name)
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.M):
            visit(child)
        target = source / (name.replace(".", "/") + ".lean")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        order.append(name)

    visit("ProfileUnitCurrent")
    visit("ProfileVoteRecord")
    for path in (ROOT / "formal/reference").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".json"}:
            pins[path.relative_to(ROOT).as_posix()] = source_digest(path)
    for path in (
        Path(__file__),
        ROOT / "formal/proposals/profile-unit-state-composition.md",
        ROOT / "formal/proposals/profile-genesis-source-contract.md",
        ROOT / "formal/proposals/arithmetic-unit-source-binding-v1.md",
        ROOT / "formal/scripts/native_source_artifacts.py",
        ROOT / "formal/reference/profile_source/README.md",
    ):
        pins[path.relative_to(ROOT).as_posix()] = source_digest(path)

    def run(command, name, cwd=ROOT, env=None):
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf8",
            timeout=900,
            check=False,
        )
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, "utf8", newline="\n")
        checks.append(dict(log=name, sha256=digest(log.encode()), exit_code=result.returncode))
        if result.returncode or "sorryAx" in log:
            raise RuntimeError(name + ": " + log[-3500:])
        print("Checked " + name, flush=True)
        return log

    version = run([str(LEAN), "--version"], "lean-version.txt")
    if "4.32.1" not in version:
        raise RuntimeError("Wrong pinned Lean")
    env = dict(os.environ, LEAN_PATH=str(objects), PYTHONUTF8="1")
    for name in order:
        out = objects / (name.replace(".", "/") + ".olean")
        out.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(out), name.replace(".", "/") + ".lean"],
            "module-" + name + ".txt",
            source,
            env,
        )
    declarations = {}
    for module in ("UnitState", "UnitCurrent", "SelectedVote"):
        raw = Path(__file__).with_name("Profile" + module + ".lean").read_text("utf8")
        declarations[module] = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    vote_source = Path(__file__).with_name("ProfileVoteRecord.lean").read_text("utf8")
    old_vote, unit_vote = vote_source.split("namespace Units\n", 1)
    for namespace, raw in (("VoteRecord", old_vote), ("VoteRecord.Units", unit_vote)):
        declarations[namespace] = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    required = {
        "UnitState": {
            "headerSource",
            "headerComplete",
            "profileSource",
            "profileComplete",
            "appliesSource",
            "appliesComplete",
            "completeProfileInventory",
            "collectionsSource",
            "collectionsComplete",
            "boundSource",
            "complete",
            "allOriginalHeaders",
            "originalParentUnits",
            "abortPreservesDownstream",
            "everyOriginalProfile",
        },
        "UnitCurrent": {
            "boundSource",
            "boundComplete",
            "selectedFromOriginalConfiguration",
            "unchangedOriginalUnits",
            "parentAndValues",
            "actualCurrentHashes",
            "runSound",
            "historyComplete",
            "everyOriginal",
            "unitsAlongCompleteHistory",
            "exactPointerScan",
            "journalSource",
            "fullOriginalInventory",
            "journalComplete",
            "noRecordOrInputErasure",
            "nativeScanAgrees",
            "incompleteRejected",
            "originSource",
            "originalGenesisToCurrentUnits",
        },
        "SelectedVote": {
            "unitChecked",
            "unitComplete",
            "unitOriginalCandidate",
            "unitOriginalIdentity",
            "unitOriginalPhysicalSequence",
            "unitArithmeticRefusal",
            "unitRecoveryOnlyReadiness",
            "unitBoundSource",
            "unitOriginalVoteBytes",
        },
        "VoteRecord.Units": {
            "boundSource",
            "complete",
            "originalReceipt",
            "cannotRelabelPolicy",
            "currentArithmeticGuard",
            "fromOriginal",
            "allOriginalBytes",
        },
    }
    if any(not required[name] <= set(declarations[name]) for name in required):
        raise RuntimeError("Missing composition obligation")
    qualified = [
        "DeltaReduce.ProfileSource." + namespace + "." + name
        for namespace, names in declarations.items()
        for name in names
    ]
    audit = "import ProfileUnitCurrent\nimport ProfileVoteRecord\n" + "".join(
        "#print axioms " + name + "\n" for name in qualified
    )
    (source / "Audit.lean").write_text(audit, "utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", source, env)
    if any(name not in log for name in qualified):
        raise RuntimeError("Incomplete axiom audit")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    from formal.reference.profile_source.unit_state_vectors import generate

    vectors, originals = generate()
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", "utf8", newline="\n"
    )
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)"
    assertions = re.findall(pattern, vectors, flags=re.MULTILINE)
    if len(assertions) != 10:
        raise RuntimeError("Incomplete kernel source vector inventory")
    definitions = re.sub(pattern, "", vectors, flags=re.MULTILINE)
    (source / "Definitions.lean").write_text(definitions, "utf8", newline="\n")
    run(
        [str(LEAN), "-o", str(objects / "Definitions.olean"), "Definitions.lean"],
        "definitions.txt",
        source,
        env,
    )
    for i, assertion in enumerate(assertions):
        case = (
            "import Definitions\nopen DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes\n"
            "set_option maxRecDepth 30000\nset_option maxHeartbeats 16000000\n"
            "namespace UnitStateVectors\n" + assertion + "end UnitStateVectors\n"
        )
        name = f"Case{i}.lean"
        (source / name).write_text(case, "utf8", newline="\n")
        run([str(LEAN), name], f"kernel-case-{i}.txt", source, env)
    from formal.reference.profile_source import configuration_route as route
    from formal.reference.profile_source.installed_state_vectors import generate as installed
    from formal.reference.profile_source.vote_record_vectors import generate as vote_records

    vote_pins = {}
    for generation in (route.LEGACY, route.UNITS):
        for prefix, generator in (("Installed", installed), ("VoteRecords", vote_records)):
            name = prefix + generation.name
            generated, byte_evidence = generator(generation=generation)
            raw_evidence = json.dumps(byte_evidence, indent=2) + "\n"
            (source / (name + ".lean")).write_text(generated, "utf8", newline="\n")
            (OUT / (name + "-originals.json")).write_text(raw_evidence, "utf8", newline="\n")
            vote_pins[name] = dict(
                lean_sha256=digest(generated.encode()),
                originals_sha256=digest(raw_evidence.encode()),
            )
            run([str(LEAN), name + ".lean"], name + "-kernel.txt", source, env)
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "formal.reference.profile_source.test_unit_state",
            "formal.reference.profile_source.test_arithmetic_units",
            "formal.reference.profile_source.test_genesis",
        ],
        "reference-tests.txt",
        env=env,
    )
    paths = [
        "formal/reference/profile_source/" + name + ".py"
        for name in (
            "unit_state",
            "unit_state_vectors",
            "test_unit_state",
            "installed_state_vectors",
            "vote_record_vectors",
        )
    ]
    paths.append("formal/proposals/b-family-transfer/check_unit_state.py")
    run([sys.executable, "-m", "ruff", "check", *paths], "lint.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "format.txt")
    if pins != {path: source_digest(ROOT / path) for path in pins}:
        raise RuntimeError("Sources changed during qualification")
    data = dict(
        task_ids=["T047", "T053"],
        scope_revision=3,
        assignment_id="2fd81f70-bb27-4872-a09c-8a712c0e2311",
        result="UNIT_STATE_SOURCE_COMPOSITION_CHECKED",
        R23="OPEN",
        formal="NO_GO",
        sources=pins,
        checks=checks,
        audited_declarations=declarations,
        generated_audit_sha256=digest(audit.encode()),
        generated_vectors_sha256=digest(vectors.encode()),
        vote_vectors=vote_pins,
        originals_sha256=digest((OUT / "originals.json").read_bytes()),
        lean=version.strip(),
        lean_binary_sha256=digest(LEAN.read_bytes()),
        source_hash_rule="Git LF-normalized text; protocol bytes unchanged",
        residual="Complete producing history, original ISC/clock/seed associations, certified "
        "import floor and full public-state initial/incomplete/ABORT correspondence "
        "remain open and unreviewed.",
        evidence_kind="SYNTHETIC_STATIC_SOURCE_NOT_LAWFUL_PRODUCER_OR_RECOVERY",
    )
    receipt = json.dumps(data, sort_keys=True, indent=2) + "\n"
    (OUT / "receipt.json").write_text(receipt, "utf8", newline="\n")
    print(
        json.dumps(dict(result=data["result"], receipt_sha256=digest(receipt.encode()), R23="OPEN"))
    )


if __name__ == "__main__":
    main()
