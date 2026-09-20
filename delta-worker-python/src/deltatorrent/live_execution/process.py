"""Single-request constrained Worker process protocol.

The process accepts exactly one bounded AuthorizedExecution JSON document on
stdin and emits exactly one bounded JSON result on stdout.  All argv values are
trusted deployment configuration; no intent field can influence a module,
callable, process command, or filesystem root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO

from deltatorrent.live_execution.crypto import jcs_bytes, sha256_prefixed
from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
from deltatorrent.live_execution.errors import (
    WorkerAdapterError,
    WorkerCancelledError,
    WorkerPreflightError,
    WorkerTimeoutError,
)
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight

MAX_AUTHORIZED_EXECUTION_BYTES = 10 * 1024 * 1024
MAX_TRUST_ROOTS_BYTES = 64 * 1024
MAX_JSON_DEPTH = 32
_FIXTURE_KEY_ID = "step5c-fixture-ed25519"
_FIXTURE_ISSUER_ID = "step5c-fixture-controller"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_ERROR_METADATA: dict[str, tuple[str, bool]] = {
    "ERR_SCHEMA_VALIDATION_FAILED": ("SCHEMA", False),
    "ERR_INTENT_DIGEST_MISMATCH": ("DIGEST", False),
    "ERR_ADMISSION_DIGEST_MISMATCH": ("DIGEST", False),
    "ERR_ADMISSION_SIGNATURE_INVALID": ("WORKER", False),
    "ERR_ADMISSION_EXPIRED": ("AUTHZ", False),
    "ERR_OPERATION_SCOPE_UNSUPPORTED": ("CATALOG", False),
    "ERR_AUTHORIZED_EXECUTION_PARITY_MISMATCH": ("LINEAGE", False),
    "ERR_STAGE_C_FORBIDDEN": ("CONSENSUS_BOUNDARY", False),
    "ERR_TIMEOUT": ("WORKER", True),
    "ERR_CANCELLED": ("WORKER", True),
    "ERR_WORKER_DISPATCH_FAILED": ("DISPATCH", True),
}


class WorkerProcessProtocolError(ValueError):
    """Raised before a trusted execution identity can be established."""


def _read_bounded(stream: BinaryIO, limit: int) -> bytes:
    payload = stream.read(limit + 1)
    if len(payload) > limit:
        raise WorkerProcessProtocolError(f"stdin exceeds the {limit}-byte process limit")
    if not payload:
        raise WorkerProcessProtocolError("stdin contains no AuthorizedExecution document")
    return payload


def _check_depth(value: Any, depth: int = 1) -> None:
    if depth > MAX_JSON_DEPTH:
        raise WorkerProcessProtocolError(f"AuthorizedExecution exceeds JSON depth {MAX_JSON_DEPTH}")
    if isinstance(value, dict):
        for nested in value.values():
            _check_depth(nested, depth + 1)
    elif isinstance(value, list):
        for nested in value:
            _check_depth(nested, depth + 1)


def load_trust_roots(path: Path | str) -> tuple[str, dict[str, str]]:
    """Load the strict runtime issuer and Ed25519 trust-root set."""
    trust_path = Path(path)
    raw = trust_path.read_bytes()
    if len(raw) > MAX_TRUST_ROOTS_BYTES:
        raise WorkerProcessProtocolError("trust-roots document exceeds 64 KiB")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerProcessProtocolError("trust-roots document is not valid UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) != {
        "schema_version",
        "issuer_id",
        "keys",
    }:
        raise WorkerProcessProtocolError("trust-roots document has an invalid shape")
    if document.get("schema_version") != "1.0.0":
        raise WorkerProcessProtocolError("unsupported trust-roots schema_version")
    issuer_id = document.get("issuer_id")
    if not isinstance(issuer_id, str) or not issuer_id.strip():
        raise WorkerProcessProtocolError("trust-roots issuer_id must be a non-empty string")
    if issuer_id == _FIXTURE_ISSUER_ID:
        raise WorkerProcessProtocolError("frozen fixture issuer is forbidden in trust roots")
    configured = document.get("keys")
    if not isinstance(configured, list) or not configured:
        raise WorkerProcessProtocolError("at least one explicit Worker trust root is required")
    trusted_keys: dict[str, str] = {}
    for item in configured:
        if not isinstance(item, dict) or set(item) != {
            "key_id",
            "algorithm",
            "public_key_hex",
        }:
            raise WorkerProcessProtocolError("trust-root key entry has an invalid shape")
        key_id = item.get("key_id")
        algorithm = item.get("algorithm")
        public_key_hex = item.get("public_key_hex")
        if not isinstance(key_id, str) or not isinstance(public_key_hex, str):
            raise WorkerProcessProtocolError("trust-root key fields must be strings")
        if algorithm != "ED25519":
            raise WorkerProcessProtocolError("trust-root algorithm must be ED25519")
        if key_id == _FIXTURE_KEY_ID:
            raise WorkerProcessProtocolError(
                "frozen fixture trust is forbidden in the Worker process"
            )
        if key_id in trusted_keys:
            raise WorkerProcessProtocolError(f"duplicate trust-root key_id '{key_id}'")
        trusted_keys[key_id] = public_key_hex
    # Reuse the fail-closed key material validator.
    AuthorizedExecutionPreflight(trusted_keys=trusted_keys)
    return (issuer_id, trusted_keys)


def _error_document(error: WorkerAdapterError) -> dict[str, Any]:
    category, retryable = _ERROR_METADATA.get(error.code, ("DISPATCH", True))
    return {
        "schema_version": "1.0.0",
        "error_code": error.code if error.code in _ERROR_METADATA else "ERR_WORKER_DISPATCH_FAILED",
        "category": category,
        "retryable": retryable,
        "message": error.message[:512],
    }


def _identity(bundle: Mapping[str, Any]) -> tuple[str, str, str]:
    intent = bundle.get("intent")
    admission = bundle.get("admission")
    if not isinstance(intent, Mapping) or not isinstance(admission, Mapping):
        return ("", "", "")
    return (
        str(admission.get("execution_id", "")),
        str(intent.get("intent_id", "")),
        str(intent.get("operation", "")),
    )


def execute_authorized_document(
    document: dict[str, Any],
    *,
    trusted_keys: Mapping[str, str],
    trusted_issuer_id: str,
    producer_commit: str,
    cache_root: Path | str,
    current_time: datetime | None = None,
) -> dict[str, Any]:
    """Preflight and execute one already-parsed AuthorizedExecution document."""
    if _SHA_RE.fullmatch(producer_commit) is None:
        raise WorkerProcessProtocolError(
            "producer_commit must be an explicit 40-character lowercase build SHA"
        )
    execution_id, intent_id, operation = _identity(document)
    admission = document.get("admission")
    authenticator = admission.get("authenticator") if isinstance(admission, dict) else None
    if not isinstance(authenticator, dict) or authenticator.get("issuer_id") != trusted_issuer_id:
        raise WorkerProcessProtocolError("admission issuer_id does not match the configured issuer")
    preflight = AuthorizedExecutionPreflight(trusted_keys=dict(trusted_keys))
    try:
        context = preflight.validate(document, current_time=current_time)
    except WorkerPreflightError as exc:
        return {
            "dispatched": False,
            "execution_id": execution_id,
            "intent_id": intent_id,
            "operation": operation,
            "status": "FAILED",
            "error": _error_document(exc),
            "receipt": None,
            "receipt_digest": None,
        }

    dispatcher = ClosedEnumWorkerDispatcher(
        producer_commit=producer_commit,
        cache_root=cache_root,
    )
    try:
        worker_result = dispatcher.dispatch(context)
        receipt = worker_result.get("receipt")
        receipt_digest = None
        if isinstance(receipt, dict):
            receipt_digest = sha256_prefixed(jcs_bytes(receipt))
        return {
            "dispatched": True,
            "execution_id": context.execution_id,
            "intent_id": context.intent_id,
            "operation": context.operation,
            "status": worker_result.get("status"),
            "receipt": receipt,
            "receipt_digest": receipt_digest,
            "metrics": worker_result.get("metrics"),
            "materialize_info": worker_result.get("materialize_info"),
        }
    except WorkerAdapterError as exc:
        if isinstance(exc, WorkerTimeoutError):
            status = "TIMED_OUT"
        elif isinstance(exc, WorkerCancelledError):
            status = "CANCELLED"
        else:
            status = "FAILED"
        return {
            "dispatched": True,
            "execution_id": context.execution_id,
            "intent_id": context.intent_id,
            "operation": context.operation,
            "status": status,
            "error": _error_document(exc),
            "receipt": None,
            "receipt_digest": None,
        }


def execute_authorized_bytes(
    raw: bytes,
    *,
    trusted_keys: Mapping[str, str],
    trusted_issuer_id: str,
    producer_commit: str,
    cache_root: Path | str,
    current_time: datetime | None = None,
) -> dict[str, Any]:
    """Parse one bounded UTF-8 JSON document and execute it."""
    if len(raw) > MAX_AUTHORIZED_EXECUTION_BYTES:
        raise WorkerProcessProtocolError(
            f"AuthorizedExecution exceeds {MAX_AUTHORIZED_EXECUTION_BYTES} bytes"
        )
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerProcessProtocolError("stdin is not one valid UTF-8 JSON document") from exc
    if not isinstance(document, dict):
        raise WorkerProcessProtocolError("AuthorizedExecution must be a JSON object")
    _check_depth(document)
    return execute_authorized_document(
        document,
        trusted_keys=trusted_keys,
        trusted_issuer_id=trusted_issuer_id,
        producer_commit=producer_commit,
        cache_root=cache_root,
        current_time=current_time,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="delta-live-worker")
    parser.add_argument("--trust-roots", type=Path, required=True)
    parser.add_argument("--producer-commit", required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        trusted_issuer_id, trusted_keys = load_trust_roots(args.trust_roots)
        payload = _read_bounded(sys.stdin.buffer, MAX_AUTHORIZED_EXECUTION_BYTES)
        result = execute_authorized_bytes(
            payload,
            trusted_keys=trusted_keys,
            trusted_issuer_id=trusted_issuer_id,
            producer_commit=args.producer_commit,
            cache_root=args.cache_root,
        )
    except (OSError, ValueError) as exc:
        result = {
            "protocol_error": {
                "error_code": "ERR_WORKER_DISPATCH_FAILED",
                "message": str(exc)[:512],
            }
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
        return 2

    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
