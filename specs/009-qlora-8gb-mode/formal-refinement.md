# Formal Refinement Obligations: 009 Certified QLoRA Mode

This file is normative for `009-qlora-8gb-mode`.

**Classification**: `REFINEMENT_ONLY`
**Formal semantics ID**: `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`
**Semantic completeness claimed**: `false`

QLoRA changes concrete worker/model artifacts, not the abstract certificate/failure semantics. The branch MUST reuse the compatible 000/008 formal semantics without adding a coordinator, partial-ticket path or alternate apply transition.

## Abstraction rules

- immutable base/tokenizer/quantization/adapter-schema hashes are part of the formal RoundConfig/ticket/certificate context;
- only complete `A_j=H` adapter tickets may map to `CommitTicket`;
- adapter q-shards map to the existing integer contribution abstraction;
- base parameters/buffers never appear in contribution, parameter coverage, outer optimizer or current adapter state;
- AggregateRootQC/ApplyQC/current actions are the same abstract actions as 008, specialized to adapter schema and immutable base fingerprint;
- OOM, cancellation, incomplete ticket or base mutation produce rejection/abort evidence and no commitment/current transition.

## Closed certificate graph

The only permitted lineage is the existing feature-008 graph:

`ISC → SeedTranscript → EC → APC → ParameterShardQC → AggregateRootQC → ApplyQC → current pointer`.

`QLoRAInputSetCertificate`, `QLoRAAggregateRootQC`, `QLoRAApplyQC` and equivalent parallel
certificate types are forbidden. A new protocol-visible state, action, failure terminal, durability
outcome or partial-apply transition is `SEMANTIC`; implementation stops and returns to feature 000.

## Required evidence

1. Legal complete adapter certificate/apply trace accepted.
2. Partial ticket, mismatched base/schema/mode, base tensor injection/mutation and current-without-ApplyQC traces rejected.
3. Four-validator adapter ApplyQC trace satisfies Apply uniqueness and parent preservation.
4. Crash/replay and base-cache/P2P behavior do not change abstract certified state semantics.
5. Formal semantics ID remains unchanged or a new branch-000 GO is obtained.
