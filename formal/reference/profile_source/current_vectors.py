"""Fresh coherent configuration/collections/current fixture, not producer history.

All dependent objects are generated afresh. Existing component fixtures retain
their original bytes. The finite SHA table lists real preimages, not a hash axiom.
"""

from dataclasses import replace
from hashlib import sha256
from importlib import import_module

from formal.reference.isc_source import policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.test_configuration import ConfigurationTests

MODULES = (
    ("input_section", "InputSectionVectors"),
    ("lineage", "LineageVectors"),
    ("eligibility", "EligibilityVectors"),
    ("plan", "PlanVectors"),
    ("parameter", "ParameterVectors"),
    ("aggregate", "AggregateVectors"),
    ("apply", "ApplyVectors"),
    ("collections", "CollectionsVectors"),
)


def generate():
    ConfigurationTests.setUpClass()
    config = ConfigurationTests().body()
    original = synthetic_body()
    config.update(
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
    config_raw = cfg.encode(config)
    cid = cfg.content_id(cfg.DOMAIN, config_raw)
    body = replace(
        original,
        formal_semantics_id=config["formal_semantics_id"],
        validator_epoch_id=config["validator_epoch_id"],
        round_config_id=cid,
    )
    modules = {}
    for name, stem in MODULES:
        generator = import_module("formal.reference.profile_source." + name + "_vectors").generate
        if name in {"apply", "collections"}:
            text, artifacts = generator(body, bind_value_hashes=True)
        else:
            text, artifacts = generator(body)
        # Independent fresh namespaces keep the previous default byte evidence
        # separate. Only the Lean module names are changed, never protocol bytes.
        for _, old in MODULES:
            text = text.replace(old, "Current" + old)
        modules["Current" + stem] = text
    full = artifacts
    p = policy.decode(bytes.fromhex(full["whole_policy"]))
    state = full["state"]
    state_raw = wire.envelope(5, state)
    p["snapshot"]["state_id"] = cfg.content_id("deltareduce:003:round-state:v1", state_raw)
    p["initial_logical_tick"] = 0
    policy_raw = policy.encode(p)
    candidate = p["snapshot"]["apply_qcs"][0]["candidate"]
    qid = p["snapshot"]["finalized_apply_ids"][0]
    parts = (
        str(body.height),
        body.parent_checkpoint_id,
        candidate["next_model_hash"],
        candidate["next_optimizer_hash"],
        qid,
    )
    table = {}

    def pointer_line(parts):
        payload = "|".join(parts).encode()
        digest = sha256(payload).digest()
        table[payload] = digest
        return payload + b"|" + digest.hex().encode()

    line = pointer_line(parts)
    wrong_qc = pointer_line((*parts[:-1], "sha256:" + "9" * 64))
    wrong_parent = pointer_line((parts[0], "sha256:" + "9" * 64, *parts[2:]))
    for domain, raw in ((cfg.DOMAIN, config_raw), ("deltareduce:003:round-state:v1", state_raw)):
        preimage = domain.encode() + b"\0" + raw
        table[preimage] = sha256(preimage).digest()
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
        "import ProfileCurrent",
        "import CurrentCollectionsVectors",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace CurrentVectors",
        f"def enrolled : Configuration.Enrollment := {enrolled}",
        f"def config : Bytes := {bs(config_raw)}",
        f"def state : Bytes := {bs(state_raw)}",
        f"def policy : Bytes := {bs(policy_raw)}",
        f"def sv : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        "def input : Current.Input := ⟨config,state,policy,sv,CurrentCollectionsVectors.originals⟩",
        f"def line : Bytes := {bs(line)}",
        f"def wrongQc : Bytes := {bs(wrong_qc)}",
        f"def wrongParent : Bytes := {bs(wrong_parent)}",
        "def before : DeltaReduce.NativeCurrentPointer.State :=",
        f"  ⟨{bs(body.parent_checkpoint_id.encode())},"
        f"{bs(candidate['parent_optimizer_hash'].encode())},[],{body.height - 1}⟩",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  CurrentCollectionsVectors.hash raw",
        "def run (s : DeltaReduce.NativeCurrentPointer.State) (raw : Bytes) :=",
        '  Current.bind hash enrolled (DeltaReduce.NativeVoteBytes.ascii "a") s raw input',
        "example : (run before line).map (fun x => (x.values.model,x.values.optimizer)) =",
        "  some ([11,12,13,14],[0,1,0,-1]) := by decide +kernel",
        "example : (run before wrongQc).isNone = true := by decide +kernel",
        "example : (run before wrongParent).isNone = true := by decide +kernel",
        f"example : (run {{before with height := {body.height}}} line).isNone = true := "
        "by decide +kernel",
        "example : (run {before with optimizer := []} line).isNone = true := by decide +kernel",
        "end CurrentVectors",
    ]
    originals = {
        "evidence_kind": "SYNTHETIC_FULL_STATIC_CURRENT_JOIN_NOT_ORIGIN_OR_RECOVERY",
        "configuration": config_raw.hex(),
        "state": state_raw.hex(),
        "policy": policy_raw.hex(),
        "pointer_line_without_terminator": line.hex(),
        "wrong_qc_line": wrong_qc.hex(),
        "wrong_parent_line": wrong_parent.hex(),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
        "collections": full,
    }
    return modules, "\n".join(lines) + "\n", originals
