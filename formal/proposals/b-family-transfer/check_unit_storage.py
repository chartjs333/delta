"""T047/T053: unit-bearing EC state joined to the original companion and source cut.

This receipt is not complete producer/public refinement or recovery qualification.
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
BUILD = ROOT / "formal/build/profile-unit-storage"
OUT = ROOT / "formal/proposals/evidence/profile-unit-storage"
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

    visit("ProfileUnitStorage")
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
        try:
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
        except subprocess.TimeoutExpired as exc:
            (OUT / name).write_text("TIMEOUT 900s\n" + str(exc), "utf8", newline="\n")
            raise
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
    raw = Path(__file__).with_name("ProfileUnitStorage.lean").read_text("utf8")
    declarations = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    required = {
        "checkedStep",
        "originalFrameUnique",
        "noPrefixErasure",
        "storageAndSourceJoined",
        "completeUnitsRetained",
        "transactionNoRelabel",
        "originalWalPreserved",
    }
    if not required <= set(declarations):
        raise RuntimeError("Missing required declaration")
    audit = (
        "import ProfileUnitStorage\n"
        + "\n".join(
            "#print axioms DeltaReduce.ProfileSource.UnitStorage." + name for name in declarations
        )
        + "\n"
    )
    (source / "Audit.lean").write_text(audit, "utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", source, env)
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    from formal.reference.profile_source.unit_storage_vectors import generate

    generated, originals = generate()
    original_json = json.dumps(originals, indent=2) + "\n"
    (source / "UnitStorageVector.lean").write_text(generated, "utf8", newline="\n")
    (OUT / "originals.json").write_text(original_json, "utf8", newline="\n")
    vector_pins = dict(
        lean_sha256=digest(generated.encode()), originals_sha256=digest(original_json.encode())
    )
    run([str(LEAN), "UnitStorageVector.lean"], "whole-storage-kernel.txt", source, env)
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/profile_source",
            "-t",
            ".",
        ],
        "reference-tests.txt",
        env=env,
    )
    paths = [
        "formal/reference/profile_source/unit_storage_vectors.py",
        "formal/reference/profile_source/test_ec_durability.py",
        "formal/proposals/b-family-transfer/check_unit_storage.py",
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "lint.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "format.txt")
    if pins != {path: source_digest(ROOT / path) for path in pins}:
        raise RuntimeError("Sources changed during qualification")
    data = dict(
        task_ids=["T047", "T053"],
        scope_revision=3,
        assignment_id="2fd81f70-bb27-4872-a09c-8a712c0e2311",
        result="UNIT_STORAGE_SOURCE_COMPOSITION_CHECKED",
        R23="OPEN",
        formal="NO_GO",
        sources=pins,
        checks=checks,
        audited_declarations=declarations,
        generated_audit_sha256=digest(audit.encode()),
        vectors=vector_pins,
        lean=version.strip(),
        lean_binary_sha256=digest(LEAN.read_bytes()),
        source_hash_rule="Git LF-normalized text; protocol bytes unchanged",
        residual="Complete producing history, original clock/seed/source associations, certified "
        "import floor and full public-state initial/incomplete/ABORT composition remain open.",
        evidence_kind="SYNTHETIC_COMPONENT_NOT_LAWFUL_PRODUCER_OR_RECOVERY",
    )
    receipt = json.dumps(data, sort_keys=True, indent=2) + "\n"
    (OUT / "receipt.json").write_text(receipt, "utf8", newline="\n")
    print(
        json.dumps(dict(result=data["result"], receipt_sha256=digest(receipt.encode()), R23="OPEN"))
    )


if __name__ == "__main__":
    main()
