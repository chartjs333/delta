"""REFERENCE_ONLY_NOT_PRODUCTION: capability probe, never a signature verifier."""

import ctypes.util
import importlib.util
import json
import platform

import cryptography
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def probe() -> dict[str, object]:
    # Entirely public invalid-key witness. No signing, private key, or randomness.
    identity_key = b"\x01" + bytes(31)
    basepoint = bytes.fromhex("58" + "66" * 31)
    signature = basepoint + (1).to_bytes(32, "little")
    try:
        Ed25519PublicKey.from_public_bytes(identity_key).verify(
            signature, b"ISC-S16 public negative probe"
        )
        result = "ACCEPTED_IDENTITY_KEY"
    except (InvalidSignature, ValueError):
        result = "REJECTED_IDENTITY_KEY"
    return {
        "scope": "REFERENCE_ONLY_NOT_PRODUCTION",
        "python": platform.python_version(),
        "cryptography_version": cryptography.__version__,
        "openssl_version": backend.openssl_version_text(),
        "nacl_available": importlib.util.find_spec("nacl") is not None,
        "ctypes_sodium": ctypes.util.find_library("sodium"),
        "ctypes_libsodium": ctypes.util.find_library("libsodium"),
        "identity_key_hex": identity_key.hex(),
        "signature_hex": signature.hex(),
        "message_ascii": "ISC-S16 public negative probe",
        "expected_strict_profile_result": "REJECTED_IDENTITY_KEY",
        "observed_result": result,
        "strict_profile_qualified": False,
        "secrets_used": False,
        "signing_performed": False,
        "qualification_note": (
            "Even rejection of this one probe would not qualify all point/subgroup checks. "
            "No replacement for the selected library is implemented."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
