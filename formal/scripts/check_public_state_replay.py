"""Replay complete candidate states against production TLA Init/Next with locked TLC."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json
from public_state_projection import MODULES, ROOT, configuration_sources, replay_sources, require
from public_state_storage import unpack
from run_formal_gate import tla_runtime
from tlc_results import FINISHED, INITIAL_STATES, successful_tlc_result


def validate_success(output: str, return_code: int, state_count: int):
    lock = load_json_strict(ROOT / "formal/toolchain/tla.lock")["tla_tools"]
    require(return_code == 0, "TLC_REPLAY_FAILED")
    parsed = successful_tlc_result(
        output,
        expected_version=lock["reported_tlc_version"],
        expected_revision=lock["release_commit"],
        fingerprint_index=0,
        seed=1,
        workers=1,
        required_actions=[],
    )
    initial = list(INITIAL_STATES.finditer(output))
    require(len(initial) == 1 and int(initial[0][1]) == 1, "TLC_NO_INITIAL_STATE")
    require(len(list(FINISHED.finditer(output))) == 1, "TLC_INCOMPLETE_OUTPUT")
    require(
        parsed["states"] == parsed["distinct_states"] == parsed["diameter"] == state_count,
        "TLC_INCOMPLETE_PATH",
    )
    return parsed


def run_case(trace, target: Path, runtime, expected_failure=None, configuration="round-config"):
    module, config = replay_sources(trace, configuration)
    target.mkdir(parents=True, exist_ok=True)
    for name in (*MODULES, *configuration_sources(configuration)[1]):
        shutil.copyfile(ROOT / f"formal/tla/{name}.tla", target / f"{name}.tla")
    source = target / "FullStateReplay.tla"
    cfg = target / "FullStateReplay.cfg"
    source.write_text(module, encoding="utf-8", newline="\n")
    cfg.write_text(config, encoding="utf-8", newline="\n")
    java, options, jar = runtime
    command = [
        java,
        *options,
        "-cp",
        str(jar),
        "tlc2.TLC",
        "-workers",
        "1",
        "-fp",
        "0",
        "-seed",
        "1",
        "-config",
        cfg.name,
        "-metadir",
        "states",
        "FullStateReplay",
    ]
    result = subprocess.run(
        command, cwd=target, capture_output=True, text=True, encoding="utf-8", timeout=90
    )
    output = result.stdout + result.stderr
    (target / "tlc.txt").write_text(output, encoding="utf-8", newline="\n")
    if expected_failure is None:
        semantic_result = validate_success(output, result.returncode, len(trace["states"]))
    else:
        marker = (
            f"Invariant {expected_failure} is violated"
            if expected_failure == "WitnessInitialOK"
            else f"Action property {expected_failure} is violated"
        )
        expected_code = 12 if expected_failure == "WitnessInitialOK" else 13
        require(
            result.returncode == expected_code and output.count(marker) == 1,
            "TLC_WRONG_COUNTEREXAMPLE",
        )
        require(len(list(FINISHED.finditer(output))) == 1, "TLC_INCOMPLETE_OUTPUT")
        semantic_result = None
    return {
        "status": "PASS" if expected_failure is None else "EXPECTED_COUNTEREXAMPLE",
        "exit_code": result.returncode,
        "expected_failure": expected_failure,
        "semantic_result": semantic_result,
        "state_count": len(trace["states"]),
        "action_count": len(trace["actions"]),
        "module_sha256": sha256_file(source),
        "configuration_sha256": sha256_file(cfg),
        "log_sha256": sha256_file(target / "tlc.txt"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vectors", type=Path, default=ROOT / "formal/proposals/public-state-vectors.json"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "formal/build/public-state-replay")
    parser.add_argument(
        "--configuration", choices=["round-config", "native-arithmetic"], default="round-config"
    )
    args = parser.parse_args()
    vectors = load_json_strict(args.vectors)
    if args.configuration == "native-arithmetic":
        from generate_public_arithmetic_vectors import NEGATIVE_RECIPES, counterexamples

        vectors["positive"] = unpack(vectors["positive"])
        require(vectors["negative"] == NEGATIVE_RECIPES, "NEGATIVE_RECIPE_MANIFEST")
        vectors["negative"] = counterexamples(vectors["positive"])
    runtime = tla_runtime()
    records = {
        "positive": run_case(
            vectors["positive"], args.output / "positive", runtime, configuration=args.configuration
        )
    }
    for index, case in enumerate(vectors["negative"]):
        records[case["name"]] = run_case(
            case["trace"],
            args.output / f"negative-{index}",
            runtime,
            case["expected_failure"],
            args.configuration,
        )
    document = {
        "status": "PASS",
        "scope": "FINITE_COMPLETE_STATE_REPLAY_NOT_NATIVE_REFINEMENT",
        "vectors_sha256": sha256_file(args.vectors),
        "cases": records,
    }
    write_canonical_json(args.output / "result.json", document)
    print(json.dumps(document, sort_keys=True))


if __name__ == "__main__":
    main()
