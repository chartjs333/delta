"""Exact original B/context to future native seed bytes. No finality/authority inference."""

from formal.reference.isc_crypto import codec as c
from formal.reference.isc_source import identity
from formal.reference.isc_source.authentication import registry
from formal.reference.seed_source import agreement as a
from formal.reference.seed_source import pvss as p


def profile_descriptor():
    return c._json(
        {
            "schema_version": "1.0.0",
            "profile": "SEED-PVSS-PBFT-REFERENCE-v1",
            "group": "edwards25519-prime-subgroup",
            "group_order": str(p.L),
            "generator": "libsodium-1.0.22-from-uniform-sha256-first-nonidentity",
            "validators": "4",
            "fault_bound": "1",
            "threshold": "3",
            "coefficient_derivation": "HMAC-SHA512-original-enrolled-seed-instance-index-mod-L",
            "proofs": "domain-separated-DLEQ-SHA512",
            "nonce_derivation": "1+HMAC-SHA512-original-enrolled-seed-core-index-mod-(L-1)",
            "agreement": a.PROFILE,
            "contribution": p.PROFILE,
            "output": "SHA256-domain-instance-sum-recovered-points",
            "native_transcript": "schema-2-consensus-b-sorted-committed-DEAL-ids",
        }
    )


def profile_id():
    return c.content_id("deltareduce.seed-reference-profile.v1", profile_descriptor())


def context_from_body(boot, original_body, original_cut_id):
    """Full source fold supplies a retained original cut; a hash is not its authority."""
    body = identity.decode_body_preimage(original_body)
    fields = {
        name: getattr(body, name)
        for name in (
            "formal_semantics_id",
            "arithmetic_profile_id",
            "parameter_schema_id",
            "round_config_id",
            "round_id",
            "validator_epoch_id",
            "parent_checkpoint_id",
        )
    }
    fields.update(
        height=str(body.height),
        view=str(body.view),
        isc_body_id=identity.body_id(body),
        source_cut_id=original_cut_id,
        registry_id=registry(boot)[0],
        origin_id=boot.origin_id,
    )
    p.context(boot, fields)
    return fields


def candidate_transcript(group, boot, original_body, original_cut_id, originals, commits, openings):
    """Candidate bytes only; full producing-fold/commit/release evidence still mandatory."""
    context = context_from_body(boot, original_body, original_cut_id)
    seed_id, evidence = a.reconstruct_candidate(group, boot, context, originals, commits, openings)
    proposal = evidence.committed(commits)
    fields = {
        name: context[name]
        for name in (
            "formal_semantics_id",
            "arithmetic_profile_id",
            "parameter_schema_id",
            "round_config_id",
            "round_id",
            "validator_epoch_id",
        )
    }
    fields.update(
        height=int(context["height"]),
        view=int(context["view"]),
        schema_version="2.0.0",
        type_name="SEED_TRANSCRIPT",
        input_set_certificate_id=context["isc_body_id"],
        seed_id=seed_id,
        seed_profile_id=profile_id(),
        share_ids=sorted(proposal.deals),
    )
    raw = identity._json(fields)
    return raw, c.content_id("deltareduce.008.seed-transcript.v1", raw), evidence
