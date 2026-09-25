"""Complete arithmetic candidate history. TLC independently decides its legality."""

import copy

from derive_public_arithmetic_inputs import derive
from formal_artifacts import load_json_strict, write_canonical_json
from generate_public_state_vectors import finite_set as ss
from generate_public_state_vectors import function, initial_state, package, replace_key
from generate_public_state_vectors import integer as ii
from generate_public_state_vectors import model as m
from generate_public_state_vectors import record as r
from generate_public_state_vectors import string as s
from public_state_projection import ROOT, model_identity, require, state_root
from public_state_storage import pack

TARGET = ROOT / "formal/proposals/public-arithmetic-vectors.json"
NEGATIVE_RECIPES = [
    {
        "name": "wrong-parameter-numerator",
        "expected_failure": "WitnessAllowed",
        "recipe": "parameter",
    },
    {"name": "wrong-next-optimizer", "expected_failure": "WitnessAllowed", "recipe": "optimizer"},
    {"name": "advance-without-apply-qc", "expected_failure": "WitnessAllowed", "recipe": "advance"},
]


def field(value, name):
    return next(v for k, v in value[1] if k == s(name))


def candidate_path(binding):
    states, actions, correspondence = [initial_state()], [], []
    source = load_json_strict(ROOT / "formal/fixtures/traces/legal/normal-apply.json")
    events = iter(enumerate(source["events"]))

    def step(action, **changes):
        state = copy.deepcopy(states[-1])
        state.update(changes)
        states.append(state)
        actions.append(action)

    def add(action, variable, value, **changes):
        step(action, **{variable: ss(*states[-1][variable][1], value)}, **changes)

    def before(action_id, actor="validator-1"):
        index, event = next(events)
        require(
            event["action_id"] == action_id and event["actor_id"] == actor, "ORIGINAL_EVENT_ORDER"
        )
        while int(states[-1]["logicalTime"][1]) < event["logical_time"]:
            step("AdvanceLogicalTime", logicalTime=ii(int(states[-1]["logicalTime"][1]) + 1))
        require(int(states[-1]["logicalTime"][1]) == event["logical_time"], "ORIGINAL_TIME")
        correspondence.append(
            {
                "legacy_event_index": index,
                "prior_state_index": len(states) - 1,
                "actor_id": actor,
                "action_id": action_id,
                "durable_sequence": event["durable_sequence"],
                "legacy_prior_root": event["prior_state_root"],
                "legacy_next_root": event["next_state_root"],
            }
        )
        return event

    def after():
        correspondence[-1]["next_state_index"] = len(states) - 1

    signers = ss(m("v1"), m("v2"), m("v3"))
    round_context = r(height=m("h1"), epoch=m("epoch1"))
    config_context = r(kind=s("ROUND_CONFIG"), height=m("h1"), epoch=m("epoch1"))
    config = m("configA")
    before("ACT-CONFIG-PROPOSE")
    add("ProposeRoundConfigAction", "proposals", r(context=config_context, body=config))
    after()

    def quorum(
        kind,
        body,
        context,
        collection,
        vote_action,
        legacy_vote,
        qc_collection,
        qc_action,
        legacy_qc,
    ):
        for number in range(1, 4):
            actor = m(f"v{number}")
            event = before(legacy_vote, f"validator-{number}")
            envelope = r(validator=actor, kind=s(kind), context=context, body=body)
            previous = states[-1]
            count = next(int(v[1]) for k, v in previous["durableSequence"][1] if k == actor) + 1
            require(count == event["durable_sequence"], "ORIGINAL_SEQUENCE")
            changes = dict(
                durableVotes=ss(*previous["durableVotes"][1], envelope),
                volatileVotes=ss(*previous["volatileVotes"][1], envelope),
                durableSequence=replace_key(previous["durableSequence"], actor, ii(count)),
            )
            if collection:
                changes[collection] = ss(*previous[collection][1], r(validator=actor, body=body))
            step(vote_action, **changes)
            after()
            step(
                "SendVoteEnvelopeAction",
                messages=ss(envelope),
                messageMultiplicity=ss(r(vote=envelope, copy=ii(1))),
            )
            step(
                "DeliverVoteEnvelopeAction",
                messages=ss(),
                messageMultiplicity=ss(),
                receivedVotes=ss(*states[-1]["receivedVotes"][1], envelope),
            )
        before(legacy_qc)
        certificate = (
            r(context=context, body=body, signers=signers)
            if kind == "ROUND_CONFIG"
            else r(body=body, signers=signers)
        )
        add(qc_action, qc_collection, certificate)
        after()

    quorum(
        "ROUND_CONFIG",
        config,
        config_context,
        None,
        "PersistConfigVoteAction",
        "ACT-CONFIG-VOTE",
        "finalizedCertificates",
        "FinalizeRoundConfigAction",
        "ACT-CONFIG-FINALIZE",
    )
    ticket = r(
        ticket=m("t1"),
        domain=m("d1"),
        data=m("data1"),
        batchBudget=ii(1),
        stepBudget=ii(1),
        parent=m("parent1"),
        schema=m("schema1"),
        profile=m("profile1"),
    )
    add("IssueTicketAction", "ticketPlan", ticket)
    step(
        "LeaseTicketAction",
        leaseOwner=replace_key(states[-1]["leaseOwner"], m("t1"), m("w1")),
        leaseActive=ss(m("t1")),
    )
    add(
        "CommitTicketAction",
        "commitments",
        r(ticket=m("t1"), worker=m("w1"), leaseEpoch=ii(0), content=m("content1")),
        leaseActive=ss(),
    )
    for shard in [m("shard1"), m("shard2")]:
        location = r(storage=m("s1"), content=m("content1"), shard=shard)
        add(
            "UploadArtifactAction",
            "materializedArtifacts",
            location,
            availableArtifacts=ss(*states[-1]["availableArtifacts"][1], location),
        )
        add(
            "AttestAvailabilityAction",
            "availabilityAttestations",
            r(storage=m("s1"), ticket=m("t1"), content=m("content1"), shard=shard),
        )
    ac = r(ticket=m("t1"), content=m("content1"))
    add("FinalizeAvailabilityAction", "availabilityCertificates", ac, availableTickets=ss(m("t1")))
    isc = r(
        round=round_context,
        config=config,
        policy=s("OMIT_UNAVAILABLE"),
        entries=ss(ac),
        canonicalRoot=ss(ac),
    )
    add("CloseInputAction", "closedInputBodies", isc)
    quorum(
        "ISC",
        isc,
        round_context,
        "iscVotes",
        "VoteISCAction",
        "ACT-ISC-VOTE",
        "inputSetCertificates",
        "FinalizeISCAction",
        "ACT-ISC-FINALIZE",
    )
    seed = r(isc=isc, epoch=m("epoch1"), value=m("seed1"))
    before("ACT-SEED-GENERATE")
    add("GenerateSeedAction", "seedTranscripts", seed)
    after()
    ec = r(isc=isc, seed=seed, members=ss(m("t1")), normEvidence=m("norm1"))
    quorum(
        "EC",
        ec,
        isc,
        "ecVotes",
        "VoteECAction",
        "ACT-EC-VOTE",
        "eligibilityCertificates",
        "FinalizeECAction",
        "ACT-EC-FINALIZE",
    )
    apc = r(isc=isc, seed=seed, ec=ec, members=ss(m("t1")), coefficientProfile=m("coeff1"))
    quorum(
        "APC",
        apc,
        ec,
        "apcVotes",
        "VoteAPCAction",
        "ACT-APC-VOTE",
        "aggregationPlanCertificates",
        "FinalizeAPCAction",
        "ACT-APC-FINALIZE",
    )
    authority = r(
        parent=m("parent1"),
        schema=m("schema1"),
        profile=m("profile1"),
        applyProfile=m("apply1"),
        inputs=binding["inputs"],
        isc=isc,
        ec=ec,
        apc=apc,
        model=r(kind=s("MODEL"), schema=m("schema1"), values=field(binding["inputs"], "model")),
        optimizer=r(
            kind=s("OPTIMIZER"), schema=m("schema1"), values=field(binding["inputs"], "optimizer")
        ),
    )
    leaves = []
    for number, body in enumerate(binding["parameters"], 1):
        parameter = r(
            round=round_context,
            config=config,
            isc=isc,
            seed=seed,
            ec=ec,
            apc=apc,
            domain=m("d1"),
            shard=m(f"shard{number}"),
            parent=m("parent1"),
            schema=m("schema1"),
            arithmeticProfile=m("profile1"),
            coefficientProfile=m("coeff1"),
            authority=authority,
            value=ii(body["numerators"][0]),
            checked=["bool", True],
        )
        leaves.append(parameter)
        add("ProposeParameterResultAction", "parameterResults", parameter)
        quorum(
            "PARAMETER",
            parameter,
            r(domain=m("d1"), shard=m(f"shard{number}")),
            "parameterVotes",
            "VoteParameterAction",
            "ACT-PARAM-VOTE",
            "parameterQCs",
            "FinalizeParameterQCAction",
            "ACT-PARAM-FINALIZE",
        )
    root = r(
        round=round_context,
        config=config,
        isc=isc,
        seed=seed,
        ec=ec,
        apc=apc,
        parent=m("parent1"),
        schema=m("schema1"),
        arithmeticProfile=m("profile1"),
        coefficientProfile=m("coeff1"),
        leaves=ss(*leaves),
        canonicalRoot=ss(*leaves),
    )
    before("ACT-ROOT-ASSEMBLE")
    add("AssembleAggregateRootAction", "aggregateCandidates", root)
    after()
    quorum(
        "AGGREGATE_ROOT",
        root,
        apc,
        "aggregateVotes",
        "VoteAggregateRootAction",
        "ACT-ROOT-VOTE",
        "aggregateRootQCs",
        "FinalizeAggregateRootQCAction",
        "ACT-ROOT-FINALIZE",
    )

    def next_hash(kind, key):
        return r(
            kind=s(kind),
            schema=m("schema1"),
            values=function(
                [[m(f"shard{i + 1}"), ii(v)] for i, v in enumerate(binding["apply"][key])]
            ),
        )

    applied = r(
        round=round_context,
        config=config,
        aggregate=root,
        parent=m("parent1"),
        applyProfile=m("apply1"),
        authority=authority,
        nextCheckpoint=m("next1"),
        nextModelHash=next_hash("MODEL", "next_model"),
        nextOptimizerHash=next_hash("OPTIMIZER", "next_optimizer"),
        checked=["bool", True],
    )
    add("ComputeApplyCandidateAction", "applyCandidates", applied)
    quorum(
        "APPLY",
        applied,
        root,
        "applyVotes",
        "VoteApplyAction",
        "ACT-APPLY-VOTE",
        "applyQCs",
        "FinalizeApplyQCAction",
        "ACT-APPLY-FINALIZE",
    )
    before("ACT-CURRENT-ADVANCE")
    add(
        "AdvanceCurrentCheckpointAction",
        "currentAdvanceReceipts",
        applied,
        currentCheckpoint=m("next1"),
        phase=s("APPLIED"),
    )
    after()
    require(next(events, None) is None, "ALL_LEGACY_EVENTS_MAPPED")
    return states, actions, correspondence


def generate(target=TARGET):
    binding = derive()
    states, actions, correspondence = candidate_path(binding)
    positive = package(states, actions, model_identity("native-arithmetic"))
    for item in correspondence:
        item["complete_prior_root"] = positive["states"][item["prior_state_index"]]["root"]
        item["complete_next_root"] = positive["states"][item["next_state_index"]]["root"]
        require(
            item["complete_prior_root"] != item["legacy_prior_root"], "LEGACY_ROOT_NOT_UPGRADED"
        )
    result = {
        "status": "CANDIDATE_PATH_REQUIRES_TLC",
        "native_execution": False,
        "configuration": "native-arithmetic",
        "positive": pack(positive),
        "negative": NEGATIVE_RECIPES,
        "legacy_correspondence": correspondence,
        "legacy_root_binding": "INCOMPATIBLE_OPAQUE_ROOTS_NOT_REWRITTEN",
    }
    write_canonical_json(target, result)
    return result


def counterexamples(positive):
    """Mechanical, explicitly rehashed mutations; TLC must reject every one."""
    result = []
    for recipe in NEGATIVE_RECIPES:
        kind = recipe["recipe"]
        action = {
            "parameter": "ProposeParameterResultAction",
            "optimizer": "ComputeApplyCandidateAction",
            "advance": "FinalizeApplyQCAction",
        }[kind]
        index = positive["actions"].index(action)
        if kind == "advance":
            states = positive["states"][: index + 1]
            changed = copy.deepcopy(states[-1])
            values = changed["state"]["variables"]
            applied = values["applyCandidates"][1][0]
            values.update(
                currentCheckpoint=m("next1"), phase=s("APPLIED"), currentAdvanceReceipts=ss(applied)
            )
            actions = [*positive["actions"][:index], "AdvanceCurrentCheckpointAction"]
        else:
            states = positive["states"][: index + 1]
            changed = copy.deepcopy(positive["states"][index + 1])
            values = changed["state"]["variables"]
            if kind == "parameter":
                original = values["parameterResults"][1][0]
                values["parameterResults"] = ss(replace_key(original, s("value"), ii(-2)))
            else:
                original = values["applyCandidates"][1][0]
                optimizer = field(original, "nextOptimizerHash")
                vector = replace_key(field(optimizer, "values"), m("shard1"), ii(3))
                optimizer = replace_key(optimizer, s("values"), vector)
                values["applyCandidates"] = ss(
                    replace_key(original, s("nextOptimizerHash"), optimizer)
                )
            actions = positive["actions"][: index + 1]
        changed["root"] = state_root(changed["state"], model_identity("native-arithmetic"))
        result.append(
            {
                **recipe,
                "trace": {
                    "profile": positive["profile"],
                    "states": [*states, changed],
                    "actions": actions,
                },
            }
        )
    return result


if __name__ == "__main__":
    result = generate()
    print(
        len(result["positive"]["trace"]["states"]),
        "complete states;",
        len(result["legacy_correspondence"]),
        "original events mapped; native provenance remains open",
    )
