"""T047/T053: exact schema-3 configuration/QC/input/W1 source-route qualification.

This does not certify a complete producing prefix or close R2.3. No production
object, runtime, guard, semantics identifier or certificate identity is changed.
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
BUILD = ROOT / "formal/build/profile-configuration-route-qualified"
OUT = ROOT / "formal/proposals/evidence/profile-configuration-route"
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
        elif name == "SourceVote":
            path = ROOT / "formal/proposals/isc-source-generation/SourceVote.lean"
        elif re.fullmatch(r"Profile[A-Za-z]+", name):
            path = Path(__file__).with_name(name + ".lean")
        else:
            raise RuntimeError("Unexpected dependency " + name)
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

    visit("ProfileConfigurationQC")
    for path in (ROOT / "formal/reference").rglob("*"):
        if path.is_file() and path.suffix in {".py", ".json"}:
            pins[path.relative_to(ROOT).as_posix()] = source_digest(path)
    for path in (
        Path(__file__),
        ROOT / "formal/scripts/native_source_artifacts.py",
        ROOT / "formal/proposals/profile-unit-state-composition.md",
        ROOT / "formal/proposals/arithmetic-unit-source-binding-v1.md",
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
            raise RuntimeError(name + ": " + log[-5000:])
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
    module = Path(__file__).with_name("ProfileConfigurationQC.lean").read_text("utf8")
    names = re.findall(r"^(?:def|theorem) ([\w.]+)", module, re.M)
    if not {
        "unitChecked",
        "unitComplete",
        "unitOriginalConfigurationAndQuorum",
        "unitEveryPairIsOriginal",
    } <= set(names):
        raise RuntimeError("Missing full configuration/QC obligations")
    qualified = ["DeltaReduce.ProfileSource.ConfigurationQC." + name for name in names]
    audit = "import ProfileConfigurationQC\n" + "".join(
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
    from formal.reference.profile_source import configuration_route as route
    from formal.reference.profile_source.configuration_qc_vectors import generate

    vector_pins = {}
    for generation in (route.LEGACY, route.UNITS):
        vectors, evidence = generate(generation=generation)
        name = "Vectors" + generation.name
        (source / (name + ".lean")).write_text(vectors, "utf8", newline="\n")
        original = json.dumps(evidence, indent=2) + "\n"
        (OUT / (name + "-originals.json")).write_text(original, "utf8", newline="\n")
        vector_pins[name] = dict(
            lean_sha256=digest(vectors.encode()), originals_sha256=digest(original.encode())
        )
        run([str(LEAN), name + ".lean"], name + "-kernel.txt", source, env)
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/profile_source",
            "-p",
            "test_*.py",
        ],
        "reference-tests.txt",
        env=env,
    )
    paths = ["formal/reference/profile_source", str(Path(__file__).relative_to(ROOT))]
    run([sys.executable, "-m", "ruff", "check", *paths], "lint.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "format.txt")
    if pins != {path: source_digest(ROOT / path) for path in pins}:
        raise RuntimeError("Sources changed during qualification")
    data = dict(
        task_ids=["T047", "T053"],
        scope_revision=3,
        assignment_id="2fd81f70-bb27-4872-a09c-8a712c0e2311",
        result="EXPLICIT_CONFIGURATION_SOURCE_ROUTE_CHECKED",
        R23="OPEN",
        formal="NO_GO",
        sources=pins,
        checks=checks,
        audited_declarations=names,
        vectors=vector_pins,
        generated_audit_sha256=digest(audit.encode()),
        lean=version.strip(),
        lean_binary_sha256=digest(LEAN.read_bytes()),
        source_hash_rule="Git LF-normalized text; protocol bytes unchanged",
        evidence_kind="SYNTHETIC_FACETS_NOT_COMPLETE_LAWFUL_PRODUCER_OR_RECOVERY",
        residual="Full original producing prefix and parent at each cut, all source/clock/seed "
        "associations, import floor and complete public family remain open/unreviewed.",
    )
    receipt = json.dumps(data, sort_keys=True, indent=2) + "\n"
    (OUT / "receipt.json").write_text(receipt, "utf8", newline="\n")
    print(
        json.dumps(dict(result=data["result"], receipt_sha256=digest(receipt.encode()), R23="OPEN"))
    )


if __name__ == "__main__":
    main()
