"""Generate exact-source QLoRA distribution/composition evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/transport-runtime.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FILES: Final = (
    ".github/workflows/qlora.yml",
    "CMakeLists.txt",
    "delta-core-cpp/include/delta/qlora/distribution.hpp",
    "delta-core-cpp/src/qlora/distribution.cpp",
    "delta-core-cpp/tests/qlora_apply_test.cpp",
    "delta-node-java/src/main/java/io/deltareduce/node/qlora/AdapterTransport.java",
    "delta-node-java/src/main/java/io/deltareduce/node/qlora/BaseObjectCache.java",
    "delta-node-java/src/main/java/io/deltareduce/node/qlora/ModelComposition.java",
    "delta-node-java/src/main/java/io/deltareduce/node/qlora/QloraContracts.java",
    "delta-node-java/src/main/java/io/deltareduce/node/qlora/QloraTelemetry.java",
    "delta-node-java/src/test/java/io/deltareduce/node/qlora/QloraConformance.java",
    "delta-worker-python/src/deltatorrent/qlora/composition.py",
    "delta-worker-python/tests/qlora/test_composition.py",
    "specs/009-qlora-8gb-mode/scripts/verify_transport_runtime.py",
)
JAVA_SOURCES: Final = (
    *(
        "delta-node-java/src/main/java/io/deltareduce/node/qlora/" + name
        for name in (
            "AdapterTransport.java",
            "BaseObjectCache.java",
            "ModelComposition.java",
            "QloraContracts.java",
            "QloraTelemetry.java",
        )
    ),
    "delta-node-java/src/test/java/io/deltareduce/node/qlora/QloraConformance.java",
)


def run(*args: str) -> str:
    return subprocess.run(
        args, cwd=ROOT, check=True, capture_output=True, encoding="utf-8", errors="replace"
    ).stdout.strip()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def exercise() -> dict[str, object]:
    javac = shutil.which("javac")
    java = shutil.which("java")
    if javac is None or java is None:
        raise RuntimeError("LOCAL_JAVA_TOOLCHAIN_UNAVAILABLE")
    with tempfile.TemporaryDirectory(prefix="delta-009-java-") as classes:
        run(javac, "--release", "17", "-Xlint:all", "-Werror", "-d", classes, *JAVA_SOURCES)
        java_output = run(java, "-cp", classes, "io.deltareduce.node.qlora.QloraConformance")
    if "zero-base-refetch/native-auth/resume/license" not in java_output:
        raise RuntimeError("JAVA_QLORA_CONFORMANCE_FAILED")
    run("cmake", "--preset", "cpp20")
    run("cmake", "--build", "--preset", "cpp20", "--target", "delta_qlora_apply_test")
    native = run("ctest", "--preset", "cpp20", "-R", "qlora", "--output-on-failure")
    if "100% tests passed" not in native:
        raise RuntimeError("NATIVE_QLORA_MEDIA_POLICY_FAILED")
    python = run(
        "uv",
        "run",
        "pytest",
        "delta-worker-python/tests/qlora/test_composition.py",
        "-q",
    )
    if "3 passed" not in python:
        raise RuntimeError("PYTHON_QLORA_COMPOSITION_FAILED")
    return {
        "ci_jdk_lanes": {"required": [25, 26], "status": "REGISTERED_PENDING_RUN"},
        "local_java": {"release": 17, "summary": "PASS"},
        "native_media_policy": "PASS",
        "python_composition": "3 passed",
    }


def build(commit: str) -> dict[str, object]:
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    if formal_diff:
        raise RuntimeError("FORMAL_SOURCE_DIFF")
    return {
        "checks": [
            "NATIVE_CERTIFIED_BASE_AND_APPLY_QC_ADAPTER_MEDIA_REGISTRY",
            "JAVA_CONTENT_ADDRESSED_BASE_TOKENIZER_PROFILE_CACHE",
            "SECOND_ADAPTER_FETCH_TRANSFERS_ZERO_BASE_BYTES",
            "NATIVE_AUTHORIZED_COMPOSITION_IN_PYTHON_AND_JAVA",
            "INCOMPATIBLE_RESUME_REJECTED_ACROSS_BOUNDARIES",
            "DERIVED_EXPORT_LICENSE_AND_PROVENANCE_ENFORCED",
            "JAVA_HAS_NO_CERTIFICATE_OR_CURRENT_STATE_AUTHORITY",
            "PINNED_JDK25_AND_JDK26_CI_LANES_REGISTERED",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": [
                {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
                for path in FILES
            ],
            "commit": commit,
            "tree": run("git", "show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": [
            "T032",
            "T033",
            "T034",
            "T035",
            "T036",
            "HR009-007",
            "HR009-010",
        ],
        "tests": exercise(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.check_only:
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = build(str(report["source"]["commit"]))
        if report != expected:
            raise RuntimeError("TRANSPORT_RUNTIME_EVIDENCE_MISMATCH")
    else:
        if run("git", "status", "--porcelain"):
            raise RuntimeError("SOURCE_TREE_NOT_CLEAN")
        report = build(run("git", "rev-parse", "HEAD"))
        OUTPUT.write_text(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
