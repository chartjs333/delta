"""Fail-closed architecture and pinned-toolchain gate for feature 004."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE_DIR: Final = ROOT / "specs" / "004-compressed-delta-protocol"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
TARGET_LOCK: Final = ROOT / "delta-core-cpp" / "toolchain" / "fixedpoint-targets.lock.json"
EXPECTED_LOCKS: Final = {
    "delta-core-cpp/toolchain/build-tools.lock.json": (
        "35c7f115524cc5f4402de48bd871df8d69df9357e21365832718e7220552e171"
    ),
    "delta-core-cpp/toolchain/compilers.lock.json": (
        "6233c7b2d46b6bbafbbf7418e3c210d34fe21b6e2a58bbc8137288cb54f132e0"
    ),
    "delta-core-cpp/toolchain/dependencies.lock.json": (
        "137c8fe8f59d3a5141730af8cd2afa6b9482cd850303a36195882446ad3552d6"
    ),
    "delta-node-java/toolchains.toml": (
        "271847bb99b647ddec67be0e1f3bd6ee3dd328e51bf00640399c940020164f29"
    ),
}
EXPECTED_TARGETS: Final = {
    "FixedPointEnvelopeConformance",
    "NativeFixedPointFfmConformance",
    "delta_direct_q_test",
    "delta_fixedpoint",
    "delta_fixedpoint_parser_fuzz",
    "delta_fixedpoint_test",
    "delta_fixedpoint_unchecked_count_mutant_test",
    "delta_shards",
    "delta_shards_skip_context_mutant_test",
    "delta_shards_test",
    "delta_shards_unbounded_header_mutant_test",
}
NATIVE_SUFFIXES: Final = {".cpp", ".cc", ".cxx", ".h", ".hpp"}
FORBIDDEN_NATIVE: Final = {
    "COMPILER_INT128_EXTENSION": re.compile(r"\b__int128\b"),
    "EXTERNAL_BIGINT": re.compile(r"\bboost::(?:multiprecision|numeric)"),
    "FAST_MATH": re.compile(r"(?:-ffast-math|/fp:fast|#pragma\s+STDC\s+FENV_ACCESS\s+OFF)"),
    "FLOAT_CONSENSUS_TYPE": re.compile(r"\b(?:float|double|long\s+double)\b"),
    "IMPLICIT_SATURATION": re.compile(r"\b(?:saturate|saturated|saturation)\s*\("),
    "Q_TO_FLOAT_CAST": re.compile(
        r"(?:static_cast\s*<\s*(?:float|double)\s*>\s*\([^)]*\bq\b|\bq\w*\s*/\s*\d+\.\d+)"
    ),
}


class ArchitectureError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ArchitectureError(f"{code}: {detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    raw = path.read_bytes()
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "JSON_ROOT_INVALID", str(path))
    return value


def verify_locks() -> list[dict[str, str]]:
    lock = load_json(TARGET_LOCK)
    require(lock["formal_semantics_id"] == FORMAL_ID, "TOOLCHAIN_FORMAL_ID_INVALID")
    require(lock["schema_version"] == "1.0.0", "TOOLCHAIN_SCHEMA_INVALID")
    records = lock["locks"]
    require(isinstance(records, list), "TOOLCHAIN_LOCKS_INVALID")
    require(
        {str(record["path"]): str(record["sha256"]) for record in records} == EXPECTED_LOCKS,
        "TOOLCHAIN_LOCK_SET_INVALID",
    )
    artifacts: list[dict[str, str]] = []
    for relative, expected in sorted(EXPECTED_LOCKS.items()):
        path = ROOT / relative
        require(sha256_file(path) == expected, "TOOLCHAIN_LOCK_HASH_INVALID", relative)
        artifacts.append({"path": relative, "sha256": expected})
    targets = lock["targets"]
    require(isinstance(targets, list), "TARGET_LOCK_INVALID")
    require({str(target["id"]) for target in targets} == EXPECTED_TARGETS, "TARGET_SET_INVALID")
    architecture = lock["architecture"]
    require(isinstance(architecture, dict), "ARCHITECTURE_LOCK_INVALID")
    require(
        architecture
        == {
            "authoritative_language": "C++",
            "consensus_float_types_allowed": False,
            "dynamic_worker_scales_allowed": False,
            "external_runtime_dependencies": 0,
            "network_during_build": False,
            "network_during_test": False,
            "python_consensus_authority": False,
            "q_to_float_reduce_allowed": False,
            "residual_runtime_allowed": False,
            "saturation_allowed": False,
        },
        "ARCHITECTURE_POLICY_INVALID",
    )
    artifacts.append(
        {
            "path": str(TARGET_LOCK.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(TARGET_LOCK),
        }
    )
    return artifacts


def _native_paths() -> list[Path]:
    roots = [
        ROOT / "delta-core-cpp" / "include" / "delta" / "fixedpoint",
        ROOT / "delta-core-cpp" / "include" / "delta" / "shards",
        ROOT / "delta-core-cpp" / "src" / "fixedpoint",
        ROOT / "delta-core-cpp" / "src" / "shards",
        ROOT / "delta-core-cpp" / "fuzz",
    ]
    paths = {
        path
        for source_root in roots
        if source_root.is_dir()
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix.lower() in NATIVE_SUFFIXES
    }
    paths.add(ROOT / "delta-ffi" / "src" / "fixedpoint_abi.cpp")
    return sorted(paths)


def verify_sources() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    artifacts: list[dict[str, str]] = []
    for path in _native_paths():
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        for identifier, pattern in FORBIDDEN_NATIVE.items():
            if pattern.search(text):
                findings.append({"id": identifier, "path": relative})
        artifacts.append({"path": relative, "sha256": sha256_file(path)})
    python_root = ROOT / "delta-worker-python" / "src" / "deltatorrent"
    authority_paths = [
        path
        for path in python_root.rglob("*.py")
        if re.search(r"/(?:fixedpoint|shards|reduce|residual)(?:/|\.)", path.as_posix())
    ]
    findings.extend(
        {"id": "PYTHON_CONSENSUS_AUTHORITY_PATH", "path": str(path.relative_to(ROOT))}
        for path in authority_paths
    )
    oracle = python_root / "reference" / "fixedpoint_encoder.py"
    oracle_text = oracle.read_text(encoding="utf-8")
    require(
        "does not participate in consensus acceptance" in oracle_text,
        "PYTHON_ORACLE_BOUNDARY_MISSING",
    )
    fixedpoint_ffi = (ROOT / "delta-ffi" / "src" / "fixedpoint_abi.cpp").read_text(encoding="utf-8")
    require(
        fixedpoint_ffi.index("validate_opaque_shard(borrowed)")
        < fixedpoint_ffi.index("owned.reserve(envelope.size)"),
        "FFI_COPY_ALLOCATES_BEFORE_VALIDATION",
    )
    residual_paths = [
        path
        for root in (ROOT / "delta-core-cpp", ROOT / "delta-worker-python" / "src")
        for path in root.rglob("*residual*")
        if path.is_file()
    ]
    findings.extend(
        {"id": "RESIDUAL_RUNTIME_PRESENT", "path": str(path.relative_to(ROOT))}
        for path in residual_paths
    )
    java_root = ROOT / "delta-node-java" / "src" / "test" / "java" / "io" / "deltareduce" / "node"
    for name in (
        "DirectCopyParity.java",
        "FixedPointEnvelopeConformance.java",
        "MalformedEnvelopeConformance.java",
        "NativeFixedPointFfmConformance.java",
    ):
        path = java_root / name
        require(path.is_file(), "JAVA_CONFORMANCE_SOURCE_MISSING", name)
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
        )
    require(not findings, "ARCHITECTURE_FINDINGS_PRESENT", json.dumps(findings, sort_keys=True))
    return findings, artifacts


def verify_build_contract() -> list[dict[str, str]]:
    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    presets = load_json(ROOT / "CMakePresets.json")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    native_workflow = (ROOT / ".github" / "workflows" / "native.yml").read_text(encoding="utf-8")
    sanitizer_workflow = (ROOT / ".github" / "workflows" / "native-verification.yml").read_text(
        encoding="utf-8"
    )
    require("-fno-fast-math" in cmake and "/fp:strict" in cmake, "STRICT_FP_FLAGS_MISSING")
    require("DELTA_CXX_STANDARD" in cmake, "CXX_STANDARD_GATE_MISSING")
    require(
        all(
            target in cmake
            for target in {
                "delta_fixedpoint",
                "delta_fixedpoint_test",
                "delta_shards",
                "delta_shards_test",
            }
        ),
        "CMAKE_TARGETS_MISSING",
    )
    configure = presets["configurePresets"]
    require(isinstance(configure, list), "CMAKE_PRESETS_INVALID")
    names = {str(item["name"]) for item in configure if isinstance(item, dict)}
    require({"cpp20", "cpp23"}.issubset(names), "CMAKE_LANGUAGE_MODES_MISSING")
    require("verify_native_architecture.py --check-only" in workflow, "CI_ARCH_GATE_MISSING")
    require(
        all(
            marker in native_workflow
            for marker in {
                "gcc-14.2.0",
                "clang-20.1.8",
                "for standard in 20 23",
                "NativeFixedPointFfmConformance",
                "25.0.4.1",
                "26.0.2.1",
            }
        ),
        "NATIVE_MATRIX_INCOMPLETE",
    )
    require(
        all(
            marker in sanitizer_workflow
            for marker in {
                "run_native_fixedpoint_sanitizers.sh",
                "ASan",
                "UBSan",
            }
        ),
        "SANITIZER_MATRIX_INCOMPLETE",
    )
    paths = [
        ROOT / "CMakeLists.txt",
        ROOT / "CMakePresets.json",
        ROOT / ".github/workflows/ci.yml",
        ROOT / ".github/workflows/native.yml",
        ROOT / ".github/workflows/native-verification.yml",
    ]
    return [
        {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256_file(path)}
        for path in paths
    ]


def verify() -> dict[str, object]:
    preflight = load_json(FEATURE_DIR / "evidence" / "preflight.json")
    contracts = load_json(FEATURE_DIR / "evidence" / "protocol-contracts.json")
    require(preflight["status"] == contracts["status"] == "PASS", "PRIOR_GATE_NOT_PASS")
    require(
        preflight["formal_semantics_id"] == contracts["formal_semantics_id"] == FORMAL_ID,
        "PRIOR_FORMAL_ID_INVALID",
    )
    lock_artifacts = verify_locks()
    findings, source_artifacts = verify_sources()
    build_artifacts = verify_build_contract()
    artifacts = {
        item["path"]: item for item in [*lock_artifacts, *source_artifacts, *build_artifacts]
    }
    return {
        "artifacts": [artifacts[path] for path in sorted(artifacts)],
        "classification": "REFINEMENT_ONLY",
        "finding_count": len(findings),
        "findings": findings,
        "formal_semantics_id": FORMAL_ID,
        "phase": "004-native-architecture",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "targets": sorted(EXPECTED_TARGETS),
        "tasks": ["T013", "T014", "T015", "T016"],
    }


def _fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {
                "error": str(error),
                "phase": "004-native-architecture",
                "schema_version": "1.0.0",
                "status": "FAIL",
            }
        ).decode("utf-8")
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (ArchitectureError, OSError, ValueError, json.JSONDecodeError) as exc:
        _fail(exc)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
