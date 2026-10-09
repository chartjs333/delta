"""T047/T053: independent bootstrap/index/trusted-floor byte composition."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-origin"
OUT = ROOT / "formal/proposals/evidence/profile-origin"
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
        try:
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
        except subprocess.TimeoutExpired as error:
            (OUT / name).write_text("TIMEOUT 300s\n" + str(error), encoding="utf8", newline="\n")
            raise
        log = result.stdout + result.stderr
        (OUT / name).write_text(log, encoding="utf8", newline="\n")
        checks.append({"log": name, "exit_code": result.returncode, "sha256": digest(log.encode())})
        if result.returncode:
            raise RuntimeError("Qualification failed " + name)
        return log

    visit("ProfileOrigin")
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
    raw = Path(__file__).with_name("ProfileOrigin.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) ([\w.]+)", raw, re.M)
    if not {
        "bootstrapSource",
        "complete",
        "originalSourceInventory",
        "originalInitialConfiguration",
        "boundFloorNoRecordErasure",
        "floorNeverRollsBack",
        "floorComplete",
    } <= set(declarations):
        raise RuntimeError("Missing original candidate obligation")
    audit = "import ProfileOrigin\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.Origin." + name + "\n" for name in declarations
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any("DeltaReduce.ProfileSource.Origin." + name not in log for name in declarations):
        raise RuntimeError("Incomplete axiom audit")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    sources["generated/Audit.lean"] = digest(audit.encode())

    from formal.reference.profile_source.origin_vectors import generate

    vectors, originals = generate()
    (src / "Vectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    sources["generated/Vectors.lean"] = digest(vectors.encode())
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    pattern = r"^example\b[\s\S]*?(?=^(?:def |end |example |namespace |open |set_option )|\Z)"
    assertions = re.findall(pattern, vectors, flags=re.MULTILINE)
    if len(assertions) != 11:
        raise RuntimeError("Wrong original assertion inventory")
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
            "set_option maxRecDepth 30000\nset_option maxHeartbeats 8000000\n"
            "namespace OriginVectors\n" + assertion + "end OriginVectors\n"
        )
        name = f"Case{i}.lean"
        (src / name).write_text(case, encoding="utf8", newline="\n")
        sources["generated/" + name] = digest(case.encode())
        run([str(LEAN), name], f"kernel-case-{i}.txt", src, environment)
    paths = [
        "formal/reference/profile_source/origin_vectors.py",
        str(Path(__file__).relative_to(ROOT)),
    ]
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
                sources[path.relative_to(ROOT).as_posix()] = digest(
                    path.read_bytes().replace(b"\r\n", b"\n")
                )
    sources[Path(__file__).relative_to(ROOT).as_posix()] = digest(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    )
    receipt = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 13,
        "result": "ORIGIN_FLOOR_SOURCE_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "sources": sources,
        "checks": checks,
        "artifacts": {"originals.json": digest((OUT / "originals.json").read_bytes())},
        "audited_declarations": declarations,
        "established": [
            "Independent bootstrap digest/pins to original source index "
            "and initial configuration bytes",
            "Complete trusted T log framing, original chain, ordinal and generation continuity",
            "Nondecreasing trusted floor; same-height exact identity; no dropped original T record",
        ],
        "not_established": [
            "Lawful genesis/initial configuration, native producing prefix, phase or barriers",
            "ApplyQC/key signature authority, semantic journal cuts, "
            "full imported snapshot binding",
            "Full public totality, R2.3 reviewed closure or recovery theorem",
        ],
        "source_hash_rule": "Git LF source text; original protocol bytes without normalization",
        "evidence_kind": "SYNTHETIC_METADATA_NOT_LAWFUL_GENESIS_OR_PRODUCER_HISTORY",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
