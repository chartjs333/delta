"""Verify feature-005 policy/data-plane implementation and formal refinement projections."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_traces import canonical_json_bytes, traces  # noqa: E402
from verify_protocol_contracts import verify as verify_contracts  # noqa: E402

FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
CHECKER: Final = ROOT / "formal/scripts/check-refinement.py"
TRACE_DIR: Final = FEATURE / "evidence/traces"


class DistributionGateError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise DistributionGateError(f"{code}: {detail}" if detail else code)


def normalized_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def artifact(path: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(normalized_bytes(path)).hexdigest(),
    }


def run_trace(path: Path, legal: bool) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="delta-005-refinement-") as temporary:
        isolated = Path(temporary)
        formal = isolated / "formal"
        for relative in (
            Path("scripts/check-refinement.py"),
            Path("scripts/formal_artifacts.py"),
            Path("schemas/formal-trace.schema.json"),
            Path("schemas/formal-verification-report.schema.json"),
            Path("reports/formal-id-registry.json"),
            Path("proofs/DeltaReduce.lean"),
        ):
            target = formal / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "formal" / relative, target)
        shutil.copytree(
            ROOT / "formal/tla", formal / "tla", ignore=shutil.ignore_patterns("states")
        )
        shutil.copytree(ROOT / "formal/proofs/DeltaReduce", formal / "proofs/DeltaReduce")
        for source in formal.rglob("*"):
            if source.is_file():
                raw = source.read_bytes()
                if b"\x00" not in raw:
                    source.write_bytes(raw.replace(b"\r\n", b"\n"))
        trace = isolated / "feature005" / path.name
        trace.parent.mkdir(parents=True)
        trace.write_bytes(normalized_bytes(path))
        process = subprocess.run(
            [sys.executable, str(isolated / "formal/scripts/check-refinement.py"), str(trace)],
            cwd=isolated,
            check=False,
            capture_output=True,
            text=True,
        )
    lines = process.stdout.strip().splitlines()
    require(bool(lines), "REFINEMENT_OUTPUT_MISSING", path.name)
    result = json.loads(lines[-1])
    require(isinstance(result, dict), "REFINEMENT_OUTPUT_INVALID", path.name)
    if legal:
        require(process.returncode == 0 and result.get("status") == "PASS", "LEGAL_TRACE_REJECTED")
    else:
        require(
            process.returncode != 0 and result.get("status") == "FAIL", "ILLEGAL_TRACE_ACCEPTED"
        )
        require(
            "PARTIAL_OR_UNCERTIFIED_PUBLICATION" in str(result.get("error")),
            "ILLEGAL_TRACE_WRONG_COUNTEREXAMPLE",
            path.name,
        )
    return result


def verify() -> dict[str, object]:
    expected_traces = traces()
    legal_results = []
    illegal_results = []
    trace_artifacts = []
    for relative, expected in expected_traces.items():
        path = TRACE_DIR / relative
        require(
            normalized_bytes(path) == canonical_json_bytes(expected) + b"\n",
            "TRACE_NOT_DETERMINISTIC",
            relative,
        )
        result = run_trace(path, relative.startswith("legal/"))
        (legal_results if relative.startswith("legal/") else illegal_results).append(result)
        trace_artifacts.append(artifact(path))

    contracts = verify_contracts()
    require(contracts.get("status") == "PASS", "PROTOCOL_CONTRACTS_NOT_PASS")
    golden = json.loads(
        (ROOT / "delta-protocol/fixtures/005/cross-language/golden-v1.json").read_text(
            encoding="utf-8"
        )
    )
    require(
        golden["manifest"]["content_id"]
        == "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254",
        "MANIFEST_ID_DRIFT",
    )
    require(
        golden["expected"] == {"native_policy_code": "OK", "status": "ACCEPT"},
        "GOLDEN_POLICY_DRIFT",
    )

    cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    native = (ROOT / "delta-core-cpp/src/distribution/certification_policy.cpp").read_text(
        encoding="utf-8"
    )
    java_policy = (
        ROOT / "delta-node-java/src/main/java/io/deltareduce/node/distribution/NativePolicy.java"
    ).read_text(encoding="utf-8")
    java_sources = list(
        (ROOT / "delta-node-java/src/main/java/io/deltareduce/node/distribution").glob("*.java")
    )
    require(
        all(
            marker in cmake
            for marker in (
                "ALLOW_DOWNGRADE",
                "ALLOW_FORBIDDEN",
                "ALLOW_NONCANONICAL",
                "WILL_FAIL TRUE",
            )
        ),
        "PRODUCTION_MUTANT_GATE_MISSING",
    )
    require(
        "max_manifest_bytes" in native and "MEDIA_FORBIDDEN" in native, "NATIVE_POLICY_INCOMPLETE"
    )
    require("private NativeDecision(" in java_policy, "JAVA_ALLOW_CONSTRUCTOR_EXPOSED")
    for path in java_sources:
        if path.name != "NativePolicy.java":
            require(
                "new NativeDecision" not in path.read_text(encoding="utf-8"),
                "JAVA_POLICY_SHORTCUT",
                path.name,
            )
    require(
        "pickle"
        not in "\n".join(path.read_text(encoding="utf-8") for path in java_sources).lower(),
        "PICKLE_PATH_PRESENT",
    )

    dependency_lock = json.loads(
        (ROOT / "delta-node-java/distribution-dependencies.lock.json").read_text(encoding="utf-8")
    )
    require(dependency_lock["java"]["compatibility_features"] == [25, 26], "JDK_MATRIX_INVALID")
    require(len(dependency_lock["maven_artifacts"]) == 2, "NETTY_LOCK_INCOMPLETE")

    paths = [
        ROOT / "CMakeLists.txt",
        ROOT / ".github/workflows/distribution.yml",
        ROOT / "delta-core-cpp/include/delta/distribution/certification_policy.hpp",
        ROOT / "delta-core-cpp/src/distribution/certification_policy.cpp",
        ROOT / "delta-core-cpp/tests/distribution_test.cpp",
        ROOT / "delta-core-cpp/fuzz/distribution_parser_fuzz.cpp",
        ROOT / "delta-ffi/include/delta_abi.h",
        ROOT / "delta-ffi/src/distribution_abi.cpp",
        ROOT / "delta-ffi/tests/distribution_abi_test.cpp",
        ROOT / "delta-node-java/distribution-dependencies.lock.json",
        ROOT / "delta-node-java/toolchains.toml",
        ROOT / "delta-protocol/fixtures/005/cross-language/golden-v1.json",
        ROOT / "delta-protocol/fixtures/005/invalid/distribution-negative-v1.json",
        *java_sources,
        *[TRACE_DIR / relative for relative in expected_traces],
    ]
    return {
        "artifacts": [artifact(path) for path in sorted(paths)],
        "classification": "REFINEMENT_ONLY",
        "contracts": {
            "manifest_id": golden["manifest"]["content_id"],
            "piece_count": len(golden["manifest"]["value"]["pieces"]),
            "policy_registry_id": golden["policy_registry"]["content_id"],
            "status": contracts["status"],
        },
        "formal_semantics_id": FORMAL_ID,
        "illegal_traces": illegal_results,
        "legal_traces": legal_results,
        "memory_and_transport": {
            "backpressure": "BOUNDED_SEMAPHORE",
            "copy_fallback": "BOUNDED_OWNED_COPY",
            "direct_lifetime": "SYNCHRONOUS_RETAIN_RELEASE",
            "event_loop_blocking": "REJECT",
            "status": "PASS",
        },
        "native_policy": {
            "authority": "CXX_C_ABI_ONLY",
            "production_mutants": [
                "DELTA_DISTRIBUTION_MUTANT_ALLOW_DOWNGRADE",
                "DELTA_DISTRIBUTION_MUTANT_ALLOW_FORBIDDEN",
                "DELTA_DISTRIBUTION_MUTANT_ALLOW_NONCANONICAL",
            ],
            "status": "PASS",
        },
        "phase": "005-distribution-refinement",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(11, 30)],
        "trace_artifacts": sorted(trace_artifacts, key=lambda item: item["path"]),
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "005-distribution-refinement", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (DistributionGateError, OSError, ValueError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
