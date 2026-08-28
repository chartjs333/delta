"""Generate deterministic feature-005 projections onto the accepted formal trace contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
TRACE_DIR: Final = FEATURE / "evidence" / "traces"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
MANIFEST_ID: Final = "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"fixture is not an object: {relative}")
    return value


def state_root(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def legal_publish() -> dict[str, Any]:
    trace = copy.deepcopy(load("formal/fixtures/traces/legal/normal-apply.json"))
    root_event = next(
        event for event in trace["events"] if event["action_id"] == "ACT-ROOT-FINALIZE"
    )
    certificate = root_event["result_hash"]
    prior = trace["terminal_state_root"]
    trace["events"].append(
        {
            "action_id": "ACT-PUBLISH",
            "actor_id": "validator-1",
            "actor_role": "VALIDATOR",
            "artifact_refs": [certificate],
            "body_hash": MANIFEST_ID,
            "durable_sequence": None,
            "error_code": None,
            "height": 1,
            "logical_time": trace["events"][-1]["logical_time"] + 1,
            "next_state_root": state_root("trace-005-certified-publish"),
            "outcome": "ACCEPTED",
            "parent_hashes": [certificate],
            "prior_state_root": prior,
            "request_id": "publish-005-golden",
            "result_hash": MANIFEST_ID,
            "round_id": "round-1",
            "schema_version": "1.0.0",
            "validator_epoch": "epoch-1",
            "view": 0,
            "vote_context_id": None,
        }
    )
    trace["terminal_state_root"] = trace["events"][-1]["next_state_root"]
    trace["trace_id"] = "TRACE-005-CERTIFIED-PUBLISH"
    return trace


def legal_repair() -> dict[str, Any]:
    trace = copy.deepcopy(load("formal/fixtures/traces/legal/artifact-repair.json"))
    for event in trace["events"]:
        event["artifact_refs"] = [MANIFEST_ID]
        event["body_hash"] = MANIFEST_ID
        if event["action_id"] == "ACT-ARTIFACT-REPAIR":
            event["result_hash"] = MANIFEST_ID
    trace["trace_id"] = "TRACE-005-MULTI-PEER-EXACT-REPAIR"
    return trace


def legal_seed_loss() -> dict[str, Any]:
    trace = legal_repair()
    trace["events"] = [trace["events"][0]]
    trace["terminal_state_root"] = trace["events"][0]["next_state_root"]
    trace["trace_id"] = "TRACE-005-SEED-LOSS-STUTTER"
    return trace


def illegal_publish(trace_id: str, artifact: str) -> dict[str, Any]:
    trace = copy.deepcopy(load("formal/fixtures/traces/illegal/partial-publication.json"))
    event = trace["events"][0]
    event["artifact_refs"] = [artifact]
    event["body_hash"] = artifact
    event["error_code"] = "PARTIAL_PUBLICATION"
    event["result_hash"] = artifact
    trace["trace_id"] = trace_id
    return trace


def traces() -> dict[str, dict[str, Any]]:
    return {
        "legal/certified-publish.json": legal_publish(),
        "legal/multi-peer-repair.json": legal_repair(),
        "legal/seed-loss-stutter.json": legal_seed_loss(),
        "illegal/certification-downgrade.json": illegal_publish(
            "TRACE-005-ILLEGAL-CERTIFICATION-DOWNGRADE", MANIFEST_ID
        ),
        "illegal/altered-content.json": illegal_publish(
            "TRACE-005-ILLEGAL-ALTERED-CONTENT",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if not arguments.write:
        parser.error("--write is required")
    outputs = []
    for relative, value in traces().items():
        path = TRACE_DIR / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes(value) + b"\n")
        outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    print(canonical_json_bytes({"outputs": sorted(outputs), "status": "PASS"}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
