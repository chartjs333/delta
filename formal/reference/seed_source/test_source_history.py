"""Original-source mutations; PUBLIC synthetic keys, no real T/production claim."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto import codec as c
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source.source_prefix import Event
from formal.reference.seed_source import durability as d
from formal.reference.seed_source import generation as gen
from formal.reference.seed_source import source_history as s
from formal.reference.seed_source.test_agreement import agreement_fixture, normal, signed


def ref(raw):
    return dict(
        schema_version="1.0.0",
        schema_id="SCHEMA-SEED-SOURCE-TEST-V1",
        media_type="application/octet-stream",
        byte_length=str(len(raw)),
        content_id=m.raw_id(raw),
        locator="originals/" + m.raw_id(raw)[7:],
    )


def event(index, actor, action, raw, inputs=(), dependencies=()):
    descriptor = m.canonical(
        dict(
            actor_id=actor,
            action_id=action,
            original_ref=ref(raw),
            input_refs=list(map(ref, inputs)),
            dependencies=list(map(str, dependencies)),
        )
    )
    return Event(index, actor, action, raw, inputs, dependencies, descriptor)


def command(state, operation, ordinal=0, commits=()):
    return m.canonical(
        dict(
            type_name="SEED_SOURCE_STEP",
            schema_version="1",
            profile_id=m.PROFILE,
            bootstrap_id=state.bootstrap_id,
            instance_id=d.instance_id(state.expected),
            operation=operation,
            intent_ordinal=str(ordinal),
            commit_ids=list(commits),
        )
    )


class Capture:
    """Fixture producer, only PUBLIC synthetic seed supplied explicitly to sign."""

    def __init__(self, initial):
        self.state, self.events = initial, []

    def step(self, operation, inputs=(), ordinal=0, commits=()):
        raw = command(self.state, operation, ordinal, commits)
        self.events.append(event(len(self.events), self.state.actor, s.ACTION, raw, inputs))
        self.state = s.invoke(self.state, s.invocation(raw), inputs)
        return self

    def record(self, operation, payload, ordinal=0, commits=()):
        return self.step(operation, (payload,), ordinal, commits).step("BARRIER").step("COMMIT")

    def sign(self, ordinal, public_test_seed):
        _, raw = d.sign(self.state, ordinal, public_test_seed)
        return self.step("SIGN", (raw,), ordinal), raw


class SourceHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.group, cls.seeds, cls.boot, cls.ctx, cls.deals = agreement_fixture()
        cls.actor = "validator-1"
        cls.bootstrap_id = m.raw_id(b"independently provisioned synthetic bootstrap")
        cls.native_wal = b"original native slots 1,2,3,2"
        cls.empty = d.initial(
            cls.group, cls.boot, cls.ctx, cls.bootstrap_id, cls.actor, cls.native_wal
        )
        cls.unsigned = gen.deal_body(cls.group, cls.boot, cls.ctx, cls.actor, cls.seeds[cls.actor])
        capture = Capture(cls.empty).record("INTENT", cls.unsigned)
        capture, cls.signed = capture.sign(1, cls.seeds[cls.actor])
        capture.record("SIGNED", cls.signed, 1).step("EXPOSE", ordinal=1)
        cls.capture = capture

    def fold(self, events=None, cuts=()):
        return s.fold(
            self.group,
            self.boot,
            self.ctx,
            self.bootstrap_id,
            self.actor,
            self.native_wal,
            tuple(self.capture.events if events is None else events),
            cuts,
        )

    def test_complete_original_chain_and_every_prefix_cut(self):
        events = tuple(self.capture.events)
        trace = self.fold(cuts=tuple(range(len(events) + 1)))
        self.assertEqual(trace.events, events)
        self.assertEqual([x.index for x in trace.outcomes], list(range(len(events))))
        self.assertTrue(all(x.disposition == "accepted" for x in trace.outcomes))
        self.assertEqual(trace.state, self.capture.state)
        self.assertEqual(trace.state.native_wal, self.native_wal)
        self.assertEqual(trace.cuts[0][1], self.empty)
        for count, state in trace.cuts:
            self.assertEqual(self.fold(events[:count]).state, state)

    def test_receive_does_not_supply_own_signing_action(self):
        capture = Capture(self.empty).record("INTENT", self.unsigned)
        capture.record("RECEIVE", self.signed)
        rows = list(capture.events)
        rows.append(
            event(
                len(rows), self.actor, s.ACTION, command(capture.state, "SIGNED", 1), (self.signed,)
            )
        )
        trace = self.fold(rows)
        self.assertEqual(trace.outcomes[-1].disposition, "rejected")
        self.assertEqual(trace.state, capture.state)
        self.assertEqual(trace.state.inspect().signed, ())
        self.assertEqual(trace.state.inspect().knowledge, (self.signed,))

    def test_missing_barrier_cannot_be_replaced_by_valid_signature(self):
        rows = [self.capture.events[0]]
        rows.append(event(1, self.actor, s.ACTION, command(self.empty, "SIGN", 1), (self.signed,)))
        rows.append(event(2, self.actor, s.ACTION, command(self.empty, "EXPOSE", 1)))
        trace = self.fold(rows)
        self.assertEqual(
            [o.disposition for o in trace.outcomes],
            ["accepted", "unresolved_original_output", "rejected"],
        )
        self.assertEqual(trace.unresolved, (1,))
        self.assertEqual(trace.state.exposed, ())

    def test_retries_invalid_receive_and_unrelated_events_keep_original_positions(self):
        capture = Capture(self.capture.state)
        capture.record("RECEIVE", b"invalid")
        capture.record("RECEIVE", b"invalid")
        capture.step("INTENT", (self.unsigned,)).step("EXPOSE", ordinal=1)
        rows = list(self.capture.events)
        for old in capture.events:
            rows.append(event(len(rows), old.actor, old.action, old.original, old.inputs))
        rows.append(event(len(rows), "other-actor", "ACT-ARTIFACT-LOSE", b"original loss"))
        trace = self.fold(rows)
        self.assertEqual(len(trace.events), len(rows))
        self.assertEqual(trace.events[-1].original, b"original loss")
        self.assertEqual(trace.outcomes[-1].disposition, "other_original_source")
        self.assertEqual(trace.state.exposed, (self.signed, self.signed))
        self.assertEqual(trace.state.inspect().knowledge[-2:], (b"invalid", b"invalid"))
        self.assertEqual(len(trace.state.inspect().intents), 1)

    def test_forged_materialized_descriptor_input_or_future_dependency_rejected(self):
        first = self.capture.events[0]
        for bad in (
            replace(first, inputs=(b"substituted",)),
            replace(first, actor="validator-2"),
            replace(first, index=1),
            replace(first, dependencies=(1,)),
            event(0, first.actor, first.action, first.original, first.inputs, (1,)),
        ):
            with self.assertRaises(c.CodecError):
                self.fold([bad])

    def test_unknown_invocation_is_unresolved_not_lawful_noop(self):
        for op in ("FUTURE_OPERATION", []):
            row = m.load(command(self.empty, "BARRIER"))
            row["operation"] = op
            trace = self.fold([event(0, self.actor, s.ACTION, m.canonical(row))])
            self.assertEqual(trace.unresolved, (0,))
            self.assertEqual(trace.state, self.empty)

    def test_foreign_context_rejected_and_original_bytes_retained(self):
        row = m.load(command(self.empty, "INTENT"))
        row["bootstrap_id"] = m.raw_id(b"self elected")
        original = event(0, self.actor, s.ACTION, m.canonical(row), (self.unsigned,))
        trace = self.fold([original])
        self.assertEqual(trace.events, (original,))
        self.assertEqual(trace.outcomes[0].disposition, "rejected")
        self.assertEqual(trace.state, self.empty)

    def test_crash_surviving_unknown_bytes_and_missing_journal_never_disappear(self):
        capture = Capture(self.empty).step("INTENT", (self.unsigned,))
        surviving = capture.state.volatile[:9]
        capture.step("CRASH", (surviving,)).step("RECOVER")
        capture.step("CRASH", (surviving,)).step("RECOVER")
        trace = self.fold(capture.events)
        self.assertEqual(trace.state.phase, "BLOCKED")
        self.assertEqual(trace.state.volatile, surviving)
        self.assertEqual(trace.state.exposed, ())
        original = (self.actor, s.journal_id(self.ctx), surviving)
        self.assertEqual(s.check_journal_tip(trace, self.actor, self.ctx, (original,)), surviving)
        for journals in ((), (original, original), ((self.actor, s.journal_id(self.ctx), b""),)):
            with self.assertRaises(c.CodecError):
                s.check_journal_tip(trace, self.actor, self.ctx, journals)

    def test_faulty_remote_deal_not_required_to_match_honest_private_kdf(self):
        # Public validity and lawful Byzantine domain do not require all dealers
        # to use the honest private generator. No coins-valid claim is made here.
        proposal, _, _ = normal(self.group, self.seeds, self.ctx, self.deals)
        capture = Capture(self.empty)
        for raw in (*self.deals, proposal):
            capture.record("RECEIVE", raw)
        trace = self.fold(capture.events)
        self.assertEqual(trace.state.inspect().knowledge, (*self.deals, proposal))

    def test_contradictory_physical_output_not_a_rejected_command(self):
        rows = list(self.capture.events)
        rows.append(event(len(rows), self.actor, s.ACTION, command(self.empty, "CRASH"), (b"",)))
        rows.append(event(len(rows), self.actor, s.ACTION, command(self.empty, "EXPOSE", 1)))
        trace = self.fold(rows)
        self.assertEqual(trace.outcomes[-2].disposition, "unresolved_original_output")
        self.assertEqual(trace.unresolved, (len(rows) - 2,))
        # The diagnostic suffix does not erase the unresolved source obligation.
        self.assertEqual(trace.events, tuple(rows))
        with self.assertRaises(c.CodecError):
            s.local_agreement(trace)

    def test_original_commits_derive_knowledge_and_status_floor_across_crash(self):
        proposal, prepares, commits = normal(self.group, self.seeds, self.ctx, self.deals)
        capture = Capture(self.empty)
        for raw in (*self.deals, proposal, *prepares):
            capture.record("RECEIVE", raw)
        commit_body = bytes.fromhex(c._load(commits[0])["body"])
        capture.record("INTENT", commit_body)
        capture.step("CRASH", (capture.state.stable,)).step("RECOVER")
        capture.step("BARRIER").step("COMMIT")
        status = signed(
            self.group,
            self.seeds,
            self.ctx,
            self.actor,
            "STATUS",
            2,
            prepared_proposal=s.a.identifier(proposal),
            prepares=[s.a.identifier(x) for x in prepares[:3]],
        )
        capture.record("INTENT", bytes.fromhex(c._load(status)["body"]))
        trace = self.fold(capture.events)
        projected = s.local_agreement(trace)
        self.assertEqual([x.kind for x in projected.actions], ["LEARN", "COMMIT", "STATUS"])
        self.assertEqual(projected.view, 2)
        self.assertEqual(projected.commits, projected.known)
        self.assertEqual(projected.reports, ((2, projected.known[0]),))
        self.assertEqual(projected.records, trace.state.inspect().records)
        for action in projected.actions:
            self.assertEqual(
                s.invocation(trace.events[action.source_position].original)["operation"], "COMMIT"
            )

    def test_uncommitted_receive_is_not_knowledge_even_with_complete_artifacts(self):
        proposal, prepares, _ = normal(self.group, self.seeds, self.ctx, self.deals)
        capture = Capture(self.empty)
        for raw in (*self.deals, proposal, *prepares[:2]):
            capture.record("RECEIVE", raw)
        capture.step("RECEIVE", (prepares[2],))
        before_barrier = self.fold(capture.events)
        self.assertEqual(s.local_agreement(before_barrier).known, ())
        capture.step("BARRIER").step("COMMIT")
        self.assertEqual(len(s.local_agreement(self.fold(capture.events)).known), 1)

    def test_initial_absence_not_manufactured_empty_or_lost_existing_journal(self):
        initial = self.fold([])
        self.assertIsNone(s.check_journal_tip(initial, self.actor, self.ctx, ()))
        explicit_empty = ((self.actor, s.journal_id(self.ctx), b""),)
        self.assertEqual(s.check_journal_tip(initial, self.actor, self.ctx, explicit_empty), b"")
        pending = self.fold(self.capture.events[:1])
        self.assertEqual(pending.state.stable, b"")
        with self.assertRaises(c.CodecError):
            s.check_journal_tip(pending, self.actor, self.ctx, ())

    def test_forged_trace_cache_cannot_replace_original_occurrences(self):
        trace = self.fold()
        altered = replace(trace, events=(), outcomes=(), commits=trace.commits)
        with self.assertRaises(c.CodecError):
            s.local_agreement(altered)
        with self.assertRaises(c.CodecError):
            s.check_journal_tip(
                altered,
                self.actor,
                self.ctx,
                ((self.actor, s.journal_id(self.ctx), trace.state.volatile),),
            )


if __name__ == "__main__":
    unittest.main()
