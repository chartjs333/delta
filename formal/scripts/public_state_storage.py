"""Lossless field pooling for evidence storage; state hash preimages stay unchanged."""

import hashlib

from formal_artifacts import canonical_json_bytes
from public_state_projection import canonical_value, inventory, require

DOMAIN = b"deltareduce.public-state-field-storage.v1\0"


def field_id(value):
    return "sha256:" + hashlib.sha256(DOMAIN + canonical_json_bytes(value)).hexdigest()


def pack(trace):
    pool, states = {}, []
    for observation in trace["states"]:
        state = observation["state"]
        fields = {}
        for name, value in state["variables"].items():
            key = field_id(value)
            pool[key] = value
            fields[name] = key
        states.append({"root": observation["root"], "state": {**state, "variables": fields}})
    return {"storage": "FIELD_POOL_V1", "pool": pool, "trace": {**trace, "states": states}}


def unpack(container):
    require(
        type(container) is dict and set(container) == {"storage", "pool", "trace"}, "STORAGE_FIELDS"
    )
    require(container["storage"] == "FIELD_POOL_V1", "STORAGE_VERSION")
    pool, trace = container["pool"], container["trace"]
    require(type(pool) is dict and len(pool) <= 16384, "STORAGE_LIMIT")
    require(type(trace) is dict and set(trace) == {"profile", "states", "actions"}, "TRACE_FIELDS")
    require(type(trace["states"]) is list and 1 <= len(trace["states"]) <= 256, "TRACE_SIZE")
    for key, value in pool.items():
        canonical_value(value)
        require(field_id(value) == key, "STORAGE_FIELD_HASH")
    states, used = [], set()
    for observation in trace["states"]:
        require(
            type(observation) is dict and set(observation) == {"root", "state"},
            "OBSERVATION_FIELDS",
        )
        state = observation["state"]
        require(
            type(state) is dict and set(state) == {"profile", "model", "variables"}, "STATE_FIELDS"
        )
        refs = state["variables"]
        require(type(refs) is dict and set(refs) == set(inventory()), "STATE_COMPLETENESS")
        require(
            all(type(key) is str and key in pool for key in refs.values()), "STORAGE_MISSING_FIELD"
        )
        used.update(refs.values())
        states.append(
            {
                "root": observation["root"],
                "state": {**state, "variables": {name: pool[key] for name, key in refs.items()}},
            }
        )
    require(used == set(pool), "STORAGE_UNUSED_FIELD")
    return {**trace, "states": states}
