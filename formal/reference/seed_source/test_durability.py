"""PUBLIC synthetic keys, modeled T primitives; no real snapshot/storage claim."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as c
from formal.reference.profile_source import metadata as m
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import durability as d
from formal.reference.seed_source import generation as gen
from formal.reference.seed_source import pvss as p
from formal.reference.seed_source.test_agreement import agreement_fixture, normal, signed


def body(raw):
    return bytes.fromhex(c._load(raw)["body"])


def finish(state):
    return d.commit(d.barrier(state))


class DurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g, cls.seeds, cls.boot, cls.ctx, cls.deals = agreement_fixture()
        cls.actor = "validator-1"
        cls.proposal, cls.prepares, cls.commits = normal(cls.g, cls.seeds, cls.ctx, cls.deals)
        cls.originals = (*cls.deals, cls.proposal, *cls.prepares, *cls.commits)
        cls.empty = d.initial(
            cls.g,
            cls.boot,
            cls.ctx,
            m.raw_id(b"independent-bootstrap-fixture"),
            cls.actor,
            b"original native WAL 1,2,3,2 -- untouched",
        )
        cls.known = cls.empty
        for raw in cls.originals:
            cls.known = finish(d.append(cls.known, "RECEIVE", raw))

    def intent(self):
        return d.append(self.known, "INTENT", body(self.prepares[0]))

    def test_intent_barrier_then_sign_then_artifact_barrier_before_expose(self):
        pending = self.intent()
        ordinal = len(d.scan(pending.volatile))
        for state in (self.known, pending, d.barrier(pending)):
            with self.assertRaises(c.CodecError):
                d.sign(state, ordinal, self.seeds[self.actor])
            with self.assertRaises(c.CodecError):
                d.expose(state, ordinal)
        committed = finish(pending)
        # Signature validity cannot substitute for an own post-barrier signing action.
        with self.assertRaises(c.CodecError):
            d.append(committed, "SIGNED", self.prepares[0], intent_ordinal=ordinal)
        produced, raw = d.sign(committed, ordinal, self.seeds[self.actor])
        self.assertEqual(raw, self.prepares[0])
        appended = d.append(produced, "SIGNED", raw, intent_ordinal=ordinal)
        for state in (produced, appended, d.barrier(appended)):
            with self.assertRaises(c.CodecError):
                d.expose(state, ordinal)
        ready = finish(appended)
        self.assertEqual(d.expose(ready, ordinal).exposed, (raw,))
        self.assertEqual(ready.native_wal, self.empty.native_wal)

    def test_retry_keeps_original_ordinals_and_occurrences(self):
        ready = finish(self.intent())
        ordinal = len(d.scan(ready.committed))
        produced, raw = d.sign(ready, ordinal, self.seeds[self.actor])
        ready = finish(d.append(produced, "SIGNED", raw, intent_ordinal=ordinal))
        retry = d.append(ready, "INTENT", body(self.prepares[0]))
        self.assertIs(retry, ready)
        self.assertIs(d.append(ready, "SIGNED", raw, intent_ordinal=ordinal), ready)
        exposed = d.expose(d.expose(ready, ordinal), ordinal)
        self.assertEqual(exposed.exposed, (raw, raw))
        self.assertEqual(exposed.committed, ready.committed)
        delivered = finish(d.append(finish(d.append(ready, "RECEIVE", b"invalid")), "RECEIVE", raw))
        self.assertEqual(delivered.inspect().knowledge, (*self.originals, raw, b"invalid", raw))
        self.assertEqual(len(delivered.inspect().records), len(ready.inspect().records) + 2)

    def test_open_requires_original_commit_quorum_before_intent_and_sign(self):
        original = gen.opening_body(
            self.g, self.boot, self.ctx, self.actor, self.seeds[self.actor], self.deals[0]
        )
        refs = tuple(a.identifier(raw) for raw in self.commits[:3])
        for state, witnesses in (
            (self.empty, refs),
            (self.known, ()),
            (self.known, refs[:2]),
            (self.known, (refs[0],) * 3),
        ):
            with self.assertRaises(c.CodecError):
                d.append(state, "INTENT", original, commit_ids=witnesses)
        state = finish(d.append(self.known, "INTENT", original, commit_ids=refs))
        ordinal = len(d.scan(state.committed))
        state, raw = d.sign(state, ordinal, self.seeds[self.actor])
        state = finish(d.append(state, "SIGNED", raw, intent_ordinal=ordinal))
        self.assertEqual(
            p.verify_open(
                self.g, self.boot, self.ctx, self.deals[0], d.expose(state, ordinal).exposed[-1]
            ).index,
            1,
        )
        # Unselected fourth original dealer cannot be opened by this quorum.
        other = gen.opening_body(
            self.g, self.boot, self.ctx, self.actor, self.seeds[self.actor], self.deals[3]
        )
        with self.assertRaises(c.CodecError):
            d.append(state, "INTENT", other, commit_ids=refs)

    def test_all_crash_regions_preserve_originals_and_need_recovery_barrier(self):
        appended = self.intent()
        base, target = self.known.committed, appended.volatile
        ordinal = len(d.scan(target))
        for surviving, phase in (
            (base, "RECOVERY_VERIFIED"),
            (target, "RECOVERY_VERIFIED"),
            (base + target[len(base) : len(base) + 9], "BLOCKED"),
            (base + b"wrong", "BLOCKED"),
        ):
            recovered = d.recover(d.crash(appended, surviving))
            self.assertEqual(recovered.phase, phase)
            self.assertEqual(recovered.volatile, surviving)
            self.assertEqual(recovered.artifacts, appended.artifacts)
            self.assertEqual(recovered.native_wal, self.empty.native_wal)
            with self.assertRaises(c.CodecError):
                d.sign(recovered, ordinal, self.seeds[self.actor])
            if phase == "RECOVERY_VERIFIED":
                ready = finish(recovered)
                self.assertEqual(ready.committed, surviving)
                if surviving == target:
                    _, raw = d.sign(ready, ordinal, self.seeds[self.actor])
                    self.assertEqual(raw, self.prepares[0])
        durable = d.barrier(appended)
        with self.assertRaises(c.CodecError):
            d.crash(durable, base)  # acknowledged bytes cannot disappear under T

    def test_crash_after_sign_loses_only_unretained_effect_then_exact_replay(self):
        state = finish(self.intent())
        ordinal = len(d.scan(state.committed))
        produced, raw = d.sign(state, ordinal, self.seeds[self.actor])
        recovered = finish(d.recover(d.crash(produced, produced.stable)))
        self.assertEqual(recovered.produced, ())
        with self.assertRaises(c.CodecError):
            d.expose(recovered, ordinal)
        recovered, again = d.sign(recovered, ordinal, self.seeds[self.actor])
        self.assertEqual(again, raw)
        state = finish(d.append(recovered, "SIGNED", again, intent_ordinal=ordinal))
        state = finish(d.recover(d.crash(state, state.stable)))
        self.assertEqual(d.expose(state, ordinal).exposed[-1], raw)

    def test_highest_prepared_and_old_view_guards_survive_recovery(self):
        status = signed(
            self.g,
            self.seeds,
            self.ctx,
            self.actor,
            "STATUS",
            1,
            prepared_proposal=a.identifier(self.proposal),
            prepares=[a.identifier(x) for x in self.prepares[:3]],
        )
        state = finish(d.append(self.known, "INTENT", body(status)))
        state = finish(d.recover(d.crash(state, state.stable)))
        self.assertEqual(state.inspect().agreement_view, 1)
        with self.assertRaises(c.CodecError):
            d.append(state, "INTENT", body(self.prepares[0]))
        false_status = signed(
            self.g, self.seeds, self.ctx, self.actor, "STATUS", 2, prepared_proposal="", prepares=[]
        )
        with self.assertRaises(c.CodecError):
            d.append(state, "INTENT", body(false_status))

    def test_no_missing_payload_or_shorter_knowledge_recovery(self):
        missing = replace(self.known, artifacts=self.known.artifacts[:-1])
        with self.assertRaises(c.CodecError):
            missing.inspect()
        rows = d.scan(self.known.committed)
        last = d.decode(rows[-1])
        last["knowledge_count"] = "0"
        last["knowledge_id"] = d.knowledge_id(())
        tampered = b"".join(d.frame(raw) for raw in rows[:-1]) + d.frame(m.canonical(last))
        with self.assertRaises(c.CodecError):
            self.known.inspect(tampered)

    def test_deal_private_derivation_not_arbitrary_valid_algebra(self):
        # The fixture's valid polynomial differs from the selected honest KDF.
        wrong = finish(d.append(self.empty, "INTENT", body(self.deals[0])))
        with self.assertRaises(c.CodecError):
            d.sign(wrong, 1, self.seeds[self.actor])
        original = gen.deal_body(self.g, self.boot, self.ctx, self.actor, self.seeds[self.actor])
        state = finish(d.append(self.empty, "INTENT", original))
        state, raw = d.sign(state, 1, self.seeds[self.actor])
        state = finish(d.append(state, "SIGNED", raw, intent_ordinal=1))
        self.assertEqual(
            p.verify_deal(self.g, self.boot, self.ctx, d.expose(state, 1).exposed[-1]).actor,
            self.actor,
        )
        with self.assertRaises(c.CodecError):
            d.append(state, "INTENT", body(self.deals[0]))

    def test_repeated_crash_cannot_promote_unknown_parseable_tail(self):
        base = finish(d.append(self.empty, "RECEIVE", b"bad"))
        intent = gen.deal_body(self.g, self.boot, self.ctx, self.actor, self.seeds[self.actor])
        pending = d.append(base, "INTENT", intent)
        row = d.decode(d.scan(pending.volatile)[-1])
        row.update(type_name="RECEIVE", payload_raw_id=m.raw_id(b"bad"), payload_bytes="3")
        foreign = base.stable + d.frame(m.canonical(row))
        self.assertLessEqual(len(foreign), len(pending.volatile))
        self.assertNotEqual(foreign, pending.volatile)
        # Parsing success cannot replace the original attempted append.
        self.assertEqual(pending.inspect(foreign).knowledge, (b"bad", b"bad"))
        for recover_between in (False, True):
            crashed = d.crash(pending, foreign)
            for _ in range(4):
                if recover_between:
                    crashed = d.recover(crashed)
                    self.assertEqual(crashed.phase, "BLOCKED")
                crashed = d.crash(crashed, foreign)
                self.assertEqual(crashed.recovery_base, base.stable)
                self.assertEqual(crashed.recovery_target, pending.volatile)
                self.assertEqual(crashed.volatile, foreign)
            rejected = d.recover(crashed)
            self.assertEqual(rejected.phase, "BLOCKED")
            with self.assertRaises(c.CodecError):
                d.barrier(rejected)

    def test_recovery_origin_survives_until_verified_commit_only(self):
        pending = self.intent()
        recovered = d.recover(d.crash(pending, pending.volatile))
        for stage in (recovered, d.barrier(recovered)):
            again = d.crash(stage, stage.volatile)
            self.assertEqual(again.recovery_base, self.known.stable)
            self.assertEqual(again.recovery_target, pending.volatile)
            ready = finish(d.recover(again))
            self.assertFalse(ready.recovery_active)
            next_append = d.append(ready, "RECEIVE", b"next original occurrence")
            next_crash = d.crash(next_append, ready.stable)
            self.assertEqual(next_crash.recovery_base, ready.stable)
            self.assertEqual(next_crash.recovery_target, next_append.volatile)


if __name__ == "__main__":
    unittest.main()
