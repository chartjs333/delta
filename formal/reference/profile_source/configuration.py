"""R2.3: source-bound configuration decoding in the isolated future generation.

DRC1 tags, type code/domain and all 22 original fields are retained. The selected
S/retention contracts require availability_policy.storage_binding; the existing
immutable input-close policy is also part of that full signed body. This module
does NOT infer proposal, delivery or finality
from a valid signature, and never admits a legacy config in the new generation.
"""

from dataclasses import dataclass
from hashlib import sha256

from formal.reference.isc_crypto.codec import (
    CodecError,
    _decimal,
    _id,
    _label,
    _require,
    _uint,
    content_id,
)
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.non_isc.authentication import (
    CONTRACT as SIGNATURE_CONTRACT,
)
from formal.reference.non_isc.authentication import (
    AuthorityInputs,
    VerifiedSignature,
    authenticate,
)
from formal.reference.profile_source.metadata import closed
from formal.reference.storage_source import codec as storage
from formal.reference.storage_source import retention

MAX_FRAME, MAX_TEXT, MAX_ITEMS, MAX_DEPTH = 16 * 1024**2, 4 * 1024**2, 100000, 32
DOMAIN = "deltareduce:003:round-config:v1"
HEADER = b"DRC1\x01\x00\x00\x01"
U32_FIELDS = {
    "availability_threshold",
    "batch_budget",
    "fault_tolerance",
    "quorum_threshold",
    "step_budget",
    "ticket_count",
}
DECIMAL_FIELDS = {"hard_deadline_tick", "height", "soft_deadline_tick", "view"}
ID_FIELDS = {
    "dataset_manifest_id",
    "formal_semantics_id",
    "parent_checkpoint_id",
    "parameter_schema_id",
    "validator_epoch_id",
}
TEXT_FIELDS = {"protocol_version", "round_id", "schema_version", "type_name"}
FIELDS = (
    U32_FIELDS
    | DECIMAL_FIELDS
    | ID_FIELDS
    | TEXT_FIELDS
    | {
        "availability_policy",
        "domain_ticket_counts",
        "integer_profile",
        "validator_ids",
    }
)


def ascii_text(value):
    _require(type(value) is str and all(32 <= ord(x) <= 126 for x in value), "DRC1 printable ASCII")
    raw = value.encode("ascii")
    _require(len(raw) <= MAX_TEXT, "existing DRC1 text bound")
    return b"\x21" + _uint(len(raw), 4) + raw


def encode_value(value, depth=0):
    _require(depth <= MAX_DEPTH, "existing DRC1 depth bound")
    if type(value) is int:
        return b"\x10" + _uint(value, 8)
    if type(value) is str:
        return ascii_text(value)
    if type(value) is list:
        _require(len(value) <= MAX_ITEMS, "existing DRC1 collection bound")
        return b"\x30" + _uint(len(value), 4) + b"".join(encode_value(x, depth + 1) for x in value)
    if type(value) is dict:
        _require(len(value) <= MAX_ITEMS, "existing DRC1 collection bound")
        _require(
            all(
                type(k) is str
                and k
                and all(c in "abcdefghijklmnopqrstuvwxyz_0123456789" for c in k)
                for k in value
            ),
            "DRC1 schema keys",
        )
        return (
            b"\x31"
            + _uint(len(value), 4)
            + b"".join(ascii_text(k) + encode_value(v, depth + 1) for k, v in sorted(value.items()))
        )
    raise CodecError("config DRC1 field type")


class Reader:
    def __init__(self, raw):
        _require(type(raw) is bytes and len(raw) <= MAX_FRAME, "existing DRC1 envelope bound")
        self.raw, self.at = raw, 0

    def take(self, count):
        _require(0 <= count <= len(self.raw) - self.at, "truncated DRC1 field")
        result = self.raw[self.at : self.at + count]
        self.at += count
        return result

    def count(self):
        return int.from_bytes(self.take(4), "big")

    def value(self, depth=0):
        _require(depth <= MAX_DEPTH, "existing DRC1 depth bound")
        tag = self.take(1)
        if tag == b"\x10":
            return int.from_bytes(self.take(8), "big")
        if tag == b"\x21":
            length = self.count()
            _require(length <= MAX_TEXT, "existing DRC1 text bound")
            raw = self.take(length)
            _require(all(32 <= b <= 126 for b in raw), "DRC1 printable ASCII")
            return raw.decode("ascii")
        if tag in (b"\x30", b"\x31"):
            count = self.count()
            _require(
                count <= MAX_ITEMS and count <= len(self.raw) - self.at, "bounded DRC1 collection"
            )
            if tag == b"\x30":
                return [self.value(depth + 1) for _ in range(count)]
            result, previous = {}, ""
            for _ in range(count):
                key = self.value(depth + 1)
                _require(type(key) is str and key > previous, "duplicate/unordered DRC1 map key")
                previous = key
                result[key] = self.value(depth + 1)
            return result
        raise CodecError("config DRC1 field tag")


def validate(value):
    closed(value, FIELDS)
    for key in U32_FIELDS:
        _uint(value[key], 4)
    for key in DECIMAL_FIELDS:
        _decimal(value[key])
    for key in ID_FIELDS:
        _id(value[key])
    for key in TEXT_FIELDS:
        ascii_text(value[key])
    _require(
        value["type_name"] == "ROUND_CONFIG" and value["schema_version"] == "2.0.0",
        "future closed configuration generation, no legacy fallback",
    )
    _label(value["round_id"])
    members = value["validator_ids"]
    _require(type(members) is list, "original validator collection")
    for member in members:
        _label(member)
    _require(members == sorted(set(members)), "original ordered validator identities")
    _require(
        len(members) == 3 * value["fault_tolerance"] + 1
        and value["quorum_threshold"] == 2 * value["fault_tolerance"] + 1,
        "original 3f+1 / 2f+1",
    )
    _require(
        int(value["soft_deadline_tick"]) < int(value["hard_deadline_tick"]),
        "original deadline order",
    )
    profile = closed(
        value["integer_profile"], {"accumulator_bits", "byte_order", "profile_id", "value_bits"}
    )
    for key in ("accumulator_bits", "value_bits"):
        _uint(profile[key], 4)
    for key in ("byte_order", "profile_id"):
        ascii_text(profile[key])
    rows = value["domain_ticket_counts"]
    _require(type(rows) is list, "original domain plan")
    names = []
    for row in rows:
        closed(row, {"domain_id", "ticket_count"})
        ascii_text(row["domain_id"])
        _uint(row["ticket_count"], 4)
        names.append(row["domain_id"])
    _require(
        names == sorted(set(names))
        and sum(row["ticket_count"] for row in rows) == value["ticket_count"],
        "original ordered complete ticket plan",
    )
    policy = closed(value["availability_policy"], {"close_policy", "storage_binding"})
    _require(
        policy["close_policy"] in ("OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE"),
        "existing immutable RoundConfig input-close policy",
    )
    binding = closed(policy["storage_binding"], retention.BINDING_KEYS)
    _id(binding["storage_registry_id"])
    _label(binding["storage_epoch_id"])
    _label(binding["retention_epoch_id"])
    threshold = _decimal(binding["threshold"], positive=True)
    _require(
        threshold < 2**32 and threshold == value["availability_threshold"],
        "same original availability threshold",
    )
    source = retention.decode_source(storage.canonical(binding["retention_policy_source"]))
    _require(
        source["retention_epoch_id"] == binding["retention_epoch_id"],
        "contextual original retention label",
    )
    return value


def encode(value):
    validate(value)
    payload = encode_value(value)
    result = HEADER + _uint(len(payload), 4) + payload
    _require(len(result) <= MAX_FRAME, "existing DRC1 envelope bound")
    return result


def decode(raw):
    reader = Reader(raw)
    _require(reader.take(8) == HEADER, "RoundConfig DRC1 header/type")
    _require(reader.count() == len(raw) - 12, "RoundConfig exact payload size")
    value = reader.value()
    _require(reader.at == len(raw), "RoundConfig trailing bytes")
    validate(value)
    _require(encode(value) == raw, "RoundConfig exact canonical source")
    return value


def vote_context(height, epoch):
    raw = _id(epoch).encode("ascii")
    preimage = b"deltareduce.vote-context.config.v1\0" + _uint(height, 8) + _uint(len(raw), 8) + raw
    return "sha256:" + sha256(preimage).hexdigest()


@dataclass(frozen=True)
class BoundConfig:
    original: bytes
    body_id: str
    context_id: str
    parent: str
    round_id: str
    height: int
    view: int
    close_policy: str
    storage_binding: retention.StorageBinding


@dataclass(frozen=True)
class NativeHeader:
    configuration: BoundConfig
    original_state: bytes
    original_policy: bytes
    actor: str


def bind_native_header(config, original_state, original_policy, actor):
    """Join original immutable headers without erasing any policy collection.

    This is one source conjunct, not a constructor of a legal initial state or
    a proof of complete P0. Phase, current view, sequence, candidate inventory,
    local clock and all downstream collections still come from the producer
    prefix. In particular, current view is not reset to the CONFIG vote's view.
    """
    from formal.reference.isc_source.policy import decode as decode_policy
    from formal.reference.profile_source.capsule_binding import read_state

    _require(type(config) is BoundConfig, "original bound configuration required")
    body = decode(config.original)
    _require(config.body_id == content_id(DOMAIN, config.original), "original config identity")
    native = read_state(original_state, body["formal_semantics_id"])
    policy = decode_policy(original_policy)
    _require(
        policy["local_validator_id"] == actor
        and actor in body["validator_ids"]
        and policy["validator_ids"] == body["validator_ids"]
        and policy["validator_epoch_id"] == body["validator_epoch_id"]
        and policy["round_id"] == native["round_id"] == body["round_id"]
        and policy["round_config_id"] == native["config_id"] == config.body_id,
        "original configuration/native actor, epoch and round context",
    )
    _require(
        int(native["height"]) == int(body["height"])
        and native["parent_checkpoint_id"] == body["parent_checkpoint_id"]
        and native["ticket_count"] == body["ticket_count"]
        and policy["soft_deadline_tick"] == int(body["soft_deadline_tick"])
        and policy["hard_deadline_tick"] == int(body["hard_deadline_tick"]),
        "original configuration/native parent, height, count and deadlines",
    )
    snapshot = policy["snapshot"]
    _require(
        snapshot["parameter_schema_id"] == body["parameter_schema_id"]
        and snapshot["state_id"] == content_id("deltareduce:003:round-state:v1", original_state),
        "original configuration/native schema and complete coarse-state ID",
    )
    return NativeHeader(config, original_state, original_policy, actor)


def bind(
    bootstrap: Bootstrap, storage_bootstrap: storage.Bootstrap, original: bytes, declaration: bytes
):
    """Original full configuration, all original fields retained and hash-bound.

    The bootstrap arguments must originate in the independently pinned profile
    bootstrap/initial config. This helper cannot authenticate those arguments or
    replace the producer-prefix check. Its result is neither finality nor READY.
    """
    value = decode(original)
    registry(bootstrap)
    _require(
        storage_bootstrap.formal_semantics_id == bootstrap.formal_semantics_id
        and storage_bootstrap.origin_id == bootstrap.origin_id,
        "same independently selected origin and semantics across roles",
    )
    _require(
        value["formal_semantics_id"] == bootstrap.formal_semantics_id
        and value["validator_epoch_id"] == bootstrap.validator_epoch_id
        and value["validator_ids"] == [name for name, _ in bootstrap.validators]
        and value["fault_tolerance"] == 1
        and value["quorum_threshold"] == 3,
        "independent fixed-epoch configuration authority",
    )
    binding = retention.bind_policy(
        retention.CONTRACT,
        storage_bootstrap,
        storage.canonical(value["availability_policy"]["storage_binding"]),
        declaration,
    )
    return BoundConfig(
        original,
        content_id(DOMAIN, original),
        vote_context(int(value["height"]), value["validator_epoch_id"]),
        value["parent_checkpoint_id"],
        value["round_id"],
        int(value["height"]),
        int(value["view"]),
        value["availability_policy"]["close_policy"],
        binding,
    )


def bind_vote(config: BoundConfig, signed: VerifiedSignature):
    value, vote = signed.vote, signed.vote.original
    _require(
        value.kind == "ROUND_CONFIG"
        and vote.body_hash == config.body_id
        and vote.context_id == config.context_id
        and vote.height == config.height
        and vote.view == config.view
        and vote.round_id == config.round_id,
        "authenticated original Vote covers exact full configuration",
    )
    # Retain the original Vote/Gn. No new vote identity, slot or certificate.
    return signed


def authenticate_config_vote(
    bootstrap, storage_bootstrap, backend, original, declaration, artifact
):
    config = bind(bootstrap, storage_bootstrap, original, declaration)
    signed = authenticate(AuthorityInputs(bootstrap, SIGNATURE_CONTRACT), backend, artifact)
    return config, bind_vote(config, signed)
