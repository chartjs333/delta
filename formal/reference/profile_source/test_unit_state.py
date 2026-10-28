"""Complete profile inventory source tests; not lawful finalized-state evidence."""

import unittest
from copy import deepcopy

from formal.reference.isc_crypto.codec import CodecError
from formal.reference.isc_source import policy
from formal.reference.profile_source import arithmetic_units as u
from formal.reference.profile_source import unit_state as s
from formal.reference.profile_source.installed_state_vectors import generate
from formal.reference.profile_source.test_arithmetic_units import PROOF, SEMANTICS, numeric


class UnitStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, raw = generate()
        cls.base = policy.decode(bytes.fromhex(raw["original_policy"]))

    def profile(self, q="1", d=4):
        return u.derive_profile(u.canonical(numeric(q, d)), PROOF, SEMANTICS)

    def original_policy(self, originals):
        p = deepcopy(self.base)
        p["snapshot"]["apply_profiles"] = [
            s.core_view(u.decode_profile(raw, SEMANTICS)) for raw in originals
        ]
        return policy.encode(p)

    def test_full_core_and_raw_and_quantum_retained(self):
        raw = self.profile()
        core = s.core_view(u.decode_profile(raw, SEMANTICS))
        out = s.bind_profile(SEMANTICS, raw, core)
        self.assertEqual(out.original, raw)
        self.assertEqual(out.core, core)
        self.assertEqual(out.numeric, numeric())
        self.assertEqual(out.identifier, u.content_id(u.DOMAIN, raw))

    def test_identical_core_distinct_quanta_are_not_collapsed(self):
        originals = sorted(
            [self.profile(), self.profile("3", 7)], key=lambda raw: u.content_id(u.DOMAIN, raw)
        )
        out = s.bind_inventory(SEMANTICS, self.original_policy(originals), originals)
        self.assertEqual(out[0].core, out[1].core)
        self.assertNotEqual(out[0].numeric, out[1].numeric)
        self.assertNotEqual(out[0].identifier, out[1].identifier)
        self.assertEqual([row.original for row in out], originals)

    def test_full_inventory_not_filtered_by_current_configuration(self):
        raw = self.profile("7", 11)
        self.assertEqual(len(s.bind_inventory(SEMANTICS, self.original_policy([raw]), [raw])), 1)

    def test_missing_extra_duplicate_reordered_originals_reject(self):
        originals = sorted(
            [self.profile(), self.profile("3", 7)], key=lambda raw: u.content_id(u.DOMAIN, raw)
        )
        original = self.original_policy(originals)
        for changed in (originals[:1], [*originals, originals[0]], originals[::-1]):
            with self.subTest(kind=len(changed)), self.assertRaises(CodecError):
                s.bind_inventory(SEMANTICS, original, changed)
        duplicate = [originals[0], originals[0]]
        duplicate_policy = self.original_policy(duplicate)
        with self.assertRaises(CodecError):
            s.bind_inventory(SEMANTICS, duplicate_policy, duplicate)

    def test_core_substitution_rejects_even_reencoded_policy(self):
        raw = self.profile()
        p = policy.decode(self.original_policy([raw]))
        p["snapshot"]["apply_profiles"][0]["learning_rate"]["numerator"] = 2
        substituted = policy.encode(p)
        with self.assertRaises(CodecError):
            s.bind_inventory(SEMANTICS, substituted, [raw])

    def test_bool_integer_core_alias_rejects(self):
        raw = self.profile()
        core = s.core_view(u.decode_profile(raw, SEMANTICS))
        core["domain_weights"][0]["pi"]["numerator"] = True
        with self.assertRaises(CodecError):
            s.bind_profile(SEMANTICS, raw, core)

    def test_duplicate_json_member_and_legacy_quantum_absence_reject(self):
        raw = self.profile()
        core = s.core_view(u.decode_profile(raw, SEMANTICS))
        duplicate = raw.replace(b'"apply_quantum":', b'"apply_quantum":{},"apply_quantum":')
        old = u.decode_profile(raw, SEMANTICS)
        del old["apply_quantum"]
        for changed in (duplicate, u.canonical(old), raw + b"\n"):
            with self.subTest(raw=changed[:30]), self.assertRaises(CodecError):
                s.bind_profile(SEMANTICS, changed, core)

    def test_wrong_independent_semantics_and_invalid_quantum_reject(self):
        raw = self.profile()
        core = s.core_view(u.decode_profile(raw, SEMANTICS))
        with self.assertRaises(CodecError):
            s.bind_profile(PROOF, raw, core)
        changed = u.decode_profile(raw, SEMANTICS)
        changed["apply_quantum"] = {"numerator": "2", "denominator": 8}
        with self.assertRaises(CodecError):
            s.bind_profile(SEMANTICS, u.canonical(changed), core)

    def test_empty_inventory_does_not_invent_profile(self):
        self.assertEqual(s.bind_inventory(SEMANTICS, self.original_policy([]), []), ())


if __name__ == "__main__":
    unittest.main()
