"""Production entry point for the local/remote Step 5C HTTP working version."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import os
import signal
import ssl
import sys
import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from deltacontroller.application import WorkingVersionApplication
from deltacontroller.audit import AuditLogger
from deltacontroller.auth import AuthenticatedSubject, StaticAuthenticationPort
from deltacontroller.dispatch import SubprocessWorkerDispatchPort
from deltacontroller.gate import AuthorizationGate
from deltacontroller.http_host import WorkingVersionHttpServer
from deltacontroller.idempotency import IdempotencyLedger
from deltacontroller.ingress import IngressParser
from deltacontroller.quota import QuotaManager
from deltacontroller.runtime_config import (
    DataDirectoryLease,
    HashedTokenAuthenticationPort,
    RuntimeIdentity,
    WorkingVersionConfig,
    load_or_bootstrap_runtime_identity,
    load_working_version_config,
    validate_build_id,
)
from deltacontroller.schema import SchemaRegistry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="delta-working-version")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--ui-dir", type=Path, required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--port", type=int)
    parser.add_argument("--bootstrap-local-identity", action="store_true")
    parser.add_argument("--signing-key", type=Path)
    parser.add_argument("--worker-trust-roots", type=Path)
    parser.add_argument("--remote-auth-config", type=Path)
    parser.add_argument("--tls-cert", type=Path)
    parser.add_argument("--tls-key", type=Path)
    parser.add_argument("--shutdown-file", type=Path)
    parser.add_argument("--instance-id")
    return parser


def _configure_logging(data_dir: Path) -> logging.Logger:
    logger = logging.getLogger("deltacontroller")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    file_handler = logging.FileHandler(data_dir / "controller.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)
    return logger


def _worker_command(identity: RuntimeIdentity, build_id: str, data_dir: Path) -> tuple[str, ...]:
    cache_root = data_dir / "worker-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    return (
        sys.executable,
        "-m",
        "deltatorrent.live_execution.process",
        "--trust-roots",
        str(identity.trust_roots_path),
        "--producer-commit",
        build_id,
        "--cache-root",
        str(cache_root),
    )


def _build_authentication_port(
    config: WorkingVersionConfig,
    remote_auth_config: Path | None,
) -> StaticAuthenticationPort | HashedTokenAuthenticationPort:
    if config.is_local:
        if remote_auth_config is not None:
            raise ValueError("LOCAL_LOOPBACK profile does not accept remote auth configuration")
        subject = AuthenticatedSubject(
            subject_id=config.local_subject_id,
            authenticated_via="LOCAL_PEER_CREDENTIAL",
            effective_roles=list(config.local_effective_roles),
        )
        return StaticAuthenticationPort(
            allow_local_peer=True,
            peer_subjects={"working-version-loopback": subject},
        )
    if remote_auth_config is None:
        raise ValueError("REMOTE_TLS profile requires --remote-auth-config")
    return HashedTokenAuthenticationPort.from_file(remote_auth_config)


def build_application(
    *,
    config: WorkingVersionConfig,
    build_id: str,
    data_dir: Path,
    allow_local_bootstrap: bool,
    signing_key_path: Path | None,
    trust_roots_path: Path | None,
    remote_auth_config: Path | None,
    instance_id: str,
) -> tuple[WorkingVersionApplication, DataDirectoryLease]:
    """Compose Controller and bounded Worker subprocess queue from explicit inputs."""
    normalized_build_id = validate_build_id(build_id)
    resolved_data_dir = data_dir.resolve()
    lease = DataDirectoryLease(resolved_data_dir, build_id=normalized_build_id)
    lease.acquire()
    try:
        identity = load_or_bootstrap_runtime_identity(
            data_dir=resolved_data_dir,
            allow_local_bootstrap=allow_local_bootstrap,
            signing_key_path=signing_key_path,
            trust_roots_path=trust_roots_path,
        )
        auth_port = _build_authentication_port(config, remote_auth_config)
        schema_registry = SchemaRegistry()
        ledger = IdempotencyLedger(
            resolved_data_dir / "controller-ledger.jsonl",
            expected_producer_commit=normalized_build_id,
        )
        dispatch_port = SubprocessWorkerDispatchPort(
            ledger=ledger,
            producer_commit=normalized_build_id,
            worker_command=_worker_command(identity, normalized_build_id, resolved_data_dir),
            schema_registry=schema_registry,
            max_workers=config.worker_processes,
            max_queue=config.worker_queue_capacity,
            recover_on_startup=True,
        )
        gate = AuthorizationGate(
            schema_registry=schema_registry,
            ingress_parser=IngressParser(
                schema_registry=schema_registry,
                max_bytes=config.request_limit_bytes,
            ),
            auth_port=auth_port,
            idempotency_ledger=ledger,
            quota_manager=QuotaManager(
                max_concurrency=config.worker_processes + config.worker_queue_capacity
            ),
            dispatch_port=dispatch_port,
            audit_logger=AuditLogger(log_path=resolved_data_dir / "controller-audit.jsonl"),
            signing_identity=identity.signing_identity,
            controller_commit=normalized_build_id,
        )
        application = WorkingVersionApplication(
            config=config,
            build_id=normalized_build_id,
            gate=gate,
            dispatch_port=dispatch_port,
            runtime_identity=identity,
            instance_id=instance_id,
        )
        return application, lease
    except BaseException:
        lease.release()
        raise


def _validate_ui_dir(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir() or not (resolved / "live.html").is_file():
        raise ValueError(f"Admin UI live build is missing live.html under '{resolved}'")
    return resolved


def _validate_shutdown_file(path: Path, data_dir: Path, instance_id: str) -> Path:
    resolved = path.resolve()
    expected = (data_dir.resolve() / f"shutdown-{instance_id}.request").resolve()
    if resolved != expected:
        raise ValueError(
            "shutdown-file must be the exact launch-scoped path "
            f"'{expected.name}' inside the durable data directory"
        )
    return resolved


def _configured_path(argument: Path | None, environment_name: str) -> Path | None:
    if argument is not None:
        return argument
    value = os.environ.get(environment_name)
    return Path(value) if value else None


def _identity_paths_for_profile(
    args: argparse.Namespace,
    config: WorkingVersionConfig,
) -> tuple[Path | None, Path | None]:
    if config.is_local:
        # A developer shell may contain remote production path variables. Never
        # let those silently replace the data-dir-owned local identity.
        if args.bootstrap_local_identity and (
            args.signing_key is not None or args.worker_trust_roots is not None
        ):
            raise ValueError(
                "Local identity bootstrap cannot be combined with explicit signing/trust paths"
            )
        return args.signing_key, args.worker_trust_roots
    return (
        _configured_path(args.signing_key, "DELTA_SIGNING_KEY_FILE"),
        _configured_path(args.worker_trust_roots, "DELTA_WORKER_TRUST_ROOTS_FILE"),
    )


def _runtime_document(
    *,
    application: WorkingVersionApplication,
    server: WorkingVersionHttpServer,
    status: str,
) -> dict[str, Any]:
    scheme = "http" if application.config.is_local else "https"
    host = application.config.bind_host
    if host == "0.0.0.0":
        host = "<configured-host>"
    return {
        "schema_version": "1.0.0",
        "status": status,
        "pid": os.getpid(),
        "profile": application.config.profile,
        "listen_host": application.config.bind_host,
        "listen_port": int(server.server_address[1]),
        "base_url": f"{scheme}://{host}:{int(server.server_address[1])}",
        "build_id": application.build_id,
        "protocol_id": application.config.protocol_id,
        "contract_schema_version": application.config.contract_schema_version,
        "formal_semantics_id": application.config.formal_semantics_id,
        "instance_id": application.instance_id,
    }


def _write_runtime_document(path: Path, document: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _install_tls(
    server: WorkingVersionHttpServer,
    config: WorkingVersionConfig,
    certificate: Path | None,
    private_key: Path | None,
) -> None:
    if config.is_local:
        if certificate is not None or private_key is not None:
            raise ValueError("LOCAL_LOOPBACK profile must not be configured as remote TLS")
        return
    if certificate is None or private_key is None:
        raise ValueError("REMOTE_TLS profile requires --tls-cert and --tls-key")
    if not certificate.is_file() or not private_key.is_file():
        raise ValueError("REMOTE_TLS certificate and private key files must exist")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(certfile=certificate, keyfile=private_key)
    server.configure_tls(context)


def _watch_shutdown_file(
    shutdown_file: Path,
    stopped: threading.Event,
    initiate_shutdown: Callable[[str], None],
    logger: logging.Logger,
    *,
    poll_interval_seconds: float = 0.25,
    cleanup_attempt_limit: int = 3,
) -> None:
    """Consume one launch-scoped shutdown request without losing it on cleanup races."""
    request_observed = False
    cleanup_attempts = 0
    while not stopped.wait(poll_interval_seconds):
        if not request_observed:
            if not shutdown_file.is_file():
                continue
            request_observed = True
        try:
            shutdown_file.unlink(missing_ok=True)
        except OSError as exc:
            cleanup_attempts += 1
            logger.warning(
                "Shutdown request cleanup failed attempt=%s error=%s",
                cleanup_attempts,
                type(exc).__name__,
            )
            if cleanup_attempts < cleanup_attempt_limit:
                continue
            logger.error("Shutdown request cleanup remained unavailable; proceeding with shutdown")
        initiate_shutdown("shutdown-file")
        return


def run_host(args: argparse.Namespace) -> int:
    config = load_working_version_config(args.config)
    if args.port is not None:
        if args.port < 1 or args.port > 65535:
            raise ValueError("--port must be in [1, 65535]")
        override_origin = "http://127.0.0.1" + ("" if args.port == 80 else f":{args.port}")
        config = replace(
            config,
            port=args.port,
            allowed_origins=(override_origin,) if config.is_local else config.allowed_origins,
        )
    build_id = validate_build_id(args.build_id)
    if args.instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        try:
            instance_id = str(uuid.UUID(args.instance_id))
        except (AttributeError, ValueError) as exc:
            raise ValueError("--instance-id must be a canonical UUID") from exc
        if args.instance_id != instance_id:
            raise ValueError("--instance-id must be a canonical lowercase UUID")
    data_dir = args.data_dir.resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    logger = _configure_logging(data_dir)
    ui_dir = _validate_ui_dir(args.ui_dir)
    shutdown_file = _validate_shutdown_file(
        args.shutdown_file or (data_dir / f"shutdown-{instance_id}.request"),
        data_dir,
        instance_id,
    )
    if not config.is_local and args.bootstrap_local_identity:
        raise ValueError("REMOTE_TLS forbids local identity bootstrap")
    signing_key, worker_trust_roots = _identity_paths_for_profile(args, config)
    if config.is_local:
        remote_auth_config = args.remote_auth_config
        tls_certificate = args.tls_cert
        tls_private_key = args.tls_key
    else:
        remote_auth_config = _configured_path(args.remote_auth_config, "DELTA_REMOTE_AUTH_CONFIG")
        tls_certificate = _configured_path(args.tls_cert, "DELTA_TLS_CERT_FILE")
        tls_private_key = _configured_path(args.tls_key, "DELTA_TLS_KEY_FILE")
    if not config.is_local and (signing_key is None or worker_trust_roots is None):
        raise ValueError(
            "REMOTE_TLS requires explicit Controller signing key and Worker trust-roots files"
        )
    if not config.is_local and (tls_certificate is None or tls_private_key is None):
        raise ValueError("REMOTE_TLS requires --tls-cert and --tls-key")

    application, lease = build_application(
        config=config,
        build_id=build_id,
        data_dir=data_dir,
        allow_local_bootstrap=bool(args.bootstrap_local_identity and config.is_local),
        signing_key_path=signing_key,
        trust_roots_path=worker_trust_roots,
        remote_auth_config=remote_auth_config,
        instance_id=instance_id,
    )
    server: WorkingVersionHttpServer | None = None
    application_shutdown = False
    runtime_path = data_dir / "runtime.json"
    try:
        server = WorkingVersionHttpServer(
            (config.bind_host, config.port),
            application,
            ui_dir=ui_dir,
            logger=logger,
        )
        _install_tls(server, config, tls_certificate, tls_private_key)
        stopped = threading.Event()
        shutdown_lock = threading.Lock()

        def initiate_shutdown(reason: str) -> None:
            with shutdown_lock:
                if stopped.is_set():
                    return
                stopped.set()
                application.begin_shutdown()
                server.stopping.set()
                logger.info("Graceful shutdown requested reason=%s", reason)
            server.shutdown()

        def watch_shutdown_file() -> None:
            _watch_shutdown_file(shutdown_file, stopped, initiate_shutdown, logger)

        monitor = threading.Thread(
            target=watch_shutdown_file,
            name="delta-shutdown-monitor",
            daemon=True,
        )
        monitor.start()

        def signal_handler(signum: int, frame: object) -> None:
            del frame
            threading.Thread(
                target=initiate_shutdown,
                args=(f"signal-{signum}",),
                name="delta-signal-shutdown",
                daemon=True,
            ).start()

        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

        running_document = _runtime_document(
            application=application,
            server=server,
            status="RUNNING",
        )
        _write_runtime_document(runtime_path, running_document)
        print(json.dumps(running_document, sort_keys=True), flush=True)
        logger.info(
            "Working version ready profile=%s bind=%s port=%s build_id=%s",
            config.profile,
            config.bind_host,
            server.server_address[1],
            build_id,
        )
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            application.begin_shutdown()
            server.stopping.set()
        finally:
            stopped.set()
            server.stopping.set()
            monitor.join(timeout=1)
            server.server_close()
            try:
                application.shutdown()
            finally:
                # The concrete dispatch shutdown contract never completes until
                # all threads/processes have stopped using the durable directory,
                # even when it reports that the configured deadline was missed.
                application_shutdown = True
            stopped_document = copy.deepcopy(running_document)
            stopped_document["status"] = "STOPPED"
            _write_runtime_document(runtime_path, stopped_document)
        return 0
    finally:
        try:
            if server is not None and not server.stopping.is_set():
                server.server_close()
        finally:
            try:
                if not application_shutdown:
                    try:
                        application.shutdown()
                    finally:
                        application_shutdown = True
            finally:
                lease.release()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return run_host(args)
    except (OSError, RuntimeError, ValueError) as exc:
        # Configuration/startup errors intentionally contain no credential values.
        print(f"delta-working-version: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
