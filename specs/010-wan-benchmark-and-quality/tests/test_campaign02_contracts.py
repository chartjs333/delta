from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

from deltatorrent.benchmark.gpu_environment import verify_gpu_environment_outputs

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("campaign02_contracts", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_campaign02_schema_and_registry_outputs_are_exact() -> None:
    module = load_script()
    outputs = module.expected_outputs()
    assert len(module.SCHEMAS) == 8
    assert all(path.read_bytes() == expected for path, expected in outputs.items())
    registry = json.loads(module.REGISTRY_PATH.read_bytes())
    assert registry["registry_version"] == "010.2.1-remediation"
    assert len(registry["fixtures"]) == 6
    assert registry["semantic_completeness_claimed"] is False
    observation = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/observation-v2.json").read_bytes()
    )
    assert len(observation["oneOf"]) == 2
    assert len(observation["properties"]["run_result"]["oneOf"]) == 2
    ticket = observation["properties"]["ticket_results"]["items"]
    assert "checkpoint_id" not in ticket["properties"]
    assert "certificate_ids" not in ticket["properties"]
    execution_plan = json.loads(
        (ROOT / "delta-protocol/schemas/010/campaign-02/execution-plan-v2.json").read_bytes()
    )
    assert len(execution_plan["oneOf"]) == 2


def test_gpu_environment_has_separate_hash_locked_platforms_and_cpu_lock() -> None:
    lock = verify_gpu_environment_outputs(ROOT)
    assert lock.document["python"] == "3.12.1"
    assert lock.document["cuda_runtime_id"] == "CUDA_12.4"
    assert lock.document["immutable_resolution"] is True
    assert lock.document["scientific_use"] is True
    assert len(lock.document["platform_locks"]) == 2
    assert lock.sbom["portable_cpu_lock_scientific_use"] is False
    assert lock.document["required_packages"] == {
        "accelerate": "1.14.0",
        "bitsandbytes": "0.50.2",
        "huggingface_hub": "1.29.0",
        "peft": "0.20.0",
        "torch": "2.6.0+cu124",
        "transformers": "5.16.1",
    }


def test_campaign01_closure_and_campaign02_authorization_fail_closed() -> None:
    closure = json.loads(
        (
            ROOT
            / "reports/benchmark/campaigns"
            / "dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
            / "closure.json"
        ).read_bytes()
    )
    authorization = json.loads(
        (
            ROOT / "reports/benchmark/campaigns/campaign-02/remediation-authorization.json"
        ).read_bytes()
    )
    assert closure["status"] == "TERMINATED_NO_GO_AFTER_STAGE_A_BEFORE_SCIENTIFIC_EXECUTION"
    assert closure["primary_scientific_execution_count"] == 0
    assert closure["stage_a_transferable_to_new_campaign"] is False
    assert authorization["status"] == "APPROVED_DESIGN_AND_QUALIFICATION_ONLY"
    assert authorization["old_stage_a_reusable"] is False
    assert authorization["primary_execution_authorized"] is False
    assert authorization["stage_c_authorized"] is False
    assert authorization["real_wan_authorized"] is False
    assert authorization["benchmark_result_qc_authorized"] is False
    assert authorization["feature_011_authorized"] is False
