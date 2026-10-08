"""T047/T053: resolve original keys from independently pinned profile metadata.

This is the bootstrap authority subrelation. Initial configuration bytes are
retained in full; the other initial-state fields still require native source
decoding. An imported registry never supplies its own trust anchor.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source.authentication import Bootstrap, registry
from formal.reference.profile_source import metadata as m
from formal.reference.storage_source import codec as storage


@dataclass(frozen=True)
class Authorities:
    validators: Bootstrap
    storage: storage.Bootstrap
    initial_config: bytes
    original_validator_keys: tuple[bytes, ...]
    original_storage_registry: bytes
    original_storage_keys: tuple[bytes, ...]


def resolve(
    meta: m.Metadata,
    validator_keys: tuple[bytes, ...],
    storage_registry: bytes,
    storage_keys: tuple[bytes, ...],
) -> Authorities:
    boot = m.validate(meta.bootstrap_bytes, "BOOTSTRAP")
    store = dict(meta.original_artifacts)

    def retained(raw):
        crypto._require(
            store.get(m.raw_id(raw)) == raw, "original key/registry in complete source inventory"
        )

    crypto._require(
        type(validator_keys) is tuple and type(storage_keys) is tuple,
        "original immutable key objects",
    )
    by_id = {}
    for raw in validator_keys:
        retained(raw)
        key = crypto.decode_key(raw)
        key_id = crypto.content_id(crypto.KEY_DOMAIN, raw)
        crypto._require(key_id not in by_id, "duplicate original validator key object")
        by_id[key_id] = key
    crypto._require(
        set(by_id) == {v["key_ref"] for v in boot["validators"]},
        "exact independent validator key refs",
    )
    validators = Bootstrap(
        boot["formal_semantics_id"],
        boot["origin_id"],
        boot["validator_epoch_id"],
        tuple((v["validator_id"], by_id[v["key_ref"]]) for v in boot["validators"]),
    )
    registry(validators)

    initial_ref = boot["initial_config_ref"]
    initial = store.get(initial_ref["content_id"])
    crypto._require(
        type(initial) is bytes
        and len(initial) == int(initial_ref["byte_length"])
        and m.raw_id(initial) == initial_ref["content_id"],
        "original independently pinned initial config",
    )
    # ADR0016 selects this original field. Preserve all surrounding bytes and
    # fields for the complete initial-state loader; no authority from retyping.
    initial_value = storage.load(initial)
    crypto._require(
        "storage_authority" in initial_value, "mandatory original initial storage authority"
    )
    selected = m.closed(
        initial_value["storage_authority"], {"storage_epoch_id", "storage_registry_id"}
    )
    crypto._label(selected["storage_epoch_id"])
    crypto._id(selected["storage_registry_id"])
    retained(storage_registry)
    doc = m.closed(storage.load(storage_registry), storage.REGISTRY)
    crypto._require(
        storage.content_id(storage.REGISTRY_DOMAIN, storage_registry)
        == selected["storage_registry_id"]
        and doc["storage_epoch_id"] == selected["storage_epoch_id"]
        and doc["origin_id"] == boot["origin_id"]
        and doc["formal_semantics_id"] == boot["formal_semantics_id"],
        "registry selected by independent initial config, not imported self-election",
    )
    resolved = {}
    for raw in storage_keys:
        retained(raw)
        key = crypto.decode_key(raw)
        key_id = crypto.content_id(storage.KEY_DOMAIN, raw)
        crypto._require(key_id not in resolved, "duplicate original storage key object")
        resolved[key_id] = key
    crypto._require(
        type(doc["members"]) is list and bool(doc["members"]), "original storage enrollment"
    )
    members = []
    for member in doc["members"]:
        m.closed(member, {"storage_id", "key_id", "roles"})
        crypto._label(member["storage_id"])
        crypto._id(member["key_id"])
        crypto._require(
            member["roles"] == ["storage"] and member["key_id"] in resolved,
            "original storage role/key",
        )
        members.append((member["storage_id"], resolved[member["key_id"]]))
    storage_boot = storage.Bootstrap(
        boot["formal_semantics_id"], boot["origin_id"], selected["storage_epoch_id"], tuple(members)
    )
    storage.bind_registry(storage_boot, storage_registry, storage_keys)
    return Authorities(
        validators, storage_boot, initial, validator_keys, storage_registry, storage_keys
    )
