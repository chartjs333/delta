"""Generate deterministic feature-008 implementation/refinement trace summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence" / "traces"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def build() -> dict[str, dict[str, Any]]:
    golden = json.loads(
        (ROOT / "delta-protocol/fixtures/008/cross-language/golden-v1.json").read_text()
    )
    names = (
        "input_set_certificate",
        "seed_transcript",
        "norm_evidence",
        "eligibility_certificate",
        "aggregation_plan_certificate",
        "aggregate_root_qc",
        "apply_candidate",
        "apply_qc",
    )
    ids = {name: golden[name]["content_id"] for name in names}
    ids["parameter_shard_qcs"] = [item["content_id"] for item in golden["parameter_shard_qcs"]]
    legal = {
        "accepted": True,
        "classification": "REFINEMENT_ONLY",
        "events": [
            {"action_id": "ACT-ISC-FINALIZE", "body_id": ids["input_set_certificate"]},
            {
                "action_id": "ACT-SEED-GENERATE",
                "body_id": ids["seed_transcript"],
                "parent_ids": [ids["input_set_certificate"]],
            },
            {
                "action_id": "ACT-EC-FINALIZE",
                "body_id": ids["eligibility_certificate"],
                "parent_ids": [ids["input_set_certificate"], ids["norm_evidence"]],
            },
            {
                "action_id": "ACT-APC-FINALIZE",
                "body_id": ids["aggregation_plan_certificate"],
                "parent_ids": [
                    ids["input_set_certificate"],
                    ids["eligibility_certificate"],
                    ids["seed_transcript"],
                ],
            },
            *[
                {
                    "action_id": "ACT-PARAM-FINALIZE",
                    "body_id": shard,
                    "parent_ids": [
                        ids["input_set_certificate"],
                        ids["eligibility_certificate"],
                        ids["aggregation_plan_certificate"],
                    ],
                }
                for shard in ids["parameter_shard_qcs"]
            ],
            {
                "action_id": "ACT-ROOT-FINALIZE",
                "body_id": ids["aggregate_root_qc"],
                "parent_ids": list(ids["parameter_shard_qcs"]),
            },
            {
                "action_id": "ACT-APPLY-FINALIZE",
                "body_id": ids["apply_qc"],
                "parent_ids": [ids["aggregate_root_qc"], ids["apply_candidate"]],
            },
            {
                "action_id": "ACT-CURRENT-ADVANCE",
                "body_id": ids["apply_qc"],
                "outcome": "APPLIED",
                "parent_ids": [ids["apply_qc"]],
            },
        ],
        "formal_semantics_id": FORMAL_ID,
        "native_test": "delta_core.certificates",
        "schema_version": "1.0.0",
        "terminal_outcome": "APPLIED",
        "trace_id": "TRACE-008-FULL-CERTIFICATE-APPLY",
    }
    recovery = {
        "accepted": True,
        "events": [
            "ACT-APPLY-VOTE",
            "ACT-CRASH",
            "ACT-RESTART",
            "ACT-JOURNAL-RECOVER",
            "ACT-APPLY-VOTE",
            "ACT-CURRENT-ADVANCE",
            "ACT-CRASH",
            "ACT-RESTART",
            "ACT-CURRENT-ADVANCE",
        ],
        "formal_fixture": "formal/fixtures/traces/legal/applyqc-pointer-recovery.json",
        "formal_semantics_id": FORMAL_ID,
        "native_test": "delta_core.certificates",
        "pointer_outcomes": ["DURABLE_BEFORE_COMMIT", "RECOVERED", "REPLAY_NO_OP"],
        "schema_version": "1.0.0",
        "trace_id": "TRACE-008-VOTE-POINTER-RECOVERY",
    }
    illegal = {
        "early-seed.json": ("seed-without-isc.json", "INPUT_SET_NOT_CERTIFIED"),
        "membership-mutation.json": ("ec-non-isc-member.json", "NON_ISC_MEMBER"),
        "wrong-parent-shard.json": ("parameter-wrong-parent.json", "WRONG_PARENT"),
        "incomplete-root.json": ("incomplete-aggregate.json", "INCOMPLETE_AGGREGATE"),
        "duplicate-root.json": ("duplicate-aggregate.json", "DUPLICATE_AGGREGATE"),
        "conflicting-apply.json": ("conflicting-durable-vote.json", "CONFLICTING_DURABLE_VOTE"),
        "uncertified-current.json": ("current-without-applyqc.json", "CURRENT_WITHOUT_APPLYQC"),
    }
    result = {"legal-full-chain.json": legal, "legal-crash-recovery.json": recovery}
    for name, (fixture, reason) in illegal.items():
        result[name] = {
            "accepted": False,
            "expected_reason": reason,
            "formal_fixture": f"formal/fixtures/traces/illegal/{fixture}",
            "formal_semantics_id": FORMAL_ID,
            "schema_version": "1.0.0",
            "trace_id": "TRACE-008-" + name.removesuffix(".json").upper(),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if arguments.check == arguments.write:
        raise SystemExit("exactly one of --check/--write is required")
    traces = build()
    if arguments.write:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        for name, document in traces.items():
            (OUTPUT / name).write_bytes(canonical(document) + b"\n")
    else:
        for name, document in traces.items():
            if (OUTPUT / name).read_bytes() != canonical(document) + b"\n":
                raise SystemExit(f"trace drift: {name}")
    print(canonical({"status": "PASS", "trace_count": len(traces)}).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
