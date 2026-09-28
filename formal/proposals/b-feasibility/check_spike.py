"""Isolated B spike: pinned diagnostic source, one carrier, synchronous TLA views.

Never regenerates production fixtures/schemas or changes a protocol predicate.
The original diagnostic receipt is NOT a production WAL/fsync attestation.
"""

# The standalone proposal deliberately imports existing, unchanged repository
# checkers after adding their directories. It is not a new installed package.
# ruff: noqa: E402

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "formal/scripts"))
sys.path.insert(0, str(ROOT / "formal/proposals"))
import native_binding as n
from formal_artifacts import load_json_strict, sha256_file, write_canonical_json
from native_durability_witness import check_durability_trace, persisted_bytes
from native_trace_witness import NativeEvidence
from public_state_projection import inventory
from run_formal_gate import tla_runtime

SOURCE = ROOT / "formal/fixtures/traces/native/native-coordinate-matrix.json"
TRACE = ROOT / "formal/fixtures/traces/legal/native-coordinate-matrix.json"
SOURCE_SHA = "3a891969a20a5cf98a7d31a20f739d73d462cf676a65430163cd736c67aea344"
TRACE_SHA = "1b13490c6cc4ca331479bac2d248b374c8755d1447bb2e51ff4af65aac6b3255"
BUILD = ROOT / "formal/build/b-feasibility"
EVIDENCE = ROOT / "formal/proposals/evidence/b-feasibility"


def tla(x):
    if isinstance(x, bool):
        return "TRUE" if x else "FALSE"
    if isinstance(x, str):
        return json.dumps(x)
    if isinstance(x, int):
        return str(x) if x >= 0 else f"({x})"
    if isinstance(x, list):
        return "<<" + ", ".join(map(tla, x)) + ">>"
    if isinstance(x, dict):
        return "(" + " @@ ".join(f"({tla(k)} :> {tla(v)})" for k, v in x.items()) + ")"
    raise TypeError(x)


def source():
    n.require(sha256_file(SOURCE) == SOURCE_SHA, "PINNED_SOURCE")
    n.require(sha256_file(TRACE) == TRACE_SHA, "PINNED_TRACE")
    trace = load_json_strict(TRACE)
    evidence = NativeEvidence(SOURCE, SOURCE_SHA)
    check_durability_trace(trace, evidence)
    event = trace["events"][22]
    n.require(event["vote_context_id"] == "PARAM:d00:s01:round-1", "SELECTED_ORIGINAL")
    snapshot = evidence.snapshots[event["arithmetic_witness"]["snapshot_id"]]
    witness = n.Witness(n.NativeAnchor(**snapshot["anchor"]), snapshot["authority"], evidence.store)
    body = witness.expected_parameter("d00", "s01")
    command = n.canonical({"action": "ACT-PARAM-VOTE", "payload": body}).decode("ascii")
    n.require(command == event["arithmetic_witness"]["command_ascii"], "ORIGINAL_COMPUTATION")
    n.require(n.digest(n.canonical(body)) == event["body_hash"], "ORIGINAL_BODY_ID")
    operation = evidence.operations[event["durability_witness"]]
    receipt, effect = persisted_bytes(event)
    n.require(
        (receipt, effect) == (operation["receipt_ascii"], operation["effect_ascii"]),
        "ORIGINAL_RECORD",
    )
    n.require(
        (operation["sequence_before"], operation["sequence_after"]) == (5, 6), "ORIGINAL_SEQUENCE"
    )
    certificate = trace["events"][25]
    n.require(certificate["body_hash"] == event["body_hash"], "CERTIFICATE_BODY")
    votes = trace["events"][22:25]
    n.require(
        [v["actor_id"] for v in votes] == [f"validator-{i}" for i in (1, 2, 3)], "ORIGINAL_SIGNERS"
    )
    n.require(
        all(v["body_hash"] == event["body_hash"] and v["durable_sequence"] == 6 for v in votes),
        "SAME_WHOLE_VOTE",
    )
    parents = {e["result_hash"] for e in trace["events"][:22] if e["result_hash"] is not None}
    for vote in votes:
        evidence.check(vote, trace["round_contract"], parents)
    # Keep the complete original preimages once. QC result is an original
    # synthetic trace label: no invented signed certificate preimage/authentication.
    carrier = dict(
        shard="s01",
        domain="d00",
        offset=witness.shards["s01"][0],
        length=witness.shards["s01"][1],
        body=body,
        command_ascii=command,
        vote_event=event,
        certificate_event=certificate,
        durability=operation,
        coordinates=trace["round_contract"]["parameter_schema"]["coordinates"][2:5],
        model=list(witness.parent_state.model[2:5]),
        optimizer=list(witness.parent_state.momentum[2:5]),
        q={
            c["ticket"]: n.resolve(witness.store, c["q"], "Q_SHARD")["values"]
            for c in witness.assignments["d00", "s01"]["contributions"]
        },
    )
    return witness, carrier


def family(carrier):
    return {
        "original": copy.deepcopy(carrier),
        "views": [
            {
                "k": k,
                "coordinate": carrier["coordinates"][k],
                "value": value,
                "model": carrier["model"][k],
                "optimizer": carrier["optimizer"][k],
                "q": {t: values[k] for t, values in carrier["q"].items()},
            }
            for k, value in enumerate(carrier["body"]["numerators"])
        ],
    }


def reconstruct(image, carrier):
    n.require(set(image) == {"original", "views"}, "FAMILY_FIELDS")
    n.require(n.canonical(image["original"]) == n.canonical(carrier), "SINGLE_ORIGINAL_CARRIER")
    views = image["views"]
    n.require(len(views) == carrier["length"], "COMPLETE_COORDINATES")
    for k, row in enumerate(views):
        n.require(
            set(row) == {"k", "coordinate", "value", "model", "optimizer", "q"},
            "NO_COORDINATE_PROTOCOL_FIELDS",
        )
        n.require(type(row["k"]) is int and row["k"] == k, "ORDERED_INDEX")
        n.require(row["coordinate"] == carrier["coordinates"][k], "ORIGINAL_COORDINATE")
        n.require(set(row["q"]) == set(carrier["q"]), "COMPLETE_TICKET_ROWS")
    restored = dict(
        model=[r["model"] for r in views],
        optimizer=[r["optimizer"] for r in views],
        q={t: [r["q"][t] for r in views] for t in carrier["q"]},
    )
    n.require(
        n.canonical(restored) == n.canonical({k: carrier[k] for k in restored}), "FULL_VECTOR_STATE"
    )
    body = {**carrier["body"], "numerators": [row["value"] for row in views]}
    raw = n.canonical({"action": "ACT-PARAM-VOTE", "payload": body}).decode("ascii")
    n.require(raw == carrier["command_ascii"], "FULL_ORIGINAL_COMMAND")
    return raw


def family_checks(carrier):
    image = family(carrier)
    n.require(reconstruct(image, carrier) == carrier["command_ascii"], "ROUNDTRIP")
    cases = {}

    def reject(name, reason, change):
        candidate = copy.deepcopy(image)
        change(candidate)
        try:
            reconstruct(candidate, carrier)
        except n.BindingError as err:
            n.require(str(err) == reason, f"WRONG_REJECTION:{name}:{err}")
        else:
            raise AssertionError(f"accepted corrupted family: {name}")
        cases[name] = reason

    reject("missing", "COMPLETE_COORDINATES", lambda x: x["views"].pop())
    reject("extra", "COMPLETE_COORDINATES", lambda x: x["views"].append(x["views"][0]))
    reject("reordered", "ORDERED_INDEX", lambda x: x["views"].reverse())
    reject("duplicate-index", "ORDERED_INDEX", lambda x: x["views"][1].update(k=0))
    reject(
        "coordinate-identity",
        "NO_COORDINATE_PROTOCOL_FIELDS",
        lambda x: x["views"][0].update(vote_id="invented"),
    )
    reject(
        "changed-coordinate",
        "ORIGINAL_COORDINATE",
        lambda x: x["views"][0].update(coordinate="p0000"),
    )
    reject("changed-result", "FULL_ORIGINAL_COMMAND", lambda x: x["views"][1].update(value=4))
    reject("changed-model", "FULL_VECTOR_STATE", lambda x: x["views"][1].update(model=0))
    reject("changed-optimizer", "FULL_VECTOR_STATE", lambda x: x["views"][2].update(optimizer=0))
    reject("changed-input", "FULL_VECTOR_STATE", lambda x: x["views"][0]["q"].update(t0000=100))
    reject(
        "changed-sequence",
        "SINGLE_ORIGINAL_CARRIER",
        lambda x: x["original"]["durability"].update(sequence_after=7),
    )
    reject(
        "changed-certificate",
        "SINGLE_ORIGINAL_CARRIER",
        lambda x: x["original"]["certificate_event"].update(result_hash="invented"),
    )
    write_canonical_json(EVIDENCE / "family.json", image)
    return cases


def run_lean(w, carrier):
    lake = os.environ.get("SPIKE_LAKE", "D:/formal-tools-20260920/lean/bin/lake.exe")
    env = {**os.environ, "LEAN_PATH": str(BUILD)}
    commands = []

    def check(name, args):
        cmd = [lake, *args]
        p = subprocess.run(
            cmd,
            cwd=ROOT / "formal/proofs",
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        output = p.stdout + p.stderr
        path = EVIDENCE / f"{name}.txt"
        path.write_text(output, encoding="utf-8", newline="\n")
        n.require(p.returncode == 0, f"LEAN:{name}")
        n.require(name == "dependencies" or "warning:" not in output, f"NEW_LEAN_WARNING:{name}")
        n.require("sorryAx" not in output, "SORRY_AXIOM")
        commands.append(
            dict(name=name, command=cmd, exit_code=p.returncode, log_sha256=sha256_file(path))
        )
        return output

    check(
        "dependencies",
        [
            "build",
            "DeltaReduce.PublicApplyArithmetic",
            "DeltaReduce.NativeVectorArithmeticVectors",
            "DeltaReduce.RecoveryKernel",
        ],
    )
    for name, original in (
        ("VectorShardRepresentation", ROOT / "formal/proposals/vector-shard-representation.lean"),
        ("SyncFamily", Path(__file__).with_name("SyncFamily.lean")),
    ):
        copy = BUILD / f"{name}.lean"
        shutil.copyfile(original, copy)
        n.require(sha256_file(copy) == sha256_file(original), "EXACT_PROPOSAL_COPY")
        check(
            name, ["env", "lean", f"--root={BUILD}", "-o", str(BUILD / f"{name}.olean"), str(copy)]
        )
    # The generated numeric fixture reads the same full original shard. Its
    # identity remains parametric: no fabricated byte decoder/authentication.
    rows = []
    for c in w.assignments["d00", "s01"]["contributions"]:
        values = n.resolve(w.store, c["q"], "Q_SHARD")["values"]
        rows.append(f"⟨{c['weight'][0]}, {c['weight'][1]}, {values}⟩")
    values = carrier["body"]["numerators"]
    denominator = carrier["body"]["denominator"]
    cells = ", ".join(
        f"⟨{carrier['q']['t0000'][k]}, {values[k]}, "
        f"{carrier['model'][k]}, {carrier['optimizer'][k]}⟩"
        for k in range(3)
    )
    numeric = f"""import SyncFamily
namespace DeltaReduce.BFeasibilityFixture
open BFeasibility
def rows : List ParameterKernel.Row := [{", ".join(rows)}]
theorem checkedOriginal :
  ParameterKernel.checkedParameter (-128) 127 (-128) 127 {denominator} 3 rows =
    some {values} := by decide
theorem actualFamily (original : Original) (control : RecoveryKernel.State) :
  ∃ s : Whole Original 3, s.original = original ∧ s.control = control ∧
    s.values = {values} ∧ reconstruct (project s) = s ∧
    ∀ k : Fin 3, ParameterKernel.checkedParameter (-128) 127 (-128) 127 {denominator} 1
      (rows.map (VectorShardRepresentation.rowAt k.val)) = some [(project s).coordinate k] :=
  checked_parameter_family checkedOriginal original control
structure Cell where
  input : Int
  parameter : Int
  model : Int
  optimizer : Int
  deriving DecidableEq
def fullState : Whole String 3 Cell := ⟨"s01", exampleControl,
  [{cells}], rfl⟩
theorem wholeStateRoundTrip : reconstruct (project fullState) = fullState :=
  reconstruct_project fullState
theorem originalModel : (reconstruct (project fullState)).values.map Cell.model =
  {carrier["model"]} := by decide
theorem originalOptimizer : (reconstruct (project fullState)).values.map Cell.optimizer =
  {carrier["optimizer"]} := by decide
end DeltaReduce.BFeasibilityFixture
"""
    fixture = BUILD / "Fixture.lean"
    source = Path(__file__).with_name("SyncFamily.lean").read_text(encoding="utf-8")
    names = re.findall(r"^(?:structure|def|theorem) (\w+)", source, re.M)
    fixture_names = re.findall(r"^(?:structure|def|theorem) (\w+)", numeric, re.M)
    audit = [f"DeltaReduce.BFeasibility.{name}" for name in names]
    audit += [f"DeltaReduce.BFeasibilityFixture.{name}" for name in fixture_names]
    numeric += "\n".join(f"#print axioms {name}" for name in audit) + "\n"
    fixture.write_text(numeric, encoding="utf-8", newline="\n")
    output = check("fixture-kernel-axioms", ["env", "lean", str(fixture)])
    audited = re.findall(
        r"'([^']+)' (?:does not depend on any axioms|depends on axioms: \[(.*?)\])", output, re.S
    )
    n.require({name for name, _ in audited} == set(audit), "COMPLETE_AXIOM_AUDIT")
    for _, axioms in audited:
        n.require(
            set(axioms.replace("\n", "").replace(" ", "").split(","))
            <= {"", "propext", "Quot.sound", "Classical.choice"},
            "UNEXPECTED_AXIOM",
        )
    shutil.copyfile(fixture, EVIDENCE / "Fixture.lean")
    return dict(commands=commands, audited_declarations=audit)


def inputs(w, k):
    # A selector is per ORIGINAL shard. The non-target s00 uses coordinate zero;
    # target s01 ranges over ALL three coordinates. No padding of short shards.
    index = {"s00": 0, "s01": k}
    weights, q = {}, {}
    for ticket, domain in w.tickets.items():
        q[ticket] = {}
        for shard in w.shards:
            a = w.assignments[domain, shard]
            c = next(c for c in a["contributions"] if c["ticket"] == ticket)
            n.require(
                ticket not in weights or weights[ticket] == c["weight"], "SHARED_TICKET_WEIGHT"
            )
            weights[ticket] = c["weight"]
            q[ticket][shard] = n.resolve(w.store, c["q"], "Q_SHARD")["values"][index[shard]]
    p = w.profile
    domain_weights = {d["domain"]: d["weight"] for d in p["domain_weights"]}
    den = {d: w.assignments[d, "s00"]["denominator"] for d in w.domains}
    n.require(
        all(w.assignments[d, s]["denominator"] == den[d] for d, s in w.assignments),
        "SHARED_DENOMINATOR",
    )
    result = dict(
        ticketOrder=list(w.tickets),
        domainOrder=w.domains,
        ticketDomain=w.tickets,
        q=q,
        weightN={t: v[0] for t, v in weights.items()},
        weightD={t: v[1] for t, v in weights.items()},
        denominator=den,
        qN={d: {s: w.assignments[d, s]["quantum"][0] for s in w.shards} for d in w.domains},
        qD={d: {s: w.assignments[d, s]["quantum"][1] for s in w.shards} for d in w.domains},
        piN={d: v[0] for d, v in domain_weights.items()},
        piD={d: v[1] for d, v in domain_weights.items()},
        mixtureD=math.lcm(*(v[1] for v in domain_weights.values())),
        applyN=p["apply_quantum"][0],
        applyD=p["apply_quantum"][1],
        model={s: w.parent_state.model[o + index[s]] for s, (o, _) in w.shards.items()},
        optimizer={s: w.parent_state.momentum[o + index[s]] for s, (o, _) in w.shards.items()},
        muN=p["momentum"][0],
        muD=p["momentum"][1],
        lrN=p["learning_rate"][0],
        lrD=p["learning_rate"][1],
        wdN=p["weight_decay"][0],
        wdD=p["weight_decay"][1],
        limit=127,
    )
    return result


def harness(w, carrier, mutation=None):
    names = inventory()
    types = (ROOT / "formal/tla/DeltaReduceTypes.tla").read_text()
    constants = re.search(r"CONSTANTS\s+(.*?)\nVARIABLES", types, re.S)[1].strip()
    declarations = ", ".join(f"p{k}_{v}" for k in range(3) for v in names)
    out = [
        "---- MODULE BFamilySpike ----\nEXTENDS Integers, FiniteSets, Sequences, TLC\n",
        "CONSTANTS Tickets, Domains, Shards, " + constants + "\n",
        "VARIABLES stage, originalJournal, originalQC, " + declarations + "\n",
        "ProjectedParameterValues == {-4, 1, 3, 5}\n",
        "Carrier == "
        + tla(
            {
                "command": carrier["command_ascii"],
                "receipt": carrier["durability"]["receipt_ascii"],
                "effect": carrier["durability"]["effect_ascii"],
                "qc": carrier["certificate_event"]["result_hash"],
                "body": carrier["vote_event"]["body_hash"],
                "shard": "s01",
            }
        )
        + "\n",
        'Signers == <<"validator-1", "validator-2", "validator-3">>\n',
        'Shard == IF stage < 11 THEN "s00" ELSE "s01"\n',
        "LocalStage == stage % 11\n",
        "Signer == Signers[((LocalStage - 1) \\div 3) + 1]\n",
        "Substep == (LocalStage - 1) % 3\n",
    ]
    for k in range(3):
        inp = inputs(w, k)
        out.append(f"Inputs{k} == {tla(inp)}\n")
        substitutions = [f"NativeArithmeticInputs <- Inputs{k}"] + [
            f"{v} <- p{k}_{v}" for v in names
        ]
        for prefix, module in (("V", "DeltaReducePhase6Harness"), ("P", "DeltaReduce")):
            out.append(f"{prefix}{k} == INSTANCE {module} WITH " + ",\n".join(substitutions) + "\n")
        out.append(f"""Body{k}(shard) == V{k}!ParameterResultBody(V{k}!HarnessAPC, "d00", shard,
    ConfiguredParentCheckpoint, ConfiguredParameterSchema, ConfiguredArithmeticProfile,
    V{k}!NativeParameterValue(V{k}!HarnessAPC, "d00", shard), TRUE)
Envelope{k} == V{k}!VoteEnvelope(Signer, "PARAMETER",
    V{k}!ParameterKey("d00", Shard), Body{k}(Shard))
Do{k} == CASE LocalStage = 0 -> V{k}!ProposeParameterResult(Body{k}(Shard))
    [] LocalStage = 10 -> V{k}!FinalizeParameterQC(Body{k}(Shard))
    [] Substep = 0 -> V{k}!VoteParameter(Signer, Body{k}(Shard))
    [] Substep = 1 -> V{k}!SendVoteEnvelope(Envelope{k})
    [] OTHER -> V{k}!DeliverVoteEnvelope(Envelope{k}, 1)
""")
    out.append(
        "InitSpike == /\\ stage = 0 /\\ originalJournal = <<>> /\\ originalQC = {}\n"
        + "\n".join(f" /\\ V{k}!Phase6Init" for k in range(3))
        + "\n"
    )
    actions = [f"Do{k}" for k in range(3)]
    if mutation == "partial-persist":
        variables = "<<" + ", ".join(f"p1_{v}" for v in names) + ">>"
        actions[1] = f"IF stage = 12 THEN UNCHANGED {variables} ELSE Do1"
    if mutation == "early-qc":
        actions = [
            f'IF stage = 18 THEN V{k}!FinalizeParameterQC(Body{k}("s01")) ELSE Do{k}'
            for k in range(3)
        ]
    out.append(
        "NextSpike == /\\ stage < 22 /\\ stage' = stage + 1\n"
        + "\n".join(f" /\\ ({a})" for a in actions)
        + "\n"
        + " /\\ originalJournal' = (IF stage = 12 THEN Append(originalJournal, Carrier.receipt) "
        + "ELSE originalJournal)\n"
        + " /\\ originalQC' = (IF stage = 21 THEN {Carrier.qc} ELSE originalQC)\n"
    )
    # Body-containing state differs numerically; all other 56 fields are equal.
    body_fields = {
        "durableVotes",
        "volatileVotes",
        "messages",
        "messageMultiplicity",
        "receivedVotes",
        "parameterResults",
        "parameterVotes",
        "parameterQCs",
    }
    common = [f"p0_{v} = p{k}_{v}" for k in (1, 2) for v in names if v not in body_fields]
    # Compare complete skeletons of all vote footprints, not just counts.
    for k in range(3):
        out.append(f"""Skeleton{k}(votes) ==
 {{[validator |-> v.validator, kind |-> v.kind, context |-> v.context] : v \\in votes}}
QC{k} == {{[domain |-> qc.body.domain, shard |-> qc.body.shard,
    signers |-> qc.signers] : qc \\in p{k}_parameterQCs}}
Results{k} == {{[domain |-> b.domain, shard |-> b.shard] : b \\in p{k}_parameterResults}}
Votes{k} == {{[validator |-> v.validator, domain |-> v.body.domain,
    shard |-> v.body.shard] : v \\in p{k}_parameterVotes}}
Copies{k} == {{[vote |-> Skeleton{k}({{x.vote}}), copy |-> x.copy] :
    x \\in p{k}_messageMultiplicity}}
""")
    common += [
        f"Skeleton0(p0_{v}) = Skeleton{k}(p{k}_{v})"
        for k in (1, 2)
        for v in ("durableVotes", "volatileVotes", "messages", "receivedVotes")
    ]
    common += [f"QC0 = QC{k}" for k in (1, 2)]
    common += [f"{name}0 = {name}{k}" for k in (1, 2) for name in ("Results", "Votes", "Copies")]
    out.append("CommonControl == /\\ " + "\n /\\ ".join(common) + "\n")
    out.append("""WholeRecordOnce ==
 /\\ Len(originalJournal) = (IF stage >= 13 THEN 1 ELSE 0)
 /\\ (stage >= 13 => originalJournal[1] = Carrier.receipt)
 /\\ originalQC = (IF stage = 22 THEN {Carrier.qc} ELSE {})
 /\\ (stage >= 13 => p0_durableSequence["validator-1"] = 6)
 /\\ (stage = 22 => QC0 = {
    [domain |-> "d00", shard |-> "s00", signers |-> {"validator-1", "validator-2", "validator-3"}],
    [domain |-> "d00", shard |-> "s01", signers |-> {"validator-1", "validator-2", "validator-3"}]})
""")
    out.append(
        "OriginalValues == /\\ "
        + "\n /\\ ".join(
            f'Body{k}("s01").value = {tla(v)}' for k, v in enumerate(carrier["body"]["numerators"])
        )
        + "\n"
    )
    out.append("Types == /\\ " + " /\\ ".join(f"V{k}!Phase6TypeOK" for k in range(3)) + "\n")
    out.append(
        "Allowed == /\\ "
        + "\n /\\ ".join(f"([][P{k}!Next]_(V{k}!ProtocolVariables))" for k in range(3))
        + "\n====\n"
    )
    config = (ROOT / "formal/proposals/public-arithmetic-replay.cfg").read_text()
    config = re.sub(r"^    (?:NativeArithmeticInputs|fixtureValue_).*\n", "", config, flags=re.M)
    replacements = {
        "Validators": '{"validator-1", "validator-2", "validator-3", "validator-4"}',
        "InitialByzantine": '{"validator-4"}',
        "Tickets": '{"t0000", "t0001", "t0002"}',
        "Domains": '{"d00", "d01", "d02"}',
        "Shards": '{"s00", "s01"}',
        "CompletedTickets": '{"t0000", "t0001", "t0002"}',
        "RequiredTickets": '{"t0000", "t0001", "t0002"}',
    }
    for key, val in replacements.items():
        config = re.sub(rf"^    {key} (?:=|<-) .*", f"    {key} = {val}", config, flags=re.M)
    config = config.replace(
        "ParameterValues <- FixtureParameterValues", "ParameterValues <- ProjectedParameterValues"
    )
    config += (
        "\nINIT InitSpike\nNEXT NextSpike\n"
        "INVARIANTS Types CommonControl WholeRecordOnce OriginalValues\nPROPERTIES Allowed\n"
    )
    config += "CHECK_DEADLOCK " + ("TRUE" if mutation == "early-qc" else "FALSE") + "\n"
    return "".join(out), config


def run_tlc(w, carrier, mutation=None):
    target = BUILD / (mutation or "positive")
    target.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "formal/tla").glob("*.tla"):
        shutil.copyfile(path, target / path.name)
    module, config = harness(w, carrier, mutation)
    (target / "BFamilySpike.tla").write_text(module, encoding="utf-8", newline="\n")
    (target / "BFamilySpike.cfg").write_text(config, encoding="utf-8", newline="\n")
    java, options, jar = tla_runtime()
    # Three instantiated production states need a deeper evaluator stack. This
    # isolated experiment records the extra JVM option; no toolchain lock changes.
    command = [
        java,
        *options,
        "-Xss16m",
        "-cp",
        str(jar),
        "tlc2.TLC",
        "-workers",
        "1",
        "-fp",
        "0",
        "-seed",
        "1",
        "-config",
        "BFamilySpike.cfg",
        "-metadir",
        "states",
        "BFamilySpike",
    ]
    proc = subprocess.run(
        command, cwd=target, capture_output=True, text=True, encoding="utf-8", timeout=90
    )
    output = proc.stdout + proc.stderr
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (target / "tlc.txt").write_text(output, encoding="utf-8", newline="\n")
    from check_public_state_replay import validate_success

    if mutation is None:
        parsed = validate_success(output, proc.returncode, 23)
        log = output
    else:
        code, marker, count, stage = {
            "partial-persist": (12, "Invariant CommonControl is violated", 14, 13),
            "early-qc": (11, "Deadlock reached", 19, 18),
        }[mutation]
        n.require(proc.returncode == code and output.count(marker) == 1, "EXPECTED_COUNTEREXAMPLE")
        n.require(
            f"{count} states generated, {count} distinct states found" in output,
            "COUNTEREXAMPLE_LENGTH",
        )
        n.require(f"/\\ stage = {stage}\n" in output, "COUNTEREXAMPLE_STAGE")
        n.require("Finished in " in output, "COMPLETE_TLC_OUTPUT")
        parsed = dict(expected_failure=marker, state_count=count, final_stage=stage)
        log = "Full raw counterexample retained in ignored build directory; excerpt below.\n"
        log += "raw_sha256=" + hashlib.sha256(output.encode()).hexdigest() + "\n"
        log += (
            "\n".join(
                line
                for line in output.splitlines()
                if line.startswith(("TLC2", "Error:", "State ", "/\\ stage =", "Finished in"))
                or "states generated" in line
            )
            + "\n"
        )
    path = EVIDENCE / f"{mutation or 'positive'}-tlc.txt"
    path.write_text(log, encoding="utf-8", newline="\n")
    result = dict(
        exit_code=proc.returncode,
        result=parsed,
        module_sha256=sha256_file(target / "BFamilySpike.tla"),
        config_sha256=sha256_file(target / "BFamilySpike.cfg"),
        log_sha256=sha256_file(path),
        command=command,
        raw_log_sha256=hashlib.sha256(output.encode()).hexdigest(),
    )
    print(mutation or "positive", json.dumps(parsed))
    return result


if __name__ == "__main__":
    BUILD.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    w, carrier = source()
    if len(sys.argv) > 1:
        run_tlc(w, carrier, sys.argv[1])
    else:
        cases = family_checks(carrier)
        lean = run_lean(w, carrier)
        tlc = {
            key: run_tlc(w, carrier, None if key == "positive" else key)
            for key in ("positive", "partial-persist", "early-qc")
        }
        for suffix in ("tla", "cfg"):
            shutil.copyfile(
                BUILD / "positive" / f"BFamilySpike.{suffix}", EVIDENCE / f"BFamilySpike.{suffix}"
            )
        result = dict(
            scope="ISOLATED_B_FEASIBILITY_NOT_R2_CLOSURE",
            result="FEASIBLE",
            completed_at_utc=datetime.now(UTC).isoformat(),
            source_sha256=SOURCE_SHA,
            trace_sha256=sha256_file(TRACE),
            coordinate_checks=cases,
            lean=lean,
            tlc=tlc,
        )
        write_canonical_json(EVIDENCE / "checks.json", result)
        print("FEASIBLE: isolated source/family/kernel/production-action experiment; not GO")
