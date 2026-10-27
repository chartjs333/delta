"""T047/T053. Isolated existing-key PVSS component, NOT a seed producer.

Concrete group/signature checks; no trusted verifier callback. A valid opening
does not establish prior lock, original source legality or release permission.
The selected immutable contract is seed-pvss-component-contract.md.
"""

from __future__ import annotations

import ctypes
import hashlib
from dataclasses import dataclass

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_crypto.sodium_reference import SCALAR_ORDER, SodiumReference, _buffer
from formal.reference.isc_source.authentication import Bootstrap, registry

L = SCALAR_ORDER
ZERO = b"\x01" + bytes(31)
PROFILE = "SEED-PVSS-ED25519-COMPONENT-v1"
SIGN = b"deltareduce.seed-pvss.statement.v1\0"
ARTIFACT = "deltareduce.seed-pvss.artifact.v1"
DEAL_PROOF = b"deltareduce.seed-pvss.deal-proof.v1\0"
OPEN_PROOF = b"deltareduce.seed-pvss.open-proof.v1\0"
GENERATOR = b"deltareduce.seed-pvss.generator.v1\0"
CONTEXT = set(
    "formal_semantics_id origin_id validator_epoch_id registry_id round_id "
    "round_config_id parent_checkpoint_id isc_body_id arithmetic_profile_id "
    "parameter_schema_id height view source_cut_id".split()
)
COMMON = {"kind", "profile", "context", "actor"}


def frame(raw: bytes) -> bytes:
    return len(raw).to_bytes(8, "big") + raw


def scalar(value: int) -> bytes:
    c._require(type(value) is int and 0 <= value < L, "canonical field scalar")
    return value.to_bytes(32, "little")


def binary(value: object, size: int) -> bytes:
    c._require(type(value) is str and len(value) == 2 * size, "fixed hex width")
    try:
        raw = bytes.fromhex(value)
    except ValueError as error:
        raise c.CodecError("hex encoding") from error
    c._require(raw.hex() == value, "canonical lowercase hex")
    return raw


class Group:
    """Only the existing SHA-pinned libsodium backend, including strict points."""

    def __init__(self, backend: SodiumReference):
        c._require(type(backend) is SodiumReference, "concrete pinned backend")
        self.backend = backend
        self.lib = backend._lib
        for name, count in (
            ("crypto_core_ed25519_add", 3),
            ("crypto_scalarmult_ed25519_noclamp", 3),
            ("crypto_scalarmult_ed25519_base_noclamp", 2),
            ("crypto_core_ed25519_from_uniform", 2),
        ):
            fn = getattr(self.lib, name)
            fn.argtypes = [ctypes.c_void_p] * count
            fn.restype = ctypes.c_int
        self.g = self._call("crypto_scalarmult_ed25519_base_noclamp", scalar(1))
        for counter in range(1 << 32):
            uniform = hashlib.sha256(GENERATOR + counter.to_bytes(4, "big")).digest()
            h = self._call("crypto_core_ed25519_from_uniform", uniform)
            if h != ZERO:
                self.point(h, identity=False)
                self.h = h
                self.generator_counter = counter
                break
        else:
            raise c.CodecError("secondary generator unavailable")

    def _call(self, name: str, *values: bytes) -> bytes:
        out = ctypes.create_string_buffer(32)
        c._require(getattr(self.lib, name)(out, *map(_buffer, values)) == 0, name)
        return out.raw

    def point(self, raw: bytes, *, identity: bool = True) -> bytes:
        c._require(type(raw) is bytes and len(raw) == 32, "point width")
        c._require(
            (identity and raw == ZERO)
            or self.lib.crypto_core_ed25519_is_valid_point(_buffer(raw)) == 1,
            "canonical prime-order point",
        )
        return raw

    def mul(self, value: int, point: bytes) -> bytes:
        scalar(value)
        self.point(point)
        if value == 0 or point == ZERO:
            return ZERO
        return self._call("crypto_scalarmult_ed25519_noclamp", scalar(value), point)

    def add(self, left: bytes, right: bytes) -> bytes:
        self.point(left)
        self.point(right)
        return self._call("crypto_core_ed25519_add", left, right)

    def total(self, values) -> bytes:
        out = ZERO
        for value in values:
            out = self.add(out, value)
        return out

    def challenge(self, domain, binding, g1, y1, g2, y2, r1, r2):
        for point in (g1, y1, g2, y2, r1, r2):
            self.point(point)
        return (
            int.from_bytes(
                hashlib.sha512(domain + frame(binding) + g1 + y1 + g2 + y2 + r1 + r2).digest(),
                "little",
            )
            % L
        )

    def prove(self, domain, binding, g1, y1, g2, y2, witness, nonce):
        """Explicit test/private coins; this function does not authenticate entropy."""
        scalar(witness)
        scalar(nonce)
        c._require(
            self.mul(witness, g1) == y1 and self.mul(witness, g2) == y2, "DLEQ witness mismatch"
        )
        challenge = self.challenge(
            domain, binding, g1, y1, g2, y2, self.mul(nonce, g1), self.mul(nonce, g2)
        )
        return scalar(challenge) + scalar((nonce - challenge * witness) % L)

    def verify(self, domain, binding, g1, y1, g2, y2, proof):
        c._require(type(proof) is bytes and len(proof) == 64, "DLEQ proof width")
        challenge, response = (int.from_bytes(proof[i : i + 32], "little") for i in (0, 32))
        scalar(challenge)
        scalar(response)
        r1 = self.add(self.mul(response, g1), self.mul(challenge, y1))
        r2 = self.add(self.mul(response, g2), self.mul(challenge, y2))
        c._require(
            self.challenge(domain, binding, g1, y1, g2, y2, r1, r2) == challenge,
            "DLEQ verification",
        )


def context(boot: Bootstrap, expected: dict) -> dict[str, bytes]:
    c._closed(expected, CONTEXT)
    registry_id, members = registry(boot)
    c._require(
        len(members) == 4 and len({v[1] for v in members.values()}) == 4,
        "existing four distinct enrolled keys",
    )
    for field in CONTEXT - {"height", "view", "round_id"}:
        c._id(expected[field])
    c._label(expected["round_id"])
    for field in ("height", "view"):
        c._decimal(expected[field], positive=field == "height")
    c._require(
        expected["registry_id"] == registry_id
        and expected["formal_semantics_id"] == boot.formal_semantics_id
        and expected["validator_epoch_id"] == boot.validator_epoch_id
        and expected["origin_id"] == boot.origin_id,
        "independent bootstrap context",
    )
    return {name: members[name][1] for name in sorted(members)}


def message(body: bytes) -> bytes:
    return SIGN + len(body).to_bytes(8, "big") + hashlib.sha512(body).digest()


def sign(group: Group, seed: bytes, body: dict) -> bytes:
    """Synthetic fixture helper only; no key loading or persistence."""
    raw = c._json(body)
    _, signature = group.backend.sign(seed, message(raw))
    return c._json({"body": raw.hex(), "signature": signature.hex()})


def authenticated(group: Group, boot: Bootstrap, expected: dict, raw: bytes):
    outer = c._closed(c._load(raw), {"body", "signature"})
    c._require(type(outer["body"]) is str, "original statement bytes")
    original = binary(outer["body"], len(outer["body"]) // 2)
    body = c._load(original)
    members = unsigned_context(group, boot, expected, body)
    signature = binary(outer["signature"], 64)
    c._require(
        group.backend.verify(members[body["actor"]], message(original), signature),
        "existing-key seed-purpose signature",
    )
    return body, members


def unsigned_context(group: Group, boot: Bootstrap, expected: dict, body: dict):
    """Shared structural checks only; never authenticates unsigned material."""
    members = context(boot, expected)
    for key in members.values():
        group.point(key, identity=False)
    c._label(body.get("actor"))
    c._require(
        COMMON <= set(body)
        and body["profile"] == PROFILE
        and body["context"] == expected
        and body["actor"] in members,
        "exact seed context/profile/actor",
    )
    return members


def artifact_id(raw: bytes) -> str:
    return c.content_id(ARTIFACT, raw)


def evaluation(group, commitments, index):
    return group.total(group.mul(pow(index, j, L), point) for j, point in enumerate(commitments))


@dataclass(frozen=True)
class Deal:
    original: bytes
    actor: str
    commitments: tuple[bytes, ...]
    encrypted: tuple[bytes, ...]


def verify_deal(group: Group, boot: Bootstrap, expected: dict, raw: bytes) -> Deal:
    body, members = authenticated(group, boot, expected, raw)
    commitments, encrypted = deal_algebra(group, body, members)
    return Deal(raw, body["actor"], commitments, encrypted)


def deal_algebra(group, body, members):
    c._closed(body, COMMON | {"commitments", "encrypted_shares", "proofs"})
    c._require(body["kind"] == "DEAL", "DEAL kind")
    for field, length in (("commitments", 3), ("encrypted_shares", 4), ("proofs", 4)):
        c._require(type(body[field]) is list and len(body[field]) == length, "complete PVSS array")
    commitments = tuple(group.point(binary(p, 32)) for p in body["commitments"])
    encrypted = tuple(group.point(binary(p, 32)) for p in body["encrypted_shares"])
    core = c._json({key: value for key, value in body.items() if key != "proofs"})
    for index, key in enumerate(members.values(), 1):
        group.verify(
            DEAL_PROOF,
            core + bytes([index]),
            group.h,
            evaluation(group, commitments, index),
            key,
            encrypted[index - 1],
            binary(body["proofs"][index - 1], 64),
        )
    return commitments, encrypted


@dataclass(frozen=True)
class Opening:
    original: bytes
    index: int
    share: bytes


def verify_open(
    group: Group, boot: Bootstrap, expected: dict, deal_raw: bytes, raw: bytes
) -> Opening:
    # Never trust a caller-constructed Deal dataclass as a validated capability.
    deal = verify_deal(group, boot, expected, deal_raw)
    body, members = authenticated(group, boot, expected, raw)
    index, share = open_algebra(group, body, members, deal_raw, deal)
    return Opening(raw, index, share)


def open_algebra(group, body, members, deal_raw, deal):
    c._closed(body, COMMON | {"deal_id", "share", "proof"})
    c._require(
        body["kind"] == "OPEN" and body["deal_id"] == artifact_id(deal_raw), "original DEAL binding"
    )
    index = list(members).index(body["actor"]) + 1
    share = group.point(binary(body["share"], 32))
    core = c._json({key: value for key, value in body.items() if key != "proof"})
    group.verify(
        OPEN_PROOF,
        core + bytes([index]),
        group.g,
        members[body["actor"]],
        share,
        deal.encrypted[index - 1],
        binary(body["proof"], 64),
    )
    return index, share


def verify_unsigned(group, boot, expected, original_body, actor, deal_raw=None):
    """Pre-sign algebra without a signature placeholder or authenticated object."""
    body = c._load(original_body)
    members = unsigned_context(group, boot, expected, body)
    c._require(body["actor"] == actor, "own unsigned PVSS intent")
    if body["kind"] == "DEAL":
        c._require(deal_raw is None, "DEAL has no prior deal")
        deal_algebra(group, body, members)
    elif body["kind"] == "OPEN":
        deal = verify_deal(group, boot, expected, deal_raw)
        open_algebra(group, body, members, deal_raw, deal)
    else:
        raise c.CodecError("unknown unsigned PVSS kind")
    return body


def reconstruct(
    group: Group, boot: Bootstrap, expected: dict, deal_raw: bytes, originals: tuple[bytes, ...]
) -> bytes:
    """Single polynomial point; never a seed, accepted history or release permission.

    This takes a selected reconstruction witness, NOT the retained event inventory.
    The producing fold must retain ALL invalid/duplicate/withheld occurrences.
    """
    c._require(type(originals) is tuple and len(originals) in (3, 4), "reconstruction witness")
    points = [verify_open(group, boot, expected, deal_raw, raw) for raw in originals]
    indices = [p.index for p in points]
    c._require(len(set(indices)) == len(indices), "distinct original recipients")
    weighted = []
    for item in points:
        weight = 1
        for other in indices:
            if other != item.index:
                weight = weight * (-other) * pow(item.index - other, -1, L) % L
        weighted.append(group.mul(weight, item.share))
    return group.total(weighted)
