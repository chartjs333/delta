"""Publish the feature-009 final compatibility and Constitution decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/009-qlora-8gb-mode"
OUTPUT: Final = FEATURE / "evidence/final-compatibility.json"
PREDECESSOR: Final = "62124e58062d876dc4c2fd903b57cfc7d89872d7"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EVIDENCE_NAMES: Final = (
    "preflight.json",
    "protocol-contracts.json",
    "python-runtime.json",
    "native-runtime.json",
    "transport-runtime.json",
    "physical-gate.json",
    "qlora-ci.json",
)
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/qlora.yml",
    "configs/qlora/8gb-reference.json",
    "delta-protocol/registry.json",
    "delta-worker-python/src/deltatorrent/qlora/qualification.py",
    "delta-worker-python/tests/hardware/test_qlora_8gb_qualification.py",
    "docs/deltareduce/qlora-8gb.md",
    "specs/009-qlora-8gb-mode/runtime-tasks.md",
    "specs/009-qlora-8gb-mode/scripts/capture_qlora_ci.py",
    "specs/009-qlora-8gb-mode/scripts/qlora_contracts.py",
    "specs/009-qlora-8gb-mode/scripts/verify_final_compatibility.py",
    "specs/009-qlora-8gb-mode/scripts/verify_physical_qualification.py",
    "specs/009-qlora-8gb-mode/tasks.md",
    "specs/009-qlora-8gb-mode/tests/test_verify_protocol_contracts.py",
)
FORBIDDEN_BINARY_SUFFIXES: Final = (
    ".bin",
    ".ckpt",
    ".gguf",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*args: str) -> bytes:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    require(
        process.returncode == 0,
        f"GIT_COMMAND_FAILED:{process.stderr.decode(errors='replace').strip()}",
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*args: str) -> str:
    return git_bytes(*args).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def checked_ids(text: str, prefix: str) -> set[str]:
    return set(re.findall(rf"^- \[x\] (?:\*\*)?({re.escape(prefix)}\d{{3}})\b", text, re.M))


def load_evidence(name: str) -> tuple[dict[str, Any], str]:
    document = json.loads((FEATURE / "evidence" / name).read_text(encoding="utf-8"))
    require(isinstance(document, dict), f"EVIDENCE_NOT_OBJECT:{name}")
    require(document.get("status") == "PASS", f"EVIDENCE_NOT_PASS:{name}")
    require(document.get("formal_semantics_id") == FORMAL_ID, f"FORMAL_ID_DRIFT:{name}")
    require(
        document.get("semantic_completeness_claimed") is False,
        f"SEMANTIC_CLAIM_OVERSTATED:{name}",
    )
    source = document.get("source")
    require(
        isinstance(source, dict) and isinstance(source.get("commit"), str), f"SOURCE_MISSING:{name}"
    )
    return document, hashlib.sha256(canonical_json_bytes(document)).hexdigest()


def verify_repository_safety(source_commit: str) -> dict[str, object]:
    changed = git_text("diff", "--name-only", PREDECESSOR, source_commit).splitlines()
    forbidden = [path for path in changed if Path(path).suffix.lower() in FORBIDDEN_BINARY_SUFFIXES]
    require(not forbidden, "MODEL_OR_CHECKPOINT_BLOB_COMMITTED:" + ",".join(forbidden))
    patterns = {
        "HUGGINGFACE_TOKEN": re.compile(rb"hf_[A-Za-z0-9]{30,}"),
        "OPENAI_STYLE_TOKEN": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}"),
        "PRIVATE_KEY": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    }
    findings: list[str] = []
    for path in changed:
        raw = source_bytes(source_commit, path)
        for label, pattern in patterns.items():
            if pattern.search(raw):
                findings.append(f"{label}:{path}")
    require(not findings, "SECRET_SCAN_FAILED:" + ",".join(findings))
    profile = json.loads(source_bytes(source_commit, "configs/qlora/8gb-reference.json"))
    model = profile["model"]
    require(
        model["license"] == "MIT"
        and model["access_token_required"] is False
        and model["gated"] is False
        and model["trust_remote_code"] is False
        and model["license_url"].endswith("/LICENSE"),
        "FROZEN_MODEL_LICENSE_POLICY_INVALID",
    )
    return {
        "forbidden_binary_count": len(forbidden),
        "license": model["license"],
        "secret_finding_count": len(findings),
        "status": "PASS",
    }


def verify_protocol_registry(source_commit: str) -> dict[str, object]:
    registry = json.loads(source_bytes(source_commit, "delta-protocol/registry.json"))
    schemas = registry["schemas"]
    fixtures = registry["fixtures"]
    require(
        [item["path"] for item in schemas] == sorted(item["path"] for item in schemas),
        "PROTOCOL_SCHEMA_REGISTRY_NOT_SORTED",
    )
    require(
        [item["path"] for item in fixtures] == sorted(item["path"] for item in fixtures),
        "PROTOCOL_FIXTURE_REGISTRY_NOT_SORTED",
    )
    records = [*schemas, *fixtures, registry["action_registry"]]
    paths = [item["path"] for item in records]
    require(len(paths) == len(set(paths)), "PROTOCOL_REGISTRY_DUPLICATE_PATH")
    for item in records:
        require(
            hashlib.sha256(
                source_bytes(source_commit, "delta-protocol/" + item["path"])
            ).hexdigest()
            == item["sha256"],
            f"PROTOCOL_REGISTRY_HASH_DRIFT:{item['path']}",
        )
    qlora_schemas = [item for item in schemas if item["path"].startswith("schemas/009/")]
    require(len(qlora_schemas) == 11, "QLORA_PROTOCOL_SCHEMA_COUNT_INVALID")
    return {
        "qlora_schema_count": len(qlora_schemas),
        "record_count": len(records),
        "status": "PASS",
    }


def build(source_ref: str) -> dict[str, object]:
    source_commit = git_text("rev-parse", source_ref)
    require(git_text("merge-base", PREDECESSOR, source_commit) == PREDECESSOR, "WRONG_PREDECESSOR")
    require(
        not git_text(
            "diff",
            "--name-only",
            PREDECESSOR,
            source_commit,
            "--",
            "formal",
            "specs/000-formal-tla-spec",
        ),
        "FORMAL_SOURCE_DIFF",
    )
    task_text = source_bytes(source_commit, "specs/009-qlora-8gb-mode/tasks.md").decode()
    runtime_text = source_bytes(source_commit, "specs/009-qlora-8gb-mode/runtime-tasks.md").decode()
    require(
        checked_ids(task_text, "T") == {f"T{index:03d}" for index in range(46)},
        "FEATURE_TASKS_INCOMPLETE",
    )
    require(
        checked_ids(runtime_text, "HR009-") == {f"HR009-{index:03d}" for index in range(1, 13)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    docs = source_bytes(source_commit, "docs/deltareduce/qlora-8gb.md").decode()
    for marker in (
        "## Immutable profile",
        "## Repository-safe model import",
        "## Physical preflight and qualification",
        "## Recorded result",
        "## Composition, resume and rollback",
        "does not claim that every 8 GiB",
    ):
        require(marker in docs, f"OPERATIONS_DOCUMENTATION_INCOMPLETE:{marker}")

    loaded = {name: load_evidence(name) for name in EVIDENCE_NAMES}
    evidence = {name: item[0] for name, item in loaded.items()}
    for name, document in evidence.items():
        evidence_commit = str(document["source"]["commit"])
        require(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", evidence_commit, source_commit], cwd=ROOT
            ).returncode
            == 0,
            f"EVIDENCE_SOURCE_NOT_ANCESTOR:{name}",
        )
    preflight = evidence["preflight.json"]
    require(preflight["formal"]["status"] == "GO", "INHERITED_FORMAL_NOT_GO")
    require(preflight["feature008"]["merge_commit"] == PREDECESSOR, "FEATURE008_CHAIN_INVALID")
    require(
        preflight["formal_impact"]
        == {
            "classification": "REFINEMENT_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
            "status": "PASS",
        },
        "FORMAL_IMPACT_DRIFT",
    )
    physical = evidence["physical-gate.json"]
    require(
        physical["classification"] == "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
        "PHYSICAL_SCOPE_INVALID",
    )
    require(physical["measurements"]["processed_tokens"] == 2048, "PHYSICAL_TICKET_INVALID")
    ci = evidence["qlora-ci.json"]
    require(ci["source"]["commit"] == source_commit, "CI_SOURCE_DIVERGENCE")
    safety = verify_repository_safety(source_commit)
    registry = verify_protocol_registry(source_commit)
    constitution = source_bytes(source_commit, ".specify/memory/constitution.md").decode()
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")

    artifacts = [
        {
            "path": path,
            "sha256": hashlib.sha256(source_bytes(source_commit, path)).hexdigest(),
        }
        for path in SOURCE_ARTIFACTS
    ]
    evidence_artifacts = [
        {
            "canonical_sha256": loaded[name][1],
            "path": f"specs/009-qlora-8gb-mode/evidence/{name}",
        }
        for name in EVIDENCE_NAMES
    ]
    return {
        "checks": [
            "ALL_T000_T045_AND_HR009_001_HR009_012_COMPLETE",
            "EXACT_FEATURE008_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "SAFE_MODEL_IMPORT_AND_EXACT_ADAPTER_SCHEMA_PASS",
            "FIXED_TICKET_AND_BASE_IMMUTABILITY_PASS",
            "EXISTING_CERTIFICATE_APPLY_QC_AND_ABI_PASS",
            "BASE_CACHE_TRANSPORT_COMPOSITION_PASS",
            "EXACT_PHYSICAL_8GIB_PROFILE_PASS",
            "STRICT_NATIVE_SANITIZER_JDK_AND_PYTHON_CI_PASS",
            "MODEL_BLOB_SECRET_AND_LICENSE_SCAN_PASS",
            "OPERATIONS_ROLLBACK_AND_OBSERVABILITY_DOCUMENTED",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "evidence_artifacts": evidence_artifacts,
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "inherited_feature008": preflight["feature008"],
        "physical": physical,
        "protocol_registry": registry,
        "repository_safety": safety,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": artifacts,
            "commit": source_commit,
            "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T042", "T043", "T044", "T045", "HR009-012"],
        "unsupported_claims": [
            "GENERAL_8_GIB_GPU_COMPATIBILITY",
            "MODEL_QUALITY_PARITY_OR_IMPROVEMENT",
            "SEMANTIC_COVERAGE_BEYOND_DECLARED_REFINEMENT",
            "PHYSICAL_CLAIM_FOR_ANY_PROFILE_OTHER_THAN_FROZEN_REFERENCE",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.write:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        report = build(arguments.source_commit)
        OUTPUT.write_bytes(canonical_json_bytes(report))
    else:
        require(arguments.check_only, "CHECK_ONLY_REQUIRED")
        raw = OUTPUT.read_bytes()
        report = json.loads(raw)
        require(isinstance(report, dict), "FINAL_REPORT_NOT_OBJECT")
        require(raw == canonical_json_bytes(report), "FINAL_REPORT_NOT_CANONICAL")
        require(report == build(str(report["source"]["commit"])), "FINAL_REPORT_MISMATCH")
    print(canonical_json_bytes(report).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
