"""REFERENCE_ONLY_NOT_PRODUCTION: pinned pure Ed25519 conformance adapter.

Inputs are public synthetic test material. This is neither a key custodian nor
an ISC admission verifier: registry, source lineage and consensus are separate.
"""

import ctypes
import hashlib
import re
from pathlib import Path

SCALAR_ORDER = 2**252 + 27742317777372353535851937790883648493
MAX_MESSAGE_BYTES = 4282


def _buffer(data: bytes) -> ctypes.Array[ctypes.c_char]:
    return ctypes.create_string_buffer(data, max(1, len(data)))


class SodiumReference:
    """Load an authenticated cached DLL using its exact recorded SHA-256 pin."""

    def __init__(self, path: str | Path, expected_sha256: str) -> None:
        candidate = Path(path)
        if not candidate.is_absolute():
            raise RuntimeError("An explicit absolute library path is required")
        if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
            raise RuntimeError("An exact SHA-256 library pin is required")
        try:
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError as exc:
            raise RuntimeError("Pinned reference library unavailable") from exc
        if digest != expected_sha256:
            raise RuntimeError("Reference library SHA-256 mismatch")
        try:
            lib = ctypes.CDLL(str(candidate.resolve(strict=True)))
            lib.sodium_version_string.argtypes = []
            lib.sodium_version_string.restype = ctypes.c_char_p
            lib.sodium_init.argtypes = []
            lib.sodium_init.restype = ctypes.c_int
            lib.crypto_core_ed25519_is_valid_point.argtypes = [ctypes.c_void_p]
            lib.crypto_core_ed25519_is_valid_point.restype = ctypes.c_int
            lib.crypto_sign_seed_keypair.argtypes = [ctypes.c_void_p] * 3
            lib.crypto_sign_seed_keypair.restype = ctypes.c_int
            lib.crypto_sign_detached.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_ulonglong),
                ctypes.c_void_p,
                ctypes.c_ulonglong,
                ctypes.c_void_p,
            ]
            lib.crypto_sign_detached.restype = ctypes.c_int
            lib.crypto_sign_verify_detached.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_ulonglong,
                ctypes.c_void_p,
            ]
            lib.crypto_sign_verify_detached.restype = ctypes.c_int
            lib.sodium_memzero.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
            lib.sodium_memzero.restype = None
        except (OSError, AttributeError) as exc:
            raise RuntimeError("Required reference library/API unavailable") from exc
        if lib.sodium_version_string() != b"1.0.22":
            raise RuntimeError("Only the pinned libsodium1.0.22 profile is supported")
        if lib.sodium_init() < 0:
            raise RuntimeError("libsodium initialization failed")
        self._lib = lib

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Strict A/Rpoint/S checks precede detached verification; no fallback."""
        if not all(isinstance(x, bytes) for x in (public_key, message, signature)):
            return False
        if len(public_key) != 32 or len(signature) != 64:
            return False
        if len(message) > MAX_MESSAGE_BYTES:
            return False
        if int.from_bytes(signature[32:], "little") >= SCALAR_ORDER:
            return False
        key, sig, msg = _buffer(public_key), _buffer(signature), _buffer(message)
        if self._lib.crypto_core_ed25519_is_valid_point(key) != 1:
            return False
        if self._lib.crypto_core_ed25519_is_valid_point(_buffer(signature[:32])) != 1:
            return False
        return bool(self._lib.crypto_sign_verify_detached(sig, msg, len(message), key) == 0)

    def sign(self, seed: bytes, message: bytes) -> tuple[bytes, bytes]:
        """Deterministic signing of public test seeds only; no persistent keys."""
        if not isinstance(seed, bytes) or len(seed) != 32:
            raise ValueError("Public synthetic seed must contain exactly 32 bytes")
        if not isinstance(message, bytes) or len(message) > MAX_MESSAGE_BYTES:
            raise ValueError("Reference message exceeds selected profile limit")
        public = ctypes.create_string_buffer(32)
        secret = ctypes.create_string_buffer(64)
        signature = ctypes.create_string_buffer(64)
        seed_buffer = _buffer(seed)
        length = ctypes.c_ulonglong()
        try:
            if self._lib.crypto_sign_seed_keypair(public, secret, seed_buffer) != 0:
                raise RuntimeError("Reference keypair derivation failed")
            if (
                self._lib.crypto_sign_detached(
                    signature, ctypes.byref(length), _buffer(message), len(message), secret
                )
                != 0
                or length.value != 64
            ):
                raise RuntimeError("Reference detached signing failed")
            return public.raw, signature.raw
        finally:
            self._lib.sodium_memzero(secret, 64)
            self._lib.sodium_memzero(seed_buffer, 32)
