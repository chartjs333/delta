#!/usr/bin/env python3
"""Run the offline feature-001 foundation gate and verify its evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[3]
FEATURE_ROOT = ROOT / "specs" / "001-reproducible-training-baseline"
PREREQUISITE = FEATURE_ROOT / "scripts" / "verify_formal_prerequisite.py"
PREREQUISITE_EVIDENCE = FEATURE_ROOT / "evidence" / "formal-prerequisite.json"
DEFAULT_OUTPUT = FEATURE_ROOT / "evidence" / "foundation-gate.json"
EXPECTED_SEMANTICS_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PLACEHOLDERS = (
    "delta-core-cpp",
    "delta-runtime-cpp",
    "delta-ffi",
    "delta-node-java",
)
COMPONENTS = {
    "delta-protocol": "canonical-data",
    "delta-worker-python": "python-executable",
    "delta-core-cpp": "documentation-placeholder",
    "delta-runtime-cpp": "documentation-placeholder",
    "delta-ffi": "documentation-placeholder",
    "delta-node-java": "documentation-placeholder",
    "integration": "conformance-layout",
}
TASK_IDS = [
    "HR001-004",
    "HR001-005",
    "HR001-006",
    "HR001-007",
    "HR001-008",
    "HR001-009",
    "HR001-010",
    "HR001-011",
    "HR001-014",
    "HR001-015",
    "T001",
    "T002",
    "T003",
    "T004",
    "T005",
    "T006",
]
GATE_COMMANDS = (
    ("LOCK-CHECK", ("uv", "lock", "--check")),
    ("OFFLINE-SYNC", ("uv", "sync", "--frozen", "--offline")),
    ("RUFF-LINT", ("uv", "run", "ruff", "check", ".")),
    ("RUFF-FORMAT", ("uv", "run", "ruff", "format", "--check", ".")),
    ("MYPY", ("uv", "run", "mypy", "delta-worker-python/src")),
    (
        "PYTEST",
        ("uv", "run", "pytest", "delta-worker-python/tests", "-q"),
    ),
    (
        "FORMAL-PREREQUISITE",
        ("uv", "run", "python", PREREQUISITE.relative_to(ROOT).as_posix(), "--check-only"),
    ),
    (
        "PREREQUISITE-NEGATIVE-TESTS",
        (
            "uv",
            "run",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            "specs/001-reproducible-training-baseline/tests",
            "-v",
        ),
    ),
    ("FORMAL-ID-CLI", ("uv", "run", "delta", "formal-id")),
)
FOUNDATION_ROOT_FILES = (
    ".github/workflows/ci.yml",
    ".python-version",
    "Makefile",
    "docs/build.md",
    "docs/dependencies.md",
    "pyproject.toml",
    "uv.lock",
    "specs/001-reproducible-training-baseline/scripts/verify_foundation.py",
    "specs/001-reproducible-training-baseline/evidence/start-ready.md",
)
FOUNDATION_COMPONENT_FILES = (
    "delta-core-cpp/README.md",
    "delta-ffi/README.md",
    "delta-node-java/README.md",
    "delta-protocol/README.md",
    "delta-protocol/action-registry/formal-projection-v1.json",
    "delta-protocol/fixtures/canonical-json/canonical-json-v1.json",
    "delta-protocol/fixtures/formal/artifact-projection-v1.json",
    "delta-protocol/fixtures/safe-tensor/safe-tensor-i32-v1.json",
    "delta-protocol/registry.json",
    "delta-protocol/schemas/artifact-ref.schema.json",
    "delta-protocol/schemas/checkpoint-manifest.schema.json",
    "delta-protocol/schemas/formal-projection.schema.json",
    "delta-protocol/schemas/protocol-registry.schema.json",
    "delta-protocol/schemas/run-manifest.schema.json",
    "delta-protocol/schemas/safe-tensor-envelope-v1.json",
    "delta-runtime-cpp/README.md",
    "delta-worker-python/README.md",
    "delta-worker-python/pyproject.toml",
    "delta-worker-python/src/deltatorrent/__init__.py",
    "delta-worker-python/src/deltatorrent/cli.py",
    "delta-worker-python/src/deltatorrent/domain/__init__.py",
    "delta-worker-python/src/deltatorrent/domain/formal_compat.py",
    "delta-worker-python/src/deltatorrent/protocol/__init__.py",
    "delta-worker-python/src/deltatorrent/protocol/canonical.py",
    "delta-worker-python/src/deltatorrent/py.typed",
    "delta-worker-python/tests/architecture/test_dependency_boundaries.py",
    "delta-worker-python/tests/architecture/test_safe_serialization.py",
    "delta-worker-python/tests/conftest.py",
    "delta-worker-python/tests/contract/test_protocol_fixtures.py",
    "delta-worker-python/tests/contract/test_registry.py",
    "integration/README.md",
    "integration/cross-language/README.md",
    "integration/traces/README.md",
)


class FoundationError(RuntimeError):
    """A stable foundation-gate rejection."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def reject(code: str, detail: str = "") -> NoReturn:
    raise FoundationError(code, detail)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_repository_text(path: Path) -> str:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        reject("FOUNDATION_FILE_NOT_UTF8", f"{path.relative_to(ROOT).as_posix()}: {exc}")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_bytes(normalized.encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    require(path.is_file(), "JSON_FILE_MISSING", path.relative_to(ROOT).as_posix())
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{path.relative_to(ROOT).as_posix()}: {exc}")
    require(isinstance(value, dict), "JSON_ROOT_NOT_OBJECT", path.relative_to(ROOT).as_posix())
    return value


def foundation_paths() -> list[Path]:
    paths = [ROOT / relative for relative in (*FOUNDATION_ROOT_FILES, *FOUNDATION_COMPONENT_FILES)]
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def verify_layout() -> list[dict[str, str]]:
    for component in COMPONENTS:
        require((ROOT / component / "README.md").is_file(), "COMPONENT_README_MISSING", component)
    for component in PLACEHOLDERS:
        files = sorted(
            path.relative_to(ROOT / component).as_posix()
            for path in (ROOT / component).rglob("*")
            if path.is_file()
        )
        require(files == ["README.md"], "PLACEHOLDER_CONTAINS_CODE", component)

    records: list[dict[str, str]] = []
    for path in foundation_paths():
        require(path.is_file(), "FOUNDATION_FILE_MISSING", path.relative_to(ROOT).as_posix())
        records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256_repository_text(path),
            }
        )
    return records


def run_gates() -> list[dict[str, Any]]:
    environment = os.environ.copy()
    environment.update(
        {
            "ALL_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "localhost,127.0.0.1,::1",
            "UV_OFFLINE": "true",
        }
    )
    results: list[dict[str, Any]] = []
    for identifier, command in GATE_COMMANDS:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            detail = (completed.stdout + completed.stderr).strip()
            reject("GATE_COMMAND_FAILED", f"{identifier}: {detail}")
        results.append(
            {
                "argv": list(command),
                "id": identifier,
                "network": "LOOPBACK_ONLY",
                "status": "PASS",
            }
        )
    return results


def verify() -> dict[str, Any]:
    prerequisite = load_json(PREREQUISITE_EVIDENCE)
    require(prerequisite.get("status") == "PASS", "FORMAL_PREREQUISITE_NOT_PASS")
    require(
        prerequisite.get("formal_semantics_id") == EXPECTED_SEMANTICS_ID,
        "FORMAL_SEMANTICS_ID_MISMATCH",
    )
    files = verify_layout()
    commands = run_gates()
    return {
        "commands": commands,
        "components": [
            {"mode": mode, "path": path}
            for path, mode in sorted(COMPONENTS.items(), key=lambda item: item[0])
        ],
        "errors": [],
        "file_hash_mode": "SHA256_UTF8_LF",
        "files": files,
        "formal_prerequisite": {
            "path": PREREQUISITE_EVIDENCE.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(PREREQUISITE_EVIDENCE.read_bytes()),
            "status": "PASS",
        },
        "formal_semantics_id": EXPECTED_SEMANTICS_ID,
        "network_policy": "PUBLIC_NETWORK_BLOCKED",
        "schema_version": "1.0.0",
        "status": "PASS",
        "task_ids": TASK_IDS,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = verify()
        encoded = canonical_json_bytes(result)
        output = args.output.resolve()
        if args.check_only:
            require(output.is_file(), "FOUNDATION_EVIDENCE_MISSING")
            require(output.read_bytes() == encoded, "FOUNDATION_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (FoundationError, OSError, subprocess.SubprocessError) as exc:
        if isinstance(exc, FoundationError):
            code = exc.code
            detail = exc.detail
        else:
            code = type(exc).__name__.upper()
            detail = str(exc)
        failure = {
            "error_code": code,
            "errors": [detail] if detail else [],
            "formal_semantics_id": EXPECTED_SEMANTICS_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2

    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
