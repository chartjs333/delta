"""Fresh complete static unit/source cases, not a lawful producing history.

Each dependent artifact is assembled afresh for these fixtures. No historical
profile/QC bytes are upgraded, relabelled or used as a new-generation witness.
"""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source import arithmetic_units as u
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_units as cu
from formal.reference.profile_source import unit_state as unit
from formal.reference.profile_source.collections_vectors import generate as collections
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.test_arithmetic_units import numeric
from formal.reference.profile_source.test_configuration import ConfigurationTests


def generate():
    ConfigurationTests.setUpClass()
    config = ConfigurationTests().body()
    original = synthetic_body()
    numbers = numeric()
    numbers["domain_weights"][0]["domain_id"] = "code"
    config.update(
        schema_version="3.0.0",
        apply_arithmetic_profile_source=u.canonical(numbers).decode(),
        height=str(original.height),
        view=str(original.view),
        round_id=original.round_id,
        parameter_schema_id=original.parameter_schema_id,
        parent_checkpoint_id=original.parent_checkpoint_id,
        validator_ids=["a", "b", "c", "d"],
        soft_deadline_tick="100",
        hard_deadline_tick="200",
        domain_ticket_counts=[{"domain_id": "code", "ticket_count": 1}],
    )
    config_raw = cu.encode(config)
    body = replace(
        original,
        formal_semantics_id=config["formal_semantics_id"],
        validator_epoch_id=config["validator_epoch_id"],
        round_config_id=cfg.content_id(cfg.DOMAIN, config_raw),
    )
    _, full = collections(body, bind_value_hashes=True)
    ap = full["prior"]
    root, param = ap["prior"], ap["prior"]["prior"]
    plan, ec = param["prior"], param["prior"]["prior"]
    lineage, inputs = ec["prior"], ec["prior"]["input_collections"]
    table = {}
    for part in (full, ap, root, param, plan, ec, lineage, inputs):
        table.update(
            (bytes.fromhex(k), bytes.fromhex(v)) for k, v in part["sha256_preimages"].items()
        )

    def identifier(domain, raw):
        preimage = domain.encode() + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    p = policy.decode(bytes.fromhex(full["whole_policy"]))
    proof = p["snapshot"]["required_accumulator_proof_id"]
    profile = u.derive_profile(u.canonical(numbers), proof, body.formal_semantics_id)
    pid = identifier(u.DOMAIN, profile)
    other_numbers = deepcopy(numbers)
    other_numbers["apply_quantum"] = {"numerator": "3", "denominator": 7}
    other = u.derive_profile(u.canonical(other_numbers), proof, body.formal_semantics_id)
    identifier(u.DOMAIN, other)
    profile_raws = sorted((profile, other), key=lambda raw: cfg.content_id(u.DOMAIN, raw))
    p["snapshot"]["apply_profiles"] = [
        unit.core_view(u.decode_profile(raw, body.formal_semantics_id)) for raw in profile_raws
    ]
    candidate = deepcopy(p["snapshot"]["apply_candidates"][0])
    candidate["apply_arithmetic_profile_id"] = pid

    def payload(value, kind):
        return u.canonical(
            {
                **value["context"],
                **{k: v for k, v in value.items() if k != "context"},
                "formal_semantics_id": body.formal_semantics_id,
                "schema_version": "2.0.0",
                "type_name": kind,
            }
        )

    candidate_raw = payload(candidate, "APPLY_CANDIDATE")
    bid = identifier("deltareduce.008.apply-candidate.v1", candidate_raw)
    cert = deepcopy(p["snapshot"]["apply_qcs"][0]["certificate"])
    cert.update(apply_arithmetic_profile_id=pid, apply_candidate_id=bid)
    cert_raw = payload(cert, "APPLY_QC")
    qid = identifier("deltareduce.008.apply-qc.v1", cert_raw)
    identifier(
        "deltareduce.008.apply-qc.v1",
        payload({**cert, "signer_ids": p["validator_ids"]}, "APPLY_QC"),
    )
    p["snapshot"].update(
        apply_candidates=[candidate],
        apply_qcs=[{"candidate": candidate, "certificate": cert}],
        finalized_apply_ids=[qid],
    )
    state = full["state"]
    state_raw = wire.envelope(5, state)
    p["snapshot"]["state_id"] = identifier("deltareduce:003:round-state:v1", state_raw)
    p["initial_logical_tick"] = 0
    policy_raw = policy.encode(p)
    identifier(cfg.DOMAIN, config_raw)
    # Retain nonempty original downstream artifacts on the ABORT example.
    # This is a separately constructed incomplete-finalization snapshot, not
    # deletion of finalized lineage from a historical snapshot to admit it.
    abort = policy.decode(bytes.fromhex(full["abort_policy"]))
    abort["snapshot"]["state_id"] = p["snapshot"]["state_id"]
    for name in ("apply_profiles", "apply_candidates", "apply_qcs"):
        abort["snapshot"][name] = deepcopy(p["snapshot"][name])
    abort["initial_logical_tick"] = 0
    abort_raw = policy.encode(abort)
    wrong_abort = deepcopy(abort)
    wrong_abort["snapshot"]["abort_bodies"][0]["parameter_ids"] = []
    wrong_abort_raw = policy.encode(wrong_abort)
    arrays = [
        [inputs["body"]],
        inputs["certificates"],
        [lineage["norm"]],
        [lineage["seed"]],
        [ec["body"]],
        [ec["certificate"]],
        [plan["body"]],
        [plan["certificate"]],
        [param["body"]],
        [param["certificate"]],
        [root["body"]],
        [root["certificate"]],
        [raw.hex() for raw in profile_raws],
        [candidate_raw.hex()],
        [cert_raw.hex()],
    ]
    text_arrays = ["[" + ",".join(bs(bytes.fromhex(x)) for x in a) + "]" for a in arrays]
    parts = (
        str(body.height),
        body.parent_checkpoint_id,
        candidate["next_model_hash"],
        candidate["next_optimizer_hash"],
        qid,
    )
    pointer_payload = "|".join(parts).encode()
    table[pointer_payload] = sha256(pointer_payload).digest()
    line = pointer_payload + b"|" + table[pointer_payload].hex().encode()
    storage = config["availability_policy"]["storage_binding"]
    enrollment = (
        config["formal_semantics_id"],
        config["validator_epoch_id"],
        config["validator_ids"],
        storage["storage_epoch_id"],
        storage["storage_registry_id"],
    )
    enrolled = (
        "⟨"
        + ",".join(
            "[" + ",".join(bs(v.encode()) for v in x) + "]"
            if isinstance(x, list)
            else bs(x.encode())
            for x in enrollment
        )
        + "⟩"
    )
    before = (
        f"⟨⟨{bs(body.parent_checkpoint_id.encode())},"
        f"{bs(candidate['parent_optimizer_hash'].encode())},[],{body.height - 1}⟩,"
        f"{bs(body.parameter_schema_id.encode())},⟨1,4⟩,⟨1,4⟩⟩"
    )
    core = policy_term(
        "apply_profile", unit.core_view(u.decode_profile(profile, body.formal_semantics_id))
    )
    lines = [
        "import ProfileUnitCurrent",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000\nset_option maxHeartbeats 16000000",
        "namespace UnitStateVectors",
        f"def enrolled : Configuration.Enrollment := {enrolled}",
        f"def before : ConfigurationUnits.Parent := {before}",
        f"def config : Bytes := {bs(config_raw)}",
        f"def state : Bytes := {bs(state_raw)}",
        f"def sv : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        f"def policy : Bytes := {bs(policy_raw)}",
        f"def abort : Bytes := {bs(abort_raw)}",
        f"def wrongAbort : Bytes := {bs(wrong_abort_raw)}",
        f"def originals : Collections.Originals := ⟨{','.join(text_arrays)}⟩",
        f"def line : Bytes := {bs(line)}",
        f"def journal : Bytes := {bs(line + b'\n')}",
        f"def profile : Bytes := {bs(profile)}",
        f"def core : DeltaReduce.NativePolicyCodec.Value := {core}",
        *(f"def preimage{i} : Bytes := {bs(raw)}" for i, raw in enumerate(table)),
        "def hash (raw : Bytes) : Bytes :=",
        *(
            f"  if raw = preimage{i} then {bs(digest)} else"
            for i, digest in enumerate(table.values())
        ),
        "  []",
        "def input (raw : Bytes) : Current.Input := ⟨config,state,raw,sv,originals⟩",
        "def run (raw : Bytes) := UnitState.bind hash enrolled before "
        '(DeltaReduce.NativeVoteBytes.ascii "a") config state raw sv originals',
        "def current (raw : Bytes) := UnitCurrent.bind hash enrolled "
        '(DeltaReduce.NativeVoteBytes.ascii "a") before line (input raw)',
        "def scan (raw : Bytes) (xs : List Current.Input) := UnitCurrent.bindJournal hash enrolled "
        '(DeltaReduce.NativeVoteBytes.ascii "a") before (.bytes raw) xs',
        "example : (run policy).map (fun x => (x.collections.applies.originalProfiles.length,"
        "x.collections.core.applies.certificates.length)) = some (2,1) := by decide +kernel",
        "example : (run abort).map (fun x => (x.collections.core.tail.lineage.parameters.length,"
        "x.collections.core.tail.lineage.roots.length,x.collections.core.applies.certificates.length))"
        " = some (1,1,1) := by decide +kernel",
        "example : (run wrongAbort).isNone = true := by decide +kernel",
        "example : (current policy).map (fun x => (x.values.model,x.values.optimizer,"
        "x.after.modelQuantum.numerator,x.after.modelQuantum.denominator)) = "
        "some ([11,12,13,14],[0,1,0,-1],1,4) := by decide +kernel",
        "example : (current abort).isNone = true := by decide +kernel",
        "example : (scan journal [input policy]).map (fun x => x.chain.rows.length) = "
        "some 1 := by decide +kernel",
        "example : (scan line [input policy]).isNone = true := by decide +kernel",
        "example : (scan journal []).isNone = true := by decide +kernel",
        "example : (scan [] []).map (fun x => x.chain.current.modelQuantum.denominator) = "
        "some 4 := by decide +kernel",
        f"example : (UnitState.bindProfile hash {bs(body.formal_semantics_id.encode())} "
        "core (profile ++ [10])).isNone = true := by decide +kernel",
        "end UnitStateVectors",
    ]
    assert len(unit.bind_inventory(body.formal_semantics_id, policy_raw, profile_raws)) == 2
    assert all(sha256(raw).digest() == digest for raw, digest in table.items())
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_COMPLETE_STATIC_UNIT_STATE_NOT_PRODUCER_OR_RECOVERY",
        "configuration": config_raw.hex(),
        "state": state_raw.hex(),
        "policy": policy_raw.hex(),
        "abort_policy": abort_raw.hex(),
        "wrong_abort_policy": wrong_abort_raw.hex(),
        "original_collections": arrays,
        "pointer_line": line.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
