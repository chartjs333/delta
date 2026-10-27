"""Public synthetic key material only; cryptographic unpredictability is not a unit test."""

import itertools
import unittest

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import generation as g
from formal.reference.seed_source import pvss as p
from formal.reference.seed_source.test_pvss import fixture


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.group, cls.seeds, cls.boot, cls.ctx = fixture()

    def make(self, context):
        raw = g.deal_body(self.group, self.boot, context, "validator-1", self.seeds["validator-1"])
        return p.sign(self.group, self.seeds["validator-1"], c._load(raw))

    def test_exact_retry_same_body_and_canonical_proof(self):
        first = self.make(self.ctx)
        self.assertEqual(first, self.make(self.ctx))
        p.verify_deal(self.group, self.boot, self.ctx, first)

    def test_cut_changes_preserve_polynomial_but_not_original_artifact(self):
        other = {**self.ctx, "source_cut_id": "sha256:" + "9" * 64}
        first, second = self.make(self.ctx), self.make(other)
        a = p.verify_deal(self.group, self.boot, self.ctx, first)
        b = p.verify_deal(self.group, self.boot, other, second)
        self.assertEqual(a.commitments, b.commitments)
        self.assertEqual(a.encrypted, b.encrypted)
        self.assertNotEqual(first, second)
        self.assertNotEqual(p.artifact_id(first), p.artifact_id(second))

    def test_all_subsets_from_generated_openings(self):
        deal = self.make(self.ctx)
        rows = tuple(
            p.sign(
                self.group,
                seed,
                c._load(g.opening_body(self.group, self.boot, self.ctx, actor, seed, deal)),
            )
            for actor, seed in self.seeds.items()
        )
        points = {
            p.reconstruct(self.group, self.boot, self.ctx, deal, subset)
            for subset in itertools.combinations(rows, 3)
        }
        self.assertEqual(len(points), 1)

    def test_wrong_existing_private_key_fails(self):
        with self.assertRaisesRegex(c.CodecError, "key correspondence"):
            g.deal_body(self.group, self.boot, self.ctx, "validator-1", self.seeds["validator-2"])

    def test_distinct_instance_changes_coefficients(self):
        other = {**self.ctx, "isc_body_id": "sha256:" + "9" * 64}
        first = p.verify_deal(self.group, self.boot, self.ctx, self.make(self.ctx))
        second = p.verify_deal(self.group, self.boot, other, self.make(other))
        self.assertNotEqual(first.commitments, second.commitments)


if __name__ == "__main__":
    unittest.main()
