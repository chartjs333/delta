from __future__ import annotations

import argparse
import logging
import ssl
import threading
from pathlib import Path
from typing import Any, cast

import pytest
from deltacontroller.host import (
    _identity_paths_for_profile,
    _install_tls,
    _validate_shutdown_file,
    _watch_shutdown_file,
)
from deltacontroller.http_host import WorkingVersionHttpServer
from deltacontroller.runtime_config import load_working_version_config

ROOT = Path(__file__).resolve().parents[2]


def _args(**overrides: Any) -> argparse.Namespace:
    values = {
        "bootstrap_local_identity": True,
        "signing_key": None,
        "worker_trust_roots": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_local_identity_never_inherits_remote_environment_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_working_version_config(ROOT / "configs/working-version/local.json")
    monkeypatch.setenv("DELTA_SIGNING_KEY_FILE", "production-signing-key.pem")
    monkeypatch.setenv("DELTA_WORKER_TRUST_ROOTS_FILE", "production-trust-roots.json")

    assert _identity_paths_for_profile(_args(), config) == (None, None)
    with pytest.raises(ValueError, match="cannot be combined"):
        _identity_paths_for_profile(
            _args(signing_key=Path("explicit.pem")),
            config,
        )


def test_remote_profile_reads_explicit_environment_paths_and_requires_tls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_working_version_config(ROOT / "configs/working-version/remote.example.json")
    monkeypatch.setenv("DELTA_SIGNING_KEY_FILE", "remote-signing-key.pem")
    monkeypatch.setenv("DELTA_WORKER_TRUST_ROOTS_FILE", "remote-trust-roots.json")
    signing, roots = _identity_paths_for_profile(
        _args(bootstrap_local_identity=False),
        config,
    )
    assert signing == Path("remote-signing-key.pem")
    assert roots == Path("remote-trust-roots.json")

    unused_server = cast(WorkingVersionHttpServer, object())
    with pytest.raises(ValueError, match="requires --tls-cert and --tls-key"):
        _install_tls(unused_server, config, None, None)


def test_local_profile_rejects_tls_configuration() -> None:
    config = load_working_version_config(ROOT / "configs/working-version/local.json")
    unused_server = cast(WorkingVersionHttpServer, object())
    with pytest.raises(ValueError, match="must not be configured as remote TLS"):
        _install_tls(
            unused_server,
            config,
            Path("certificate.pem"),
            Path("private-key.pem"),
        )


def test_shutdown_file_must_be_exactly_bound_to_instance(tmp_path: Path) -> None:
    instance_id = "11111111-1111-4111-8111-111111111111"
    expected = tmp_path / f"shutdown-{instance_id}.request"
    assert _validate_shutdown_file(expected, tmp_path, instance_id) == expected.resolve()

    for forbidden in (
        tmp_path / "runtime.json",
        tmp_path / "controller-ledger.jsonl",
        tmp_path / "shutdown.request",
        tmp_path / "shutdown-22222222-2222-4222-8222-222222222222.request",
    ):
        with pytest.raises(ValueError, match="exact launch-scoped path"):
            _validate_shutdown_file(forbidden, tmp_path, instance_id)


def test_remote_tls_configures_accepted_sockets_without_wrapping_listener(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_working_version_config(ROOT / "configs/working-version/remote.example.json")
    certificate = tmp_path / "certificate.pem"
    private_key = tmp_path / "private-key.pem"
    certificate.touch()
    private_key.touch()
    monkeypatch.setattr(ssl.SSLContext, "load_cert_chain", lambda *args, **kwargs: None)

    class RecordingServer:
        def __init__(self) -> None:
            self.socket = object()
            self.context: ssl.SSLContext | None = None

        def configure_tls(self, context: ssl.SSLContext) -> None:
            self.context = context

    server = RecordingServer()
    listener = server.socket
    _install_tls(cast(WorkingVersionHttpServer, server), config, certificate, private_key)

    assert server.socket is listener
    assert isinstance(server.context, ssl.SSLContext)
    assert server.context.minimum_version == ssl.TLSVersion.TLSv1_2


def test_shutdown_file_watcher_retries_transient_cleanup_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    shutdown_file = tmp_path / "shutdown-instance.request"
    shutdown_file.write_text("request", encoding="utf-8")
    real_unlink = Path.unlink
    attempts = 0

    def flaky_unlink(path: Path, missing_ok: bool = False) -> None:
        nonlocal attempts
        if path == shutdown_file:
            attempts += 1
            if attempts == 1:
                raise PermissionError("simulated transient sharing violation")
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", flaky_unlink)
    stopped = threading.Event()
    shutdown_requested = threading.Event()
    reasons: list[str] = []

    def initiate_shutdown(reason: str) -> None:
        reasons.append(reason)
        shutdown_requested.set()

    caplog.set_level(logging.WARNING)
    watcher = threading.Thread(
        target=_watch_shutdown_file,
        args=(shutdown_file, stopped, initiate_shutdown, logging.getLogger("test.shutdown")),
        kwargs={"poll_interval_seconds": 0.01},
        daemon=True,
    )
    watcher.start()
    try:
        assert shutdown_requested.wait(timeout=1)
        watcher.join(timeout=1)
        assert not watcher.is_alive()
        assert attempts == 2
        assert reasons == ["shutdown-file"]
        assert not shutdown_file.exists()
        assert "Shutdown request cleanup failed" in caplog.text
    finally:
        stopped.set()
