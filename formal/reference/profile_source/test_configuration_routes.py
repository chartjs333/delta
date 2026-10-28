"""Fresh whole schema-3 original CONFIG/input histories, never legacy relabels."""

import unittest
from dataclasses import replace

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.profile_source import configuration_history as history
from formal.reference.profile_source import configuration_qc as qc
from formal.reference.profile_source import configuration_route as route
from formal.reference.profile_source import test_configuration_history as hf
from formal.reference.profile_source import test_configuration_qc as qf
from formal.reference.profile_source import test_input_capsule as cf
from formal.reference.profile_source import test_input_history as inf
from formal.reference.profile_source import test_source_prefix as sf


class UnitQcTests(qf.ConfigQcTests):
    generation = route.UNITS

    def test_no_imported_schema_fallback_or_opaque_generation_callback(self):
        original = qf.ConfigQcTests()
        original.setUp()
        for raw, generation in ((self.raw, route.LEGACY), (original.raw, route.UNITS)):
            with self.subTest(generation=generation), self.assertRaises(CodecError):
                route.bind(
                    self.f.boot, self.f.storage_boot, raw, self.f.declaration, generation=generation
                )
        for generation in (True, False, "3.0.0", None, lambda _: True):
            with self.subTest(generation=generation), self.assertRaises(CodecError):
                route.decode(self.raw, generation=generation)
        self.assertEqual(route.decode(self.raw, generation=route.UNITS), self.body)
        self.assertEqual(self.check().config.original, self.raw)
        self.assertNotEqual(self.check().config.body_id, original.check().config.body_id)


class UnitHistoryTests(hf.ConfigurationHistoryTests):
    configuration_case = UnitQcTests

    def test_finalization_and_proposal_are_local_to_original_receiver(self):
        self.actor_separation()

    def actor_separation(self):
        first, second = self.x.names[:2]

        def event(actor, raw):
            return replace(self.event(raw), actor=actor)

        def propose(actor):
            out = history.propose(
                self.state,
                event(actor, self.x.raw),
                self.f.boot,
                self.f.storage_boot,
                self.f.declaration,
                generation=self.x.generation,
            )
            self.state = out.state
            return out.disposition

        def deliver(actor):
            for row in self.x.delivered:
                self.state = history.deliver(
                    self.state, event(actor, row.original_artifact), self.f.boot, self.f.backend
                ).state

        def finalize(actor):
            out = history.finalize(
                self.state,
                event(actor, qc.encode(self.x.qc)),
                self.f.boot,
                self.f.storage_boot,
                self.f.backend,
                generation=self.x.generation,
            )
            self.state = out.state
            return out.disposition

        self.assertEqual(propose(first), "recorded")
        deliver(first)
        self.assertEqual(finalize(first), "recorded")
        original = self.state.finalized[0]
        self.assertEqual(finalize(second), "rejected_configuration_quorum")
        deliver(second)
        self.assertEqual(finalize(second), "rejected_configuration_quorum")
        self.assertEqual(propose(second), "recorded")
        self.assertEqual(finalize(second), "recorded")
        self.assertIs(self.state.finalized[0], original)
        self.assertEqual([row.source.actor for row in self.state.finalized], [first, second])
        self.assertEqual([row.source.actor for row in self.state.proposals], [first, second])
        self.assertEqual(len(self.state.received), 8)
        self.assertEqual(finalize(first), "replay")
        self.assertEqual(finalize(second), "replay")
        self.assertEqual(len(self.state.events), self.index)
        other_generation = route.LEGACY if self.x.generation is route.UNITS else route.UNITS
        out = history.finalize(
            self.state,
            event(first, qc.encode(self.x.qc)),
            self.f.boot,
            self.f.storage_boot,
            self.f.backend,
            generation=other_generation,
        )
        self.assertEqual(out.disposition, "rejected_configuration_quorum")
        self.assertEqual(out.state.finalized, self.state.finalized)


class OriginalHistoryActorTests(UnitHistoryTests):
    configuration_case = qf.ConfigQcTests


class UnitPrefixTests(sf.SourcePrefixTests):
    configuration_case = UnitQcTests


class UnitInputTests(inf.InputHistoryTests):
    generation = route.UNITS


class UnitCapsuleTests(cf.InputCapsuleTests):
    input_case = UnitInputTests


if __name__ == "__main__":
    unittest.main()
