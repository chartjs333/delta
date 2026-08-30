from __future__ import annotations

import json
from pathlib import Path

import pytest
from deltatorrent.cli.main import main

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def test_definition_cli_validates_exact_identity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    artifacts = json.loads(FIXTURE.read_text(encoding="utf-8"))["artifacts"]
    definition = tmp_path / "definition.json"
    definition.write_bytes(
        json.dumps(artifacts["definition"]["value"], separators=(",", ":"), sort_keys=True).encode()
    )
    assert main(("benchmark", "validate-definition", str(definition))) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "definition_id": artifacts["definition"]["content_id"],
        "primary": False,
        "status": "PASS",
    }


def test_synthetic_cli_preserves_non_primary_label(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(("benchmark", "synthetic", str(FIXTURE), str(tmp_path / "run"))) == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["fixture_class"] == "SYNTHETIC_NOT_PRIMARY_EVIDENCE"
    assert result["status"] == "PASS"


def test_definition_cli_rejects_noncanonical_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    definition = tmp_path / "definition.json"
    definition.write_text('{"primary": false}\n', encoding="utf-8")
    assert main(("benchmark", "validate-definition", str(definition))) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.err)["status"] == "REJECTED"
