"""T016: AuthorizationGate end-to-end admission, Ed25519 signing, status, and audit redaction."""

from __future__ import annotations

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.audit import AuditLogger, redact_sensitive_data
from deltacontroller.auth import AuthenticatedSubject, StaticAuthenticationPort
from deltacontroller.canonical import compute_intent_digest, verify_admission_signature
from deltacontroller.dispatch import MockWorkerDispatchPort
from deltacontroller.errors import QuotaExceededError, WorkerDispatchFailedError
from deltacontroller.gate import AdmissionSigningIdentity, AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.quota import CEILING_MAX_MEMORY_BYTES, QuotaManager, ResourceGrants

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)

TEST_PEER_ID = "peer-uid-1000"
TEST_SUBJECT = AuthenticatedSubject(
    subject_id="operator.alpha",
    authenticated_via="LOCAL_PEER_CREDENTIAL",
    effective_roles=["OPERATOR"],
)
TEST_BUILD_SHA = "ab1e522e07f3a2207ec37e3c2e2d4943b48a3a6e"


def _load_train_ticket() -> dict:
    intent_path = CONTRACTS_ROOT / "fixtures" / "valid" / "execution-intent.train-ticket.json"
    with intent_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _trusted_auth_port() -> StaticAuthenticationPort:
    return StaticAuthenticationPort(
        allow_local_peer=True,
        peer_subjects={TEST_PEER_ID: TEST_SUBJECT},
    )


def _test_signing_identity(
    private_key: Ed25519PrivateKey | None = None,
) -> AdmissionSigningIdentity:
    return AdmissionSigningIdentity(
        private_key=private_key or Ed25519PrivateKey.generate(),
        key_id="controller-test-key-v1",
        issuer_id="controller-test-issuer",
    )


def _operator_credentials() -> dict:
    return {
        "type": "LOCAL_PEER_CREDENTIAL",
        "subject_id": TEST_PEER_ID,
        "roles": ["AUDITOR"],
    }


def test_full_authorization_pipeline_success(tmp_path: Path) -> None:
    intent_doc = _load_train_ticket()

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    dispatch_mock = MockWorkerDispatchPort()

    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(private_key),
        idempotency_ledger=IdempotencyLedger(tmp_path / "ledger.jsonl"),
        dispatch_port=dispatch_mock,
    )

    now = datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC)
    credentials = _operator_credentials()

    result = gate.admit_and_dispatch(intent_doc, credentials=credentials, current_time=now)
    assert result["action"] == "ADMITTED"
    assert "bundle" not in result

    admission = result["admission"]
    assert admission["schema_version"] == "1.0.0"
    assert admission["intent_id"] == intent_doc["intent_id"]
    assert admission["intent_digest"] == intent_doc["intent_digest"]
    assert admission["policy_context"]["verdict"] == "ADMITTED"
    assert admission["authenticated_subject"] == TEST_SUBJECT.to_dict()
    assert admission["authenticator"]["key_id"] == "controller-test-key-v1"
    assert admission["authenticator"]["issuer_id"] == "controller-test-issuer"

    # Verify Ed25519 signature over admission
    assert verify_admission_signature(admission, public_key) is True

    # Verify deadline invariants
    admitted_at = datetime.fromisoformat(admission["admitted_at"].replace("Z", "+00:00"))
    admission_expires_at = datetime.fromisoformat(
        admission["admission_expires_at"].replace("Z", "+00:00")
    )
    intent_expires_at = datetime.fromisoformat(intent_doc["expires_at"].replace("Z", "+00:00"))

    assert admitted_at <= admission_expires_at
    assert admission_expires_at <= intent_expires_at

    # Verify AuthorizedExecution bundle in dispatch port
    assert len(dispatch_mock.dispatched_bundles) == 1
    bundle = dispatch_mock.dispatched_bundles[0]
    assert bundle["schema_version"] == "1.0.0"
    assert bundle["admission"]["execution_id"] == admission["execution_id"]
    assert bundle["intent"]["intent_id"] == intent_doc["intent_id"]

    # Verify initial status read model
    status = result["status"]
    assert status["schema_version"] == "1.0.0"
    assert status["execution_id"] == admission["execution_id"]
    assert status["state"] == "RUNNING"
    assert gate.get_receipt(status["execution_id"], credentials=credentials) is None


def test_audit_sensitive_data_redaction() -> None:
    bearer_secret = "Bearer " + "b" * 40
    assignment_secret = "opaque-secret-value"
    raw_event = {
        "user": "operator1",
        "token": "secret-bearer-token-12345",
        "password": "super-secret-password",
        "private_key": "raw-key-bytes",
        "nested": {
            "api_key": "key-99999",
            "safe_metric": 42,
            "message": f"Authorization failed for {bearer_secret}",
            "events": [f"retry token={assignment_secret}"],
            "safe_text": "token count is 3",
        },
    }
    redacted = redact_sensitive_data(raw_event)
    assert redacted["token"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["private_key"] == "[REDACTED]"
    assert redacted["nested"]["api_key"] == "[REDACTED]"
    assert redacted["nested"]["safe_metric"] == 42
    assert redacted["nested"]["message"] == "Authorization failed for [REDACTED]"
    assert redacted["nested"]["events"] == ["retry [REDACTED]"]
    assert redacted["nested"]["safe_text"] == "token count is 3"
    serialized = json.dumps(redacted)
    assert bearer_secret not in serialized
    assert assignment_secret not in serialized


def test_audit_logger_never_persists_secret_bearing_neutral_values(tmp_path: Path) -> None:
    secret = "Bearer " + "z" * 40
    refresh_secret = "opaque-refresh-value"
    client_secret = "opaque-client-value"
    assigned_client_secret = "opaque-client-assignment-value"
    api_secret = "opaque-api-value"
    audit_path = tmp_path / "audit.jsonl"
    event = AuditLogger(log_path=audit_path).log_event(
        "AUTH_FAILURE",
        "operator.alpha",
        {
            "message": f"Rejected {secret}; oauth client_secret={assigned_client_secret}",
            "items": [secret],
            "refresh_token": refresh_secret,
            "client-secret": client_secret,
            "api-key": api_secret,
        },
    )

    assert event["details"]["message"] == "Rejected [REDACTED]; oauth [REDACTED]"
    assert event["details"]["items"] == ["[REDACTED]"]
    assert event["details"]["refresh_token"] == "[REDACTED]"
    assert event["details"]["client-secret"] == "[REDACTED]"
    assert event["details"]["api-key"] == "[REDACTED]"
    serialized = audit_path.read_text(encoding="utf-8")
    for value in (secret, refresh_secret, client_secret, assigned_client_secret, api_secret):
        assert value not in serialized


def test_gate_requires_explicit_authentication_and_signing_identity() -> None:
    with pytest.raises(ValueError, match="AuthenticationPort"):
        AuthorizationGate(
            signing_identity=_test_signing_identity(), controller_commit=TEST_BUILD_SHA
        )

    with pytest.raises(ValueError, match="AdmissionSigningIdentity"):
        AuthorizationGate(auth_port=_trusted_auth_port(), controller_commit=TEST_BUILD_SHA)

    with pytest.raises(ValueError, match="durable IdempotencyLedger"):
        AuthorizationGate(
            controller_commit=TEST_BUILD_SHA,
            auth_port=_trusted_auth_port(),
            signing_identity=_test_signing_identity(),
            idempotency_ledger=IdempotencyLedger(),
        )


def test_gate_rejects_frozen_fixture_signing_metadata() -> None:
    with pytest.raises(ValueError, match="test-vector-only"):
        AdmissionSigningIdentity(
            private_key=Ed25519PrivateKey.generate(),
            key_id="step5c-fixture-ed25519",
            issuer_id="step5c-fixture-controller",
        )


class _BlockingDispatchPort(MockWorkerDispatchPort):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def dispatch(self, bundle: dict) -> dict:
        self.entered.set()
        if not self.release.wait(timeout=5):
            raise AssertionError("Timed out waiting to release test dispatch")
        return super().dispatch(bundle)


def test_concurrent_duplicate_submissions_dispatch_one_execution(tmp_path: Path) -> None:
    intent_doc = _load_train_ticket()
    ledger = IdempotencyLedger(tmp_path / "duplicate-ledger.jsonl")
    dispatch_port = _BlockingDispatchPort()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(),
        idempotency_ledger=ledger,
        dispatch_port=dispatch_port,
    )

    def submit() -> dict:
        return gate.admit_and_dispatch(
            intent_doc,
            credentials=_operator_credentials(),
            current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(submit)
        assert dispatch_port.entered.wait(timeout=5)
        second = executor.submit(submit)
        try:
            replay = second.result(timeout=5)
        finally:
            dispatch_port.release.set()
        results = [first.result(timeout=5), replay]

    assert sorted(result["action"] for result in results) == [
        "ADMITTED",
        "ALREADY_ADMITTED",
    ]
    execution_ids = {result["status"]["execution_id"] for result in results}
    assert len(execution_ids) == 1
    assert len(dispatch_port.dispatched_bundles) == 1
    record = ledger.get_by_intent_id(intent_doc["intent_id"])
    assert record is not None
    assert record.execution_id == execution_ids.pop()


class _FailOnceQuotaManager(QuotaManager):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def evaluate_grants(
        self,
        intent_doc: dict,
        current_active_count: int,
    ) -> ResourceGrants:
        self.calls += 1
        if self.calls == 1:
            raise QuotaExceededError("Synthetic one-shot quota failure")
        return super().evaluate_grants(intent_doc, current_active_count)


class _FailOnceCapacityPort(MockWorkerDispatchPort):
    def __init__(self) -> None:
        super().__init__()
        self.reserve_calls = 0

    def reserve_capacity(self, intent_id: str) -> None:
        self.reserve_calls += 1
        if self.reserve_calls == 1:
            raise QuotaExceededError("Synthetic physical queue exhaustion")
        super().reserve_capacity(intent_id)


def test_capacity_failure_precedes_durable_admission_and_allows_retry(tmp_path: Path) -> None:
    intent_doc = _load_train_ticket()
    ledger = IdempotencyLedger(tmp_path / "capacity-ledger.jsonl")
    dispatch_port = _FailOnceCapacityPort()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(),
        idempotency_ledger=ledger,
        dispatch_port=dispatch_port,
    )

    with pytest.raises(QuotaExceededError, match="physical queue"):
        gate.admit_and_dispatch(
            intent_doc,
            credentials=_operator_credentials(),
            current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
        )

    assert ledger.get_by_intent_id(intent_doc["intent_id"]) is None
    retry = gate.admit_and_dispatch(
        intent_doc,
        credentials=_operator_credentials(),
        current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
    )
    assert retry["action"] == "ADMITTED"
    assert len(dispatch_port.dispatched_bundles) == 1


def test_precommit_failure_releases_idempotency_reservation(tmp_path: Path) -> None:
    intent_doc = _load_train_ticket()
    ledger = IdempotencyLedger(tmp_path / "precommit-ledger.jsonl")
    dispatch_port = MockWorkerDispatchPort()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(),
        idempotency_ledger=ledger,
        quota_manager=_FailOnceQuotaManager(),
        dispatch_port=dispatch_port,
    )

    with pytest.raises(QuotaExceededError):
        gate.admit_and_dispatch(
            intent_doc,
            credentials=_operator_credentials(),
            current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
        )

    assert ledger.get_by_intent_id(intent_doc["intent_id"]) is None
    retry = gate.admit_and_dispatch(
        intent_doc,
        credentials=_operator_credentials(),
        current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
    )
    assert retry["action"] == "ADMITTED"
    assert len(dispatch_port.dispatched_bundles) == 1


def test_memory_ceiling_rejection_starts_no_worker_and_leaves_no_record(
    tmp_path: Path,
) -> None:
    intent_doc = _load_train_ticket()
    ledger = IdempotencyLedger(tmp_path / "memory-ledger.jsonl")
    dispatch_port = MockWorkerDispatchPort()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(),
        idempotency_ledger=ledger,
        quota_manager=QuotaManager(default_memory_bytes=CEILING_MAX_MEMORY_BYTES + 1),
        dispatch_port=dispatch_port,
    )

    with pytest.raises(QuotaExceededError):
        gate.admit_and_dispatch(
            intent_doc,
            credentials=_operator_credentials(),
            current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
        )

    assert dispatch_port.dispatched_bundles == []
    assert ledger.get_by_intent_id(intent_doc["intent_id"]) is None


class _FailOnceDispatchPort(MockWorkerDispatchPort):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def dispatch(self, bundle: dict) -> dict:
        self.calls += 1
        if self.calls == 1:
            raise WorkerDispatchFailedError("Synthetic one-shot dispatch failure")
        return super().dispatch(bundle)


def test_dispatch_failure_is_terminal_for_committed_execution_identity(tmp_path: Path) -> None:
    intent_doc = _load_train_ticket()
    ledger_path = tmp_path / "dispatch-ledger.jsonl"
    ledger = IdempotencyLedger(ledger_path)
    dispatch_port = _FailOnceDispatchPort()
    signing_identity = _test_signing_identity()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=signing_identity,
        idempotency_ledger=ledger,
        dispatch_port=dispatch_port,
    )

    with pytest.raises(WorkerDispatchFailedError):
        gate.admit_and_dispatch(
            intent_doc,
            credentials=_operator_credentials(),
            current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
        )

    failed = ledger.get_by_intent_id(intent_doc["intent_id"])
    assert failed is not None
    assert failed.status == "FAILED"
    assert failed.error is not None
    assert failed.error["error_code"] == "ERR_WORKER_DISPATCH_FAILED"

    restarted_dispatch = MockWorkerDispatchPort()
    restarted_gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=signing_identity,
        idempotency_ledger=IdempotencyLedger(ledger_path),
        dispatch_port=restarted_dispatch,
    )
    retry = restarted_gate.admit_and_dispatch(
        intent_doc,
        credentials=_operator_credentials(),
        current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
    )
    assert retry["action"] == "ALREADY_ADMITTED"
    assert retry["status"]["state"] == "FAILED"
    assert retry["status"]["execution_id"] == failed.execution_id
    assert dispatch_port.calls == 1
    assert dispatch_port.dispatched_bundles == []
    assert restarted_dispatch.dispatched_bundles == []


class _BarrierLedger(IdempotencyLedger):
    def __init__(self, persistence_path: Path) -> None:
        super().__init__(persistence_path)
        self.barrier = threading.Barrier(2)

    def active_count(self, reservation_intent_id: str | None = None) -> int:
        self.barrier.wait(timeout=5)
        return super().active_count(reservation_intent_id)


def test_concurrent_distinct_intents_cannot_bypass_concurrency_limit(tmp_path: Path) -> None:
    first_intent = _load_train_ticket()
    second_intent = json.loads(json.dumps(first_intent))
    second_intent["intent_id"] = str(uuid.uuid4())
    second_intent["intent_digest"] = compute_intent_digest(second_intent)

    ledger = _BarrierLedger(tmp_path / "concurrency-ledger.jsonl")
    dispatch_port = MockWorkerDispatchPort()
    gate = AuthorizationGate(
        controller_commit=TEST_BUILD_SHA,
        auth_port=_trusted_auth_port(),
        signing_identity=_test_signing_identity(),
        idempotency_ledger=ledger,
        quota_manager=QuotaManager(max_concurrency=1),
        dispatch_port=dispatch_port,
    )

    def submit(intent_doc: dict) -> tuple[str, object]:
        try:
            return (
                "ADMITTED",
                gate.admit_and_dispatch(
                    intent_doc,
                    credentials=_operator_credentials(),
                    current_time=datetime(2026, 9, 17, 14, 30, 0, tzinfo=UTC),
                ),
            )
        except QuotaExceededError as exc:
            return ("REJECTED", exc)

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(submit, (first_intent, second_intent)))

    assert sorted(kind for kind, _ in outcomes) == ["ADMITTED", "REJECTED"]
    assert len(dispatch_port.dispatched_bundles) == 1
    committed = [
        record
        for intent in (first_intent, second_intent)
        if (record := ledger.get_by_intent_id(intent["intent_id"])) is not None
    ]
    assert len(committed) == 1
