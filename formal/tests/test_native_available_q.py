"""Original Q preimages, native availability primitives and explicit trust gaps."""

import copy
import hashlib
import json
import struct
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_available_q as gen  # noqa: E402
import generate_native_plan_weights as plans  # noqa: E402
import native_available_q as available  # noqa: E402
import native_source_artifacts as src  # noqa: E402


class NativeAvailableQTests(unittest.TestCase):
    def setUp(self):
        self.store, self.golden, self.obs = gen.fixture()

    def check(self, observation=None):
        oid, raw = available.observation_bytes(self.obs if observation is None else observation)
        self.store[oid] = raw
        return available.resolve_available_q(self.store, oid)

    def test_original_q_preimages_and_both_distinct_orders(self):
        result = self.check()
        self.assertEqual(len(result.required_leaves), 5)
        self.assertEqual(result.required_leaves, tuple(sorted(result.required_leaves)))
        self.assertEqual(
            [v for r in result.source.q.rows for v in r["values"]], self.golden["q_values"]
        )
        self.assertEqual(len(result.source.q.sources), 12)
        self.assertEqual(
            result.source.q.manifest["shards"], self.golden["manifest"]["value"]["shards"]
        )
        for row in result.source.q.sources:
            self.assertEqual(bytes.fromhex(row["bytes_hex"]), self.store[row["id"]])

    def test_matched_incomplete_native_leaf_sets_do_not_supply_source_coverage(self):
        for count in (1, 4):
            obs = copy.deepcopy(self.obs)
            obs["required_leaf_ids"] = obs["required_leaf_ids"][:count]
            obs["availability"]["covered_leaf_ids"] = list(obs["required_leaf_ids"])
            available.ledger_inputs(obs)
            with self.assertRaisesRegex(src.SourceError, "REQUIRED_Q_LEAF_SET"):
                self.check(obs)

    def test_matched_extra_native_leaf_rejects_at_source(self):
        extra = "sha256:" + "f" * 64
        self.obs["required_leaf_ids"] = sorted([*self.obs["required_leaf_ids"], extra])
        self.obs["availability"]["covered_leaf_ids"] = list(self.obs["required_leaf_ids"])
        available.ledger_inputs(self.obs)
        with self.assertRaisesRegex(src.SourceError, "REQUIRED_Q_LEAF_SET"):
            self.check()

    def test_native_shapes_coverage_order_quorum_and_empty_sets(self):
        expected = json.loads((gen.FOLDER / "cpp-cross-check.json").read_bytes())["observed"]
        for name, obs in gen.cases().items():
            if expected[name]["status"] == "REJECT":
                with self.subTest(name=name), self.assertRaises(src.SourceError):
                    available.ledger_inputs(obs)
            else:
                frozen = available.ledger_inputs(obs)
                self.assertEqual(list(frozen.values()), expected[name]["fields"])
        for field in ("permitted_ticket_ids", "permitted_attester_ids", "required_leaf_ids"):
            obs = copy.deepcopy(self.obs)
            obs[field] = []
            with self.subTest(field=field), self.assertRaises(src.SourceError):
                self.check(obs)

    def test_opaque_ids_do_not_establish_manifest_or_root_identity(self):
        result = self.check()
        self.assertNotEqual(result.frozen_input["commitment_id"], result.source.q.manifest_id)
        self.assertNotEqual(
            result.frozen_input["commitment_id"], result.source.q.manifest["commitment_root"]
        )
        for digit in ("a", "b"):
            obs = copy.deepcopy(self.obs)
            obs["commitment"]["commitment_id"] = "sha256:" + digit * 64
            obs["availability"]["commitment_id"] = obs["commitment"]["commitment_id"]
            obs["availability"]["certificate_id"] = "sha256:" + digit * 64
            self.check(obs)  # explicit boundary countercheck, NEVER authentication

    def test_manifest_ticket_cannot_be_replaced_by_consistent_native_alias(self):
        self.obs["permitted_ticket_ids"] = ["new-ticket"]
        self.obs["commitment"]["ticket_id"] = "new-ticket"
        self.obs["availability"]["ticket_id"] = "new-ticket"
        available.ledger_inputs(self.obs)
        with self.assertRaisesRegex(src.SourceError, "MANIFEST_TICKET"):
            self.check()

    def test_every_observation_field_and_unknown_auth_flag_rejects(self):
        for field in [*self.obs, "native_export_authenticated"]:
            obs = copy.deepcopy(self.obs)
            if field in obs:
                del obs[field]
            else:
                obs[field] = True
            with self.subTest(field=field), self.assertRaises(src.SourceError):
                self.check(obs)

    def test_nested_record_fields_exact(self):
        for name in ("commitment", "availability"):
            for field in [*self.obs[name], "extra"]:
                obs = copy.deepcopy(self.obs)
                if field in obs[name]:
                    del obs[name][field]
                else:
                    obs[name][field] = True
                with self.subTest(record=name, field=field), self.assertRaises(src.SourceError):
                    self.check(obs)

    def test_case_mutations_do_not_share_required_and_covered_lists(self):
        cases = gen.cases()
        baseline = cases["actual-004-leaf-coverage-synthetic-ledger-input"]
        changed = cases["missing-covered-leaf"]
        self.assertIsNot(
            baseline["required_leaf_ids"], baseline["availability"]["covered_leaf_ids"]
        )
        self.assertEqual(changed["required_leaf_ids"], baseline["required_leaf_ids"])
        self.assertEqual(len(changed["availability"]["covered_leaf_ids"]), 4)
        with self.assertRaisesRegex(src.SourceError, "AVAILABILITY_COVERAGE"):
            available.ledger_inputs(changed)

    def test_version_source_and_forged_provenance(self):
        for field, value in (
            ("version", "native-export.v1"),
            ("source_commit", "0" * 40),
            ("provenance", "AUTHENTICATED_NATIVE_EXPORT"),
        ):
            obs = copy.deepcopy(self.obs)
            obs[field] = value
            with self.subTest(field=field), self.assertRaises(src.SourceError):
                self.check(obs)

    def test_observation_hash_and_canonical_preimage(self):
        oid, raw = available.observation_bytes(self.obs)
        for changed in (
            raw + b" ",
            b'{"a":1,"a":1}',
            raw.replace(b'"required_threshold":2', b'"required_threshold":3'),
        ):
            self.store[oid] = changed
            with self.assertRaises(src.SourceError):
                available.resolve_available_q(self.store, oid)

    def test_all_source_objects_missing_and_corrupt(self):
        result = self.check()
        for row in result.source.q.sources:
            for bad in (None, self.store[row["id"]] + b" "):
                store = dict(self.store)
                if bad is None:
                    del store[row["id"]]
                else:
                    store[row["id"]] = bad
                with self.subTest(kind=row["kind"]), self.assertRaises(src.SourceError):
                    available.resolve_available_q(store, result.observation_id)

    def test_threshold_types_ranges_and_resources(self):
        for value in (True, "2", 0, -1, 1 << 32):
            obs = copy.deepcopy(self.obs)
            obs["required_threshold"] = value
            obs["availability"]["threshold"] = value
            with self.subTest(value=value), self.assertRaises(src.SourceError):
                self.check(obs)
        with (
            patch.object(available, "MAX_TOTAL", 1),
            self.assertRaisesRegex(src.SourceError, "SOURCE_TOTAL_LIMIT"),
        ):
            self.check()

    def test_composed_plan_source_relation_and_no_later_aggregate(self):
        store, plan, edges, observations, _, _ = gen.joined_fixture()
        out = available.resolve_plan_available_q(store, plan, edges, observations)
        self.assertEqual(out.inputs[0].source.q.manifest_id, self.golden["manifest"]["content_id"])
        self.assertEqual(out.plan.rows[0]["coefficient"], 1)
        used = (
            {s["id"] for s in out.plan.sources}
            | {s["id"] for s in out.inputs[0].source.q.sources}
            | set(observations)
        )
        self.assertEqual(
            available.resolve_plan_available_q(
                {k: store[k] for k in used}, plan, edges, observations
            ),
            out,
        )

    def test_composed_original_id_edges_cannot_be_substituted(self):
        store, plan, edges, _observations, _, obs = gen.joined_fixture()
        for field in ("commitment_id", "certificate_id"):
            changed = copy.deepcopy(obs)
            changed["availability"][field] = "sha256:" + "f" * 64
            if field == "commitment_id":
                changed["commitment"][field] = changed["availability"][field]
            oid, raw = available.observation_bytes(changed)
            store[oid] = raw
            available.resolve_available_q(store, oid)
            with self.assertRaisesRegex(src.SourceError, "PLAN_INPUT_IDENTITY"):
                available.resolve_plan_available_q(store, plan, edges, [oid])

    def test_composed_domain_and_proof_identity(self):
        store, _plan, _edges, observations, docs, _ = gen.joined_fixture()
        for name in ("ISC", "EC"):
            key = "tuples" if name == "ISC" else "entries"
            docs[name][key][0]["domain_id"] = "other-domain"
        pid, e = plans.put_graph(store, docs)
        with self.assertRaisesRegex(src.SourceError, "PLAN_INPUT_DOMAIN"):
            available.resolve_plan_available_q(store, pid, e, observations)
        store, _plan, _edges, observations, docs, _ = gen.joined_fixture()
        proof = json.loads(store[docs["APC"]["accumulator_proof_id"]])
        proof["common_denominator"] = "2"
        raw = src.canonical(proof)
        new_id = src.content_id(raw, src.DOMAINS["proof"])
        store[new_id] = raw
        docs["APC"]["accumulator_proof_id"] = new_id
        pid, e = plans.put_graph(store, docs)
        with self.assertRaisesRegex(src.SourceError, "PLAN_INPUT_PROOF"):
            available.resolve_plan_available_q(store, pid, e, observations)

    def test_complete_input_count(self):
        store, plan, edges, observations, _, _ = gen.joined_fixture()
        for candidates in ([], observations * 2):
            with self.assertRaises(src.SourceError):
                available.resolve_plan_available_q(store, plan, edges, candidates)

    def test_two_ticket_order_and_no_duplicate_substitution(self):
        store, plan, edges, observations, docs, obs = gen.joined_fixture()
        m = copy.deepcopy(self.golden["manifest"]["value"])
        ticket = m["ticket_id"] + "x"
        m["ticket_id"] = ticket
        total = 0
        for row, original in zip(m["shards"], self.golden["shards"], strict=True):
            header = copy.deepcopy(original["header"])
            header["ticket_id"] = ticket
            h, payload = src.canonical(header), bytes.fromhex(original["payload_hex"])
            raw = struct.pack("<4sHHII", b"DRQ1", 1, 0, len(h), len(payload)) + h + payload
            row["leaf_id"] = src.content_id(raw, src.DOMAINS["leaf"])
            row["envelope_bytes"] = len(raw)
            store[row["leaf_id"]] = raw
            total += len(raw)
        m["total_envelope_bytes"] = total
        m["commitment_root"] = src.merkle_root([r["leaf_id"] for r in m["shards"]])
        raw = src.canonical(m)
        mid = src.content_id(raw, src.DOMAINS["manifest"])
        store[mid] = raw
        other = copy.deepcopy(obs)
        other["manifest_id"] = mid
        other["permitted_ticket_ids"] = [ticket]
        other["commitment"]["ticket_id"] = other["availability"]["ticket_id"] = ticket
        other["required_leaf_ids"] = sorted(r["leaf_id"] for r in m["shards"])
        other["availability"]["covered_leaf_ids"] = list(other["required_leaf_ids"])
        oid, raw = available.observation_bytes(other)
        store[oid] = raw
        for name, key in (
            ("ISC", "tuples"),
            ("EC", "entries"),
            ("NORM", "entries"),
            ("APC", "weights"),
            ("APC", "bucket_assignments"),
        ):
            docs[name][key].append({**docs[name][key][0], "ticket_id": ticket})
        plan, edges = plans.put_graph(store, docs)
        available.resolve_plan_available_q(store, plan, edges, [*observations, oid])
        for wrong in ([oid, *observations], observations * 2):
            with self.assertRaisesRegex(src.SourceError, "PLAN_INPUT_IDENTITY"):
                available.resolve_plan_available_q(store, plan, edges, wrong)

    def test_pinned_native_sources_and_exact_generated_evidence(self):
        boundary = json.loads((gen.FOLDER / "native-source-boundary.json").read_bytes())
        for row in boundary["files"]:
            raw = subprocess.check_output(
                ["git", "show", boundary["commit"] + ":" + row["path"]], cwd=ROOT
            )
            self.assertEqual(raw, (ROOT / row["retained_path"]).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        self.assertEqual(gen.generate(), json.loads(gen.TARGET.read_bytes()))
        self.assertEqual(gen.harness().encode(), (gen.FOLDER / "harness.cpp").read_bytes())


if __name__ == "__main__":
    unittest.main()
