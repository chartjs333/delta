"""One-command local product walkthrough for a commission or technical review.

This runner composes existing public interfaces: Formal GO inspection, disposable
demo-controller quorum verification, real CPU training, immutable artifact
verification, deterministic WAN simulation, and the non-primary benchmark slice.
It never invokes Campaign 02 Stage A or creates production governance authority.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import shutil
import sys
import webbrowser
from dataclasses import dataclass, replace
from pathlib import Path

from deltatorrent.adapters.netem.simulated import SimulatedFaultyStream
from deltatorrent.artifacts.verifier import BundleVerifier
from deltatorrent.benchmark.campaign02_demo_controllers import (
    DemoControllerError,
    generate_demo_controller_bundle,
    run_demo_quorum_smoke,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.synthetic import execute_synthetic_fixture
from deltatorrent.domain.errors import DeltaError
from deltatorrent.domain.network import NetworkProfile
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.runner import run_baseline


class CommissionDemoError(ValueError):
    """Stable failure for an invalid or incomplete local presentation run."""


@dataclass(frozen=True, slots=True)
class CommissionDemoResult:
    """Paths and public summary for a completed local product walkthrough."""

    output_dir: Path
    report_json: Path
    report_html: Path
    validator_set_id: str
    training_run_id: str

    @property
    def document(self) -> dict[str, object]:
        return {
            "demo_status": "DEMO_PASS",
            "execution_authorized": False,
            "feature_010_go_claimed": False,
            "governance_eligible": False,
            "output_dir": str(self.output_dir),
            "report_html": str(self.report_html),
            "report_json": str(self.report_json),
            "training_run_id": self.training_run_id,
            "validator_set_id": self.validator_set_id,
        }


def _load_object(path: Path, code: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CommissionDemoError(code) from exc
    if not isinstance(value, dict):
        raise CommissionDemoError(code)
    return value


def _wan_smoke(repository_root: Path) -> dict[str, object]:
    profile = NetworkProfile.from_json_file(repository_root / "configs/netem/wan-smoke-v1.json")
    frames = tuple((index * 7, f"frame-{index}".encode()) for index in range(8))
    schedule = SimulatedFaultyStream(profile).transmit_stream(frames)
    schedule_document = [item.to_dict() for item in schedule]
    replay_document = [
        item.to_dict() for item in SimulatedFaultyStream(profile).transmit_stream(frames)
    ]
    if schedule_document != replay_document:
        raise CommissionDemoError("COMMISSION_DEMO_WAN_REPLAY_MISMATCH")
    expected_payloads = {index: payload for index, (_sent_at, payload) in enumerate(frames)}
    if not schedule or not any(item.payload is None for item in schedule):
        raise CommissionDemoError("COMMISSION_DEMO_WAN_FAULTS_NOT_EXERCISED")
    if not any(item.payload is not None for item in schedule):
        raise CommissionDemoError("COMMISSION_DEMO_WAN_DELIVERY_NOT_EXERCISED")
    if any(
        item.payload is not None and item.payload != expected_payloads[item.sequence]
        for item in schedule
    ):
        raise CommissionDemoError("COMMISSION_DEMO_WAN_PAYLOAD_MISMATCH")
    schedule_bytes = json.dumps(
        schedule_document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "delivered": sum(item.payload is not None for item in schedule),
        "deterministic_replay": True,
        "faulted": sum(item.payload is None for item in schedule),
        "profile_id": profile.profile_id,
        "schedule_id": f"sha256:{hashlib.sha256(schedule_bytes).hexdigest()}",
        "status": "PASS",
        "total_frames": len(schedule),
    }


def _training_metrics(path: Path) -> dict[str, object]:
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CommissionDemoError("COMMISSION_DEMO_TRAINING_METRICS_INVALID") from exc
    if not records or any(not isinstance(item, dict) for item in records):
        raise CommissionDemoError("COMMISSION_DEMO_TRAINING_METRICS_INVALID")
    first = records[0]
    last = records[-1]
    first_loss = first.get("loss")
    last_loss = last.get("loss")
    optimizer_steps = last.get("optimizer_step")
    processed_tokens = last.get("processed_tokens")
    if (
        isinstance(first_loss, bool)
        or not isinstance(first_loss, (int, float))
        or not math.isfinite(first_loss)
        or isinstance(last_loss, bool)
        or not isinstance(last_loss, (int, float))
        or not math.isfinite(last_loss)
        or isinstance(optimizer_steps, bool)
        or not isinstance(optimizer_steps, int)
        or optimizer_steps <= 0
        or isinstance(processed_tokens, bool)
        or not isinstance(processed_tokens, int)
        or processed_tokens <= 0
    ):
        raise CommissionDemoError("COMMISSION_DEMO_TRAINING_METRICS_INVALID")
    return {
        "first_loss": first_loss,
        "last_loss": last_loss,
        "optimizer_steps": optimizer_steps,
        "processed_tokens": processed_tokens,
        "record_count": len(records),
    }


def _render_html(report: dict[str, object]) -> str:
    checks = report["checks"]
    if not isinstance(checks, list):
        raise CommissionDemoError("COMMISSION_DEMO_REPORT_CHECKS_INVALID")
    rows: list[str] = []
    for check in checks:
        if not isinstance(check, dict):
            raise CommissionDemoError("COMMISSION_DEMO_REPORT_CHECK_INVALID")
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(check['name']))}</td>"
            f'<td><span class="pass">{html.escape(str(check["status"]))}</span></td>'
            f"<td>{html.escape(str(check['detail']))}</td>"
            "</tr>"
        )
    validator_set_id = html.escape(str(report["validator_set_id"]))
    formal_semantics_id = html.escape(str(report["formal_semantics_id"]))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DeltaReduce local end-to-end demo</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; }}
    body {{ margin: 0; background: #07111f; color: #e5edf7; }}
    main {{ max-width: 1100px; margin: auto; padding: 40px 24px 64px; }}
    .hero {{ padding: 30px; border: 1px solid #28425f; border-radius: 18px;
      background: linear-gradient(135deg, #102844, #101827); }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 5vw, 48px); }}
    .badge {{ display: inline-block; margin-top: 12px; padding: 8px 14px;
      border-radius: 999px; color: #052e1d; background: #57e39a; font-weight: 800; }}
    .warning {{ margin: 24px 0; padding: 18px; border-left: 5px solid #f7c948;
      background: #24200f; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; background: #0d1b2b; }}
    th, td {{ padding: 14px; border-bottom: 1px solid #26394f; text-align: left; }}
    th {{ color: #a8c3df; }} .pass {{ color: #57e39a; font-weight: 800; }}
    code {{ overflow-wrap: anywhere; color: #8ed0ff; }}
    footer {{ margin-top: 28px; color: #98a9bc; }}
  </style>
</head>
<body>
<main>
  <section class="hero">
    <div>DeltaReduce · local presentation profile</div>
    <h1>End-to-end product walkthrough</h1>
    <p>Real CPU training, immutable artifact verification, deterministic WAN faults,
       four synthetic controllers with valid Ed25519 key pairs, and the production
       quorum verifier.</p>
    <span class="badge">DEMO PASS</span>
  </section>
  <aside class="warning"><strong>Demo boundary:</strong> synthetic local evidence only.
    This page does not claim controller appointment, Campaign 02 authorization,
    Feature 010 GO, a real WAN run, or pilot readiness.</aside>
  <table>
    <thead><tr><th>Stage</th><th>Status</th><th>Observed result</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  <p><strong>Demo validator set:</strong> <code>{validator_set_id}</code></p>
  <p><strong>Formal semantics:</strong> <code>{formal_semantics_id}</code></p>
  <footer>Generated locally from repository-owned fixtures. No public network or
    production Campaign 02 action was used.</footer>
</main>
</body>
</html>
"""


def run_commission_demo(repository_root: Path, output_dir: Path) -> CommissionDemoResult:
    """Run the bounded local walkthrough and publish JSON plus static HTML summaries."""
    root = repository_root.resolve(strict=True)
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    destination = destination.resolve(strict=False)
    if destination.exists():
        raise CommissionDemoError("COMMISSION_DEMO_OUTPUT_ALREADY_EXISTS")
    destination.mkdir(parents=True)
    try:
        return _run_commission_demo(root, destination)
    except Exception:
        if destination.is_symlink():
            destination.unlink()
        elif destination.exists():
            shutil.rmtree(destination)
        raise


def _run_commission_demo(root: Path, destination: Path) -> CommissionDemoResult:
    """Execute the demo inside a newly created directory owned by this invocation."""

    formal = _load_object(
        root / "formal/reports/formal-verification-report.json",
        "COMMISSION_DEMO_FORMAL_REPORT_INVALID",
    )
    if formal.get("decision") != "GO" or formal.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
        raise CommissionDemoError("COMMISSION_DEMO_FORMAL_GO_MISMATCH")

    controllers_dir = destination / "controllers"
    controller_bundle = generate_demo_controller_bundle(controllers_dir)
    controller_smoke = run_demo_quorum_smoke(controllers_dir)

    source_config = BaselineConfig.from_json_file(root / "configs/baseline/cpu-smoke-v1.json")
    training_run_id = "commission-demo-cpu-training"
    training_root = destination / "training"
    training_config = replace(
        source_config,
        run_id=training_run_id,
        output_dir=str(training_root),
    )
    training = run_baseline(training_config, repository_root=root)
    if training.run_manifest.status.value != "COMPLETED":
        raise CommissionDemoError("COMMISSION_DEMO_TRAINING_NOT_COMPLETED")
    manifest_path = training_root / "runs" / training_run_id / "run-manifest.json"
    verification = BundleVerifier(
        training_root,
        root / "delta-protocol/registry.json",
    ).verify(manifest_path)
    metrics = _training_metrics(training_root / "runs" / training_run_id / "metrics.jsonl")
    if metrics["optimizer_steps"] != training_config.optimizer_steps:
        raise CommissionDemoError("COMMISSION_DEMO_TRAINING_STEPS_MISMATCH")

    wan = _wan_smoke(root)
    synthetic = execute_synthetic_fixture(
        root / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json",
        destination / "synthetic-benchmark",
    )
    if synthetic.verification.status != "PASS":
        raise CommissionDemoError("COMMISSION_DEMO_SYNTHETIC_VERIFICATION_FAILED")
    if (
        synthetic.fixture_class != "SYNTHETIC_NOT_PRIMARY_EVIDENCE"
        or synthetic.benchmark_result.decision != "GO"
    ):
        raise CommissionDemoError("COMMISSION_DEMO_SYNTHETIC_BOUNDARY_INVALID")

    checks: list[dict[str, str]] = [
        {
            "detail": f"accepted semantics {FORMAL_SEMANTICS_ID}",
            "name": "Formal baseline",
            "status": "PASS",
        },
        {
            "detail": "4 valid Ed25519 keys; 3-of-4 accepted; 2-of-4 and forgery rejected",
            "name": "Demo controller quorum",
            "status": "PASS",
        },
        {
            "detail": (
                f"{metrics['optimizer_steps']} optimizer steps, "
                f"{metrics['processed_tokens']} processed tokens"
            ),
            "name": "CPU model training",
            "status": "PASS",
        },
        {
            "detail": f"{verification.verified_objects} immutable objects verified",
            "name": "Training artifact integrity",
            "status": "PASS",
        },
        {
            "detail": (
                f"deterministic replay; {wan['delivered']} delivered and "
                f"{wan['faulted']} faulted frames"
            ),
            "name": "Deterministic WAN simulation",
            "status": "PASS",
        },
        {
            "detail": (
                f"{synthetic.run_count} synthetic runs; internal decision path="
                f"{synthetic.benchmark_result.decision} (not Feature 010 GO); "
                f"class={synthetic.fixture_class}"
            ),
            "name": "Synthetic benchmark control plane",
            "status": "PASS",
        },
    ]
    report: dict[str, object] = {
        "authoritative": False,
        "checks": checks,
        "controller_quorum": controller_smoke.document,
        "demo_status": "DEMO_PASS",
        "environment": "LOCAL_COMMISSION_DEMO_ONLY",
        "execution_authorized": False,
        "feature_010_go_claimed": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "governance_eligible": False,
        "limitations": [
            "DEMO_CONTROLLERS_ARE_NOT_APPOINTED_OR_CUSTODY_AUDITED",
            "CPU_TINY_CORPUS_IS_NOT_PRIMARY_SCIENTIFIC_EVIDENCE",
            "WAN_PROFILE_IS_LOGICAL_AND_LOCAL_NOT_REAL_WAN",
            "BENCHMARK_SLICE_IS_SYNTHETIC_NOT_PRIMARY_EVIDENCE",
            "NO_EXECUTE_STAGE_A_OR_PILOT_ACTION_PERFORMED",
        ],
        "schema_version": "1.0.0",
        "synthetic_benchmark": {
            "decision": synthetic.benchmark_result.decision,
            "fixture_class": synthetic.fixture_class,
            "run_count": synthetic.run_count,
            "verification_status": synthetic.verification.status,
        },
        "training": {
            "artifact_verification": verification.to_dict(),
            "checkpoint_manifest_id": training.final_checkpoint.named_manifest_ref.content_id,
            "metrics": metrics,
            "run_id": training_run_id,
            "run_manifest_id": training.run_manifest_ref.content_id,
            "status": training.run_manifest.status.value,
        },
        "type_name": "DELTAREDUCE_LOCAL_COMMISSION_DEMO_REPORT",
        "validator_set_id": controller_bundle.validator_set_id,
        "wan": wan,
    }
    report_json = destination / "commission-demo-report.json"
    report_html = destination / "commission-demo-report.html"
    report_json.write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report_html.write_text(_render_html(report), encoding="utf-8", newline="\n")
    return CommissionDemoResult(
        output_dir=destination,
        report_json=report_json,
        report_html=report_html,
        validator_set_id=controller_bundle.validator_set_id,
        training_run_id=training_run_id,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local DeltaReduce commission demo.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh local output directory; existing destinations are rejected.",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository checkout root (default: current directory).",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the generated static HTML report with the local default browser.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the commission-demo CLI."""
    args = _parser().parse_args(argv)
    try:
        result = run_commission_demo(args.repository_root, args.output_dir)
    except (CommissionDemoError, DemoControllerError, DeltaError, OSError, ValueError) as exc:
        print(f"commission-demo error: {exc}", file=sys.stderr)
        return 2
    if args.open_browser:
        webbrowser.open(result.report_html.as_uri())
    print(json.dumps(result.document, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
