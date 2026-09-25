"""Exact pinned native components, explicit external provenance, fail-closed graph."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_certificate_chain as vectors  # noqa: E402
import native_certificate_chain as codec  # noqa: E402
from formal_artifacts import canonical_json_bytes  # noqa: E402


def repin(changes):
    """Test-only rebuild under a NEW caller anchor; never authenticates that anchor."""
    docs, _, _, _ = vectors.fixture()
    originals = {name: codec.content_id(doc) for name, doc in docs.items()}
    changes(docs)
    renamed = {}

    def translate(value):
        if isinstance(value, dict):
            return {key: translate(child) for key, child in value.items()}
        if isinstance(value, list):
            return [translate(child) for child in value]
        return renamed.get(value, value) if isinstance(value, str) else value

    store, ids = {}, {}
    for name, doc in docs.items():
        doc = translate(doc)
        if name == "ROOT":
            doc["merkle_root"] = codec.merkle_root(doc["leaves"])
        identifier = codec.content_id(doc)
        renamed[originals[name]] = identifier
        ids[name] = identifier
        store[identifier] = canonical_json_bytes(doc)
    return store, ids["ROOT"], {ids["EC"]: ids["SEED"]}


class NativeCertificateChainTests(unittest.TestCase):
    def setUp(self):
        self.docs, self.store, self.root, self.binding = vectors.fixture()

    def decode(self, doc):
        return codec.decode_certificate(
            canonical_json_bytes(doc), codec.content_id(doc), doc["type_name"]
        )

    def test_seven_exact_native_encodings_hashes_and_four_body_ids(self):
        evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        self.assertEqual(evidence["observed"], vectors.expected_components())
        self.assertEqual(len(evidence["observed"]["certificates"]), 7)
        self.assertEqual(len(evidence["observed"]["bodies"]), 4)
        self.assertTrue(evidence["native_component_execution"])
        self.assertFalse(evidence["native_runtime_execution"])
        self.assertFalse(evidence["native_export_authenticated"])
        self.assertFalse(evidence["gate_eligible"])
        for doc in self.docs.values():
            self.assertEqual(self.decode(doc), doc)

    def test_whole_graph_loads_every_exact_parent_and_leaf(self):
        projection = codec.bind_graph(self.store, self.root, self.binding)
        self.assertEqual(projection["loaded_ids"], sorted(self.store))
        self.assertEqual(len(projection["loaded_ids"]), 7)
        self.assertFalse(projection["native_admission_verified"])
        self.assertFalse(projection["native_export_authenticated"])
        self.assertEqual(projection["native_semantics_id"], codec.NATIVE_SEMANTICS)

    def test_each_missing_or_substituted_artifact_rejects(self):
        for identifier, raw in self.store.items():
            with self.subTest(identifier=identifier):
                missing = dict(self.store)
                del missing[identifier]
                with self.assertRaisesRegex(ValueError, "missing artifact"):
                    codec.bind_graph(missing, self.root, self.binding)
                substituted = dict(self.store)
                changed = json.loads(raw)
                changed["view"] += 1
                substituted[identifier] = canonical_json_bytes(changed)
                with self.assertRaisesRegex(ValueError, "certificate hash"):
                    codec.bind_graph(substituted, self.root, self.binding)

    def test_rehashed_mixed_contexts_and_wrong_parent_edges_reject(self):
        for name in ["ISC", "SEED", "NORM", "EC", "APC", "PARAMETER"]:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "mixed context"):
                codec.bind_graph(*repin(lambda docs, name=name: docs[name].update(view=1)))
        for name, field in [
            ("EC", "input_set_certificate_id"),
            ("APC", "eligibility_certificate_id"),
            ("SEED", "input_set_certificate_id"),
            ("NORM", "input_set_certificate_id"),
            ("PARAMETER", "aggregation_plan_certificate_id"),
        ]:
            with self.subTest(name=name, field=field), self.assertRaisesRegex(ValueError, "parent"):
                codec.bind_graph(
                    *repin(
                        lambda docs, name=name, field=field: docs[name].update(
                            {field: "sha256:" + "a" * 64}
                        )
                    )
                )

    def test_ec_seed_is_independent_metadata_absent_from_certificate(self):
        self.assertNotIn("seed_transcript_id", self.docs["EC"])
        for supplied in [{}, {next(iter(self.binding)): "sha256:" + "f" * 64}]:
            with self.assertRaisesRegex(ValueError, "independent EC seed"):
                codec.bind_graph(self.store, self.root, supplied)
        with self.assertRaisesRegex(ValueError, "seed parent missing"):
            codec.voted_body(self.docs["EC"])
        invented = {**self.docs["EC"], "seed_transcript_id": next(iter(self.binding.values()))}
        with self.assertRaisesRegex(ValueError, "certificate fields"):
            self.decode(invented)

    def test_signers_affect_qc_id_but_not_prequorum_body(self):
        original = self.docs["ISC"]
        changed = {**original, "signer_ids": ["validator-1", "validator-2", "validator-4"]}
        self.decode(changed)  # Shape validation is deliberately not signature authentication.
        self.assertNotEqual(codec.content_id(original), codec.content_id(changed))
        self.assertEqual(codec.voted_body(original), codec.voted_body(changed))
        first = codec.voted_body(self.docs["EC"], next(iter(self.binding.values())))
        second = codec.voted_body(self.docs["EC"], "sha256:" + "9" * 64)
        self.assertNotEqual(first["body_id"], second["body_id"])

    def test_complete_ordered_leaf_coverage_and_leaf_keys(self):
        def wrong_key(docs):
            docs["ROOT"]["required_keys"][0]["shard_id"] = "shard-b"

        with self.assertRaisesRegex(ValueError, "coverage"):
            codec.bind_graph(*repin(wrong_key))
        with self.assertRaisesRegex(ValueError, "leaf key"):
            codec.bind_graph(*repin(lambda docs: docs["PARAMETER"].update(shard_id="shard-b")))
        for field in ["leaves", "required_keys"]:
            doc = copy.deepcopy(self.docs["ROOT"])
            doc[field].append(copy.deepcopy(doc[field][0]))
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "strict list order"):
                self.decode(doc)

    def test_merkle_odd_promotion_order_and_full_coverage(self):
        leaves = [
            {"domain_id": "d", "parameter_shard_qc_id": "sha256:" + str(i) * 64, "shard_id": str(i)}
            for i in range(1, 5)
        ]
        hashed = [
            codec.digest("deltareduce.008.aggregate-leaf.v1", canonical_json_bytes(row))
            for row in leaves
        ]

        def pair(a, b):
            return codec.digest("deltareduce.008.aggregate-node.v1", bytes.fromhex(a[7:] + b[7:]))

        self.assertEqual(codec.merkle_root(leaves[:1]), hashed[0])
        self.assertEqual(codec.merkle_root(leaves[:3]), pair(pair(*hashed[:2]), hashed[2]))
        self.assertEqual(codec.merkle_root(leaves), pair(pair(*hashed[:2]), pair(*hashed[2:])))
        self.assertNotEqual(codec.merkle_root(leaves), codec.merkle_root(leaves[::-1]))
        self.assertNotEqual(codec.merkle_root(leaves[:3]), codec.merkle_root(leaves))

    def test_native_shape_rejections_are_not_silently_normalized(self):
        cases = []
        doc = copy.deepcopy(self.docs["ISC"])
        doc["tuples"] = []
        cases.append(doc)
        doc = copy.deepcopy(self.docs["ISC"])
        doc["signer_ids"][1] = doc["signer_ids"][0]
        cases.append(doc)
        cases.append({**self.docs["ISC"], "input_root": "invalid"})
        cases.append({**self.docs["ROOT"], "merkle_root": "sha256:" + "0" * 64})
        doc = copy.deepcopy(self.docs["ROOT"])
        doc["leaves"] *= 2
        cases.append(doc)
        for index, doc in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.decode(doc)

    def test_strict_integer_fraction_nested_field_and_sequence_shapes(self):
        for value in [True, -1, 2**64, "1", 1.0, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.decode({**self.docs["ISC"], "height": value})
        for fraction in [
            {"numerator": "2", "denominator": 2},
            {"numerator": "-1", "denominator": 1},
            {"numerator": str(2**63), "denominator": 1},
            {"numerator": "01", "denominator": 1},
            {"numerator": "1", "denominator": False},
            {"numerator": "1", "denominator": 1, "extra": 1},
        ]:
            doc = copy.deepcopy(self.docs["EC"])
            doc["entries"][0]["gamma"] = fraction
            with self.subTest(fraction=fraction), self.assertRaises(ValueError):
                self.decode(doc)
        for field in ["tuples", "signer_ids"]:
            for value in [1, {}, "wrong", None]:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.decode({**self.docs["ISC"], field: value})

    def test_native_semantics_not_upgraded_to_candidate(self):
        for field, value in [
            ("formal_semantics_id", "sha256:" + "c" * 64),
            ("schema_version", "2.0.0"),
            ("native_export_authenticated", True),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.decode({**self.docs["ISC"], field: value})

    def test_noncanonical_duplicate_unknown_and_deep_json_reject(self):
        doc = self.docs["ISC"]
        original = canonical_json_bytes(doc)
        cases = [
            original + b" ",
            json.dumps(doc, indent=2).encode(),
            original[:-1] + b',"height":1}',
            b"[" * 2000 + b"0" + b"]" * 2000,
            b"\xff",
        ]
        for raw in cases:
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                codec.decode_certificate(raw, codec.content_id(doc), doc["type_name"])
        with self.assertRaisesRegex(ValueError, "certificate fields"):
            self.decode({**doc, "unknown": 1})

    def test_proposal_resource_bounds_remain_explicit(self):
        doc = self.docs["ISC"]
        with self.assertRaisesRegex(ValueError, "payload bound"):
            codec.decode_certificate(b"x" * (codec.MAX_BYTES + 1), "", doc["type_name"])
        with self.assertRaisesRegex(ValueError, "text bound"):
            self.decode({**doc, "round_id": "a" * 129})
        with self.assertRaisesRegex(ValueError, "list bound"):
            self.decode({**doc, "tuples": doc["tuples"] * 4097})
        with self.assertRaisesRegex(ValueError, "store bound"):
            codec.bind_graph(dict.fromkeys(range(4097), b""), self.root, self.binding)

    def test_rehashed_graph_does_not_replace_independently_fixed_anchor(self):
        store, root, binding = repin(
            lambda docs: docs["ISC"].update(input_root="sha256:" + "a" * 64)
        )
        self.assertNotEqual(root, self.root)
        with self.assertRaisesRegex(ValueError, "missing artifact"):
            codec.bind_graph(store, self.root, binding)
        # Explicit countercheck: a caller-provided NEW anchor makes an opaque input_root
        # shape acceptable. No commitment/availability root preimage has been checked.
        result = codec.bind_graph(store, root, binding)
        self.assertFalse(result["native_admission_verified"])
        self.assertFalse(result["native_export_authenticated"])

    def test_component_output_parser_rejects_missing_duplicate_and_extra_results(self):
        expected = vectors.expected_components()
        rows = []
        for key, item in expected["certificates"].items():
            rows.append("\t".join(["CERT", key, item["id"], item["json_hex"]]))
        for kind, field in [("BODY", "bodies"), ("MERKLE", "merkle_cases")]:
            rows.extend("\t".join([kind, key, value]) for key, value in expected[field].items())
        rows.extend("REJECT\t" + name for name in expected["rejections"])
        rows.extend(
            "VARIANT\t" + key + "\t" + value
            for key, value in expected.items()
            if key.startswith("alternate")
        )
        raw = "\n".join(rows)
        self.assertEqual(vectors.parse_output(raw), expected)
        for bad in [
            "\n".join(rows[1:]),
            raw + "\n" + rows[0],
            raw + "\nCERT\tx",
            raw + "\nOK",
            raw + "\nVARIANT\tbodies\tx",
            raw + "\nREJECT\textra",
        ]:
            with self.subTest(suffix=bad[-40:]), self.assertRaises(ValueError):
                vectors.parse_output(bad)

    def test_source_spans_whole_components_and_byte_exact_reproduction(self):
        blobs = vectors.blobs()
        code, spans = vectors.harness(blobs)
        evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        self.assertEqual(len(spans), 24)
        self.assertEqual(evidence["extracted_definitions"], spans)
        self.assertEqual(
            evidence["unmodified_translation_units"],
            ["canonical.cpp", "sha256.cpp", "contracts.cpp"],
        )
        self.assertEqual(
            evidence["source_sha256"],
            {path: hashlib.sha256(raw).hexdigest() for path, raw in blobs.items()},
        )
        self.assertEqual(evidence["harness_sha256"], hashlib.sha256(code.encode()).hexdigest())
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_bytes(), code.encode())
        self.assertEqual(vectors.TARGET.read_bytes(), canonical_json_bytes(vectors.document()))


if __name__ == "__main__":
    unittest.main()
