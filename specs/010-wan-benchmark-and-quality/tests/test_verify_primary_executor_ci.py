from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_primary_executor_ci.py"
SPEC = importlib.util.spec_from_file_location("verify_primary_executor_ci", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_junit_skip_parser_accepts_only_declared_hardware_lanes(tmp_path: Path) -> None:
    report = tmp_path / "pytest.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite>
<testcase classname="tests.hardware.test_qlora" name="test_complete_physical_ticket">
<skipped message="physical qualification is a dedicated explicit lane" />
</testcase>
</testsuite></testsuites>
""",
        encoding="utf-8",
    )
    assert MODULE.parse_skips(report) == [
        {
            "reason": "physical qualification is a dedicated explicit lane",
            "test_id": "tests.hardware.test_qlora::test_complete_physical_ticket",
        }
    ]


def test_junit_skip_parser_rejects_portable_executor_skip(tmp_path: Path) -> None:
    report = tmp_path / "pytest.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite>
<testcase classname="tests.benchmark.test_primary_executor" name="test_create_only">
<skipped message="unexpected" />
</testcase>
</testsuite></testsuites>
""",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="UNAPPROVED_TEST_SKIP:test_create_only"):
        MODULE.parse_skips(report)


def test_exact_qualification_check_set_is_closed() -> None:
    assert MODULE.REQUIRED_CHECKS == {
        "architecture_guard",
        "cli_round_trip",
        "create_only_concurrency",
        "executor_negative_matrix",
        "formal_regression",
        "format",
        "mypy",
        "production_attacks",
        "pytest",
        "ruff",
    }
