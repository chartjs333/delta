"""Semantic verification for retained Campaign 02 Stage A workflow artifacts."""

from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

NATIVE_TESTS: Final = (
    "delta_core.certificates",
    "delta_ffi.abi",
    "delta_ffi.certificate_chain",
    "delta_ffi.certificate_chain_mutant_observed_coverage",
    "delta_ffi.certificate_chain_mutant_seed_parent",
    "delta_ffi.certificates",
    "delta_ffi.hierarchy",
    "delta_ffi.scheduling",
    "delta_runtime.behavior",
)
PYTHON_TEST_PATHS: Final = (
    "delta-worker-python/tests/benchmark/test_campaign02_execution_binding.py",
    "delta-worker-python/tests/benchmark/test_native_chain_conformance.py",
)
JAVA_MARKERS: Final = (
    "native runtime FFM compatible on JDK {feature}: exact effects",
    "native hierarchy/routing compatible on JDK {feature}:",
    "certificate adapters compatible on JDK {feature}:",
    "native scheduling adapter compatible on JDK {feature}:",
    "CROSS_LANGUAGE",
)
EXPECTED_FILENAMES: Final = frozenset(
    {
        "java-jdk25.log",
        "java-jdk26.log",
        "native-clang-cpp20.xml",
        "native-clang-cpp23.xml",
        "native-gcc-cpp20.xml",
        "native-gcc-cpp23.xml",
        "python-cross-component.xml",
    }
)


class StageAEvidenceError(ValueError):
    """Stable fail-closed Stage A artifact rejection."""


def _fail(code: str) -> StageAEvidenceError:
    return StageAEvidenceError(code)


@dataclass(frozen=True, slots=True)
class VerifiedArtifactSummary:
    filename: str
    raw_digest: str
    evidence_type: str
    verified_items: tuple[str, ...]
    test_count: int

    @property
    def document(self) -> dict[str, object]:
        return {
            "evidence_type": self.evidence_type,
            "filename": self.filename,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "raw_digest": self.raw_digest,
            "schema_version": "1.0.0",
            "test_count": self.test_count,
            "type_name": "CAMPAIGN02_STAGE_A_VERIFIED_ARTIFACT_SUMMARY",
            "verified_items": list(self.verified_items),
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-a-artifact-summary.v1\0"
            + canonical_json_bytes(self.document)
        )


@dataclass(frozen=True, slots=True)
class StageASemanticEvidenceSummary:
    artifacts: tuple[VerifiedArtifactSummary, ...]

    @property
    def document(self) -> dict[str, object]:
        return {
            "artifact_summaries": [item.document for item in self.artifacts],
            "artifact_summary_ids": [item.content_id for item in self.artifacts],
            "decision": "PASS",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "schema_version": "1.0.0",
            "type_name": "CAMPAIGN02_STAGE_A_SEMANTIC_EVIDENCE_SUMMARY",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-stage-a-semantic-evidence.v1\0"
            + canonical_json_bytes(self.document)
        )


def _junit_cases(path: Path) -> tuple[tuple[str, str], ...]:
    try:
        root = ElementTree.fromstring(path.read_bytes())
    except (OSError, ElementTree.ParseError) as exc:
        raise _fail("CAMPAIGN02_STAGE_A_JUNIT_INVALID") from exc
    suites = (root,) if root.tag == "testsuite" else tuple(root.findall("testsuite"))
    if not suites:
        raise _fail("CAMPAIGN02_STAGE_A_JUNIT_INVALID")
    cases: list[tuple[str, str]] = []
    for suite in suites:
        for field in ("tests", "failures", "errors", "skipped"):
            value = suite.get(field)
            if value is None or re.fullmatch(r"[0-9]+", value) is None:
                raise _fail("CAMPAIGN02_STAGE_A_JUNIT_COUNTER_INVALID")
        if any(int(suite.get(field, "-1")) != 0 for field in ("failures", "errors", "skipped")):
            raise _fail("CAMPAIGN02_STAGE_A_JUNIT_NOT_PASS")
        for case in suite.findall("testcase"):
            name = case.get("name")
            classname = case.get("classname", "")
            if not name or case.find("failure") is not None or case.find("error") is not None:
                raise _fail("CAMPAIGN02_STAGE_A_JUNIT_CASE_INVALID")
            cases.append((classname, name))
    if not cases or len(set(cases)) != len(cases):
        raise _fail("CAMPAIGN02_STAGE_A_JUNIT_CASE_SET_INVALID")
    return tuple(sorted(cases))


def _collect_python_cases(source_root: Path) -> tuple[tuple[str, str], ...]:
    process = subprocess.run(
        (sys.executable, "-m", "pytest", "--collect-only", "-q", *PYTHON_TEST_PATHS),
        cwd=source_root,
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.returncode != 0:
        raise _fail("CAMPAIGN02_STAGE_A_PYTHON_COLLECTION_FAILED")
    cases: list[tuple[str, str]] = []
    for line in process.stdout.splitlines():
        if "::" not in line or line.startswith(("=", "<")):
            continue
        path, *parts = line.strip().split("::")
        if not path.endswith(".py") or not parts:
            continue
        classname_parts = [path[:-3].replace("\\", "/").replace("/", ".")]
        if len(parts) > 1:
            classname_parts.extend(parts[:-1])
        cases.append((".".join(classname_parts), parts[-1]))
    if not cases or len(set(cases)) != len(cases):
        raise _fail("CAMPAIGN02_STAGE_A_PYTHON_COLLECTION_INVALID")
    return tuple(sorted(cases))


def _junit_summary(
    path: Path,
    *,
    expected: tuple[tuple[str, str], ...] | tuple[str, ...],
    python: bool,
) -> VerifiedArtifactSummary:
    cases = _junit_cases(path)
    actual_names = tuple(name for _classname, name in cases)
    if (python and cases != expected) or (not python and actual_names != tuple(sorted(expected))):
        raise _fail("CAMPAIGN02_STAGE_A_JUNIT_TEST_SET_MISMATCH")
    verified = tuple(f"{classname}::{name}" for classname, name in cases)
    return VerifiedArtifactSummary(
        filename=path.name,
        raw_digest=sha256_content_id(path.read_bytes()),
        evidence_type="PYTHON_JUNIT" if python else "NATIVE_CTEST_JUNIT",
        verified_items=verified,
        test_count=len(cases),
    )


def _java_summary(path: Path, feature: int, version: str) -> VerifiedArtifactSummary:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _fail("CAMPAIGN02_STAGE_A_JAVA_LOG_INVALID") from exc
    lines = tuple(line.strip() for line in text.splitlines() if line.strip())
    expected_markers = tuple(item.format(feature=feature) for item in JAVA_MARKERS)
    if (
        not lines
        or not re.search(rf'^(?:openjdk|java) version "{re.escape(version)}"', lines[0])
        or any(not any(marker in line for line in lines) for marker in expected_markers)
    ):
        raise _fail("CAMPAIGN02_STAGE_A_JAVA_SEMANTICS_INVALID")
    return VerifiedArtifactSummary(
        filename=path.name,
        raw_digest=sha256_content_id(path.read_bytes()),
        evidence_type="JAVA_CONFORMANCE_LOG",
        verified_items=(f"JDK_VERSION:{version}", *expected_markers),
        test_count=len(expected_markers),
    )


def verify_stage_a_artifacts(
    paths: tuple[Path, ...],
    *,
    source_root: Path,
    expected_python_cases: tuple[tuple[str, str], ...] | None = None,
) -> StageASemanticEvidenceSummary:
    """Parse all seven retained files and return canonical verified summaries."""
    by_name = {path.name: path for path in paths}
    if len(by_name) != len(paths) or set(by_name) != EXPECTED_FILENAMES:
        raise _fail("CAMPAIGN02_STAGE_A_EXACTNESS_MATRIX_INCOMPLETE")
    python_cases = (
        expected_python_cases
        if expected_python_cases is not None
        else _collect_python_cases(source_root)
    )
    summaries: list[VerifiedArtifactSummary] = []
    for compiler in ("clang", "gcc"):
        for standard in (20, 23):
            path = by_name[f"native-{compiler}-cpp{standard}.xml"]
            summaries.append(
                _junit_summary(path, expected=tuple(sorted(NATIVE_TESTS)), python=False)
            )
    summaries.extend(
        (
            _java_summary(by_name["java-jdk25.log"], 25, "25.0.4.1"),
            _java_summary(by_name["java-jdk26.log"], 26, "26.0.2"),
            _junit_summary(
                by_name["python-cross-component.xml"],
                expected=python_cases,
                python=True,
            ),
        )
    )
    return StageASemanticEvidenceSummary(tuple(sorted(summaries, key=lambda item: item.filename)))
