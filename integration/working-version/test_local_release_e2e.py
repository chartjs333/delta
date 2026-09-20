"""Clean-checkout process/socket E2E for the local working-version launcher."""

from __future__ import annotations

import importlib.util
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
from uuid import UUID, uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "tools" / "working-version" / "delta-local.ps1"
SMOKE_CLIENT = ROOT / "tools" / "working-version" / "smoke-working-version.py"
LOCAL_DESCRIPTOR = ROOT / "configs" / "working-version" / "local.json"


def _load_smoke_client() -> ModuleType:
    spec = importlib.util.spec_from_file_location("working_version_smoke", SMOKE_CLIENT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _require_platform_commands() -> str:
    missing = [name for name in ("git", "npm", "pwsh", "uv") if shutil.which(name) is None]
    if missing:
        pytest.skip("missing required platform executable(s): " + ", ".join(missing))
    executable = shutil.which("pwsh")
    assert executable is not None
    return executable


def _run_launcher(
    powershell: str,
    action: str,
    *,
    descriptor: Path,
    data_dir: Path,
    skip_install: bool = False,
    ready_timeout_seconds: int = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    command = [
        powershell,
        "-NoLogo",
        "-NoProfile",
        "-File",
        str(LAUNCHER),
        "-Action",
        action,
        "-Config",
        str(descriptor),
        "-DataDir",
        str(data_dir),
        "-AllowDirty",
        "-ReadyTimeoutSeconds",
        str(ready_timeout_seconds),
        "-ShutdownTimeoutSeconds",
        "75",
    ]
    if skip_install:
        command.append("-SkipInstall")
    # File-backed capture is deliberate. On Windows a detached grandchild can
    # inherit anonymous pipe handles and keep subprocess.run(capture_output=True)
    # waiting after the short-lived PowerShell launcher has exited.
    with (
        tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout_file,
        tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr_file,
    ):
        process_result = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            timeout=900,
        )
        stdout_file.seek(0)
        stderr_file.seek(0)
        completed = subprocess.CompletedProcess(
            process_result.args,
            process_result.returncode,
            stdout_file.read(),
            stderr_file.read(),
        )
    if check and completed.returncode != 0:
        pytest.fail(
            f"launcher action {action!r} failed with {completed.returncode}\n"
            f"stdout:\n{completed.stdout[-8000:]}\n"
            f"stderr:\n{completed.stderr[-8000:]}"
        )
    return completed


def _wait_unreachable(url: str, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.5):
                time.sleep(0.1)
        except (OSError, URLError):
            return
    pytest.fail(f"endpoint remained reachable after graceful stop: {url}")


def _write_runtime_descriptor(path: Path, port: int) -> str:
    document = json.loads(LOCAL_DESCRIPTOR.read_text(encoding="utf-8"))
    origin = f"http://127.0.0.1:{port}"
    document["bindings"]["port"] = port
    document["bindings"]["allowed_origins"] = [origin]
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return origin


def _start_foreign_readiness_server(
    *,
    data_dir: Path,
    descriptor_document: dict[str, Any],
    build_id: str,
) -> tuple[ThreadingHTTPServer, threading.Thread, list[str]]:
    """Serve a forged ready document that follows the launcher's state UUID."""

    observed_instance_ids: list[str] = []
    state_path = data_dir / "working-version-state.json"

    class ExclusiveThreadingHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = False

        def server_bind(self) -> None:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_EXCLUSIVEADDRUSE,
                    1,
                )
            super().server_bind()

    class ForeignReadinessHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != "/readyz":
                self.send_error(404)
                return
            instance_id = "00000000-0000-0000-0000-000000000000"
            try:
                state = json.loads(state_path.read_text(encoding="utf-8-sig"))
                candidate = str(state["instance_id"])
                if str(UUID(candidate)) == candidate:
                    instance_id = candidate
            except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
                pass
            observed_instance_ids.append(instance_id)
            payload = json.dumps(
                {
                    "schema_version": "1.0.0",
                    "status": "READY",
                    "build_id": build_id,
                    "protocol_id": descriptor_document["protocol_id"],
                    "contract_schema_version": descriptor_document["contract_schema_version"],
                    "formal_semantics_id": descriptor_document["formal_semantics_id"],
                    "instance_id": instance_id,
                    "signing_key_id": "foreign",
                    "worker_trust_root": "EXPLICIT_MATCH",
                },
                separators=(",", ":"),
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    server = ExclusiveThreadingHTTPServer(("127.0.0.1", 0), ForeignReadinessHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, observed_instance_ids


def test_clean_checkout_start_submit_cancel_restart_recovery_and_shutdown(
    tmp_path: Path,
) -> None:
    powershell = _require_platform_commands()
    smoke = _load_smoke_client()
    port = _free_loopback_port()
    descriptor = tmp_path / "local-e2e.json"
    data_dir = tmp_path / "durable-data"
    base_url = _write_runtime_descriptor(descriptor, port)
    started = False
    first_shutdown_path: Path | None = None
    second_shutdown_path: Path | None = None

    try:
        # The first start exercises the clean-checkout install/build path.  -AllowDirty
        # is test-only because this test is also run against the candidate worktree.
        _run_launcher(
            powershell,
            "start",
            descriptor=descriptor,
            data_dir=data_dir,
        )
        started = True

        state_path = data_dir / "working-version-state.json"
        first_state_text = state_path.read_text(encoding="utf-8-sig")
        first_state = json.loads(first_state_text)
        assert str(UUID(first_state["instance_id"])) == first_state["instance_id"]
        assert first_state["process_start_time_utc"]
        first_shutdown_path = Path(first_state["shutdown_request_path"])
        assert first_shutdown_path == data_dir / (f"shutdown-{first_state['instance_id']}.request")
        assert not first_shutdown_path.exists()

        # A live PID alone is insufficient: changing the recorded creation time
        # must make the launcher refuse to identify the process as its child.
        mismatched_state = dict(first_state)
        mismatched_state["process_start_time_utc"] = "1970-01-01T00:00:00.0000000Z"
        state_path.write_text(json.dumps(mismatched_state), encoding="utf-8")
        try:
            stale_status = _run_launcher(
                powershell,
                "status",
                descriptor=descriptor,
                data_dir=data_dir,
                skip_install=True,
                check=False,
            )
            assert stale_status.returncode == 3
            assert '"STALE_METADATA"' in stale_status.stdout
        finally:
            state_path.write_text(first_state_text, encoding="utf-8")

        result = smoke.run_smoke(
            base_url=base_url,
            origin=base_url,
            request_timeout_seconds=30.0,
            terminal_timeout_seconds=120.0,
        )
        assert result["result"] == "PASS"
        assert result["rejection"]["http_status"] == 400
        assert result["cancellation"]["state"] == "CANCELLED"

        success = result["success"]
        execution_id = success["execution_id"]
        original_status = success["status"]
        original_receipt = success["receipt"]

        _run_launcher(
            powershell,
            "stop",
            descriptor=descriptor,
            data_dir=data_dir,
            skip_install=True,
        )
        started = False
        _wait_unreachable(f"{base_url}/healthz")
        assert not state_path.exists()
        assert not (data_dir / "working-version.pid").exists()
        assert not first_shutdown_path.exists()

        # Restart reuses the durable ledger and explicit local signing/trust identity.
        _run_launcher(
            powershell,
            "start",
            descriptor=descriptor,
            data_dir=data_dir,
            skip_install=True,
        )
        started = True
        second_state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        assert second_state["instance_id"] != first_state["instance_id"]
        second_shutdown_path = Path(second_state["shutdown_request_path"])
        assert second_shutdown_path != first_shutdown_path
        client = smoke.WorkingVersionClient(base_url, base_url, 30.0)
        recovered_status: dict[str, Any] = client.status(execution_id)
        recovered_receipt: dict[str, Any] = client.receipt(execution_id)
        assert recovered_status == original_status
        assert recovered_receipt == original_receipt

        status_result = _run_launcher(
            powershell,
            "status",
            descriptor=descriptor,
            data_dir=data_dir,
            skip_install=True,
        )
        assert '"READY"' in status_result.stdout
    finally:
        if started:
            _run_launcher(
                powershell,
                "stop",
                descriptor=descriptor,
                data_dir=data_dir,
                skip_install=True,
                check=False,
            )

    _wait_unreachable(f"{base_url}/healthz")
    assert (data_dir / "controller-ledger.jsonl").is_file()
    assert (data_dir / "worker-trust-roots.json").is_file()
    assert (data_dir / "controller-signing-key.pem").is_file()
    assert not (data_dir / "working-version-state.json").exists()
    assert second_shutdown_path is not None
    assert not second_shutdown_path.exists()


def test_occupied_port_foreign_matching_readiness_cannot_pass_startup(
    tmp_path: Path,
) -> None:
    powershell = _require_platform_commands()
    descriptor_document = json.loads(LOCAL_DESCRIPTOR.read_text(encoding="utf-8"))
    build_id = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    data_dir = tmp_path / "foreign-ready-data"
    server, thread, observed_instance_ids = _start_foreign_readiness_server(
        data_dir=data_dir,
        descriptor_document=descriptor_document,
        build_id=build_id,
    )
    port = int(server.server_address[1])
    descriptor = tmp_path / "foreign-ready.json"
    base_url = _write_runtime_descriptor(descriptor, port)
    launcher_started = False

    try:
        result = _run_launcher(
            powershell,
            "start",
            descriptor=descriptor,
            data_dir=data_dir,
            skip_install=True,
            ready_timeout_seconds=8,
            check=False,
        )
        launcher_started = result.returncode == 0
        assert result.returncode != 0
        assert '"RUNNING"' not in result.stdout
        assert observed_instance_ids
        assert any(
            value != "00000000-0000-0000-0000-000000000000" for value in observed_instance_ids
        )
        assert not (data_dir / "working-version-state.json").exists()
        assert not (data_dir / "working-version.pid").exists()
        assert not (data_dir / "runtime.json").exists()
        assert not list(data_dir.glob("shutdown-*.request"))
        with urlopen(f"{base_url}/readyz", timeout=1) as response:
            assert response.status == 200
    finally:
        if launcher_started:
            _run_launcher(
                powershell,
                "stop",
                descriptor=descriptor,
                data_dir=data_dir,
                skip_install=True,
                check=False,
            )
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_stop_retains_metadata_when_supervised_process_exits_nonzero(
    tmp_path: Path,
) -> None:
    powershell = _require_platform_commands()
    port = _free_loopback_port()
    descriptor = tmp_path / "nonzero-stop.json"
    _write_runtime_descriptor(descriptor, port)
    data_dir = tmp_path / "nonzero-stop-data"
    data_dir.mkdir()
    instance_id = str(uuid4())
    shutdown_path = data_dir / f"shutdown-{instance_id}.request"
    exit_code_path = data_dir / f"exit-{instance_id}.code"
    supervisor_path = data_dir / f"supervisor-{instance_id}.ps1"
    supervisor_spec_path = data_dir / f"supervisor-{instance_id}.json"
    monitor_source = """
import pathlib
import sys
import time

shutdown_path = pathlib.Path(sys.argv[1])
exit_code_path = pathlib.Path(sys.argv[2])
deadline = time.monotonic() + 60
while time.monotonic() < deadline and not shutdown_path.is_file():
    time.sleep(0.05)
if not shutdown_path.is_file():
    raise SystemExit(9)
exit_code_path.write_text("7", encoding="utf-8")
raise SystemExit(7)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", monitor_source, str(shutdown_path), str(exit_code_path)]
    )
    try:
        start_identity = subprocess.check_output(
            [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-Command",
                (
                    f"(Get-Process -Id {process.pid}).StartTime.ToUniversalTime()"
                    ".ToString('O',[Globalization.CultureInfo]::InvariantCulture)"
                ),
            ],
            text=True,
        ).strip()
        state_path = data_dir / "working-version-state.json"
        state_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "process_id": process.pid,
                    "process_start_time_utc": start_identity,
                    "instance_id": instance_id,
                    "shutdown_request_path": str(shutdown_path),
                    "exit_code_path": str(exit_code_path),
                    "supervisor_script_path": str(supervisor_path),
                    "supervisor_spec_path": str(supervisor_spec_path),
                    "build_id": "0" * 40,
                }
            ),
            encoding="utf-8",
        )
        pid_path = data_dir / "working-version.pid"
        pid_path.write_text(str(process.pid), encoding="utf-8")

        result = _run_launcher(
            powershell,
            "stop",
            descriptor=descriptor,
            data_dir=data_dir,
            skip_install=True,
            check=False,
        )
        process.wait(timeout=10)
        assert result.returncode != 0
        assert "exited with code 7" in result.stderr
        assert "metadata and diagnostics were retained" in result.stderr
        assert state_path.is_file()
        assert pid_path.is_file()
        assert shutdown_path.is_file()
        assert exit_code_path.read_text(encoding="utf-8") == "7"
        assert '"graceful"' not in result.stdout
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
