"""Bounded HTTP/JSON transport host for Step 5C controlled execution."""

from __future__ import annotations

import json
import logging
import mimetypes
import re
import socket
import ssl
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import unquote, urlsplit

from deltacontroller.errors import ControllerError
from deltacontroller.runtime_config import WorkingVersionConfig

_EXECUTION_ROUTE = re.compile(r"^/api/v1/execution/([0-9a-fA-F-]{36})/(status|receipt|cancel)$")

_HTTP_STATUS_BY_ERROR: dict[str, HTTPStatus] = {
    "ERR_AUTHENTICATION_REQUIRED": HTTPStatus.UNAUTHORIZED,
    "ERR_AUTHENTICATION_FAILED": HTTPStatus.UNAUTHORIZED,
    "ERR_UNAUTHORIZED_CALLER": HTTPStatus.FORBIDDEN,
    "ERR_POLICY_DENIED": HTTPStatus.FORBIDDEN,
    "ERR_ROLE_FORBIDDEN": HTTPStatus.FORBIDDEN,
    "ERR_CATALOG_REF_MISMATCH": HTTPStatus.FORBIDDEN,
    "ERR_UNKNOWN_PLUGIN_ID": HTTPStatus.FORBIDDEN,
    "ERR_UNKNOWN_DATASET_ID": HTTPStatus.FORBIDDEN,
    "ERR_OPERATION_SCOPE_UNSUPPORTED": HTTPStatus.FORBIDDEN,
    "ERR_STAGE_C_FORBIDDEN": HTTPStatus.FORBIDDEN,
    "ERR_INTENT_ID_DIGEST_CONFLICT": HTTPStatus.CONFLICT,
    "ERR_INTENT_COLLISION_DETECTED": HTTPStatus.CONFLICT,
    "ERR_EXECUTION_TERMINAL": HTTPStatus.CONFLICT,
    "ERR_QUOTA_EXCEEDED": HTTPStatus.TOO_MANY_REQUESTS,
    "ERR_SHUTTING_DOWN": HTTPStatus.SERVICE_UNAVAILABLE,
    "ERR_WORKER_DISPATCH_FAILED": HTTPStatus.SERVICE_UNAVAILABLE,
}


class WorkingVersionApi(Protocol):
    """Operations exposed to the HTTP adapter by the trusted runtime composition."""

    config: WorkingVersionConfig

    def credentials_for_request(
        self, peer_ip: str, authorization_header: str | None
    ) -> dict[str, Any]: ...

    def submit(self, body: bytes, credentials: dict[str, Any]) -> dict[str, Any]: ...

    def get_status(
        self, execution_id: str, credentials: dict[str, Any]
    ) -> dict[str, Any] | None: ...

    def get_receipt(
        self, execution_id: str, credentials: dict[str, Any]
    ) -> dict[str, Any] | None: ...

    def cancel(self, execution_id: str, credentials: dict[str, Any]) -> dict[str, Any] | None: ...

    def health_document(self) -> dict[str, Any]: ...

    def readiness_document(self) -> tuple[bool, dict[str, Any]]: ...


class WorkingVersionHttpServer(ThreadingHTTPServer):
    """HTTP server with bounded accept backlog and request-thread concurrency."""

    daemon_threads = False
    block_on_close = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        api: WorkingVersionApi,
        *,
        ui_dir: Path | None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.api = api
        self.ui_dir = ui_dir.resolve() if ui_dir is not None else None
        self.request_queue_size = api.config.request_queue_size
        self.request_slots = threading.BoundedSemaphore(api.config.max_inflight_requests)
        self.transport_logger = logger or logging.getLogger("deltacontroller.http")
        self.stopping = threading.Event()
        self._tls_context: ssl.SSLContext | None = None
        self._request_deadlines: dict[socket.socket, float] = {}
        self._request_deadline_condition = threading.Condition()
        self._deadline_monitor_stopping = False
        super().__init__(server_address, WorkingVersionRequestHandler, bind_and_activate=True)
        self._deadline_monitor = threading.Thread(
            target=self._enforce_request_deadlines,
            name="delta-http-request-deadlines",
            daemon=True,
        )
        self._deadline_monitor.start()

    def get_request(self) -> tuple[socket.socket, Any]:
        connection, address = super().get_request()
        try:
            connection.settimeout(self.api.config.request_timeout_seconds)
            if self._tls_context is not None:
                connection = self._tls_context.wrap_socket(
                    connection,
                    server_side=True,
                    do_handshake_on_connect=False,
                )
                connection.settimeout(self.api.config.request_timeout_seconds)
            return connection, address
        except BaseException:
            connection.close()
            raise

    def configure_tls(self, context: ssl.SSLContext) -> None:
        """Install TLS for future accepted sockets without wrapping the listener."""
        if self._tls_context is not None:
            raise RuntimeError("TLS is already configured")
        self._tls_context = context

    def process_request(self, request: Any, client_address: Any) -> None:
        """Acquire capacity before ThreadingMixIn is allowed to create a thread."""
        if not self.request_slots.acquire(blocking=False):
            self._reject_connection_at_capacity(request)
            self.shutdown_request(request)
            return
        request_socket = cast(socket.socket, request)
        if not self._track_request(request_socket):
            self.request_slots.release()
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._untrack_request(request_socket)
            self.request_slots.release()
            self.shutdown_request(request)
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        request_socket = cast(socket.socket, request)
        try:
            if isinstance(request_socket, ssl.SSLSocket):
                try:
                    request_socket.do_handshake()
                except OSError:
                    self.shutdown_request(request)
                    return
            super().process_request_thread(request, client_address)
        finally:
            self._untrack_request(request_socket)
            self.request_slots.release()

    def shutdown(self) -> None:
        """Stop accepting work and unblock every in-flight socket before waiting."""
        self.stopping.set()
        self._close_active_requests()
        super().shutdown()

    def server_close(self) -> None:
        """Close active sockets before ThreadingMixIn joins non-daemon threads."""
        self.stopping.set()
        self._stop_deadline_monitor()
        super().server_close()

    def _track_request(self, request: socket.socket) -> bool:
        deadline = time.monotonic() + float(self.api.config.request_timeout_seconds)
        with self._request_deadline_condition:
            if self.stopping.is_set() or self._deadline_monitor_stopping:
                return False
            self._request_deadlines[request] = deadline
            self._request_deadline_condition.notify()
        return True

    def _untrack_request(self, request: socket.socket) -> None:
        with self._request_deadline_condition:
            if self._request_deadlines.pop(request, None) is not None:
                self._request_deadline_condition.notify()

    def _enforce_request_deadlines(self) -> None:
        """Close sockets at one absolute monotonic deadline, even during trickle I/O."""
        while True:
            expired: list[socket.socket]
            with self._request_deadline_condition:
                while not self._deadline_monitor_stopping and not self._request_deadlines:
                    self._request_deadline_condition.wait()
                if self._deadline_monitor_stopping:
                    return

                now = time.monotonic()
                next_deadline = min(self._request_deadlines.values())
                if next_deadline > now:
                    self._request_deadline_condition.wait(timeout=next_deadline - now)
                    continue

                expired = [
                    request
                    for request, deadline in self._request_deadlines.items()
                    if deadline <= now
                ]
                for request in expired:
                    del self._request_deadlines[request]
            for request in expired:
                self._close_request_socket(request)

    def _close_active_requests(self) -> None:
        with self._request_deadline_condition:
            requests = list(self._request_deadlines)
            self._request_deadlines.clear()
            self._request_deadline_condition.notify()
        for request in requests:
            self._close_request_socket(request)

    def _stop_deadline_monitor(self) -> None:
        with self._request_deadline_condition:
            self._deadline_monitor_stopping = True
            requests = list(self._request_deadlines)
            self._request_deadlines.clear()
            self._request_deadline_condition.notify_all()
        for request in requests:
            self._close_request_socket(request)
        if self._deadline_monitor is not threading.current_thread():
            self._deadline_monitor.join(timeout=1)

    @staticmethod
    def _close_request_socket(request: socket.socket) -> None:
        try:
            request.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        # BaseHTTPRequestHandler keeps buffered makefile references.  A plain
        # socket.close() can therefore defer the OS close and leave recv()
        # blocked on Windows; closing the detached descriptor is immediate.
        try:
            descriptor = request.detach()
        except OSError:
            return
        if descriptor >= 0:
            try:
                socket.close(descriptor)
            except OSError:
                pass

    @staticmethod
    def _reject_connection_at_capacity(request: Any) -> None:
        document = {
            "schema_version": "1.0.0",
            "error": {
                "schema_version": "1.0.0",
                "error_code": "ERR_BACKPRESSURE",
                "category": "TRANSPORT",
                "retryable": True,
                "message": "HTTP request concurrency limit reached",
            },
        }
        payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
        head = (
            "HTTP/1.1 429 Too Many Requests\r\n"
            "Connection: close\r\n"
            "Cache-Control: no-store\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(payload)}\r\n"
            "Retry-After: 1\r\n"
            "X-Content-Type-Options: nosniff\r\n"
            "\r\n"
        ).encode("ascii")
        try:
            # Do not let a client that is not reading its response stall the
            # single accept loop while the bounded worker slots are occupied.
            request.settimeout(0.1)
            received = bytearray()
            while b"\r\n\r\n" not in received and len(received) <= 65536:
                chunk = request.recv(min(4096, 65537 - len(received)))
                if not chunk:
                    break
                received.extend(chunk)
            if b"\r\n\r\n" not in received:
                return
            request.sendall(head + payload)
        except OSError:
            pass


class WorkingVersionRequestHandler(BaseHTTPRequestHandler):
    """Strict request handler; authority always comes from the server-side API."""

    protocol_version = "HTTP/1.1"
    server_version = "DeltaWorkingVersion/1"
    sys_version = ""

    @property
    def runtime_server(self) -> WorkingVersionHttpServer:
        return cast(WorkingVersionHttpServer, self.server)

    def log_message(self, format: str, *args: object) -> None:
        # Never log headers, request bodies, query strings, credentials, or raw error text.
        path = urlsplit(self.path).path
        self.runtime_server.transport_logger.info(
            "HTTP method=%s path=%s peer=%s",
            self.command,
            path,
            self.client_address[0],
        )

    def handle_expect_100(self) -> bool:
        try:
            content_length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            content_length = -1
        if content_length < 0:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_SCHEMA_VALIDATION_FAILED",
                "A valid Content-Length header is required",
            )
            return False
        if content_length > self.runtime_server.api.config.request_limit_bytes:
            self._send_transport_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "ERR_PAYLOAD_TOO_LARGE",
                "Request body exceeds the 10 MiB limit",
            )
            return False
        self.send_response_only(HTTPStatus.CONTINUE)
        self.end_headers()
        return True

    def do_OPTIONS(self) -> None:
        self._bounded(self._handle_options)

    def do_GET(self) -> None:
        self._bounded(self._handle_get)

    def do_HEAD(self) -> None:
        self._bounded(lambda: self._handle_static(head_only=True))

    def do_POST(self) -> None:
        self._bounded(self._handle_post)

    def _bounded(self, operation: Any) -> None:
        if not self._validate_host_and_request_target():
            return
        try:
            operation()
        except (BrokenPipeError, ConnectionResetError):
            return
        except TimeoutError:
            self._send_transport_error(
                HTTPStatus.REQUEST_TIMEOUT,
                "ERR_REQUEST_TIMEOUT",
                "HTTP request timed out",
                retryable=True,
            )
        except ControllerError as exc:
            status = _HTTP_STATUS_BY_ERROR.get(exc.code, HTTPStatus.BAD_REQUEST)
            message = exc.message
            if status == HTTPStatus.UNAUTHORIZED:
                message = "Authentication failed"
            self._send_error_document(
                status,
                {
                    "schema_version": "1.0.0",
                    "error_code": exc.code,
                    "category": exc.category,
                    "retryable": exc.retryable,
                    "message": message[:512],
                },
            )
        except (KeyError, ValueError) as exc:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_SCHEMA_VALIDATION_FAILED",
                str(exc)[:512],
            )
        except Exception:
            self.runtime_server.transport_logger.exception("Unhandled HTTP request failure")
            self._send_transport_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "ERR_INTERNAL",
                "Internal request failure",
                retryable=True,
            )

    def _validate_host_and_request_target(self) -> bool:
        if not self.path.startswith("/"):
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_REQUEST_TARGET_INVALID",
                "Only origin-form HTTP request targets are accepted",
            )
            return False
        host_values = self.headers.get_all("Host", failobj=[])
        if len(host_values) != 1:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_HOST_HEADER_INVALID",
                "Exactly one Host header is required",
            )
            return False
        supplied_host = host_values[0].strip().casefold()
        if self.runtime_server.api.config.is_local:
            port = int(self.runtime_server.server_address[1])
            allowed_hosts = {"127.0.0.1" if port == 80 else f"127.0.0.1:{port}"}
        else:
            allowed_hosts = {
                urlsplit(origin).netloc.casefold()
                for origin in self.runtime_server.api.config.allowed_origins
            }
        if supplied_host not in allowed_hosts:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_HOST_HEADER_INVALID",
                "Host header does not match the configured service authority",
            )
            return False
        return True

    def _handle_options(self) -> None:
        origin = self._validated_origin(required=True)
        if not isinstance(origin, str):
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers(origin=origin, api_response=True)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers", "Content-Type, Authorization, X-Delta-Request"
        )
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _handle_get(self) -> None:
        path = urlsplit(self.path).path
        if path == "/healthz":
            self._send_json(HTTPStatus.OK, self.runtime_server.api.health_document())
            return
        if path == "/readyz":
            ready, document = self.runtime_server.api.readiness_document()
            self._send_json(HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE, document)
            return

        match = _EXECUTION_ROUTE.fullmatch(path)
        if match is not None and match.group(2) in {"status", "receipt"}:
            if not self._validate_api_request(require_json=False):
                return
            credentials = self._credentials()
            execution_id, operation = match.groups()
            if operation == "status":
                result = self.runtime_server.api.get_status(execution_id, credentials)
            else:
                result = self.runtime_server.api.get_receipt(execution_id, credentials)
            if result is None:
                self._send_transport_error(
                    HTTPStatus.NOT_FOUND,
                    "ERR_EXECUTION_NOT_FOUND",
                    "Execution or terminal receipt is unavailable",
                )
                return
            self._send_json(HTTPStatus.OK, result)
            return

        if path.startswith("/api/"):
            self._send_transport_error(
                HTTPStatus.NOT_FOUND,
                "ERR_ENDPOINT_NOT_FOUND",
                "API endpoint not found",
            )
            return
        self._handle_static(head_only=False)

    def _handle_post(self) -> None:
        path = urlsplit(self.path).path
        if not self._validate_api_request(require_json=True):
            return
        credentials = self._credentials()
        if path == "/api/v1/intent/submit":
            body = self._read_bounded_body()
            if body is None:
                return
            result = self.runtime_server.api.submit(body, credentials)
            # AuthorizedExecution is an internal Controller -> Worker object and is never exposed.
            public_result = {key: value for key, value in result.items() if key != "bundle"}
            status = (
                HTTPStatus.CREATED if public_result.get("action") == "ADMITTED" else HTTPStatus.OK
            )
            self._send_json(status, public_result)
            return

        match = _EXECUTION_ROUTE.fullmatch(path)
        if match is not None and match.group(2) == "cancel":
            body = self._read_bounded_body(allow_empty=True)
            if body is None:
                return
            if body not in {b"", b"{}", b"{ }"}:
                try:
                    parsed = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"Cancellation body must be an empty JSON object: {exc}"
                    ) from exc
                if parsed != {}:
                    raise ValueError("Cancellation body must be an empty JSON object")
            cancel_result = self.runtime_server.api.cancel(match.group(1), credentials)
            if cancel_result is None:
                self._send_transport_error(
                    HTTPStatus.NOT_FOUND,
                    "ERR_EXECUTION_NOT_FOUND",
                    "Execution is unavailable",
                )
                return
            self._send_json(HTTPStatus.OK, cancel_result)
            return

        self._send_transport_error(
            HTTPStatus.NOT_FOUND,
            "ERR_ENDPOINT_NOT_FOUND",
            "API endpoint not found",
        )

    def _validate_api_request(self, *, require_json: bool) -> bool:
        if self.runtime_server.stopping.is_set():
            self._send_transport_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                "ERR_SHUTTING_DOWN",
                "Controller is shutting down",
                retryable=True,
            )
            return False
        if self._validated_origin(required=False) is False:
            return False
        if self.headers.get("X-Delta-Request") != "1":
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_DELTA_REQUEST_HEADER_REQUIRED",
                "X-Delta-Request: 1 is required",
            )
            return False
        if require_json:
            content_type = self.headers.get("Content-Type")
            if content_type is None:
                self._send_transport_error(
                    HTTPStatus.BAD_REQUEST,
                    "ERR_CONTENT_TYPE_REQUIRED",
                    "Content-Type: application/json is required",
                )
                return False
            parts = [part.strip().lower() for part in content_type.split(";")]
            if parts[0] != "application/json" or any(
                part and part != "charset=utf-8" for part in parts[1:]
            ):
                self._send_transport_error(
                    HTTPStatus.BAD_REQUEST,
                    "ERR_CONTENT_TYPE_UNSUPPORTED",
                    "Content-Type must be application/json with optional charset=utf-8",
                )
                return False
        return True

    def _validated_origin(self, *, required: bool) -> str | bool | None:
        origin = self.headers.get("Origin")
        if origin is None:
            if required:
                self._send_transport_error(
                    HTTPStatus.FORBIDDEN,
                    "ERR_ORIGIN_FORBIDDEN",
                    "Origin is required for CORS preflight",
                )
                return None
            return None
        if origin not in self.runtime_server.api.config.allowed_origins:
            self._send_transport_error(
                HTTPStatus.FORBIDDEN,
                "ERR_ORIGIN_FORBIDDEN",
                "Request origin is not configured",
            )
            return False
        return origin

    def _credentials(self) -> dict[str, Any]:
        return self.runtime_server.api.credentials_for_request(
            self.client_address[0], self.headers.get("Authorization")
        )

    def _read_bounded_body(self, *, allow_empty: bool = False) -> bytes | None:
        if self.headers.get("Transfer-Encoding") is not None:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_TRANSFER_ENCODING_UNSUPPORTED",
                "Chunked request bodies are not supported",
            )
            return None
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_CONTENT_LENGTH_REQUIRED",
                "Content-Length is required",
            )
            return None
        try:
            content_length = int(raw_length, 10)
        except ValueError:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_CONTENT_LENGTH_INVALID",
                "Content-Length must be a non-negative integer",
            )
            return None
        if content_length < 0:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_CONTENT_LENGTH_INVALID",
                "Content-Length must be a non-negative integer",
            )
            return None
        if content_length > self.runtime_server.api.config.request_limit_bytes:
            self._send_transport_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "ERR_PAYLOAD_TOO_LARGE",
                "Request body exceeds the 10 MiB limit",
            )
            return None
        if content_length == 0 and not allow_empty:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_SCHEMA_VALIDATION_FAILED",
                "JSON request body must not be empty",
            )
            return None
        body = self.rfile.read(content_length)
        if len(body) != content_length:
            self._send_transport_error(
                HTTPStatus.BAD_REQUEST,
                "ERR_TRUNCATED_BODY",
                "Request body ended before Content-Length bytes were received",
            )
            return None
        return body

    def _handle_static(self, *, head_only: bool) -> None:
        ui_dir = self.runtime_server.ui_dir
        if ui_dir is None:
            self._send_transport_error(
                HTTPStatus.NOT_FOUND,
                "ERR_UI_NOT_CONFIGURED",
                "Admin UI is not configured",
            )
            return
        request_path = unquote(urlsplit(self.path).path)
        relative = "live.html" if request_path in {"", "/"} else request_path.lstrip("/")
        candidate = (ui_dir / relative).resolve()
        try:
            candidate.relative_to(ui_dir)
        except ValueError:
            self._send_transport_error(
                HTTPStatus.NOT_FOUND,
                "ERR_STATIC_PATH_INVALID",
                "Static resource not found",
            )
            return
        if not candidate.is_file():
            self._send_transport_error(
                HTTPStatus.NOT_FOUND,
                "ERR_STATIC_NOT_FOUND",
                "Static resource not found",
            )
            return
        payload = candidate.read_bytes()
        media_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self._send_common_headers(origin=None, api_response=False)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(payload)))
        if candidate.suffix.lower() == ".html":
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; connect-src 'self'; img-src 'self' blob: data:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; "
                "base-uri 'none'; form-action 'none'",
            )
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _send_transport_error(
        self,
        status: HTTPStatus,
        code: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        self._send_error_document(
            status,
            {
                "schema_version": "1.0.0",
                "error_code": code,
                "category": "TRANSPORT",
                "retryable": retryable,
                "message": message[:512],
            },
        )

    def _send_error_document(self, status: HTTPStatus, error: dict[str, Any]) -> None:
        self._send_json(status, {"schema_version": "1.0.0", "error": error})

    def _send_json(self, status: HTTPStatus, document: dict[str, Any]) -> None:
        payload = json.dumps(
            document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        origin_value = self._response_origin()
        self.send_response(status)
        self._send_common_headers(origin=origin_value, api_response=True)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if status == HTTPStatus.UNAUTHORIZED:
            self.send_header("WWW-Authenticate", 'Bearer realm="delta-working-version"')
        if status == HTTPStatus.TOO_MANY_REQUESTS:
            self.send_header("Retry-After", "1")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _response_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        if origin is None:
            return None
        if origin in self.runtime_server.api.config.allowed_origins:
            return origin
        return None

    def _send_common_headers(self, *, origin: str | None, api_response: bool) -> None:
        self.send_header("Connection", "close")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        if api_response:
            self.send_header("Cache-Control", "no-store")
        if origin is not None:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
