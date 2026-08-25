# Formal Refinement Obligations: 005 Certified P2P Distribution

This file is normative for `005-content-addressed-p2p-distribution`.

## Formal scope

The branch refines `PublishCertifiedObject`, artifact loss/repair and plane-separation behavior from the 000 baseline. Discovery and piece scheduling are non-authoritative implementation details and may stutter in the abstract model unless they change verified artifact availability.

## Required properties

- Only allowlisted global objects with the required finalized certificate lineage may become published/usable.
- Worker q-shards, commitments, AC fragments and regional/parameter partials never enter `publishedObjects`.
- Repair restores the exact original content ID; it cannot replace bytes, commitment, ISC or certificate lineage.
- Initial seed loss or incomplete peer union may block distribution, but cannot revoke/rewrite ApplyQC or current checkpoint.
- Duplicate/reordered/corrupt piece messages are idempotently rejected/ignored and cannot alter trusted manifest identity.
- Certification downgrade never maps to a legal publication transition.

## Refinement evidence

1. Legal publish, multi-peer repair and seed-loss traces accepted.
2. Local/partial publication, wrong policy, altered content and certificate downgrade traces rejected.
3. Current state unchanged under distribution unavailability.
4. The 000 plane-separation and current-certification mutants remain detectable.
5. Formal-impact report binds the exact certification-policy registry and semantics ID.
