"""T047/T053: finite, original-byte profile metadata; never snapshot authority.

The primitive trust-side input is independent of the imported package. This
module checks the profile's four control-document shapes, retained source
inventory, exact references and trusted-log chain. Certificate authentication
and native producing-history replay are separate required composition steps.
No filesystem activation, networking, recovery runtime or public projection.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from formal.reference.isc_crypto.codec import CodecError, _decimal, _id, _pairs, _require

PROFILE = "snapshot-provenance-linux-single-epoch-v1"
MAX_CONTROL = 4 * 1024 * 1024
MAX_REFS = 65536
MAX_SOURCE_BYTES = 64 * 1024**3
MAX_EVENTS = MAX_RECORDS = 1000000
DOMAINS = {
    "BOOTSTRAP": "deltareduce.snapshot-provenance.bootstrap.v1",
    "MANIFEST": "deltareduce.snapshot-provenance.manifest.v1",
    "SOURCE_INDEX": "deltareduce.snapshot-provenance.source-index.v1",
    "TRUST_RECORD": "deltareduce.snapshot-provenance.trust-record.v1",
}
COMMON = {"type_name", "schema_version", "profile_id"}
FIELDS = {
    "BOOTSTRAP": {
        "origin_id",
        "genesis_ref",
        "initial_config_ref",
        "validator_epoch_id",
        "validators",
        "quorum_threshold",
        "local_validator_id",
        "runtime_build_id",
        "formal_semantics_id",
        "schema_set_id",
        "signature_codec_id",
        "producer_rules_id",
        "initial_anchor",
    },
    "MANIFEST": {
        "origin_id",
        "validator_epoch_id",
        "local_validator_id",
        "bootstrap_id",
        "formal_semantics_id",
        "schema_set_id",
        "anchor",
        "apply_qc_ref",
        "apply_candidate_ref",
        "snapshot_ref",
        "source_index_ref",
        "cut_event_index",
        "target_event_index",
        "journals",
        "artifacts",
    },
    "SOURCE_INDEX": {
        "origin_id",
        "validator_epoch_id",
        "local_validator_id",
        "genesis_ref",
        "events",
        "artifacts",
        "original_journal_refs",
    },
}
PINS = (
    "runtime_build_id",
    "formal_semantics_id",
    "schema_set_id",
    "signature_codec_id",
    "producer_rules_id",
)


def closed(value: Any, keys: set[str]) -> dict:
    _require(type(value) is dict and set(value) == keys, "closed profile field set")
    return value


def text(value: Any, *, nonempty: bool = False) -> str:
    _require(type(value) is str, "profile string required")
    _require(not nonempty or bool(value), "nonempty profile string")
    _require(all(32 <= ord(c) <= 126 and c not in '\\"' for c in value), "profile ASCII")
    return value


def scalar_tree(value: Any) -> None:
    if type(value) is str:
        text(value)
    elif type(value) is bool:
        pass
    elif type(value) is list:
        for item in value:
            scalar_tree(item)
    elif type(value) is dict:
        for key, item in value.items():
            text(key, nonempty=True)
            scalar_tree(item)
    else:
        raise CodecError("profile permits strings, booleans, arrays and objects only")


def canonical(value: dict) -> bytes:
    try:
        scalar_tree(value)
        raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
            "ascii"
        )
    except (RecursionError, UnicodeError) as exc:
        raise CodecError("profile canonical encoding") from exc
    _require(len(raw) <= MAX_CONTROL, "approved control-document budget")
    return raw


def no_number(_: str) -> None:
    raise CodecError("profile number/null is not an exact decimal string")


def load(raw: bytes) -> dict:
    _require(type(raw) is bytes and len(raw) <= MAX_CONTROL, "original bounded profile bytes")
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_pairs,
            parse_int=no_number,
            parse_float=no_number,
            parse_constant=no_number,
        )
        _require(type(value) is dict and canonical(value) == raw, "profile canonical re-encoding")
        return value
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise CodecError("profile decoding: " + str(exc)) from exc


def raw_id(raw: bytes) -> str:
    _require(type(raw) is bytes, "original immutable bytes")
    return "sha256:" + sha256(raw).hexdigest()


def reference(value: Any) -> dict:
    ref = closed(
        value, {"schema_version", "schema_id", "media_type", "byte_length", "content_id", "locator"}
    )
    _require(ref["schema_version"] == "1.0.0", "artifact-ref version")
    _require(
        re.fullmatch(r"SCHEMA-[A-Z0-9-]+-V[0-9]+", text(ref["schema_id"])) is not None,
        "artifact schema ID",
    )
    _require(1 <= len(text(ref["media_type"])) <= 255, "artifact media type")
    _decimal(ref["byte_length"])
    _id(ref["content_id"])
    locator = text(ref["locator"])
    _require(
        re.fullmatch(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*", locator) is not None,
        "relative artifact locator",
    )
    _require(all(part not in (".", "..") for part in locator.split("/")), "artifact traversal")
    return ref


def refs(value: Any) -> list[dict]:
    _require(type(value) is list and len(value) <= MAX_REFS, "approved artifact-ref budget")
    result = [reference(item) for item in value]
    ids = [item["content_id"] for item in result]
    _require(ids == sorted(set(ids)), "artifact inventory sorted unique")
    _require(
        sum(int(item["byte_length"]) for item in result) <= MAX_SOURCE_BYTES,
        "approved original-byte inventory budget",
    )
    return result


def anchor(value: Any) -> dict:
    value = closed(value, {"height", "checkpoint_id", "optimizer_id", "apply_qc_id"})
    _decimal(value["height"])
    for key in ("checkpoint_id", "optimizer_id", "apply_qc_id"):
        _id(value[key])
    return value


def cuts(value: Any) -> list[dict]:
    _require(type(value) is list, "explicit journal inventory")
    keys, count = [], 0
    for item in value:
        row = closed(
            item,
            {"actor_id", "journal_id", "ref", "entry_count", "first_sequence", "last_sequence"},
        )
        keys.append((text(row["actor_id"], nonempty=True), text(row["journal_id"], nonempty=True)))
        ref = reference(row["ref"])
        n = _decimal(row["entry_count"])
        first, last = _decimal(row["first_sequence"]), _decimal(row["last_sequence"])
        if n == 0:
            _require(
                first == last == 0
                and ref["byte_length"] == "0"
                and ref["content_id"] == raw_id(b""),
                "explicit empty journal",
            )
        else:
            _require(
                first <= last and last - first + 1 == n and int(ref["byte_length"]) > 0,
                "exact journal sequence interval",
            )
        count += n
    _require(keys == sorted(set(keys)), "journal identities sorted unique")
    _require(count <= MAX_RECORDS, "approved original record budget")
    return value


def journal_ranges(value: Any) -> list[dict]:
    """Manifest cut and target are separate original prefixes of the same journal."""
    _require(type(value) is list, "explicit cut/target journal inventory")
    keys, count = [], 0
    for row in value:
        closed(row, {"actor_id", "journal_id", "cut", "target"})
        identity = {key: row[key] for key in ("actor_id", "journal_id")}
        keys.append((text(row["actor_id"], nonempty=True), text(row["journal_id"], nonempty=True)))
        for side in ("cut", "target"):
            closed(row[side], {"ref", "entry_count", "first_sequence", "last_sequence"})
            cuts([{**identity, **row[side]}])
        _require(
            int(row["cut"]["entry_count"]) <= int(row["target"]["entry_count"]),
            "journal cut <= target",
        )
        count += int(row["target"]["entry_count"])
    _require(
        keys == sorted(set(keys)) and count <= MAX_RECORDS, "original journal inventory/budget"
    )
    return value


def validate(raw: bytes, kind: str) -> dict:
    _require(kind in DOMAINS, "independent profile document dispatch")
    obj = load(raw)
    if kind == "TRUST_RECORD":
        fields = {"ordinal", "previous_record_id", "bootstrap_id", "kind", "anchor", "journal_cuts"}
        if obj.get("kind") in ("ACTIVATE", "ANCHOR"):
            fields |= {"generation_id", "manifest_id"}
        closed(obj, COMMON | fields)
    else:
        closed(obj, COMMON | FIELDS[kind])
    _require(
        obj["type_name"] == kind and obj["schema_version"] == "1" and obj["profile_id"] == PROFILE,
        "fixed profile/schema/type",
    )
    if kind != "TRUST_RECORD":
        _id(obj["origin_id"])
        _id(obj["validator_epoch_id"])
        text(obj["local_validator_id"], nonempty=True)
    if kind == "BOOTSTRAP":
        reference(obj["genesis_ref"])
        reference(obj["initial_config_ref"])
        anchor(obj["initial_anchor"])
        for key in PINS:
            _id(obj[key])
        _require(obj["quorum_threshold"] == "3", "fixed profile quorum")
        members = obj["validators"]
        _require(type(members) is list and len(members) == 4, "fixed profile committee")
        names, keys = [], []
        for member in members:
            closed(member, {"validator_id", "key_ref", "roles"})
            names.append(text(member["validator_id"], nonempty=True))
            keys.append(_id(member["key_ref"]))
            _require(member["roles"] == ["validator"], "enrolled validator role")
        _require(
            names == sorted(set(names)) and len(set(keys)) == 4, "independent unique enrollment"
        )
        _require(obj["local_validator_id"] in names, "retained enrolled identity")
    elif kind == "MANIFEST":
        for key in ("bootstrap_id", "formal_semantics_id", "schema_set_id"):
            _id(obj[key])
        anchor(obj["anchor"])
        for key in ("apply_qc_ref", "apply_candidate_ref", "snapshot_ref", "source_index_ref"):
            reference(obj[key])
        first, last = _decimal(obj["cut_event_index"]), _decimal(obj["target_event_index"])
        _require(first <= last <= MAX_EVENTS, "finite source cut <= target")
        journal_ranges(obj["journals"])
        refs(obj["artifacts"])
    elif kind == "SOURCE_INDEX":
        reference(obj["genesis_ref"])
        refs(obj["artifacts"])
        cuts(obj["original_journal_refs"])
        events = obj["events"]
        _require(type(events) is list and len(events) <= MAX_EVENTS, "approved source-event budget")
        for index, event in enumerate(events):
            closed(event, {"actor_id", "action_id", "original_ref", "input_refs", "dependencies"})
            text(event["actor_id"], nonempty=True)
            text(event["action_id"], nonempty=True)
            reference(event["original_ref"])
            _require(type(event["input_refs"]) is list, "original ordered inputs")
            for ref in event["input_refs"]:
                reference(ref)
            deps = event["dependencies"]
            _require(type(deps) is list, "explicit original dependencies")
            values = [_decimal(dep) for dep in deps]
            _require(
                values == sorted(set(values)) and all(dep < index for dep in values),
                "strict backward source dependencies",
            )
        # Repeated original messages are distinct occurrences in this ordered
        # list. Do not turn it into a set or require unique original_ref values.
    else:
        _decimal(obj["ordinal"])
        _id(obj["bootstrap_id"])
        anchor(obj["anchor"])
        cuts(obj["journal_cuts"])
        _require(obj["kind"] in ("INIT", "ACTIVATE", "ANCHOR"), "known trust record kind")
        if obj["kind"] == "INIT":
            _require(
                obj["ordinal"] == "0" and obj["previous_record_id"] == "GENESIS",
                "initial trust record",
            )
        else:
            _require(int(obj["ordinal"]) > 0, "noninitial trust ordinal")
            for key in ("previous_record_id", "generation_id", "manifest_id"):
                _id(obj[key])
    return obj


def document_id(raw: bytes, kind: str) -> str:
    validate(raw, kind)
    return "sha256:" + sha256(DOMAINS[kind].encode("ascii") + b"\0" + raw).hexdigest()


@dataclass(frozen=True)
class PrimitiveTrust:
    """Independent T/provisioning facts, not parsed from the imported D bundle.

    Complete original bytes are retained, including the latest trusted log and
    own journals. Custody/barrier faithfulness is the explicit Profile premise;
    no public success, arbitrary legal-origin flag or recovered equality occurs.
    """

    bootstrap_raw_sha256: str
    source_index_raw_sha256: str
    approved_pins: tuple[tuple[str, str], ...]
    bootstrap: bytes
    trusted_log: bytes
    own_journals: tuple[tuple[str, str, bytes], ...]


@dataclass(frozen=True)
class Metadata:
    bootstrap_bytes: bytes
    manifest_bytes: bytes
    source_index_bytes: bytes
    trusted_record_bytes: tuple[bytes, ...]
    original_artifacts: tuple[tuple[str, bytes], ...]
    original_own_journals: tuple[tuple[str, str, bytes], ...]
    floor: dict
    cut: int
    target: int


def scan_trust(raw: bytes) -> tuple[bytes, ...]:
    _require(type(raw) is bytes, "original trusted log bytes")
    at, records = 0, []
    while at < len(raw):
        _require(
            len(records) < MAX_RECORDS and len(raw) - at >= 4, "trusted log budget/truncated length"
        )
        length = int.from_bytes(raw[at : at + 4], "big")
        _require(
            length <= MAX_CONTROL and len(raw) - at - 4 >= length + 32, "trusted log complete frame"
        )
        body = raw[at + 4 : at + 4 + length]
        digest = raw[at + 4 + length : at + 4 + length + 32]
        _require(
            bytes.fromhex(document_id(body, "TRUST_RECORD")[7:]) == digest, "trusted log digest"
        )
        records.append(body)
        at += 4 + length + 32
    _require(bool(records), "trusted log required; no empty reset")
    return tuple(records)


def check_metadata(
    trust: PrimitiveTrust,
    manifest: bytes,
    source_index: bytes,
    artifacts: tuple[tuple[str, bytes], ...],
) -> Metadata:
    _require(type(trust) is PrimitiveTrust, "independent primitive trust input")
    _require(
        raw_id(trust.bootstrap) == trust.bootstrap_raw_sha256, "independent bootstrap raw digest"
    )
    _require(
        raw_id(source_index) == trust.source_index_raw_sha256,
        "independently retained original source inventory",
    )
    boot = validate(trust.bootstrap, "BOOTSTRAP")
    _require(
        tuple(sorted(trust.approved_pins)) == tuple((key, boot[key]) for key in sorted(PINS)),
        "independent exact approved verifier/codec/producer pins",
    )
    boot_id = document_id(trust.bootstrap, "BOOTSTRAP")
    imp, source = validate(manifest, "MANIFEST"), validate(source_index, "SOURCE_INDEX")
    for key in ("origin_id", "validator_epoch_id", "local_validator_id"):
        _require(boot[key] == imp[key] == source[key], "same independent origin/epoch/identity")
    _require(
        imp["bootstrap_id"] == boot_id
        and all(boot[key] == imp[key] for key in ("formal_semantics_id", "schema_set_id")),
        "import cannot select trust/schema",
    )
    _require(source["genesis_ref"] == boot["genesis_ref"], "independently pinned genesis")
    _require(imp["artifacts"] == source["artifacts"], "complete same source inventory")
    _require(type(artifacts) is tuple, "immutable original artifact inventory")
    ids = [key for key, _ in artifacts]
    _require(
        ids == [ref["content_id"] for ref in source["artifacts"]],
        "exact source artifacts, no extras/subsets",
    )
    store = dict(artifacts)
    descriptors = {ref["content_id"]: ref for ref in source["artifacts"]}

    def resolve(ref: dict) -> bytes:
        reference(ref)
        _require(ref["content_id"] in store, "missing original artifact")
        _require(ref == descriptors[ref["content_id"]], "original descriptor identity")
        value = store[ref["content_id"]]
        _require(
            type(value) is bytes
            and len(value) == int(ref["byte_length"])
            and raw_id(value) == ref["content_id"],
            "original complete artifact bytes",
        )
        return value

    for ref in source["artifacts"]:
        resolve(ref)
    index_ref = imp["source_index_ref"]
    _require(
        raw_id(source_index) == index_ref["content_id"]
        and len(source_index) == int(index_ref["byte_length"]),
        "source index raw binding",
    )
    # The source index describes original protocol objects, never its own hash.
    # Its descriptor belongs to the enclosing manifest, avoiding a hash cycle.
    _require(
        len(source_index)
        + len(manifest)
        + len(trust.bootstrap)
        + len(trust.trusted_log)
        + sum(len(raw) for _, raw in artifacts)
        <= MAX_SOURCE_BYTES,
        "approved complete source-byte budget",
    )
    for ref in [
        boot["genesis_ref"],
        boot["initial_config_ref"],
        imp["apply_qc_ref"],
        imp["apply_candidate_ref"],
        imp["snapshot_ref"],
    ]:
        resolve(ref)
    for event in source["events"]:
        resolve(event["original_ref"])
        for ref in event["input_refs"]:
            resolve(ref)
    _require(int(imp["target_event_index"]) <= len(source["events"]), "source cut present")

    records = scan_trust(trust.trusted_log)
    previous_id, previous = "GENESIS", None
    for ordinal, raw in enumerate(records):
        row = validate(raw, "TRUST_RECORD")
        _require(
            int(row["ordinal"]) == ordinal
            and row["previous_record_id"] == previous_id
            and row["bootstrap_id"] == boot_id,
            "unbroken original trusted chain",
        )
        if ordinal == 0:
            _require(
                row["kind"] == "INIT" and row["anchor"] == boot["initial_anchor"],
                "independent initial floor",
            )
        else:
            _require(row["kind"] != "INIT", "no trusted log reset")
            assert previous is not None
            old, new = previous["anchor"], row["anchor"]
            _require(int(new["height"]) >= int(old["height"]), "trusted floor rollback")
            _require(new["height"] != old["height"] or new == old, "same-height floor fork")
            if row["kind"] == "ANCHOR":
                _require(
                    previous.get("generation_id") == row["generation_id"],
                    "anchor preserves activated generation",
                )
        previous, previous_id = row, document_id(raw, "TRUST_RECORD")
    assert previous is not None
    _require(imp["anchor"] == previous["anchor"], "exact latest independently trusted floor")
    targets = [
        {"actor_id": row["actor_id"], "journal_id": row["journal_id"], **row["target"]}
        for row in imp["journals"]
    ]
    _require(targets == source["original_journal_refs"], "exact retained target journal inventory")
    own = trust.own_journals
    _require(
        type(own) is tuple
        and [(a, j) for a, j, _ in own]
        == [(row["actor_id"], row["journal_id"]) for row in imp["journals"]],
        "complete own journal identities",
    )
    for (actor, _, raw), row in zip(own, targets, strict=True):
        _require(
            actor == boot["local_validator_id"] and resolve(row["ref"]) == raw,
            "original own bytes from independent T, no remote private journal substitution",
        )
    own_by_identity = {(actor, journal): raw for actor, journal, raw in own}

    def prefix(row):
        key = row["actor_id"], row["journal_id"]
        _require(key in own_by_identity, "original trusted/cut journal identity")
        full = own_by_identity[key]
        length = int(row["ref"]["byte_length"])
        _require(
            length <= len(full) and raw_id(full[:length]) == row["ref"]["content_id"],
            "trusted/cut record names an exact original journal prefix",
        )

    # The latest F may precede further durable votes at the same current F.
    # Retain all of L; do not require its length to equal the ANCHOR cut.
    for raw in records:
        for row in load(raw)["journal_cuts"]:
            prefix(row)
    for row in imp["journals"]:
        prefix({"actor_id": row["actor_id"], "journal_id": row["journal_id"], **row["cut"]})
    # ApplyQC authenticity, history-derived floor/cut equality, native record
    # decoding and total public-family construction have NOT run here.
    return Metadata(
        trust.bootstrap,
        manifest,
        source_index,
        records,
        artifacts,
        own,
        previous["anchor"],
        int(imp["cut_event_index"]),
        int(imp["target_event_index"]),
    )
