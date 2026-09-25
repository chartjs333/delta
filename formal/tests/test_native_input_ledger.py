"""Native input component transitions must not be called full CloseInput refinement."""

import copy
import hashlib
import json
import sys
import unittest
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_input_ledger_vectors as vectors  # noqa: E402
from formal_artifacts import canonical_json_bytes  # noqa: E402
from native_certificate_chain import content_id  # noqa: E402
from native_input_ledger import bind_frozen_isc, check_required_ticket_coverage  # noqa: E402


class NativeInputLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((vectors.FOLDER / "cpp-cross-check.json").read_bytes())
        cls.rows = cls.evidence["observed"][-2]["after"]["frozen_inputs"]
        cls.domains = {"ticket-a": "domain-a", "ticket-b": "domain-b"}
        cls.isc = vectors.closure_certificate()

    def bind(self, rows, domains=None, isc=None):
        isc = self.isc if isc is None else isc
        return bind_frozen_isc(
            canonical_json_bytes(isc),
            content_id(isc),
            rows,
            self.domains if domains is None else domains,
        )

    def test_all_native_operation_results_and_accessor_snapshots_match(self):
        self.assertEqual(self.evidence["observed"], vectors.expected())
        self.assertEqual(len(vectors.scenarios()), 36)
        self.assertTrue(self.evidence["native_component_execution"])
        self.assertFalse(self.evidence["native_runtime_execution"])
        self.assertFalse(self.evidence["native_export_authenticated"])
        self.assertFalse(self.evidence["gate_eligible"])
        actual = self.evidence["observed"]
        for left, right in pairwise(actual[:-1]):
            self.assertEqual(left["after"], right["before"])

    def test_errors_retries_and_late_evidence_preserve_frozen_rows(self):
        operations = self.evidence["observed"][:-1]
        for row in operations:
            if row["disposition"].startswith("ERROR:") or row["disposition"] == "replay":
                with self.subTest(name=row["name"]):
                    self.assertEqual(row["before"], row["after"])
        cut = next(
            i for i, row in enumerate(operations) if row["name"] == "freeze-partial-permitted-set"
        )
        frozen = operations[cut]["after"]["frozen_inputs"]
        for row in operations[cut:]:
            self.assertEqual(row["after"]["frozen_inputs"], frozen)
        final = operations[-1]["after"]
        self.assertEqual(final["late_commitments"], 1)
        self.assertEqual(final["late_availability"], 1)
        # Late payloads themselves have no native public accessor and are not
        # represented as a complete native/private state snapshot in this evidence.

    def test_complete_frozen_rows_derive_new_native_isc_and_body_ids(self):
        item = self.evidence["observed"][-1]
        self.assertEqual(item["certificate_ascii"].encode(), canonical_json_bytes(self.isc))
        self.assertEqual(item["certificate_id"], content_id(self.isc))
        result = self.bind(self.rows)
        self.assertEqual(result["tuples"], self.isc["tuples"])
        self.assertFalse(result["root_preimage_verified"])
        self.assertFalse(result["full_public_close_relation"])
        old = vectors.chain.fixture()[0]["ISC"]
        with self.assertRaisesRegex(ValueError, "tuple mismatch"):
            self.bind(self.rows, isc=old)

    def test_frozen_missing_extra_duplicate_reordered_and_substituted_reject(self):
        mutations = [
            self.rows[:1],
            self.rows[::-1],
            self.rows * 2,
            [*self.rows, {**self.rows[-1], "ticket_id": "ticket-c"}],
        ]
        for key, value in [
            ("ticket_id", "ticket-c"),
            ("commitment_id", vectors.cid("e")),
            ("availability_certificate_id", vectors.cid("f")),
        ]:
            changed = copy.deepcopy(self.rows)
            changed[0][key] = value
            mutations.append(changed)
        for index, rows in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.bind(rows)

    def test_domain_metadata_cannot_be_omitted_changed_or_inferred_from_hash(self):
        for mapping in [{}, {"ticket-a": "domain-a"}, {**self.domains, "ticket-b": "domain-a"}]:
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                self.bind(self.rows, domains=mapping)
        forged = copy.deepcopy(self.rows)
        forged[0]["domain_id"] = "domain-a"
        with self.assertRaisesRegex(ValueError, "exact nested fields"):
            self.bind(forged)

    def test_freeze_does_not_discharge_required_ticket_policy(self):
        required = ["ticket-" + t for t in "abcd"]
        self.assertEqual(
            check_required_ticket_coverage(self.rows, required, "OMIT_UNAVAILABLE"), required[:2]
        )
        with self.assertRaisesRegex(ValueError, "incomplete required"):
            check_required_ticket_coverage(self.rows, required, "ABORT_ON_INCOMPLETE")
        self.assertEqual(
            check_required_ticket_coverage(self.rows, required[:2], "ABORT_ON_INCOMPLETE"),
            required[:2],
        )
        for candidates, policy in [
            (["ticket-a"], "OMIT_UNAVAILABLE"),
            (required[::-1], "OMIT_UNAVAILABLE"),
            (required, "invented-policy"),
            (["ticket-a"] * 2, "OMIT_UNAVAILABLE"),
        ]:
            with self.assertRaises(ValueError):
                check_required_ticket_coverage(self.rows, candidates, policy)
        # TLA OMIT_UNAVAILABLE's coverage conjunct accepts empty entries; actual
        # InputLedger::freeze rejects empty availability. These are not equivalent APIs.
        self.assertEqual(check_required_ticket_coverage([], required, "OMIT_UNAVAILABLE"), [])
        self.assertEqual(self.evidence["observed"][0]["disposition"], "ERROR:input_set_empty")

    def test_root_provenance_is_not_invented_from_exact_frozen_rows(self):
        changed = {**self.isc, "input_root": vectors.cid("f")}
        result = self.bind(self.rows, isc=changed)
        self.assertFalse(result["root_preimage_verified"])
        self.assertFalse(result["native_export_authenticated"])
        self.assertNotEqual(content_id(changed), content_id(self.isc))
        with self.assertRaisesRegex(ValueError, "certificate hash"):
            bind_frozen_isc(
                canonical_json_bytes(changed), content_id(self.isc), self.rows, self.domains
            )

    def test_component_parser_rejects_missing_duplicate_reordered_and_typed_substitution(self):
        rows = self.evidence["observed"]

        def encode(data):
            return "\n".join(canonical_json_bytes(x).decode() for x in data)

        self.assertEqual(vectors.parse_output(encode(rows)), rows)
        altered = copy.deepcopy(rows)
        altered[0]["after"]["frozen"] = 0
        cases = [rows[:-1], rows[::-1], [*rows, rows[-1]], altered]
        for bad in cases:
            with self.assertRaisesRegex(ValueError, "mismatch"):
                vectors.parse_output(encode(bad))
        with self.assertRaisesRegex(ValueError, "duplicate native"):
            vectors.parse_output('{"name":"a","name":"b"}')

    def test_exact_source_and_diagnostic_fixture_reproduction(self):
        blobs = vectors.sources()
        self.assertEqual(
            self.evidence["source_sha256"],
            {p: hashlib.sha256(b).hexdigest() for p, b in blobs.items()},
        )
        self.assertEqual(
            self.evidence["unmodified_translation_units"],
            ["consensus.cpp", "canonical.cpp", "sha256.cpp", "contracts.cpp"],
        )
        code = vectors.harness().encode()
        self.assertEqual(hashlib.sha256(code).hexdigest(), self.evidence["harness_sha256"])
        self.assertEqual((vectors.FOLDER / "harness.cpp").read_bytes(), code)
        self.assertEqual(vectors.TARGET.read_bytes(), canonical_json_bytes(vectors.document()))


if __name__ == "__main__":
    unittest.main()
