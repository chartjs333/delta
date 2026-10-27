"""Synthetic original B and full seed transcript byte join; no production claims."""

import itertools
import json
import unittest

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_source import identity as isc
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import generation as gen
from formal.reference.seed_source import native as n
from formal.reference.seed_source import pvss as p
from formal.reference.seed_source.test_agreement import normal
from formal.reference.seed_source.test_pvss import fixture


class NativeSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g, cls.seeds, cls.boot, ctx = fixture()
        tuples = (
            isc.InputTuple("sha256:" + "5" * 64, "sha256:" + "6" * 64, "domain-a", "ticket-a"),
        )
        cls.b = isc.Body(
            cls.boot.formal_semantics_id,
            ctx["arithmetic_profile_id"],
            1,
            ctx["parameter_schema_id"],
            ctx["round_config_id"],
            ctx["round_id"],
            cls.boot.validator_epoch_id,
            0,
            ctx["parent_checkpoint_id"],
            isc.input_root(tuples),
            tuples,
        )
        cls.body = isc.body_preimage(cls.b)
        cls.ctx = n.context_from_body(cls.boot, cls.body, ctx["source_cut_id"])
        cls.deals = tuple(
            p.sign(cls.g, key, c._load(gen.deal_body(cls.g, cls.boot, cls.ctx, actor, key)))
            for actor, key in cls.seeds.items()
        )
        proposal, prepares, cls.commits = normal(cls.g, cls.seeds, cls.ctx, cls.deals)
        cls.originals = (*cls.deals, proposal, *prepares, *cls.commits)
        cls.opens = {
            p.artifact_id(raw): tuple(
                p.sign(
                    cls.g, key, c._load(gen.opening_body(cls.g, cls.boot, cls.ctx, actor, key, raw))
                )
                for actor, key in cls.seeds.items()
            )
            for raw in cls.deals[:3]
        }

    def candidate(self, commits=None, openings=None):
        return n.candidate_transcript(
            self.g,
            self.boot,
            self.body,
            self.ctx["source_cut_id"],
            self.originals,
            [a.identifier(x) for x in (self.commits[:3] if commits is None else commits)],
            self.opens if openings is None else openings,
        )

    def test_full_native_body_parent_and_original_deals(self):
        raw, ident, evidence = self.candidate()
        value = json.loads(raw)
        self.assertEqual(value["input_set_certificate_id"], isc.body_id(self.b))
        self.assertEqual(value["seed_profile_id"], n.profile_id())
        self.assertEqual(value["share_ids"], sorted(p.artifact_id(x) for x in self.deals[:3]))
        self.assertEqual(value["schema_version"], "2.0.0")
        self.assertEqual(ident, c.content_id("deltareduce.008.seed-transcript.v1", raw))
        self.assertEqual(tuple(x.original for x in evidence.occurrences), self.originals)

    def test_commit_and_opening_witnesses_do_not_change_native_transcript_id(self):
        expected = self.candidate()[:2]
        for indices in itertools.combinations(range(4), 3):
            openings = {
                ident: tuple(rows[i] for i in indices) for ident, rows in self.opens.items()
            }
            commits = tuple(self.commits[i] for i in indices)
            self.assertEqual(self.candidate(commits, openings)[:2], expected)

    def test_certificate_witness_c_cannot_replace_original_body_b(self):
        for signers in (tuple(self.seeds)[:3], tuple(self.seeds)[1:]):
            witness = isc.Certificate(self.b, signers)
            self.assertNotEqual(isc.certificate_id(witness), isc.body_id(self.b))
            with self.assertRaises(c.CodecError):
                n.context_from_body(
                    self.boot, isc.certificate_bytes(witness), self.ctx["source_cut_id"]
                )

    def test_trailing_original_body_bytes_rejected(self):
        with self.assertRaises(c.CodecError):
            n.context_from_body(self.boot, self.body + b"\0", self.ctx["source_cut_id"])


if __name__ == "__main__":
    unittest.main()
