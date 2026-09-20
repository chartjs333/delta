#!/usr/bin/env python3
"""Black-box smoke client for the single-host Delta working version.

The client intentionally uses only the Python standard library.  In the local
profile it sends no credential or identity header: the host derives the trusted
subject from the accepted loopback socket peer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CATALOG_BACKEND_REF = "670b58f6458fe84620f4f9f46401f855d04ae05d"
MODEL_PLUGIN_ID = "tabular-10gene-phenotype-v1"
DATASET_ID = "synthetic-10gene-cohort-v1"
TERMINAL_STATES = frozenset({"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"})


class SmokeFailure(RuntimeError):
    """Raised when the live working-version behavior differs from its contract."""


@dataclass(frozen=True, slots=True)
class HttpFailure(Exception):
    status: int
    document: object

    def __str__(self) -> str:
        return f"HTTP {self.status}: {self.document!r}"


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _reject_floating_point(value: object) -> None:
    if isinstance(value, float):
        raise TypeError("Smoke intent canonicalization does not permit floating-point values")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_floating_point(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_floating_point(nested)


def canonical_json(value: object) -> bytes:
    """Return RFC 8785-compatible bytes for the integer/string smoke document.

    ExecutionIntent field names and generated values are ASCII, and its only
    JSON number is an integer.  Under that deliberately narrow input domain,
    compact UTF-8 JSON with lexicographically sorted keys is identical to JCS.
    """

    _reject_floating_point(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def compute_intent_digest(intent: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in intent.items() if key != "intent_digest"}
    return "sha256:" + hashlib.sha256(canonical_json(unsigned)).hexdigest()


def build_train_intent(*, retry_of: str | None = None) -> dict[str, Any]:
    now = datetime.now(UTC)
    intent_id = str(uuid.uuid4())
    constraints: dict[str, Any] = {
        "requested_allow_downloads": False,
        "timeout_seconds": 60,
    }
    if retry_of is not None:
        constraints["retry_of_intent_id"] = retry_of

    intent: dict[str, Any] = {
        "schema_version": "1.0.0",
        "intent_id": intent_id,
        "created_at": _timestamp(now),
        "expires_at": _timestamp(now + timedelta(minutes=10)),
        "declared_operator": {
            "subject_id": "untrusted.local-draft",
            "role": "OPERATOR",
        },
        "workload": {
            "model_plugin_id": MODEL_PLUGIN_ID,
            "dataset_id": DATASET_ID,
            "requested_scope": "PLUGIN_BOUNDARY",
            "catalog_backend_ref": CATALOG_BACKEND_REF,
        },
        "operation": "TRAIN_TICKET",
        "operation_payload": {
            "ticket_id": "smoke_" + intent_id.replace("-", "")[:20],
            "partition_id": "partition_00",
        },
        "execution_constraints": constraints,
    }
    intent["intent_digest"] = compute_intent_digest(intent)
    return intent


class WorkingVersionClient:
    def __init__(self, base_url: str, origin: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.origin = origin
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        document: object | None = None,
        *,
        include_delta_request: bool = True,
    ) -> tuple[int, object]:
        body = None
        headers = {
            "Accept": "application/json",
            "Origin": self.origin,
        }
        if include_delta_request:
            headers["X-Delta-Request"] = "1"
        if document is not None:
            body = json.dumps(
                document,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(
            self.base_url + path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
                parsed: object = json.loads(raw) if raw else None
                return response.status, parsed
        except HTTPError as exc:
            raw = exc.read()
            try:
                parsed_error: object = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed_error = raw.decode("utf-8", errors="replace")[:512]
            raise HttpFailure(exc.code, parsed_error) from exc
        except URLError as exc:
            raise SmokeFailure(f"Cannot reach {self.base_url}{path}: {exc.reason}") from exc

    def health(self) -> dict[str, Any]:
        _, document = self._request("GET", "/healthz")
        return _require_object(document, "health response")

    def ready(self) -> dict[str, Any]:
        _, document = self._request("GET", "/readyz")
        return _require_object(document, "readiness response")

    def submit(self, intent: dict[str, Any]) -> dict[str, Any]:
        status, document = self._request("POST", "/api/v1/intent/submit", intent)
        if status not in {200, 201}:
            raise SmokeFailure(f"Unexpected submit status {status}")
        result = _require_object(document, "submit response")
        _require_object(result.get("admission"), "submit admission")
        _require_object(result.get("status"), "submit status")
        return result

    def status(self, execution_id: str) -> dict[str, Any]:
        _, document = self._request("GET", f"/api/v1/execution/{execution_id}/status")
        return _require_object(document, "execution status")

    def receipt(self, execution_id: str) -> dict[str, Any]:
        _, document = self._request("GET", f"/api/v1/execution/{execution_id}/receipt")
        return _require_object(document, "execution receipt")

    def cancel(self, execution_id: str) -> dict[str, Any]:
        _, document = self._request(
            "POST",
            f"/api/v1/execution/{execution_id}/cancel",
            {},
        )
        return _require_object(document, "cancel status")

    def wait_terminal(self, execution_id: str, deadline_seconds: float) -> dict[str, Any]:
        deadline = time.monotonic() + deadline_seconds
        last_status: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            last_status = self.status(execution_id)
            if last_status.get("state") in TERMINAL_STATES:
                return last_status
            time.sleep(0.1)
        raise SmokeFailure(
            f"Execution {execution_id} did not become terminal; last status={last_status!r}"
        )


def _require_object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SmokeFailure(f"{name} must be a JSON object")
    return value


def _execution_id(submission: dict[str, Any]) -> str:
    admission = _require_object(submission.get("admission"), "submit admission")
    value = admission.get("execution_id")
    if not isinstance(value, str):
        raise SmokeFailure("Submit admission lacks execution_id")
    return value


def _verify_rejection(client: WorkingVersionClient) -> dict[str, Any]:
    rejected_intent = build_train_intent()
    try:
        client._request(
            "POST",
            "/api/v1/intent/submit",
            rejected_intent,
            include_delta_request=False,
        )
    except HttpFailure as exc:
        if exc.status != 400:
            raise SmokeFailure(
                f"Missing X-Delta-Request mapped to {exc.status}, expected 400"
            ) from exc
        return {
            "http_status": exc.status,
            "intent_id": rejected_intent["intent_id"],
        }
    raise SmokeFailure("Submit without X-Delta-Request was not rejected")


def _verify_cancel(client: WorkingVersionClient, attempts: int = 3) -> dict[str, Any]:
    terminal_races: list[str] = []
    for _ in range(attempts):
        intent = build_train_intent()
        submission = client.submit(intent)
        execution_id = _execution_id(submission)
        try:
            cancelled = client.cancel(execution_id)
        except HttpFailure as exc:
            if exc.status == 409:
                terminal_races.append(execution_id)
                continue
            raise
        if cancelled.get("state") != "CANCELLED" or cancelled.get("terminal") is not True:
            raise SmokeFailure(f"Cancel did not return terminal CANCELLED: {cancelled!r}")
        try:
            client.receipt(execution_id)
        except HttpFailure as exc:
            if exc.status != 404:
                raise SmokeFailure(
                    f"Cancelled execution receipt mapped to {exc.status}, expected 404"
                ) from exc
        else:
            raise SmokeFailure("Cancelled execution unexpectedly published a success receipt")
        return {
            "execution_id": execution_id,
            "intent_id": intent["intent_id"],
            "state": "CANCELLED",
            "terminal_races_before_cancel": terminal_races,
        }
    raise SmokeFailure(
        "Immediate cancellation lost every race; terminal executions were "
        + ", ".join(terminal_races)
    )


def _verify_success(
    client: WorkingVersionClient,
    terminal_timeout_seconds: float,
) -> dict[str, Any]:
    intent = build_train_intent()
    submission = client.submit(intent)
    admission = _require_object(submission.get("admission"), "submit admission")
    execution_id = _execution_id(submission)
    status = client.wait_terminal(execution_id, terminal_timeout_seconds)
    if status.get("state") != "COMPLETED" or status.get("terminal") is not True:
        raise SmokeFailure(f"Expected terminal COMPLETED execution, got {status!r}")

    receipt = client.receipt(execution_id)
    provenance = _require_object(receipt.get("provenance"), "receipt provenance")
    expected = {
        "intent_id": intent["intent_id"],
        "intent_digest": intent["intent_digest"],
        "admission_id": admission.get("admission_id"),
        "admission_digest": admission.get("admission_digest"),
        "execution_id": execution_id,
    }
    mismatches = {
        key: {"expected": value, "actual": provenance.get(key)}
        for key, value in expected.items()
        if provenance.get(key) != value
    }
    if mismatches:
        raise SmokeFailure(f"Receipt lineage mismatch: {mismatches!r}")

    return {
        "intent_id": intent["intent_id"],
        "intent_digest": intent["intent_digest"],
        "admission_id": admission["admission_id"],
        "admission_digest": admission["admission_digest"],
        "execution_id": execution_id,
        "status": status,
        "receipt": receipt,
    }


def run_smoke(
    *,
    base_url: str,
    origin: str,
    request_timeout_seconds: float = 30.0,
    terminal_timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    client = WorkingVersionClient(base_url, origin, request_timeout_seconds)
    health = client.health()
    readiness = client.ready()
    rejection = _verify_rejection(client)
    cancellation = _verify_cancel(client)
    success = _verify_success(client, terminal_timeout_seconds)
    return {
        "schema_version": "1.0.0",
        "result": "PASS",
        "base_url": base_url.rstrip("/"),
        "health": health,
        "readiness": readiness,
        "rejection": rejection,
        "cancellation": cancellation,
        "success": success,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--origin", default=None)
    parser.add_argument("--request-timeout-seconds", type=float, default=30.0)
    parser.add_argument("--terminal-timeout-seconds", type=float, default=120.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    origin = args.origin or args.base_url.rstrip("/")
    try:
        result = run_smoke(
            base_url=args.base_url,
            origin=origin,
            request_timeout_seconds=args.request_timeout_seconds,
            terminal_timeout_seconds=args.terminal_timeout_seconds,
        )
    except (HttpFailure, SmokeFailure, ValueError, TypeError) as exc:
        print(f"working-version smoke: FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
