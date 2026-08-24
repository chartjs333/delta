#!/usr/bin/env python3
"""Offline verifier for a canonical DeltaReduce FormalVerificationReport."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from formal_artifacts import (
    CanonicalJsonError,
    SchemaValidationError,
    verify_report_document,
)


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--require-go", action="store_true")
    arguments = parser.parse_args()

    try:
        result = verify_report_document(
            arguments.report.resolve(), arguments.root.resolve(), require_go=arguments.require_go
        )
    except (
        CanonicalJsonError,
        SchemaValidationError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        result: dict[str, Any] = {
            "schema_version": "1.0.0",
            "status": "FAIL",
            "decision": "NO_GO",
            "errors": [f"{type(error).__name__}:{error}"],
        }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
