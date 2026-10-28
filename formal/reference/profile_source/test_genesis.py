"""Synthetic metadata/value examples; never a complete lawful imported snapshot."""

import copy
import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import configuration_units as cu
from formal.reference.profile_source import genesis as g
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import test_authority as af
from formal.reference.profile_source.test_arithmetic_units import numeric
from formal.reference.profile_source.test_metadata import Package, frame, identifier, ref
from formal.reference.storage_source.codec import canonical


def document():
    p = Package()
    return dict(
        formal_semantics_id=p.boot["formal_semantics_id"],
        height="0",
        model_values=[str(g.I64_MIN), "0", str(g.I64_MAX), "-19"],
        optimizer_values=["2", "-2", "0", "7"],
        origin_id=p.boot["origin_id"],
        schema_version="1.0.0",
        type_name="PROFILE_GENESIS_VALUES",
        validator_epoch_id=p.boot["validator_epoch_id"],
    )


def package():
    p = Package()
    raw = canonical(document())
    initial = m.canonical(
        {
            "arithmetic_units": {
                "type_name": "INITIAL_ARITHMETIC_UNITS",
                "schema_version": "1.0.0",
                "parameter_schema_id": identifier("original schema"),
                "quantum": {"numerator": "3", "denominator": "7"},
            },
            "other_original_initial_fields": "retained; validated by their own existing handlers",
        }
    )
    # Earlier unrelated event inputs stay original, even after selecting the
    # independently pinned genesis/initial configuration in this fixture.
    originals = [*p.raw, raw, initial]
    p.artifacts = tuple(sorted((m.raw_id(x), x) for x in originals))
    table = sorted(map(ref, originals), key=lambda r: r["content_id"])
    p.boot.update(genesis_ref=ref(raw), initial_config_ref=ref(initial))
    p.boot_raw = m.canonical(p.boot)
    bid = m.document_id(p.boot_raw, "BOOTSTRAP")
    p.index.update(genesis_ref=ref(raw), artifacts=table)
    p.index_raw = m.canonical(p.index)
    p.record["bootstrap_id"] = bid
    p.trust = replace(
        p.trust,
        bootstrap=p.boot_raw,
        bootstrap_raw_sha256=m.raw_id(p.boot_raw),
        source_index_raw_sha256=m.raw_id(p.index_raw),
        trusted_log=frame(p.record),
    )
    p.manifest.update(bootstrap_id=bid, artifacts=table, source_index_ref=ref(p.index_raw))
    return p, initial


def configuration_package(change=None):
    """Explicit synthetic reprovisioning, never a claimed lawful import."""
    af.AuthorityTests.setUpClass()
    fixture = af.AuthorityTests()
    fixture.setUp()
    p = fixture.package
    doc = document()
    for name in ("formal_semantics_id", "origin_id", "validator_epoch_id"):
        doc[name] = p.boot[name]
    genesis = canonical(doc)
    image = g.decode(
        genesis, doc["formal_semantics_id"], doc["origin_id"], doc["validator_epoch_id"]
    )
    u = m.load(package()[1])["arithmetic_units"]
    initial = canonical({**m.load(fixture.initial), "arithmetic_units": u})
    body = fixture.fixture.body()
    body.update(
        schema_version="3.0.0",
        parent_checkpoint_id=image.checkpoint_id,
        parameter_schema_id=u["parameter_schema_id"],
        apply_arithmetic_profile_source=cu.units.canonical(numeric("3", 7)).decode(),
    )
    if change:
        change(body)
    config = cu.encode(body)
    declaration = fixture.fixture.declaration
    originals = {*(raw for _, raw in p.artifacts), genesis, initial, config, declaration}
    p.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in originals))
    table = [ref(raw) for _, raw in p.artifacts]
    p.boot.update(genesis_ref=ref(genesis), initial_config_ref=ref(initial))
    p.boot_raw = m.canonical(p.boot)
    bid = m.document_id(p.boot_raw, "BOOTSTRAP")
    p.index.update(genesis_ref=ref(genesis), artifacts=table)
    p.index_raw = m.canonical(p.index)
    p.record["bootstrap_id"] = bid
    p.trust = replace(
        p.trust,
        bootstrap=p.boot_raw,
        bootstrap_raw_sha256=m.raw_id(p.boot_raw),
        source_index_raw_sha256=m.raw_id(p.index_raw),
        trusted_log=frame(p.record),
    )
    p.manifest.update(bootstrap_id=bid, artifacts=table, source_index_ref=ref(p.index_raw))
    return fixture, p, config, declaration


def bind_configuration_package(parts):
    fixture, p, config, declaration = parts
    return g.bind_configuration(
        p.trust,
        m.canonical(p.manifest),
        p.index_raw,
        p.artifacts,
        fixture.keys,
        fixture.registry,
        fixture.storage_keys,
        config,
        declaration,
    )


class GenesisTests(unittest.TestCase):
    def test_one_raw_origin_for_enrollment_values_units_and_whole_configuration(self):
        parts = configuration_package()
        result = bind_configuration_package(parts)
        self.assertEqual(result.configuration.original, parts[2])
        self.assertEqual(result.original_declaration, parts[3])
        self.assertEqual(result.origin.initial_configuration, result.authorities.initial_config)
        self.assertEqual(result.configuration.parent, result.origin.genesis.checkpoint_id)
        self.assertEqual(result.origin.genesis.apply_qc_id, "")
        self.assertEqual(
            result.origin.source.events,
            g.bind(
                parts[1].trust,
                m.canonical(parts[1].manifest),
                parts[1].index_raw,
                parts[1].artifacts,
            ).source.events,
        )

    def test_rehashed_config_cannot_override_original_parent_schema_height_or_units(self):
        for change in (
            lambda b: b.update(parent_checkpoint_id=identifier("wrong original parent")),
            lambda b: b.update(height="0"),
            lambda b: b.update(parameter_schema_id=identifier("wrong original schema")),
            lambda b: b.update(
                apply_arithmetic_profile_source=cu.units.canonical(numeric("1", 7)).decode()
            ),
            lambda b: b.update(validator_epoch_id=identifier("wrong original epoch")),
        ):
            parts = configuration_package(change)
            with self.subTest(change=change), self.assertRaises(CodecError):
                bind_configuration_package(parts)

    def test_original_keys_and_source_cannot_be_replaced_by_bound_caches(self):
        fixture, p, raw, declaration = configuration_package()
        args = (
            m.canonical(p.manifest),
            p.index_raw,
            p.artifacts,
            fixture.keys,
            fixture.registry,
            fixture.storage_keys,
            raw,
            declaration,
        )
        with self.assertRaisesRegex(CodecError, "independent primitive"):
            g.bind_configuration(p.check(), *args)
        with self.assertRaises(CodecError):
            g.bind_configuration(p.trust, *args[:3], fixture.keys[:-1], *args[4:])

    def decode(self, doc):
        base = document()
        return g.decode(
            canonical(doc),
            base["formal_semantics_id"],
            base["origin_id"],
            base["validator_epoch_id"],
        )

    def test_exact_native_values_preimages_and_no_fabricated_qc(self):
        row = document()
        result = self.decode(row)
        self.assertEqual(result.model, (g.I64_MIN, 0, g.I64_MAX, -19))
        self.assertEqual(
            result.model_preimage,
            b"deltareduce.008.model.v1\0"
            + b"".join(x.encode() + b";" for x in row["model_values"]),
        )
        self.assertEqual(result.checkpoint_id, m.raw_id(result.model_preimage))
        self.assertEqual(result.optimizer_id, m.raw_id(result.optimizer_preimage))
        self.assertEqual(result.apply_qc_id, "")
        row["height"] = str(2**64 - 1)
        self.assertEqual(self.decode(row).height, 2**64 - 1)

    def test_no_extra_control_cap_or_zero_initialization(self):
        row = document()
        row["model_values"] = [str(g.I64_MIN)] * g.MAX_VALUES
        row["optimizer_values"] = [str(g.I64_MAX)] * g.MAX_VALUES
        raw = canonical(row)
        self.assertGreater(len(raw), m.MAX_CONTROL)
        image = self.decode(row)
        self.assertEqual(len(image.model), g.MAX_VALUES)
        self.assertEqual(image.optimizer[-1], g.I64_MAX)

    def test_unknown_duplicate_noncanonical_context_and_numeric_rejected(self):
        base = document()
        for name, bad in (
            ("height", str(2**64)),
            ("height", "00"),
            ("model_values", []),
            ("model_values", ["1"]),
            ("origin_id", identifier("different")),
            ("type_name", "IMPORT_CURRENT"),
            ("unknown", "extra"),
        ):
            row = copy.deepcopy(base)
            row[name] = bad
            with self.assertRaises(CodecError):
                self.decode(row)
        for value in ("-0", "+1", "01", str(g.I64_MIN - 1), str(g.I64_MAX + 1)):
            row = copy.deepcopy(base)
            row["model_values"][0] = value
            with self.assertRaises(CodecError):
                self.decode(row)
        for raw in (
            canonical(base) + b"\n",
            b'{"height":"1",' + canonical(base)[1:],
            canonical(base).replace(b'"height":"0"', b'"height":0'),
        ):
            with self.assertRaises(CodecError):
                g.decode(
                    raw, base["formal_semantics_id"], base["origin_id"], base["validator_epoch_id"]
                )

    def test_independent_raw_genesis_configuration_and_units_jointly_bound(self):
        p, initial = package()
        origin = g.bind(p.trust, m.canonical(p.manifest), p.index_raw, p.artifacts)
        self.assertEqual(origin.initial_configuration, initial)
        self.assertEqual(origin.quantum.numerator, 3)
        self.assertEqual(origin.quantum.denominator, 7)
        self.assertEqual(origin.source.events[0].original, b"delivery")
        self.assertEqual(origin.source.events[1].original, b"delivery")
        self.assertEqual(origin.source.metadata.floor, p.anchor)
        self.assertNotEqual(origin.genesis.apply_qc_id, p.anchor["apply_qc_id"])
        # Keep all hashes/pins fixed: imported content cannot select new units.
        bad = tuple(
            (key, raw.replace(b'"numerator":"3"', b'"numerator":"4"')) for key, raw in p.artifacts
        )
        with self.assertRaises(CodecError):
            g.bind(p.trust, m.canonical(p.manifest), p.index_raw, bad)
        with self.assertRaises(CodecError):
            g.bind(origin.source.metadata, m.canonical(p.manifest), p.index_raw, p.artifacts)


if __name__ == "__main__":
    unittest.main()
