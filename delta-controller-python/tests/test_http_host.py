from __future__ import annotations

import http.client
import json
import socket
import ssl
import threading
import time
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from deltacontroller.errors import (
    AuthenticationRequiredError,
    ControllerError,
    QuotaExceededError,
    UnauthorizedCallerError,
)
from deltacontroller.http_host import WorkingVersionHttpServer
from deltacontroller.runtime_config import (
    CONTRACT_SCHEMA_VERSION,
    FORMAL_SEMANTICS_ID,
    HTTP_PROTOCOL_ID,
    MAX_JSON_DEPTH,
    MAX_REQUEST_BYTES,
    WorkingVersionConfig,
)

EXECUTION_ID = "55555555-5555-4555-8555-555555555555"


def _config() -> WorkingVersionConfig:
    return WorkingVersionConfig(
        profile="LOCAL_LOOPBACK",
        bind_host="127.0.0.1",
        port=0,
        allowed_origins=("http://127.0.0.1:8765",),
        request_limit_bytes=MAX_REQUEST_BYTES,
        json_max_depth=MAX_JSON_DEPTH,
        request_timeout_seconds=5,
        max_inflight_requests=4,
        request_queue_size=4,
        worker_queue_capacity=4,
        worker_processes=1,
        shutdown_grace_seconds=2,
        local_subject_id="local.operator",
        local_effective_roles=("OPERATOR",),
        protocol_id=HTTP_PROTOCOL_ID,
        contract_schema_version=CONTRACT_SCHEMA_VERSION,
        formal_semantics_id=FORMAL_SEMANTICS_ID,
    )


def _tls_server_context(tmp_path: Path) -> ssl.SSLContext:
    private_key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(private_key.public_key())
        .serial_number(1)
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(minutes=5))
        .sign(private_key, hashes.SHA256())
    )
    certificate_path = tmp_path / "server-cert.pem"
    private_key_path = tmp_path / "server-key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    private_key_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate_path, private_key_path)
    return context


class _FakeApi:
    def __init__(self) -> None:
        self.config = _config()
        self.cancelled = False
        self.credentials_error: ControllerError | None = None
        self.status_error: ControllerError | None = None
        self.submit_error: ControllerError | None = None
        self.cancel_error: ControllerError | None = None

    def credentials_for_request(
        self, peer_ip: str, authorization_header: str | None
    ) -> dict[str, Any]:
        if self.credentials_error is not None:
            raise self.credentials_error
        assert peer_ip == "127.0.0.1"
        assert authorization_header is None
        return {"type": "LOCAL_PEER_CREDENTIAL", "subject_id": "loopback"}

    def submit(self, body: bytes, credentials: dict[str, Any]) -> dict[str, Any]:
        if self.submit_error is not None:
            raise self.submit_error
        assert credentials["subject_id"] == "loopback"
        intent = json.loads(body)
        return {
            "action": "ADMITTED",
            "admission": {"execution_id": EXECUTION_ID},
            "bundle": {"private_boundary": True},
            "status": {"execution_id": EXECUTION_ID, "state": "QUEUED"},
            "intent_echo": intent["intent_id"],
        }

    def get_status(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        if self.status_error is not None:
            raise self.status_error
        if execution_id != EXECUTION_ID:
            return None
        return {
            "schema_version": "1.0.0",
            "execution_id": execution_id,
            "state": "CANCELLED" if self.cancelled else "COMPLETED",
        }

    def get_receipt(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        if execution_id != EXECUTION_ID or self.cancelled:
            return None
        return {"schema_version": "1.0.0", "execution_id": execution_id}

    def cancel(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None:
        if self.cancel_error is not None:
            raise self.cancel_error
        if execution_id != EXECUTION_ID:
            return None
        self.cancelled = True
        return self.get_status(execution_id, credentials)

    def health_document(self) -> dict[str, Any]:
        return {"status": "UP", "formal_semantics_id": FORMAL_SEMANTICS_ID}

    def readiness_document(self) -> tuple[bool, dict[str, Any]]:
        return True, {"status": "READY", "protocol_id": HTTP_PROTOCOL_ID}


@pytest.fixture
def running_server(tmp_path: Path) -> Iterator[tuple[_FakeApi, int]]:
    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    (ui_dir / "live.html").write_text("<!doctype html><title>Live Delta</title>", encoding="utf-8")
    api = _FakeApi()
    server = WorkingVersionHttpServer(("127.0.0.1", 0), api, ui_dir=ui_dir)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield api, int(server.server_address[1])
    finally:
        server.stopping.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _request(
    port: int,
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path, body=body, headers=headers or {})
    response = connection.getresponse()
    payload = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    status = response.status
    connection.close()
    return status, response_headers, payload


def test_health_readiness_and_live_ui(running_server: tuple[_FakeApi, int]) -> None:
    _, port = running_server
    health_status, _, health_payload = _request(port, "GET", "/healthz")
    assert health_status == 200
    assert json.loads(health_payload)["formal_semantics_id"] == FORMAL_SEMANTICS_ID

    ready_status, _, ready_payload = _request(port, "GET", "/readyz")
    assert ready_status == 200
    assert json.loads(ready_payload)["protocol_id"] == HTTP_PROTOCOL_ID

    ui_status, ui_headers, ui_payload = _request(port, "GET", "/")
    assert ui_status == 200
    assert b"Live Delta" in ui_payload
    assert "connect-src 'self'" in ui_headers["content-security-policy"]


def test_submit_hides_internal_bundle_and_enforces_headers(
    running_server: tuple[_FakeApi, int],
) -> None:
    _, port = running_server
    payload = json.dumps({"intent_id": "11111111-1111-4111-8111-111111111111"}).encode()
    status, _, body = _request(
        port,
        "POST",
        "/api/v1/intent/submit",
        body=payload,
        headers={"Content-Type": "application/json", "X-Delta-Request": "1"},
    )
    assert status == 201
    result = json.loads(body)
    assert result["action"] == "ADMITTED"
    assert "bundle" not in result

    missing_header_status, _, missing_header_body = _request(
        port,
        "POST",
        "/api/v1/intent/submit",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    assert missing_header_status == 400
    assert json.loads(missing_header_body)["error"]["error_code"] == (
        "ERR_DELTA_REQUEST_HEADER_REQUIRED"
    )

    bad_media_status, _, bad_media_body = _request(
        port,
        "POST",
        "/api/v1/intent/submit",
        body=payload,
        headers={"Content-Type": "text/plain", "X-Delta-Request": "1"},
    )
    assert bad_media_status == 400
    assert json.loads(bad_media_body)["error"]["error_code"] == ("ERR_CONTENT_TYPE_UNSUPPORTED")

    bad_host_status, _, bad_host_body = _request(
        port,
        "POST",
        "/api/v1/intent/submit",
        body=payload,
        headers={
            "Host": "attacker.invalid",
            "Content-Type": "application/json",
            "X-Delta-Request": "1",
        },
    )
    assert bad_host_status == 400
    assert json.loads(bad_host_body)["error"]["error_code"] == "ERR_HOST_HEADER_INVALID"


def test_origin_status_receipt_and_cancel(running_server: tuple[_FakeApi, int]) -> None:
    _, port = running_server
    common = {"X-Delta-Request": "1"}
    forbidden_status, _, forbidden_body = _request(
        port,
        "GET",
        f"/api/v1/execution/{EXECUTION_ID}/status",
        headers={**common, "Origin": "https://attacker.invalid"},
    )
    assert forbidden_status == 403
    assert json.loads(forbidden_body)["error"]["error_code"] == "ERR_ORIGIN_FORBIDDEN"

    status_code, _, status_body = _request(
        port, "GET", f"/api/v1/execution/{EXECUTION_ID}/status", headers=common
    )
    assert status_code == 200
    assert json.loads(status_body)["state"] == "COMPLETED"

    receipt_code, _, receipt_body = _request(
        port, "GET", f"/api/v1/execution/{EXECUTION_ID}/receipt", headers=common
    )
    assert receipt_code == 200
    assert json.loads(receipt_body)["execution_id"] == EXECUTION_ID

    cancel_code, _, cancel_body = _request(
        port,
        "POST",
        f"/api/v1/execution/{EXECUTION_ID}/cancel",
        body=b"{}",
        headers={**common, "Content-Type": "application/json"},
    )
    assert cancel_code == 200
    assert json.loads(cancel_body)["state"] == "CANCELLED"

    missing_receipt_code, _, _ = _request(
        port, "GET", f"/api/v1/execution/{EXECUTION_ID}/receipt", headers=common
    )
    assert missing_receipt_code == 404


def test_request_limit_rejects_before_body_read(running_server: tuple[_FakeApi, int]) -> None:
    _, port = running_server
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.putrequest("POST", "/api/v1/intent/submit")
    connection.putheader("Content-Type", "application/json")
    connection.putheader("X-Delta-Request", "1")
    connection.putheader("Content-Length", str(MAX_REQUEST_BYTES + 1))
    connection.endheaders()
    response = connection.getresponse()
    body = response.read()
    connection.close()
    assert response.status == 413
    assert json.loads(body)["error"]["error_code"] == "ERR_PAYLOAD_TOO_LARGE"


def test_typed_auth_policy_conflict_and_quota_http_mappings(
    running_server: tuple[_FakeApi, int],
) -> None:
    api, port = running_server
    common = {"X-Delta-Request": "1"}

    api.credentials_error = AuthenticationRequiredError("must not be reflected")
    status, headers, body = _request(
        port,
        "GET",
        f"/api/v1/execution/{EXECUTION_ID}/status",
        headers=common,
    )
    assert status == 401
    assert headers["www-authenticate"].startswith("Bearer")
    assert b"must not be reflected" not in body
    api.credentials_error = None

    api.status_error = UnauthorizedCallerError()
    status, _, body = _request(
        port,
        "GET",
        f"/api/v1/execution/{EXECUTION_ID}/status",
        headers=common,
    )
    assert status == 403
    assert json.loads(body)["error"]["error_code"] == "ERR_UNAUTHORIZED_CALLER"
    api.status_error = None

    api.cancel_error = ControllerError(
        "ERR_EXECUTION_TERMINAL",
        "already terminal",
        "IDEMPOTENCY",
    )
    status, _, body = _request(
        port,
        "POST",
        f"/api/v1/execution/{EXECUTION_ID}/cancel",
        body=b"{}",
        headers={**common, "Content-Type": "application/json"},
    )
    assert status == 409
    assert json.loads(body)["error"]["error_code"] == "ERR_EXECUTION_TERMINAL"
    api.cancel_error = None

    api.submit_error = QuotaExceededError()
    status, headers, body = _request(
        port,
        "POST",
        "/api/v1/intent/submit",
        body=b"{}",
        headers={**common, "Content-Type": "application/json"},
    )
    assert status == 429
    assert headers["retry-after"] == "1"
    assert json.loads(body)["error"]["error_code"] == "ERR_QUOTA_EXCEEDED"


def test_backpressure_rejects_before_spawning_another_request_thread(tmp_path: Path) -> None:
    class BlockingApi(_FakeApi):
        def __init__(self) -> None:
            super().__init__()
            self.config = replace(self.config, max_inflight_requests=1)
            self.entered = threading.Event()
            self.release = threading.Event()

        def submit(self, body: bytes, credentials: dict[str, Any]) -> dict[str, Any]:
            self.entered.set()
            assert self.release.wait(timeout=5)
            return super().submit(body, credentials)

    class CountingServer(WorkingVersionHttpServer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.spawn_count = 0
            super().__init__(*args, **kwargs)

        def process_request_thread(self, request: Any, client_address: Any) -> None:
            self.spawn_count += 1
            super().process_request_thread(request, client_address)

    ui_dir = tmp_path / "ui"
    ui_dir.mkdir()
    (ui_dir / "live.html").write_text("<!doctype html><title>Live Delta</title>", "utf-8")
    api = BlockingApi()
    server = CountingServer(("127.0.0.1", 0), api, ui_dir=ui_dir)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = int(server.server_address[1])
    first_result: list[tuple[int, dict[str, str], bytes]] = []
    payload = json.dumps({"intent_id": "11111111-1111-4111-8111-111111111111"}).encode()
    first = threading.Thread(
        target=lambda: first_result.append(
            _request(
                port,
                "POST",
                "/api/v1/intent/submit",
                body=payload,
                headers={"Content-Type": "application/json", "X-Delta-Request": "1"},
            )
        )
    )
    first.start()
    try:
        assert api.entered.wait(timeout=5)
        status, headers, body = _request(port, "GET", "/healthz")
        assert status == 429
        assert headers["retry-after"] == "1"
        assert json.loads(body)["error"]["error_code"] == "ERR_BACKPRESSURE"
        assert server.spawn_count == 1
    finally:
        api.release.set()
        first.join(timeout=5)
        server.stopping.set()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
    assert first_result[0][0] == 201


def _trickle_until_peer_closes(
    connection: socket.socket, *, chunk: bytes, maximum_seconds: float
) -> float:
    started = time.monotonic()
    connection.settimeout(0.02)
    while time.monotonic() - started < maximum_seconds:
        try:
            connection.sendall(chunk)
        except OSError:
            return time.monotonic() - started
        try:
            response = connection.recv(1)
        except TimeoutError:
            response = None
        except OSError:
            return time.monotonic() - started
        if response == b"":
            return time.monotonic() - started
        time.sleep(0.04)
    pytest.fail("server did not enforce the absolute request-read deadline")


@pytest.mark.parametrize("request_phase", ["headers", "body"])
def test_absolute_deadline_closes_slow_trickle_requests(tmp_path: Path, request_phase: str) -> None:
    api = _FakeApi()
    api.config = replace(api.config, request_timeout_seconds=0.3)
    server = WorkingVersionHttpServer(("127.0.0.1", 0), api, ui_dir=tmp_path)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = int(server.server_address[1])
    connection = socket.create_connection(("127.0.0.1", port), timeout=1)
    if request_phase == "headers":
        prefix = f"GET /healthz HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nX-Slow: ".encode()
        chunk = b"x"
    else:
        prefix = (
            "POST /api/v1/intent/submit HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{port}\r\n"
            "Content-Type: application/json\r\n"
            "X-Delta-Request: 1\r\n"
            "Content-Length: 1000\r\n\r\n"
        ).encode()
        chunk = b" "
    try:
        connection.sendall(prefix)
        elapsed = _trickle_until_peer_closes(
            connection,
            chunk=chunk,
            maximum_seconds=0.9,
        )
        assert elapsed < 0.9
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)


def test_shutdown_force_closes_partial_request_before_thread_join(tmp_path: Path) -> None:
    class ObservableServer(WorkingVersionHttpServer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.request_started = threading.Event()
            super().__init__(*args, **kwargs)

        def process_request_thread(self, request: socket.socket, client_address: Any) -> None:
            self.request_started.set()
            super().process_request_thread(request, client_address)

    api = _FakeApi()
    api.config = replace(api.config, request_timeout_seconds=60)
    server = ObservableServer(("127.0.0.1", 0), api, ui_dir=tmp_path)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = int(server.server_address[1])
    connection = socket.create_connection(("127.0.0.1", port), timeout=1)
    connection.sendall(b"GET /healthz HTTP/1.1\r\nX-Slow: ")
    assert server.request_started.wait(timeout=1)

    stopped = threading.Event()

    def stop_server() -> None:
        server.shutdown()
        server.server_close()
        stopped.set()

    stopper = threading.Thread(target=stop_server, daemon=True)
    started = time.monotonic()
    stopper.start()
    try:
        assert stopped.wait(timeout=2), "server_close blocked on a partial request"
        assert time.monotonic() - started < 2
        server_thread.join(timeout=1)
        assert not server_thread.is_alive()
    finally:
        connection.close()
        if not stopped.is_set():
            assert stopped.wait(timeout=2)


def test_silent_tls_client_is_deadlined_and_cannot_block_shutdown(tmp_path: Path) -> None:
    class ObservableTlsServer(WorkingVersionHttpServer):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.request_threads_started = threading.Semaphore(0)
            super().__init__(*args, **kwargs)

        def process_request_thread(self, request: Any, client_address: Any) -> None:
            self.request_threads_started.release()
            super().process_request_thread(request, client_address)

    api = _FakeApi()
    api.config = replace(api.config, request_timeout_seconds=0.3)
    server = ObservableTlsServer(("127.0.0.1", 0), api, ui_dir=tmp_path)
    server.configure_tls(_tls_server_context(tmp_path))
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = int(server.server_address[1])
    first = socket.create_connection(("127.0.0.1", port), timeout=1)
    stopped = threading.Event()
    try:
        assert server.request_threads_started.acquire(timeout=1)
        started = time.monotonic()
        first.settimeout(1)
        try:
            received = first.recv(1)
        except TimeoutError:
            pytest.fail("silent TLS connection outlived the absolute request deadline")
        except OSError:
            received = b""
        assert received == b""
        assert time.monotonic() - started < 1

        second = socket.create_connection(("127.0.0.1", port), timeout=1)
        try:
            assert server.request_threads_started.acquire(timeout=1)

            def stop_server() -> None:
                server.shutdown()
                server.server_close()
                stopped.set()

            threading.Thread(target=stop_server, daemon=True).start()
            assert stopped.wait(timeout=2), "TLS handshake blocked server shutdown"
            server_thread.join(timeout=1)
            assert not server_thread.is_alive()
        finally:
            second.close()
    finally:
        first.close()
        if not stopped.is_set():
            server.shutdown()
            server.server_close()
        server_thread.join(timeout=2)
