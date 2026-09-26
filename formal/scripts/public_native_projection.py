"""Checked finite native/state correspondence, never authenticated native export.

The source registry is independently pinned. v1 native snapshots are retained as
source evidence; a v2 wrapper must not turn their opaque roots into state hashes.
TLC legality and producer authentication are separate from this structural check.
"""

from __future__ import annotations

import copy
import hashlib
import re

from derive_public_arithmetic_inputs import SOURCE, SOURCE_SHA256, derive
from formal_artifacts import canonical_json_bytes, load_json_strict, sha256_file
from generate_public_journal_vectors import refinement
from generate_public_state_vectors import finite_set as ss
from generate_public_state_vectors import function, replace_key
from generate_public_state_vectors import integer as ii
from generate_public_state_vectors import model as m
from generate_public_state_vectors import record as r
from generate_public_state_vectors import string as s
from native_durability_witness import PERSIST_STAGES, envelope, persisted_bytes
from native_trace_witness import NativeEvidence, n
from public_state_projection import (
    ROOT,
    check_observation,
    configuration_sources,
    model_identity,
    require,
)

VERSION = "deltareduce.full-public-native.v2-candidate"
PUBLIC = ROOT / "formal/fixtures/traces/legal/normal-apply.json"
PUBLIC_SHA256 = "3bfcaca96c991f71701ecc9866ffa3d42f741369b48b7af62c4fa3d3607abf2a"


def fields(value):
    require(value[0] == "fun", "PROJECTION_RECORD")
    require(all(k[0] == "str" for k, _ in value[1]), "PROJECTION_RECORD_KEYS")
    return {k[1]: v for k, v in value[1]}


def field(value, name):
    result = fields(value)
    require(name in result, "PROJECTION_FIELD")
    return result[name]


def at(value, key):
    require(value[0] == "fun", "PROJECTION_FUNCTION")
    matches = [v for k, v in value[1] if k == key]
    require(len(matches) == 1, "PROJECTION_FUNCTION_DOMAIN")
    return matches[0]


def items(value):
    require(value[0] == "set", "PROJECTION_SET")
    return value[1]


def singleton(values, reason):
    require(len(values) == 1, reason)
    return values[0]


def certified(state, collection, kind, body, context):
    """Check the actual modeled quorum/delivery fields; not cryptographic signatures."""
    qc = singleton(
        [c for c in items(state[collection]) if field(c, "body") == body], "PROJECTION_QC"
    )
    data = fields(qc)
    require(
        set(data)
        == ({"body", "context", "signers"} if kind == "ROUND_CONFIG" else {"body", "signers"}),
        "PROJECTION_QC_SHAPE",
    )
    if kind == "ROUND_CONFIG":
        require(data["context"] == context, "PROJECTION_QC_CONTEXT")
    signers = items(data["signers"])
    require(
        len(signers) >= 3 and all(v in [m(f"v{i}") for i in range(1, 5)] for v in signers),
        "PROJECTION_QUORUM",
    )
    for actor in signers:
        vote = r(validator=actor, kind=s(kind), context=context, body=body)
        require(
            vote in items(state["receivedVotes"]) and vote in items(state["durableVotes"]),
            "PROJECTION_UNDELIVERED_QC",
        )


class PinnedFixtureSources:
    """Finite, synthetic source registry. Its digest is not exporter authentication."""

    def __init__(self, public=PUBLIC, native=SOURCE):
        require(sha256_file(public) == PUBLIC_SHA256, "PROJECTION_PUBLIC_PIN")
        self.native = NativeEvidence(native, SOURCE_SHA256)
        self.checked = refinement.check_trace(public, self.native)
        self.trace = load_json_strict(public)
        self.binding = derive(native)
        self.identity = model_identity("native-arithmetic")
        config = configuration_sources("native-arithmetic")[0].read_text(encoding="utf-8")
        deadlines = re.findall(r"^\s*HardDeadline = ([0-9]+)\s*$", config, re.M)
        require(
            deadlines == [str(self.binding["context"]["hard_deadline"])],
            "PROJECTION_CONFIG_DEADLINE",
        )

    def _parents(self, state, body):
        # Native graph supplies the immutable math; actual state supplies all
        # certificate bodies. The abstract config/seed identities are finite here.
        b = fields(body)
        isc, ec, apc = b["isc"], b["ec"], b["apc"]
        round_context = r(height=m("h1"), epoch=m("epoch1"))
        entries = ss(r(ticket=m("t1"), content=m("content1")))
        require(
            isc
            == r(
                round=round_context,
                config=m("configA"),
                policy=s("OMIT_UNAVAILABLE"),
                entries=entries,
                canonicalRoot=entries,
            ),
            "PROJECTION_ISC_BODY",
        )
        seed = r(isc=isc, epoch=m("epoch1"), value=m("seed1"))
        require(
            ec == r(isc=isc, seed=seed, members=ss(m("t1")), normEvidence=m("norm1")),
            "PROJECTION_EC_BODY",
        )
        require(
            apc
            == r(isc=isc, seed=seed, ec=ec, members=ss(m("t1")), coefficientProfile=m("coeff1")),
            "PROJECTION_APC_BODY",
        )
        require(
            field(isc, "round") == round_context and field(isc, "config") == m("configA"),
            "PROJECTION_ROUND",
        )
        certified(
            state,
            "finalizedCertificates",
            "ROUND_CONFIG",
            m("configA"),
            r(kind=s("ROUND_CONFIG"), height=m("h1"), epoch=m("epoch1")),
        )
        certified(state, "inputSetCertificates", "ISC", isc, round_context)
        certified(state, "eligibilityCertificates", "EC", ec, isc)
        certified(state, "aggregationPlanCertificates", "APC", apc, ec)
        require(
            field(ec, "isc") == isc and field(apc, "isc") == isc and field(apc, "ec") == ec,
            "PROJECTION_PARENT_CHAIN",
        )
        seed = field(apc, "seed")
        require(
            field(ec, "seed") == seed
            and seed in items(state["seedTranscripts"])
            and field(seed, "isc") == isc,
            "PROJECTION_SEED",
        )
        require(
            field(ec, "members") == field(apc, "members") == ss(m("t1")), "PROJECTION_ELIGIBLE_SET"
        )
        definition = singleton(items(state["ticketPlan"]), "PROJECTION_TICKET_COVERAGE")
        require(
            definition
            == r(
                ticket=m("t1"),
                domain=m("d1"),
                data=m("data1"),
                batchBudget=ii(1),
                stepBudget=ii(1),
                parent=m("parent1"),
                schema=m("schema1"),
                profile=m("profile1"),
            ),
            "PROJECTION_TICKET_METADATA",
        )
        require(
            field(isc, "entries") == ss(r(ticket=m("t1"), content=m("content1"))),
            "PROJECTION_COMMITMENT",
        )
        require(
            any(
                field(c, "ticket") == m("t1") and field(c, "content") == m("content1")
                for c in items(state["commitments"])
            ),
            "PROJECTION_COMMITMENT",
        )
        require(
            r(ticket=m("t1"), content=m("content1")) in items(state["availabilityCertificates"]),
            "PROJECTION_AVAILABILITY",
        )
        return isc, ec, apc, seed, round_context

    def _authority(self, isc, ec, apc):
        inputs = self.binding["inputs"]
        return r(
            parent=m("parent1"),
            schema=m("schema1"),
            profile=m("profile1"),
            applyProfile=m("apply1"),
            inputs=inputs,
            isc=isc,
            ec=ec,
            apc=apc,
            model=r(kind=s("MODEL"), schema=m("schema1"), values=field(inputs, "model")),
            optimizer=r(
                kind=s("OPTIMIZER"), schema=m("schema1"), values=field(inputs, "optimizer")
            ),
        )

    def _parameter(self, state, body, witness):
        b = fields(body)
        require(
            set(b)
            == set(
                (
                    "round config isc seed ec apc domain shard parent schema arithmeticProfile "
                    "coefficientProfile authority value checked"
                ).split()
            ),
            "PROJECTION_PARAMETER_FIELDS",
        )
        isc, ec, apc, seed, round_context = self._parents(state, body)
        require(
            b["domain"] == m("d1") and b["shard"] in [m("shard1"), m("shard2")],
            "PROJECTION_PARAMETER_KEY",
        )
        index = [m("shard1"), m("shard2")].index(b["shard"])
        expected = witness.expected_parameter("d1", f"s{index + 1}")
        complete = r(
            round=round_context,
            config=m("configA"),
            isc=isc,
            seed=seed,
            ec=ec,
            apc=apc,
            domain=m("d1"),
            shard=m(f"shard{index + 1}"),
            parent=m("parent1"),
            schema=m("schema1"),
            arithmeticProfile=m("profile1"),
            coefficientProfile=field(apc, "coefficientProfile"),
            authority=self._authority(isc, ec, apc),
            value=ii(expected["numerators"][0]),
            checked=["bool", True],
        )
        require(body == complete, "PROJECTION_PARAMETER_NATIVE_BODY")
        return expected

    def _apply(self, state, body, witness):
        b = fields(body)
        require(
            set(b)
            == set(
                (
                    "round config aggregate parent applyProfile authority nextCheckpoint "
                    "nextModelHash nextOptimizerHash checked"
                ).split()
            ),
            "PROJECTION_APPLY_FIELDS",
        )
        root = b["aggregate"]
        rb = fields(root)
        require(
            set(rb)
            == set(
                (
                    "round config isc seed ec apc parent schema arithmeticProfile "
                    "coefficientProfile leaves canonicalRoot"
                ).split()
            ),
            "PROJECTION_AGGREGATE_FIELDS",
        )
        isc, ec, apc, seed, round_context = self._parents(state, root)
        leaves = items(rb["leaves"])
        require(len(leaves) == 2, "PROJECTION_PARAMETER_COVERAGE")
        parameters = {}
        for leaf in leaves:
            native = self._parameter(state, leaf, witness)
            key = native["shard"]
            require(key not in parameters, "PROJECTION_PARAMETER_COVERAGE")
            parameters[key] = native
            certified(
                state,
                "parameterQCs",
                "PARAMETER",
                leaf,
                r(domain=field(leaf, "domain"), shard=field(leaf, "shard")),
            )
        require(set(parameters) == {"s1", "s2"}, "PROJECTION_PARAMETER_COVERAGE")
        expected_root = r(
            round=round_context,
            config=m("configA"),
            isc=isc,
            seed=seed,
            ec=ec,
            apc=apc,
            parent=m("parent1"),
            schema=m("schema1"),
            arithmeticProfile=m("profile1"),
            coefficientProfile=field(apc, "coefficientProfile"),
            leaves=ss(*leaves),
            canonicalRoot=ss(*leaves),
        )
        require(root == expected_root, "PROJECTION_AGGREGATE_BODY")
        certified(state, "aggregateRootQCs", "AGGREGATE_ROOT", root, apc)
        expected = witness.expected_apply([parameters["s1"], parameters["s2"]])

        def value_hash(kind, key):
            return r(
                kind=s(kind),
                schema=m("schema1"),
                values=function([[m(f"shard{i + 1}"), ii(v)] for i, v in enumerate(expected[key])]),
            )

        complete = r(
            round=round_context,
            config=m("configA"),
            aggregate=root,
            parent=m("parent1"),
            applyProfile=m("apply1"),
            authority=self._authority(isc, ec, apc),
            nextCheckpoint=m("next1"),
            nextModelHash=value_hash("MODEL", "next_model"),
            nextOptimizerHash=value_hash("OPTIMIZER", "next_optimizer"),
            checked=["bool", True],
        )
        require(body == complete, "PROJECTION_APPLY_NATIVE_BODY")
        return expected

    def bind_first(self, event_index, prior_observation, next_observation, action):
        require(
            type(event_index) is int and 0 <= event_index < len(self.trace["events"]),
            "PROJECTION_EVENT_INDEX",
        )
        event = self.trace["events"][event_index]
        kind = {"ACT-PARAM-VOTE": "PARAMETER", "ACT-APPLY-VOTE": "APPLY"}.get(event["action_id"])
        require(
            kind is not None and event["outcome"] == "ACCEPTED", "PROJECTION_FIRST_ARITHMETIC_ONLY"
        )
        require(
            action == ("VoteParameterAction" if kind == "PARAMETER" else "VoteApplyAction"),
            "PROJECTION_ACTION",
        )
        before = check_observation(prior_observation, self.identity)
        after = check_observation(next_observation, self.identity)
        actor_number = singleton(
            [i for i in range(1, 4) if event["actor_id"] == f"validator-{i}"], "PROJECTION_ACTOR"
        )
        actor = m(f"v{actor_number}")
        source_snapshot = self.native.snapshots[event["arithmetic_witness"]["snapshot_id"]]
        anchor = n.NativeAnchor(**source_snapshot["anchor"])
        require(
            before["currentCheckpoint"] == m("parent1")
            and source_snapshot["current_checkpoint"] == self.binding["symbol_binding"]["parent1"],
            "PROJECTION_CURRENT",
        )
        require(
            actor in items(before["alive"]) and at(before["recoveryState"], actor) == s("READY"),
            "PROJECTION_READY",
        )
        require(
            before["phase"] == s("ACTIVE") and not items(before["abortRequests"]),
            "PROJECTION_PHASE",
        )
        require(
            before["view"] == ii(anchor.view)
            and before["logicalTime"] == ii(anchor.logical_time)
            and anchor.logical_time < anchor.hard_deadline,
            "PROJECTION_TIME_VIEW",
        )
        require(
            event["height"] == self.binding["symbol_binding"]["h1"]
            and event["validator_epoch"] == self.binding["symbol_binding"]["epoch1"]
            and event["round_id"] == self.binding["context"]["round"],
            "PROJECTION_EVENT_CONTEXT",
        )
        # Derive the only appended envelope from complete before/after states.
        added = [v for v in items(after["durableVotes"]) if v not in items(before["durableVotes"])]
        vote = singleton(added, "PROJECTION_ONE_NEW_VOTE")
        v = fields(vote)
        require(
            set(v) == {"validator", "kind", "context", "body"}
            and v["validator"] == actor
            and v["kind"] == s(kind),
            "PROJECTION_ENVELOPE",
        )
        body = v["body"]
        require(
            body in items(before["parameterResults" if kind == "PARAMETER" else "applyCandidates"]),
            "PROJECTION_CANDIDATE",
        )
        expected_context = (
            r(domain=field(body, "domain"), shard=field(body, "shard"))
            if kind == "PARAMETER"
            else field(body, "aggregate")
        )
        require(v["context"] == expected_context, "PROJECTION_VOTE_CONTEXT")
        previous = [v for v in items(before["durableVotes"]) if field(v, "validator") == actor]
        require(
            all(
                not (field(v, "kind") == s(kind) and field(v, "context") == expected_context)
                for v in previous
            ),
            "PROJECTION_FRESH_CONTEXT",
        )
        sequence = len(previous) + 1
        require(
            at(before["durableSequence"], actor) == ii(sequence - 1)
            and sequence == event["durable_sequence"] == source_snapshot["durable_sequence"],
            "PROJECTION_SEQUENCE",
        )
        changed = copy.deepcopy(before)
        collection = "parameterVotes" if kind == "PARAMETER" else "applyVotes"
        changed.update(
            durableVotes=ss(*items(before["durableVotes"]), vote),
            volatileVotes=ss(*items(before["volatileVotes"]), vote),
            durableSequence=replace_key(before["durableSequence"], actor, ii(sequence)),
        )
        changed[collection] = ss(*items(before[collection]), r(validator=actor, body=body))
        require(after == changed, "PROJECTION_VOTE_EFFECT_FIELDS")
        witness = n.Witness(anchor, source_snapshot["authority"], self.native.store)
        expected = (
            self._parameter(before, body, witness)
            if kind == "PARAMETER"
            else self._apply(before, body, witness)
        )
        command = n.canonical({"action": event["action_id"], "payload": expected}).decode("ascii")
        require(
            command == event["arithmetic_witness"]["command_ascii"]
            and n.digest(n.canonical(expected)) == event["body_hash"],
            "PROJECTION_NATIVE_COMMAND",
        )
        operation = self.native.operations[event["durability_witness"]]
        require(operation["stages"] == PERSIST_STAGES, "PROJECTION_COMPLETE_OBSERVATION_ONLY")
        receipt, effect = persisted_bytes(event)
        require(
            (receipt, effect) == (operation["receipt_ascii"], operation["effect_ascii"]),
            "PROJECTION_ORIGINAL_RECEIPT",
        )
        require(
            source_snapshot["prior_state_root"] != prior_observation["root"],
            "PROJECTION_LEGACY_ROOT_SCOPE",
        )
        return {
            "projection_version": VERSION,
            "source_public_sha256": PUBLIC_SHA256,
            "source_native_sha256": SOURCE_SHA256,
            "source_event_index": event_index,
            "source_snapshot_id": event["arithmetic_witness"]["snapshot_id"],
            "source_operation_id": event["durability_witness"],
            "source_snapshot_ascii": n.canonical(source_snapshot).decode("ascii"),
            "complete_prior_root": prior_observation["root"],
            "complete_next_root": next_observation["root"],
            "state_model": self.identity,
            "actor_symbol": actor[1],
            "sequence": sequence,
            "native_anchor": source_snapshot["anchor"],
            "vote_context_id": event["vote_context_id"],
            "native_body_hash": event["body_hash"],
            "tla_envelope": vote,
            "envelope_ascii": n.canonical(envelope(event)).decode("ascii"),
            "command_ascii": command,
            "receipt_ascii": receipt,
            "effect_ascii": effect,
            "provenance": "SYNTHETIC_PINNED_FIXTURE_NOT_NATIVE_AUTHENTICATION",
            "legacy_roots_upgraded": False,
        }


def projection_id(value):
    return (
        "sha256:"
        + hashlib.sha256(VERSION.encode("ascii") + b"\0" + canonical_json_bytes(value)).hexdigest()
    )


def verify_projection(sources, claim, event_index, prior, next_state, action):
    require(
        type(claim) is dict and claim.get("projection_version") == VERSION, "PROJECTION_VERSION"
    )
    expected = sources.bind_first(event_index, prior, next_state, action)
    require(
        canonical_json_bytes(claim) == canonical_json_bytes(expected), "PROJECTION_DERIVED_FIELDS"
    )
    return projection_id(expected)
