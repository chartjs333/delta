"""T047/T053: source-bound genesis/U qualification, not whole R2.3 or Formal GO."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-genesis"
OUT = ROOT / "formal/proposals/evidence/profile-genesis"
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

    visit("ProfileGenesis")
    # Pin the full repository reference import surface, including fixture code
    # and package initializers. This is source applicability, not source trust.
    for path in (ROOT / "formal/reference").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".json"}:
            pins[path.relative_to(ROOT).as_posix()] = source_digest(path)
    for path in (
        Path(__file__),
        ROOT / "formal/proposals/profile-genesis-source-contract.md",
        ROOT / "formal/scripts/native_source_artifacts.py",
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
            timeout=600,
            check=False,
        )
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, "utf8", newline="\n")
        checks.append(dict(log=name, sha256=digest(log.encode()), exit_code=result.returncode))
        if result.returncode:
            raise RuntimeError(name + ": " + log[-3500:])
        return log

    version = run([str(LEAN), "--version"], "lean-version.txt")
    if "4.32.1" not in version:
        raise RuntimeError("Wrong pinned Lean")
    env = dict(os.environ, LEAN_PATH=str(objects))
    for name in order:
        out = objects / (name.replace(".", "/") + ".olean")
        out.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(out), name.replace(".", "/") + ".lean"],
            "module-" + name + ".txt",
            source,
            env,
        )
    raw = Path(__file__).with_name("ProfileGenesis.lean").read_text("utf8")
    declarations = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    required = {
        "complete",
        "boundSource",
        "originalCoordinateSpellings",
        "fullCoordinateCounts",
        "nativeValueBounds",
        "existingHashPreimages",
        "noInventedCertificate",
        "originalConfigurationAndUnits",
        "independentlyBoundOrigin",
    }
    if not required <= set(declarations):
        raise RuntimeError("Missing genesis source obligation")
    audit = "import ProfileGenesis\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.Genesis." + name + "\n" for name in declarations
    )
    (source / "Audit.lean").write_text(audit, "utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", source, env)
    if any("DeltaReduce.ProfileSource.Genesis." + name not in log for name in declarations):
        raise RuntimeError("Incomplete axiom audit")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    from formal.reference.profile_source.genesis_vectors import generate

    vectors, originals = generate()
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", "utf8", newline="\n"
    )
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)"
    assertions = re.findall(pattern, vectors, flags=re.MULTILINE)
    if len(assertions) != 5:
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
            "set_option maxRecDepth 30000\nset_option maxHeartbeats 8000000\n"
            "namespace GenesisVectors\n" + assertion + "end GenesisVectors\n"
        )
        name = f"Case{i}.lean"
        (source / name).write_text(case, "utf8", newline="\n")
        run([str(LEAN), name], f"kernel-case-{i}.txt", source, env)
    run(
        [sys.executable, "-m", "unittest", "formal.reference.profile_source.test_genesis"],
        "reference-tests.txt",
    )
    paths = [
        "formal/reference/profile_source/genesis.py",
        "formal/reference/profile_source/test_genesis.py",
        "formal/reference/profile_source/genesis_vectors.py",
        "formal/proposals/b-family-transfer/check_genesis.py",
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "lint.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "format.txt")
    if pins != {path: source_digest(ROOT / path) for path in pins}:
        raise RuntimeError("Sources changed during qualification")
    data = dict(
        task_ids=["T047", "T053"],
        scope_revision=3,
        assignment_id="2fd81f70-bb27-4872-a09c-8a712c0e2311",
        result="GENESIS_VALUE_SOURCE_CHECKED",
        R23="OPEN",
        formal="NO_GO",
        sources=pins,
        checks=checks,
        audited_declarations=declarations,
        generated_audit_sha256=digest(audit.encode()),
        generated_vectors_sha256=digest(vectors.encode()),
        originals_sha256=digest((OUT / "originals.json").read_bytes()),
        lean=version.strip(),
        lean_binary_sha256=digest(LEAN.read_bytes()),
        source_hash_rule="Git LF-normalized text; original protocol bytes unchanged",
        residual="Complete producing history, original ISC/clock/seed association, certified floor "
        "and full public-state/initial/incomplete/ABORT composition remain "
        "unclosed and unreviewed.",
        evidence_kind="SYNTHETIC_METADATA_VALUES_NOT_FULL_LAWFUL_SNAPSHOT",
    )
    receipt = json.dumps(data, sort_keys=True, indent=2) + "\n"
    (OUT / "receipt.json").write_text(receipt, "utf8", newline="\n")
    print(
        json.dumps(dict(result=data["result"], receipt_sha256=digest(receipt.encode()), R23="OPEN"))
    )


if __name__ == "__main__":
    main()
