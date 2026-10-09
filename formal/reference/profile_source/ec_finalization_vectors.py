"""Synthetic EC cut/candidate vectors, not a lawful complete source history."""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

from formal.reference.isc_crypto import codec as crypto
from formal.reference.isc_source import finalization as isc
from formal.reference.isc_source import identity, policy
from formal.reference.isc_source.test_identity import synthetic_body
from formal.reference.non_isc import codec as non_isc
from formal.reference.non_isc.authentication import CONTRACT, AuthorityInputs
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import ec_finalization as ec
from formal.reference.profile_source.configuration_vectors import bytes_term as bs
from formal.reference.profile_source.configuration_vectors import value_term
from formal.reference.profile_source.installed_state_vectors import generate as installed
from formal.reference.profile_source.lineage_vectors import generate as lineage
from formal.reference.profile_source.test_configuration import ConfigurationTests
from formal.reference.profile_source.vote_vectors import wire_term


def fixture():
    _, originals = installed()
    test = ConfigurationTests()
    boot, backend = test.boot, test.backend
    config_raw, state_raw = (
        bytes.fromhex(originals["original_config"]),
        bytes.fromhex(originals["original_state"]),
    )
    config = cfg.decode(config_raw)
    p = policy.decode(bytes.fromhex(originals["original_policy"]))
    names = p["validator_ids"]
    body = replace(
        synthetic_body(),
        formal_semantics_id=boot.formal_semantics_id,
        arithmetic_profile_id=p["snapshot"]["arithmetic_profile_id"],
        height=int(config["height"]),
        parameter_schema_id=config["parameter_schema_id"],
        round_config_id=p["round_config_id"],
        round_id=config["round_id"],
        validator_epoch_id=boot.validator_epoch_id,
        view=int(config["view"]),
        parent_checkpoint_id=config["parent_checkpoint_id"],
    )
    _, links = lineage(body)
    lp = policy.decode(bytes.fromhex(links["whole_policy"]))
    norm_raw, seed_raw = bytes.fromhex(links["norm"]), bytes.fromhex(links["seed"])
    certificates = sorted(
        (identity.Certificate(body, tuple(names[:3])), identity.Certificate(body, tuple(names))),
        key=identity.certificate_id,
    )
    b = identity.body_id(body)
    eb = {
        "context": isc.body_tree(body)["context"],
        "entries": [
            {
                "accepted": True,
                "domain_id": "code",
                "gamma": {"numerator": 1, "denominator": 1},
                "reason_code": "ACCEPT",
                "ticket_id": "ticket-001",
            }
        ],
        "input_set_certificate_id": b,
        "norm_evidence_id": crypto.content_id("deltareduce.008.norm-evidence.v1", norm_raw),
        "robust_profile_id": "sha256:" + "e" * 64,
        "seed_transcript_id": crypto.content_id("deltareduce.008.seed-transcript.v1", seed_raw),
    }
    c4 = {k: deepcopy(v) for k, v in eb.items() if k != "seed_transcript_id"}
    c4.update(quorum_threshold=3, signer_ids=names)
    p["snapshot"].update(
        finalized_round_config_ids=[p["round_config_id"]],
        input_set_bodies=[isc.body_tree(body)],
        input_set_certificates=[isc.certificate_tree(c) for c in certificates],
        closed_input_set_ids=[b],
        finalized_input_set_ids=[b],
        norm_evidence=lp["snapshot"]["norm_evidence"],
        seed_transcripts=lp["snapshot"]["seed_transcripts"],
        eligibility_bodies=[eb],
        eligibility_certificates=[
            {"certificate": c4, "seed_transcript_id": eb["seed_transcript_id"]}
        ],
        finalized_eligibility_ids=[],
    )
    prior, raw_body = policy.encode(p), ec.body_bytes(eb)
    h, k = crypto.content_id(ec.BODY_DOMAIN, raw_body), ec.context_id(b)
    rows, signed_values = [], []
    for position, name in enumerate([*names[:3], names[0], names[3]], 1):
        vote = crypto.Vote(
            h,
            k,
            2,
            boot.formal_semantics_id,
            body.height,
            body.round_id,
            boot.validator_epoch_id,
            name,
            body.view,
        )
        raw_vote = non_isc.encode_vote(non_isc.NonIscVote(vote, "EC"))
        key, _ = test.keys[name]
        _, signature = backend.sign(
            test.signer.seeds[name], non_isc.preimage(test.registry_id, key, raw_vote)
        )
        artifact = crypto.Artifact(test.registry_id, key, raw_vote, signature)
        original_g = non_isc.encode_artifact(artifact)
        rows.append(ec.Delivery(position, p["local_validator_id"], original_g))
        signed_values.append((vote, artifact, original_g))
    table = {
        bytes.fromhex(raw): bytes.fromhex(digest)
        for raw, digest in originals["sha256_preimages"].items()
    }

    def add(domain, raw):
        pre = domain.encode() + b"\0" + raw
        table[pre] = sha256(pre).digest()

    for domain, raw in (
        (identity.BODY_DOMAIN, identity.body_preimage(body)),
        ("deltareduce.008.norm-evidence.v1", norm_raw),
        ("deltareduce.008.seed-transcript.v1", seed_raw),
        (ec.BODY_DOMAIN, raw_body),
        ("deltareduce.vote-context.ec.v1", ec.text64(b)),
        (ec.EC_DOMAIN, ec.certificate_bytes(boot.formal_semantics_id, c4)),
    ):
        add(domain, raw)
    for c in certificates:
        add(identity.CERTIFICATE_DOMAIN, identity.certificate_bytes(c))
    for t in body.tuples:
        pre = identity.LEAF_DOMAIN + identity.tuple_bytes(t)
        table[pre] = sha256(pre).digest()
    return dict(
        boot=boot,
        backend=backend,
        authority=AuthorityInputs(boot, CONTRACT),
        config=config,
        config_raw=config_raw,
        state=state_raw,
        p=p,
        prior=prior,
        body=raw_body,
        typed_body=eb,
        isc_certificates=certificates,
        seed=seed_raw,
        norm=norm_raw,
        rows=tuple(rows),
        signed_values=signed_values,
        table=table,
    )


def generate():
    f = fixture()
    p, boot = f["p"], f["boot"]
    actor = p["local_validator_id"]
    results = [
        ec.assemble_first(
            f["authority"],
            f["backend"],
            f["prior"],
            f["state"],
            f["body"],
            f["rows"],
            actor=actor,
            cut=cut,
            tick=0,
        )
        for cut in (4, 5)
    ]
    for result in results:
        pre = ec.EC_DOMAIN.encode() + b"\0" + result.certificate
        f["table"][pre] = sha256(pre).digest()
    state = ec.wire.read_state(f["state"], boot.formal_semantics_id)
    storage = f["config"]["availability_policy"]["storage_binding"]
    parts = (
        boot.formal_semantics_id,
        boot.validator_epoch_id,
        p["validator_ids"],
        storage["storage_epoch_id"],
        storage["storage_registry_id"],
    )
    enrolled = (
        "⟨"
        + ",".join(
            "[" + ",".join(bs(v.encode()) for v in part) + "]"
            if isinstance(part, list)
            else bs(part.encode())
            for part in parts
        )
        + "⟩"
    )
    raws = [identity.certificate_bytes(c) for c in f["isc_certificates"]]
    old_ec = ec.certificate_bytes(
        boot.formal_semantics_id, p["snapshot"]["eligibility_certificates"][0]["certificate"]
    )
    input_body = identity.body_preimage(f["isc_certificates"][0].body)
    lines = [
        "import ProfileEcFinalization",
        "open DeltaReduce.ProfileSource DeltaReduce.NativeReceiptBytes",
        "set_option maxRecDepth 30000",
        "set_option maxHeartbeats 12000000",
        "namespace EcFinalizationVectors",
        f"def enrolled : Configuration.Enrollment := {enrolled}",
        f"def actor : Bytes := {bs(actor.encode())}",
        f"def config : Bytes := {bs(f['config_raw'])}",
        f"def state : Bytes := {bs(f['state'])}",
        f"def sv : DeltaReduce.NativePolicyCodec.Value := {value_term(state)}",
        f"def prior : Bytes := {bs(f['prior'])}",
        f"def bodyId : Bytes := {bs(crypto.content_id(ec.BODY_DOMAIN, f['body']).encode())}",
        "def originals : Collections.Originals := ⟨",
        f"[{bs(input_body)}],[{','.join(bs(r) for r in raws)}],"
        f"[{bs(f['norm'])}],[{bs(f['seed'])}],",
        f"[{bs(f['body'])}],[{bs(old_ec)}],[],[],[],[],[],[],[],[],[]⟩",
        "def hash (raw : Bytes) : Bytes :=",
        *(f"  if raw = {bs(raw)} then {bs(digest)} else" for raw, digest in f["table"].items()),
        "  []",
    ]
    for i, (v, g, raw_g) in enumerate(f["signed_values"]):
        lines += [
            f"def wire{i} : Vote.WireVote := {wire_term('EC', v)}",
            f"def v{i} : Vote.Vote := ⟨wire{i},2,{v.height},{v.view}⟩",
            f"def g{i} : Vote.Artifact := ⟨{bs(g.registry_id.encode())},{bs(g.key_id.encode())},"
            f"{bs(g.vote_bytes)},{bs(g.signature)}⟩",
            f"def row{i} : ConfigurationQC.Received := "
            f"⟨{i + 1},actor,{bs(raw_g)},g{i},v{i},by decide +kernel⟩",
        ]
    lines += [
        "def rows : List ConfigurationQC.Received := [row0,row1,row2,row3,row4]",
        "def run (cut tick : Nat) (raw : Bytes) := "
        "EcFinalization.checkWhole hash enrolled actor config state raw sv originals "
        "cut tick bodyId rows",
    ]
    for cut, result in zip((4, 5), results, strict=True):
        lines += [
            f"example : (run {cut} 0 prior).map (fun x => (x.source.candidate.update.raw,",
            "  x.source.candidate.certificate.raw,x.source.candidate.certificate.value.id)) =",
            f"  some ({bs(result.next_policy)},{bs(result.certificate)},"
            f"{bs(result.certificate_id.encode())}) := by decide +kernel",
        ]
    lines += [
        "example : (run 2 0 prior).isNone = true := by decide +kernel",
        f"example : (run 4 {p['hard_deadline_tick']} prior).isNone = true := by decide +kernel",
        "def event (s : EcFinalization.Whole) (parent : Bytes) : Index.Event :=",
        '  ⟨5,.object .nil,actor,DeltaReduce.NativeVoteBytes.ascii "ACT-EC-FINALIZE",',
        "    s.source.candidate.certificate.raw,",
        f"    [prior,state,{bs(f['body'])},parent,{bs(f['seed'])},{bs(f['norm'])}],",
        "    [0,1,2,3,4]⟩",
        "example : ((run 4 0 prior).map (fun s =>",
        f"  ((EcFinalization.bindEvent (event s {bs(raws[0])}) s prior state actor 4 [0]).isSome,",
        f"   (EcFinalization.bindEvent (event s {bs(raws[1])}) "
        "s prior state actor 4 [0]).isSome)))",
        "  = some (true,true) := by decide +kernel",
        "example : ((run 4 0 prior).map (fun s =>",
        f"  (EcFinalization.bindEvent {{event s {bs(raws[0])} with dependencies := [0,1,2,3]}}",
        "    s prior state actor 4 [0]).isNone)) = some true := by decide +kernel",
        "example : ((run 4 0 prior).map (fun s =>",
        "  (EcFinalization.replay s s.following).isSome)) = some true := by decide +kernel",
        "example : ((run 4 0 prior).map (fun s =>",
        "  (EcFinalization.assemble hash s.following actor 5 0 bodyId rows).isNone))",
        "  = some true := by decide +kernel",
        "end EcFinalizationVectors",
    ]
    return "\n".join(lines) + "\n", {
        "evidence_kind": "SYNTHETIC_EC_SOURCE_CONJUNCTS_NOT_AUTHENTIC_PRODUCER_HISTORY",
        "prior_policy": f["prior"].hex(),
        "original_state": f["state"].hex(),
        "body": f["body"].hex(),
        "original_g": [r.original_g.hex() for r in f["rows"]],
        "results": [
            {
                "cut": cut,
                "certificate": r.certificate.hex(),
                "certificate_id": r.certificate_id,
                "next_policy": r.next_policy.hex(),
                "signers": r.signers,
            }
            for cut, r in zip((4, 5), results, strict=True)
        ],
        "sha256_preimages": {r.hex(): h.hex() for r, h in f["table"].items()},
    }
