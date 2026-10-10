"""T047/T053: original EC companion qualification; not whole R2.3 closure."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-ec-durability"
OUT = ROOT / "formal/proposals/evidence/profile-ec-durability"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    src, objects = BUILD / "source", BUILD / "objects"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").unlink(missing_ok=True)
    sources, order, checks = {}, [], []
    source_folders = (
        "profile_source",
        "isc_source",
        "isc_crypto",
        "isc_w1",
        "storage_source",
        "non_isc",
    )

    def reference_inputs():
        return {
            path.relative_to(ROOT).as_posix(): digest(path.read_bytes().replace(b"\r\n", b"\n"))
            for folder in source_folders
            for path in sorted((ROOT / "formal/reference" / folder).iterdir())
            if path.suffix in {".py", ".json"}
        }

    starting_references = reference_inputs()
    authorization_path = ROOT / "formal/proposals/evidence/profile-ec-durability/authorization.json"
    authorization = json.loads(authorization_path.read_text(encoding="utf8"))
    contract = ROOT / "formal/proposals/ec-durable-binding-contract.md"
    if digest(contract.read_bytes()) != authorization["contract_sha256"]:
        raise RuntimeError("Selected immutable contract byte mismatch")

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
            raise RuntimeError("Unexpected dependency " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
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
            print(log, flush=True)
            raise RuntimeError("Qualification failed " + name)
        return log

    visit("ProfileEcDurability")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = run([str(LEAN), "--version"], "lean-version.txt").strip()
    for name in order:
        output = objects / (name.replace(".", "/") + ".olean")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Development resumes may reuse ONLY source-equal objects. A qualifying
        # run (no --compile-only) always recompiles the complete closure.
        stamp = output.with_suffix(".source-sha256")
        source = src / (name.replace(".", "/") + ".lean")
        sha = digest(source.read_bytes())
        if "--compile-only" not in sys.argv or not (
            output.exists() and stamp.exists() and stamp.read_text() == sha
        ):
            run(
                [str(LEAN), "-o", str(output), source.relative_to(src).as_posix()],
                "module-" + name + ".txt",
                src,
                environment,
            )
            stamp.write_text(sha)
        print("compiled " + name, flush=True)
    if "--compile-only" in sys.argv:
        return
    raw = Path(__file__).with_name("ProfileEcDurability.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) ([\w.]+)\b", raw, re.M)
    audit = "import ProfileEcDurability\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.EcDurability." + name + "\n"
        for name in declarations
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    for name in declarations:
        if "DeltaReduce.ProfileSource.EcDurability." + name not in log:
            raise RuntimeError("Incomplete axiom audit " + name)
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    sources["generated/Audit.lean"] = digest(audit.encode())
    from formal.reference.profile_source.ec_durability_vectors import generate

    vectors, originals = generate()
    (src / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    sources["generated/Vectors.lean"] = digest(vectors.encode())
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option |--)|\Z)"
    assertions = re.findall(pattern, vectors, flags=re.MULTILINE)
    if len(assertions) != 18:
        raise RuntimeError("Wrong exact assertion inventory")
    definitions = re.sub(pattern, "", vectors, flags=re.MULTILINE)
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
            "import Definitions\nopen DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes\n"
            "open EcDurability\nset_option maxRecDepth 30000\nset_option maxHeartbeats 12000000\n"
            "namespace EcDurabilityVectors\n" + assertion + "end EcDurabilityVectors\n"
        )
        name = f"Case{i}.lean"
        (src / name).write_text(case, encoding="utf8", newline="\n")
        sources["generated/" + name] = digest(case.encode())
        run([str(LEAN), name], f"kernel-case-{i}.txt", src, environment)
        print("checked " + name, flush=True)
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    paths = [
        "formal/reference/profile_source/ec_durability.py",
        "formal/reference/profile_source/ec_durability_vectors.py",
        "formal/reference/profile_source/test_ec_durability.py",
        str(Path(__file__).relative_to(ROOT)),
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
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
        "profile-source-regression.txt",
    )
    if reference_inputs() != starting_references:
        raise RuntimeError("Reference source changed during qualification")
    sources.update(starting_references)
    for name, expected in sources.items():
        if (
            not name.startswith("generated/")
            and digest((ROOT / name).read_bytes().replace(b"\r\n", b"\n")) != expected
        ):
            raise RuntimeError("Source changed during qualification: " + name)
    sources[Path(__file__).relative_to(ROOT).as_posix()] = digest(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    )
    for relative in (
        "formal/proposals/ec-durable-binding-contract.md",
        "formal/proposals/evidence/profile-ec-durability/authorization.json",
    ):
        sources[relative] = digest((ROOT / relative).read_bytes().replace(b"\r\n", b"\n"))
    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "b04b6d00-763e-4db0-a5c0-5adc39638af1",
        "scope_revision": 18,
        "result": "EC_COMPANION_CONJUNCTS_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "sources": sources,
        "checks": checks,
        "artifacts": {"originals.json": digest((OUT / "originals.json").read_bytes())},
        "audited_declarations": declarations,
        "limits": [
            "Not the complete native producing fold or R2.3 composition",
            "Primitive successful barrier uses existing Profile T assumption",
            "Synthetic vectors are not deployed production histories",
            "One-transaction crash machine does not replace arbitrary later current/ABORT replay",
            "Hash collision resistance is not proved by finite vectors",
            "No production storage change, deployment or Formal GO",
        ],
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(
        json.dumps({key: receipt[key] for key in ("result", "formal_status", "r2_3")}), flush=True
    )


if __name__ == "__main__":
    main()
