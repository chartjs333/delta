"""Thin command-line composition boundary for the worker package."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from deltatorrent import __version__
from deltatorrent.cli import artifacts, baseline, netem, qlora, worker
from deltatorrent.domain.errors import DeltaError
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="delta")
    parser.add_argument("--version", action="version", version=__version__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("formal-id", help="print the accepted formal semantics ID")
    artifacts.configure(subcommands.add_parser("artifacts", help="artifact bundle operations"))
    baseline.configure(subcommands.add_parser("baseline", help="single-node reference training"))
    netem.configure(subcommands.add_parser("netem", help="deterministic WAN emulation"))
    qlora.configure(subcommands.add_parser("qlora", help="certified fixed-ticket QLoRA mode"))
    worker.configure(subcommands.add_parser("worker", help="fixed-ticket local worker"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "formal-id":
            print(FORMAL_SEMANTICS_ID)
            return 0
        if args.command == "artifacts":
            return artifacts.execute(args, Path.cwd())
        if args.command == "baseline":
            return baseline.execute(args, Path.cwd())
        if args.command == "netem":
            return netem.execute(args)
        if args.command == "qlora":
            return qlora.execute(args)
        if args.command == "worker":
            return worker.execute(args, Path.cwd())
    except DeltaError as exc:
        print(json.dumps(exc.to_dict(), sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    return 2
