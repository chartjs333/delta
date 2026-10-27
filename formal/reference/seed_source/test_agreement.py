"""Synthetic evidence checks; no claim these are complete authenticated snapshots."""

import itertools
import unittest

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import pvss as p
from formal.reference.seed_source.test_pvss import fixture, make_deal, make_open


def signed(group, seeds, ctx, actor, kind, view, **fields):
    return a.sign(
        group,
        seeds[actor],
        dict(
            profile=a.PROFILE,
            kind=kind,
            instance=a.instance(ctx),
            actor=actor,
            agreement_view=str(view),
            **fields,
        ),
    )


def agreement_fixture():
    group, seeds, boot, ctx = fixture()
    deals = tuple(
        make_deal(group, seeds, boot, ctx, coefficients=(7 + 10 * i, 11, 13), actor=actor)
        for i, actor in enumerate(seeds)
    )
    return group, seeds, boot, ctx, deals


def normal(group, seeds, ctx, deals, view=0, statuses=()):
    ids = [p.artifact_id(raw) for raw in deals[:3]]
    proposal = signed(
        group,
        seeds,
        ctx,
        list(seeds)[view % 4],
        "PROPOSE",
        view,
        deals=ids,
        new_view=[a.identifier(raw) for raw in statuses],
    )
    proposal_id = a.identifier(proposal)
    prepares = tuple(
        signed(group, seeds, ctx, actor, "PREPARE", view, proposal_id=proposal_id)
        for actor in seeds
    )
    commits = tuple(
        signed(
            group,
            seeds,
            ctx,
            actor,
            "COMMIT",
            view,
            proposal_id=proposal_id,
            prepares=[a.identifier(x) for x in prepares[:3]],
        )
        for actor in seeds
    )
    return proposal, prepares, commits


class AgreementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g, cls.seeds, cls.boot, cls.ctx, cls.deals = agreement_fixture()
        cls.proposal, cls.prepares, cls.commits = normal(cls.g, cls.seeds, cls.ctx, cls.deals)
        cls.originals = (*cls.deals, cls.proposal, *cls.prepares, *cls.commits)
        cls.opens = {
            p.artifact_id(raw): tuple(
                make_open(cls.g, cls.seeds, cls.boot, cls.ctx, raw, actor) for actor in cls.seeds
            )
            for raw in cls.deals[:3]
        }

    def evidence(self, raws=None):
        return a.Evidence(self.g, self.boot, self.ctx, self.originals if raws is None else raws)

    def test_original_positions_and_duplicate_occurrences_retained(self):
        originals = (*self.originals, self.prepares[0], b"bad", self.prepares[0])
        evidence = self.evidence(originals)
        self.assertEqual(tuple(x.original for x in evidence.occurrences), originals)
        self.assertEqual(
            tuple(x.position for x in evidence.occurrences), tuple(range(len(originals)))
        )
        self.assertIsNotNone(evidence.occurrences[-2].error)
        self.assertIsNone(evidence.occurrences[-1].error)

    def test_commit_witness_and_reconstruction_subset_independence(self):
        outputs = set()
        for actors in itertools.combinations(range(4), 3):
            chosen = {ident: tuple(rows[i] for i in actors) for ident, rows in self.opens.items()}
            for cert in itertools.combinations(self.commits, 3):
                value, evidence = a.reconstruct_candidate(
                    self.g,
                    self.boot,
                    self.ctx,
                    self.originals,
                    [a.identifier(x) for x in cert],
                    chosen,
                )
                self.assertTrue(all(row.error is None for row in evidence.occurrences))
                outputs.add(value)
        self.assertEqual(len(outputs), 1)

    def test_new_view_preserves_highest_prepared_candidate(self):
        statuses = tuple(
            signed(
                self.g,
                self.seeds,
                self.ctx,
                actor,
                "STATUS",
                1,
                prepared_proposal=a.identifier(self.proposal),
                prepares=[a.identifier(x) for x in self.prepares[:3]],
            )
            for actor in list(self.seeds)[:3]
        )
        proposal, prepares, commits = normal(self.g, self.seeds, self.ctx, self.deals, 1, statuses)
        originals = (*self.originals, *statuses, proposal, *prepares, *commits)
        self.assertTrue(all(x.error is None for x in self.evidence(originals).occurrences))
        wrong = signed(
            self.g,
            self.seeds,
            self.ctx,
            "validator-2",
            "PROPOSE",
            1,
            deals=[p.artifact_id(x) for x in self.deals[1:]],
            new_view=[a.identifier(x) for x in statuses],
        )
        self.assertIn("highest prepared", self.evidence((*originals, wrong)).occurrences[-1].error)

    def test_missing_and_duplicate_witnesses_cannot_commit(self):
        for refs in (
            [a.identifier(x) for x in self.commits[:2]],
            [a.identifier(self.commits[0])] * 3,
        ):
            with self.assertRaises(c.CodecError):
                self.evidence().committed(refs)

    def test_future_reference_is_not_retroactively_accepted(self):
        raws = (*self.deals, self.prepares[0], self.proposal, self.prepares[0])
        out = self.evidence(raws)
        self.assertIsNotNone(out.occurrences[4].error)
        self.assertIsNone(out.occurrences[6].error)
        self.assertEqual(out.occurrences[4].original, out.occurrences[6].original)

    def test_wrong_leader_and_relabelled_signature_rejected(self):
        bad = signed(
            self.g,
            self.seeds,
            self.ctx,
            "validator-2",
            "PROPOSE",
            0,
            deals=[p.artifact_id(x) for x in self.deals[:3]],
            new_view=[],
        )
        self.assertIn("leader", self.evidence((*self.deals, bad)).occurrences[-1].error)
        outer = c._load(self.proposal)
        body = c._load(bytes.fromhex(outer["body"]))
        body["agreement_view"] = "4"
        outer["body"] = c._json(body).hex()
        self.assertIn(
            "signature", self.evidence((*self.originals, c._json(outer))).occurrences[-1].error
        )

    def test_absent_opening_is_incomplete_not_a_seed_fallback(self):
        broken = dict(self.opens)
        broken.pop(next(iter(broken)))
        with self.assertRaises(c.CodecError):
            a.reconstruct_candidate(
                self.g,
                self.boot,
                self.ctx,
                self.originals,
                [a.identifier(x) for x in self.commits[:3]],
                broken,
            )

    def test_invalid_actor_type_remains_an_occurrence(self):
        value = dict(
            profile=a.PROFILE,
            kind="PREPARE",
            instance=a.instance(self.ctx),
            actor=[],
            agreement_view="0",
            proposal_id=a.identifier(self.proposal),
        )
        raw = a.sign(self.g, self.seeds["validator-1"], value)
        out = self.evidence((*self.originals, raw))
        self.assertIsNotNone(out.occurrences[-1].error)
        self.assertEqual(out.occurrences[-1].original, raw)


if __name__ == "__main__":
    unittest.main()
