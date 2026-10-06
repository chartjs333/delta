"""T047/T053: isolated successor source-component check, never a GO report."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BUILD = ROOT / "formal/build/isc-source-v2"
OUT = ROOT / "formal/proposals/evidence/isc-source-v2"
LEAN = Path(os.environ.get("FAMILY_LEAN", "D:/formal-tools-20260920/lean/bin/lean.exe"))
PIN = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
AMENDMENT = "docs/adr/0014-isc-production-contract-amendment-v1.md"
AMENDMENT_SHA = "214ca238fde93ebe2e6e08b25a6ea366b93d735333125f651398c0d0daad58fd"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    exact = subprocess.check_output(["git", "show", f"{PIN}:{AMENDMENT}"], cwd=ROOT)
    if digest(exact) != AMENDMENT_SHA:
        raise RuntimeError("Approved amendment source mismatch")
    OUT.mkdir(parents=True, exist_ok=True)
    source, objects = BUILD / "source", BUILD / "objects"
    sources, order = {}, []

    def visit(name: str) -> None:
        if name in sources or name in {"Std", "Init"}:
            return
        if name in {"SourcePolicy", "SourceBudget"}:
            path = Path(__file__).with_name(name + ".lean")
        elif name.startswith("DeltaReduce."):
            path = ROOT / "formal/proofs" / (name.replace(".", "/") + ".lean")
        else:
            raise RuntimeError("Unreviewed import: " + name)
        raw = path.read_bytes()
        sources[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(raw)}
        text = raw.decode("utf-8-sig")
        for child in re.findall(r"^import\s+(\S+)", text, re.M):
            visit(child)
        destination = source / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8", newline="\n")
        order.append(name)

    visit("SourcePolicy")
    visit("SourceBudget")
    environment = dict(os.environ, LEAN_PATH=str(objects))
    version = subprocess.check_output([str(LEAN), "--version"], text=True).strip()
    if "version 4.32.1" not in version:
        raise RuntimeError("Unqualified Lean version: " + version)
    checks = []
    for name in order:
        target = objects / (name.replace(".", "/") + ".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(
            [str(LEAN), "-o", str(target), name.replace(".", "/") + ".lean"],
            cwd=source,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        log = process.stdout + process.stderr
        (OUT / (name + ".txt")).write_text(log, encoding="utf-8", newline="\n")
        checks.append(
            {"module": name, "exit_code": process.returncode, "log_sha256": digest(log.encode())}
        )
        if process.returncode or "sorry" in log:
            raise RuntimeError(name + "\n" + log)
        print("checked " + name, flush=True)
    names = [
        "bodyOriginal",
        "certificateOriginal",
        "completeSnapshotInventory",
        "completePolicyInventory",
        "bodyParentExact",
        "certificateParentExact",
        "bodyIgnoresWitness",
        "distinctLegacyHeader",
        "fullPolicyRoundTrip",
        "fullPolicyNoErasure",
        "snapshotLineageRetained",
        "fullPolicyOutsideSnapshotRetained",
    ]
    audit = "import SourcePolicy\nimport SourceBudget\n" + "".join(
        "#print axioms DeltaReduce.ISCSourceV2." + name + "\n" for name in names
    )
    audit += "".join(
        "#print axioms DeltaReduce.ISCSourceV2.Budget." + name + "\n"
        for name in ["walSufficient", "outputSufficient", "logicalResponseSufficient"]
    )
    (source / "Audit.lean").write_text(audit, encoding="utf-8")
    process = subprocess.run(
        [str(LEAN), "Audit.lean"],
        cwd=source,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    log = process.stdout + process.stderr
    (OUT / "axioms.txt").write_text(log, encoding="utf-8", newline="\n")
    if process.returncode or "sorryAx" in log:
        raise RuntimeError(log)
    # Only standard kernel foundations; unknown user axioms are rejected.
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log, re.S):
        if set(group.replace("\n", " ").replace(" ", "").split(",")) - {
            "",
            "propext",
            "Classical.choice",
            "Quot.sound",
        }:
            raise RuntimeError("Unexpected axiom: " + group)
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "formal/reference/isc_source",
        "-p",
        "test_*.py",
        "-v",
    ]
    process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
    (OUT / "reference-tests.txt").write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode:
        raise RuntimeError(process.stdout + process.stderr)
    reference = ROOT / "formal/reference/isc_source"
    receipt = {
        "task_id": "ISC-S16-D01",
        "scope_revision": 3,
        "approved_contract": {"commit": PIN, "path": AMENDMENT, "sha256": AMENDMENT_SHA},
        "lean": version,
        "sources": sources,
        "checks": checks,
        "reference": {
            p.relative_to(ROOT).as_posix(): digest(p.read_bytes())
            for p in sorted(reference.iterdir())
            if p.suffix in {".py", ".json", ".md"}
        },
        "checker_sha256": digest(Path(__file__).read_bytes()),
        "axioms_sha256": digest(log.encode()),
        "reference_test_exit": process.returncode,
        "result": "SUCCESSOR_SOURCE_REPRESENTATION_COMPONENTS_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "limits": [
            "No producer-origin or complete Profile-v1 applicability theorem yet.",
            "No full public family, R2.3 closure, recovery theorem or production changes.",
            "Synthetic byte fixtures do not authenticate a deployment history.",
            "Legacy semantics/evidence unchanged; sigma remains a parameter.",
        ],
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
