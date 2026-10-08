"""Original index/cut composition; synthetic data, not a complete legal prefix."""

import copy
import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix as s
from formal.reference.profile_source import test_configuration_qc as config_fixture
from formal.reference.profile_source.test_metadata import Package, ref


class SourcePrefixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_fixture.ConfigQcTests.setUpClass()

    def setUp(self):
        self.config = config_fixture.ConfigQcTests()
        self.config.setUp()
        self.p = Package()
        f = self.config
        events = [("ACT-CONFIG-PROPOSE", f.raw, [f.f.declaration], [])]
        events += [("ACT-MESSAGE-DELIVER", b"invalid-original", [], [])]
        events += [("ACT-MESSAGE-DELIVER", d.original_artifact, [], [0]) for d in f.delivered]
        # Same original frame occurs twice and stays at two original positions.
        events += [("ACT-MESSAGE-DELIVER", f.delivered[0].original_artifact, [], [0])]
        events += [("ACT-CONFIG-FINALIZE", qc.encode(f.qc), [], [0, 2, 3, 4, 5])]
        events += [("ACT-ARTIFACT-LOSE", b"original-loss-observation", [], [7])]
        self.p.index["events"] = [
            {
                "actor_id": "original-receiver",
                "action_id": action,
                "original_ref": ref(raw),
                "input_refs": list(map(ref, inputs)),
                "dependencies": list(map(str, deps)),
            }
            for action, raw, inputs, deps in events
        ]
        raws = set(self.p.raw)
        for _, raw, inputs, _ in events:
            raws.update([raw, *inputs])
        self.p.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in raws))
        table = sorted(map(ref, raws), key=lambda r: r["content_id"])
        self.p.index["artifacts"] = table
        self.p.manifest.update(
            artifacts=table, cut_event_index="7", target_event_index=str(len(events))
        )
        self.rebind()

    def rebind(self):
        self.p.index_raw = m.canonical(self.p.index)
        self.p.manifest["source_index_ref"] = ref(self.p.index_raw)
        self.p.trust = replace(self.p.trust, source_index_raw_sha256=m.raw_id(self.p.index_raw))

    def check(self):
        prefix = s.materialize(self.p.check())
        f = self.config.f
        return s.configuration_prefix(prefix, f.boot, f.storage_boot, f.backend)

    def test_cut_and_target_derived_from_whole_original_index(self):
        result = self.check()
        self.assertEqual(result.cut.finalized, ())
        self.assertEqual(len(result.target.finalized), 1)
        self.assertEqual(result.target.finalized[0].source.index, 7)
        self.assertEqual(result.target.events[2].original, result.target.events[6].original)
        self.assertNotEqual(result.target.events[2].index, result.target.events[6].index)
        self.assertEqual([event.index for event in result.other_actions], [8])
        self.assertEqual(result.target.events[-1].original, b"original-loss-observation")
        self.assertEqual(result.source.events[7].dependencies, (0, 2, 3, 4, 5))

    def test_original_cut_cannot_borrow_later_delivery(self):
        # Move finalization before the fourth signature while preserving all
        # original artifacts. The attempted four-signer QC is rejected there.
        events = self.p.index["events"]
        events[5], events[7] = events[7], events[5]
        events[5]["dependencies"] = ["0", "2", "3", "4"]
        self.rebind()
        result = self.check()
        self.assertEqual(result.target.finalized, ())
        self.assertEqual(len(result.target.received), 5)

    def test_original_inputs_and_dependencies_not_sorted_or_invented(self):
        original = self.p.index["events"][0]
        original["input_refs"] = [ref(b"configuration"), *original["input_refs"] * 2]
        self.rebind()
        result = self.check()
        self.assertEqual(
            result.source.events[0].inputs,
            (b"configuration", self.config.f.declaration, self.config.f.declaration),
        )
        self.p.index["events"][0]["dependencies"] = ["1"]
        self.rebind()
        with self.assertRaisesRegex(CodecError, "backward"):
            self.check()

    def test_artifact_digest_is_not_an_original_event_occurrence(self):
        # Keep the QC, all signatures and E in the artifact inventory, but no
        # original proposal event. A hash/signature graph cannot replace it.
        self.p.index["events"][0]["action_id"] = "OTHER-ORIGINAL-OBSERVATION"
        self.rebind()
        result = self.check()
        self.assertEqual(result.target.finalized, ())
        self.assertEqual([e.index for e in result.other_actions], [0, 8])

    def test_rejected_config_attempt_is_retained_without_inventing_proposal(self):
        # Missing original E makes the attempt inadmissible. Later authentic
        # signatures cannot supply the missing proposal or delete its position.
        self.p.index["events"][0]["input_refs"] = []
        self.rebind()
        result = self.check()
        self.assertEqual(result.target.proposals, ())
        self.assertEqual(result.target.finalized, ())
        self.assertEqual(len(result.target.events), len(self.p.index["events"]))
        self.assertEqual(result.target.events[0].original, self.config.raw)

    def test_receiver_position_does_not_manufacture_w1_peer_identity(self):
        result = self.check()
        first = result.target.received[0]
        self.assertEqual(first.source.actor, "original-receiver")
        self.assertIs(type(first.original), qc.SignedOccurrence)
        self.assertEqual(first.original.index, first.source.index)
        self.assertEqual(first.original.original_artifact, first.source.original)
        self.assertFalse(hasattr(first.original, "event"))

    def test_importer_cannot_rewrite_the_independent_source_index(self):
        changed = copy.deepcopy(self.p.index)
        changed["events"].pop()
        raw = m.canonical(changed)
        manifest = {**self.p.manifest, "source_index_ref": ref(raw)}
        with self.assertRaisesRegex(CodecError, "independently retained original source inventory"):
            m.check_metadata(self.p.trust, m.canonical(manifest), raw, self.p.artifacts)

    def retain_index(self, index, extra=()):
        raw = m.canonical(index)
        originals = dict(self.p.artifacts)
        originals.update((m.raw_id(value), value) for value in (raw, *extra))
        self.p.artifacts = tuple(sorted(originals.items()))
        table = sorted((ref(value) for value in originals.values()), key=lambda r: r["content_id"])
        self.p.index["artifacts"] = table
        self.p.manifest["artifacts"] = table
        self.rebind()
        return raw

    def earlier(self):
        old = copy.deepcopy(self.p.index)
        old["events"] = old["events"][:7]
        return old

    def bind_earlier(self, raw, *, cut=6, before=7, identifier=None):
        prefix = s.materialize(self.p.check())
        return s.retained_cut(
            prefix, raw, identifier or m.document_id(raw, "SOURCE_INDEX"), cut, before
        )

    def test_w1_uses_retained_prior_index_without_self_referential_later_index(self):
        raw = self.retain_index(self.earlier())
        result = self.bind_earlier(raw)
        self.assertNotEqual(result.original_index, self.p.index_raw)
        self.assertNotEqual(result.index_id, m.document_id(self.p.index_raw, "SOURCE_INDEX"))
        self.assertEqual(len(result.events), result.inclusive_cut + 1)
        self.assertEqual(result.events[2].original, result.events[6].original)
        self.assertEqual([e.index for e in result.events], list(range(7)))
        self.assertEqual(result.journals[0][1], b"journal")
        # Inclusive W1 cut 5 means exactly six events, not five or seven.
        self.assertEqual(len(self.bind_earlier(raw, cut=5).events), 6)

    def test_w1_cannot_borrow_future_index_or_rewrite_original_prefix(self):
        future = copy.deepcopy(self.p.index)
        raw = self.retain_index(future)
        with self.assertRaisesRegex(CodecError, "precedes"):
            self.bind_earlier(raw)
        for key, value in (("actor_id", "another-receiver"), ("dependencies", ["1"])):
            with self.subTest(key=key):
                old = self.earlier()
                old["events"][2][key] = value
                raw = self.retain_index(old)
                with self.assertRaisesRegex(CodecError, "whole original event prefix"):
                    self.bind_earlier(raw)

    def test_w1_requires_actual_retained_index_and_its_document_identity(self):
        raw = m.canonical(self.earlier())
        with self.assertRaisesRegex(CodecError, "independently retained original"):
            self.bind_earlier(raw)
        self.retain_index(self.earlier())
        with self.assertRaisesRegex(CodecError, "domain-separated"):
            self.bind_earlier(raw, identifier=m.raw_id(raw))

    def test_w1_no_delivery_collapse_or_fabricated_journal_prefix(self):
        old = self.earlier()
        old["events"].pop(2)
        # Keep well-formed backwards dependency coordinates, not a malformed
        # index that would fail before the original-prefix comparison.
        raw = self.retain_index(old)
        with self.assertRaisesRegex(CodecError, "whole original event prefix"):
            self.bind_earlier(raw, cut=5)
        old = self.earlier()
        bad = b"ourn"
        old["original_journal_refs"][0]["ref"] = ref(bad)
        old["artifacts"] = sorted([*old["artifacts"], ref(bad)], key=lambda row: row["content_id"])
        raw = self.retain_index(old, (bad,))
        with self.assertRaisesRegex(CodecError, "journal byte/sequence prefix"):
            self.bind_earlier(raw)


if __name__ == "__main__":
    unittest.main()
