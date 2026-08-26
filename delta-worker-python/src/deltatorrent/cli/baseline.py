"""Baseline run and resume CLI adapters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.runner import run_baseline


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="baseline_command", required=True)
    run = commands.add_parser("run", help="run a deterministic baseline")
    run.add_argument("config", type=Path)
    resume = commands.add_parser("resume", help="resume from an optimizer-step checkpoint")
    resume.add_argument("config", type=Path)
    resume.add_argument("checkpoint_manifest", type=Path)


def execute(args: argparse.Namespace, repository_root: Path) -> int:
    config = BaselineConfig.from_json_file(args.config)
    checkpoint = args.checkpoint_manifest if args.baseline_command == "resume" else None
    result = run_baseline(config, repository_root=repository_root, resume_checkpoint=checkpoint)
    print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0
