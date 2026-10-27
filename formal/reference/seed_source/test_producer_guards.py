"""Pure guard regressions over synthetic prefixes, not full source snapshots."""

import unittest

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import producer_guards as g
from formal.reference.seed_source import pvss as p
from formal.reference.seed_source.test_agreement import agreement_fixture, normal, signed


def unsigned(raw):
    return bytes.fromhex(c._load(raw)["body"])


class ProducerGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.group, cls.seeds, cls.boot, cls.ctx, cls.deals = agreement_fixture()
        cls.proposal, cls.prepares, cls.commits = normal(cls.group, cls.seeds, cls.ctx, cls.deals)
        cls.prefix = (*cls.deals, cls.proposal, *cls.prepares)

    def run_guard(self, intents, originals=None, actor="validator-2"):
        return g.guard_sequence(
            self.group,
            self.boot,
            self.ctx,
            actor,
            self.prefix if originals is None else originals,
            tuple(intents),
        )

    def status(self, view=1, prepared=True):
        return signed(
            self.group,
            self.seeds,
            self.ctx,
            "validator-2",
            "STATUS",
            view,
            prepared_proposal=a.identifier(self.proposal) if prepared else "",
            prepares=[a.identifier(x) for x in self.prepares[:3]] if prepared else [],
        )

    def test_highest_prepared_is_computed_and_cannot_be_omitted(self):
        cut = len(self.prefix)
        ok = self.run_guard([g.Intent(unsigned(self.status()), cut)])
        self.assertEqual(ok.view, 1)
        with self.assertRaisesRegex(c.CodecError, "highest prepared"):
            self.run_guard([g.Intent(unsigned(self.status(prepared=False)), cut)])

    def test_conflicting_prepare_for_one_view_is_rejected(self):
        other = signed(
            self.group,
            self.seeds,
            self.ctx,
            "validator-1",
            "PROPOSE",
            0,
            deals=[p.artifact_id(x) for x in self.deals[1:]],
            new_view=[],
        )
        vote = signed(
            self.group,
            self.seeds,
            self.ctx,
            "validator-2",
            "PREPARE",
            0,
            proposal_id=a.identifier(other),
        )
        prefix = (*self.prefix, other)
        with self.assertRaisesRegex(c.CodecError, "conflicting original intent"):
            self.run_guard(
                [
                    g.Intent(unsigned(self.prepares[1]), len(prefix)),
                    g.Intent(unsigned(vote), len(prefix)),
                ],
                prefix,
            )

    def test_new_old_view_intent_rejected_but_exact_retry_retained(self):
        cut = len(self.prefix)
        prepare = g.Intent(unsigned(self.prepares[1]), cut)
        status = g.Intent(unsigned(self.status()), cut)
        out = self.run_guard([prepare, status, prepare])
        self.assertEqual(out.intents, (prepare, status, prepare))
        with self.assertRaisesRegex(c.CodecError, "old/future view"):
            self.run_guard([status, g.Intent(unsigned(self.commits[1]), cut)])

    def test_unknown_or_decreasing_cut_rejected(self):
        cut = len(self.prefix)
        with self.assertRaisesRegex(c.CodecError, "knowledge cut"):
            self.run_guard([g.Intent(unsigned(self.status()), cut + 1)])
        with self.assertRaisesRegex(c.CodecError, "knowledge cut"):
            self.run_guard(
                [
                    g.Intent(unsigned(self.prepares[1]), cut),
                    g.Intent(unsigned(self.prepares[1]), cut - 1),
                ]
            )

    def test_foreign_signer_is_not_an_own_intent(self):
        with self.assertRaisesRegex(c.CodecError, "own original"):
            self.run_guard([g.Intent(unsigned(self.prepares[0]), len(self.prefix))])

    def test_full_inventory_retained_with_no_or_partial_intents(self):
        original = (*self.prefix, b"malformed", self.prefix[0])
        for intents in ([], [g.Intent(unsigned(self.prepares[1]), len(self.prefix))]):
            self.assertEqual(self.run_guard(intents, original).retained_knowledge, original)


if __name__ == "__main__":
    unittest.main()
