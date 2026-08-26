"""Artifact bundle verification CLI adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deltatorrent.artifacts.verifier import BundleVerifier, infer_store_root


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="artifacts_command", required=True)
    verify = commands.add_parser("verify", help="recursively verify an immutable run bundle")
    verify.add_argument("run_manifest", type=Path)
    verify.add_argument("--root", type=Path)
    verify.add_argument("--registry", type=Path, default=Path("delta-protocol/registry.json"))


def execute(args: argparse.Namespace, repository_root: Path) -> int:
    manifest_path = _resolve(repository_root, args.run_manifest)
    store_root = (
        _resolve(repository_root, args.root) if args.root else infer_store_root(manifest_path)
    )
    registry_path = _resolve(repository_root, args.registry)
    result = BundleVerifier(store_root, registry_path).verify(manifest_path)
    print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0


def _resolve(root: Path, value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (root / value).resolve()
