from __future__ import annotations

import os
from pathlib import Path

import pytest
from deltatorrent.qlora.qualification import (
    load_profile,
    probe_gpu,
    run_physical_qualification,
    validate_physical_readiness,
)

ROOT = Path(__file__).parents[3]
PROFILE = ROOT / "configs" / "qlora" / "8gb-reference.json"


def test_frozen_physical_profile_matches_designated_gpu() -> None:
    profile = load_profile(PROFILE)
    validate_physical_readiness(profile, probe_gpu())


@pytest.mark.skipif(
    os.environ.get("DELTA_QLORA_PHYSICAL") != "1",
    reason="physical qualification is a dedicated explicit lane",
)
def test_complete_physical_ticket() -> None:
    report = run_physical_qualification(
        PROFILE,
        ROOT / "out" / "build" / "cpp20" / "Debug" / "delta_ffi.dll",
    )
    assert report["status"] == "PASS"
    assert report["claim"]["eligible"] is True
    assert report["ticket"]["actual_optimizer_steps"] == report["ticket"]["fixed_H"]
    assert report["base"]["hash_before"] == report["base"]["hash_after"]
