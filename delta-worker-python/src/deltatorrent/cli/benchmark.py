"""Operational commands for immutable feature-010 benchmark artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from deltatorrent.benchmark.definition import (
    FORMAL_SEMANTICS_ID,
    BenchmarkDefinition,
    load_definition,
)
from deltatorrent.benchmark.preregistration import (
    PreregisteredDefinition,
    PreregistrationStore,
)
from deltatorrent.benchmark.report import parse_machine_report
from deltatorrent.benchmark.review import GovernanceAttestation
from deltatorrent.benchmark.synthetic import execute_synthetic_fixture
from deltatorrent.protocol.canonical import canonical_json_bytes


class BenchmarkCliError(ValueError):
    """Stable benchmark CLI rejection."""


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="benchmark_command", required=True)

    validate = commands.add_parser("validate-definition", help="validate and identify a definition")
    validate.add_argument("definition", type=Path)

    preregister = commands.add_parser(
        "preregister", help="seal a definition with an existing governance attestation"
    )
    preregister.add_argument("definition", type=Path)
    preregister.add_argument("attestation", type=Path)
    preregister.add_argument("store", type=Path)

    synthetic = commands.add_parser(
        "synthetic", help="run the explicitly non-primary deterministic vertical slice"
    )
    synthetic.add_argument("fixture", type=Path)
    synthetic.add_argument("output", type=Path)

    verify_report = commands.add_parser(
        "verify-report", help="verify canonical machine-report encoding"
    )
    verify_report.add_argument("report", type=Path)


def _load_object(path: Path, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchmarkCliError(code) from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise BenchmarkCliError(code)
    return value


def _attestation(path: Path, definition: BenchmarkDefinition) -> GovernanceAttestation:
    value = _load_object(path, "BENCHMARK_ATTESTATION_INVALID")
    expected = {
        "benchmark_definition_id",
        "f_b",
        "formal_semantics_id",
        "governance_only",
        "ordered_signers",
        "quorum_threshold",
        "schema_version",
        "type_name",
        "validator_set_id",
    }
    if (
        set(value) != expected
        or value["type_name"] != "BENCHMARK_DEFINITION_ATTESTATION"
        or value["benchmark_definition_id"] != definition.content_id
        or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
        or value["schema_version"] != "1.0.0"
        or value["governance_only"] is not True
    ):
        raise BenchmarkCliError("BENCHMARK_ATTESTATION_INVALID")
    signers = value["ordered_signers"]
    f_b = value["f_b"]
    if (
        isinstance(f_b, bool)
        or not isinstance(f_b, int)
        or f_b < 0
        or not isinstance(signers, list)
        or any(not isinstance(item, str) or not item for item in signers)
        or signers != sorted(set(signers))
        or value["quorum_threshold"] != 2 * f_b + 1
        or len(signers) < 2 * f_b + 1
    ):
        raise BenchmarkCliError("BENCHMARK_ATTESTATION_INVALID")
    validator_set_id = value["validator_set_id"]
    if (
        not isinstance(validator_set_id, str)
        or not validator_set_id.startswith("sha256:")
        or len(validator_set_id) != 71
    ):
        raise BenchmarkCliError("BENCHMARK_ATTESTATION_INVALID")
    return GovernanceAttestation(
        body_id=definition.content_id,
        validator_set_id=validator_set_id,
        purpose="DEFINITION",
        f_b=f_b,
        ordered_signers=tuple(signers),
    )


def execute(args: argparse.Namespace) -> int:
    try:
        if args.benchmark_command == "validate-definition":
            definition = load_definition(args.definition)
            print(
                json.dumps(
                    {
                        "definition_id": definition.content_id,
                        "primary": definition.primary,
                        "status": "PASS",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            return 0
        if args.benchmark_command == "preregister":
            definition = load_definition(args.definition)
            attestation = _attestation(args.attestation, definition)
            target = PreregistrationStore(args.store).seal(
                PreregisteredDefinition(definition, attestation)
            )
            print(
                json.dumps(
                    {
                        "definition_id": definition.content_id,
                        "path": target.as_posix(),
                        "status": "PASS",
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            return 0
        if args.benchmark_command == "synthetic":
            result = execute_synthetic_fixture(args.fixture, args.output)
            print(
                json.dumps(
                    {
                        "decision": result.benchmark_result.decision,
                        "fixture_class": result.fixture_class,
                        "run_count": result.run_count,
                        "status": result.verification.status,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            return 0
        if args.benchmark_command == "verify-report":
            report = parse_machine_report(args.report.read_bytes())
            print(
                json.dumps(
                    {"decision": report.get("decision"), "status": "PASS"},
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            return 0
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {"code": str(error), "status": "REJECTED"},
                separators=(",", ":"),
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    return 2
