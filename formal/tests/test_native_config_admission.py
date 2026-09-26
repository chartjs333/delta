"""Fail-closed CONFIG policy/vote guards and retained native evidence."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_native_config_admission as native
import native_config_admission as check
import native_policy_codec as codec
from formal_artifacts import load_json_strict
from generate_native_state_vectors import envelope


class ConfigAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = load_json_strict(native.FOLDER / "cpp-cross-check.json")
        cls.rows = {r["name"]: r for r in cls.doc["observed"]}

    def test_native_replay(self):
        native.verify_document(self.doc)

    def test_recovery_never_bypasses_invalidation_or_deadline(self):
        self.assertTrue(self.rows["recovery-without-ready"]["computed"]["admitted"])
        for name in ["recovery-invalidated", "recovery-expired"]:
            self.assertFalse(self.rows[name]["computed"]["admitted"])

    def test_parent_checked_at_vote_not_startup(self):
        rows = [r for n, r in self.rows.items() if n.startswith("parent-parent_checkpoint_id")]
        self.assertIn(dict(startup=True, admitted=False), [r["computed"] for r in rows])

    def test_source_rehash_is_not_authentication(self):
        self.assertFalse(self.rows["stale-state-root"]["computed"]["startup"])
        self.assertTrue(self.rows["rebound-state-root-not-authentication"]["computed"]["admitted"])
        self.assertFalse(self.doc["native_export_authenticated"])

    def test_all_non_config_actions_reject(self):
        p, s, _ = native.original()
        for action in range(2, 10):
            q = copy.deepcopy(p)
            q["candidates"][0]["action"] = action
            with self.subTest(action=action), self.assertRaises(ValueError):
                check.prepare(codec.encode(q), envelope(5, sorted(s.items())))

    def test_omitted_or_extra_policy_field_rejects(self):
        p, _, _ = native.original()
        for key in list(p):
            q = copy.deepcopy(p)
            del q[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                codec.encode_value("policy", q)
        p["approved"] = True
        with self.assertRaises(ValueError):
            codec.encode(p)

    def test_untrusted_runtime_shapes_reject(self):
        r = self.rows["original"]
        p, s, v = (bytes.fromhex(r[k]) for k in ["policy_hex", "state_hex", "vote_hex"])
        for k, x in [
            ("tick", -1),
            ("tick", 2**64),
            ("expected", 2**64),
            ("ready", 1),
            ("recovery", 1),
            ("invalidated", 0),
        ]:
            facts = dict(r["facts"])
            facts[k] = x
            with self.subTest(key=k, value=x), self.assertRaises(ValueError):
                check.check(p, s, v, facts)

    def test_incomplete_bytes_reject(self):
        r = self.rows["original"]
        raw = [bytes.fromhex(r[k]) for k in ["policy_hex", "state_hex", "vote_hex"]]
        for index in range(3):
            for suffix in [b"", b"\x00"]:
                altered = raw.copy()
                altered[index] = raw[index][:-1] if not suffix else raw[index] + suffix
                with self.subTest(index=index, suffix=suffix), self.assertRaises(ValueError):
                    check.check(*altered, r["facts"])

    def test_evidence_forgery_rejects(self):
        for key, value in [
            ("native_export_authenticated", True),
            ("source_commit", "f" * 40),
            ("runtime_wal_execution", True),
        ]:
            doc = copy.deepcopy(self.doc)
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                native.verify_document(doc)
        doc = copy.deepcopy(self.doc)
        doc["observed"][0]["native"]["admitted"] = False
        with self.assertRaises(ValueError):
            native.verify_document(doc)

    def test_context_does_not_encode_view_but_admission_checks_it(self):
        self.assertTrue(self.rows["view-rebound-context-unchanged"]["computed"]["admitted"])
        self.assertFalse(self.rows["candidate-view"]["computed"]["startup"])

    def test_nonempty_graph_explicitly_unsupported(self):
        r = self.rows["nonempty-abort-graph-unsupported"]
        self.assertFalse(r["supported"])
        self.assertTrue(r["native"]["startup"])
        self.assertFalse(r["computed"]["startup"])


if __name__ == "__main__":
    unittest.main()
