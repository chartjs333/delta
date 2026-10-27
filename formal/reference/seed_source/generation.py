"""Existing-key deterministic unsigned seed bodies; FORMAL/REFERENCE ONLY.

No key loading, production signer, disk I/O or exposure. Callers must satisfy
the complete source/persistence/release rules before a statement is signed.
Tests supply PUBLIC synthetic Ed25519 seeds; never pass deployed secrets here.
"""

import hashlib
import hmac

from formal.reference.isc_crypto import codec as c
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import pvss as p

COEFFICIENT = b"deltareduce.seed-pvss.coefficient.v1\0"
DEAL_NONCE = b"deltareduce.seed-pvss.nonce.deal.v1\0"
OPEN_NONCE = b"deltareduce.seed-pvss.nonce.open.v1\0"


def key_scalar(group, seed, public):
    c._require(type(seed) is bytes and len(seed) == 32, "original Ed25519 seed width")
    raw = bytearray(hashlib.sha512(seed).digest()[:32])
    raw[0] &= 248
    raw[31] &= 63
    raw[31] |= 64
    secret = int.from_bytes(raw, "little") % p.L
    c._require(
        secret != 0 and group.mul(secret, group.g) == public,
        "original existing private/public key correspondence",
    )
    return secret


def derive(seed, domain, core, index):
    c._require(type(index) is int and 0 <= index < 256, "one-byte derivation index")
    return int.from_bytes(
        hmac.new(seed, domain + p.frame(core) + bytes([index]), hashlib.sha512).digest(), "little"
    )


def deal_body(group, boot, context, actor, private_seed):
    members = p.context(boot, context)
    c._require(actor in members, "existing enrolled dealer")
    key_scalar(group, private_seed, members[actor])
    semantic = c._json(a.instance(context))
    coefficients = [derive(private_seed, COEFFICIENT, semantic, j) % p.L for j in range(3)]
    commitments = [group.mul(value, group.h) for value in coefficients]
    evaluations = [
        sum(value * i**j for j, value in enumerate(coefficients)) % p.L for i in range(1, 5)
    ]
    encrypted = [
        group.mul(value, key) for value, key in zip(evaluations, members.values(), strict=True)
    ]
    body = dict(
        profile=p.PROFILE,
        kind="DEAL",
        context=context,
        actor=actor,
        commitments=[value.hex() for value in commitments],
        encrypted_shares=[value.hex() for value in encrypted],
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
            evaluations[i - 1],
            1 + derive(private_seed, DEAL_NONCE, core, i) % (p.L - 1),
        ).hex()
        for i, key in enumerate(members.values(), 1)
    ]
    return c._json(body)


def opening_body(group, boot, context, actor, private_seed, deal_raw):
    """Unsigned primitive only; does NOT grant release or bypass a commit lock."""
    members = p.context(boot, context)
    c._require(actor in members, "existing enrolled recipient")
    secret = key_scalar(group, private_seed, members[actor])
    deal = p.verify_deal(group, boot, context, deal_raw)
    index = list(members).index(actor) + 1
    share = group.mul(pow(secret, -1, p.L), deal.encrypted[index - 1])
    body = dict(
        profile=p.PROFILE,
        kind="OPEN",
        context=context,
        actor=actor,
        deal_id=p.artifact_id(deal_raw),
        share=share.hex(),
    )
    core = c._json(body)
    nonce = 1 + derive(private_seed, OPEN_NONCE, core, index) % (p.L - 1)
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
    return c._json(body)
