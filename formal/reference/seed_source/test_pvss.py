"""Public synthetic fixtures only. No production seed/private key is loaded."""

import itertools
import json
import os
import unittest
from dataclasses import replace
from hashlib import sha512
from pathlib import Path

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_crypto.sodium_reference import SodiumReference
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.seed_source import pvss as p


def fixture_group():
    pin = json.loads(Path("formal/reference/isc_crypto/library-provenance.json").read_text("utf8"))
    return p.Group(SodiumReference(os.environ["ISC_SODIUM_DLL"], pin["dll"]["sha256"]))


def fixture():
    group = fixture_group()
    # Deliberately PUBLIC test seeds, not deployed credentials.
    seeds = {f"validator-{i}": bytes([i]) * 32 for i in range(1, 5)}
    keys = {
        actor: group.backend.sign(seed, b"synthetic fixture only")[0]
        for actor, seed in seeds.items()
    }
    boot = Bootstrap(
        "sha256:" + "1" * 64, "sha256:" + "2" * 64, "sha256:" + "3" * 64, tuple(keys.items())
    )
    ctx = {field: "sha256:" + "4" * 64 for field in p.CONTEXT}
    ctx.update(
        formal_semantics_id=boot.formal_semantics_id,
        origin_id=boot.origin_id,
        validator_epoch_id=boot.validator_epoch_id,
        registry_id=registry(boot)[0],
        round_id="round-synthetic",
        height="1",
        view="0",
    )
    return group, seeds, boot, ctx


def secret_scalar(seed):
    raw = bytearray(sha512(seed).digest()[:32])
    raw[0] &= 248
    raw[31] &= 63
    raw[31] |= 64
    return int.from_bytes(raw, "little") % p.L


def make_deal(group, seeds, boot, ctx, coefficients=(7, 11, 13), nonce_offset=0):
    members = p.context(boot, ctx)
    commitments = tuple(group.mul(a, group.h) for a in coefficients)
    values = [sum(a * i**j for j, a in enumerate(coefficients)) % p.L for i in range(1, 5)]
    encrypted = [group.mul(value, key) for value, key in zip(values, members.values(), strict=True)]
    body = dict(
        kind="DEAL",
        profile=p.PROFILE,
        context=ctx,
        actor="validator-1",
        commitments=[x.hex() for x in commitments],
        encrypted_shares=[x.hex() for x in encrypted],
    )
    core = c._json(body)
    body["proofs"] = [
        group.prove(
            p.DEAL_PROOF,
            core + bytes([i]),
            group.h,
            p.evaluation(group, commitments, i),
            key,
            encrypted[i - 1],
            values[i - 1],
            100 + i + nonce_offset,
        ).hex()
        for i, key in enumerate(members.values(), 1)
    ]
    return p.sign(group, seeds["validator-1"], body)


def make_open(group, seeds, boot, ctx, deal_raw, actor, nonce=43):
    deal = p.verify_deal(group, boot, ctx, deal_raw)
    members = p.context(boot, ctx)
    index = list(members).index(actor) + 1
    secret = secret_scalar(seeds[actor])
    assert group.mul(secret, group.g) == members[actor]
    share = group.mul(pow(secret, -1, p.L), deal.encrypted[index - 1])
    body = dict(
        kind="OPEN",
        profile=p.PROFILE,
        context=ctx,
        actor=actor,
        deal_id=p.artifact_id(deal_raw),
        share=share.hex(),
    )
    core = c._json(body)
    body["proof"] = group.prove(
        p.OPEN_PROOF,
        core + bytes([index]),
        group.g,
        members[actor],
        share,
        deal.encrypted[index - 1],
        secret,
        nonce,
    ).hex()
    return p.sign(group, seeds[actor], body)


def body(raw):
    return c._load(bytes.fromhex(c._load(raw)["body"]))


class PvssTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g, cls.seeds, cls.boot, cls.ctx = fixture()
        cls.deal = make_deal(cls.g, cls.seeds, cls.boot, cls.ctx)
        cls.opens = tuple(
            make_open(cls.g, cls.seeds, cls.boot, cls.ctx, cls.deal, actor) for actor in cls.seeds
        )

    def check_deal(self, raw, **kwargs):
        return p.verify_deal(
            self.g, kwargs.get("boot", self.boot), kwargs.get("ctx", self.ctx), raw
        )

    def resign(self, value):
        return p.sign(self.g, self.seeds[value["actor"]], value)

    def test_all_threshold_subsets_and_arrival_permutations(self):
        expected = self.g.mul(7, self.g.g)
        for count in (3, 4):
            for originals in itertools.permutations(self.opens, count):
                self.assertEqual(
                    p.reconstruct(self.g, self.boot, self.ctx, self.deal, originals), expected
                )

    def test_zero_polynomial_and_zero_individual_evaluation(self):
        for coefficients in ((0, 0, 0), (2, p.L - 3, 1), (0, 11, 13)):
            deal = make_deal(self.g, self.seeds, self.boot, self.ctx, coefficients)
            opens = tuple(
                make_open(self.g, self.seeds, self.boot, self.ctx, deal, actor)
                for actor in self.seeds
            )
            for subset in itertools.combinations(opens, 3):
                self.assertEqual(
                    p.reconstruct(self.g, self.boot, self.ctx, deal, subset),
                    self.g.mul(coefficients[0], self.g.g),
                )

    def test_randomized_witness_does_not_change_reconstructed_point(self):
        alt = make_deal(self.g, self.seeds, self.boot, self.ctx, nonce_offset=1000)
        self.assertNotEqual(p.artifact_id(self.deal), p.artifact_id(alt))
        opens = tuple(
            make_open(self.g, self.seeds, self.boot, self.ctx, alt, actor, 543)
            for actor in self.seeds
        )
        self.assertEqual(
            p.reconstruct(self.g, self.boot, self.ctx, alt, opens),
            p.reconstruct(self.g, self.boot, self.ctx, self.deal, self.opens),
        )

    def test_full_context_changes_rejected(self):
        for field in p.CONTEXT:
            changed = dict(self.ctx)
            changed[field] = (
                "2"
                if field in {"height", "view"}
                else "other-round"
                if field == "round_id"
                else "sha256:" + "9" * 64
            )
            with self.subTest(field=field), self.assertRaises(c.CodecError):
                self.check_deal(self.deal, ctx=changed)

    def test_body_and_original_array_binding_even_if_resigned(self):
        mutations = []
        value = body(self.deal)
        value["encrypted_shares"].reverse()
        mutations.append(value)
        value = body(self.deal)
        value["commitments"][0] = self.g.g.hex()
        mutations.append(value)
        value = body(self.deal)
        value["proofs"].reverse()
        mutations.append(value)
        value = body(self.deal)
        value["actor"] = "validator-2"
        mutations.append(value)
        value = body(self.deal)
        value["context"]["source_cut_id"] = "sha256:" + "9" * 64
        mutations.append(value)
        for value in mutations:
            with self.assertRaises(c.CodecError):
                self.check_deal(self.resign(value), ctx=value["context"])

    def test_exact_canonical_bytes_and_members(self):
        self.assertEqual(self.check_deal(self.deal).original, self.deal)
        for raw in (self.deal + b" ", self.deal.replace(b"{", b'{"body":"",', 1)):
            with self.assertRaises(c.CodecError):
                self.check_deal(raw)
        for name in ("extra", "proof"):
            value = body(self.deal)
            value[name] = "wrong"
            with self.assertRaises(c.CodecError):
                self.check_deal(self.resign(value))

    def test_signature_corruption_and_old_domain_fail_closed(self):
        envelope = c._load(self.deal)
        envelope["signature"] = bytes(64).hex()
        with self.assertRaises(c.CodecError):
            self.check_deal(c._json(envelope))
        raw_body = bytes.fromhex(envelope["body"])
        _, sig = self.g.backend.sign(self.seeds["validator-1"], b"NSG1" + sha512(raw_body).digest())
        envelope["signature"] = sig.hex()
        with self.assertRaises(c.CodecError):
            self.check_deal(c._json(envelope))

    def test_noncanonical_scalar_and_mixed_order_points(self):
        value = body(self.deal)
        value["proofs"][0] = p.L.to_bytes(32, "little").hex() + bytes(32).hex()
        with self.assertRaises(c.CodecError):
            self.check_deal(self.resign(value))
        for bad in (
            bytes(32),
            bytes.fromhex("95" + "99" * 31),
            bytes.fromhex("ee" + "ff" * 30 + "7f"),
        ):
            value = body(self.deal)
            value["encrypted_shares"][0] = bad.hex()
            with self.assertRaises(c.CodecError):
                self.check_deal(self.resign(value))

    def test_missing_and_duplicate_recipient_witnesses(self):
        for originals in (self.opens[:2], (self.opens[0], self.opens[0], self.opens[1])):
            with self.assertRaises(c.CodecError):
                p.reconstruct(self.g, self.boot, self.ctx, self.deal, originals)

    def test_opening_wrong_deal_share_recipient_and_proof(self):
        for field, value in (
            ("deal_id", "sha256:" + "9" * 64),
            ("share", self.g.g.hex()),
            ("actor", "validator-2"),
            ("proof", bytes(64).hex()),
        ):
            changed = body(self.opens[0])
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(c.CodecError):
                p.verify_open(self.g, self.boot, self.ctx, self.deal, self.resign(changed))

    def test_wrong_registry_key_and_duplicate_key(self):
        for vals in (
            (self.boot.validators[0],) * 4,
            (*self.boot.validators[:3], ("validator-4", self.boot.validators[0][1])),
        ):
            with self.assertRaises(c.CodecError):
                self.check_deal(self.deal, boot=replace(self.boot, validators=vals))


if __name__ == "__main__":
    unittest.main()
