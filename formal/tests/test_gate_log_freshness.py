from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / "formal" / "scripts"))

import run_formal_gate as gate  # noqa: E402
from test_tlc_results import parse_success, successful_output  # noqa: E402
from tlc_results import TlcResultError  # noqa: E402


class GateLogFreshnessTests(unittest.TestCase):
    def test_timeout_replaces_old_pass_even_when_partial_output_claims_success(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "tlc.log"
            log.write_text(successful_output(), encoding="utf-8")
            timeout = subprocess.TimeoutExpired(
                ["java"], 1, output=successful_output().encode(), stderr=b"diagnostic"
            )
            with patch.object(gate.subprocess, "run", side_effect=timeout):
                with self.assertRaises(subprocess.TimeoutExpired):
                    gate.run_capture(
                        ["java"], cwd=Path(directory), timeout=1, echo=False, output_path=log
                    )
            result = log.read_text(encoding="utf-8")
            self.assertIn("diagnostic", result)
            self.assertIn("process timeout", result)
            with self.assertRaises(TlcResultError):
                parse_success(result)

    def test_nonzero_exit_retains_diagnostic_and_cannot_be_reused_as_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "tlc.log"
            process = subprocess.CompletedProcess(["java"], 1, successful_output(), "crash")
            with patch.object(gate.subprocess, "run", return_value=process):
                with self.assertRaises(subprocess.CalledProcessError):
                    gate.run_capture(
                        ["java"], cwd=Path(directory), timeout=1, echo=False, output_path=log
                    )
            result = log.read_text(encoding="utf-8")
            self.assertIn("crash", result)
            with self.assertRaises(TlcResultError):
                parse_success(result)

    def test_launch_failure_invalidates_old_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "tlc.log"
            log.write_text(successful_output(), encoding="utf-8")
            with patch.object(gate.subprocess, "run", side_effect=FileNotFoundError):
                with self.assertRaises(FileNotFoundError):
                    gate.run_capture(
                        ["java"], cwd=Path(directory), timeout=1, echo=False, output_path=log
                    )
            with self.assertRaises(TlcResultError):
                parse_success(log.read_text(encoding="utf-8"))

    def test_entire_gate_invalidated_before_first_process_can_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            configs = [{"id": "FIRST"}, {"id": "LATER"}]
            for config in configs:
                log = root / "formal" / "build" / "tlc" / config["id"] / "tlc.log"
                log.parent.mkdir(parents=True)
                log.write_text(successful_output(), encoding="utf-8")
            with patch.object(gate, "ROOT", root):
                gate.invalidate_tlc_logs(configs)
            for config in configs:
                log = root / "formal" / "build" / "tlc" / config["id"] / "tlc.log"
                with self.assertRaises(TlcResultError):
                    parse_success(log.read_text(encoding="utf-8"))

    def test_success_still_produces_valid_semantic_result(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "tlc.log"
            process = subprocess.CompletedProcess(["java"], 0, successful_output(), "")
            with patch.object(gate.subprocess, "run", return_value=process):
                gate.run_capture(
                    ["java"], cwd=Path(directory), timeout=1, echo=False, output_path=log
                )
            self.assertEqual(parse_success(log.read_text(encoding="utf-8"))["states"], 10)


if __name__ == "__main__":
    unittest.main()
