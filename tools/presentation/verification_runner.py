"""Run a frozen proposal oracle in a child process. No runtime/WAL/QC authority."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ORACLE = Path(__file__).with_name("verification_oracle")
MANIFEST_SHA = "2bf8ea7c39444703973d360bbd18da736fafed68d05e62c19327bf7698f48ae2"
SCENARIOS = (
    "valid",
    "repeat",
    "parameter-tamper",
    "apply-tamper",
    "artifact-tamper",
    "missing-optimizer",
    "stale-parent",
)
EXPECTED = {
    "valid": "ACCEPTED",
    "repeat": "IDENTICAL",
    "parameter-tamper": "ARITHMETIC_RESULT_MISMATCH",
    "apply-tamper": "ARITHMETIC_RESULT_MISMATCH",
    "artifact-tamper": "ARTIFACT_BYTES",
    "missing-optimizer": "ARTIFACT_MISSING",
    "stale-parent": "PARENT_MODEL",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_bundle(root: Path = ORACLE) -> dict:
    raw = (root / "manifest.json").read_bytes()
    if sha(raw) != MANIFEST_SHA:
        raise ValueError("ORACLE_MANIFEST_MISMATCH")
    manifest = json.loads(raw)
    for name, identity in manifest["files"].items():
        if sha((root / name).read_bytes()) != identity["sha256"]:
            raise ValueError("ORACLE_SOURCE_MISMATCH:" + name)
    return manifest


def load_oracle():
    manifest = verify_bundle()
    # Explicit paths prevent a caller's import path from substituting the oracle.
    for name in ("arithmetic_binding", "native_binding"):
        spec = importlib.util.spec_from_file_location(name, ORACLE / (name + ".py"))
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules["native_binding"], manifest


def fixture():
    bundle = json.loads((ORACLE / "normal-apply.json").read_bytes())
    store = {key: value.encode("ascii") for key, value in bundle["artifacts"].items()}
    snapshots = list(bundle["snapshots"].values())
    apply = next(s for s in snapshots if s["action_id"] == "ACT-APPLY-VOTE")
    parameter = next(s for s in snapshots if s["action_id"] == "ACT-PARAM-VOTE")
    return store, apply, parameter


def derive(n, store: dict, snapshot: dict):
    witness = n.Witness(n.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], store)
    parameters = [witness.expected_parameter(*key) for key in witness.assignments]
    result = witness.expected_apply(parameters)
    return witness, parameters, result


def attempt(n, scenario: str) -> dict:
    store, apply_snapshot, parameter_snapshot = fixture()
    witness, parameters, result = derive(n, store, apply_snapshot)
    detail: dict = {}
    started = time.perf_counter_ns()
    observed = "ACCEPTED"
    rejected = False
    try:
        if scenario == "repeat":
            _, repeated_parameters, repeated = derive(n, dict(store), copy.deepcopy(apply_snapshot))
            first = n.canonical({"parameters": parameters, "apply": result})
            second = n.canonical({"parameters": repeated_parameters, "apply": repeated})
            detail = {
                "first_sha256": sha(first),
                "second_sha256": sha(second),
                "byte_count": len(first),
            }
            observed = "IDENTICAL" if first == second else "DIFFERENT"
        elif scenario in {"valid", "parameter-tamper", "apply-tamper"}:
            candidate = copy.deepcopy(parameters[0] if scenario == "parameter-tamper" else result)
            action = "ACT-APPLY-VOTE"
            if scenario == "parameter-tamper":
                detail = {"field": "numerators[0]", "expected": candidate["numerators"][0]}
                candidate["numerators"][0] += 1
                detail["supplied"] = candidate["numerators"][0]
                action = "ACT-PARAM-VOTE"
                witness = n.Witness(
                    n.NativeAnchor(**parameter_snapshot["anchor"]),
                    parameter_snapshot["authority"],
                    store,
                )
            elif scenario == "apply-tamper":
                detail = {"field": "next_optimizer[0]", "expected": candidate["next_optimizer"][0]}
                candidate["next_optimizer"][0] += 1
                detail["supplied"] = candidate["next_optimizer"][0]
            else:
                pw = n.Witness(
                    n.NativeAnchor(**parameter_snapshot["anchor"]),
                    parameter_snapshot["authority"],
                    store,
                )
                for body in parameters:
                    pw.admit(n.canonical({"action": "ACT-PARAM-VOTE", "payload": body}))
            accepted = witness.admit(n.canonical({"action": action, "payload": candidate}))
            detail.update(
                {"accepted_body_sha256": sha(accepted), "accepted_body_bytes": len(accepted)}
            )
        else:
            if scenario == "artifact-tamper":
                ref = parameters[0]["input_leaf_ids"][0]
                value = n.decode(store[ref])
                original = value["payload"]["values"][0]
                value["payload"]["values"][0] += 1
                store[ref] = n.canonical(value)
                detail = {
                    "field": "Q_SHARD.values[0]",
                    "expected": original,
                    "supplied": original + 1,
                    "retained_content_id": ref,
                }
            elif scenario == "missing-optimizer":
                ref = witness.root["optimizer"]["id"]
                del store[ref]
                detail = {"field": "optimizer artifact", "missing_content_id": ref}
            elif scenario == "stale-parent":
                detail = {
                    "field": "current_model_hash",
                    "expected": apply_snapshot["anchor"]["current_model_hash"],
                    "supplied": "sha256:" + "0" * 64,
                }
                apply_snapshot["anchor"]["current_model_hash"] = detail["supplied"]
            derive(n, store, apply_snapshot)
    except n.BindingError as error:
        observed = str(error)
        rejected = True
    return {
        "scenario": scenario,
        "observed": observed,
        "expected": EXPECTED[scenario],
        "matches_expectation": observed == EXPECTED[scenario],
        "outcome": "REJECTED" if rejected else observed,
        "elapsed_us": (time.perf_counter_ns() - started) // 1000,
        "detail": detail,
    }


def run(scenario: str = "all") -> dict:
    if scenario not in ("all", *SCENARIOS):
        raise ValueError("UNKNOWN_SCENARIO")
    started = time.perf_counter_ns()
    n, manifest = load_oracle()
    store, snapshot, _ = fixture()
    witness, parameters, result = derive(n, store, snapshot)
    conversions = []
    for body in parameters:
        assignment = witness.assignments[(body["domain"], body["shard"])]
        converted = n.arithmetic.domain_vector(
            tuple(body["numerators"]),
            body["denominator"],
            q_quantum=tuple(assignment["quantum"]),
            apply_quantum=witness.quantum,
            bits=witness.profile["accumulator_bits"],
        )
        conversions.append(
            {
                "domain": body["domain"],
                "shard": body["shard"],
                "quantum": assignment["quantum"],
                "values": list(converted),
            }
        )
    computation = {"parameters": parameters, "apply": result}
    cases = [attempt(n, item) for item in (SCENARIOS if scenario == "all" else (scenario,))]
    report = {
        "schema": "deltareduce.verification-demo.v1",
        "created_at": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "scope": "FORMAL_REFERENCE_DEMO",
        "mode": "SIMULATED_LOCAL",
        "executor": "PINNED_PYTHON_PROPOSAL_ORACLE",
        "native_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "benchmark_result_qc": None,
        "go_checkpoint": None,
        "wal_receipt": None,
        "source": manifest,
        "manifest_sha256": MANIFEST_SHA,
        "scenario": scenario,
        "checks_passed": all(c["matches_expectation"] for c in cases),
        "cases": cases,
        "elapsed_us": (time.perf_counter_ns() - started) // 1000,
        "inputs": {
            "artifact_count": len(store),
            "parent_model": list(witness.parent_state.model),
            "optimizer": list(witness.parent_state.momentum),
            "profile": witness.profile,
            "authority_id": witness.authority["id"],
            "domain_count": len(witness.domains),
            "shard_count": len(witness.shards),
        },
        "conversions": conversions,
        "computation": computation,
        "computation_sha256": sha(n.canonical(computation)),
    }
    encoded = canonical(report)
    return {
        "report": report,
        "canonical_report": encoded.decode("ascii"),
        "report_sha256": sha(encoded),
    }


def validate_result(value: dict) -> dict:
    raw = value["canonical_report"].encode("ascii")
    report = value["report"]
    if canonical(report) != raw or sha(raw) != value["report_sha256"]:
        raise ValueError("REPORT_DIGEST_MISMATCH")
    scenario = report["scenario"]
    if scenario not in ("all", *SCENARIOS):
        raise ValueError("UNKNOWN_SCENARIO")
    expected_cases = SCENARIOS if scenario == "all" else (scenario,)
    if (
        tuple(case["scenario"] for case in report["cases"]) != expected_cases
        or any(
            case["observed"] != EXPECTED[case["scenario"]]
            or case["expected"] != EXPECTED[case["scenario"]]
            or case["matches_expectation"] is not True
            or case["outcome"]
            != (
                EXPECTED[case["scenario"]]
                if case["scenario"] in {"valid", "repeat"}
                else "REJECTED"
            )
            for case in report["cases"]
        )
        or report["source"] != verify_bundle()
        or report["computation_sha256"] != sha(canonical(report["computation"]))
    ):
        raise ValueError("REFERENCE_RESULT_INCONSISTENT")
    if (
        report["manifest_sha256"] != MANIFEST_SHA
        or report["scope"] != "FORMAL_REFERENCE_DEMO"
        or report["native_execution"] is not False
        or report["gate_eligible"] is not False
        or report["wal_receipt"] is not None
        or report["benchmark_result_qc"] is not None
        or report["go_checkpoint"] is not None
        or report["checks_passed"] is not True
    ):
        raise ValueError("VERIFICATION_SCOPE_OR_CHECK_FAILED")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("all", *SCENARIOS), default="all")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = validate_result(run(args.scenario))
    temporary = args.output.with_suffix(".tmp")
    temporary.write_bytes(canonical(value))
    temporary.replace(args.output)
    print(
        json.dumps(
            {"report_sha256": value["report_sha256"], "checks": len(value["report"]["cases"])}
        )
    )


if __name__ == "__main__":
    main()
