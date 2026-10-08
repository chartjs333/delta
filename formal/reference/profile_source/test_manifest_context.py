"""Synthetic successor bytes and actual crypto; no legacy-object relabel/migration."""

import copy
import json
import struct
import unittest
from pathlib import Path

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import availability_ledger as ledger
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import manifest_context as m
from formal.reference.profile_source import test_configuration as config_fixture
from formal.reference.storage_source import test_codec as storage_fixture
from formal.scripts import native_source_artifacts as old

ROOT = Path(__file__).resolve().parents[3]


def synthetic_fixture(f, *, ticket_id=None):
    """Create new synthetic objects from the published arithmetic dimensions.

    Every changed preimage receives its new real hash. No original QC/signature,
    frozen fixture, semantics authority or production capture is repurposed.
    """
    golden = json.loads(
        (ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json").read_text()
    )
    schema = json.loads(
        (ROOT / "delta-protocol/fixtures/local-round/parameter-schema-v1.json").read_text()
    )
    originals = {}

    def put(kind, value):
        raw = old.canonical(value)
        identifier = old.content_id(raw, old.DOMAINS[kind])
        originals[identifier] = raw
        return identifier

    schema_id = put("schema", schema)
    body = f.body()
    body["parameter_schema_id"] = schema_id
    body["step_budget"] = golden["manifest"]["value"]["aggregation_steps"]
    body["domain_ticket_counts"] = [
        {"domain_id": golden["manifest"]["value"]["domain_id"], "ticket_count": 1}
    ]
    config_raw = cfg.encode(body)
    bound = cfg.bind(f.boot, f.storage_boot, config_raw, f.declaration)

    def context(kind):
        value = copy.deepcopy(golden[kind]["value"])
        value["formal_semantics_id"] = f.boot.formal_semantics_id
        return value

    profile_id = put("profile", context("profile"))
    scale = context("scale_table")
    scale.update(profile_id=profile_id, parameter_schema_id=schema_id)
    scale_id = put("scale", scale)
    plan = context("shard_plan")
    plan.update(profile_id=profile_id, parameter_schema_id=schema_id, scale_table_id=scale_id)
    plan_id = put("plan", plan)
    fixed = context("fixedpoint_config")
    fixed.update(
        profile_id=profile_id,
        parameter_schema_id=schema_id,
        scale_table_id=scale_id,
        shard_plan_id=plan_id,
        base_round_config_id=bound.body_id,
    )
    fixed_id = put("config", fixed)
    proof = context("proof_instance")
    proof.update(profile_id=profile_id, scale_table_id=scale_id, config_id=fixed_id)
    proof_id = put("proof", proof)
    manifest = context("manifest")
    if ticket_id is not None:
        manifest["ticket_id"] = ticket_id
    manifest.update(
        profile_id=profile_id,
        parameter_schema_id=schema_id,
        scale_table_id=scale_id,
        shard_plan_id=plan_id,
        round_config_id=fixed_id,
        proof_instance_id=proof_id,
        parent_checkpoint_id=bound.parent,
    )
    raws, refs = [], []
    for entry, original in zip(plan["entries"], golden["shards"], strict=True):
        original_raw = bytes.fromhex(original["envelope_hex"])
        payload = original_raw[-entry["payload_bytes"] :]
        header = {
            key: manifest[key]
            for key in (
                "formal_semantics_id",
                "parameter_schema_id",
                "profile_id",
                "proof_instance_id",
                "round_config_id",
                "scale_table_id",
                "shard_plan_id",
                "ticket_id",
            )
        }
        header.update({key: value for key, value in entry.items() if key != "payload_bytes"})
        header.update(
            schema_version="1.0.0",
            type_name="ENCODED_INT16_SHARD",
            payload_sha256=old.content_id(payload),
        )
        hb = old.canonical(header)
        raw = struct.pack("<4sHHII", b"DRQ1", 1, 0, len(hb), len(payload)) + hb + payload
        leaf = old.content_id(raw, old.DOMAINS["leaf"])
        refs.append({**entry, "leaf_id": leaf, "envelope_bytes": len(raw)})
        raws.append(raw)
    manifest.update(
        shards=refs,
        commitment_root=old.merkle_root([r["leaf_id"] for r in refs]),
        total_envelope_bytes=sum(len(raw) for raw in raws),
    )
    manifest_id = put("manifest", manifest)
    commitment = ledger.Commitment(manifest["ticket_id"], manifest["commitment_root"])
    return originals, manifest_id, config_raw, commitment, tuple(raws)


class ManifestContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_fixture.ConfigurationTests.setUpClass()
        cls.f = config_fixture.ConfigurationTests()

    def setUp(self):
        self.store, self.mid, self.config, self.commitment, self.raws = synthetic_fixture(self.f)

    def bind(self, **changes):
        return m.bind_context(
            self.f.boot,
            self.f.storage_boot,
            changes.get("config", self.config),
            self.f.declaration,
            changes.get("store", self.store),
            changes.get("mid", self.mid),
            changes.get("commitment", self.commitment),
        )

    def replace_manifest(self, value):
        raw = old.canonical(value)
        identifier = old.content_id(raw, old.DOMAINS["manifest"])
        return {**self.store, identifier: raw}, identifier

    def test_complete_original_context_without_any_q_bytes(self):
        metadata, context = self.bind()
        self.assertEqual(len(self.store), 7)
        self.assertTrue(all(raw not in self.store.values() for raw in self.raws))
        self.assertIs(metadata.original_manifest, self.store[self.mid])
        self.assertNotEqual(metadata.manifest_id, metadata.commitment_id)
        self.assertEqual(tuple(n for _, n in context.required_leaves), tuple(map(len, self.raws)))
        self.assertEqual(len(context.required_leaves), len(self.raws))
        common = m.storage.load(context.common_bytes)
        self.assertEqual(common["commitment_id"], self.commitment.commitment_id)
        self.assertEqual(common["round_config_id"], metadata.base_config_id)
        self.assertNotEqual(common["round_config_id"], metadata.fixed_config_id)
        self.assertEqual(len(metadata.original_sources), 7)

    def test_wrong_manifest_identity_or_commitment_cannot_be_substituted(self):
        with self.assertRaisesRegex(CodecError, "commitment root"):
            self.bind(commitment=ledger.Commitment(self.commitment.ticket_id, self.mid))
        with self.assertRaisesRegex(CodecError, "missing original"):
            self.bind(mid=self.commitment.commitment_id)
        altered = {**self.store, self.mid: self.store[self.mid] + b" "}
        with self.assertRaisesRegex(CodecError, "identity"):
            self.bind(store=altered)

    def test_changed_order_missing_leaf_or_context_rejects(self):
        manifest = m.decode(self.store[self.mid])
        for field, value in (
            ("parent_checkpoint_id", "sha256:" + "9" * 64),
            ("aggregation_steps", manifest["aggregation_steps"] + 1),
            ("shards", manifest["shards"][:-1]),
            ("shards", list(reversed(manifest["shards"]))),
        ):
            store, identifier = self.replace_manifest({**manifest, field: value})
            with self.subTest(field=field), self.assertRaises(CodecError):
                self.bind(store=store, mid=identifier)
        for identifier in tuple(self.store):
            with self.subTest(missing=identifier), self.assertRaises(CodecError):
                self.bind(store={k: v for k, v in self.store.items() if k != identifier})

    def test_exact_first_use_preserves_unsplit_originals_and_order(self):
        out = tuple(
            m.read_q(self.store, self.f.boot.formal_semantics_id, self.mid, i, raw)
            for i, raw in enumerate(self.raws)
        )
        self.assertEqual([len(x.values) for x in out], [4, 8, 8, 8, 8])
        self.assertEqual([x.ordinal for x in out], list(range(5)))
        self.assertTrue(
            all(x.original_envelope is raw for x, raw in zip(out, self.raws, strict=True))
        )
        for raw in (None, b"", self.raws[1], self.raws[0][:-1], self.raws[0] + b"\0"):
            with self.subTest(raw=type(raw)), self.assertRaises(CodecError):
                m.read_q(self.store, self.f.boot.formal_semantics_id, self.mid, 0, raw)

    def test_no_implicit_legacy_semantics_or_duplicate_members(self):
        with self.assertRaisesRegex(CodecError, "semantics"):
            m.resolve(self.store, old.SEMANTICS, self.mid)
        with self.assertRaises(CodecError):
            m.decode(b'{"a":1,"a":2}')

    def test_context_to_ac_to_frozen_inputs_preserves_all_original_identities(self):
        metadata, context = self.bind()
        st = storage_fixture.StorageSourceTests()
        st.common, st.value = m.storage.load(context.common_bytes), context
        ac, gs = st.witness(
            sorted((leaf, f"storage-{n}") for leaf, _ in context.required_leaves for n in (1, 2, 3))
        )
        state = ledger.empty((self.commitment.ticket_id,))
        state = ledger.record_commitment(
            state,
            ledger.Occurrence(0, "worker-1", b"synthetic-original-commitment-event"),
            self.commitment,
        ).state
        for i, raw in enumerate((b"invalid-unrelated-G", *gs, gs[0]), 1):
            state = ledger.deliver(state, ledger.Occurrence(i, "relay-1", raw))
        cut = len(state.events)
        result = ledger.record_source_availability(
            state,
            ledger.Occurrence(cut, "validator-1", ac),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            self.config,
            self.f.declaration,
            self.store,
            self.mid,
        )
        self.assertEqual(result.disposition, "recorded")
        accepted = result.state.availabilities[0]
        self.assertIs(accepted.occurrence.original, ac)
        self.assertEqual(
            accepted.bound.witness.original_inventory, tuple(e.original for e in state.deliveries)
        )
        frozen = ledger.freeze(result.state, ledger.Occurrence(cut + 1, "validator-1", b"freeze"))
        tuples = ledger.original_tuples(frozen.state, {metadata.ticket_id: metadata.domain_id})
        self.assertEqual(len(tuples), 1)  # One original vector ticket, never five shard tickets.
        self.assertEqual(tuples[0].commitment_id, self.commitment.commitment_id)
        self.assertEqual(
            tuples[0].availability_certificate_id,
            m.storage.content_id(m.storage.CERTIFICATE_DOMAIN, ac),
        )
        bad = ledger.record_source_availability(
            state,
            ledger.Occurrence(cut, "validator-1", ac),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            self.config,
            self.f.declaration,
            {},
            self.mid,
        )
        self.assertEqual(bad.disposition, "rejected_original_manifest")
        self.assertEqual(bad.state.availabilities, ())
        self.assertEqual(bad.state.events[-1].original, ac)


if __name__ == "__main__":
    unittest.main()
