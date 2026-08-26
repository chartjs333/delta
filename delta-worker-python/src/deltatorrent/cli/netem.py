"""Deterministic unprivileged netem smoke command."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from deltatorrent.adapters.netem.simulated import SimulatedFaultyStream
from deltatorrent.domain.network import NetworkProfile


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="netem_command", required=True)
    smoke = commands.add_parser("smoke", help="emit a deterministic logical fault schedule")
    smoke.add_argument("profile", type=Path)


def execute(args: argparse.Namespace) -> int:
    profile = NetworkProfile.from_json_file(args.profile)
    frames = tuple((index * 7, f"frame-{index}".encode()) for index in range(8))
    schedule = SimulatedFaultyStream(profile).transmit_stream(frames)
    result = {
        "delivered": sum(item.payload is not None for item in schedule),
        "profile_id": profile.profile_id,
        "schedule": [item.to_dict() for item in schedule],
        "schedule_id": "sha256:"
        + hashlib.sha256(
            json.dumps(
                [item.to_dict() for item in schedule], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "schema_version": "1.0.0",
        "status": "PASS",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0
