"""Original preimage preservation, fail-closed decoding and explicit trust gaps."""

import copy
import hashlib
import json
import struct
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_source_artifacts as generator  # noqa: E402
import native_source_artifacts as source  # noqa: E402


class NativeSourceArtifactTests(unittest.TestCase):
    def setUp(self):
        self.store, self.golden, self.other = generator.fixture_store()
        self.manifest_id = self.golden["manifest"]["content_id"]

    def new_manifest(self, value):
        raw = source.canonical(value)
        identifier = source.content_id(raw, source.DOMAINS["manifest"])
        self.store[identifier] = raw
        return identifier

    def replace_leaf(self, raw):
        m = copy.deepcopy(self.golden["manifest"]["value"])
        identifier = source.content_id(raw, source.DOMAINS["leaf"])
        self.store[identifier] = raw
        m["shards"][0]["leaf_id"] = identifier
        m["total_envelope_bytes"] += len(raw) - m["shards"][0]["envelope_bytes"]
        m["shards"][0]["envelope_bytes"] = len(raw)
        m["commitment_root"] = source.merkle_root([r["leaf_id"] for r in m["shards"]])
        return self.new_manifest(m)

    def envelope(self, header=None, payload=None):
        row = self.golden["shards"][0]
        header = copy.deepcopy(row["header"] if header is None else header)
        payload = bytes.fromhex(row["payload_hex"]) if payload is None else payload
        header["payload_sha256"] = source.content_id(payload)
        encoded = source.canonical(header)
        return struct.pack("<4sHHII", b"DRQ1", 1, 0, len(encoded), len(payload)) + encoded + payload

    def test_source_copies_are_exact_pinned_git_blobs(self):
        boundary = json.loads((generator.EVIDENCE / "native-source-boundary.json").read_bytes())
        for row in boundary["files"]:
            raw = subprocess.check_output(
                ["git", "show", boundary["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(raw, (generator.EVIDENCE / row["copy"]).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_exact_regeneration_and_all_original_coordinates(self):
        generated = generator.generate()
        retained = json.loads(
            (ROOT / "formal/proposals/native-source-artifact-vectors.json").read_bytes()
        )
        self.assertEqual(generated, retained)
        result = source.resolve_q_source(self.store, self.manifest_id)
        self.assertEqual([n for row in result.rows for n in row["values"]], self.golden["q_values"])
        self.assertEqual(len(result.sources), 12)
        self.assertEqual(len(result.rows), 5)
        for row in result.sources:
            self.assertEqual(bytes.fromhex(row["bytes_hex"]), self.store[row["id"]])

    def test_every_source_must_be_present_and_hash_match(self):
        for identifier in self.store:
            with self.subTest(identifier=identifier):
                changed = dict(self.store)
                del changed[identifier]
                with self.assertRaisesRegex(source.SourceError, "MISSING_PREIMAGE"):
                    source.resolve_q_source(changed, self.manifest_id)
                changed[identifier] = self.store[identifier] + b" "
                with self.assertRaisesRegex(source.SourceError, "SOURCE_HASH"):
                    source.resolve_q_source(changed, self.manifest_id)

    def test_exact_hash_domain_is_not_interchangeable(self):
        r = source.Resolver(self.store)
        with self.assertRaisesRegex(source.SourceError, "SOURCE_HASH"):
            r.raw(self.manifest_id, "schema")

    def test_all_envelope_prefix_corruption_rejects(self):
        raw = self.envelope()
        variants = [
            raw[:15],
            raw[:-1],
            raw + b"\0",
            b"X" + raw[1:],
            raw[:4] + b"\x02\0" + raw[6:],
            raw[:6] + b"\x01\0" + raw[8:],
            raw[:8] + struct.pack("<I", source.MAX_HEADER + 1) + raw[12:],
            raw[:12] + struct.pack("<I", source.MAX_PAYLOAD + 2) + raw[16:],
        ]
        for mutated in variants:
            with self.subTest(prefix=mutated[:16]), self.assertRaises(source.SourceError):
                source.read_drq1(mutated)

    def test_header_json_canonicality_and_duplicate_keys(self):
        for raw in [
            b'{"x":1,"x":2}',
            b'{"x": 1}',
            b'{"x":null}',
            b'{"x":1.0}',
            b'{"x":NaN}',
            b'{"x":"\\u0061"}',
            b'{"x":true}\n',
            b'{"x":"\\u0000"}',
            b'{"x":"\\u00e9"}',
            b"[]",
        ]:
            with self.subTest(raw=raw), self.assertRaises(source.SourceError):
                source.decode(raw)

    def test_q_endpoints_odd_length_payload_hash_and_forbidden_minimum(self):
        good = self.envelope(payload=struct.pack("<hhhh", -32767, 32767, -1, 0))
        self.assertEqual(source.read_drq1(good)[1], (-32767, 32767, -1, 0))
        for bad in [
            self.envelope(payload=b"x"),
            self.envelope(payload=b"\0\x80"),
            good[:-1] + bytes([good[-1] ^ 1]),
        ]:
            with self.assertRaises(source.SourceError):
                source.read_drq1(bad)

    def test_rehashed_every_header_field_substitution_rejects(self):
        base = self.golden["shards"][0]["header"]
        for key, value in base.items():
            if key == "payload_sha256":
                continue  # recomputed from actual payload; tested separately
            header = copy.deepcopy(base)
            header[key] = value + 1 if type(value) is int else "substituted"
            with self.subTest(key=key):
                root = self.replace_leaf(self.envelope(header=header))
                with self.assertRaisesRegex(source.SourceError, "HEADER_CONTEXT"):
                    source.resolve_q_source(self.store, root)

    def test_header_omission_extra_and_boolean_not_integer(self):
        for mode in ("omitted", "extra", "bool"):
            h = copy.deepcopy(self.golden["shards"][0]["header"])
            if mode == "omitted":
                del h["ticket_id"]
            elif mode == "extra":
                h["approved"] = True
            else:
                h["ordinal"] = False
            with self.assertRaises(source.SourceError):
                source.resolve_q_source(self.store, self.replace_leaf(self.envelope(header=h)))

    def test_manifest_missing_extra_duplicate_reordered_ranges(self):
        for mode in range(4):
            m = copy.deepcopy(self.golden["manifest"]["value"])
            if mode == 0:
                m["shards"].pop()
            elif mode == 1:
                m["shards"].append(m["shards"][-1])
            elif mode == 2:
                m["shards"][1] = m["shards"][0]
            else:
                m["shards"].reverse()
            with self.assertRaises(source.SourceError):
                source.resolve_q_source(self.store, self.new_manifest(m))

    def test_commitment_and_totals_are_recomputed(self):
        for key in (
            "commitment_root",
            "total_elements",
            "total_payload_bytes",
            "total_envelope_bytes",
        ):
            m = copy.deepcopy(self.golden["manifest"]["value"])
            m[key] = "sha256:" + "0" * 64 if key == "commitment_root" else m[key] + 1
            with self.subTest(key=key), self.assertRaises(source.SourceError):
                source.resolve_q_source(self.store, self.new_manifest(m))

    def test_schema_omission_alias_and_layout_preserve_all_metadata(self):
        schema = json.loads(self.store[self.golden["manifest"]["value"]["parameter_schema_id"]])
        segments = source.schema_segments(schema)
        self.assertEqual(
            [(x["segment_id"], x["element_count"]) for x in segments],
            [("decoder.bias", 4), ("embedding.weight", 32)],
        )
        include = copy.deepcopy(schema)
        include["frozen_omission_policy"] = "INCLUDE_ALL"
        self.assertEqual(source.schema_segments(include)[-1]["element_count"], 1)
        for mode in ("duplicate", "reverse", "alias", "bool", "huge", "long-segment"):
            s = copy.deepcopy(schema)
            if mode == "duplicate":
                s["parameters"].append(s["parameters"][0])
            elif mode == "reverse":
                s["parameters"].reverse()
            elif mode == "alias":
                s["tied_aliases"]["bad"] = "missing"
            elif mode == "long-segment":
                s["parameters"][0]["name"] = "a" * 256
            else:
                s["parameters"][0]["shape"] = [True] if mode == "bool" else [source.MAX_ELEMENTS, 2]
            with self.subTest(mode=mode), self.assertRaises(source.SourceError):
                source.schema_segments(s)

    def test_json_depth_and_total_resource_limits(self):
        with self.assertRaises(source.SourceError):
            source.decode(b'{"a":' * 34 + b"{}" + b"}" * 34)
        with self.assertRaises(source.SourceError):
            source.decode(b" " * (source.MAX_JSON + 1))
        r = source.Resolver(self.store)
        r.total = source.MAX_TOTAL
        with self.assertRaisesRegex(source.SourceError, "SOURCE_TOTAL_LIMIT"):
            r.raw(self.manifest_id, "manifest")

    def test_rehashed_changed_q_is_new_source_not_same_authority(self):
        # Content validation must accept a DIFFERENT valid source; authorization
        # cannot be inferred from this. The old independently pinned root differs.
        new_id = self.replace_leaf(self.envelope(payload=struct.pack("<hhhh", 1, 2, 3, 4)))
        result = source.resolve_q_source(self.store, new_id)
        self.assertNotEqual(new_id, self.manifest_id)
        self.assertEqual(result.rows[0]["values"], [1, 2, 3, 4])
        self.assertNotEqual(result.rows, source.resolve_q_source(self.store, self.manifest_id).rows)

    def test_proof_metadata_is_retained_not_an_admission_boolean(self):
        m = copy.deepcopy(self.golden["manifest"]["value"])
        proof = copy.deepcopy(self.golden["proof_instance"]["value"])
        proof["result"] = "NOT_A_PROOF"
        # The content resolver deliberately does NOT authenticate theorem metadata.
        raw = source.canonical(proof)
        identifier = source.content_id(raw, source.DOMAINS["proof"])
        self.store[identifier] = raw
        self.assertEqual(
            source.Resolver(self.store).document(identifier, "proof")["result"], "NOT_A_PROOF"
        )
        # It cannot replace an original contribution's referenced proof silently.
        m["proof_instance_id"] = identifier
        with self.assertRaisesRegex(source.SourceError, "HEADER_CONTEXT"):
            source.resolve_q_source(self.store, self.new_manifest(m))

    def test_old008_ids_and_label_leaves_do_not_resolve_as004(self):
        report = generator.generate()
        self.assertEqual(len(report["original008_unresolved"]), 16)
        self.assertEqual(
            sum(
                x["status"] == "LABEL_HASH_WITHOUT_DRQ1_PREIMAGE"
                for x in report["original008_unresolved"]
            ),
            12,
        )
        for row in report["original008_unresolved"]:
            with self.assertRaisesRegex(source.SourceError, "MISSING_PREIMAGE"):
                source.Resolver(self.store).raw(row["id"], "leaf")
        self.assertFalse(report["native_export_authenticated"])
        self.assertFalse(report["cross_fixture_source_join"])
        self.assertFalse(report["draft_graph_schema_q_identity_join"])

    def test_rehashed_scale_plan_config_proof_links_and_omissions_reject(self):
        for fixture_key, kind, manifest_key, fields in [
            ("scale_table", "scale", "scale_table_id", ["parameter_schema_id", "segments"]),
            ("shard_plan", "plan", "shard_plan_id", ["scale_table_id", "entries"]),
            ("fixedpoint_config", "config", "round_config_id", ["profile_id", "shard_plan_id"]),
            ("proof_instance", "proof", "proof_instance_id", ["config_id", "common_denominator"]),
        ]:
            for field in fields:
                for mode in ("omit", "substitute"):
                    doc = copy.deepcopy(self.golden[fixture_key]["value"])
                    if mode == "omit":
                        del doc[field]
                    else:
                        doc[field] = "sha256:" + "0" * 64 if field.endswith("_id") else []
                    raw = source.canonical(doc)
                    identifier = source.content_id(raw, source.DOMAINS[kind])
                    self.store[identifier] = raw
                    m = copy.deepcopy(self.golden["manifest"]["value"])
                    m[manifest_key] = identifier
                    with self.subTest(kind=kind, field=field, mode=mode):
                        with self.assertRaises(source.SourceError):
                            source.resolve_q_source(self.store, self.new_manifest(m))


if __name__ == "__main__":
    unittest.main()
