"""T047/T053 scope13: exact retention binding qualification, never Formal GO."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "formal/build/retention-source-v1"
OUT = ROOT / "formal/proposals/evidence/retention-source-v1"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))
PIN = "12326b892690705b7141fcd32bf3f32cf07d092e"
CONTRACT = "formal/proposals/retention-policy-source-binding-v1.md"
CONTRACT_SHA = "143452dac55c556cff99286e3e01df2a5ee27164c8c9668bf5079518c068540c"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    exact = subprocess.check_output(["git", "show", f"{PIN}:{CONTRACT}"], cwd=ROOT)
    if digest(exact) != CONTRACT_SHA:
        raise RuntimeError("Approved retention contract mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    src, objects = BUILD / "source", BUILD / "objects"
    sources, order, checks = {}, [], []

    def visit(name):
        if name in order or name in {"Init", "Std"}:
            return
        if name in {"RetentionSource", "RetentionSourceVectors"}:
            path = Path(__file__).with_name(name + ".lean")
        elif name.startswith("DeltaReduce."):
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        else:
            raise RuntimeError("Unqualified import " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        sources[path.relative_to(ROOT).as_posix()] = digest(raw)
        # Names are tracked separately from source paths to avoid repeated visits.
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.M):
            if child not in order:
                visit(child)
        destination = src / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        order.append(name)

    visit("RetentionSourceVectors")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = subprocess.check_output([str(LEAN), "--version"], text=True).strip()
    if "version 4.32.1" not in version:
        raise RuntimeError("Unqualified Lean toolchain " + version)

    def run(command, log_name, cwd=ROOT, env=None):
        proc = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf8",
            timeout=240,
        )
        log = proc.stdout + proc.stderr
        (OUT / log_name).write_text(log, encoding="utf8", newline="\n")
        checks.append(
            {"log": log_name, "exit_code": proc.returncode, "sha256": digest(log.encode())}
        )
        if proc.returncode or "sorryAx" in log or "declaration uses 'sorry'" in log:
            raise RuntimeError(log)
        return log

    for name in order:
        target = objects / (name.replace(".", "/") + ".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        run(
            [str(LEAN), "-o", str(target), name.replace(".", "/") + ".lean"],
            name + ".txt",
            src,
            environment,
        )
        print("checked " + name, flush=True)
    theorem_names = [
        "validSafe",
        "readEncoded",
        "decoded",
        "roundTrip",
        "encodingInjective",
        "resolved",
        "complete",
        "nonemptyOriginal",
        "substitutionRequiresDigestCollision",
    ]
    audit = "import RetentionSource\n" + "".join(
        "#print axioms DeltaReduce.RetentionSource." + name + "\n" for name in theorem_names
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log, re.S):
        if set(group.replace("\n", "").replace(" ", "").split(",")) - {
            "",
            "propext",
            "Classical.choice",
            "Quot.sound",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/storage_source",
            "-p",
            "test_*.py",
            "-v",
        ],
        "reference-tests.txt",
    )
    paths = ["formal/reference/storage_source", str(Path(__file__).relative_to(ROOT))]
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
    inputs = [
        *sorted((ROOT / "formal/reference/storage_source").glob("*.py")),
        ROOT / "formal/reference/storage_source/retention-source.schema.json",
        ROOT / "formal/reference/storage_source/retention-vectors.json",
        ROOT / "formal/reference/storage_source/README.md",
        ROOT / "formal/reference/isc_crypto/codec.py",
        ROOT / "formal/reference/isc_crypto/sodium_reference.py",
        ROOT / "formal/reference/isc_crypto/library-provenance.json",
        Path(__file__),
    ]
    for path in inputs:
        sources[path.relative_to(ROOT).as_posix()] = digest(
            path.read_bytes().replace(b"\r\n", b"\n")
        )
    pin = json.loads((ROOT / "formal/reference/isc_crypto/library-provenance.json").read_text())
    if digest(Path(os.environ["ISC_SODIUM_DLL"]).read_bytes()) != pin["dll"]["sha256"]:
        raise RuntimeError("Unqualified crypto backend")
    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "scope_revision": 13,
        "decision_id": "scope-decision-ccba23f3167be9feed1dd79a49db09b0",
        "ack_id": "scope-ack-a30732f8d640518596da678cfa2e63c3",
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "contract": {"commit": PIN, "path": CONTRACT, "sha256": CONTRACT_SHA},
        "result": "EXACT_RETENTION_SOURCE_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "lean": version,
        "source_hash_rule": "Git-compatible LF source text only; original protocol bytes unchanged",
        "sources": sources,
        "checks": checks,
        "backend_sha256": pin["dll"]["sha256"],
        "closed_component": [
            "Strict closed R, raw declaration length/digest and contextual epoch binding",
            "Canonical Lean decoder/encoder inverse and injectivity, exact raw resolution",
            "Substitution of differing accepted E requires a digest collision; no collision axiom",
            "Required storage_binding and actual S crypto composition preserve full inventory",
        ],
        "residual": (
            "Original complete configuration grammar/authority/producing-prefix composition, "
            "full O state/refinement and affected model/mutant/review gates remain open. "
            "Component Context is not provenance; no production policy or physical-retention claim."
        ),
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
