"""One coherent full CONFIG/S0/P0 static join, before any finalized certificate.

The fixture is newly constructed synthetic input. It is not a pruned historical
snapshot, an authenticated genesis or a claimed complete native producer prefix.
"""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import policy
from formal.reference.non_isc import codec
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.native_header_vectors import policy_term
from formal.reference.profile_source.test_configuration import ConfigurationTests


def generate():
    ConfigurationTests.setUpClass()
    config = ConfigurationTests().body()
    raw_config = cfg.encode(config)
    cid = cfg.content_id(cfg.DOMAIN, raw_config)
    actor = config["validator_ids"][0]
    state = {
        "available_ticket_count": 0,
        "committed_ticket_count": 0,
        "config_id": cid,
        "durable_sequence": "0",
        "formal_semantics_id": config["formal_semantics_id"],
        "height": config["height"],
        "parent_checkpoint_id": config["parent_checkpoint_id"],
        "phase": "TICKETING_OPEN",
        "round_id": config["round_id"],
        "schema_version": "1.0.0",
        "state_root": "sha256:" + "8" * 64,
        "ticket_count": config["ticket_count"],
        "type_name": "ROUND_STATE",
        "view": config["view"],
    }
    raw_state = wire.envelope(5, state)
    snapshot = {}
    for name, shape in policy.SCHEMAS["snapshot"]:
        if policy.vector_shape(shape) is not None:
            snapshot[name] = []
        elif shape == "text":
            snapshot[name] = ""
        else:
            raise AssertionError("Unaccounted original snapshot field")
    snapshot.update(
        state_id=cfg.content_id("deltareduce:003:round-state:v1", raw_state),
        parameter_schema_id=config["parameter_schema_id"],
        arithmetic_profile_id="sha256:" + "3" * 64,
        proposed_round_config_ids=[cid],
    )
    parents = {name: "" for name, _ in policy.SCHEMAS["parents"]}
    parents.update(round_config_id=cid, parent_checkpoint_id=config["parent_checkpoint_id"])
    p = {
        "local_validator_id": actor,
        "validator_epoch_id": config["validator_epoch_id"],
        "validator_ids": config["validator_ids"],
        "role": 1,
        "round_id": config["round_id"],
        "round_config_id": cid,
        "configured_abort_reason": "INCOMPLETE_INPUT",
        "initial_logical_tick": 0,
        "soft_deadline_tick": int(config["soft_deadline_tick"]),
        "hard_deadline_tick": int(config["hard_deadline_tick"]),
        "snapshot": snapshot,
        "candidates": [
            {
                "action": 1,
                "body_hash": cid,
                "context_id": cfg.vote_context(int(config["height"]), config["validator_epoch_id"]),
                "height": int(config["height"]),
                "view": int(config["view"]),
                "parents": parents,
            }
        ],
    }
    raw_policy = policy.encode(p)
    vote = crypto.Vote(
        cid,
        p["candidates"][0]["context_id"],
        1,
        config["formal_semantics_id"],
        int(config["height"]),
        config["round_id"],
        config["validator_epoch_id"],
        actor,
        int(config["view"]),
    )
    vote_raw = codec.encode_vote(codec.NonIscVote(vote, "ROUND_CONFIG"))
    bad = deepcopy(p)
    bad["candidates"][0]["parents"]["round_config_id"] = "sha256:" + "9" * 64
    bad_raw = policy.encode(bad)
    # Static policy admission only requires this checkpoint slot to be a
    # content ID. The separate native live voting guard enforces current parent.
    # Do not accidentally strengthen the source domain at this static join.
    different_parent = deepcopy(p)
    different_parent["candidates"][0]["parents"]["parent_checkpoint_id"] = "sha256:" + "9" * 64
    different_parent_raw = policy.encode(different_parent)
    table = {}
    for domain, raw in (
        (cfg.DOMAIN, raw_config),
        ("deltareduce:003:round-state:v1", raw_state),
    ):
        preimage = domain.encode() + b"\0" + raw
        table[preimage] = sha256(preimage).digest()
    context_preimage = b"deltareduce.vote-context.config.v1\0"
    context_preimage += int(config["height"]).to_bytes(8, "big")
    epoch = config["validator_epoch_id"].encode()
    context_preimage += len(epoch).to_bytes(8, "big") + epoch
    table[context_preimage] = sha256(context_preimage).digest()
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
            "[" + ",".join(bs(v.encode()) for v in part) + "]"
            if isinstance(part, list)
            else bs(part.encode())
            for part in enrollment
        )
        + "⟩"
    )
    lines = [
        "import ProfileSelectedVote",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace InstalledStateVectors",
        f"def enrolled : Configuration.Enrollment := {enrolled}",
        f"def actor : Bytes := {bs(actor.encode())}",
        f"def config : Bytes := {bs(raw_config)}",
        f"def state : Bytes := {bs(raw_state)}",
        f"def sv : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        f"def original : Bytes := {bs(raw_policy)}",
        f"def bad : Bytes := {bs(bad_raw)}",
        f"def differentParent : Bytes := {bs(different_parent_raw)}",
        f"def vote : Bytes := {bs(vote_raw)}",
        f"def p : DeltaReduce.NativePolicyCodec.Value := {policy_term('policy', p)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  []",
        "def originals : Collections.Originals := ⟨[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]⟩",
        "def run (raw : Bytes) := InstalledState.bind hash enrolled actor config state raw sv "
        "originals",
        "example : (run original).map (fun out => (out.collections.finalizedConfigs.length,",
        "  out.collections.eligibility.lineage.inputs.certificates.length,out.candidates.length))",
        "  = some (0,0,1) := by decide +kernel",
        "example : (run bad).isNone = true := by decide +kernel",
        "example : (run differentParent).isSome = true := by decide +kernel",
        "def facts : DeltaReduce.NativeConfigAdmission.RuntimeFacts := ⟨0,true,false,false,1⟩",
        "def fresh (raw : Bytes) (r : DeltaReduce.NativeConfigAdmission.RuntimeFacts) :=",
        "  SelectedVote.bind hash enrolled actor config state raw sv originals r vote",
        "example : (fresh original facts).isSome = true := by decide +kernel",
        "example : (fresh differentParent facts).isNone = true := by decide +kernel",
        "example : (fresh original {facts with expectedSequence := 2}).isNone = true "
        ":= by decide +kernel",
        "example : (fresh original {facts with ready := false}).isNone = true := by decide +kernel",
        "example : (fresh original {facts with recovery := true, ready := false}).isSome = true "
        ":= by decide +kernel",
        "end InstalledStateVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_FULL_STATIC_JOIN_NOT_INITIAL_AUTHORITY",
        "original_config": raw_config.hex(),
        "original_state": raw_state.hex(),
        "original_policy": raw_policy.hex(),
        "original_vote": vote_raw.hex(),
        "wrong_candidate_configuration": bad_raw.hex(),
        "different_parent_requires_live_guard": different_parent_raw.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
