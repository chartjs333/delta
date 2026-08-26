from __future__ import annotations

import hashlib
import json
import locale
import struct
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from deltatorrent.domain.formal_compat import FORMAL_SEMANTICS_ID, load_formal_compatibility
from deltatorrent.protocol import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "delta-protocol"


def load(path: str) -> dict[str, object]:
    value = json.loads((PROTOCOL / path).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_canonical_json_exact_bytes_and_hash() -> None:
    vector = load("fixtures/canonical-json/canonical-json-v1.json")
    value = dict(vector["input_pairs"])  # type: ignore[arg-type]
    encoded = canonical_json_bytes(value)
    assert encoded.decode("utf-8") == vector["expected_utf8"]
    assert encoded.hex() == vector["expected_hex"]
    assert hashlib.sha256(encoded).hexdigest() == vector["expected_sha256"]
    assert sha256_content_id(encoded) == f"sha256:{vector['expected_sha256']}"


def test_safe_tensor_vector_is_bounded_and_self_consistent() -> None:
    vector = load("fixtures/safe-tensor/safe-tensor-i32-v1.json")
    encoded = bytes.fromhex(str(vector["encoded_hex"]))
    assert len(encoded) == vector["byte_length"]
    assert hashlib.sha256(encoded).hexdigest() == vector["sha256"]
    header_length = struct.unpack("<Q", encoded[:8])[0]
    header = encoded[8 : 8 + header_length]
    assert header.rstrip(b" ").decode("utf-8") == vector["header_utf8"]
    assert len(header) - len(header.rstrip(b" ")) == vector["header_padding_bytes"]
    assert struct.unpack("<ii", encoded[8 + header_length :]) == (1, -2)
    assert not encoded.startswith(b"\x80")


def test_formal_projection_registry_is_bound_to_feature_zero() -> None:
    path = PROTOCOL / "action-registry" / "formal-projection-v1.json"
    compatibility = load_formal_compatibility(path)
    formal_schema = json.loads(
        (ROOT / "formal" / "schemas" / "formal-trace.schema.json").read_text(encoding="utf-8")
    )
    event_properties = formal_schema["$defs"]["event"]["properties"]
    assert compatibility.formal_semantics_id == FORMAL_SEMANTICS_ID
    assert compatibility.action_ids <= set(event_properties["action_id"]["enum"])
    assert compatibility.outcomes <= set(event_properties["outcome"]["enum"])


def test_projection_fixture_uses_registered_values() -> None:
    vector = load("fixtures/formal/artifact-projection-v1.json")
    compatibility = load_formal_compatibility(
        PROTOCOL / "action-registry" / "formal-projection-v1.json"
    )
    assert vector["formal_semantics_id"] == FORMAL_SEMANTICS_ID
    for case in vector["cases"]:  # type: ignore[union-attr]
        assert case["action_id"] in compatibility.action_ids
        assert case["outcome"] in compatibility.outcomes
        assert case["error_code"] is None or case["error_code"] in compatibility.error_codes


def test_map_order_and_locale_cannot_change_protocol_bytes() -> None:
    left = {"z": 2, "a": 1}
    right = {"a": 1, "z": 2}
    expected = b'{"a":1,"z":2}'
    with patch.object(locale, "localeconv", return_value={"decimal_point": ","}):
        assert canonical_json_bytes(left) == expected
        assert canonical_json_bytes(right) == expected


@dataclass
class InMemoryLayout:
    value: int


@pytest.mark.parametrize("unsafe", [b"pickle-like", bytearray(b"mutable"), InMemoryLayout(1)])
def test_memory_layout_and_pickle_bytes_are_not_json_values(unsafe: object) -> None:
    with pytest.raises(TypeError, match="UNSAFE_SERIALIZATION_TYPE"):
        canonical_json_bytes(unsafe)


@pytest.mark.parametrize("number", [0.0, float("nan"), float("inf")])
def test_floating_values_are_not_canonical_protocol_numbers(number: float) -> None:
    with pytest.raises(TypeError, match="FLOAT_NOT_CANONICAL"):
        canonical_json_bytes({"value": number})
