#!/usr/bin/env python3
"""Fail-closed, reproducible projections of TLC success and counterexamples."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from formal_artifacts import canonical_json_bytes

VERSION = re.compile(r"^TLC2 Version (.+?) \(rev: ([0-9a-f]+)\)$", re.MULTILINE)
RUN_HEADER = re.compile(
    r"^Running breadth-first search Model-Checking with fp ([0-9]+) "
    r"and seed ([0-9]+) with ([0-9]+) workers? on .+$",
    re.MULTILINE,
)
FINAL_SUMMARY = re.compile(
    r"^([0-9][0-9,]*) states generated, "
    r"([0-9][0-9,]*) distinct states found, 0 states left on queue\.$",
    re.MULTILINE,
)
DEPTH = re.compile(
    r"^The depth of the complete state graph search is ([0-9][0-9,]*)\.$",
    re.MULTILINE,
)
TOP_LEVEL_ACTION = re.compile(
    r"^<([A-Za-z][A-Za-z0-9_]*)\b[^>]*>:\s+"
    r"([0-9][0-9,]*):([0-9][0-9,]*)$",
    re.MULTILINE,
)
SUCCESS = "Model checking completed. No error has been found."
FAILURE_PATTERNS = (
    re.compile(r"^Error:", re.MULTILINE),
    re.compile(r"\bInvariant [A-Za-z][A-Za-z0-9_]* is violated\."),
    re.compile(r"\bTemporal propert(?:y|ies).*(?:violated|false)", re.IGNORECASE),
    re.compile(r"\bDeadlock reached\."),
    re.compile(r"Exception in thread|java\.[A-Za-z0-9_.]+Exception|Traceback \("),
)
INVARIANT_ERROR = re.compile(
    r"^Error: Invariant ([A-Za-z][A-Za-z0-9_]*) is violated\.$",
    re.MULTILINE,
)
STATE = re.compile(r"^State ([0-9]+): <([^>]+)>$", re.MULTILINE)
INITIAL_STATES = re.compile(
    r"^Finished computing initial states: ([0-9][0-9,]*) distinct states? generated",
    re.MULTILINE,
)
FINISHED = re.compile(r"^Finished in .+$", re.MULTILINE)
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


class TlcResultError(ValueError):
    """TLC output does not prove the required canonical result."""


def _one(pattern: re.Pattern[str], output: str, label: str) -> re.Match[str]:
    matches = list(pattern.finditer(output))
    if len(matches) != 1:
        raise TlcResultError(f"expected exactly one {label}, found {len(matches)}")
    return matches[0]


def _integer(value: str) -> int:
    return int(value.replace(",", ""))


def _verify_identity(
    output: str,
    *,
    expected_version: str,
    expected_revision: str,
    fingerprint_index: int,
    seed: int,
    workers: int,
) -> tuple[re.Match[str], re.Match[str]]:
    version = _one(VERSION, output, "TLC version banner")
    if version.group(1) != expected_version or version.group(2) != expected_revision[:7]:
        raise TlcResultError("TLC version/revision differs from the lock")
    header = _one(RUN_HEADER, output, "TLC run header")
    observed = tuple(int(header.group(index)) for index in range(1, 4))
    expected = (fingerprint_index, seed, workers)
    if observed != expected:
        raise TlcResultError(
            f"TLC fp/seed/workers mismatch: observed={observed}, expected={expected}"
        )
    return version, header


def top_level_action_counts(output: str) -> dict[str, int]:
    """Return unique top-level action invocation counts from TLC coverage."""

    counts: dict[str, int] = {}
    for match in TOP_LEVEL_ACTION.finditer(output):
        action = match.group(1)
        if action in counts:
            raise TlcResultError(f"duplicate top-level TLC coverage row for {action}")
        counts[action] = _integer(match.group(3))
    return counts


def successful_tlc_result(
    output: str,
    *,
    expected_version: str,
    expected_revision: str,
    fingerprint_index: int,
    seed: int,
    workers: int,
    required_actions: list[str],
) -> dict[str, Any]:
    """Project a successful TLC transcript onto correctness-relevant fields."""

    output = output.replace("\r\n", "\n").replace("\r", "\n")
    if output.count(SUCCESS) != 1:
        raise TlcResultError(
            f"expected exactly one TLC success marker, found {output.count(SUCCESS)}"
        )
    for pattern in FAILURE_PATTERNS:
        if pattern.search(output):
            raise TlcResultError(f"TLC success output contains failure marker {pattern.pattern!r}")
    version, header = _verify_identity(
        output,
        expected_version=expected_version,
        expected_revision=expected_revision,
        fingerprint_index=fingerprint_index,
        seed=seed,
        workers=workers,
    )
    summary = _one(FINAL_SUMMARY, output, "anchored final state summary")
    depth_match = _one(DEPTH, output, "complete state-graph depth")
    success_offset = output.index(SUCCESS)
    if not (header.start() < success_offset < summary.start() < depth_match.start()):
        raise TlcResultError("TLC success, summary and depth markers are out of order")

    states = _integer(summary.group(1))
    distinct_states = _integer(summary.group(2))
    diameter = _integer(depth_match.group(1))
    if distinct_states <= 0 or states < distinct_states or diameter < 0:
        raise TlcResultError("invalid TLC state/depth metrics")

    if len(required_actions) != len(set(required_actions)):
        raise TlcResultError("required TLC action list contains duplicates")
    action_counts = top_level_action_counts(output)
    reached: dict[str, bool] = {}
    for action in sorted(required_actions):
        count = action_counts.get(action)
        if count is None:
            raise TlcResultError(f"TLC action coverage missing for {action}")
        if count <= 0:
            raise TlcResultError(f"TLC action coverage is zero for {action}")
        reached[action] = True

    return {
        "schema_version": "1.0.0",
        "outcome": "NO_ERROR",
        "tlc_version": version.group(1),
        "tlc_revision": version.group(2),
        "fingerprint_index": fingerprint_index,
        "seed": seed,
        "workers": workers,
        "states": states,
        "distinct_states": distinct_states,
        "diameter": diameter,
        "required_action_reached": reached,
    }


def result_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _basename(path_text: str) -> str:
    return re.split(r"[\\/]", path_text.strip())[-1]


def sanitize_counterexample_output(output: str) -> str:
    """Remove only documented runtime metadata while retaining state valuations."""

    normalized = output.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for raw_line in normalized.splitlines():
        line = raw_line.rstrip()
        if line.startswith("Progress("):
            continue
        if line.startswith("Running breadth-first search Model-Checking with fp "):
            match = RUN_HEADER.fullmatch(line)
            if match is None:
                raise TlcResultError("malformed TLC run header")
            line = (
                "Running breadth-first search Model-Checking with fp "
                f"{match.group(1)} and seed {match.group(2)} with "
                f"{match.group(3)} worker(s) on <runtime-metadata>."
            )
        elif line.startswith("Parsing file "):
            line = f"Parsing file <{_basename(line[len('Parsing file ') :])}>"
        line = TIMESTAMP.sub("<timestamp>", line)
        if line.startswith("Finished in "):
            line = re.sub(r"^Finished in .+? at ", "Finished in <elapsed> at ", line)
        elif line.startswith("Finished checking temporal properties in "):
            line = re.sub(
                r"^Finished checking temporal properties in .+? at ",
                "Finished checking temporal properties in <elapsed> at ",
                line,
            )
        lines.append(line)
    return "\n".join(lines).rstrip("\n") + "\n"


def mutant_tlc_result(
    output: str,
    *,
    return_code: int,
    expected_invariant: str,
    expected_version: str,
    expected_revision: str,
    fingerprint_index: int,
    seed: int,
    workers: int,
) -> dict[str, Any]:
    """Validate and project an intended invariant counterexample."""

    output = output.replace("\r\n", "\n").replace("\r", "\n")
    if return_code != 12:
        raise TlcResultError(
            f"mutant TLC run returned {return_code}, expected invariant-violation code 12"
        )
    _verify_identity(
        output,
        expected_version=expected_version,
        expected_revision=expected_revision,
        fingerprint_index=fingerprint_index,
        seed=seed,
        workers=workers,
    )
    violations = INVARIANT_ERROR.findall(output)
    if violations != [expected_invariant]:
        raise TlcResultError(f"expected only invariant {expected_invariant}, observed {violations}")
    allowed_errors = {
        f"Error: Invariant {expected_invariant} is violated.",
        "Error: The behavior up to this point is:",
    }
    error_lines = {line.strip() for line in output.splitlines() if line.startswith("Error:")}
    if not error_lines or not error_lines <= allowed_errors:
        raise TlcResultError(f"unexpected TLC counterexample error lines: {sorted(error_lines)}")
    if re.search(r"Exception in thread|java\.[A-Za-z0-9_.]+Exception|Traceback \(", output):
        raise TlcResultError("counterexample output contains an unexpected exception")
    if SUCCESS in output:
        raise TlcResultError("counterexample output also contains a TLC success marker")
    initial = _one(INITIAL_STATES, output, "non-vacuous initial-state summary")
    if _integer(initial.group(1)) <= 0:
        raise TlcResultError("mutant model has no initial states")

    state_matches = list(STATE.finditer(output))
    numbers = [int(match.group(1)) for match in state_matches]
    if not numbers or numbers != list(range(1, len(numbers) + 1)):
        raise TlcResultError("counterexample state numbers are empty or non-contiguous")
    trace = [match.group(2).strip() for match in state_matches]
    if trace[0] != "Initial predicate":
        raise TlcResultError("counterexample does not begin with the initial predicate")
    finished = _one(FINISHED, output, "TLC counterexample completion marker")
    if finished.start() < state_matches[-1].end():
        raise TlcResultError("TLC counterexample completion marker precedes its trace")

    sanitized = sanitize_counterexample_output(output)
    return {
        "schema_version": "1.0.0",
        "outcome": "EXPECTED_INVARIANT_VIOLATION",
        "violated_invariant": expected_invariant,
        "fingerprint_index": fingerprint_index,
        "seed": seed,
        "workers": workers,
        "normalized_trace": trace,
        "normalized_output_sha256": hashlib.sha256(sanitized.encode("utf-8")).hexdigest(),
    }
