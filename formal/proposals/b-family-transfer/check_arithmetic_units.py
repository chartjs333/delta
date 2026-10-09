"""T047/T053: qualify only the selected U/R/P byte component, not R2.3/GO."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-arithmetic-units"
OUT = ROOT / "formal/proposals/evidence/profile-arithmetic-units"
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
        elif name == "ProfileArithmeticUnits":
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

    visit("ProfileArithmeticUnits")
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

    from formal.reference.profile_source import arithmetic_units as u
    from formal.reference.profile_source import metadata
    from formal.reference.profile_source.test_arithmetic_units import (
        PROOF,
        SCHEMA,
        SEMANTICS,
        initial,
        numeric,
    )

    r = u.canonical(numeric())
    p = u.derive_profile(r, PROOF, SEMANTICS)
    original_u = metadata.canonical(initial())
    numeric_literal = '(⟨⟨1,4⟩,[⟨ascii "d0",⟨1,1⟩⟩],⟨1,4⟩,⟨0,1⟩,⟨0,1⟩⟩ : Numeric)'

    def literal(raw):
        return "(" + str(list(raw)) + " : DeltaReduce.NativeReceiptBytes.Bytes)"

    defs = [
        "import ProfileArithmeticUnits",
        "open DeltaReduce.ProfileSource.ArithmeticUnits",
        "open DeltaReduce.NativeVoteBytes (ascii)",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace UnitVectors",
        "def r := " + literal(r),
        "def p := " + literal(p),
        "def u := " + literal(original_u),
        "def expected := " + numeric_literal,
        "def sigma := " + literal(SEMANTICS.encode()),
        "def proof := " + literal(PROOF.encode()),
        "def schema := " + literal(SCHEMA.encode()),
    ]
    preimage = u.DOMAIN.encode() + b"\0" + p
    defs.append(
        "def sha (raw : DeltaReduce.NativeReceiptBytes.Bytes) "
        ": DeltaReduce.NativeReceiptBytes.Bytes := if raw = "
        + literal(u.DOMAIN.encode())
        + " ++ [0] ++ p then "
        + str(list(hashlib.sha256(preimage).digest()))
        + " else []"
    )
    # A finite real SHA256 table is byte evidence, not a trusted source history.
    assertions = [
        "example : decodeNumeric r = some expected := by decide",
        "example : decodeInitial u = some ⟨schema,⟨1,4⟩⟩ := by decide",
        "example : numericJSON expected = r := by decide",
        "example : profileJSON sigma proof expected = p := by decide",
        "example : (select sha sigma proof r p).isSome = true := by decide",
        "example : select sha sigma schema r p = none := by decide",
        "example : select sha schema proof r p = none := by decide",
    ]
    bads = [
        r + b" ",
        r.replace(b'"numerator":"1"', b'"numerator":"01"', 1),
        r.replace(b'"denominator":4', b'"denominator":"4"', 1),
        r.replace(b'"denominator":4', b'"denominator":4.0', 1),
        r.replace(b'"nesterov":true', b'"nesterov":false'),
        r.replace(b'"nesterov":true', b'"nesterov":true,"nesterov":true'),
        u.canonical(numeric("2", 8)),
        u.canonical(numeric("0", 1)),
    ]
    assertions.extend(
        "example : decodeNumeric (" + literal(bad) + ") = none := by decide" for bad in bads
    )
    assertions.append(
        "example : decodeInitial ("
        + literal(original_u.replace(b'"4"', b"4", 1))
        + ") = none := by decide"
    )
    assertions = [assertion + " +kernel" for assertion in assertions]
    vectors = "\n".join(defs + assertions + ["end UnitVectors", ""])
    (src / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    sources["generated/Vectors.lean"] = digest(vectors.encode())
    (OUT / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    definitions = "\n".join([*defs, "end UnitVectors", ""])
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
            "import Definitions\nopen DeltaReduce.ProfileSource.ArithmeticUnits\n"
            "open DeltaReduce.NativeVoteBytes (ascii)\n"
            "set_option maxRecDepth 30000\nset_option maxHeartbeats 8000000\n"
            "namespace UnitVectors\n" + assertion + "\nend UnitVectors\n"
        )
        name = f"Case{i}.lean"
        (src / name).write_text(case, encoding="utf8", newline="\n")
        sources["generated/" + name] = digest(case.encode())
        run([str(LEAN), name], f"kernel-case-{i}.txt", src, environment)
        print(f"Kernel vector {i + 1}/{len(assertions)} checked", flush=True)

    raw = Path(__file__).with_name("ProfileArithmeticUnits.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    audit = "import ProfileArithmeticUnits\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.ArithmeticUnits." + name + "\n"
        for name in declarations
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    sources["generated/Audit.lean"] = digest(audit.encode())
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any("DeltaReduce.ProfileSource.ArithmeticUnits." + name not in log for name in declarations):
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
        "base_commit": "9f4d23b11fd1fa26586bce6fd8826c657fdfb0d1",
        "status": "BYTE_COMPONENT_ONLY",
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
            "numericComplete requires its explicit lexer premise; "
            "universal lexer completeness remains work",
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
