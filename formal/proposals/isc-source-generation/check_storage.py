"""T047/T053: reproducible scope11 storage-byte component evidence, not GO."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "formal/proposals/evidence/storage-source-v1"
CONTRACTS = [
    (
        "1438fa3d78ec99291475cf4660fd8c190ac01bb3",
        "docs/adr/0016-storage-availability-source-binding-v1.md",
    ),
    (
        "90561a97de7f41f409bf22065ad6cdc9b3932458",
        "docs/adr/0018-authenticated-availability-contract-v1.md",
    ),
    (
        "85ba58e483db34a778673743885343b1264132d2",
        "orchestration/sprints/isc-s16-continuous/scope-requests/ISC-S16-R23-O-AUTHENTICATED-AVAILABILITY-CONTRACT.json",
    ),
]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    contracts = []
    for commit, path in CONTRACTS:
        raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        contracts.append({"commit": commit, "path": path, "sha256": digest(raw)})
    assert (
        contracts[1]["sha256"] == "4b5c91196b63644dc472954447e9b1426cbf88055f78a5d49eb903821780b0d5"
    )
    assert (
        contracts[2]["sha256"] == "d13cc05328c418d145cf0cc2fdf96bd3c69fef3c1f8b1b1477f1dc4f104de8e8"
    )
    commands = [
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
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "formal/reference/storage_source",
            str(Path(__file__).relative_to(ROOT)),
        ],
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            "formal/reference/storage_source",
            str(Path(__file__).relative_to(ROOT)),
        ],
    ]
    results = []
    for i, command in enumerate(commands):
        run = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, encoding="utf8", timeout=120
        )
        log = run.stdout + run.stderr
        name = f"check-{i}.txt"
        (OUT / name).write_text(log, encoding="utf8", newline="\n")
        results.append(
            {
                "command": command[1:],
                "exit_code": run.returncode,
                "log": name,
                "sha256": digest(log.encode()),
            }
        )
        if run.returncode:
            raise RuntimeError(log)
    inputs = [
        *sorted((ROOT / "formal/reference/storage_source").glob("*.py")),
        ROOT / "formal/reference/storage_source/README.md",
        Path(__file__),
        ROOT / "formal/reference/isc_crypto/codec.py",
        ROOT / "formal/reference/isc_crypto/sodium_reference.py",
        ROOT / "formal/reference/isc_crypto/library-provenance.json",
    ]
    dll = Path(os.environ["ISC_SODIUM_DLL"])
    pin = json.loads((ROOT / "formal/reference/isc_crypto/library-provenance.json").read_text())
    assert digest(dll.read_bytes()) == pin["dll"]["sha256"]
    result = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 11,
        "decision_id": "scope-decision-e5c12ebc8342d99630d5fcf28a9c6753",
        "ack_id": "scope-ack-a07a96b9126f50c24a663f2b99658f95",
        "result": "STORAGE_AUTHENTICATION_COMPONENT_CHECKED",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "contracts": contracts,
        "checks": results,
        "backend_sha256": pin["dll"]["sha256"],
        "source_hash_rule": (
            "Git-compatible LF normalization for source text only; "
            "original protocol/signature bytes are never normalized."
        ),
        "sources": {
            p.relative_to(ROOT).as_posix(): digest(p.read_bytes().replace(b"\r\n", b"\n"))
            for p in inputs
        },
        "residual": (
            "Derive Context and complete original prefix from independently checked "
            "source/configuration/ticket/commitment/manifest history, then full O "
            "source/public-state composition and applicable gates. "
            "Byte authentication alone establishes none of those premises."
        ),
        "limits": [
            "Synthetic conformance, not production capture or independent attestation.",
            "No physical availability inference or complete source/budget qualification.",
            "No refinement result, Lean/TLA claim, recovery theorem, production change or sigma.",
        ],
    }
    (OUT / "receipt.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(result["result"])


if __name__ == "__main__":
    main()
