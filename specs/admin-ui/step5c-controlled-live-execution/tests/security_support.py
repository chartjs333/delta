"""Security test support for Step 5C (T029-T034).

Pure-Python, zero external dependencies, mathematically compliant with:
- RFC 8785 (JSON Canonicalization Scheme)
- RFC 8032 (Ed25519 digital signature verification)
- ADR 0002 controlled execution boundary invariants
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

FIXTURE_PUBLIC_KEY_HEX = "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"
FIXTURE_KEY_ID = "step5c-fixture-ed25519"
POLICY_VERSION = "step5c-policy-v1"
SCHEMA_VERSION = "1.0.0"


# --- RFC 8785 JCS Canonicalization ---


def _number_to_jcs(value: int | float) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JCS does not permit non-finite floats")
        if value == 0.0:
            return "0"
        return json.dumps(value)
    raise TypeError(f"unsupported number type: {type(value)!r}")


def jcs_dumps(obj: Any) -> str:
    """Serialize object to RFC 8785 canonical JSON string."""
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, (int, float)):
        return _number_to_jcs(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, list):
        return "[" + ",".join(jcs_dumps(item) for item in obj) + "]"
    if isinstance(obj, dict):
        sorted_keys = sorted(obj.keys(), key=lambda k: k.encode("utf-16-be"))
        pairs = [f"{json.dumps(k, ensure_ascii=False)}:{jcs_dumps(obj[k])}" for k in sorted_keys]
        return "{" + ",".join(pairs) + "}"
    raise TypeError(f"Object of type {type(obj).__name__} is not JCS serializable")


def jcs_bytes(obj: Any) -> bytes:
    """Serialize object to RFC 8785 canonical UTF-8 bytes."""
    return jcs_dumps(obj).encode("utf-8")


def sha256_prefixed(data: bytes) -> str:
    """Compute sha256 hex prefixed with 'sha256:'."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_intent_digest(intent: dict[str, Any]) -> bool:
    r"""Verify intent_digest over intent \ {intent_digest}."""
    declared = intent.get("intent_digest")
    if not declared:
        return False
    intent_copy = copy.deepcopy(intent)
    intent_copy.pop("intent_digest", None)
    expected = sha256_prefixed(jcs_bytes(intent_copy))
    return bool(declared == expected)


def verify_admission_digest(admission: dict[str, Any]) -> bool:
    r"""Verify admission_digest over admission \ {admission_digest, authenticator}."""
    declared = admission.get("admission_digest")
    if not declared:
        return False
    adm_copy = copy.deepcopy(admission)
    adm_copy.pop("admission_digest", None)
    adm_copy.pop("authenticator", None)
    expected = sha256_prefixed(jcs_bytes(adm_copy))
    return bool(declared == expected)


# --- RFC 8032 Pure-Python Ed25519 Verification ---

_P = 2**255 - 19
_D = -121665 * pow(121666, _P - 2, _P) % _P
_Q = 2**252 + 27742317777372353535851937790883648493
_I = pow(2, (_P - 1) // 4, _P)


def _inv(z: int) -> int:
    return pow(z, _P - 2, _P)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P != 0:
        x = (x * _I) % _P
    if x % 2 != 0:
        x = _P - x
    return x


_By = 4 * _inv(5) % _P
_Bx = _xrecover(_By)
_B = (_Bx % _P, _By % _P)


def _edwards_add(p1: tuple[int, int], p2: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = p1
    x2, y2 = p2
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _D * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _D * x1 * x2 * y1 * y2)
    return (x3 % _P, y3 % _P)


def _scalarmult(pt: tuple[int, int], e: int) -> tuple[int, int]:
    if e == 0:
        return (0, 1)
    q = _scalarmult(pt, e // 2)
    q = _edwards_add(q, q)
    if e & 1:
        q = _edwards_add(q, pt)
    return q


def _decodepoint(s: bytes) -> tuple[int, int]:
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    x = _xrecover(y)
    if (x & 1) != ((s[31] >> 7) & 1):
        x = _P - x
    return (x, y)


def verify_ed25519(
    public_key_bytes: bytes,
    msg: bytes,
    sig_bytes: bytes,
) -> bool:
    """Verify Ed25519 digital signature per RFC 8032."""
    if len(public_key_bytes) != 32 or len(sig_bytes) != 64:
        return False
    try:
        r_raw = sig_bytes[:32]
        s_raw = sig_bytes[32:]
        s_val = int.from_bytes(s_raw, "little")
        if s_val >= _Q:
            return False
        pt_a = _decodepoint(public_key_bytes)
        pt_r = _decodepoint(r_raw)
        h = hashlib.sha512(r_raw + public_key_bytes + msg).digest()
        k = int.from_bytes(h, "little") % _Q
        sb = _scalarmult(_B, s_val)
        rak = _edwards_add(pt_r, _scalarmult(pt_a, k))
        return bool(sb == rak)
    except Exception:
        return False


def verify_admission_signature(
    admission: dict[str, Any],
    trusted_pubkey_hex: str | None = None,
) -> bool:
    r"""Verify Ed25519 signature on AdmissionRecord over admission \ {authenticator.signature}."""
    authenticator = admission.get("authenticator")
    if not isinstance(authenticator, dict):
        return False
    sig_hex = authenticator.get("signature")
    if not isinstance(sig_hex, str):
        return False

    pub_hex = trusted_pubkey_hex or FIXTURE_PUBLIC_KEY_HEX
    try:
        sig_bytes = bytes.fromhex(sig_hex)
        pub_bytes = bytes.fromhex(pub_hex)
    except Exception:
        return False

    adm_copy = copy.deepcopy(admission)
    if "authenticator" in adm_copy and isinstance(adm_copy["authenticator"], dict):
        adm_copy["authenticator"].pop("signature", None)

    msg_bytes = jcs_bytes(adm_copy)
    return verify_ed25519(pub_bytes, msg_bytes, sig_bytes)


# --- Idempotency & Replay Ledger Simulation ---


@dataclass
class IntentLedgerEntry:
    intent_id: str
    intent_digest: str
    authenticated_subject: str
    admitted_at: str
    execution_id: str
    admission_record: dict[str, Any]
    status: str = "ADMITTED"


class SecurityIdempotencyLedger:
    """Authoritative Controller idempotency ledger adhering to ADR 0002."""

    def __init__(self) -> None:
        self.by_intent_id: dict[str, IntentLedgerEntry] = {}
        self.by_intent_digest: dict[str, str] = {}
        self.worker_start_count = 0

    def submit_intent(
        self,
        intent: dict[str, Any],
        authenticated_subject: str,
        admission_factory: Any = None,
    ) -> tuple[str, str, dict[str, Any] | None]:
        intent_id = intent.get("intent_id", "")
        intent_digest = intent.get("intent_digest", "")

        if not verify_intent_digest(intent):
            return "REJECTED", "ERR_INTENT_DIGEST_MISMATCH", None

        # Replay / Idempotency evaluation
        if intent_id in self.by_intent_id:
            existing = self.by_intent_id[intent_id]

            if existing.authenticated_subject != authenticated_subject:
                return "REJECTED", "ERR_UNAUTHORIZED_PEER_OR_ROLE", None

            if existing.intent_digest != intent_digest:
                return "REJECTED", "ERR_INTENT_COLLISION_DETECTED", None

            return "REPLAY_IDEMPOTENT", "OK", existing.admission_record

        if intent_digest in self.by_intent_digest:
            return "REJECTED", "ERR_INTENT_COLLISION_DETECTED", None

        execution_id = f"exec-{intent_id[:8]}"
        if admission_factory:
            admission = admission_factory(intent, execution_id, authenticated_subject)
        else:
            admission = {
                "admission_id": f"adm-{intent_id[:8]}",
                "intent_id": intent_id,
                "intent_digest": intent_digest,
                "execution_id": execution_id,
            }

        entry = IntentLedgerEntry(
            intent_id=intent_id,
            intent_digest=intent_digest,
            authenticated_subject=authenticated_subject,
            admitted_at=datetime.now(UTC).isoformat(),
            execution_id=execution_id,
            admission_record=admission,
        )
        self.by_intent_id[intent_id] = entry
        self.by_intent_digest[intent_digest] = intent_id
        self.worker_start_count += 1

        return "ADMITTED", "OK", admission

    def snapshot(self) -> str:
        data = {
            "by_intent_id": {
                k: {
                    "intent_id": v.intent_id,
                    "intent_digest": v.intent_digest,
                    "authenticated_subject": v.authenticated_subject,
                    "admitted_at": v.admitted_at,
                    "execution_id": v.execution_id,
                    "admission_record": v.admission_record,
                    "status": v.status,
                }
                for k, v in self.by_intent_id.items()
            },
            "by_intent_digest": self.by_intent_digest,
            "worker_start_count": self.worker_start_count,
        }
        return json.dumps(data)

    @classmethod
    def restore(cls, snapshot_json: str) -> SecurityIdempotencyLedger:
        data = json.loads(snapshot_json)
        ledger = cls()
        for k, v in data["by_intent_id"].items():
            ledger.by_intent_id[k] = IntentLedgerEntry(**v)
        ledger.by_intent_digest = data["by_intent_digest"]
        ledger.worker_start_count = data["worker_start_count"]
        return ledger


# --- Policy & Role Access Control Simulation ---


class SecurityPolicyEngine:
    """Policy engine enforcing RBAC, audience, and catalog boundaries per ADR 0002."""

    REQUIRED_POLICY_VERSION = "step5c-policy-v1"
    ALLOWED_ROLES = frozenset({"OPERATOR", "ADMIN"})

    @classmethod
    def evaluate(
        cls,
        intent: dict[str, Any],
        peer_credential: dict[str, Any],
        catalog_snapshot: dict[str, Any],
    ) -> tuple[bool, str]:
        if peer_credential.get("expired", False):
            return False, "ERR_AUTH_TOKEN_EXPIRED"

        if peer_credential.get("audience") != "delta-live-execution-controller":
            return False, "ERR_INVALID_AUDIENCE"

        effective_roles = set(peer_credential.get("roles", []))
        if not (effective_roles & cls.ALLOWED_ROLES):
            return False, "ERR_UNAUTHORIZED_PEER_OR_ROLE"

        declared_op = intent.get("declared_operator", {})
        declared_role = declared_op.get("role")
        if declared_role in cls.ALLOWED_ROLES and declared_role not in effective_roles:
            return False, "ERR_ROLE_ESCALATION_DETECTED"

        declared_policy = intent.get("policy_version") or intent.get("policy_context", {}).get(
            "policy_version"
        )
        if declared_policy and declared_policy != cls.REQUIRED_POLICY_VERSION:
            return False, "ERR_POLICY_VERSION_MISMATCH"

        expected_cat_ref = catalog_snapshot.get("source", {}).get("backend_ref")
        intent_cat_ref = intent.get("workload", {}).get("catalog_backend_ref")
        if not intent_cat_ref or intent_cat_ref != expected_cat_ref:
            return False, "ERR_CATALOG_REF_MISMATCH"

        op = intent.get("operation")
        scope = intent.get("workload", {}).get("requested_scope")
        plugin_id = intent.get("workload", {}).get("model_plugin_id")

        plugins = catalog_snapshot.get("model_plugins", [])
        plugin_desc = next((p for p in plugins if p.get("plugin_id") == plugin_id), None)
        if not plugin_desc:
            return False, "ERR_UNKNOWN_MODEL_PLUGIN"

        if scope not in plugin_desc.get("supported_scopes", []):
            return False, "ERR_UNSUPPORTED_SCOPE"

        if op not in plugin_desc.get("supported_operations", []):
            return False, "ERR_UNSUPPORTED_OPERATION"

        return True, "OK"
