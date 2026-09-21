from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from deltatorrent.benchmark.canonical import canonical_bytes
from deltatorrent.benchmark.contracts import CanonicalContract, ContractError
from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "delta-protocol" / "fixtures" / "010" / "cross-language" / "foundation-v1.json"
SCHEMA = ROOT / "delta-protocol" / "schemas" / "010" / "foundation-contracts-v1.json"
GENERATOR = ROOT / "specs" / "010-wan-benchmark-and-quality" / "scripts" / "foundation_fixtures.py"
CONFORMANCE = ROOT / "specs" / "010-wan-benchmark-and-quality" / "conformance"


def _document() -> dict[str, object]:
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_golden_fixture_is_reproducible_and_every_wrapper_is_exact() -> None:
    process = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    document = _document()
    artifacts = document["artifacts"]
    assert isinstance(artifacts, dict)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_names = {
        "arm": "BenchmarkArm",
        "attestation": "AttestationManifest",
        "definition": "BenchmarkDefinition",
        "evidence_manifest": "EvidenceManifest",
        "evidence_node": "EvidenceNode",
        "result": "BenchmarkResult",
        "run_manifest": "RunManifest",
    }
    for name, definition_name in schema_names.items():
        wrapper = artifacts[name]
        assert isinstance(wrapper, dict)
        value = wrapper["value"]
        encoded = bytes.fromhex(str(wrapper["bytes_hex"]))
        assert encoded == canonical_bytes(value)
        assert wrapper["content_id"] == "sha256:" + hashlib.sha256(encoded).hexdigest()
        assert CanonicalContract.from_bytes(encoded).to_dict() == value
        validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$defs": schema["$defs"],
                "$ref": f"#/$defs/{definition_name}",
            }
        )
        assert not list(validator.iter_errors(value))


def test_golden_negative_vectors_fail_closed() -> None:
    artifacts = _document()["artifacts"]
    definition_bytes = bytes.fromhex(str(artifacts["definition"]["bytes_hex"]))
    with pytest.raises(ValueError, match="JSON_BYTES_NOT_CANONICAL"):
        CanonicalContract.from_bytes(b" " + definition_bytes)
    run = dict(artifacts["run_manifest"]["value"])
    run["primary_eligible"] = True
    with pytest.raises(ContractError, match="PRIMARY_ELIGIBILITY_FORBIDDEN"):
        CanonicalContract.from_dict(run)


def test_java_fixture_consumer_checks_exact_bytes_and_sha256(tmp_path: Path) -> None:
    javac = shutil.which("javac")
    java = shutil.which("java")
    if javac is None or java is None:
        pytest.skip("JDK unavailable")
    source = CONFORMANCE / "FoundationFixtureConsumer.java"
    subprocess.run([javac, "-d", str(tmp_path), str(source)], check=True, cwd=ROOT)
    process = subprocess.run(
        [java, "-cp", str(tmp_path), "FoundationFixtureConsumer", str(FIXTURE)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert process.stdout.strip() == _document()["artifacts"]["arm"]["content_id"]
    expected_id = str(_document()["artifacts"]["arm"]["content_id"])
    corrupted = tmp_path / "corrupted-foundation.json"
    corrupted.write_text(
        FIXTURE.read_text(encoding="utf-8").replace(
            f'"content_id":"{expected_id}"',
            '"content_id":"sha256:' + "0" * 64 + '"',
            1,
        ),
        encoding="utf-8",
    )
    rejected = subprocess.run(
        [java, "-cp", str(tmp_path), "FoundationFixtureConsumer", str(corrupted)],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0


def test_cpp_fixture_consumer_checks_exact_bytes_when_compiler_is_available(
    tmp_path: Path,
) -> None:
    compiler = next(
        (candidate for name in ("c++", "g++", "clang++") if (candidate := shutil.which(name))),
        None,
    )
    if compiler is None:
        pytest.skip("standalone C++ compiler unavailable")
    source = CONFORMANCE / "foundation_fixture_consumer.cpp"
    executable = tmp_path / "foundation_fixture_consumer"
    subprocess.run(
        [compiler, "-std=c++20", str(source), "-o", str(executable)],
        check=True,
        cwd=ROOT,
    )
    process = subprocess.run(
        [str(executable), str(FIXTURE)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert process.stdout.strip() == _document()["artifacts"]["arm"]["content_id"]
    expected_id = str(_document()["artifacts"]["arm"]["content_id"])
    corrupted = tmp_path / "corrupted-foundation.json"
    corrupted.write_text(
        FIXTURE.read_text(encoding="utf-8").replace(
            f'"content_id":"{expected_id}"',
            '"content_id":"sha256:' + "0" * 64 + '"',
            1,
        ),
        encoding="utf-8",
    )
    rejected = subprocess.run(
        [str(executable), str(corrupted)],
        check=False,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0
