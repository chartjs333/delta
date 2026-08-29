"""QLoRA operational CLI; all certificate/current decisions remain native."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from deltatorrent.qlora.composition import compose
from deltatorrent.qlora.manifests import load_import_request
from deltatorrent.qlora.model_loader import load_tiny_backend
from deltatorrent.qlora.qualification import (
    load_profile,
    probe_gpu,
    run_physical_qualification,
    validate_physical_readiness,
    write_evidence,
)
from deltatorrent.qlora.trainer import Batch, Ticket, train_fixed_ticket


def configure(parser: argparse.ArgumentParser) -> None:
    commands = parser.add_subparsers(dest="qlora_command", required=True)
    import_command = commands.add_parser("import", help="validate one repository-safe import")
    import_command.add_argument("--manifest", type=Path, required=True)
    import_command.add_argument("--allowed-root", type=Path, required=True)
    preflight = commands.add_parser("preflight", help="validate the frozen physical profile")
    preflight.add_argument("--profile", type=Path, required=True)
    train = commands.add_parser("train", help="run the deterministic tiny fixed ticket")
    train.add_argument("--fixture", type=Path, required=True)
    compose_command = commands.add_parser("compose", help="validate native composition metadata")
    compose_command.add_argument("--context", type=Path, required=True)
    compose_command.add_argument("--checkpoint", type=Path, required=True)
    qualify = commands.add_parser("qualify", help="execute the preregistered physical gate")
    qualify.add_argument("--profile", type=Path, required=True)
    qualify.add_argument("--native-library", type=Path, required=True)
    qualify.add_argument("--output", type=Path, required=True)


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def execute(args: argparse.Namespace) -> int:
    if args.qlora_command == "import":
        request = load_import_request(args.manifest, allowed_root=args.allowed_root)
        _print({"base_model_manifest_id": request.manifest.content_id, "status": "PASS"})
        return 0
    if args.qlora_command == "preflight":
        profile = load_profile(args.profile)
        gpu = probe_gpu()
        validate_physical_readiness(profile, gpu)
        _print({"free_memory_bytes": gpu.free_memory_bytes, "status": "PASS", "uuid": gpu.uuid})
        return 0
    if args.qlora_command == "train":
        _, backend = load_tiny_backend(args.fixture)
        batches = (
            Batch(torch.tensor([[1.0, 0.0], [0.0, 1.0]]), torch.zeros((2, 2)), 4),
            Batch(torch.tensor([[1.0, 1.0], [0.5, -0.5]]), torch.ones((2, 2)), 4),
        )
        training_result = train_fixed_ticket(
            backend,
            Ticket("tiny-ticket-009", "tiny-text", 8, 2, "sha256:" + "a" * 64),
            batches,
            learning_rate=0.01,
        )
        _print(
            {
                "actual_optimizer_steps": training_result.actual_optimizer_steps,
                "base_immutable": (
                    training_result.base_hash_before == training_result.base_hash_after
                ),
                "eligible_for_commitment": training_result.eligible_for_commitment,
                "status": training_result.status,
            }
        )
        return 0 if training_result.eligible_for_commitment else 2
    if args.qlora_command == "compose":
        context = json.loads(args.context.read_text(encoding="utf-8"))
        checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        composition = compose(context, checkpoint, b"cli-native-authorization")
        _print(
            {
                "adapter_checkpoint_id": composition.adapter_checkpoint_id,
                "apply_qc_id": composition.apply_qc_id,
                "status": "PASS",
            }
        )
        return 0
    if args.qlora_command == "qualify":
        report = run_physical_qualification(args.profile, args.native_library)
        write_evidence(report, args.output)
        _print(report)
        return 0
    return 2
