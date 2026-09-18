"""T034: production audit redaction, recursive lineage guard and secret scan."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from deltacontroller.audit import AuditLogger, redact_sensitive_data
from deltacontroller.errors import SchemaValidationError
from deltacontroller.schema import SchemaRegistry
from security_support import CONTRACT_FREEZE_SHA, CONTRACTS_DIR, EVIDENCE_DIR, ROOT_DIR

HOSTILE_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ED25519 )?PRIVATE KEY-----"),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-.]{32,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"glpat-[a-zA-Z0-9\-_]{20}"),
    re.compile(r"xox[baprs]-[0-9]{10,}-[a-zA-Z0-9]{24,}"),
]

TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cmake",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".json",
    ".lean",
    ".md",
    ".mjs",
    ".py",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

SECRET_SCAN_EXCLUSIONS = {
    # This file intentionally carries detector regexes.
    "specs/admin-ui/step5c-controlled-live-execution/tests/test_t034_audit_secret_scan_redaction.py",
}


def iter_tracked_text_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT_DIR,
        check=True,
        text=True,
        capture_output=True,
    )
    paths: list[Path] = []
    for rel in result.stdout.splitlines():
        rel_norm = rel.replace("\\", "/")
        if rel_norm in SECRET_SCAN_EXCLUSIONS:
            continue
        path = ROOT_DIR / rel_norm
        if path.suffix.lower() in TEXT_EXTENSIONS:
            paths.append(path)
    return paths


def test_t034_tracked_repository_secret_scan_with_explicit_exclusions() -> None:
    scanned = 0
    for path in iter_tracked_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        for pattern in HOSTILE_SECRET_PATTERNS:
            match = pattern.search(text)
            assert match is None, f"Sensitive secret matched in tracked file {path}"

    assert scanned >= 900, f"Expected broad tracked repository scan, scanned {scanned}"


def test_t034_production_audit_logger_recursively_redacts_secrets(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_path=audit_path)
    raw_details = {
        "authorization": "Bearer " + "a" * 40,
        "nested": {
            "api_key": "sk-test-key",
            "messages": [
                {"token": "secret-token"},
                {"safe": "Bearer " + "b" * 40},
            ],
        },
        "safe_metric": 42,
    }

    event = logger.log_event(
        "SECURITY_NEGATIVE_TEST",
        "operator.alpha",
        raw_details,
        intent_id="11111111-1111-4111-8111-111111111111",
        execution_id="55555555-5555-4555-8555-555555555555",
    )
    serialized = audit_path.read_text(encoding="utf-8")

    assert event["details"]["authorization"] == "[REDACTED]"
    assert event["details"]["nested"]["api_key"] == "[REDACTED]"
    assert event["details"]["nested"]["messages"][0]["token"] == "[REDACTED]"
    assert event["details"]["nested"]["messages"][1]["safe"] == "[REDACTED]"
    assert event["details"]["safe_metric"] == 42
    assert "a" * 40 not in serialized
    assert "b" * 40 not in serialized
    assert "sk-test-key" not in serialized


def test_t034_redact_sensitive_data_handles_secret_bearing_strings() -> None:
    redacted = redact_sensitive_data(
        {
            "message": "Authorization failed for Bearer " + "c" * 40,
            "list": ["Bearer " + "d" * 40],
        }
    )

    assert redacted["message"] == "Authorization failed for [REDACTED]"
    assert redacted["list"] == ["[REDACTED]"]


def test_t034_recursive_receipt_lineage_guard_rejects_consensus_claims() -> None:
    registry = SchemaRegistry()
    invalid_names = [
        "receipt-lineage.consensus-field.json",
        "receipt-lineage.top-level-consensus-claim.json",
        "receipt-lineage.workload-consensus-claim.json",
        "receipt-lineage.execution-consensus-claim.json",
        "receipt-lineage.nested-arbitrary-state-root.json",
        "receipt-lineage.deep-array-wal-sequence.json",
    ]

    for name in invalid_names:
        fixture = json.loads(
            (CONTRACTS_DIR / "fixtures" / "invalid" / name).read_text(encoding="utf-8")
        )
        with pytest.raises(SchemaValidationError):
            registry.validate("receipt-lineage", fixture)


def test_t034_valid_receipts_have_lineage_and_no_consensus_fields() -> None:
    registry = SchemaRegistry()
    valid_receipts = list((CONTRACTS_DIR / "fixtures" / "valid").glob("*receipt*.json"))
    assert valid_receipts

    forbidden = {
        "round_id",
        "state_root",
        "wal_sequence",
        "qc",
        "apply_qc",
        "stage_c_proposal",
        "consensus_round",
        "consensus_view",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden.isdisjoint(value.keys())
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for path in valid_receipts:
        data = json.loads(path.read_text(encoding="utf-8"))
        registry.validate("receipt-lineage", data)
        walk(data)
        provenance = data["provenance"]
        for field in (
            "intent_id",
            "intent_digest",
            "admission_id",
            "admission_digest",
            "execution_id",
        ):
            assert field in provenance


def test_t034_immutable_evidence_files_valid() -> None:
    evidence_files = sorted(EVIDENCE_DIR.glob("t0*.json"))
    assert len(evidence_files) >= 6

    for ev_path in evidence_files:
        data = json.loads(ev_path.read_text(encoding="utf-8"))
        assert data["status"] in {
            "COMPLETE",
            "BLOCKED_ON_CONTROLLER_FIX",
            "BLOCKED_ON_WORKER_FIX",
            "BLOCKED_ON_ADMIN_UI_FIX",
        }
        assert data["contract_freeze_sha"] in {
            CONTRACT_FREEZE_SHA,
            "37407f9e69af70dcc8ba571b76bace199a281478",
        }
        if data["status"].startswith("BLOCKED_ON_"):
            assert data["finding_owner"]["component"]
            assert data["blocking_findings"]
