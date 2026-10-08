"""Complete static collections/candidates; no claim of a legal producing history."""

from copy import deepcopy
from hashlib import sha256

from formal.reference.isc_source import identity, policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source.apply_vectors import generate as apply
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.eligibility_vectors import text64, u64
from formal.reference.profile_source.isc_vectors import bs
from formal.reference.profile_source.parameter_vectors import texts
from formal.reference.profile_source.policy_vectors import projected


def generate(body=None, *, bind_value_hashes=False):
    body = synthetic_body() if body is None else body
    _, originals = apply(body, bind_value_hashes=bind_value_hashes)
    p = policy.decode(bytes.fromhex(originals["whole_policy"]))
    ctx = p["snapshot"]["input_set_bodies"][0]["context"]
    p.update(
        local_validator_id="a",
        validator_epoch_id=ctx["validator_epoch_id"],
        round_id=ctx["round_id"],
        round_config_id=ctx["round_config_id"],
        soft_deadline_tick=100,
        hard_deadline_tick=200,
    )
    p["snapshot"].update(
        parameter_schema_id=ctx["parameter_schema_id"],
        arithmetic_profile_id=ctx["arithmetic_profile_id"],
        proposed_round_config_ids=[ctx["round_config_id"]],
        finalized_round_config_ids=[ctx["round_config_id"]],
        timeout_observations=[],
        view_change_bodies=[],
        abort_requests=[],
        abort_bodies=[],
    )
    table = {}

    def identifier(domain, raw):
        preimage = domain.encode("ascii") + b"\0" + raw
        digest = sha256(preimage).digest()
        table[preimage] = digest
        return "sha256:" + digest.hex()

    parents = {key: "" for key in p["candidates"][0]["parents"]}
    parents.update(
        round_config_id=ctx["round_config_id"], parent_checkpoint_id=body.parent_checkpoint_id
    )
    p["candidates"] = [
        {
            "action": 2,
            "body_hash": identity.body_id(body),
            "context_id": identifier("deltareduce.vote-context.isc.v1", text64(ctx["round_id"])),
            "height": ctx["height"],
            "view": ctx["view"],
            "parents": parents,
        }
    ]
    state = {
        "available_ticket_count": 1,
        "committed_ticket_count": 1,
        "config_id": ctx["round_config_id"],
        "durable_sequence": "7",
        "formal_semantics_id": body.formal_semantics_id,
        "height": str(ctx["height"]),
        "parent_checkpoint_id": body.parent_checkpoint_id,
        "phase": "ELIGIBLE",
        "round_id": ctx["round_id"],
        "schema_version": "1.0.0",
        "state_root": "sha256:" + "7" * 64,
        "ticket_count": 1,
        "type_name": "ROUND_STATE",
        "view": str(ctx["view"]),
    }
    abort = deepcopy(p)
    # Existing native ABORT guard forbids finalized APPLY. Its candidate/QC
    # artifacts remain retained; no certificate list is cleared to pass it.
    abort["snapshot"]["finalized_apply_ids"] = []
    # Explicit native abort requests have only the two existing refusal reasons.
    # HARD_DEADLINE is a timer reason, not a request producer outcome.
    abort["configured_abort_reason"] = "INCOMPLETE_INPUT"
    ancestry = {
        "round_config_ids": "finalized_round_config_ids",
        "input_set_ids": "finalized_input_set_ids",
        "eligibility_ids": "finalized_eligibility_ids",
        "aggregation_plan_ids": "finalized_aggregation_plan_ids",
        "parameter_ids": "finalized_parameter_ids",
        "aggregate_root_ids": "finalized_aggregate_root_ids",
        "apply_ids": "finalized_apply_ids",
    }
    a = {
        "round_id": ctx["round_id"],
        "validator_epoch_id": ctx["validator_epoch_id"],
        "height": ctx["height"],
        "view": ctx["view"],
        "hard_deadline_tick": 200,
        "parent_checkpoint_id": body.parent_checkpoint_id,
        "reason_code": "INCOMPLETE_INPUT",
        **{key: abort["snapshot"][value] for key, value in ancestry.items()},
    }

    def abort_bytes(value):
        raw = text64(value["round_id"]) + text64(value["validator_epoch_id"])
        raw += u64(value["height"]) + u64(value["view"]) + u64(value["hard_deadline_tick"])
        raw += text64(value["parent_checkpoint_id"]) + text64(value["reason_code"])
        return raw + b"".join(texts(value[key]) for key in ancestry)

    a_raw = abort_bytes(a)
    a_id = identifier("deltareduce.vote.abort-body.v1", a_raw)
    abort["snapshot"]["abort_bodies"] = [a]
    abort["snapshot"]["abort_requests"] = [
        {"round_id": ctx["round_id"], "reason_code": "INCOMPLETE_INPUT"}
    ]
    abort["candidates"] = [
        {
            **p["candidates"][0],
            "action": 9,
            "body_hash": a_id,
            "context_id": identifier("deltareduce.vote-context.abort.v1", text64(ctx["round_id"])),
            "parents": {**parents, "reason_code": "INCOMPLETE_INPUT"},
        }
    ]
    wrong = deepcopy(abort)
    wrong_body = wrong["snapshot"]["abort_bodies"][0]
    wrong_body["parameter_ids"] = []
    wrong["candidates"][0]["body_hash"] = identifier(
        "deltareduce.vote.abort-body.v1", abort_bytes(wrong_body)
    )
    bad_request = deepcopy(abort)
    bad_request["snapshot"]["abort_requests"][0]["reason_code"] = "HARD_DEADLINE"
    lines = [
        "import ProfileCandidates\nimport ApplyVectors",
        "open DeltaReduce.ISCSourceV2 DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ProfileSource.InputSection",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace CollectionsVectors",
        "open InputSectionVectors DeltaReduce.ProfileSource",
        f"def p : DeltaReduce.NativePolicyBytes.Policy := {projected(p)}",
        f"def abort : DeltaReduce.NativePolicyBytes.Policy := {projected(abort)}",
        f"def wrong : DeltaReduce.NativePolicyBytes.Policy := {projected(wrong)}",
        f"def badRequest : DeltaReduce.NativePolicyBytes.Policy := {projected(bad_request)}",
        f"def state : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(r)} then {bs(d)} else" for r, d in table.items()),
        "  ApplyVectors.hash raw",
        "def originals : Collections.Originals :=",
        "  ⟨[bodyRaw],raws,[LineageVectors.normRaw],[LineageVectors.seedRaw],",
        "    [EligibilityVectors.bodyRawEC],[EligibilityVectors.certRawEC],",
        "    [PlanVectors.bodyRawAPC],[PlanVectors.certRawAPC],",
        "    [ParameterVectors.bodyRawP],[ParameterVectors.certRawP],",
        "    [AggregateVectors.bodyRawR],[AggregateVectors.certRawR],",
        "    [ApplyVectors.profileRaw],[ApplyVectors.candidateRaw],[ApplyVectors.certRawA]⟩",
        "def run (p : DeltaReduce.NativePolicyBytes.Policy) := do",
        "  let s ← NativeHeader.readCoarse state",
        "  let b ← Collections.bind hash s p originals",
        "  let es ← Candidates.checkAll hash p s b p.candidates",
        "  some (b,es)",
        "example : (run p).map (fun x => (x.1.applies.finalized.length,x.2.length))",
        "  = some (1,1) := by decide +kernel",
        "example : (run abort).map (fun x =>",
        "  (x.1.tail.lineage.parameters.length,x.1.tail.lineage.roots.length,",
        "   x.1.tail.lineage.applies.length,x.1.applies.certificates.length,x.2.length))",
        "  = some (1,1,0,1,1) := by decide +kernel",
        "example : (run wrong).isNone = true := by decide +kernel",
        "example : (run badRequest).isNone = true := by decide +kernel",
        "end CollectionsVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_COMPLETE_STATIC_COLLECTIONS_NOT_LEGAL_HISTORY",
        "prior": originals,
        "whole_policy": policy.encode(p).hex(),
        "state": state,
        "abort_policy": policy.encode(abort).hex(),
        "changed_abort_policy": policy.encode(wrong).hex(),
        "bad_request_policy": policy.encode(bad_request).hex(),
        "abort_body": a_raw.hex(),
        "sha256_preimages": {r.hex(): d.hex() for r, d in table.items()},
    }
