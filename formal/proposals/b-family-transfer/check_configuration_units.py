"""T047/T053: qualify schema-3 CONFIG source composition, not R2.3/GO."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-configuration-units"
OUT = ROOT / "formal/proposals/evidence/profile-configuration-units"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    src, objects = BUILD / "source", BUILD / "objects"
    OUT.mkdir(parents=True, exist_ok=True)
    sources, order, checks = {}, [], []

    def visit(name):
        if name in order or name in {"Init", "Std"}:
            return
        if name.startswith("DeltaReduce."):
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        elif name in {
            "ProfileArithmeticUnits",
            "ProfileConfiguration",
            "ProfileConfigurationUnits",
        }:
            path = Path(__file__).with_name(name + ".lean")
        else:
            raise RuntimeError("Unexpected dependency " + name)
        raw = path.read_bytes()
        sources[path.relative_to(ROOT).as_posix()] = digest(raw)
        if re.search(
            r"\b(sorry|axiom)\b", re.sub(r"/-.*?-/|--[^\n]*", "", raw.decode(), flags=re.S)
        ):
            raise RuntimeError("Unproved source " + name)
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.M):
            visit(child)
        destination = src / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        order.append(name)

    def run(command, name, cwd=ROOT, env=None):
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf8",
            timeout=300,
            check=False,
        )
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, encoding="utf8", newline="\n")
        checks.append({"log": name, "exit_code": result.returncode, "sha256": digest(log.encode())})
        if result.returncode:
            raise RuntimeError("Qualification failed " + name)
        return log

    visit("ProfileConfigurationUnits")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = run([str(LEAN), "--version"], "lean-version.txt").strip()
    for name in order:
        output = objects / (name.replace(".", "/") + ".olean")
        output.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(output), name.replace(".", "/") + ".lean"],
            "module-" + name + ".txt",
            src,
            environment,
        )
        print("Kernel checked " + name, flush=True)

    from formal.reference.profile_source.configuration_unit_vectors import generate

    defs, assertions = generate()
    vectors = "\n".join(defs + assertions + ["end ConfigUnitVectors", ""])
    (src / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    sources["generated/Vectors.lean"] = digest(vectors.encode())
    (OUT / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    definitions = "\n".join([*defs, "end ConfigUnitVectors", ""])
    (src / "Definitions.lean").write_text(definitions, encoding="utf8", newline="\n")
    sources["generated/Definitions.lean"] = digest(definitions.encode())
    run(
        [str(LEAN), "-o", str(objects / "Definitions.olean"), "Definitions.lean"],
        "definitions.txt",
        src,
        environment,
    )
    for i, assertion in enumerate(assertions):
        case = (
            "import Definitions\nopen DeltaReduce.ProfileSource.ConfigurationUnits\n"
            "open DeltaReduce.NativeVoteBytes (ascii)\n"
            "set_option maxRecDepth 40000\nset_option maxHeartbeats 12000000\n"
            "namespace ConfigUnitVectors\n" + assertion + "\nend ConfigUnitVectors\n"
        )
        name = f"Case{i}.lean"
        (src / name).write_text(case, encoding="utf8", newline="\n")
        sources["generated/" + name] = digest(case.encode())
        run([str(LEAN), name], f"kernel-case-{i}.txt", src, environment)
        print(f"Kernel vector {i + 1}/{len(assertions)} checked", flush=True)

    audit = "import ProfileConfigurationUnits\n"
    declarations = []
    for module, namespace in (
        ("ProfileConfiguration", "Configuration"),
        ("ProfileConfigurationUnits", "ConfigurationUnits"),
    ):
        raw = Path(__file__).with_name(module + ".lean").read_text(encoding="utf8")
        for name in re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M):
            qualified = "DeltaReduce.ProfileSource." + namespace + "." + name
            declarations.append(qualified)
            audit += "#print axioms " + qualified + "\n"
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    sources["generated/Audit.lean"] = digest(audit.encode())
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any(name not in log for name in declarations):
        raise RuntimeError("Incomplete axiom audit")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    paths = [
        "formal/reference/profile_source/" + name
        for name in (
            "arithmetic_units.py",
            "configuration_units.py",
            "configuration.py",
            "test_arithmetic_units.py",
            "configuration_unit_vectors.py",
        )
    ]
    paths.append(Path(__file__).relative_to(ROOT).as_posix())
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "formal.reference.profile_source.test_arithmetic_units",
            "-v",
        ],
        "python-units.txt",
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "formal.reference.profile_source.test_configuration",
            "-v",
        ],
        "configuration-regression.txt",
    )
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
            "-q",
        ],
        "profile-source-regression.txt",
    )
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
    for folder in (
        "profile_source",
        "isc_source",
        "isc_crypto",
        "isc_w1",
        "storage_source",
        "non_isc",
    ):
        for path in sorted((ROOT / "formal/reference" / folder).iterdir()):
            if path.suffix in {".py", ".json"}:
                sources[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    sources[paths[-1]] = digest(Path(__file__).read_bytes())
    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 15,
        "ack_id": "scope-ack-3af86533ad045e34125ea0b923d80680",
        "base_commit": "4dea988bae971c6b05f004319764a220cd9e4717",
        "status": "CONFIGURATION_SOURCE_CONJUNCT_ONLY",
        "r2_3": "OPEN",
        "formal_go": False,
        "lean_version": version,
        "lean_binary_sha256": digest(LEAN.read_bytes()),
        "kernel_vector_count": len(assertions),
        "checks": checks,
        "sources": sources,
        "source_hash_rule": "exact_file_bytes",
        "limits": [
            "Not full original producer/initial authority or history-derived UnitSource",
            "No graph review, independent attestation or recovery theorem closure",
            "Parent supplied here must still be independently derived from genesis/current history",
            "Numeric lexer completeness is inherited as an explicitly open obligation",
            "New model/mutant/refinement/budget/compatibility qualification still required",
        ],
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(
        json.dumps({k: receipt[k] for k in ("status", "r2_3", "kernel_vector_count")}), flush=True
    )


if __name__ == "__main__":
    main()
