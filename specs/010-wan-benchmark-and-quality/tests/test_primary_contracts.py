from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/primary_contracts.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("primary_contracts", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_primary_definition_is_complete_before_execution() -> None:
    module = load_script()
    commit = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    outputs = module.expected_outputs(commit)
    definition = json.loads(outputs[module.OUTPUT_ROOT / "primary.yaml"])
    assert definition["primary"] is True
    assert definition["decision_function"] == "ALL_MANDATORY"
    assert definition["missing_run_policy"] == "FAIL_CLOSED"
    assert definition["isolation_policy"] == "COMPARE_BOTH"
    assert len(definition["arm_ids"]) == 5
    assert len(definition["network_profile_ids"]) == 4
    assert len(definition["seeds"]) == definition["repetitions"] == 3
    metric_ids = {item["metric_id"] for item in definition["metric_definitions"]}
    assert {
        "validation_loss_micro",
        "downstream_lambada_accuracy_ppm",
        "post_training_hellaswag_accuracy_ppm",
        "per_domain_wikitext_loss_micro",
    } <= metric_ids


def test_external_dependencies_are_immutable_and_licensed() -> None:
    dependencies = load_script().external_dependencies()
    for artifact in dependencies["artifacts"]:
        assert len(artifact["revision"]) == 40
        assert artifact["license"]
        if "sha256" in artifact:
            assert len(artifact["sha256"]) == 64
