"""Candidate native pre-state witness checks; certificate/recovery trust is a premise.

The evidence file and its digest are supplied separately by the verifier, never
selected from a trace. This is an offline projection checker, not a WAL adapter,
signature verifier, receipt generator, or authorization for a runtime change.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

from coordinate_projection import native_schema_projection
from formal_artifacts import load_json_strict, validate_json_schema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "proposals"))
import native_binding as n

ACTIONS = {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
MAX_EVIDENCE_BYTES = n.MAX_BYTES


def snapshot_id(payload: dict) -> str:
    return (
        "sha256:"
        + hashlib.sha256(
            b"deltareduce.native-snapshot-witness.v1\x00" + n.canonical(payload)
        ).hexdigest()
    )


class NativeEvidence:
    def __init__(self, path: Path, expected_sha256: str):
        n.require(
            type(expected_sha256) is str
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None,
            "NATIVE_EVIDENCE_DIGEST_REQUIRED",
        )
        n.require(path.stat().st_size <= MAX_EVIDENCE_BYTES, "NATIVE_EVIDENCE_BOUND")
        data = path.read_bytes()
        n.require(hashlib.sha256(data).hexdigest() == expected_sha256, "NATIVE_EVIDENCE_DIGEST")
        self.sha256 = expected_sha256
        # The evidence container uses the same strict canonical JSON profile.
        bundle = n.shape(n.decode(data), "schema_version snapshots artifacts operations")
        n.require(bundle["schema_version"] == "1.2.0", "NATIVE_EVIDENCE_VERSION")
        n.require(type(bundle["snapshots"]) is dict, "NATIVE_SNAPSHOTS")
        n.require(type(bundle["artifacts"]) is dict, "NATIVE_ARTIFACTS")
        from native_durability_witness import observation_id

        n.require(type(bundle["operations"]) is dict, "NATIVE_OPERATIONS")
        self.operations = bundle["operations"]
        for key, value in self.operations.items():
            n.require(observation_id(value) == key, "NATIVE_OBSERVATION_ID")
        self.snapshots = bundle["snapshots"]
        self.store = {}
        for key, value in bundle["artifacts"].items():
            n.require(type(value) is str and value.isascii(), "NATIVE_ARTIFACT_ENCODING")
            raw = value.encode("ascii")
            n.require(n.digest(raw) == key, "NATIVE_ARTIFACT_ID")
            n.decode(raw)
            self.store[key] = raw
        schema = load_json_strict(
            Path(__file__).resolve().parents[1] / "schemas/formal-trace.schema.json"
        )
        for key, value in self.snapshots.items():
            n.require(snapshot_id(value) == key, "NATIVE_SNAPSHOT_ID")
            validate_json_schema(
                value, {"$ref": "#/$defs/nativeSnapshot", "$defs": schema["$defs"]}
            )

    def check(self, event: dict, contract: dict, available_parents: set[str]) -> None:
        n.require(event["actor_role"] == "VALIDATOR", "NATIVE_EVENT_ROLE")
        proof = n.shape(event["arithmetic_witness"], "snapshot_id command_ascii")
        snapshot = self.snapshots.get(proof["snapshot_id"])
        n.require(snapshot is not None, "NATIVE_SNAPSHOT_MISSING")
        n.shape(
            snapshot,
            "actor_id action_id prior_state_root round_contract_id vote_context_id "
            "durable_sequence current_checkpoint parent_certificate projection_id anchor authority",
        )
        for field in (
            "actor_id",
            "action_id",
            "prior_state_root",
            "vote_context_id",
            "durable_sequence",
        ):
            n.require(
                n.canonical(snapshot[field]) == n.canonical(event[field]), "NATIVE_EVENT_BINDING"
            )
        n.require(snapshot["round_contract_id"] == contract["contract_id"], "NATIVE_ROUND_CONTRACT")
        n.integer(snapshot["durable_sequence"], 1)
        n.require(
            snapshot["parent_certificate"] in available_parents, "NATIVE_CERTIFICATE_NOT_FINALIZED"
        )
        n.require(
            event["parent_hashes"] == [snapshot["parent_certificate"]], "NATIVE_CERTIFICATE_PARENT"
        )
        try:
            anchor = n.NativeAnchor(**snapshot["anchor"])
        except TypeError as error:
            raise n.BindingError("NATIVE_ANCHOR_SHAPE") from error
        n.require(
            anchor.parent_checkpoint == snapshot["current_checkpoint"], "NATIVE_STALE_CURRENT"
        )
        for field, value in (
            ("round_id", anchor.round_id),
            ("height", anchor.height),
            ("view", anchor.view),
            ("validator_epoch", anchor.epoch),
            ("logical_time", anchor.logical_time),
        ):
            n.require(n.canonical(event[field]) == n.canonical(value), "NATIVE_EVENT_CONTEXT")
        witness = n.Witness(anchor, snapshot["authority"], self.store)
        resolved_schema = n.resolve(self.store, witness.root["schema"], "SCHEMA")
        n.require(
            n.canonical(resolved_schema) == n.canonical(native_schema_projection(contract)),
            "NATIVE_COORDINATE_SCHEMA_BINDING",
        )
        assignments = sorted(
            (item["domain_id"], item["shard_id"], item["vote_context_id"])
            for item in contract["shard_plan"]["assignments"]
        )
        expected = sorted((d, s, item["context"]) for (d, s), item in witness.assignments.items())
        n.require(assignments == expected, "NATIVE_ASSIGNMENT_BINDING")
        n.require(
            witness.domains == contract["round_config"]["domain_ids"], "NATIVE_DOMAIN_BINDING"
        )
        command = proof["command_ascii"]
        n.require(type(command) is str and command.isascii(), "NATIVE_COMMAND_ENCODING")
        decoded = n.shape(n.decode(command.encode("ascii")), "action payload")
        n.require(decoded["action"] == event["action_id"], "NATIVE_COMMAND_ACTION")
        n.require(type(decoded["payload"]) is dict, "NATIVE_COMMAND_BODY")
        if event["action_id"] == "ACT-PARAM-VOTE":
            projection_id = witness.root["parents"]["apc"]["id"]
            n.require(
                decoded["payload"].get("context") == event["vote_context_id"], "NATIVE_VOTE_CONTEXT"
            )
        else:
            projection_id = anchor.aggregate_id
        n.require(projection_id == snapshot["projection_id"], "NATIVE_CERTIFICATE_PROJECTION")
        result = witness.admit(command.encode("ascii"))
        n.require(n.digest(result) == event["body_hash"], "NATIVE_RESULT_BODY_HASH")


def check_native_trace(trace: dict, evidence: NativeEvidence | None) -> int:
    parents: dict[str, set[str]] = {"ACT-PARAM-VOTE": set(), "ACT-APPLY-VOTE": set()}
    count = 0
    current_advanced = False
    last_sequence = {}
    for event in trace["events"]:
        action = event["action_id"]
        accepted = event["outcome"] in {"ACCEPTED", "FINALIZED"}
        if action in ACTIONS and accepted:
            n.require(evidence is not None, "NATIVE_EVIDENCE_REQUIRED")
            n.require(event.get("arithmetic_witness") is not None, "NATIVE_WITNESS_REQUIRED")
            n.require(not current_advanced, "NATIVE_STALE_CURRENT")
            evidence.check(event, trace["round_contract"], parents[action])
            n.require(
                event["durable_sequence"] > last_sequence.get(event["actor_id"], 0),
                "NATIVE_SEQUENCE_REUSE",
            )
            count += 1
        if accepted and action.endswith("-VOTE") and event["durable_sequence"] is not None:
            last_sequence[event["actor_id"]] = max(
                last_sequence.get(event["actor_id"], 0), event["durable_sequence"]
            )
        if accepted and action == "ACT-APC-FINALIZE":
            parents["ACT-PARAM-VOTE"].add(event["result_hash"])
        if accepted and action == "ACT-ROOT-FINALIZE":
            parents["ACT-APPLY-VOTE"].add(event["result_hash"])
        if accepted and action == "ACT-CURRENT-ADVANCE":
            current_advanced = True
    return count
