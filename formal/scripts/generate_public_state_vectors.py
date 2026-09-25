"""Full-state candidate paths. Their legality is checked by TLC, not this builder."""

import copy
from pathlib import Path

from formal_artifacts import canonical_json_bytes, write_canonical_json
from public_state_projection import PROFILE, inventory, model_identity, state_root

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proposals/public-state-vectors.json"


def integer(n):
    return ["int", str(n)]


def string(s):
    return ["str", s]


def model(s):
    return ["model", s]


def finite_set(*items):
    return ["set", sorted(items, key=canonical_json_bytes)]


def function(pairs):
    return ["fun", sorted(pairs, key=lambda p: canonical_json_bytes(p[0]))]


def record(**items):
    return function([[string(k), v] for k, v in items.items()])


def replace_key(value, key, result):
    return function([[k, result if k == key else v] for k, v in value[1]])


def initial_state():
    values = {name: finite_set() for name in inventory()}
    validators = [model(f"v{i}") for i in range(1, 5)]
    values.update(
        byzantine=finite_set(model("v4")),
        alive=finite_set(*validators),
        durableSequence=function([[v, integer(0)] for v in validators]),
        recoveryState=function([[v, string("READY")] for v in validators]),
        leaseOwner=function([[model("t1"), string("NO_WORKER")]]),
        leaseEpoch=function([[model("t1"), integer(0)]]),
        repairAttempts=function([[model("content1"), integer(0)]]),
        currentCheckpoint=model("parent1"),
        view=integer(0),
        logicalTime=integer(0),
        phase=string("ACTIVE"),
        abortReason=string("NO_ABORT"),
    )
    return values


def candidate_path():
    states, actions = [initial_state()], []

    def append(action, **changes):
        state = copy.deepcopy(states[-1])
        state.update(changes)
        states.append(state)
        actions.append(action)

    context = record(kind=string("ROUND_CONFIG"), height=model("h1"), epoch=model("epoch1"))
    proposal = record(context=context, body=model("configA"))
    append("ProposeRoundConfigAction", proposals=finite_set(proposal))
    for actor in [model("v1"), model("v2"), model("v3")]:
        vote = record(
            validator=actor, kind=string("ROUND_CONFIG"), context=context, body=model("configA")
        )
        current = states[-1]
        append(
            "PersistConfigVoteAction",
            durableVotes=finite_set(*current["durableVotes"][1], vote),
            volatileVotes=finite_set(*current["volatileVotes"][1], vote),
            durableSequence=replace_key(current["durableSequence"], actor, integer(1)),
        )
        if actor == model("v1"):
            append(
                "CrashAfterPersistAction",
                alive=finite_set(model("v2"), model("v3"), model("v4")),
                volatileVotes=finite_set(),
                crashCoverage=finite_set(string("AFTER_PERSIST")),
                recoveryState=replace_key(states[-1]["recoveryState"], actor, string("CRASHED")),
            )
            append(
                "RestartAction",
                alive=states[0]["alive"],
                recoveryState=replace_key(states[-1]["recoveryState"], actor, string("RECOVERING")),
            )
            append(
                "RecoverJournalAction",
                volatileVotes=states[-1]["durableVotes"],
                recoveryState=replace_key(states[-1]["recoveryState"], actor, string("READY")),
            )
        append(
            "SendVoteEnvelopeAction",
            messages=finite_set(vote),
            messageMultiplicity=finite_set(record(vote=vote, copy=integer(1))),
        )
        append(
            "DeliverVoteEnvelopeAction",
            messages=finite_set(),
            messageMultiplicity=finite_set(),
            receivedVotes=finite_set(*states[-1]["receivedVotes"][1], vote),
        )
    append(
        "FinalizeRoundConfigAction",
        finalizedCertificates=finite_set(
            record(
                context=context,
                body=model("configA"),
                signers=finite_set(model("v1"), model("v2"), model("v3")),
            )
        ),
    )
    append("STUTTER")
    return states, actions


def package(states, actions, identity=None):
    identity = model_identity() if identity is None else identity
    observations = []
    for values in states:
        state = {"profile": PROFILE, "model": identity, "variables": values}
        observations.append({"state": state, "root": state_root(state, identity)})
    return {"profile": PROFILE, "states": observations, "actions": actions}


def generate(target=TARGET):
    states, actions = candidate_path()
    identity = model_identity()
    positive = package(states, actions, identity)
    negatives = []

    def case(name, values, labels, failure):
        negatives.append(
            {"name": name, "expected_failure": failure, "trace": package(values, labels, identity)}
        )

    wrong_initial = copy.deepcopy(states[:2])
    wrong_initial[0]["logicalTime"] = integer(1)
    case("noninitial-state", wrong_initial, actions[:1], "WitnessInitialOK")
    wrong_side_effect = copy.deepcopy(states[:2])
    wrong_side_effect[1]["logicalTime"] = integer(1)
    case("hidden-clock-side-effect", wrong_side_effect, actions[:1], "WitnessAllowed")
    case("wrong-action-label", states[:2], ["PersistConfigVoteAction"], "WitnessLabelled")
    erased = copy.deepcopy(states[:4])
    erased[-1]["durableVotes"] = finite_set()
    case("crash-erases-durable-vote", erased, actions[:3], "WitnessAllowed")
    early = [*copy.deepcopy(states[:2]), copy.deepcopy(states[6])]
    early[-1]["durableVotes"] = finite_set()
    early[-1]["volatileVotes"] = finite_set()
    early[-1]["durableSequence"] = states[0]["durableSequence"]
    early[-1]["crashCoverage"] = finite_set()
    case("send-before-persist", early, [*actions[:1], "SendVoteEnvelopeAction"], "WitnessAllowed")
    # Three persisted votes are not three delivered votes.
    premature = copy.deepcopy(states[:13])
    premature.append(copy.deepcopy(premature[-1]))
    premature[-1]["finalizedCertificates"] = states[-1]["finalizedCertificates"]
    case(
        "qc-before-third-delivery",
        premature,
        [*actions[:12], "FinalizeRoundConfigAction"],
        "WitnessAllowed",
    )
    false_stutter = copy.deepcopy(states[:2])
    case("changed-state-called-stutter", false_stutter, ["STUTTER"], "WitnessLabelled")
    document = {
        "status": "CANDIDATE_PATHS_REQUIRE_TLC",
        "native_execution": False,
        "variables": list(inventory()),
        "positive": positive,
        "negative": negatives,
    }
    write_canonical_json(target, document)
    return document


if __name__ == "__main__":
    result = generate()
    print(
        f"{len(result['positive']['states'])} complete states; "
        f"{len(result['negative'])} rehashed invalid paths"
    )
