from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/008-certificates-and-consensus/scripts"


def load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_refinement_trace_is_applied_and_uses_formal_action_ids() -> None:
    traces = load("generate_refinement_traces").build()
    legal = traces["legal-full-chain.json"]
    actions = [event["action_id"] for event in legal["events"]]
    assert legal["terminal_outcome"] == "APPLIED"
    assert actions[0:4] == [
        "ACT-ISC-FINALIZE",
        "ACT-SEED-GENERATE",
        "ACT-EC-FINALIZE",
        "ACT-APC-FINALIZE",
    ]
    assert actions[-3:] == [
        "ACT-ROOT-FINALIZE",
        "ACT-APPLY-FINALIZE",
        "ACT-CURRENT-ADVANCE",
    ]


def test_refinement_negative_set_is_closed() -> None:
    traces = load("generate_refinement_traces").build()
    rejected = [document for document in traces.values() if document["accepted"] is False]
    assert len(traces) == 9
    assert len(rejected) == 7
    assert all(
        document["formal_fixture"].startswith("formal/fixtures/traces/illegal/")
        for document in rejected
    )
