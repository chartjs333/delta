"""Synthetic exact-byte/crash cases, NOT an authentic producer history."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_source.authentication import registry
from formal.reference.profile_source import ec_durability as d
from formal.reference.profile_source import metadata as m
from formal.reference.profile_source import source_prefix as source
from formal.reference.profile_source import test_ec_finalization as ec_cases
from formal.reference.profile_source.ec_finalization_vectors import fixture
from formal.reference.profile_source.test_metadata import Package
from formal.reference.profile_source.test_metadata import frame as trust_frame


def ref(raw):
    return {
        "schema_version": "1.0.0",
        "schema_id": "SCHEMA-SYNTHETIC-V1",
        "media_type": "application/octet-stream",
        "byte_length": str(len(raw)),
        "content_id": m.raw_id(raw),
        "locator": m.raw_id(raw)[7:] + ".bin",
    }


def descriptor(actor, action, original, inputs=(), dependencies=()):
    return m.canonical(
        {
            "actor_id": actor,
            "action_id": action,
            "original_ref": ref(original),
            "input_refs": [ref(v) for v in inputs],
            "dependencies": [str(v) for v in dependencies],
        }
    )


def example():
    f = fixture()
    t = ec_cases.EcFinalizationTests()
    t.f = f
    candidate = t.run_candidate()
    event = t.event(candidate)
    event = replace(
        event,
        original_descriptor=descriptor(
            event.actor, event.action, event.original, event.inputs, event.dependencies
        ),
    )
    prefix = (
        descriptor(event.actor, "SYNTHETIC-PREREQUISITE", f["config_raw"]),
        *(
            descriptor(row.receiver, "ACT-MESSAGE-DELIVER", row.original_g)
            for row in f["rows"]
            if row.position < event.index
        ),
    )
    args = dict(
        authority=f["authority"],
        backend=f["backend"],
        bootstrap_id="sha256:" + "b" * 64,
        original_event=event,
        original_descriptors=prefix,
        journal_cuts=[],
        prior_companion=b"",
        original_rows=f["rows"],
        original_tick=0,
        prerequisite_positions=(0,),
    )
    return f, args, d.compute(**args)


def indexed_example():
    """Complete original METADATA join; genesis/floor placeholders are not authority."""
    f, args, _ = example()
    p = Package()
    event = args["original_event"]
    boot = args["authority"].bootstrap
    _, keys = registry(boot)
    context = {
        "origin_id": boot.origin_id,
        "validator_epoch_id": boot.validator_epoch_id,
        "local_validator_id": event.actor,
    }
    p.boot.update(
        context,
        formal_semantics_id=boot.formal_semantics_id,
        genesis_ref=ref(b"genesis"),
        initial_config_ref=ref(b"configuration"),
        validators=[
            {"validator_id": name, "key_ref": key, "roles": ["validator"]}
            for name, (key, _) in keys.items()
        ],
    )
    p.boot_raw = m.canonical(p.boot)
    args["bootstrap_id"] = m.document_id(p.boot_raw, "BOOTSTRAP")
    bound = d.compute(**args)
    originals = {raw for _, raw in p.artifacts}
    originals.update(
        (f["config_raw"], event.original, *event.inputs, *(row.original_g for row in f["rows"]))
    )

    def table(values):
        return sorted(map(ref, values), key=lambda row: row["content_id"])

    p.index.update(
        context,
        genesis_ref=ref(b"genesis"),
        events=[m.load(raw) for raw in args["original_descriptors"]],
        artifacts=table(originals),
        original_journal_refs=[],
    )
    prior_index = m.canonical(p.index)
    full = bound.record.original_frame
    originals.update((prior_index, full))
    row = {
        "actor_id": event.actor,
        "journal_id": d.JOURNAL,
        "ref": ref(full),
        "entry_count": "1",
        "first_sequence": "1",
        "last_sequence": "1",
    }
    p.index.update(
        events=[*p.index["events"], m.load(event.original_descriptor)],
        artifacts=table(originals),
        original_journal_refs=[row],
    )
    p.index_raw = m.canonical(p.index)
    p.artifacts = tuple(sorted((m.raw_id(raw), raw) for raw in originals))
    p.record.update(bootstrap_id=args["bootstrap_id"], journal_cuts=[])
    span = {key: value for key, value in row.items() if key not in ("actor_id", "journal_id")}
    p.manifest.update(
        context,
        bootstrap_id=args["bootstrap_id"],
        formal_semantics_id=boot.formal_semantics_id,
        source_index_ref=ref(p.index_raw),
        artifacts=table(originals),
        apply_qc_ref=ref(b"QC"),
        apply_candidate_ref=ref(b"candidate"),
        snapshot_ref=ref(b"snapshot"),
        cut_event_index=str(event.index + 1),
        target_event_index=str(event.index + 1),
        journals=[{"actor_id": event.actor, "journal_id": d.JOURNAL, "cut": span, "target": span}],
    )
    p.trust = m.PrimitiveTrust(
        m.raw_id(p.boot_raw),
        m.raw_id(p.index_raw),
        tuple((key, p.boot[key]) for key in m.PINS),
        p.boot_raw,
        trust_frame(p.record),
        ((event.actor, d.JOURNAL, full),),
    )
    return args, source.materialize(p.check()), prior_index, bound


class EcDurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f, cls.args, cls.bound = example()

    def initial(self):
        # Deliberately opaque synthetic original native WAL; this component
        # proves byte retention, not that these bytes form a valid WAL history.
        return d.prepared(self.bound, b"original native physical slots / vote ranks")

    def test_profile_cut_bootstrap_and_own_original_journal_join(self):
        args, original, old_index, expected = indexed_example()

        def bind(p=original, old=old_index, authority=args["authority"]):
            return d.bind_profile(
                p,
                authority,
                args["backend"],
                expected.event.index,
                old,
                args["original_rows"],
                args["original_tick"],
                args["prerequisite_positions"],
            )

        checked = bind()
        self.assertEqual(checked.binding, expected)
        self.assertEqual(checked.original_cut.events, original.events[: expected.event.index])
        self.assertEqual(checked.complete_own_journal, expected.record.original_frame)
        self.assertEqual(checked.original_records, (expected.record,))
        with self.assertRaises(CodecError):
            bind(old=original.metadata.source_index_bytes)  # Circular successor is not old cut.
        foreign = replace(
            args["authority"],
            bootstrap=replace(args["authority"].bootstrap, origin_id=m.raw_id(b"other")),
        )
        with self.assertRaises(CodecError):
            bind(authority=foreign)
        for raw in (b"", expected.record.original_frame[:-1], expected.record.original_frame * 2):
            meta = replace(
                original.metadata, original_own_journals=((expected.event.actor, d.JOURNAL, raw),)
            )
            with self.assertRaises(CodecError):
                bind(p=replace(original, metadata=meta))
        meta = replace(
            original.metadata,
            original_artifacts=tuple(
                (key, raw) for key, raw in original.metadata.original_artifacts if raw != old_index
            ),
        )
        with self.assertRaises(CodecError):
            bind(p=replace(original, metadata=meta))

    def test_exact_record_complete_fields_and_namespace(self):
        b = self.bound
        record = b.record
        self.assertEqual(d.scan(record.original_frame), (record,))
        self.assertEqual(record.fields["prior_policy_raw_id"], m.raw_id(b.candidate.prior_policy))
        self.assertEqual(record.fields["next_policy_raw_id"], m.raw_id(b.candidate.next_policy))
        self.assertEqual(record.fields["seed_raw_id"], m.raw_id(self.f["seed"]))
        self.assertEqual(record.fields["certificate_raw_id"], m.raw_id(b.candidate.certificate))
        self.assertNotEqual(record.id, b.candidate.certificate_id)
        self.assertEqual(set(record.fields), d.FIELDS)
        self.assertIs(d.bind_original(b, record.original_frame), b)

    def test_complete_prior_companion_inventory_and_chain(self):
        first = self.bound.record
        # This is a STRUCTURAL chain case, not another lawful EC for the same b.
        fields = first.fields
        fields.update(
            ordinal="2",
            previous_record_id=first.id,
            event_index=str(int(fields["event_index"]) + 1),
        )
        second_raw = m.canonical(fields)
        second = d.Record(second_raw, d.frame(second_raw))
        whole = first.original_frame + second.original_frame
        self.assertEqual(d.scan(whole), (first, second))
        row = {
            "actor_id": self.bound.event.actor,
            "journal_id": d.JOURNAL,
            "ref": ref(whole),
            "entry_count": "2",
            "first_sequence": "1",
            "last_sequence": "2",
        }
        self.assertEqual(d.companion_cut([row], self.bound.event.actor, whole), (first, second))
        for cut in (
            [],
            [{**row, "entry_count": "1", "last_sequence": "1"}],
            [{**row, "ref": ref(first.original_frame)}],
        ):
            with self.subTest(cut=cut), self.assertRaises(CodecError):
                d.companion_cut(cut, self.bound.event.actor, whole)
        fields["previous_record_id"] = "sha256:" + "f" * 64
        with self.assertRaises(CodecError):
            d.scan(first.original_frame + d.frame(m.canonical(fields)))
        fields["previous_record_id"], fields["event_index"] = first.id, first.fields["event_index"]
        with self.assertRaises(CodecError):
            d.scan(first.original_frame + d.frame(m.canonical(fields)))

    def test_rehashed_substitutions_do_not_match_computed_transaction(self):
        for name in d.HASH_FIELDS - {"bootstrap_id"}:
            fields = self.bound.record.fields
            fields[name] = "sha256:" + "f" * 64
            with self.subTest(field=name), self.assertRaises(CodecError):
                d.bind_original(self.bound, d.frame(m.canonical(fields)))
        fields = self.bound.record.fields
        fields["actor_id"] = "other-validator"
        with self.assertRaises(CodecError):
            d.bind_original(self.bound, d.frame(m.canonical(fields)))

    def test_duplicate_unknown_noncanonical_members_and_frame_tails(self):
        raw = self.bound.record.raw
        for malformed in (
            b'{"actor_id":"first",' + raw[1:],
            raw + b"\n",
            m.canonical({**self.bound.record.fields, "durable": True}),
            raw.replace(b'"ordinal":"1"', b'"ordinal":"01"'),
        ):
            with self.subTest(raw=malformed[:50]), self.assertRaises(CodecError):
                d.frame(malformed)
        frame = self.bound.record.original_frame
        for malformed in (frame[:-1], frame + b"\0", frame[:-1] + bytes([frame[-1] ^ 1])):
            with self.assertRaises(CodecError):
                d.scan(malformed)
        with self.assertRaises(CodecError):
            d.scan(frame + frame)  # A repeat is NOT another original ordinal.

    def test_descriptor_cut_and_original_occurrence_multiplicity(self):
        args = self.args
        event = args["original_event"]
        with self.assertRaises(CodecError):
            d.compute(**{**args, "original_event": replace(event, original_descriptor=b"{}")})
        with self.assertRaises(CodecError):
            d.compute(**{**args, "original_descriptors": args["original_descriptors"][:-1]})
        prefix = args["original_descriptors"]
        self.assertNotEqual(
            d.source_digest(args["bootstrap_id"], prefix),
            d.source_digest(args["bootstrap_id"], prefix[:-1]),
        )
        self.assertEqual(self.bound.candidate.matching_positions, (1, 2, 3, 4))
        self.assertEqual(len(self.bound.candidate.signers), 3)
        # A later original arrival must not change the original signer cut.
        later = replace(self.f["rows"][-1], position=900)
        more = d.compute(**{**args, "original_rows": (*args["original_rows"], later)})
        self.assertEqual(more, self.bound)

    def test_no_commit_or_exposure_before_barrier(self):
        s = self.initial()
        for state in (s, d.append(s)):
            with self.assertRaises(CodecError):
                d.commit(state)
            with self.assertRaises(CodecError):
                d.expose(state)
        with self.assertRaises(CodecError):
            d.commit(replace(s, phase="DURABLE"))
        with self.assertRaises(CodecError):
            d.expose(replace(s, phase="COMMITTED"))
        durable = d.barrier(d.append(s))
        with self.assertRaises(CodecError):
            d.expose(durable)
        committed = d.commit(durable)
        exposed = d.expose(committed)
        self.assertEqual(exposed.native_wal, s.native_wal)
        self.assertEqual(exposed.current_policy, self.bound.candidate.next_policy)
        self.assertEqual(exposed.exposed, (self.bound.candidate.certificate,))
        self.assertEqual(len(d.scan(exposed.stable)), 1)

    def test_absent_complete_and_arbitrary_torn_unacknowledged_bytes(self):
        a = d.append(self.initial())
        absent = d.recover(d.crash(a, b""), self.bound)
        self.assertEqual(absent.phase, "PREPARED")
        full = d.recover(d.crash(a, a.volatile), self.bound)
        self.assertEqual(full.phase, "RECOVERY_VERIFIED")
        with self.assertRaises(CodecError):
            d.expose(full)
        with self.assertRaises(CodecError):
            d.commit(full)
        self.assertEqual(d.expose(d.commit(d.barrier(full))).stable, a.volatile)
        for tail in (a.volatile[:1], a.volatile[:-1], b"\0" * len(a.volatile), b"unknown"):
            blocked = d.recover(d.crash(a, tail), self.bound)
            self.assertEqual(blocked.phase, "BLOCKED")
            self.assertEqual(blocked.volatile, tail)
            for action in (d.append, d.barrier, d.commit, d.expose):
                with self.assertRaises(CodecError):
                    action(blocked)

    def test_crash_after_barrier_commit_exposure_preserves_original_history(self):
        durable = d.barrier(d.append(self.initial()))
        committed = d.commit(durable)
        exposed = d.expose(committed)
        for state in (durable, committed, exposed):
            with self.assertRaises(CodecError):
                d.crash(state, b"")  # Profile T cannot drop acknowledged bytes.
            crashed = d.crash(state, state.stable)
            self.assertEqual(crashed.exposed, state.exposed)
            self.assertEqual(crashed.current_policy, state.current_policy)
            restored = d.commit(d.barrier(d.recover(crashed, self.bound)))
            self.assertEqual(restored.native_wal, state.native_wal)
            self.assertEqual(restored.stable, state.stable)
            self.assertEqual(restored.current_policy, self.bound.candidate.next_policy)
            self.assertEqual(len(d.scan(restored.stable)), 1)
            with self.assertRaises(CodecError):
                d.append(restored)
        twice = d.expose(exposed)
        self.assertEqual(twice.exposed[0], twice.exposed[1])
        self.assertEqual(twice.stable, exposed.stable)


if __name__ == "__main__":
    unittest.main()
