"""T047/T053: qualify the successor coarse producer, without full R2.3 claims."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-command-source"
OUT = ROOT / "formal/proposals/evidence/profile-command-source"
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
        elif name in {"SourcePolicy", "SourceVote"}:
            path = ROOT / "formal/proposals/isc-source-generation" / (name + ".lean")
        elif name.startswith("Profile") and re.fullmatch(r"Profile[A-Za-z]+", name):
            path = Path(__file__).with_name(name + ".lean")
        else:
            raise RuntimeError("Unexpected project dependency " + name)
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        sources[path.relative_to(ROOT).as_posix()] = digest(raw)
        if re.search(
            r"\b(sorry|axiom)\b", re.sub(r"/-.*?-/|--[^\n]*", "", raw.decode(), flags=re.S)
        ):
            raise RuntimeError("Unproved source declaration " + name)
        for child in re.findall(r"^import\s+(\S+)", raw.decode(), re.M):
            visit(child)
        destination = src / (name.replace(".", "/") + ".lean")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        order.append(name)

    def run(command, name, cwd=ROOT, env=None):
        result = subprocess.run(
            command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf8", timeout=300
        )
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, encoding="utf8", newline="\n")
        checks.append({"log": name, "exit_code": result.returncode, "sha256": digest(log.encode())})
        if result.returncode:
            raise RuntimeError("Qualification failed " + name)
        return log

    visit("ProfileCommands")
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

    raw = Path(__file__).with_name("ProfileCommands.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) (\w+)", raw, re.M)
    required = {
        "derivedSource",
        "derivedComplete",
        "computedState",
        "executedSource",
        "executedComplete",
        "storedComputed",
        "physicalSlotIndependent",
    }
    if not required <= set(declarations):
        raise RuntimeError("Required command result missing")
    audit = "import ProfileCommands\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.Commands." + name + "\n" for name in declarations
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any("DeltaReduce.ProfileSource.Commands." + name not in log for name in declarations):
        raise RuntimeError("Incomplete axiom audit output")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    sources["generated/Audit.lean"] = digest(audit.encode())

    from formal.reference.profile_source.command_vectors import generate

    vectors, originals = generate()
    (src / "CommandVectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run([str(LEAN), "CommandVectors.lean"], "kernel-vectors.txt", src, environment)
    sources["generated/CommandVectors.lean"] = digest(vectors.encode())
    run(
        [sys.executable, "-m", "unittest", "formal.reference.profile_source.test_commands", "-v"],
        "native-capture-reference.txt",
    )

    capture_path = ROOT / "formal/proposals/evidence/native-transition/cpp-cross-check.json"
    capture = json.loads(capture_path.read_text())
    pin = "60c692f6e391f839829dfc64e93380db54cd507b"
    if capture["source_commit"] != pin:
        raise RuntimeError("Native capture source pin changed")
    for path, expected in capture["source_sha256"].items():
        if not re.fullmatch(r"delta-[A-Za-z0-9_./-]+", path) or ".." in path:
            raise RuntimeError("Unexpected native source path")
        native = subprocess.check_output(
            ["cmd.exe", "/d", "/c", "git", "cat-file", "blob", pin + ":" + path], cwd=ROOT
        )
        if digest(native) != expected:
            raise RuntimeError("Native capture source hash changed")

    paths = [
        "formal/reference/profile_source/command_vectors.py",
        str(Path(__file__).relative_to(ROOT)),
    ]
    run([sys.executable, "-m", "ruff", "check", *paths], "ruff.txt")
    run([sys.executable, "-m", "ruff", "format", "--check", *paths], "ruff-format.txt")
    # Pin complete reference inputs used by the generator/native cross-check.
    for folder in (
        "profile_source",
        "isc_source",
        "isc_crypto",
        "isc_w1",
        "storage_source",
        "non_isc",
    ):
        for path in sorted((ROOT / "formal/reference" / folder).iterdir()):
            if path.suffix not in {".py", ".json"}:
                continue
            sources[path.relative_to(ROOT).as_posix()] = digest(
                path.read_bytes().replace(b"\r\n", b"\n")
            )
    for path in (
        Path(__file__),
        capture_path,
        ROOT / "formal/proposals/native-transition-vectors.json",
        ROOT / "formal/scripts/native_source_artifacts.py",
        ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json",
        ROOT / "delta-protocol/fixtures/007/cross-language/golden-v1.json",
    ):
        sources[path.relative_to(ROOT).as_posix()] = digest(
            path.read_bytes().replace(b"\r\n", b"\n")
        )

    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 13,
        "result": "COARSE_COMMAND_SOURCE_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "sources": sources,
        "checks": checks,
        "artifacts": {"originals.json": digest((OUT / "originals.json").read_bytes())},
        "audited_declarations": declarations,
        "source_hash_rule": "Git LF source text; protocol originals retained without normalization",
        "native_evidence": {
            "source_commit": pin,
            "source_sha256": capture["source_sha256"],
            "kind": "REUSE_VERIFIED_CAPTURE_NOT_NEW_NATIVE_EXECUTION",
        },
        "established": [
            "Original seven command guards and deterministic successor state bytes",
            "Full computed effects and inner WAL record; altered stored bytes reject",
            "Existing physical slot is independent of coarse state sequence",
        ],
        "not_established": [
            "Initial origin, phase/delivery/finality/durability source composition",
            "Complete O state relation, totality or reviewed R2.3 closure",
            "Named recovery theorem, full formal gates or production GO",
        ],
        "evidence_kind": "SYNTHETIC_SUCCESSOR_COMPONENT_AND_RETAINED_LEGACY_CAPTURE",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
