"""Approved exact-byte binding, including hostile original wire representations."""

import copy
import json
import unittest
from hashlib import sha256
from pathlib import Path

from jsonschema import Draft202012Validator

from formal.reference.isc_crypto.codec import CodecError, content_id
from formal.reference.storage_source import test_codec
from formal.reference.storage_source.codec import canonical, load
from formal.reference.storage_source.retention import (
    CONTRACT,
    DOMAIN,
    authenticate_bound_witness,
    bind_policy,
    decode_source,
    resolve,
)


def source(declaration, epoch="retention-1"):
    return {
        "obligation_ref": {
            "byte_length": str(len(declaration)),
            "sha256": sha256(declaration).hexdigest(),
        },
        "retention_epoch_id": epoch,
        "schema_version": "1.0.0",
        "type_name": "STORAGE_RETENTION_POLICY_SOURCE",
    }


class RetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse public synthetic storage keys and actual strict crypto, not a mock.
        test_codec.StorageSourceTests.setUpClass()
        cls.storage = test_codec.StorageSourceTests()
        cls.schema = json.loads(
            Path(__file__).with_name("retention-source.schema.json").read_text()
        )
        Draft202012Validator.check_schema(cls.schema)

    def binding(self, declaration=b"original policy\r\n"):
        return canonical(
            {
                "retention_epoch_id": "retention-1",
                "retention_policy_source": source(declaration),
                "storage_epoch_id": self.storage.common["storage_epoch_id"],
                "storage_registry_id": self.storage.common["storage_registry_id"],
                "threshold": "3",
            }
        )

    def test_shared_lean_python_byte_vectors(self):
        vectors = json.loads(
            Path(__file__).with_name("retention-vectors.json").read_text(encoding="utf-8")
        )["vectors"]
        for row in vectors:
            e = bytes.fromhex(row["declaration_hex"])
            raw = row["source_ascii"].encode("ascii")
            result = resolve(CONTRACT, raw, e, row["epoch"])
            self.assertEqual(result.source_id, row["source_id"])
            self.assertEqual(result.declaration_sha256, row["digest"])
            self.assertEqual(decode_source(raw)["obligation_ref"]["byte_length"], row["length"])

    def test_exact_raw_binary_declaration_and_separate_id(self):
        for declaration in (b"original policy\r\n", b"\x00\xff\xef\xbb\xbf\n", b"x"):
            raw = canonical(source(declaration))
            Draft202012Validator(self.schema).validate(load(raw))
            result = resolve(CONTRACT, raw, declaration, "retention-1")
            self.assertEqual(result.original_source, raw)
            self.assertIs(result.original_declaration, declaration)
            self.assertEqual(result.source_id, content_id(DOMAIN, raw))
            self.assertNotEqual(result.source_id, "sha256:" + sha256(declaration).hexdigest())
            with self.assertRaises(CodecError):
                resolve(CONTRACT, raw, declaration.decode("latin1"), "retention-1")

    def test_no_label_only_fallback_and_no_normalization(self):
        a, b = b"original policy\r\n", b"original policy\n"
        ra, rb = canonical(source(a)), canonical(source(b))
        self.assertNotEqual(content_id(DOMAIN, ra), content_id(DOMAIN, rb))
        for altered in (b, b"", a + b"\0", b"X" + a[1:]):
            with self.assertRaises(CodecError):
                resolve(CONTRACT, ra, altered, "retention-1")
        with self.assertRaises(CodecError):
            resolve(CONTRACT, ra, a, "later")
        with self.assertRaises(CodecError):
            resolve("snapshot-selected-codec", ra, a, "retention-1")

    def test_strict_wire_before_schema_and_typed_value(self):
        raw = canonical(source(b"x"))
        bad = [
            b'{"retention_epoch_id":"old",' + raw[1:],
            raw.replace(b'"byte_length":"1"', b'"byte_length":"1","byte_length":"1"'),
            raw.replace(b'"byte_length":"1"', b'"byte_length":1'),
            raw.replace(b'"byte_length":"1"', b'"byte_length":true'),
            raw.replace(b'"obligation_ref":', b'"obligation\\u005fref":'),
            raw + b"\n",
            b"\xef\xbb\xbf" + raw,
            json.dumps(load(raw), indent=2).encode(),
        ]
        for value in bad:
            with self.subTest(value=value[:40]), self.assertRaises(CodecError):
                decode_source(value)
        unknown = load(raw)
        unknown["policy_valid"] = True
        with self.assertRaises(CodecError):
            decode_source(canonical(unknown))
        missing = load(raw)
        del missing["obligation_ref"]
        with self.assertRaises(CodecError):
            decode_source(canonical(missing))

    def test_exact_u64_bound_not_python_integer_or_schema_approximation(self):
        for length in ("1", "9", "18446744073709551615"):
            obj = source(b"x")
            obj["obligation_ref"]["byte_length"] = length
            decode_source(canonical(obj))
            Draft202012Validator(self.schema).validate(obj)
        for length in ("0", "01", "+1", "-1", "1e1", "18446744073709551616", "9" * 21):
            obj = source(b"x")
            obj["obligation_ref"]["byte_length"] = length
            self.assertFalse(Draft202012Validator(self.schema).is_valid(obj))
            with self.assertRaises(CodecError):
                decode_source(canonical(obj))
        # A representable large declared length is not a supplied artifact.
        obj = source(b"x")
        obj["obligation_ref"]["byte_length"] = "18446744073709551615"
        with self.assertRaises(CodecError):
            resolve(CONTRACT, canonical(obj), b"x", "retention-1")

    def test_digest_and_closed_source_shape(self):
        base = source(b"x")
        for digest in ("A" * 64, "g" * 64, "0" * 63, "sha256:" + "0" * 64, True):
            obj = copy.deepcopy(base)
            obj["obligation_ref"]["sha256"] = digest
            self.assertFalse(Draft202012Validator(self.schema).is_valid(obj))
            with self.assertRaises(CodecError):
                decode_source(canonical(obj))
        obj = copy.deepcopy(base)
        obj["obligation_ref"]["uri"] = "later-local-policy"
        with self.assertRaises(CodecError):
            decode_source(canonical(obj))

    def test_mandatory_future_binding_and_existing_storage_authority(self):
        raw = self.binding()
        result = bind_policy(CONTRACT, self.storage.bootstrap, raw, b"original policy\r\n")
        self.assertEqual(result.original_binding, raw)
        binding_schema = dict(self.schema, **{"$ref": "#/$defs/storage_binding"})
        # The top-level schema is R; use only shared definitions for binding dispatch.
        binding_schema = {k: binding_schema[k] for k in ("$schema", "$defs", "$ref")}
        Draft202012Validator(binding_schema).validate(load(raw))
        changes = [
            ("storage_epoch_id", "other"),
            ("storage_registry_id", "sha256:" + "0" * 64),
            ("retention_epoch_id", "other"),
            ("threshold", "0"),
            ("threshold", "5"),
            ("threshold", str(2**32)),
        ]
        for key, value in changes:
            obj = load(raw)
            obj[key] = value
            with self.assertRaises(CodecError):
                bind_policy(
                    CONTRACT, self.storage.bootstrap, canonical(obj), b"original policy\r\n"
                )
        obj = load(raw)
        del obj["retention_policy_source"]
        with self.assertRaises(CodecError):
            bind_policy(CONTRACT, self.storage.bootstrap, canonical(obj), b"original policy\r\n")

    def test_bound_crypto_witness_preserves_original_objects_and_occurrences(self):
        d, inventory = self.storage.witness()
        retained = (*inventory, inventory[0], b"original invalid delivery")
        result = authenticate_bound_witness(
            CONTRACT,
            self.storage.bootstrap,
            self.storage.backend,
            self.storage.value,
            self.binding(),
            b"original policy\r\n",
            d,
            retained,
        )
        self.assertEqual(result.witness.original_inventory, retained)
        self.assertEqual(result.witness.original_certificate, d)
        self.assertEqual(result.binding.source.original_declaration, b"original policy\r\n")
        # Loss affects later data use, not the identity of the certificate/statement.
        self.assertFalse(hasattr(result, "physically_available"))
        self.assertFalse(hasattr(result, "configuration_finalized"))
        obj = load(self.binding())
        obj["retention_policy_source"] = source(b"another policy", "other")
        obj["retention_epoch_id"] = "other"
        with self.assertRaisesRegex(CodecError, "policy/statement"):
            authenticate_bound_witness(
                CONTRACT,
                self.storage.bootstrap,
                self.storage.backend,
                self.storage.value,
                canonical(obj),
                b"another policy",
                d,
                retained,
            )


if __name__ == "__main__":
    unittest.main()
