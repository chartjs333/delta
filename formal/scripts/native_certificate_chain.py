"""Proposal projection of exact PR50 certificate bytes into voted-body hashes.

No availability/root-of-input computation, signatures, native admission, WAL or
public-state refinement is claimed. EC's seed parent is independently supplied
metadata because it is absent from the feature-008 EC wire object.
"""

import hashlib
import json
import math
import re
from itertools import pairwise

from formal_artifacts import canonical_json_bytes
from native_isc_body import DOMAIN, MAX_BYTES, Context, require, text, u64

NATIVE_SEMANTICS = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
COMMON = set(Context.__annotations__) | {"formal_semantics_id", "schema_version", "type_name"}
FIELDS = {
    "INPUT_SET_CERTIFICATE": {"input_root", "quorum_threshold", "signer_ids", "tuples"},
    "SEED_TRANSCRIPT": {"input_set_certificate_id", "seed_id", "seed_profile_id", "share_ids"},
    "NORM_EVIDENCE": {"entries", "input_set_certificate_id", "norm_root"},
    "ELIGIBILITY_CERTIFICATE": {
        "entries",
        "input_set_certificate_id",
        "norm_evidence_id",
        "quorum_threshold",
        "robust_profile_id",
        "signer_ids",
    },
    "AGGREGATION_PLAN_CERTIFICATE": {
        "accumulator_proof_id",
        "bucket_assignments",
        "eligibility_certificate_id",
        "input_set_certificate_id",
        "iteration_count",
        "quorum_threshold",
        "seed_transcript_id",
        "signer_ids",
        "transcript_root",
        "weights",
    },
    "PARAMETER_SHARD_QC": {
        "aggregation_plan_certificate_id",
        "denominator",
        "domain_id",
        "eligibility_certificate_id",
        "input_leaf_ids",
        "input_set_certificate_id",
        "quorum_threshold",
        "result_numerators",
        "shard_id",
        "signer_ids",
    },
    "AGGREGATE_ROOT_QC": {
        "aggregation_plan_certificate_id",
        "eligibility_certificate_id",
        "input_set_certificate_id",
        "leaves",
        "merkle_root",
        "quorum_threshold",
        "required_keys",
        "signer_ids",
    },
}
DOMAINS = {
    "INPUT_SET_CERTIFICATE": "input-set-certificate",
    "SEED_TRANSCRIPT": "seed-transcript",
    "NORM_EVIDENCE": "norm-evidence",
    "ELIGIBILITY_CERTIFICATE": "eligibility-certificate",
    "AGGREGATION_PLAN_CERTIFICATE": "aggregation-plan-certificate",
    "PARAMETER_SHARD_QC": "parameter-shard-qc",
    "AGGREGATE_ROOT_QC": "aggregate-root-qc",
}


def digest(domain, raw):
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\0" + raw).hexdigest()


def content_id(doc):
    return digest("deltareduce.008." + DOMAINS[doc["type_name"]] + ".v1", canonical_json_bytes(doc))


def sequence(rows, encode):
    require(type(rows) is list and len(rows) <= 4096, "projection list limit/type")
    return u64(len(rows)) + b"".join(encode(row) for row in rows)


def keys(row, expected):
    require(type(row) is dict and set(row) == set(expected.split()), "exact nested fields")


def rational(row):
    keys(row, "numerator denominator")
    value = row["numerator"]
    require(type(value) is str and re.fullmatch(r"0|-?[1-9][0-9]*", value), "signed decimal")
    numerator = int(value)
    require(-(2**63) <= numerator < 2**63, "int64 numerator")
    return u64(numerator % 2**64) + u64(row["denominator"])


def input_tuple(row):
    keys(row, "availability_certificate_id commitment_id domain_id ticket_id")
    return b"".join(
        text(row[key])
        for key in ["availability_certificate_id", "commitment_id", "domain_id", "ticket_id"]
    )


def eligibility(row):
    keys(row, "accepted domain_id gamma reason_code ticket_id")
    require(type(row["accepted"]) is bool, "boolean")
    return (
        bytes([int(row["accepted"])])
        + text(row["domain_id"])
        + rational(row["gamma"])
        + text(row["reason_code"])
        + text(row["ticket_id"])
    )


def bucket(row):
    keys(row, "bucket_id ticket_id")
    return text(row["bucket_id"]) + text(row["ticket_id"])


def weight(row):
    keys(row, "alpha ticket_id")
    return rational(row["alpha"]) + text(row["ticket_id"])


def leaf(row):
    keys(row, "domain_id parameter_shard_qc_id shard_id")
    return text(row["domain_id"]) + text(row["parameter_shard_qc_id"]) + text(row["shard_id"])


def shard_key(row):
    keys(row, "domain_id shard_id")
    return text(row["domain_id"]) + text(row["shard_id"])


def merkle_root(leaves):
    require(type(leaves) is list and 0 < len(leaves) <= 4096, "nonempty Merkle leaves")
    for row in leaves:
        leaf(row)
    level = [
        digest("deltareduce.008.aggregate-leaf.v1", canonical_json_bytes(row)) for row in leaves
    ]
    while len(level) > 1:
        level = [
            digest(
                "deltareduce.008.aggregate-node.v1", bytes.fromhex(level[i][7:] + level[i + 1][7:])
            )
            if i + 1 < len(level)
            else level[i]
            for i in range(0, len(level), 2)
        ]
    return level[0]


def _integer(value, bits=64, positive=True):
    require(type(value) is int and int(positive) <= value < 2**bits, "integer range/type")


def _label(value):
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value), "label")


def _content(value):
    require(type(value) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", value), "content ID")


def _decimal(value, nonnegative=False):
    require(type(value) is str and re.fullmatch(r"0|-?[1-9][0-9]*", value), "decimal")
    number = int(value)
    require((0 if nonnegative else -(2**63)) <= number < 2**63, "decimal range")
    return number


def _list(value, key=lambda x: x, ordered=True):
    require(type(value) is list and 0 < len(value) <= 4096, "list bound/type")
    if ordered:
        projected = [key(item) for item in value]
        require(all(a < b for a, b in pairwise(projected)), "strict list order")


def _fraction(row):
    keys(row, "numerator denominator")
    n = _decimal(row["numerator"], True)
    _integer(row["denominator"])
    require(math.gcd(n, row["denominator"]) == 1, "reduced fraction")


def _profile(value, depth=0, budget=None):
    if budget is None:
        budget = [100000]
    budget[0] -= 1
    require(depth <= 16 and budget[0] >= 0, "proposal tree bound")
    if type(value) is dict:
        require(len(value) <= 64 and all(type(k) is str for k in value), "object bound/type")
        for key, child in value.items():
            _profile(key, depth + 1, budget)
            _profile(child, depth + 1, budget)
    elif type(value) is list:
        require(len(value) <= 4096, "proposal list bound")
        for child in value:
            _profile(child, depth + 1, budget)
    elif type(value) is str:
        require(len(value.encode("ascii")) <= 128, "proposal text bound")
    else:
        require(type(value) in (int, bool), "JSON primitive type")


def validate_shape(doc):
    """Supported certificate shape; does not authenticate signers or admission."""
    _profile(doc)
    for name in Context.__annotations__:
        if name in ("height", "view"):
            _integer(doc[name], positive=name == "height")
        elif name == "round_id":
            _label(doc[name])
        else:
            _content(doc[name])
    for name, value in doc.items():
        if name in COMMON:
            continue
        if name in ("quorum_threshold", "iteration_count"):
            _integer(value, 32)
        elif name == "denominator":
            _integer(value)
        elif name in ("domain_id", "shard_id"):
            _label(value)
        elif name.endswith("_id") or name.endswith("_root"):
            _content(value)
    if "signer_ids" in doc:
        _list(doc["signer_ids"])
        require(len(doc["signer_ids"]) >= doc["quorum_threshold"], "signer threshold")
        for signer in doc["signer_ids"]:
            _label(signer)
    if "tuples" in doc:
        _list(doc["tuples"], ordered=False)
        for row in doc["tuples"]:
            input_tuple(row)
            _content(row["availability_certificate_id"])
            _content(row["commitment_id"])
            _label(row["ticket_id"])
            _label(row["domain_id"])
        _list(doc["tuples"], lambda row: (row["ticket_id"], row["commitment_id"]))
    for name in ("share_ids", "input_leaf_ids"):
        if name in doc:
            _list(doc[name])
            for value in doc[name]:
                _content(value)
    if "entries" in doc:
        _list(doc["entries"], ordered=False)
        for row in doc["entries"]:
            if doc["type_name"] == "NORM_EVIDENCE":
                keys(row, "scale_denominator squared_norm ticket_id")
                _integer(row["scale_denominator"])
                _decimal(row["squared_norm"], True)
            else:
                eligibility(row)
                _fraction(row["gamma"])
                _label(row["domain_id"])
                _label(row["reason_code"])
            _label(row["ticket_id"])
        _list(doc["entries"], lambda row: row["ticket_id"])
    for name, encode in [("bucket_assignments", bucket), ("weights", weight)]:
        if name in doc:
            _list(doc[name], ordered=False)
            for row in doc[name]:
                encode(row)
                _label(row["ticket_id"])
                if name == "weights":
                    _fraction(row["alpha"])
                else:
                    _label(row["bucket_id"])
            _list(doc[name], lambda row: row["ticket_id"])
    if "result_numerators" in doc:
        _list(doc["result_numerators"], ordered=False)
        for value in doc["result_numerators"]:
            _decimal(value)
    for name, encode in [("leaves", leaf), ("required_keys", shard_key)]:
        if name in doc:
            _list(doc[name], ordered=False)
            for row in doc[name]:
                encode(row)
                _label(row["domain_id"])
                _label(row["shard_id"])
                if name == "leaves":
                    _content(row["parameter_shard_qc_id"])
            _list(doc[name], lambda row: (row["domain_id"], row["shard_id"]))
    if "leaves" in doc:
        require(doc["merkle_root"] == merkle_root(doc["leaves"]), "Merkle root")


def decode_certificate(raw, expected_id, kind):
    require(type(raw) is bytes and len(raw) <= MAX_BYTES, "certificate payload bound")
    require(kind in FIELDS, "supported certificate kind")
    try:
        doc = json.loads(raw)
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise ValueError("certificate JSON decoding") from exc
    require(type(doc) is dict and set(doc) == COMMON | FIELDS[kind], "certificate fields")
    require(
        doc["type_name"] == kind and doc["schema_version"] == "1.0.0", "certificate kind/version"
    )
    require(doc["formal_semantics_id"] == NATIVE_SEMANTICS, "pinned native semantics")
    require(canonical_json_bytes(doc) == raw, "canonical certificate bytes")
    require(content_id(doc) == expected_id, "certificate hash")
    validate_shape(doc)
    Context(**{key: doc[key] for key in Context.__annotations__}).encode()
    return doc


def voted_body(doc, seed_parent=None):
    kind = doc["type_name"]
    context = Context(**{key: doc[key] for key in Context.__annotations__}).encode()
    if kind == "INPUT_SET_CERTIFICATE":
        raw = context + text(doc["input_root"]) + sequence(doc["tuples"], input_tuple)
        domain = DOMAIN[:-1].decode("ascii")
    elif kind == "ELIGIBILITY_CERTIFICATE":
        require(type(seed_parent) is str, "independently bound EC seed parent missing")
        raw = (
            context
            + sequence(doc["entries"], eligibility)
            + b"".join(
                text(doc[key])
                for key in ["input_set_certificate_id", "norm_evidence_id", "robust_profile_id"]
            )
            + text(seed_parent)
        )
        domain = "deltareduce.vote.eligibility-body.v1"
    elif kind == "AGGREGATION_PLAN_CERTIFICATE":
        raw = (
            context
            + text(doc["accumulator_proof_id"])
            + sequence(doc["bucket_assignments"], bucket)
            + text(doc["eligibility_certificate_id"])
            + text(doc["input_set_certificate_id"])
            + u64(doc["iteration_count"])
            + text(doc["seed_transcript_id"])
            + text(doc["transcript_root"])
            + sequence(doc["weights"], weight)
        )
        domain = "deltareduce.vote.aggregation-plan-body.v1"
    elif kind == "AGGREGATE_ROOT_QC":
        raw = (
            context
            + b"".join(
                text(doc[key])
                for key in [
                    "aggregation_plan_certificate_id",
                    "eligibility_certificate_id",
                    "input_set_certificate_id",
                ]
            )
            + sequence(doc["leaves"], leaf)
            + text(doc["merkle_root"])
            + sequence(doc["required_keys"], shard_key)
        )
        domain = "deltareduce.vote.aggregate-root-body.v1"
    else:
        raise ValueError("unsupported voted body")
    require(len(raw) <= MAX_BYTES, "body bound")
    return {"domain": domain, "payload_hex": raw.hex(), "body_id": digest(domain, raw)}


def bind_graph(store, root_id, ec_seed_bindings):
    """Resolve anchored exact bytes and parent edges, NOT native admission.

    root_id and ec_seed_bindings require separate native-state authentication;
    the supplied store does not establish that provenance.
    """
    require(type(store) is dict and len(store) <= 4096, "store bound")
    loaded = {}

    def load(identifier, kind):
        require(identifier in store, "missing artifact")
        doc = decode_certificate(store[identifier], identifier, kind)
        if loaded:
            first = next(iter(loaded.values()))
            require(all(doc[key] == first[key] for key in Context.__annotations__), "mixed context")
        loaded[identifier] = doc
        return doc

    root = load(root_id, "AGGREGATE_ROOT_QC")
    plan_id, ec_id, isc_id = [
        root[key]
        for key in [
            "aggregation_plan_certificate_id",
            "eligibility_certificate_id",
            "input_set_certificate_id",
        ]
    ]
    plan = load(plan_id, "AGGREGATION_PLAN_CERTIFICATE")
    ec = load(ec_id, "ELIGIBILITY_CERTIFICATE")
    isc = load(isc_id, "INPUT_SET_CERTIFICATE")
    require(
        plan["eligibility_certificate_id"] == ec_id
        and plan["input_set_certificate_id"] == isc_id
        and ec["input_set_certificate_id"] == isc_id,
        "parent edge",
    )
    seed_id = plan["seed_transcript_id"]
    require(ec_seed_bindings.get(ec_id) == seed_id, "independent EC seed binding")
    seed = load(seed_id, "SEED_TRANSCRIPT")
    norms = load(ec["norm_evidence_id"], "NORM_EVIDENCE")
    require(
        seed["input_set_certificate_id"] == norms["input_set_certificate_id"] == isc_id,
        "seed/norm parent",
    )
    require(merkle_root(root["leaves"]) == root["merkle_root"], "Merkle root")
    actual_keys = [
        {"domain_id": row["domain_id"], "shard_id": row["shard_id"]} for row in root["leaves"]
    ]
    require(actual_keys == root["required_keys"], "complete ordered shard coverage")
    pairs = [(row["domain_id"], row["shard_id"]) for row in actual_keys]
    require(pairs == sorted(set(pairs)), "unique ordered shard keys")
    for row in root["leaves"]:
        parameter = load(row["parameter_shard_qc_id"], "PARAMETER_SHARD_QC")
        require(
            parameter["domain_id"] == row["domain_id"] and parameter["shard_id"] == row["shard_id"],
            "parameter leaf key",
        )
        require(
            parameter["aggregation_plan_certificate_id"] == plan_id
            and parameter["eligibility_certificate_id"] == ec_id
            and parameter["input_set_certificate_id"] == isc_id,
            "parameter parent edge",
        )
    return {
        "loaded_ids": sorted(loaded),
        "bodies": {
            "ISC": voted_body(isc),
            "EC": voted_body(ec, seed_id),
            "APC": voted_body(plan),
            "ROOT": voted_body(root),
        },
        "native_semantics_id": NATIVE_SEMANTICS,
        "native_export_authenticated": False,
        "native_admission_verified": False,
        "scope": "EXACT_CERTIFICATE_BYTES_PARENT_EDGES_AND_BODY_PROJECTION_ONLY",
    }
