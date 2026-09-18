"""Pure-Python standalone RFC 8785 (JCS), SHA-256 and Ed25519 verification.

Zero external dependencies to preserve strict offline worker isolation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from typing import Any

# Pinned fixture public key hex matching ADR 0002 / T008 contract fixtures
FIXTURE_PUBLIC_KEY_HEX = "03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8"


def _number_to_jcs(value: int | float) -> str:
    """Serialize number per RFC 8785 Section 3.2.2.3 and ECMA-262 Section 7.1.12.1."""
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not valid JCS")
        if value == 0.0:
            return "0"
        if value < 0:
            return "-" + _number_to_jcs(-value)

        s_rep = repr(value)
        if "e" in s_rep or "E" in s_rep:
            parts = s_rep.lower().split("e")
            significand = parts[0]
            exp = int(parts[1])
        else:
            significand = s_rep
            exp = 0

        if "." in significand:
            int_part, frac_part = significand.split(".")
            digits = int_part + frac_part
            dec_places = len(frac_part)
        else:
            digits = significand
            dec_places = 0

        digits = digits.lstrip("0")
        if not digits:
            return "0"

        trimmed_digits = digits.rstrip("0")
        trailing_zeroes = len(digits) - len(trimmed_digits)
        dec_places -= trailing_zeroes
        digits = trimmed_digits

        k = len(digits)
        n = exp - dec_places + k

        # Rule 6: If k <= n <= 21
        if k <= n <= 21:
            return digits + "0" * (n - k)
        # Rule 7: If 0 < n <= 21 and n < k
        if 0 < n <= 21:
            return digits[:n] + "." + digits[n:]
        # Rule 8: If -6 < n <= 0
        if -6 < n <= 0:
            return "0." + "0" * (-n) + digits
        # Rule 9 & 10: Exponential
        exp_val = n - 1
        sign = "+" if exp_val >= 0 else "-"
        exp_str = f"e{sign}{abs(exp_val)}"
        if k == 1:
            return digits + exp_str
        return digits[0] + "." + digits[1:] + exp_str
    raise TypeError(f"unsupported number type: {type(value)!r}")


def jcs_dumps(obj: Any) -> str:
    """RFC 8785 canonical JSON serializer with UTF-16 code-unit sorted keys."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return _number_to_jcs(obj)
    if isinstance(obj, list):
        return "[" + ",".join(jcs_dumps(item) for item in obj) + "]"
    if isinstance(obj, dict):
        pieces: list[str] = []
        for key in sorted(obj, key=lambda item: str(item).encode("utf-16-be")):
            pieces.append(jcs_dumps(str(key)) + ":" + jcs_dumps(obj[key]))
        return "{" + ",".join(pieces) + "}"
    raise TypeError(f"unsupported JCS value: {type(obj)!r}")


def jcs_bytes(obj: Any) -> bytes:
    return jcs_dumps(obj).encode("utf-8")


def sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verify_intent_digest(intent: dict[str, Any]) -> bool:
    declared = intent.get("intent_digest")
    if not declared:
        return False
    intent_copy = copy.deepcopy(intent)
    intent_copy.pop("intent_digest", None)
    expected = sha256_prefixed(jcs_bytes(intent_copy))
    return bool(declared == expected)


def verify_admission_digest(admission: dict[str, Any]) -> bool:
    declared = admission.get("admission_digest")
    if not declared:
        return False
    adm_copy = copy.deepcopy(admission)
    adm_copy.pop("admission_digest", None)
    adm_copy.pop("authenticator", None)
    expected = sha256_prefixed(jcs_bytes(adm_copy))
    return bool(declared == expected)


# --- RFC 8032 pure-Python Ed25519 verification ---

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


_BY = 4 * _inv(5) % _P
_BX = _xrecover(_BY)
_B = (_BX, _BY)


def _edwards_add(P: tuple[int, int], Q: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _D * x1 * x2 * y1 * y2) % _P
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _D * x1 * x2 * y1 * y2) % _P
    return (x3, y3)


def _scalarmult(P: tuple[int, int], e: int) -> tuple[int, int]:
    if e == 0:
        return (0, 1)
    Q = _scalarmult(P, e // 2)
    Q = _edwards_add(Q, Q)
    if e & 1:
        Q = _edwards_add(Q, P)
    return Q


def _decodepoint(s: bytes) -> tuple[int, int]:
    y = sum(256**i * s[i] for i in range(32))
    clamp = y & ((1 << 255) - 1)
    x = _xrecover(clamp)
    if (x & 1) != (y >> 255):
        x = _P - x
    return (x, clamp)


def verify_ed25519(public_key_bytes: bytes, msg: bytes, sig_bytes: bytes) -> bool:
    """Verify Ed25519 signature per RFC 8032."""
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
        return sb == rak
    except Exception:
        return False


def verify_admission_signature(
    admission: dict[str, Any],
    trusted_pubkey_hex: str | None = None,
) -> bool:
    """Verify Ed25519 signature on AdmissionRecord over admission \\ {authenticator.signature}."""
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

    # Payload to sign is admission \ {"authenticator": {"signature": ...}}
    adm_copy = copy.deepcopy(admission)
    if "authenticator" in adm_copy and isinstance(adm_copy["authenticator"], dict):
        adm_copy["authenticator"].pop("signature", None)

    msg_bytes = jcs_bytes(adm_copy)
    return verify_ed25519(pub_bytes, msg_bytes, sig_bytes)
