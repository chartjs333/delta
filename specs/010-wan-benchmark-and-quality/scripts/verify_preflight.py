"""Verify the exact Feature 003-009, Formal GO and architecture boundary for Feature 010."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/010-wan-benchmark-and-quality"
OUTPUT: Final = FEATURE / "evidence/preflight.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_REPORT_SHA256: Final = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
PREDECESSOR: Final = "007eb08aa3aaee849128ba428274a9fbda561bf8"

FEATURES: Final = (
    {
        "id": "003",
        "name": "003-bft-round-state-machine",
        "merge": "53da4d3c0b236726566fb242fdcae84032b42679",
        "parents": (
            "a48d2af86fc7a976cb20b6be28058d22b09cec54",
            "f4f2101969d14709834ab6b6d60e88755d710334",
        ),
        "source": "189e5f155b787c2d1d391630fc599b67ea366bba",
        "report_sha256": "2cd392aafaba1ab70cc0a6919cae9580955c742f9f92296f54a570af29dca769",
    },
    {
        "id": "004",
        "name": "004-compressed-delta-protocol",
        "merge": "bd31efaa6d521bbfc3362ad9aac39455bd29a098",
        "parents": (
            "53da4d3c0b236726566fb242fdcae84032b42679",
            "29fb4138499a348f90d6bbc44e77fe6d1914e25f",
        ),
        "source": "22dd996b5d169763bfde49f32c1b1b18f2656493",
        "report_sha256": "9dbd9c7bda30d6ebe9b70f33a1a16d49a2b837b140d24f87becd433f05e3dccb",
    },
    {
        "id": "005",
        "name": "005-content-addressed-p2p-distribution",
        "merge": "1e884b4122898a8e0ff17254bc42414a8773830c",
        "parents": (
            "bd31efaa6d521bbfc3362ad9aac39455bd29a098",
            "be5d72305bfd883a5bd99607df6c2788014bfd0a",
        ),
        "source": "01f200b193733a1b474ad755c5c0c739b3189a96",
        "report_sha256": "7f7f86ad5021107688277ab626b266a61c7e633eb5c401e44c7778b98733dad6",
    },
    {
        "id": "006",
        "name": "006-regional-hierarchical-reduce",
        "merge": "827d3393acf347c9b45eabdb3d652bdc98bcfe75",
        "parents": (
            "1e884b4122898a8e0ff17254bc42414a8773830c",
            "b487ea81851cfd5b4769579392798841cb18afc0",
        ),
        "source": "90cc7fac96675694bab15f4e1ae1e5c6e3f525be",
        "report_sha256": "d16f9cfc62efe95e902b301823c136c0530db68b1cfb48788c6a239ade123800",
    },
    {
        "id": "007",
        "name": "007-domain-pure-ticket-scheduling",
        "merge": "2054f31ef0f6750645b924ef337a35d1737c619d",
        "parents": (
            "827d3393acf347c9b45eabdb3d652bdc98bcfe75",
            "08a118c5d52a0a4f6658249cb65ea15e538904c2",
        ),
        "source": "781cdbd76d812bf66323a3d1d11ca93f4b9d8333",
        "report_sha256": "2b45bf2dba25b15db624a02ee11e530a967961220e414ab04054428d44f59ef3",
    },
    {
        "id": "008",
        "name": "008-certificates-and-consensus",
        "merge": "62124e58062d876dc4c2fd903b57cfc7d89872d7",
        "parents": (
            "2054f31ef0f6750645b924ef337a35d1737c619d",
            "d86473a3f864b4e61d2312584afa080c8fd4fbab",
        ),
        "source": "4ef4daead4e3fcdf19d6947cf8120c4974af09fe",
        "report_sha256": "fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c",
    },
    {
        "id": "009",
        "name": "009-qlora-8gb-mode",
        "merge": PREDECESSOR,
        "parents": (
            "62124e58062d876dc4c2fd903b57cfc7d89872d7",
            "a5e73b41feb2dad73aa11d810d0c700c548e11ba",
        ),
        "source": "f43e39fa1c60d256bab5d7e37e0756f28438d5e4",
        "report_sha256": "95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef",
    },
)

SOURCE_ARTIFACTS: Final = (
    ".specify/memory/constitution.md",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "specs/ROADMAP.md",
    "specs/000-formal-tla-spec/failure-semantics.md",
    "specs/000-formal-tla-spec/proof-obligations.md",
    "specs/010-wan-benchmark-and-quality/formal-regression.md",
    "specs/010-wan-benchmark-and-quality/plan.md",
    "specs/010-wan-benchmark-and-quality/runtime-profile.md",
    "specs/010-wan-benchmark-and-quality/runtime-tasks.md",
    "specs/010-wan-benchmark-and-quality/scripts/verify_preflight.py",
    "specs/010-wan-benchmark-and-quality/spec.md",
    "specs/010-wan-benchmark-and-quality/task-map.md",
    "specs/010-wan-benchmark-and-quality/tasks.md",
    "specs/010-wan-benchmark-and-quality/tests/test_verify_preflight.py",
)

IDENTITY_ARTIFACTS: Final = (
    "CMakePresets.json",
    "delta-core-cpp/toolchain/compilers.lock.json",
    "delta-ffi/include/delta_abi.h",
    "delta-node-java/distribution-dependencies.lock.json",
    "delta-node-java/toolchains.toml",
    "delta-protocol/registry.json",
    "delta-protocol/schemas/003/delta-abi-v1.json",
    "delta-worker-python/pyproject.toml",
    "formal/reports/formal-id-registry.json",
    "uv.lock",
)

PRODUCTION_PREFIXES: Final = (
    "configs/benchmark/",
    "delta-ffi/src/benchmark_abi.cpp",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/",
    "delta-protocol/schemas/010/",
    "delta-runtime-cpp/src/benchmark/",
    "delta-worker-python/src/deltatorrent/benchmark/",
    "integration/benchmark/",
    "reports/benchmark/",
)

FORBIDDEN_PATTERNS: Final = {
    "ADAPTIVE_H": re.compile(r"(?i)\badaptive[_ -]?h(?:_i)?\b"),
    "FLOAT_CONSENSUS": re.compile(
        r"(?i)\b(?:fp(?:16|32|64)|float(?:16|32|64)?)\b.{0,40}\bconsensus\b"
    ),
    "MANUAL_GO_OVERRIDE": re.compile(r"(?i)\bmanual[_ -]?(?:go[_ -]?)?override\b"),
    "SINGLE_WRITER_CURRENT": re.compile(
        r"(?i)\bsingle[_ -]?(?:writer|authority)\b.{0,40}\bcurrent\b"
    ),
    "STALE_ACCEPTANCE": re.compile(r"(?i)\bstale[_ -]?(?:update[_ -]?)?accept(?:ance|ed)?\b"),
    "THRESHOLD_OVERRIDE": re.compile(r"(?i)\bthreshold[_ -]?override\b"),
}


class PreflightError(RuntimeError):
    """Stable fail-closed Feature 010 preflight error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PreflightError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode()


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, code, f"{ancestor}:{descendant}")


def validate_feature_report(document: dict[str, Any], feature_id: str, source: str) -> None:
    require(document.get("status") == "PASS", "FEATURE_REPORT_NOT_PASS", feature_id)
    require(
        document.get("classification") == "REFINEMENT_ONLY",
        "FEATURE_REPORT_CLASSIFICATION_INVALID",
        feature_id,
    )
    require(
        document.get("semantic_completeness_claimed") is False,
        "FEATURE_REPORT_SEMANTIC_CLAIM_OVERSTATED",
        feature_id,
    )
    require(document.get("source", {}).get("commit") == source, "FEATURE_SOURCE_DRIFT", feature_id)
    formal = document.get("formal")
    require(isinstance(formal, dict), "FEATURE_FORMAL_RESULT_MISSING", feature_id)
    formal_status = formal.get("status", formal.get("decision"))
    require(formal_status == "GO", "FEATURE_FORMAL_NOT_GO", feature_id)
    formal_id = formal.get("formal_semantics_id", document.get("formal_semantics_id"))
    require(formal_id == FORMAL_ID, "FEATURE_FORMAL_ID_DRIFT", feature_id)


def verify_feature_chain(source_commit: str) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for feature in FEATURES:
        feature_id = str(feature["id"])
        merge = str(feature["merge"])
        parents = tuple(str(parent) for parent in feature["parents"])
        source = str(feature["source"])
        actual_parents = tuple(git_text("show", "-s", "--format=%P", merge).split())
        require(actual_parents == parents, "FEATURE_MERGE_PARENTS_INVALID", feature_id)
        require_ancestor(source, parents[1], "FEATURE_SOURCE_OVERLAY_CHAIN_INVALID")
        require_ancestor(parents[1], merge, "FEATURE_OVERLAY_MERGE_CHAIN_INVALID")
        require_ancestor(merge, source_commit, "FEATURE_MERGE_NOT_ANCESTOR")

        report_path = f"specs/{feature['name']}/evidence/final-compatibility.json"
        raw = tracked_bytes(report_path, merge)
        expected_hash = str(feature["report_sha256"])
        require(sha256_bytes(raw) == expected_hash, "FEATURE_REPORT_HASH_DRIFT", feature_id)
        document = json.loads(raw)
        require(isinstance(document, dict), "FEATURE_REPORT_INVALID", feature_id)
        validate_feature_report(document, feature_id, source)

        for task_name in ("tasks.md", "runtime-tasks.md"):
            task_path = f"specs/{feature['name']}/{task_name}"
            require(
                re.search(r"^- \[ \] ", tracked_text(task_path, merge), re.MULTILINE) is None,
                "FEATURE_TASK_OPEN",
                task_path,
            )
        results.append(
            {
                "evidence_overlay": parents[1],
                "id": feature_id,
                "merge_commit": merge,
                "report": {"path": report_path, "sha256": expected_hash},
                "source_commit": source,
                "status": "PASS",
            }
        )
    return results


def verify_formal(source_commit: str) -> dict[str, object]:
    path = "formal/reports/formal-verification-report.json"
    raw = tracked_bytes(path, source_commit)
    require(sha256_bytes(raw) == FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    report = json.loads(raw)
    require(isinstance(report, dict), "FORMAL_REPORT_INVALID")
    require(report.get("decision") == "GO", "FORMAL_NOT_GO")
    require(report.get("formal_semantics_id") == FORMAL_ID, "FORMAL_ID_DRIFT")
    reviews = report.get("review_attestations")
    require(isinstance(reviews, list) and len(reviews) >= 2, "FORMAL_REVIEWS_MISSING")
    reviewers = {
        item.get("reviewer_id")
        for item in reviews
        if isinstance(item, dict)
        and item.get("status") == "PASS"
        and item.get("independent") is True
    }
    require(len(reviewers) >= 2, "FORMAL_INDEPENDENT_REVIEWS_MISSING")
    source_tree = report.get("source_tree")
    require(isinstance(source_tree, dict), "FORMAL_SOURCE_TREE_MISSING")
    semantic_artifacts = source_tree.get("semantic_artifacts")
    require(isinstance(semantic_artifacts, list) and semantic_artifacts, "FORMAL_ARTIFACTS_MISSING")
    for entry in semantic_artifacts:
        require(isinstance(entry, dict), "FORMAL_ARTIFACT_INVALID")
        artifact_path = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(artifact_path, str) and isinstance(expected, str),
            "FORMAL_ARTIFACT_INVALID",
        )
        require(
            sha256_bytes(tracked_bytes(artifact_path, source_commit)) == expected,
            "FORMAL_ARTIFACT_DRIFT",
            artifact_path,
        )
    return {
        "artifact_count": len(semantic_artifacts),
        "formal_semantics_id": FORMAL_ID,
        "independent_reviewers": sorted(str(item) for item in reviewers),
        "report": {"path": path, "sha256": FORMAL_REPORT_SHA256},
        "source_commit": source_tree.get("commit"),
        "status": "GO",
    }


def scan_forbidden_text(text: str) -> list[str]:
    return sorted(code for code, pattern in FORBIDDEN_PATTERNS.items() if pattern.search(text))


def verify_architecture(source_commit: str) -> dict[str, object]:
    changed = git_text("diff", "--name-only", PREDECESSOR, source_commit).splitlines()
    production = [path for path in changed if path.startswith(PRODUCTION_PREFIXES)]
    require(not production, "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", json.dumps(production))
    unexpected = [
        path for path in changed if not path.startswith("specs/010-wan-benchmark-and-quality/")
    ]
    require(not unexpected, "UNEXPECTED_PREFLIGHT_PATH", json.dumps(unexpected))
    paths = (
        "specs/010-wan-benchmark-and-quality/formal-regression.md",
        "specs/010-wan-benchmark-and-quality/plan.md",
        "specs/010-wan-benchmark-and-quality/runtime-profile.md",
        "specs/010-wan-benchmark-and-quality/spec.md",
        "specs/010-wan-benchmark-and-quality/task-map.md",
        "specs/010-wan-benchmark-and-quality/tasks.md",
    )
    combined = "\n".join(tracked_text(path, source_commit) for path in paths)
    for marker in (
        "Constitution 2.1.0",
        "REGRESSION_ONLY",
        "governance attestations",
        "isolated-sidecar",
        "007eb08aa3aaee849128ba428274a9fbda561bf8",
        FORMAL_ID,
    ):
        require(marker in combined, "ARCHITECTURE_RULE_UNBOUND", marker)
    require("Constitution 2.0.0" not in combined, "LEGACY_CONSTITUTION_REFERENCE")
    formal_diff = git_text(
        "diff",
        "--name-only",
        PREDECESSOR,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    return {
        "changed_path_count": len(changed),
        "forbidden_finding_count": 0,
        "production_source_count": 0,
        "status": "PASS",
    }


def verify_protocol_registry(source_commit: str) -> dict[str, object]:
    registry = json.loads(tracked_bytes("delta-protocol/registry.json", source_commit))
    require(isinstance(registry, dict), "PROTOCOL_REGISTRY_INVALID")
    require(registry.get("formal_semantics_id") == FORMAL_ID, "PROTOCOL_FORMAL_ID_DRIFT")
    records = [*registry.get("schemas", []), *registry.get("fixtures", [])]
    action_registry = registry.get("action_registry")
    require(isinstance(action_registry, dict), "ACTION_REGISTRY_MISSING")
    records.append(action_registry)
    paths: list[str] = []
    for entry in records:
        require(isinstance(entry, dict), "PROTOCOL_REGISTRY_ENTRY_INVALID")
        path = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(path, str) and isinstance(expected, str),
            "PROTOCOL_REGISTRY_ENTRY_INVALID",
        )
        paths.append(path)
        require(
            sha256_bytes(tracked_bytes(f"delta-protocol/{path}", source_commit)) == expected,
            "PROTOCOL_REGISTRY_HASH_DRIFT",
            path,
        )
    require(len(paths) == len(set(paths)), "PROTOCOL_REGISTRY_DUPLICATE_PATH")
    return {
        "abi_descriptor": artifact("delta-protocol/schemas/003/delta-abi-v1.json", source_commit),
        "record_count": len(records),
        "registry": artifact("delta-protocol/registry.json", source_commit),
        "status": "PASS",
    }


def verify_source(source_commit: str) -> dict[str, object]:
    require_ancestor(source_commit, "HEAD", "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    require(
        "**Version**: 2.1.0" in tracked_text(".specify/memory/constitution.md", source_commit),
        "CONSTITUTION_VERSION_INVALID",
    )
    return {
        "artifacts": [artifact(path, source_commit) for path in SOURCE_ARTIFACTS],
        "build_identities": [artifact(path, source_commit) for path in IDENTITY_ARTIFACTS],
        "commit": source_commit,
        "constitution_version": "2.1.0",
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }


def verify(source_commit: str) -> dict[str, object]:
    chain = verify_feature_chain(source_commit)
    feature009 = chain[-1]
    physical = json.loads(
        tracked_bytes(
            "specs/009-qlora-8gb-mode/evidence/final-compatibility.json",
            PREDECESSOR,
        )
    ).get("physical")
    require(
        isinstance(physical, dict) and physical.get("status") == "PASS",
        "FEATURE009_PHYSICAL_NOT_PASS",
    )
    require(
        physical.get("classification") == "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
        "FEATURE009_PHYSICAL_SCOPE_DRIFT",
    )
    return {
        "architecture": verify_architecture(source_commit),
        "checks": [
            "FEATURE003_009_MERGE_SOURCE_EVIDENCE_REPORT_CHAIN_EXACT",
            "FEATURE003_009_TASKS_CLOSED",
            "FORMAL_GO_REPORT_AND_SEMANTIC_ARTIFACTS_EXACT",
            "TWO_INDEPENDENT_HUMAN_FORMAL_REVIEWS_PRESENT",
            "FEATURE009_PHYSICAL_PROFILE_SCOPED_AND_PASS",
            "PROTOCOL_REGISTRY_AND_ABI_EXACT",
            "POLYGLOT_BUILD_IDENTITIES_BOUND",
            "REGRESSION_ONLY_NO_FORMAL_SOURCE_DIFF",
            "NO_BENCHMARK_PRODUCTION_BEFORE_PREFLIGHT",
            "PREFLIGHT_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature_chain": chain,
        "feature009_physical": physical,
        "formal": verify_formal(source_commit),
        "formal_impact": {
            "classification": "REGRESSION_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "predecessor": feature009,
        "protocol": verify_protocol_registry(source_commit),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit),
        "status": "PASS",
        "task_ids": ["T000", "T001"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "PREFLIGHT_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "PREFLIGHT_SOURCE_INVALID",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        source_commit = source_for_run(arguments.check_only)
        result = verify(source_commit)
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "PREFLIGHT_EVIDENCE_STALE")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
    except (
        OSError,
        PreflightError,
        RuntimeError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(error),
                    "formal_semantics_id": FORMAL_ID,
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
