"""RFC 8785 JSON Canonicalization Scheme (JCS), SHA-256, and Ed25519 operations."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from deltacontroller.errors import JcsCanonicalizationError


def _order_keys(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            key: _order_keys(obj[key])
            for key in sorted(obj, key=lambda item: item.encode("utf-16-be"))
        }
    if isinstance(obj, list):
        return [_order_keys(item) for item in obj]
    return obj


def _format_number(value: int | float) -> str:
    if isinstance(value, bool):
        raise TypeError("bool is not a valid number")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite numbers are forbidden in JCS")
        if value == 0.0:
            return "0"
        text = repr(value)
        if "e" in text or "E" in text:
            base, exp = text.lower().split("e")
            exp_int = int(exp)
            return f"{base}e{'+' if exp_int >= 0 else ''}{exp_int}"
        return text
    raise TypeError(f"Unsupported number type: {type(value)}")


def canonicalize_jcs(value: Any) -> bytes:
    """Canonicalize a JSON-serializable Python data structure per RFC 8785."""
    try:
        ordered = _order_keys(value)
        # Use separators=(',', ':') and ensure_ascii=False for standard UTF-8 output
        raw = json.dumps(
            ordered,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        return raw.encode("utf-8")
    except Exception as exc:
        raise JcsCanonicalizationError(
            f"Failed to canonicalize document per RFC 8785: {exc}"
        ) from exc


def sha256_digest(canonical_bytes: bytes) -> str:
    """Compute sha256:... digest string over canonical bytes."""
    return f"sha256:{hashlib.sha256(canonical_bytes).hexdigest()}"


def compute_intent_digest(intent_doc: dict[str, Any]) -> str:
    """Compute RFC 8785 digest over ExecutionIntent excluding 'intent_digest'."""
    doc = copy.deepcopy(intent_doc)
    doc.pop("intent_digest", None)
    return sha256_digest(canonicalize_jcs(doc))


def verify_intent_digest(intent_doc: dict[str, Any]) -> bool:
    """Verify that intent_doc['intent_digest'] matches recomputed JCS digest."""
    declared = intent_doc.get("intent_digest")
    if not declared:
        return False
    expected = compute_intent_digest(intent_doc)
    return bool(declared == expected)


def compute_admission_digest(admission_doc: dict[str, Any]) -> str:
    """Compute RFC 8785 digest over AdmissionRecord excluding digest and authenticator."""
    doc = copy.deepcopy(admission_doc)
    doc.pop("admission_digest", None)
    doc.pop("authenticator", None)
    return sha256_digest(canonicalize_jcs(doc))


def get_admission_signing_payload(admission_doc: dict[str, Any]) -> bytes:
    """Get RFC 8785 bytes of AdmissionRecord excluding only 'authenticator.signature'."""
    doc = copy.deepcopy(admission_doc)
    auth = doc.get("authenticator")
    if isinstance(auth, dict):
        auth_copy = copy.deepcopy(auth)
        auth_copy.pop("signature", None)
        doc["authenticator"] = auth_copy
    return canonicalize_jcs(doc)


def sign_admission(admission_doc: dict[str, Any], private_key: Ed25519PrivateKey) -> str:
    """Sign AdmissionRecord over RFC8785(admission \\ signature) and return hex signature."""
    payload = get_admission_signing_payload(admission_doc)
    sig_bytes = private_key.sign(payload)
    return sig_bytes.hex()


def verify_admission_signature(admission_doc: dict[str, Any], public_key: Ed25519PublicKey) -> bool:
    """Verify admission signature over RFC8785(admission \\ signature)."""
    auth = admission_doc.get("authenticator")
    if not isinstance(auth, dict):
        return False
    sig_hex = auth.get("signature")
    if not isinstance(sig_hex, str):
        return False
    try:
        sig_bytes = bytes.fromhex(sig_hex)
        payload = get_admission_signing_payload(admission_doc)
        public_key.verify(sig_bytes, payload)
        return True
    except (ValueError, InvalidSignature):
        return False


def get_public_key_hex(private_key: Ed25519PrivateKey) -> str:
    """Extract raw 32-byte public key as hex string."""
    return private_key.public_key().public_bytes_raw().hex()


def load_private_key(key_input: Ed25519PrivateKey | bytes | str) -> Ed25519PrivateKey:
    """Load or parse an Ed25519PrivateKey from instance, bytes, hex, or PEM string/path."""
    if isinstance(key_input, Ed25519PrivateKey):
        return key_input
    if isinstance(key_input, bytes):
        if len(key_input) == 32:
            return Ed25519PrivateKey.from_private_bytes(key_input)
        loaded = serialization.load_pem_private_key(key_input, password=None)
        if isinstance(loaded, Ed25519PrivateKey):
            return loaded
        raise ValueError(f"Loaded key is not Ed25519PrivateKey: {type(loaded)}")
    if isinstance(key_input, str):
        path = Path(key_input)
        if path.exists() and path.is_file():
            return load_private_key(path.read_bytes())
        if "BEGIN PRIVATE KEY" in key_input or "BEGIN ED25519 PRIVATE KEY" in key_input:
            loaded = serialization.load_pem_private_key(key_input.encode("utf-8"), password=None)
            if isinstance(loaded, Ed25519PrivateKey):
                return loaded
            raise ValueError(f"Loaded key is not Ed25519PrivateKey: {type(loaded)}")
        raw_text = key_input.strip()
        try:
            raw_bytes = bytes.fromhex(raw_text)
            if len(raw_bytes) == 32:
                return Ed25519PrivateKey.from_private_bytes(raw_bytes)
        except ValueError:
            pass
    raise ValueError(f"Cannot load Ed25519 private key from input type: {type(key_input)}")
