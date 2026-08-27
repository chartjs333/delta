"""Verify feature-003 native source, toolchain and license provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "native-supply-chain.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_TOOLCHAIN_EVIDENCE_SHA256 = (
    "dfc8037582fbbe99539cf635e57e9ae64b41c9c7b2d4e32a47e8fcc347763197"
)
EXPECTED_ARCHITECTURE_EVIDENCE_SHA256 = (
    "5b27142b78a7713a5d833f4f98d5d2d36d192a420e87c62ecc4518cbbc8a66ef"
)
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".java"}
SOURCE_PREFIXES = ("delta-core-cpp/", "delta-runtime-cpp/", "delta-ffi/", "delta-node-java/")
EXPLICIT_SOURCE_PATHS = (".github/workflows/native.yml", "CMakeLists.txt", "CMakePresets.json")

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class SupplyChainError(RuntimeError):
    """Stable fail-closed supply-chain error."""


def reject(code: str, detail: str = "") -> None:
    raise SupplyChainError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject(
            "GIT_COMMAND_FAILED",
            completed.stderr.decode("utf-8", errors="replace").strip(),
        )
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def read_bytes(path: str, revision: str | None) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    if revision is None:
        return (ROOT / relative).read_bytes()
    return git_bytes("show", f"{revision}:{path}")


def load_json(path: str, revision: str | None) -> dict[str, Any]:
    try:
        value = json.loads(read_bytes(path, revision).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{path}:{exc}")
    require(isinstance(value, dict), "JSON_ROOT_INVALID", path)
    return value


def source_paths(revision: str | None) -> list[str]:
    if revision is None:
        candidates = [
            path.relative_to(ROOT).as_posix()
            for prefix in SOURCE_PREFIXES
            for path in (ROOT / prefix).rglob("*")
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES
        ]
    else:
        candidates = git_text(
            "ls-tree", "-r", "--name-only", revision, "--", *SOURCE_PREFIXES
        ).splitlines()
    selected = {
        path
        for path in candidates
        if path.startswith(SOURCE_PREFIXES) and Path(path).suffix.lower() in SOURCE_SUFFIXES
    }
    selected.update(EXPLICIT_SOURCE_PATHS)
    return sorted(selected)


def artifact(path: str, revision: str | None) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256(read_bytes(path, revision)).hexdigest()}


def verify_evidence(path: str, expected: str, revision: str | None) -> dict[str, str]:
    raw = read_bytes(path, revision)
    require(hashlib.sha256(raw).hexdigest() == expected, "PREREQUISITE_EVIDENCE_DRIFT", path)
    document = json.loads(raw.decode("utf-8"))
    require(
        document.get("status") == "PASS"
        and document.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "PREREQUISITE_EVIDENCE_NOT_PASS",
        path,
    )
    return {"path": path, "sha256": expected}


def external_licenses(revision: str | None) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    compilers = load_json("delta-core-cpp/toolchain/compilers.lock.json", revision)["compilers"]
    build_tools = load_json("delta-core-cpp/toolchain/build-tools.lock.json", revision)["artifacts"]
    jextract = load_json("delta-ffi/toolchain/jextract.lock.json", revision)["artifacts"]
    jdks = tomllib.loads(read_bytes("delta-node-java/toolchains.toml", revision).decode("utf-8"))[
        "toolchains"
    ]
    for item in [*compilers, *build_tools, *jextract, *jdks]:
        identifier = item.get("id")
        license_id = item.get("license")
        require(isinstance(identifier, str) and identifier, "COMPONENT_ID_MISSING")
        require(isinstance(license_id, str) and license_id, "COMPONENT_LICENSE_MISSING", identifier)
        records.append({"component_id": identifier, "license": license_id})
    records.sort(key=lambda item: item["component_id"])
    require(
        len({item["component_id"] for item in records}) == len(records),
        "COMPONENT_ID_DUPLICATE",
    )
    return records


def verify(content_revision: str | None, source_commit: str) -> dict[str, Any]:
    sources = [artifact(path, content_revision) for path in source_paths(content_revision)]
    require(len(sources) >= 10, "NATIVE_SOURCE_SET_INCOMPLETE")
    dependencies = load_json("delta-core-cpp/toolchain/dependencies.lock.json", content_revision)
    require(dependencies.get("dependencies") == [], "RUNTIME_DEPENDENCIES_NOT_EMPTY")
    workflow = read_bytes(".github/workflows/native.yml", content_revision).decode("utf-8")
    compilers = load_json("delta-core-cpp/toolchain/compilers.lock.json", content_revision)
    for compiler in compilers["compilers"]:
        image = compiler["execution_image"]
        require(
            image["linux_amd64_manifest"] in workflow, "COMPILER_IMAGE_NOT_IN_CI", compiler["id"]
        )
    jdks = tomllib.loads(
        read_bytes("delta-node-java/toolchains.toml", content_revision).decode("utf-8")
    )
    for jdk in jdks["toolchains"]:
        require(jdk["archive_sha256"] in workflow, "JDK_ARCHIVE_NOT_IN_CI", jdk["id"])

    prerequisites = [
        verify_evidence(
            "specs/003-bft-round-state-machine/evidence/toolchain-locks.json",
            EXPECTED_TOOLCHAIN_EVIDENCE_SHA256,
            content_revision,
        ),
        verify_evidence(
            "specs/003-bft-round-state-machine/evidence/core-architecture.json",
            EXPECTED_ARCHITECTURE_EVIDENCE_SHA256,
            content_revision,
        ),
    ]
    licenses = external_licenses(content_revision)
    return {
        "checks": [
            "TOOLCHAIN_AND_ARCHITECTURE_EVIDENCE_EXACT",
            "NATIVE_SOURCE_MANIFEST_CONTENT_ADDRESSED",
            "COMPILER_IMAGES_CONTENT_ADDRESSED",
            "JDK_ARCHIVES_CONTENT_ADDRESSED",
            "EXTERNAL_LICENSES_DECLARED",
            "RUNTIME_DEPENDENCY_SET_EMPTY",
            "INTERNAL_SOURCE_DISTRIBUTION_STATUS_EXPLICIT",
        ],
        "dependency_manifest": {
            "runtime_dependency_count": 0,
            "standard_library_only": True,
        },
        "errors": [],
        "formal_impact": "NONE",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "license_manifest": {
            "external_components": licenses,
            "project_source": {
                "distribution_status": "INTERNAL_ONLY_UNTIL_LICENSE_ASSIGNED",
                "license": "LicenseRef-DeltaReduce-Internal",
                "redistribution_granted": False,
            },
        },
        "prerequisite_evidence": prerequisites,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source_manifest": sources,
        "source_tree": {
            "commit": source_commit,
            "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T015"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        if args.check_only:
            require(output.is_file(), "NATIVE_SUPPLY_CHAIN_EVIDENCE_MISSING")
            existing = json.loads(output.read_text(encoding="utf-8"))
            source_commit = existing.get("source_tree", {}).get("commit")
            require(
                isinstance(source_commit, str)
                and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
                "NATIVE_SUPPLY_CHAIN_SOURCE_INVALID",
            )
            completed = subprocess.run(
                ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            require(completed.returncode == 0, "NATIVE_SUPPLY_CHAIN_SOURCE_NOT_ANCESTOR")
            result = verify("HEAD", source_commit)
            encoded = canonical_json_bytes(result)
            require(output.read_bytes() == encoded, "NATIVE_SUPPLY_CHAIN_EVIDENCE_STALE")
        else:
            require(
                not git_text("status", "--porcelain", "--untracked-files=all"),
                "SOURCE_TREE_NOT_CLEAN",
            )
            source_commit = git_text("rev-parse", "HEAD")
            result = verify("HEAD", source_commit)
            encoded = canonical_json_bytes(result)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (SupplyChainError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
