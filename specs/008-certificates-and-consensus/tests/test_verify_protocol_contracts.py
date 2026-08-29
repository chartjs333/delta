from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/008-certificates-and-consensus/scripts/verify_protocol_contracts.py"


def load_verifier():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location("feature008_contract_evidence", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preflight_is_exact_and_passed() -> None:
    module = load_verifier()
    result = module.verify_preflight()
    assert result["status"] == "PASS"
    assert len(result["commit"]) == 40


def test_contract_outputs_cover_eleven_schemas_and_three_fixtures() -> None:
    module = load_verifier()
    contracts = module.load_contracts()
    outputs = contracts.build_outputs()
    assert len(contracts.SCHEMAS) == 11
    assert len([path for path in outputs if path.startswith("fixtures/008/")]) == 3
    assert contracts.validate_outputs(outputs)["status"] == "PASS"
