"""Derive a bounded TLA embedding from the separately pinned twelve-artifact graph."""

import hashlib
import sys

from formal_artifacts import write_canonical_json
from generate_public_state_vectors import function, integer, model, record
from public_state_projection import MODEL_VALUES, ROOT, require, tla_value

sys.path.insert(0, str(ROOT / "formal/proposals"))
import native_binding as n

SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
SOURCE_SHA256 = "a768ce4a038c3413d21a41df634a2c643e237e80855232820144a604258353fa"
TARGET = ROOT / "formal/proposals/public-arithmetic-inputs.json"


def derive(source=SOURCE):
    require(
        hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256, "PINNED_NATIVE_SOURCE"
    )
    bundle = n.decode(source.read_bytes())
    store = {key: raw.encode("ascii") for key, raw in bundle["artifacts"].items()}
    for key, raw in store.items():
        require(n.digest(raw) == key, "NATIVE_ARTIFACT_ID")
    snapshot = next(s for s in bundle["snapshots"].values() if s["action_id"] == "ACT-APPLY-VOTE")
    witness = n.Witness(n.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], store)
    require(list(witness.tickets.items()) == [("t0000", "d1")], "SINGLE_TICKET_EMBEDDING")
    require(witness.shards == {"s1": (0, 1), "s2": (1, 1)}, "SCALAR_SHARD_EMBEDDING")
    bodies = [witness.expected_parameter(*key) for key in witness.assignments]
    applied = witness.expected_apply(bodies)
    assignments = list(witness.assignments.values())
    require(len(assignments) == 2, "EXACT_ASSIGNMENT_COVERAGE")
    for assignment in assignments:
        require(len(assignment["contributions"]) == 1, "SINGLE_CONTRIBUTION")
        require(assignment["contributions"][0]["ticket"] == "t0000", "TICKET_BINDING")
    require(assignments[0]["denominator"] == assignments[1]["denominator"], "DOMAIN_DENOMINATOR")
    weights = [a["contributions"][0]["weight"] for a in assignments]
    require(weights[0] == weights[1], "TICKET_WEIGHT_PER_SHARD")
    q = [n.resolve(store, a["contributions"][0]["q"], "Q_SHARD")["values"][0] for a in assignments]

    def by_shard(values):
        return function(
            [[model(f"shard{i + 1}"), integer(value)] for i, value in enumerate(values)]
        )

    def domain(value):
        return function([[model("d1"), value]])

    def ticket(value):
        return function([[model("t1"), value]])

    profile = witness.profile
    domain_weights = profile["domain_weights"]
    require(domain_weights == [{"domain": "d1", "weight": [1, 1]}], "SINGLE_NORMALIZED_DOMAIN")
    inputs = record(
        ticketOrder=function([[integer(1), model("t1")]]),
        domainOrder=function([[integer(1), model("d1")]]),
        ticketDomain=ticket(model("d1")),
        q=ticket(by_shard(q)),
        weightN=ticket(integer(weights[0][0])),
        weightD=ticket(integer(weights[0][1])),
        denominator=domain(integer(assignments[0]["denominator"])),
        qN=domain(by_shard([a["quantum"][0] for a in assignments])),
        qD=domain(by_shard([a["quantum"][1] for a in assignments])),
        piN=domain(integer(1)),
        piD=domain(integer(1)),
        mixtureD=integer(1),
        applyN=integer(profile["apply_quantum"][0]),
        applyD=integer(profile["apply_quantum"][1]),
        model=by_shard(witness.parent_state.model),
        optimizer=by_shard(witness.parent_state.momentum),
        muN=integer(profile["momentum"][0]),
        muD=integer(profile["momentum"][1]),
        lrN=integer(profile["learning_rate"][0]),
        lrD=integer(profile["learning_rate"][1]),
        wdN=integer(profile["weight_decay"][0]),
        wdD=integer(profile["weight_decay"][1]),
        limit=integer(127),
    )
    return {
        "schema_version": "1.0.0",
        "scope": "PINNED_FINITE_EMBEDDING_NOT_NATIVE_EXECUTION",
        "source_sha256": SOURCE_SHA256,
        "authority": snapshot["authority"],
        "context": witness.context,
        "root": witness.root,
        "artifact_sha256": {key: hashlib.sha256(raw).hexdigest() for key, raw in store.items()},
        "symbol_binding": {
            "t1": "t0000",
            "d1": "d1",
            "shard1": "s1",
            "shard2": "s2",
            "schema1": witness.root["schema"]["id"],
            "profile1": witness.root["profile"]["id"],
            "parent1": witness.context["parent_checkpoint"],
            "h1": witness.context["height"],
            "epoch1": witness.context["epoch"],
            "v1": "validator-1",
            "v2": "validator-2",
            "v3": "validator-3",
        },
        "native_accumulator_bits": profile["accumulator_bits"],
        "tlc_signed_limit": 127,
        "limit_claim": "This path is checked within [-128,127]; "
        "native INT64/INT128 coverage is NOT claimed.",
        "inputs": inputs,
        "parameters": bodies,
        "apply": applied,
    }


def generate(source=SOURCE, target=TARGET, module=None, config=None):
    result = derive(source)
    module = ROOT / "formal/tla/DeltaReduceFixtureInputs.tla" if module is None else module
    config = ROOT / "formal/proposals/public-arithmetic-replay.cfg" if config is None else config
    content = (
        "---- MODULE DeltaReduceFixtureInputs ----\nEXTENDS DeltaReducePublicState\n"
        "\\* Generated finite embedding from separately pinned native artifact bytes.\n"
        "\\* Source SHA256: " + SOURCE_SHA256 + "\n"
        "\\* Limit 127 is a finite TLC restriction, NOT a native arithmetic profile.\n"
        "CONSTANTS " + ", ".join("fixtureValue_" + name for name in sorted(MODEL_VALUES)) + "\n"
        "FixtureArithmeticInputs == "
        + tla_value(result["inputs"]).replace("witnessValue_", "fixtureValue_")
        + "\nFixtureParameterValues == {1, -2}\n====\n"
    )
    cfg = (ROOT / "formal/proposals/public-state-replay.cfg").read_text(encoding="utf-8")
    cfg = cfg.replace(
        "NativeArithmeticInputs <- ZeroArithmeticInputs",
        "NativeArithmeticInputs <- FixtureArithmeticInputs",
    )
    cfg = cfg.replace("Shards = {shard1}", "Shards = {shard1, shard2}")
    cfg = cfg.replace("ParameterValues = {0}", "ParameterValues <- FixtureParameterValues")
    cfg = cfg.replace("AccumulatorBound = 1\n", "AccumulatorBound = 127\n")
    cfg = cfg.replace("MaxDurableSequence = 2", "MaxDurableSequence = 8")
    cfg = cfg.replace("MaxLogicalTime = 2", "MaxLogicalTime = 100000")
    cfg = cfg.replace("SoftDeadline = 1\n", "SoftDeadline = 99999\n")
    cfg = cfg.replace("HardDeadline = 2", "HardDeadline = 100000")
    for flag in [
        "TicketActions",
        "AvailabilityActions",
        "CertificateActions",
        "PlanningActions",
        "ReduceApplyActions",
        "AggregateActions",
        "ApplyActions",
        "TimeoutActions",
    ]:
        cfg = cfg.replace(f"Enable{flag} = FALSE", f"Enable{flag} = TRUE")
    cfg += (
        "\n"
        + "\n".join(f"    fixtureValue_{name} = {name}" for name in sorted(MODEL_VALUES))
        + "\n"
    )
    # All validation precedes output. No regenerated authority or legacy snapshot is written.
    module.write_text(content, encoding="utf-8", newline="\n")
    config.write_text(cfg, encoding="utf-8", newline="\n")
    write_canonical_json(target, result)
    return result


if __name__ == "__main__":
    result = generate()
    print("Pinned artifact inputs and bounded two-shard TLA configuration generated")
