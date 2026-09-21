"""Git-object-bound zero-tolerance preflight for the Feature 010 foundation."""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from deltatorrent.benchmark.canonical import canonical_bytes, content_id, load_json_bytes
from deltatorrent.benchmark.contracts import CanonicalContract, ContractError

PREFLIGHT_POLICY_ID = "feature010-zero-tolerance-v1"
DEFAULT_INCLUDE_PATHS = (
    "configs/benchmark/",
    "delta-protocol/fixtures/010/",
    "delta-protocol/registry.json",
    "delta-protocol/schemas/010/",
    "delta-worker-python/pyproject.toml",
    "delta-worker-python/src/deltatorrent/benchmark/",
    "delta-worker-python/tests/benchmark/conftest.py",
    "specs/010-wan-benchmark-and-quality/conformance/",
    "specs/010-wan-benchmark-and-quality/scripts/foundation_fixtures.py",
    "uv.lock",
)
DEFAULT_REQUIRED_PREFIXES = (
    "configs/benchmark/",
    "delta-protocol/fixtures/010/",
    "delta-protocol/schemas/010/",
    "delta-worker-python/pyproject.toml",
    "delta-worker-python/src/deltatorrent/benchmark/",
    "delta-worker-python/tests/benchmark/conftest.py",
    "specs/010-wan-benchmark-and-quality/conformance/",
    "specs/010-wan-benchmark-and-quality/scripts/foundation_fixtures.py",
    "uv.lock",
)
_FORBIDDEN_TEXT_PATTERNS = {
    "ADAPTIVE_H_ENABLED": re.compile(r"\badaptive[_-]?h\b['\"]?\s*[:=]\s*(?:true|True|1)"),
    "CENTRAL_CURRENT_AUTHORITY": re.compile(
        r"\bcurrent[_-]?authority\b['\"]?\s*[:=]\s*['\"]?"
        r"(?!NATIVE_RUNTIME\b)(?:CENTRAL|JAVA|PYTHON)\b",
        re.IGNORECASE,
    ),
    "FLOAT_CONSENSUS_FALLBACK": re.compile(
        r"\bconsensus[_-]?arithmetic\b['\"]?\s*[:=]\s*['\"]?"
        r"(?:FLOAT|FLOATING_POINT|FP)\b",
        re.IGNORECASE,
    ),
    "PRIMARY_FIXTURE_PROMOTION": re.compile(
        r"\bevidence[_-]?class\b['\"]?\s*[:=]\s*['\"]?PRIMARY\b", re.IGNORECASE
    ),
    "REAL_WAN_RELABEL": re.compile(r"\blabel\b['\"]?\s*[:=]\s*['\"]?REAL_WAN\b", re.IGNORECASE),
    "STALE_ACCEPTANCE_ENABLED": re.compile(r"\baccept[_-]?stale\b['\"]?\s*[:=]\s*(?:true|True|1)"),
    "THRESHOLD_OVERRIDE_ENABLED": re.compile(
        r"\bthreshold[_-]?override\b['\"]?\s*[:=]\s*(?:true|True|1)"
    ),
}


@dataclass(frozen=True, slots=True)
class GitBlob:
    path: str
    mode: str
    git_blob_id: str
    sha256: str
    byte_length: int
    value: bytes

    def manifest_dict(self) -> dict[str, object]:
        return {
            "byte_length": self.byte_length,
            "git_blob_id": self.git_blob_id,
            "mode": self.mode,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class GitTreeSnapshot:
    source_commit: str
    source_tree: str
    include_paths: tuple[str, ...]
    blobs: tuple[GitBlob, ...]

    @property
    def manifest_id(self) -> str:
        return content_id(canonical_bytes([blob.manifest_dict() for blob in self.blobs]))


@dataclass(frozen=True, slots=True)
class PreflightFinding:
    code: str
    path: str
    line: int


@dataclass(frozen=True, slots=True)
class PreflightReport:
    source_commit: str
    source_tree: str
    include_paths: tuple[str, ...]
    scanned_paths: tuple[str, ...]
    source_manifest_id: str
    findings: tuple[PreflightFinding, ...]
    policy_id: str = PREFLIGHT_POLICY_ID

    @property
    def status(self) -> str:
        return "PASS" if not self.findings else "FAIL"


def _git(repo: Path, *arguments: str) -> bytes:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    process = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        env=environment,
        check=False,
        capture_output=True,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ContractError(f"PREFLIGHT_GIT_COMMAND_FAILED:{detail}")
    return process.stdout


def load_git_tree_snapshot(
    repo: Path,
    *,
    source_commit: str,
    expected_tree: str,
    include_paths: tuple[str, ...] = DEFAULT_INCLUDE_PATHS,
    required_prefixes: tuple[str, ...] = DEFAULT_REQUIRED_PREFIXES,
) -> GitTreeSnapshot:
    """Load only regular UTF-8 blobs from one exact immutable Git tree."""

    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ContractError("PREFLIGHT_SOURCE_COMMIT_INVALID")
    if re.fullmatch(r"[0-9a-f]{40}", expected_tree) is None:
        raise ContractError("PREFLIGHT_SOURCE_TREE_INVALID")
    resolved_commit = (
        _git(repo, "rev-parse", "--verify", f"{source_commit}^{{commit}}").decode().strip()
    )
    if resolved_commit != source_commit:
        raise ContractError("PREFLIGHT_SOURCE_COMMIT_MISMATCH")
    source_tree = _git(repo, "rev-parse", f"{source_commit}^{{tree}}").decode().strip()
    if source_tree != expected_tree:
        raise ContractError("PREFLIGHT_SOURCE_TREE_MISMATCH")
    if not include_paths or tuple(sorted(set(include_paths))) != include_paths:
        raise ContractError("PREFLIGHT_INCLUDE_PATHS_INVALID")
    raw_entries = _git(
        repo,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        source_commit,
        "--",
        *include_paths,
    )
    blobs: list[GitBlob] = []
    for raw_entry in raw_entries.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode, object_type, raw_oid = metadata.split(b" ", 2)
            path = raw_path.decode("utf-8", errors="strict")
            oid = raw_oid.decode("ascii", errors="strict")
            decoded_mode = mode.decode("ascii", errors="strict")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ContractError("PREFLIGHT_TREE_ENTRY_INVALID") from exc
        if not path or "\\" in path or path.startswith("/") or ".." in path.split("/"):
            raise ContractError("PREFLIGHT_PATH_INVALID")
        if object_type != b"blob" or decoded_mode not in {"100644", "100755"}:
            raise ContractError("PREFLIGHT_NON_REGULAR_ENTRY_FORBIDDEN")
        value = _git(repo, "cat-file", "blob", oid)
        try:
            value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ContractError("PREFLIGHT_SOURCE_NOT_UTF8") from exc
        blobs.append(
            GitBlob(
                path=path,
                mode=decoded_mode,
                git_blob_id=oid,
                sha256=hashlib.sha256(value).hexdigest(),
                byte_length=len(value),
                value=value,
            )
        )
    blobs.sort(key=lambda blob: blob.path)
    if not blobs or len({blob.path for blob in blobs}) != len(blobs):
        raise ContractError("PREFLIGHT_SOURCE_MANIFEST_INVALID")
    for prefix in required_prefixes:
        if not any(blob.path.startswith(prefix) for blob in blobs):
            raise ContractError(f"PREFLIGHT_REQUIRED_PREFIX_EMPTY:{prefix}")
    return GitTreeSnapshot(
        source_commit=source_commit,
        source_tree=source_tree,
        include_paths=include_paths,
        blobs=tuple(blobs),
    )


def _json_findings(path: str, value: object) -> list[PreflightFinding]:
    findings: list[PreflightFinding] = []

    def walk(item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                normalized = str(key).lower()
                checks = {
                    "accept_stale": (child is True, "STALE_ACCEPTANCE_ENABLED"),
                    "adaptive_h": (child is True, "ADAPTIVE_H_ENABLED"),
                    "threshold_override": (child is True, "THRESHOLD_OVERRIDE_ENABLED"),
                    "current_authority": (
                        isinstance(child, str) and child != "NATIVE_RUNTIME",
                        "CENTRAL_CURRENT_AUTHORITY",
                    ),
                    "consensus_arithmetic": (
                        isinstance(child, str) and child != "CHECKED_FIXED_POINT",
                        "FLOAT_CONSENSUS_FALLBACK",
                    ),
                    "evidence_class": (child == "PRIMARY", "PRIMARY_FIXTURE_PROMOTION"),
                    "label": (child == "REAL_WAN", "REAL_WAN_RELABEL"),
                }
                if normalized in checks and checks[normalized][0]:
                    findings.append(PreflightFinding(checks[normalized][1], path, 1))
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return findings


def _python_findings(path: str, text: str) -> list[PreflightFinding]:
    """Inspect literal policy mappings without executing repository code."""

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[PreflightFinding] = []

    def inspect_literal(key: str, value: object, line: int) -> None:
        checks = {
            "accept_stale": (value is True, "STALE_ACCEPTANCE_ENABLED"),
            "adaptive_h": (value is True, "ADAPTIVE_H_ENABLED"),
            "threshold_override": (value is True, "THRESHOLD_OVERRIDE_ENABLED"),
            "current_authority": (
                isinstance(value, str) and value != "NATIVE_RUNTIME",
                "CENTRAL_CURRENT_AUTHORITY",
            ),
            "consensus_arithmetic": (
                isinstance(value, str) and value != "CHECKED_FIXED_POINT",
                "FLOAT_CONSENSUS_FALLBACK",
            ),
            "evidence_class": (value == "PRIMARY", "PRIMARY_FIXTURE_PROMOTION"),
            "label": (value == "REAL_WAN", "REAL_WAN_RELABEL"),
        }
        if key in checks and checks[key][0]:
            findings.append(PreflightFinding(checks[key][1], path, line))

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key_node, value_node in zip(node.keys, node.values, strict=True):
                if (
                    isinstance(key_node, ast.Constant)
                    and isinstance(key_node.value, str)
                    and isinstance(value_node, ast.Constant)
                ):
                    inspect_literal(key_node.value.lower(), value_node.value, node.lineno)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Constant):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    inspect_literal(target.id.lower(), node.value.value, node.lineno)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg is not None and isinstance(keyword.value, ast.Constant):
                    inspect_literal(keyword.arg.lower(), keyword.value.value, node.lineno)
    return findings


def scan_snapshot(snapshot: GitTreeSnapshot) -> PreflightReport:
    findings: list[PreflightFinding] = []
    scanned_paths: list[str] = []
    for blob in snapshot.blobs:
        scanned_paths.append(blob.path)
        text = blob.value.decode("utf-8")
        if blob.path.endswith(".py"):
            findings.extend(_python_findings(blob.path, text))
        if blob.path.endswith(".json"):
            try:
                document = load_json_bytes(blob.value, require_canonical=False)
            except ValueError:
                document = None
            if document is not None:
                findings.extend(_json_findings(blob.path, document))
        for line_number, line in enumerate(text.splitlines(), start=1):
            for code, pattern in _FORBIDDEN_TEXT_PATTERNS.items():
                if pattern.search(line):
                    findings.append(PreflightFinding(code, blob.path, line_number))
    return PreflightReport(
        source_commit=snapshot.source_commit,
        source_tree=snapshot.source_tree,
        include_paths=snapshot.include_paths,
        scanned_paths=tuple(scanned_paths),
        source_manifest_id=snapshot.manifest_id,
        findings=tuple(sorted(set(findings), key=lambda item: (item.path, item.line, item.code))),
    )


def scan_git_tree(
    repo: Path,
    *,
    source_commit: str,
    expected_tree: str,
    include_paths: tuple[str, ...] = DEFAULT_INCLUDE_PATHS,
    required_prefixes: tuple[str, ...] = DEFAULT_REQUIRED_PREFIXES,
) -> PreflightReport:
    return scan_snapshot(
        load_git_tree_snapshot(
            repo,
            source_commit=source_commit,
            expected_tree=expected_tree,
            include_paths=include_paths,
            required_prefixes=required_prefixes,
        )
    )


def run_required_preflight(
    repo: Path,
    *,
    source_commit: str,
    expected_tree: str,
) -> PreflightReport:
    """Run the authoritative policy with non-caller-selectable source coverage."""

    report = scan_git_tree(
        repo,
        source_commit=source_commit,
        expected_tree=expected_tree,
        include_paths=DEFAULT_INCLUDE_PATHS,
        required_prefixes=DEFAULT_REQUIRED_PREFIXES,
    )
    if report.include_paths != DEFAULT_INCLUDE_PATHS or report.policy_id != PREFLIGHT_POLICY_ID:
        raise ContractError("PREFLIGHT_POLICY_BINDING_MISMATCH")
    return report


def validate_definition_preflight(definition: CanonicalContract) -> None:
    """Assert that a validated definition retains the structural STOP policy."""

    if definition.type_name != "BENCHMARK_DEFINITION":
        raise ContractError("PREFLIGHT_DEFINITION_TYPE_INVALID")
    policy = definition.to_dict()["policy"]
    expected = {
        "accept_stale": False,
        "adaptive_h": False,
        "consensus_arithmetic": "CHECKED_FIXED_POINT",
        "current_authority": "NATIVE_RUNTIME",
        "threshold_override": False,
    }
    if policy != expected:
        raise ContractError("ZERO_TOLERANCE_POLICY_VIOLATION")
