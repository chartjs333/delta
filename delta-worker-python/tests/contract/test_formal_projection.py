from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "delta-worker-python" / "tests" / "fixtures" / "formal" / "001"
CHECKER = ROOT / "formal" / "scripts" / "check-refinement.py"


def load_reference(name: str) -> tuple[dict[str, Any], Path]:
    reference = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    source = ROOT / reference["source"]
    assert source.is_file()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == reference["sha256"]
    assert reference["formal_semantics_id"] == FORMAL_SEMANTICS_ID
    return reference, source


def run_checker(source: Path) -> tuple[int, dict[str, Any]]:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD", "formal"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    assert archive.returncode == 0
    with tempfile.TemporaryDirectory(prefix="delta-refinement-") as directory:
        snapshot = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
            bundle.extractall(snapshot, filter="data")
        snapshot_checker = snapshot / CHECKER.relative_to(ROOT)
        snapshot_source = snapshot / source.relative_to(ROOT)
        completed = subprocess.run(
            [sys.executable, str(snapshot_checker), str(snapshot_source)],
            cwd=snapshot,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    assert completed.stderr == ""
    return completed.returncode, json.loads(completed.stdout)


def test_identity_preserving_artifact_repair_refines() -> None:
    reference, source = load_reference("legal-artifact-repair.ref.json")
    code, result = run_checker(source)
    assert code == 0
    assert result["status"] == reference["expected_status"]
    assert result["trace_id"] == "TRACE-ARTIFACT-REPAIR"


def test_partial_artifact_publication_is_rejected() -> None:
    reference, source = load_reference("illegal-partial-publication.ref.json")
    code, result = run_checker(source)
    assert code == 1
    assert result["status"] == reference["expected_status"]
    assert reference["expected_error"] in result["error"]
