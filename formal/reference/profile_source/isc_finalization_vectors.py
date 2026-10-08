"""Exact pure P0/C/P1 comparison, not an authenticated producing history."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import finalization, identity, policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.profile_source import capsule_binding as wire
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.installed_state_vectors import generate as installed
from formal.reference.profile_source.isc_vectors import lean_body
from formal.reference.profile_source.vote_vectors import wire_term


def generate():
    _, original = installed()
    config_raw = bytes.fromhex(original["original_config"])
    state_raw = bytes.fromhex(original["original_state"])
    # The original framed body is decoded by the existing reference codec.
    from formal.reference.profile_source.configuration import decode

    config = decode(config_raw)
    p = policy.decode(bytes.fromhex(original["original_policy"]))
    state = wire.read_envelope(
        state_raw, 5, wire.STATE_FIELDS, config["formal_semantics_id"], "ROUND_STATE"
    )
    names = p["validator_ids"]
    body = replace(
        synthetic_body(),
        formal_semantics_id=config["formal_semantics_id"],
        arithmetic_profile_id=p["snapshot"]["arithmetic_profile_id"],
        height=int(config["height"]),
        parameter_schema_id=config["parameter_schema_id"],
        round_config_id=p["round_config_id"],
        round_id=config["round_id"],
        validator_epoch_id=config["validator_epoch_id"],
        view=int(config["view"]),
        parent_checkpoint_id=config["parent_checkpoint_id"],
    )
    b = identity.body_id(body)
    c3 = identity.Certificate(body, tuple(names[:3]))
    c4 = identity.Certificate(body, tuple(names))
    p["snapshot"].update(
        finalized_round_config_ids=[p["round_config_id"]],
        input_set_bodies=[finalization.body_tree(body)],
        input_set_certificates=[finalization.certificate_tree(c4)],
        closed_input_set_ids=[b],
    )
    prior = policy.encode(p)
    expected = deepcopy(p)
    ordered = sorted((c3, c4), key=identity.certificate_id)
    expected["snapshot"]["input_set_certificates"] = [
        finalization.certificate_tree(c) for c in ordered
    ]
    expected["snapshot"]["finalized_input_set_ids"] = [b]
    following = policy.encode(expected)
    table = {
        bytes.fromhex(raw): bytes.fromhex(digest)
        for raw, digest in original["sha256_preimages"].items()
    }
    round_raw = body.round_id.encode()
    ctx_pre = b"deltareduce.vote-context.isc.v1\0" + len(round_raw).to_bytes(8, "big") + round_raw
    context = "sha256:" + sha256(ctx_pre).hexdigest()
    preimages = [
        ctx_pre,
        identity.LEAF_DOMAIN + identity.tuple_bytes(body.tuples[0]),
        identity.BODY_DOMAIN.encode() + b"\0" + identity.body_preimage(body),
        *(
            identity.CERTIFICATE_DOMAIN.encode() + b"\0" + identity.certificate_bytes(c)
            for c in (c3, c4)
        ),
    ]
    table.update({raw: sha256(raw).digest() for raw in preimages})
    storage = config["availability_policy"]["storage_binding"]
    parts = (
        body.formal_semantics_id,
        body.validator_epoch_id,
        names,
        storage["storage_epoch_id"],
        storage["storage_registry_id"],
    )
    enrollment = (
        "⟨"
        + ",".join(
            "[" + ",".join(bs(s.encode()) for s in part) + "]"
            if isinstance(part, list)
            else bs(part.encode())
            for part in parts
        )
        + "⟩"
    )
    lines = [
        "import ProfileIscFinalization",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "open DeltaReduce.ISCSourceV2",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 8000000",
        "namespace IscFinalizationVectors",
        f"def enrolled : Configuration.Enrollment := {enrollment}",
        f"def actor : Bytes := {bs(p['local_validator_id'].encode())}",
        f"def config : Bytes := {bs(config_raw)}",
        f"def state : Bytes := {bs(state_raw)}",
        f"def sv : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        f"def prior : Bytes := {bs(prior)}",
        f"def following : Bytes := {bs(following)}",
        f"def body : Body := {lean_body(body)}",
        f"def b : Bytes := {bs(b.encode())}",
        f"def c : Bytes := {bs(identity.certificate_id(c3).encode())}",
        f"def certificate : Bytes := {bs(identity.certificate_bytes(c3))}",
        "def originals : Collections.Originals := ⟨",
        f"  [{bs(identity.body_preimage(body))}],[{bs(identity.certificate_bytes(c4))}],",
        "  [],[],[],[],[],[],[],[],[],[],[],[],[]⟩",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in table.items()),
        "  []",
    ]
    deliveries = []
    for i, signer in enumerate([*names[:3], names[0], names[3]]):
        vote = crypto.Vote(
            b,
            context,
            2,
            body.formal_semantics_id,
            body.height,
            body.round_id,
            body.validator_epoch_id,
            signer,
            body.view,
        )
        frame = crypto.encode_vote(vote)
        g = crypto.Artifact("sha256:" + "4" * 64, "sha256:" + "5" * 64, frame, bytes(64))
        raw_g = crypto.encode_artifact(g)
        lines += [
            f"def wire{i} : Vote.WireVote := {wire_term('ISC', vote)}",
            f"def v{i} : Vote.Vote := ⟨wire{i},2,{body.height},{body.view}⟩",
            f"def g{i} : Vote.Artifact := ⟨{bs(g.registry_id.encode())},"
            f"{bs(g.key_id.encode())},{bs(frame)},{bs(g.signature)}⟩",
            f"def row{i} : ConfigurationQC.Received := ⟨{i + 1},actor,"
            f"{bs(raw_g)},g{i},v{i},by decide +kernel⟩",
        ]
        deliveries.append(
            {
                "position": i + 1,
                "original_G": raw_g.hex(),
                "signature_status": "ZERO_BYTES_STRUCTURAL_ONLY",
            }
        )
    lines += [
        "def rows : List ConfigurationQC.Received := [row0,row1,row2,row3,row4]",
        "def run (cut tick : Nat) (id : Bytes) (inventory : List ConfigurationQC.Received) :=",
        "  IscFinalization.fromBytes hash enrolled actor config state prior sv originals",
        "    cut tick id body.tuples inventory",
        "example : (run 4 0 b rows).map (fun x => (x.candidate.update.raw,",
        "  x.candidate.certificate.originalBytes,x.candidate.certificate.consensusId,",
        "  x.candidate.certificate.witnessId,x.candidate.quorum.originalRows.length))",
        "  = some (following,certificate,b,c,5) := by decide +kernel",
        "example : (run 2 0 b rows).isNone = true := by decide +kernel",
        f"example : (run 4 {p['hard_deadline_tick']} b rows).isNone = true := by decide +kernel",
        "example : (run 4 0 c rows).isNone = true := by decide +kernel",
        "example : (run 4 0 b [row0,row0,row1]).isNone = true := by decide +kernel",
        "end IscFinalizationVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_PURE_FINALIZATION_NOT_PRODUCER_OR_AUTHORITY",
        "original_config": config_raw.hex(),
        "original_state": state_raw.hex(),
        "original_policy": prior.hex(),
        "expected_policy": following.hex(),
        "original_deliveries": deliveries,
        "certificate": identity.certificate_bytes(c3).hex(),
        "b": b,
        "c": identity.certificate_id(c3),
        "previous_c": identity.certificate_id(c4),
        "sha256_preimages": {raw.hex(): digest.hex() for raw, digest in table.items()},
    }
