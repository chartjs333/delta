"""Verify frozen feature-003 native/JVM toolchain locks and emit deterministic evidence."""

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
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "toolchain-locks.json"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_PREFLIGHT_SHA256 = "978d0dfed831e9de079a4efb18cb4c279d11a31db06c28c55fc320928bc8557d"

LOCK_PATHS = (
    "delta-core-cpp/toolchain/build-tools.lock.json",
    "delta-core-cpp/toolchain/compilers.lock.json",
    "delta-core-cpp/toolchain/dependencies.lock.json",
    "delta-ffi/toolchain/jextract.lock.json",
    "delta-node-java/toolchains.toml",
)
SOURCE_PATHS = (
    *LOCK_PATHS,
    "delta-core-cpp/toolchain/README.md",
    "specs/003-bft-round-state-machine/scripts/verify_native_toolchains.py",
)
EXPECTED = {
    "cmake": ("4.0.1", "d66c11c010588c8256ee20a26b45977cd5b2f4aee2b742d4b8a353769940d147"),
    "ninja": ("1.12.1", "6f98805688d19672bd699fbbfa2c2cf0fc054ac3df1f0e6a47664d963d530255"),
    "gcc": ("14.2.0", "04696df09633baf97cdbbdd6e9929b9d472161d3"),
    "clang": ("20.1.8", "87f0227cb60147a26a1eeb4fb06e3b505e9c7261"),
    "jdk25": ("25.0.4.1+1", "dbb698396d478e7fa2b1e50f4103324b2a99b90569ee27c33f2261f9215cf41e"),
    "jdk26": ("26.0.2.1+1", "451c12e68747bcfa2fb5a2c16b00483fedb9fa6d77bc962d30957f76ac17044d"),
    "jextract": (
        "25-jextract+2-4",
        "d0cc481abc1adb16fb9514e1c5e0bfc08d38c29228bece667fb5054ceaffaa42",
    ),
}
ALLOWED_HOSTS = {"github.com", "download.java.net"}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class ToolchainError(RuntimeError):
    """Stable fail-closed toolchain lock error."""


def reject(code: str, detail: str = "") -> None:
    raise ToolchainError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "UNSAFE_TRACKED_PATH",
        path,
    )
    return git_bytes("show", f"{revision}:{path}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def load_json(path: str, revision: str) -> dict[str, Any]:
    raw = tracked_bytes(path, revision)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("LOCK_JSON_INVALID", f"{path}:{exc}")
    require(isinstance(value, dict), "LOCK_JSON_ROOT_INVALID", path)
    canonical = canonical_json_bytes(value)
    require(raw in {canonical, canonical + b"\n"}, "LOCK_JSON_NOT_CANONICAL", path)
    return value


def validate_digest(value: object, path: str) -> None:
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        "LOCK_DIGEST_INVALID",
        path,
    )


def validate_artifact(artifact: dict[str, Any], path: str) -> None:
    url = artifact.get("archive_url")
    require(isinstance(url, str), "LOCK_URL_MISSING", path)
    parsed = urlparse(url)
    require(parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS, "LOCK_URL_INVALID", path)
    validate_digest(artifact.get("archive_sha256"), path)
    require(
        isinstance(artifact.get("archive_size_bytes"), int) and artifact["archive_size_bytes"] > 0,
        "LOCK_SIZE_INVALID",
        path,
    )
    require(
        isinstance(artifact.get("license"), str) and artifact["license"],
        "LOCK_LICENSE_MISSING",
        path,
    )


def verify_compilers(revision: str) -> dict[str, Any]:
    path = "delta-core-cpp/toolchain/compilers.lock.json"
    lock = load_json(path, revision)
    compilers = lock.get("compilers")
    require(isinstance(compilers, list) and len(compilers) == 2, "COMPILER_SET_INVALID")
    by_family = {item.get("family"): item for item in compilers if isinstance(item, dict)}
    require(set(by_family) == {"gcc", "clang"}, "COMPILER_FAMILIES_INVALID")
    for family in ("gcc", "clang"):
        item = by_family[family]
        version, commit = EXPECTED[family]
        require(item.get("version") == version, "COMPILER_VERSION_INVALID", family)
        require(item.get("cxx_standard_modes") == ["c++20", "c++23"], "CXX_MODES_INVALID", family)
        require(item.get("source", {}).get("commit") == commit, "COMPILER_SOURCE_INVALID", family)
        require(isinstance(item.get("license"), str), "COMPILER_LICENSE_MISSING", family)
    host = lock.get("host_contract")
    require(
        host
        == {
            "architecture": "x86_64",
            "binary_sha256_required_in_execution_evidence": True,
            "os": "linux",
        },
        "COMPILER_HOST_CONTRACT_INVALID",
    )
    return {"families": ["clang", "gcc"], "modes": ["c++20", "c++23"]}


def verify_build_tools(revision: str) -> dict[str, str]:
    path = "delta-core-cpp/toolchain/build-tools.lock.json"
    lock = load_json(path, revision)
    artifacts = lock.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 2, "BUILD_TOOL_SET_INVALID")
    result: dict[str, str] = {}
    for artifact in artifacts:
        require(isinstance(artifact, dict), "BUILD_TOOL_RECORD_INVALID")
        validate_artifact(artifact, path)
        key = "cmake" if str(artifact.get("id", "")).startswith("cmake-") else "ninja"
        version, digest = EXPECTED[key]
        require(
            artifact.get("version") == version and artifact.get("archive_sha256") == digest,
            "BUILD_TOOL_IDENTITY_INVALID",
            key,
        )
        result[key] = version
    require(lock.get("generator") == "Ninja", "BUILD_GENERATOR_INVALID")
    return result


def verify_dependencies(revision: str) -> int:
    lock = load_json("delta-core-cpp/toolchain/dependencies.lock.json", revision)
    require(lock.get("dependencies") == [], "NATIVE_DEPENDENCY_SET_NOT_EMPTY")
    require(
        lock.get("policy")
        == {
            "network_during_build": False,
            "network_during_test": False,
            "runtime_third_party_dependency_count": 0,
            "standard_library_only": True,
        },
        "NATIVE_DEPENDENCY_POLICY_INVALID",
    )
    return 0


def verify_jextract(revision: str) -> str:
    path = "delta-ffi/toolchain/jextract.lock.json"
    lock = load_json(path, revision)
    artifacts = lock.get("artifacts")
    require(isinstance(artifacts, list) and len(artifacts) == 1, "JEXTRACT_SET_INVALID")
    artifact = artifacts[0]
    require(isinstance(artifact, dict), "JEXTRACT_RECORD_INVALID")
    validate_artifact(artifact, path)
    version, digest = EXPECTED["jextract"]
    require(
        artifact.get("version") == version
        and artifact.get("archive_sha256") == digest
        and artifact.get("jdk_feature") == 25,
        "JEXTRACT_IDENTITY_INVALID",
    )
    require(
        lock.get("header_authoritative") is True
        and lock.get("generated_output_authoritative") is False,
        "JEXTRACT_AUTHORITY_INVALID",
    )
    return version


def verify_jdks(revision: str) -> list[dict[str, Any]]:
    path = "delta-node-java/toolchains.toml"
    try:
        lock = tomllib.loads(tracked_bytes(path, revision).decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        reject("JDK_LOCK_INVALID", str(exc))
    require(lock.get("schema_version") == "1.0.0", "JDK_LOCK_VERSION_INVALID")
    records = lock.get("toolchains")
    require(isinstance(records, list) and len(records) == 2, "JDK_SET_INVALID")
    by_feature = {item.get("feature"): item for item in records if isinstance(item, dict)}
    require(set(by_feature) == {25, 26}, "JDK_FEATURES_INVALID")
    summary: list[dict[str, Any]] = []
    for feature, key, role in ((25, "jdk25", "BASELINE"), (26, "jdk26", "COMPATIBILITY")):
        record = by_feature[feature]
        validate_artifact(record, path)
        version, digest = EXPECTED[key]
        require(
            record.get("version") == version
            and record.get("archive_sha256") == digest
            and record.get("role") == role,
            "JDK_IDENTITY_INVALID",
            str(feature),
        )
        summary.append({"feature": feature, "id": record["id"], "role": role})
    require(lock.get("baseline_id") == by_feature[25]["id"], "JDK_BASELINE_INVALID")
    require(lock.get("compatibility_id") == by_feature[26]["id"], "JDK_COMPATIBILITY_INVALID")
    return summary


def verify_preflight(revision: str) -> dict[str, str]:
    path = "specs/003-bft-round-state-machine/evidence/preflight.json"
    raw = tracked_bytes(path, revision)
    require(sha256_bytes(raw) == EXPECTED_PREFLIGHT_SHA256, "PREFLIGHT_HASH_INVALID")
    document = json.loads(raw.decode("utf-8"))
    require(
        document.get("status") == "PASS"
        and document.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and document.get("architecture", {}).get("finding_count") == 0,
        "PREFLIGHT_NOT_PASS",
    )
    return {"path": path, "sha256": EXPECTED_PREFLIGHT_SHA256}


def artifact_records(revision: str) -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}
        for path in SOURCE_PATHS
    ]


def verify(revision: str) -> dict[str, Any]:
    compilers = verify_compilers(revision)
    build_tools = verify_build_tools(revision)
    dependency_count = verify_dependencies(revision)
    jextract = verify_jextract(revision)
    jdks = verify_jdks(revision)
    preflight = verify_preflight(revision)
    return {
        "artifacts": artifact_records(revision),
        "build_tools": build_tools,
        "checks": [
            "PREFLIGHT_EXACT",
            "COMPILER_SOURCE_IDENTITIES_PINNED",
            "CXX20_CXX23_MATRIX_FROZEN",
            "BUILD_TOOL_ARCHIVES_CONTENT_ADDRESSED",
            "JDK25_JDK26_ARCHIVES_CONTENT_ADDRESSED",
            "JEXTRACT_ARCHIVE_CONTENT_ADDRESSED",
            "NATIVE_DEPENDENCY_SET_EMPTY",
            "OFFLINE_BUILD_TEST_POLICY",
        ],
        "compilers": compilers,
        "dependency_count": dependency_count,
        "errors": [],
        "formal_impact": "NONE",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "jdks": jdks,
        "jextract": jextract,
        "network_policy": "PROVISION_VERIFIED_CACHE_THEN_BUILD_AND_TEST_OFFLINE",
        "preflight": preflight,
        "schema_version": "1.0.0",
        "source_tree": {
            "commit": revision,
            "tree": git_text("rev-parse", f"{revision}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T011", "HR003-002"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def source_revision(output: Path, check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(output.is_file(), "TOOLCHAIN_EVIDENCE_MISSING")
    try:
        document = json.loads(output.read_text(encoding="utf-8"))
        revision = document["source_tree"]["commit"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        reject("TOOLCHAIN_EVIDENCE_INVALID", str(exc))
    require(
        isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision) is not None,
        "TOOLCHAIN_SOURCE_INVALID",
    )
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", revision, "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, "TOOLCHAIN_SOURCE_NOT_ANCESTOR")
    return revision


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        revision = source_revision(output, args.check_only)
        result = verify(revision)
        encoded = canonical_json_bytes(result)
        if args.check_only:
            require(output.read_bytes() == encoded, "TOOLCHAIN_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (ToolchainError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
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
