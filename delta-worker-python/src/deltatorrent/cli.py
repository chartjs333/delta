"""Thin command-line composition boundary for the worker package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from deltatorrent import __version__
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="delta")
    parser.add_argument("--version", action="version", version=__version__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("formal-id", help="print the accepted formal semantics ID")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "formal-id":
        print(FORMAL_SEMANTICS_ID)
        return 0
    return 2
