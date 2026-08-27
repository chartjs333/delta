"""Generate feature-004 projections for the accepted formal trace checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
LEGAL_SOURCE: Final = ROOT / "formal" / "fixtures" / "traces" / "legal" / "normal-apply.json"
UNSAFE_SOURCE: Final = (
    ROOT / "formal" / "fixtures" / "traces" / "illegal" / "unchecked-overflow.json"
)
LEGAL_PATH: Final = FEATURE / "evidence" / "traces" / "direct-q-applied.json"
UNSAFE_PATH: Final = FEATURE / "evidence" / "mutants" / "unchecked-bound.json"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"trace root is not an object: {path}")
    return value


def feature_ids() -> tuple[str, str, str, str]:
    golden = load(
        ROOT / "delta-protocol" / "fixtures" / "004" / "cross-language" / "golden-v1.json"
    )
    negative = load(
        ROOT / "delta-protocol" / "fixtures" / "004" / "invalid" / "fixedpoint-negative-v1.json"
    )
    config_id = str(golden["fixedpoint_config"]["content_id"])  # type: ignore[index]
    proof_id = str(golden["proof_instance"]["content_id"])  # type: ignore[index]
    unsafe_case = next(
        item
        for item in negative["cases"]  # type: ignore[union-attr]
        if isinstance(item, dict) and item.get("id") == "int64-first-unsafe"
    )
    unsafe_config_id = str(unsafe_case["fixedpoint_config"]["content_id"])  # type: ignore[index]
    unsafe_proof = unsafe_case["proof"]
    unsafe_proof_id = (
        "sha256:"
        + __import__("hashlib")
        .sha256(b"deltareduce.004.proof-instance.v1\0" + canonical_json_bytes(unsafe_proof))
        .hexdigest()
    )
    return config_id, proof_id, unsafe_config_id, unsafe_proof_id


def direct_q_trace() -> dict[str, object]:
    trace = load(LEGAL_SOURCE)
    config_id, proof_id, _, _ = feature_ids()
    trace["trace_id"] = "TRACE-004-DIRECT-Q-APPLY"
    events = trace["events"]
    if not isinstance(events, list):
        raise ValueError("legal trace events are invalid")
    matched = 0
    for event in events:
        if isinstance(event, dict) and event.get("action_id") == "ACT-PARAM-VOTE":
            event["artifact_refs"] = [config_id, proof_id]
            matched += 1
    if matched == 0:
        raise ValueError("legal trace has no parameter vote")
    return trace


def unchecked_bound_trace() -> dict[str, object]:
    trace = load(UNSAFE_SOURCE)
    _, _, config_id, proof_id = feature_ids()
    trace["formal_semantics_id"] = FORMAL_ID
    trace["trace_id"] = "TRACE-004-UNCHECKED-BOUND-MUTANT"
    events = trace["events"]
    if not isinstance(events, list) or len(events) != 1 or not isinstance(events[0], dict):
        raise ValueError("unchecked-overflow source trace changed")
    events[0]["artifact_refs"] = [config_id, proof_id]
    return trace


def write() -> None:
    for path, value in ((LEGAL_PATH, direct_q_trace()), (UNSAFE_PATH, unchecked_bound_trace())):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes(value) + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if not arguments.write:
        parser.error("--write is required")
    write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
