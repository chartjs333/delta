"""Bounded async subprocess queue, recovery, and cancellation-CAS tests."""

from __future__ import annotations

import copy
import json
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltacontroller.auth import AuthenticatedSubject, StaticAuthenticationPort
from deltacontroller.canonical import canonicalize_jcs, sha256_digest
from deltacontroller.dispatch import JsonSubprocessWorkerRunner, SubprocessWorkerDispatchPort
from deltacontroller.errors import QuotaExceededError, WorkerDispatchFailedError
from deltacontroller.gate import AdmissionSigningIdentity, AuthorizationGate
from deltacontroller.idempotency import IdempotencyLedger

CONTRACTS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "admin-ui"
    / "step5c-controlled-live-execution"
    / "contracts"
)
PRODUCER_COMMIT = "4992d9eca319da21b5a2c7b94593f3668b92329c"


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((CONTRACTS_ROOT / "fixtures" / "valid" / name).read_text("utf-8"))


def _bundle() -> dict[str, Any]:
    return _fixture("authorized-execution.train-ticket.json")


def _receipt() -> dict[str, Any]:
    return _fixture("execution-receipt-lineage-extension.train-ticket.json")


def _record_bundle(ledger: IdempotencyLedger, bundle: dict[str, Any]) -> None:
    intent = bundle["intent"]
    admission = bundle["admission"]
    ledger.record_admission(
        intent["intent_id"],
        intent["intent_digest"],
        admission["authenticated_subject"]["subject_id"],
        admission["execution_id"],
        admission,
        intent=intent,
        operation=intent["operation"],
    )


def _completed_result(bundle: dict[str, Any]) -> dict[str, Any]:
    receipt = _receipt()
    return {
        "dispatched": True,
        "execution_id": bundle["admission"]["execution_id"],
        "intent_id": bundle["intent"]["intent_id"],
        "operation": bundle["intent"]["operation"],
        "status": "COMPLETED",
        "receipt": receipt,
        "receipt_digest": sha256_digest(canonicalize_jcs(receipt)),
    }


def _wait_status(ledger: IdempotencyLedger, execution_id: str, status: str) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        record = ledger.get_by_execution_id(execution_id)
        if record is not None and record.status == status:
            return
        time.sleep(0.01)
    record = ledger.get_by_execution_id(execution_id)
    raise AssertionError(f"expected {status}, got {record.status if record else None}")


class _ImmediateRunner:
    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]:
        assert not cancellation_requested.is_set()
        return _completed_result(bundle)


class _BlockingRunner:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]:
        self.entered.set()
        assert self.release.wait(timeout=5)
        return _completed_result(bundle)


class _CancellationAwareRunner:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.exited = threading.Event()

    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]:
        self.entered.set()
        assert cancellation_requested.wait(timeout=5)
        self.exited.set()
        return _completed_result(bundle)


class _DelayedCancellationRunner:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.cancellation_seen = threading.Event()
        self.release = threading.Event()

    def run(
        self,
        bundle: dict[str, Any],
        cancellation_requested: threading.Event,
    ) -> dict[str, Any]:
        self.entered.set()
        assert cancellation_requested.wait(timeout=5)
        self.cancellation_seen.set()
        assert self.release.wait(timeout=5)
        return _completed_result(bundle)


def test_queue_ack_and_durable_terminal_result(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "ledger.jsonl")
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=_ImmediateRunner(),
        max_workers=1,
        max_queue=1,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)

    ack = port.dispatch(bundle)
    assert ack == {
        "dispatched": True,
        "execution_id": bundle["admission"]["execution_id"],
        "intent_id": bundle["intent"]["intent_id"],
        "status": "QUEUED",
    }
    _wait_status(ledger, bundle["admission"]["execution_id"], "COMPLETED")
    record = ledger.get_by_execution_id(bundle["admission"]["execution_id"])
    assert record is not None and record.terminal_receipt == _receipt()
    port.shutdown(1)


def test_cancel_wins_cas_and_late_receipt_is_discarded(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "cancel-ledger.jsonl")
    runner = _BlockingRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    port.dispatch(bundle)
    assert runner.entered.wait(timeout=5)

    cancelled = port.cancel(bundle["admission"]["execution_id"])
    assert cancelled is not None and cancelled.status == "CANCELLED"
    runner.release.set()
    _wait_status(ledger, bundle["admission"]["execution_id"], "CANCELLED")
    time.sleep(0.05)
    record = ledger.get_by_execution_id(bundle["admission"]["execution_id"])
    assert record is not None
    assert record.terminal_receipt is None
    assert record.receipt_digest is None
    port.shutdown(1)


def test_queue_backpressure_is_typed(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "backpressure-ledger.jsonl")
    runner = _BlockingRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    first = _bundle()
    _record_bundle(ledger, first)
    port.dispatch(first)
    assert runner.entered.wait(timeout=5)

    second = copy.deepcopy(first)
    second["intent"]["intent_id"] = "22222222-2222-4222-8222-222222222222"
    second["admission"]["intent_id"] = second["intent"]["intent_id"]
    second["admission"]["execution_id"] = "66666666-6666-4666-8666-666666666666"
    # The physical queue rejects before any ledger transition, so no second
    # durable admission is needed (or allowed) for this capacity test.
    with pytest.raises(QuotaExceededError):
        port.dispatch(second)

    runner.release.set()
    port.shutdown(1)


def test_failed_duplicate_dispatch_does_not_remove_live_job_or_leak_capacity(
    tmp_path: Path,
) -> None:
    ledger = IdempotencyLedger(tmp_path / "duplicate-capacity-ledger.jsonl")
    runner = _BlockingRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    port.dispatch(bundle)
    assert runner.entered.wait(timeout=5)

    with pytest.raises(QuotaExceededError):
        port.dispatch(bundle)

    runner.release.set()
    _wait_status(ledger, bundle["admission"]["execution_id"], "COMPLETED")
    deadline = time.monotonic() + 5
    while True:
        try:
            port.reserve_capacity("22222222-2222-4222-8222-222222222222")
            break
        except QuotaExceededError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)
    port.release_capacity_reservation("22222222-2222-4222-8222-222222222222")
    port.shutdown(1)


def test_startup_recovery_fails_closed_orphaned_nonterminal_record(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "orphan-ledger.jsonl")
    bundle = _bundle()
    _record_bundle(ledger, bundle)

    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=_ImmediateRunner(),
        recover_on_startup=True,
    )
    assert port.recovered_orphan_count == 1
    record = ledger.get_by_execution_id(bundle["admission"]["execution_id"])
    assert record is not None and record.status == "FAILED"
    assert record.error is not None
    assert record.error["error_code"] == "ERR_WORKER_DISPATCH_FAILED"
    assert port.recover_orphans() == 0
    port.shutdown(1)


def test_subprocess_runner_rejects_output_over_bound_without_pipe_buffering() -> None:
    runner = JsonSubprocessWorkerRunner(
        (sys.executable, "-c", "import sys; sys.stdout.write('x' * 4096)"),
        max_output_bytes=1024,
        poll_interval_seconds=0.01,
    )
    with pytest.raises(WorkerDispatchFailedError, match="output exceeded"):
        runner.run(_bundle(), threading.Event())


def test_subprocess_runner_does_not_inherit_controller_secret_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DELTA_SIGNING_KEY_FILE", "must-not-cross-worker-boundary.pem")
    command = (
        sys.executable,
        "-c",
        (
            "import json, os, sys; sys.stdin.buffer.read(); "
            "print(json.dumps({'inherited': os.getenv('DELTA_SIGNING_KEY_FILE')}))"
        ),
    )
    result = JsonSubprocessWorkerRunner(command).run(_bundle(), threading.Event())
    assert result == {"inherited": None}


def test_worker_result_rejects_backend_commit_that_differs_from_catalog_ref(
    tmp_path: Path,
) -> None:
    port = SubprocessWorkerDispatchPort(
        ledger=IdempotencyLedger(tmp_path / "backend-lineage-ledger.jsonl"),
        producer_commit=PRODUCER_COMMIT,
        runner=_ImmediateRunner(),
    )
    bundle = _bundle()
    result = _completed_result(bundle)
    result["receipt"]["provenance"]["backend_commit"] = "0" * 40
    result["receipt_digest"] = sha256_digest(canonicalize_jcs(result["receipt"]))
    with pytest.raises(WorkerDispatchFailedError, match="provenance mismatch"):
        port._validate_terminal_result(bundle, result)
    port.shutdown(1)


@pytest.mark.parametrize("field", ["backend_commit", "producer_commit"])
def test_durable_receipt_rejects_wrong_build_lineage_on_replay_boundary(
    tmp_path: Path,
    field: str,
) -> None:
    ledger = IdempotencyLedger(
        tmp_path / f"wrong-{field}-ledger.jsonl",
        expected_producer_commit=PRODUCER_COMMIT,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    execution_id = bundle["admission"]["execution_id"]
    assert ledger.transition_execution(execution_id, {"ADMITTED"}, "RUNNING") is not None
    receipt = _receipt()
    receipt["provenance"][field] = "0" * 40
    with pytest.raises(ValueError, match="lineage"):
        ledger.transition_execution(
            execution_id,
            {"RUNNING"},
            "COMPLETED",
            terminal_receipt=receipt,
            receipt_digest=sha256_digest(canonicalize_jcs(receipt)),
        )


def test_subprocess_runner_large_stdin_remains_cancellable_when_child_does_not_read() -> None:
    bundle = _bundle()
    bundle["bounded_test_padding"] = "x" * (1024 * 1024)
    cancellation_requested = threading.Event()
    timer = threading.Timer(0.1, cancellation_requested.set)
    runner = JsonSubprocessWorkerRunner(
        (sys.executable, "-c", "import time; time.sleep(60)"),
        startup_grace_seconds=0,
        poll_interval_seconds=0.01,
    )

    started_at = time.monotonic()
    timer.start()
    try:
        with pytest.raises(RuntimeError, match="cancelled"):
            runner.run(bundle, cancellation_requested)
    finally:
        timer.cancel()
        timer.join(timeout=1)
    assert time.monotonic() - started_at < 5


def test_shutdown_waits_for_cancelled_worker_before_returning(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "shutdown-ledger.jsonl")
    runner = _CancellationAwareRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    port.dispatch(bundle)
    assert runner.entered.wait(timeout=5)

    port.shutdown(0)

    assert runner.exited.is_set()
    record = ledger.get_by_execution_id(bundle["admission"]["execution_id"])
    assert record is not None and record.status == "CANCELLED"


def test_cancelled_job_retains_physical_capacity_until_runner_exits(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "physical-capacity-ledger.jsonl")
    runner = _DelayedCancellationRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    port.dispatch(bundle)
    assert runner.entered.wait(timeout=5)
    assert port.cancel(bundle["admission"]["execution_id"]) is not None
    assert runner.cancellation_seen.wait(timeout=5)

    with pytest.raises(QuotaExceededError, match="capacity is exhausted"):
        port.reserve_capacity("22222222-2222-4222-8222-222222222222")

    runner.release.set()
    port.shutdown(2)


def test_shutdown_never_returns_while_cancelled_runner_still_owns_data(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "fail-closed-shutdown-ledger.jsonl")
    runner = _DelayedCancellationRunner()
    port = SubprocessWorkerDispatchPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    bundle = _bundle()
    _record_bundle(ledger, bundle)
    port.dispatch(bundle)
    assert runner.entered.wait(timeout=5)

    observed: list[BaseException] = []

    def shutdown() -> None:
        try:
            port.shutdown(0)
        except BaseException as exc:
            observed.append(exc)

    shutdown_thread = threading.Thread(target=shutdown)
    shutdown_thread.start()
    assert runner.cancellation_seen.wait(timeout=5)
    shutdown_thread.join(timeout=0.1)
    assert shutdown_thread.is_alive()

    runner.release.set()
    shutdown_thread.join(timeout=5)
    assert not shutdown_thread.is_alive()
    assert observed == []


def test_gate_never_rolls_async_running_state_back_to_queued(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(tmp_path / "gate-race-ledger.jsonl")
    runner = _BlockingRunner()

    class CoordinatedPort(SubprocessWorkerDispatchPort):
        def dispatch(self, bundle: dict[str, Any]) -> dict[str, Any]:
            ack = super().dispatch(bundle)
            assert runner.entered.wait(timeout=5)
            return ack

    port = CoordinatedPort(
        ledger=ledger,
        producer_commit=PRODUCER_COMMIT,
        runner=runner,
        max_workers=1,
        max_queue=0,
    )
    private_key = Ed25519PrivateKey.generate()
    gate = AuthorizationGate(
        controller_commit=PRODUCER_COMMIT,
        auth_port=StaticAuthenticationPort(
            allow_local_peer=True,
            peer_subjects={
                "peer": AuthenticatedSubject(
                    "operator.alpha", "LOCAL_PEER_CREDENTIAL", ["OPERATOR"]
                )
            },
        ),
        signing_identity=AdmissionSigningIdentity(
            private_key=private_key,
            key_id="runtime-race-key",
            issuer_id="runtime-race-controller",
        ),
        idempotency_ledger=ledger,
        dispatch_port=port,
    )
    intent = _fixture("execution-intent.train-ticket.json")
    result = gate.admit_and_dispatch(
        intent,
        credentials={"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "peer"},
        current_time=datetime(2026, 9, 17, 14, 30, tzinfo=UTC),
    )
    execution_id = result["status"]["execution_id"]
    assert result["status"]["state"] == "RUNNING"
    running = ledger.get_by_execution_id(execution_id)
    assert running is not None and running.status == "RUNNING"

    assert port.cancel(execution_id) is not None
    runner.release.set()
    port.shutdown(1)
