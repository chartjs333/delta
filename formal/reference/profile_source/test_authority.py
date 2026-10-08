"""Independent enrollment resolves original objects; synthetic package, not a valid history."""

import copy
import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as crypto
from formal.reference.profile_source import authority as a
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import test_configuration as fixtures
from formal.reference.profile_source.test_metadata import Package, frame, ref
from formal.reference.storage_source import codec as storage


class AuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ConfigurationTests.setUpClass()
        cls.fixture = fixtures.ConfigurationTests()

    def setUp(self):
        f = self.fixture
        p = Package()
        self.keys = tuple(crypto.encode_key(key) for _, key in f.boot.validators)
        self.storage_keys = tuple(crypto.encode_key(key) for _, key in f.storage_boot.storage_keys)
        self.registry = storage.registry(f.storage_boot)[0]
        self.initial = storage.canonical(
            {
                "storage_authority": {
                    "storage_epoch_id": f.storage_boot.storage_epoch_id,
                    "storage_registry_id": storage.content_id(
                        storage.REGISTRY_DOMAIN, self.registry
                    ),
                },
                "other_original_initial_fields": ["retained-not-qualified-as-genesis"],
            }
        )
        context = {
            "origin_id": f.boot.origin_id,
            "validator_epoch_id": f.boot.validator_epoch_id,
            "local_validator_id": f.boot.validators[0][0],
        }
        p.boot.update(context)
        p.boot["formal_semantics_id"] = f.boot.formal_semantics_id
        p.boot["initial_config_ref"] = ref(self.initial)
        p.boot["validators"] = [
            {
                "validator_id": name,
                "key_ref": crypto.content_id(crypto.KEY_DOMAIN, raw),
                "roles": ["validator"],
            }
            for (name, _), raw in zip(f.boot.validators, self.keys, strict=True)
        ]
        p.boot_raw = m.canonical(p.boot)
        raws = set(
            p.raw + list(self.keys) + list(self.storage_keys) + [self.registry, self.initial]
        )
        p.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in raws))
        p.table = sorted((ref(raw) for raw in raws), key=lambda v: v["content_id"])
        # Metadata is deliberately synthetic but the independent trust side is
        # explicitly re-provisioned by this fixture, never taken from the import.
        for row in p.journals:
            row["actor_id"] = context["local_validator_id"]
        p.index.update(context)
        p.index["artifacts"] = p.table
        p.index_raw = m.canonical(p.index)
        boot_id = m.document_id(p.boot_raw, "BOOTSTRAP")
        p.record["bootstrap_id"] = boot_id
        p.trust = m.PrimitiveTrust(
            m.raw_id(p.boot_raw),
            m.raw_id(p.index_raw),
            tuple(sorted((key, p.boot[key]) for key in m.PINS)),
            p.boot_raw,
            frame(p.record),
            ((context["local_validator_id"], "consensus", b"journal"),),
        )
        p.manifest.update(context)
        p.manifest.update(
            bootstrap_id=boot_id,
            formal_semantics_id=f.boot.formal_semantics_id,
            artifacts=p.table,
            source_index_ref=ref(p.index_raw),
        )
        p.manifest["journals"][0]["actor_id"] = context["local_validator_id"]
        self.package = p

    def test_original_bootstrap_and_initial_configuration_select_keys(self):
        meta = self.package.check()
        result = a.resolve(meta, self.keys, self.registry, self.storage_keys)
        self.assertEqual(result.validators, self.fixture.boot)
        self.assertEqual(result.storage, self.fixture.storage_boot)
        self.assertEqual(result.initial_config, self.initial)
        self.assertEqual(result.original_validator_keys, self.keys)

    def test_imported_registry_cannot_elect_itself(self):
        meta = self.package.check()
        doc = storage.load(self.registry)
        doc["storage_epoch_id"] = "other"
        altered = storage.canonical(doc)
        meta = replace(
            meta, original_artifacts=(*meta.original_artifacts, (m.raw_id(altered), altered))
        )
        with self.assertRaisesRegex(crypto.CodecError, "self-election"):
            a.resolve(meta, self.keys, altered, self.storage_keys)
        with self.assertRaises(crypto.CodecError):
            a.resolve(self.package.check(), self.keys[:-1], self.registry, self.storage_keys)

    def test_profile_shape_schema_matches_all_control_documents(self):
        import json
        from pathlib import Path

        import jsonschema

        schema = json.loads(
            (
                Path(__file__).parents[2] / "proposals/b-family-transfer/profile-v1.schema.json"
            ).read_text()
        )
        validator = jsonschema.Draft202012Validator(schema)
        validator.check_schema(schema)
        p = self.package
        for doc in (p.boot, p.index, p.manifest, p.record):
            validator.validate(doc)
            changed = copy.deepcopy(doc)
            changed["unexpected"] = "silently-ignored"
            self.assertFalse(validator.is_valid(changed))


if __name__ == "__main__":
    unittest.main()
