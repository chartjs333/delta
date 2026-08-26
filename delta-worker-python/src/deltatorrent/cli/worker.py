"""Local fixed-ticket worker CLI adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.training.config import BaselineConfig
from deltatorrent.worker.engine import LocalRoundEngine
from deltatorrent.worker.validation import LocalRoundLimits, resolve_local_round


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="worker_command", required=True)
    run = commands.add_parser("run-ticket", help="execute one immutable local work ticket")
    run.add_argument("ticket", type=Path)
    run.add_argument("config", type=Path)
    run.add_argument("parameter_schema", type=Path)
    run.add_argument("tokenizer_ref", type=Path)
    run.add_argument("--store-root", type=Path, required=True)
    run.add_argument("--worker-id", default="worker-local-1")
    run.add_argument("--per-tensor-norm-ceiling-microunits", type=int, default=1_000_000_000_000)
    run.add_argument("--global-norm-ceiling-microunits", type=int, default=1_000_000_000_000)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeltaError(ErrorCode.SCHEMA_INVALID, f"{label}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise DeltaError(ErrorCode.SCHEMA_INVALID, f"{label}_ROOT_INVALID")
    return value


def execute(args: argparse.Namespace, repository_root: Path) -> int:
    if args.worker_command != "run-ticket":
        return 2
    ticket = DomainPureWorkTicket.from_dict(_load_object(args.ticket, "WORK_TICKET"))
    config = BaselineConfig.from_json_file(args.config)
    parameter_schema = ParameterSchema.from_dict(
        _load_object(args.parameter_schema, "PARAMETER_SCHEMA")
    )
    tokenizer_ref = ArtifactRef.from_dict(_load_object(args.tokenizer_ref, "TOKENIZER_REF"))
    limits = LocalRoundLimits(
        per_tensor_norm_ceiling_microunits=args.per_tensor_norm_ceiling_microunits,
        global_norm_ceiling_microunits=args.global_norm_ceiling_microunits,
    )
    store_root = (
        args.store_root if args.store_root.is_absolute() else repository_root / args.store_root
    )
    store = FilesystemArtifactStore(store_root)
    resolved = resolve_local_round(
        ticket=ticket,
        config=config,
        parameter_schema=parameter_schema,
        tokenizer_ref=tokenizer_ref,
        store=store,
        limits=limits,
    )
    result = LocalRoundEngine(store, worker_id=args.worker_id).run(resolved)
    print(json.dumps(result.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0
