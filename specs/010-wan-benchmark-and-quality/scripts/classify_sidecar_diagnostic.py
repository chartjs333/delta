#!/usr/bin/env python3
"""Recompute a sealed PR50 diagnostic classification without running a campaign."""

from __future__ import annotations

import argparse
from pathlib import Path

import run_sidecar_diagnostic as runner
import sidecar_diagnostic_common as contract


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_directory", type=Path)
    arguments = parser.parse_args()
    try:
        evidence = runner.verify_evidence_directory(arguments.evidence_directory)
        classification = evidence["campaign_classification"]
        slots = evidence["classified_missed_slots"]
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        contract.DiagnosticError,
    ) as error:
        print(f"sidecar diagnostic evidence invalid: {error}")
        return 1
    print(
        "sidecar diagnostic evidence verified: "
        f"classification={classification} missed_slots={len(slots)} selected_profile=null"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
