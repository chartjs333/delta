"""T047/T053: fresh exact original vote-row qualification, not full R2.3."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / "formal/build/profile-vote-record"
OUT = ROOT / "formal/proposals/evidence/profile-vote-record"
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

    visit("ProfileVoteRecord")
    visit("ProfileCurrentJournal")
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

    raw = Path(__file__).with_name("ProfileVoteRecord.lean").read_text(encoding="utf8")
    declarations = re.findall(r"^(?:def|theorem) (\w+)", raw, re.M)
    if not {
        "boundSource",
        "complete",
        "originalReceipt",
        "cannotRelabelPolicy",
        "currentArithmeticGuard",
        "fromOriginal",
        "allOriginalBytes",
    } <= set(declarations):
        raise RuntimeError("Missing original record obligation")
    audit = "import ProfileVoteRecord\nimport ProfileCurrentJournal\n" + "".join(
        "#print axioms DeltaReduce.ProfileSource.VoteRecord." + name + "\n" for name in declarations
    )
    journal_raw = Path(__file__).with_name("ProfileCurrentJournal.lean").read_text(encoding="utf8")
    journal_declarations = re.findall(r"^(?:def|theorem) (\w+)", journal_raw, re.M)
    if not {
        "fullOriginalInventory",
        "bindComplete",
        "nativeScanAgrees",
        "noRecordOrInputErasure",
        "incompleteRejected",
        "unknownRejected",
    } <= set(journal_declarations):
        raise RuntimeError("Missing full original pointer inventory obligation")
    audit += "".join(
        "#print axioms DeltaReduce.ProfileSource.CurrentJournal." + name + "\n"
        for name in journal_declarations
    )
    (src / "Audit.lean").write_text(audit, encoding="utf8", newline="\n")
    log = run([str(LEAN), "Audit.lean"], "axioms.txt", src, environment)
    if any("DeltaReduce.ProfileSource.VoteRecord." + name not in log for name in declarations):
        raise RuntimeError("Incomplete axiom audit")
    if any(
        "DeltaReduce.ProfileSource.CurrentJournal." + name not in log
        for name in journal_declarations
    ):
        raise RuntimeError("Incomplete original pointer inventory axiom audit")
    for group in re.findall(r"depends on axioms:\s*\[([^]]*)\]", log):
        if set(group.replace(" ", "").replace("\n", "").split(",")) - {
            "propext",
            "Classical.choice",
            "Quot.sound",
            "",
        }:
            raise RuntimeError("Unexpected axiom " + group)
    sources["generated/Audit.lean"] = digest(audit.encode())

    from formal.reference.profile_source.vote_record_vectors import generate

    vectors, originals = generate()
    (src / "VoteRecordVectors.lean").write_text(vectors, encoding="utf8", newline="\n")
    (OUT / "originals.json").write_text(
        json.dumps(originals, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    run([str(LEAN), "VoteRecordVectors.lean"], "kernel-vectors.txt", src, environment)
    sources["generated/VoteRecordVectors.lean"] = digest(vectors.encode())
    # These dummy input descriptors exercise only the inventory alignment.
    # They are never asserted to be admissible snapshots or successful rows.
    inventory = """import ProfileCurrentJournal
open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes
def input : Current.Input := ⟨[],[],[],.end,⟨[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]⟩⟩
example : (CurrentJournal.align [[1],[2],[]] [input,input]).map
    (List.map Prod.fst) = some [[1],[2]] := by decide +kernel
example : (CurrentJournal.align [[1],[2],[]] [input]).isNone = true := by decide +kernel
example : (CurrentJournal.align [[1],[]] [input,input]).isNone = true := by decide +kernel
example : (CurrentJournal.align [[1],[2]] [input]).isNone = true := by decide +kernel
example : (CurrentJournal.align [[]] []).map List.length = some 0 := by decide +kernel
example : (CurrentJournal.align [] []).isNone = true := by decide +kernel
"""
    (src / "PointerInventoryVectors.lean").write_text(inventory, encoding="utf8", newline="\n")
    sources["generated/PointerInventoryVectors.lean"] = digest(inventory.encode())
    run([str(LEAN), "PointerInventoryVectors.lean"], "pointer-inventory.txt", src, environment)
    paths = [
        "formal/reference/profile_source/vote_record_vectors.py",
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
    for path in (
        Path(__file__),
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
        "result": "ORIGINAL_VOTE_RECORD_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "reviewed_r2_closure": False,
        "lean": version,
        "sources": sources,
        "checks": checks,
        "artifacts": {"originals.json": digest((OUT / "originals.json").read_bytes())},
        "audited_declarations": declarations,
        "audited_pointer_inventory_declarations": journal_declarations,
        "established": [
            "Full original kind-2 DRW1, whole policy, candidate, Vote and receipt join",
            "Original current parent, physical sequence, own context and arithmetic guard",
            "Complete original pointer bytes fix every row/input and agree with the existing scan",
            "Unknown/torn required pointer journals reject without lineage truncation",
        ],
        "not_established": [
            "Original producing prefix, barriers or complete source provenance",
            "Whole public state relation/totality, R2.3 closure or named recovery",
        ],
        "source_hash_rule": "Git LF source text; original protocol bytes without normalization",
        "evidence_kind": "SYNTHETIC_ORIGINAL_ROW_NOT_PRODUCER_HISTORY",
    }
    (OUT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(receipt["result"], flush=True)


if __name__ == "__main__":
    main()
