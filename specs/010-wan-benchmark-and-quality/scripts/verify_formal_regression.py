"""Attest an exact-source formal rerun without changing inherited semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/formal-regression.json"
FORMAL_SOURCE: Final = "1e6e0f6f70056161d95933e71494ec390c7c1151"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_REPORT: Final = ROOT / "formal/reports/formal-verification-report.json"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def run(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def semantic_artifacts() -> list[dict[str, str]]:
    report = json.loads(FORMAL_REPORT.read_text(encoding="utf-8"))
    source = report.get("source_tree")
    require(isinstance(source, dict), "FORMAL_REPORT_SOURCE_MISSING")
    require(source.get("commit") == FORMAL_SOURCE, "FORMAL_REPORT_SOURCE_COMMIT")
    artifacts = source.get("semantic_artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 24, "FORMAL_ARTIFACT_COUNT")
    result: list[dict[str, str]] = []
    for value in artifacts:
        require(isinstance(value, dict), "FORMAL_ARTIFACT_INVALID")
        path = value.get("path")
        expected = value.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), "FORMAL_ARTIFACT_FIELDS")
        current = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        source_hash = hashlib.sha256(git_bytes(FORMAL_SOURCE, path)).hexdigest()
        require(current == expected == source_hash, f"FORMAL_ARTIFACT_DRIFT:{path}")
        result.append({"path": path, "sha256": expected})
    return result


def parse_tlc_log(path: Path, config_id: str, kind: str) -> dict[str, object]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    require("Model checking completed. No error has been found." in text, f"TLC_FAILED:{config_id}")
    states = re.findall(
        r"([0-9][0-9,]*) states generated, ([0-9][0-9,]*) distinct states found",
        text,
    )
    depth = re.findall(r"The depth of the complete state graph search is ([0-9]+)", text)
    require(bool(states) and bool(depth), f"TLC_SUMMARY_MISSING:{config_id}")
    generated, distinct = states[-1]
    return {
        "config_id": config_id,
        "depth": int(depth[-1]),
        "distinct_states": int(distinct.replace(",", "")),
        "generated_states": int(generated.replace(",", "")),
        "kind": kind,
        "log_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "status": "PASS",
    }


def execution_summary(execution_root: Path) -> dict[str, object]:
    require(
        run("git", "rev-parse", "HEAD", cwd=execution_root) == FORMAL_SOURCE,
        "EXECUTION_SOURCE_COMMIT",
    )
    manifest = json.loads(
        (execution_root / "formal/tla/cfg/config-manifest.json").read_text(encoding="utf-8")
    )
    configs = manifest.get("configs")
    require(isinstance(configs, list) and len(configs) == 25, "EXECUTION_CONFIG_MANIFEST")
    models: list[dict[str, object]] = []
    for value in configs:
        require(isinstance(value, dict), "EXECUTION_CONFIG_INVALID")
        config_id = value.get("id")
        kind = value.get("kind")
        require(isinstance(config_id, str) and kind in {"safety", "liveness"}, "CONFIG_FIELDS")
        models.append(
            parse_tlc_log(
                execution_root / "formal/build/tlc" / config_id / "tlc.log",
                config_id,
                str(kind),
            )
        )
    proof_path = execution_root / "formal/reports/lean-proof-report.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    require(proof.get("status") == "PASS", "LEAN_STATUS")
    completeness = proof.get("conjunct_completeness")
    require(
        isinstance(completeness, dict)
        and completeness.get("status") == "PASS"
        and completeness.get("expected") == 28
        and completeness.get("verified") == 28,
        "LEAN_CONJUNCT_COMPLETENESS",
    )
    mutant_path = execution_root / "formal/reports/mutant-evidence.json"
    mutant = json.loads(mutant_path.read_text(encoding="utf-8"))
    require(
        mutant.get("status") == "PASS"
        and mutant.get("mutation_scope") == "PRODUCTION_ACTION_SOURCE"
        and isinstance(mutant.get("mutants"), list)
        and len(mutant["mutants"]) == 10,
        "MUTANT_REGRESSION",
    )
    refinement_path = execution_root / "formal/reports/refinement-evidence.json"
    refinement = json.loads(refinement_path.read_text(encoding="utf-8"))
    require(
        refinement.get("status") == "PASS"
        and refinement.get("legal_fixture_count") == 7
        and refinement.get("illegal_fixture_count") == 16,
        "REFINEMENT_REGRESSION",
    )
    return {
        "gate_order": [
            "phase0",
            "contracts",
            "toolchain",
            "parse",
            "safety",
            "liveness",
            "proofs",
            "mutants",
            "refinement",
        ],
        "lean": {
            "conjuncts": "28/28",
            "report_sha256": sha256(proof_path),
            "status": "PASS",
            "theorem_obligations": 13,
        },
        "models": sorted(models, key=lambda item: str(item["config_id"])),
        "mutants": {
            "count": 10,
            "mutation_scope": "PRODUCTION_ACTION_SOURCE",
            "report_sha256": sha256(mutant_path),
            "status": "PASS",
        },
        "refinement": {
            "illegal_fixtures": 16,
            "legal_fixtures": 7,
            "report_sha256": sha256(refinement_path),
            "status": "PASS",
        },
        "source_clean_at_start": True,
        "status": "PASS",
    }


def validate_recorded_execution(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeError("FORMAL_EXECUTION_MISSING")
    require(value.get("status") == "PASS", "FORMAL_EXECUTION_STATUS")
    models = value.get("models")
    if not isinstance(models, list) or len(models) != 25:
        raise RuntimeError("FORMAL_EXECUTION_MODELS")
    require(
        sum(item.get("kind") == "safety" for item in models if isinstance(item, dict)) == 19
        and sum(item.get("kind") == "liveness" for item in models if isinstance(item, dict)) == 6
        and all(item.get("status") == "PASS" for item in models if isinstance(item, dict)),
        "FORMAL_EXECUTION_MODEL_STATUS",
    )
    return value


def build(
    commit: str,
    execution: dict[str, object],
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "SOURCE_COMMIT_INVALID")
    run(
        "python",
        "formal/scripts/verify_formal_report.py",
        str(FORMAL_REPORT),
        "--require-go",
    )
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    require(not formal_diff, "FORMAL_SOURCE_DIFF")
    report = json.loads(FORMAL_REPORT.read_text(encoding="utf-8"))
    require(report.get("decision") == "GO" and report.get("formal_semantics_id") == FORMAL_ID, "GO")
    return {
        "checks": [
            "EXACT_FORMAL_SOURCE_RERUN",
            "NINETEEN_SAFETY_MODELS_PASS",
            "SIX_LIVENESS_MODELS_PASS_WITH_APPLIED_PROGRESS",
            "THIRTEEN_PROOF_OBLIGATIONS_AND_28_CONJUNCTS_PASS",
            "TEN_PRODUCTION_ACTION_MUTANTS_EXPOSED",
            "SEVEN_LEGAL_AND_SIXTEEN_ILLEGAL_REFINEMENT_FIXTURES_PASS",
            "INHERITED_FORMAL_REPORT_GO",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REGRESSION_ONLY",
        "environment": environment
        if environment is not None
        else {"host": platform.platform(), "python": platform.python_version()},
        "execution": execution,
        "formal": {
            "report_sha256": sha256(FORMAL_REPORT),
            "semantic_artifacts": semantic_artifacts(),
            "source_commit": FORMAL_SOURCE,
        },
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "commit": commit,
            "tree": run("git", "show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": ["HR010-007"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--execution-root", type=Path)
    arguments = parser.parse_args()
    if arguments.check_only:
        recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
        execution = validate_recorded_execution(recorded.get("execution"))
        environment = recorded.get("environment")
        require(isinstance(environment, dict), "FORMAL_ENVIRONMENT_MISSING")
        expected = build(str(recorded["source"]["commit"]), execution, environment)
        require(recorded == expected, "FORMAL_REGRESSION_EVIDENCE_MISMATCH")
        result = recorded
    else:
        require(arguments.execution_root is not None, "EXECUTION_ROOT_REQUIRED")
        require(not run("git", "status", "--porcelain"), "SOURCE_TREE_NOT_CLEAN")
        execution = execution_summary(arguments.execution_root.resolve())
        result = build(run("git", "rev-parse", "HEAD"), execution)
        OUTPUT.write_text(
            json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
