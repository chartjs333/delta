"""T047/T053 seed reference evidence/intent components; not whole producer qualification."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "formal/proposals/evidence/profile-seed-agreement"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def text_digest(path):
    return digest(path.read_bytes().replace(b"\r\n", b"\n"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "receipt.json").unlink(missing_ok=True)
    sources = [
        Path(__file__),
        Path(__file__).with_name("ProfileSeedIntent.lean"),
        Path(__file__).with_name("ProfileSeedDurability.lean"),
        Path(__file__).with_name("ProfileSeedKnowledge.lean"),
        Path(__file__).with_name("ProfileSeedAgreementSafety.lean"),
        ROOT / "formal/proofs/DeltaReduce/Quorum.lean",
        ROOT / "formal/proposals/seed-agreement-contract.md",
        ROOT / "formal/proposals/seed-durable-producer-contract.md",
    ]
    for folder in ("seed_source", "isc_crypto", "isc_source", "isc_w1"):
        sources.extend(sorted((ROOT / "formal/reference" / folder).glob("*.py")))
    pins = {p.relative_to(ROOT).as_posix(): text_digest(p) for p in sources}
    pvss = ROOT / "formal/proposals/evidence/profile-seed-pvss/receipt.json"
    prior = json.loads(pvss.read_text("utf8"))
    if prior["status"] != "PVSS_COMPONENT_CHECKED" or any(
        text_digest(ROOT / path) != h for path, h in prior["sources"].items()
    ):
        raise RuntimeError("PVSS component receipt not applicable")
    checks = []

    def run(command, name):
        result = subprocess.run(
            command,
            cwd=ROOT,
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
            raise RuntimeError(name + " failed: " + log[-3000:])
        return log

    lean = Path(os.environ["FAMILY_LEAN"])
    version = run([str(lean), "--version"], "lean-version.txt").strip()
    if "4.32.1" not in version:
        raise RuntimeError("Wrong Lean version")
    axioms_log = run(
        [str(lean), "formal/proposals/b-family-transfer/ProfileSeedIntent.lean"],
        "intent-proof-and-axioms.txt",
    )
    axioms = re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]", axioms_log)
    if len(axioms) != 8 or any(
        set(values.split(", ")) - {"propext", "Quot.sound"} for _, values in axioms
    ):
        raise RuntimeError("Unexpected/incomplete intent axiom audit")
    storage_log = run(
        [str(lean), "formal/proposals/b-family-transfer/ProfileSeedDurability.lean"],
        "durability-proof-and-axioms.txt",
    )
    storage_axioms = re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]", storage_log)
    if len(storage_axioms) != 8 or any(
        set(values.split(", ")) - {"propext", "Quot.sound"} for _, values in storage_axioms
    ):
        raise RuntimeError("Unexpected/incomplete durability axiom audit")
    axioms += storage_axioms
    packages = Path(os.environ["PVSS_MATHLIB_PACKAGES"])
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=packages / "mathlib", text=True
    ).strip()
    if actual != "520045ab14e26149ee970e2e617ca04b09bde5d6":
        raise RuntimeError("Wrong pinned mathlib revision")
    cache = ROOT / ".cache/seed-proof"
    (cache / "DeltaReduce").mkdir(parents=True, exist_ok=True)
    os.environ["LEAN_PATH"] = os.pathsep.join(
        [str(p / ".lake/build/lib/lean") for p in packages.iterdir() if p.is_dir()] + [str(cache)]
    )
    run(
        [
            str(lean),
            "-o",
            str(cache / "DeltaReduce/Quorum.olean"),
            "formal/proofs/DeltaReduce/Quorum.lean",
        ],
        "quorum-reuse.txt",
    )
    for module, name in (
        ("ProfileSeedKnowledge", "knowledge"),
        ("ProfileSeedAgreementSafety", "cross-view-factor"),
    ):
        log = run(
            [str(lean), "formal/proposals/b-family-transfer/" + module + ".lean"],
            name + "-proof-and-axioms.txt",
        )
        checked = re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]", log)
        if len(checked) != 4 or any(
            set(values.replace("\n", "").replace(" ", "").split(","))
            - {"propext", "Quot.sound", "Classical.choice"}
            for _, values in checked
        ):
            raise RuntimeError("Unexpected/incomplete " + name + " axiom audit")
        axioms += checked
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/reference/seed_source",
            "-p",
            "test_*.py",
            "-v",
        ],
        "reference-tests.txt",
    )
    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "formal/reference/seed_source",
            "formal/proposals/b-family-transfer/check_seed_pvss.py",
            str(Path(__file__)),
        ],
        "lint.txt",
    )
    run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "formal/reference/seed_source",
            "formal/proposals/b-family-transfer/check_seed_pvss.py",
            str(Path(__file__)),
        ],
        "format.txt",
    )
    if pins != {p.relative_to(ROOT).as_posix(): text_digest(p) for p in sources}:
        raise RuntimeError("Sources changed during qualification")
    data = dict(
        status="SEED_EVIDENCE_AND_INTENT_COMPONENTS_CHECKED",
        R23="OPEN",
        formal="NO_GO",
        complete_seed_producer=False,
        durability_primitive_checked=True,
        local_status_floor_checked=True,
        cross_view_factor_checked=True,
        cross_view_safety_proved=False,
        original_source_join_closed=False,
        production_compatible=False,
        sources=pins,
        source_hash_encoding="Git LF-normalized text only",
        pvss_receipt_sha256=text_digest(pvss),
        lean=version,
        lean_binary_sha256=digest(lean.read_bytes()),
        checks=checks,
        axioms={
            name: values.replace("\n", "").replace(" ", "").split(",") for name, values in axioms
        },
        residual="complete honest source-index association of generating/durable/release prefix, "
        "cross-view safety and "
        "existing-policy progress, source-index/native-state join; all three full "
        "R2.3 obligations remain; no named recovery theorem or Formal GO",
    )
    raw = json.dumps(data, sort_keys=True, indent=2) + "\n"
    (OUT / "receipt.json").write_text(raw, "utf8", newline="\n")
    print(
        json.dumps(
            {"status": data["status"], "receipt_sha256": digest(raw.encode()), "R23": "OPEN"}
        )
    )


if __name__ == "__main__":
    main()
