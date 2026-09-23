from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / "formal" / "scripts"))

from tlc_results import (  # noqa: E402
    TlcResultError,
    mutant_tlc_result,
    result_sha256,
    successful_tlc_result,
)

VERSION = "2.19 of 08 August 2024"
REVISION = "5a47802b5c391f59ecdd44117981f4ff8c0656ba"


def successful_output(
    *,
    pid: int = 10,
    timestamp: str = "2026-09-20 01:02:03",
    action_count: int = 2,
    depth: int = 4,
    extra: str = "",
) -> str:
    return (
        "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n"
        "Running breadth-first search Model-Checking with fp 7 and seed 42 with "
        f"1 worker on 8 cores with 1024MB heap [pid: {pid}] (Linux host).\n"
        f"Starting... ({timestamp})\n"
        f"Progress(3) at {timestamp}: 9 states generated, 4 distinct states found, "
        "1 states left on queue.\n"
        "Model checking completed. No error has been found.\n"
        f"The coverage statistics at {timestamp}\n"
        f"<RequiredAction line 1, col 1 to line 1, col 2 of module M>: 1:{action_count}\n"
        "End of statistics.\n"
        "10 states generated, 5 distinct states found, 0 states left on queue.\n"
        f"The depth of the complete state graph search is {depth}.\n"
        f"{extra}"
        f"Finished in 01s at ({timestamp})\n"
    )


def parse_success(output: str) -> dict[str, object]:
    return successful_tlc_result(
        output,
        expected_version=VERSION,
        expected_revision=REVISION,
        fingerprint_index=7,
        seed=42,
        workers=1,
        required_actions=["RequiredAction"],
    )


def mutant_output(
    *,
    prefix: str = "/tmp/run-a",
    pid: int = 10,
    timestamp: str = "2026-09-20 01:02:03",
    elapsed: str = "01s",
    second_state: int = 2,
    invariant: str = "Safe",
    value: int = 1,
    extra: str = "",
) -> str:
    return (
        "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)\n"
        "Running breadth-first search Model-Checking with fp 3 and seed 99 with "
        f"1 worker on 8 cores with 1024MB heap [pid: {pid}] (Linux host).\n"
        f"Parsing file {prefix}/M.tla\n"
        f"Starting... ({timestamp})\n"
        f"Finished computing initial states: 1 distinct state generated at {timestamp}.\n"
        f"Error: Invariant {invariant} is violated.\n"
        "Error: The behavior up to this point is:\n"
        "State 1: <Initial predicate>\n"
        "/\\ x = 0\n"
        f"State {second_state}: <BadAction line 1, col 1 to line 1, col 2 of module M>\n"
        f"/\\ x = {value}\n"
        f"{extra}"
        f"Finished in {elapsed} at ({timestamp})\n"
    )


def parse_mutant(output: str) -> dict[str, object]:
    return mutant_tlc_result(
        output,
        return_code=12,
        expected_invariant="Safe",
        expected_version=VERSION,
        expected_revision=REVISION,
        fingerprint_index=3,
        seed=99,
        workers=1,
    )


class SuccessfulTlcResultTests(unittest.TestCase):
    def test_periodic_coverage_uses_final_snapshot(self) -> None:
        output = successful_output(action_count=7)
        periodic = ("The coverage statistics at 2026-09-20 01:02:02\n"
                    "<RequiredAction line 1, col 1 to line 1, col 2 of module M>: 0:0\n"
                    "End of statistics.\n")
        output = output.replace("Model checking completed.", periodic + "Model checking completed.")
        self.assertEqual(parse_success(output), parse_success(successful_output()))

    def test_periodic_snapshot_cannot_hide_missing_final_coverage(self) -> None:
        output = successful_output()
        start = output.index("The coverage statistics at")
        end = output.index("End of statistics.") + len("End of statistics.\n")
        coverage = output[start:end]
        output = output[:start] + output[end:]
        output = output.replace("Model checking completed.", coverage + "Model checking completed.")
        with self.assertRaisesRegex(TlcResultError, "missing final TLC coverage"):
            parse_success(output)

    def test_duplicate_within_coverage_snapshot_is_rejected(self) -> None:
        output = successful_output().replace("End of statistics.",
                "<RequiredAction line 1, col 1 to line 1, col 2 of module M>: 1:3\nEnd of statistics.")
        with self.assertRaisesRegex(TlcResultError, "duplicate top-level"):
            parse_success(output)

    def test_incomplete_snapshot_is_rejected(self) -> None:
        with self.assertRaisesRegex(TlcResultError, "incomplete TLC coverage"):
            parse_success(successful_output().replace("End of statistics.\n", ""))

    def test_cumulative_snapshot_regression_is_rejected(self) -> None:
        periodic = ("The coverage statistics at earlier\n"
                    "<RequiredAction line 1, col 1 to line 1, col 2 of module M>: 1:999\n"
                    "End of statistics.\n")
        with self.assertRaisesRegex(TlcResultError, "regressed"):
            parse_success(successful_output().replace("Model checking completed.",
                                                      periodic + "Model checking completed."))

    def test_runtime_noise_and_positive_coverage_counts_do_not_change_hash(self) -> None:
        first = parse_success(successful_output())
        second = parse_success(
            successful_output(
                pid=999,
                timestamp="2026-09-20 05:06:07",
                action_count=17,
            ).replace("\n", "\r\n")
        )
        self.assertEqual(first, second)
        self.assertEqual(result_sha256(first), result_sha256(second))
        self.assertEqual(first["required_action_reached"], {"RequiredAction": True})

    def test_semantic_metric_change_changes_hash(self) -> None:
        self.assertNotEqual(
            result_sha256(parse_success(successful_output(depth=4))),
            result_sha256(parse_success(successful_output(depth=5))),
        )

    def test_short_or_wrong_tlc_revision_rejects(self) -> None:
        with self.assertRaises(TlcResultError):
            parse_success(successful_output().replace("(rev: 5a47802)", "(rev: 5)"))
        with self.assertRaises(TlcResultError):
            parse_success(successful_output().replace("(rev: 5a47802)", "(rev: 0000000)"))

    def test_missing_zero_duplicate_and_failure_markers_reject(self) -> None:
        with self.assertRaises(TlcResultError):
            parse_success(successful_output(action_count=0))
        with self.assertRaises(TlcResultError):
            parse_success(successful_output().replace("<RequiredAction", "<OtherAction"))
        duplicate = successful_output().replace(
            "End of statistics.",
            "<RequiredAction line 2, col 1 to line 2, col 2 of module M>: 1:3\nEnd of statistics.",
        )
        with self.assertRaises(TlcResultError):
            parse_success(duplicate)
        with self.assertRaises(TlcResultError):
            parse_success(successful_output(extra="Error: unexpected failure\n"))

    def test_duplicate_final_summary_rejects_progress_lookalikes_safely(self) -> None:
        duplicate = successful_output().replace(
            "The depth of the complete state graph search is 4.",
            "10 states generated, 5 distinct states found, 0 states left on queue.\n"
            "The depth of the complete state graph search is 4.",
        )
        with self.assertRaises(TlcResultError):
            parse_success(duplicate)


class MutantTlcResultTests(unittest.TestCase):
    def test_runtime_paths_pid_time_and_duration_do_not_change_full_output_hash(self) -> None:
        first = parse_mutant(mutant_output())
        second = parse_mutant(
            mutant_output(
                prefix=r"C:\\Temp\\run-b",
                pid=999,
                timestamp="2026-09-20 05:06:07",
                elapsed="00s",
            ).replace("\n", "\r\n")
        )
        self.assertEqual(first, second)
        self.assertEqual(
            first["normalized_trace"],
            ["Initial predicate", "BadAction line 1, col 1 to line 1, col 2 of module M"],
        )

    def test_state_valuation_change_remains_hash_significant(self) -> None:
        first = parse_mutant(mutant_output(value=1))
        second = parse_mutant(mutant_output(value=2))
        self.assertNotEqual(first["normalized_output_sha256"], second["normalized_output_sha256"])

    def test_wrong_invariant_noncontiguous_trace_and_exception_reject(self) -> None:
        with self.assertRaises(TlcResultError):
            parse_mutant(mutant_output(invariant="Wrong"))
        with self.assertRaises(TlcResultError):
            parse_mutant(mutant_output(second_state=3))
        with self.assertRaises(TlcResultError):
            parse_mutant(mutant_output(extra="Exception in thread main\n"))

    def test_wrong_exit_truncation_and_success_marker_reject(self) -> None:
        arguments = {
            "expected_invariant": "Safe",
            "expected_version": VERSION,
            "expected_revision": REVISION,
            "fingerprint_index": 3,
            "seed": 99,
            "workers": 1,
        }
        with self.assertRaises(TlcResultError):
            mutant_tlc_result(mutant_output(), return_code=1, **arguments)
        truncated = mutant_output().split("Finished in", maxsplit=1)[0]
        with self.assertRaises(TlcResultError):
            mutant_tlc_result(truncated, return_code=12, **arguments)
        with self.assertRaises(TlcResultError):
            mutant_tlc_result(
                mutant_output(extra="Model checking completed. No error has been found.\n"),
                return_code=12,
                **arguments,
            )


if __name__ == "__main__":
    unittest.main()
