# Local round contract

Feature 002 executes one immutable `DomainPureWorkTicket` inside the Python worker. It does not
participate in validator consensus, open validator sockets, quantize a contribution or publish a
worker-local tensor through the distribution plane.

## Immutable inputs

The canonical ticket binds the ticket and domain IDs, exact data artifact and half-open cursor
range, batch budget `B`, optimizer-step budget `H`, parent model, parameter schema, optimizer
profile, arithmetic profile, deterministic seed and logical deadline. The ticket fingerprint is
the SHA-256 content ID of its canonical JSON bytes.

The optimizer profile is derived from integer AdamW fields. The arithmetic profile transitively
binds tokenizer content, model dimensions, device/dtype, gradient accumulation and integer
micro-unit norm ceilings. Parent, data and tokenizer bytes are hash-verified before training
resources are allocated. Reusing one `ticket_id` with any different binding fails closed.

## Accounting boundary

`A_j` counts successful optimizer updates, not backward calls or microbatches. Sampler cursor and
non-padding tokens are staged during gradient accumulation and committed only after the AdamW
update succeeds. A cancellation, deadline, OOM, data exhaustion or numeric failure during a
partial accumulation discards staged cursor/token accounting.

An eligible result requires the exact equality:

```text
A_j = H
```

Adaptive `H_i`, speed weighting, partial-ticket eligibility and post-claim budget mutation are
not supported.

## Delta sign and normalization

Canonical schema-owner tensors are projected to contiguous CPU FP32 in lexicographic parameter
order. Tied aliases are explicit and never duplicated. Frozen parameters follow the schema's
omission policy.

```text
LocalDelta = parent - final
final      = parent - LocalDelta
NormalizedContributionCandidate = LocalDelta / A_j
```

`LocalDelta` is an internal reconstruction/reference artifact and is never commit-eligible.
Only the normalized FP32 safetensors artifact may be referenced by a candidate, and only after
exact tensor-set/order/shape/dtype checks, a full finite scan, configured per-tensor/global norm
checks and `A_j=H`.

## Publication and recovery

Tensor objects are staged by content ID. The immutable completion is written before the candidate
manifest; the candidate manifest is the final commit point. An incomplete outcome contains a
terminal completion with no `LocalDelta` reference and no candidate manifest. Orphaned staged
tensor objects are not eligible outputs.

Claims and outcomes are atomically persisted by `ticket_id`. Exact replay returns the original
canonical outcome. Conflicting reuse and concurrent in-flight execution are rejected. Recovery of
an orphaned exact claim is explicit (`--recover-incomplete`) and never changes the ticket
fingerprint.

## CLI

```text
delta worker run-ticket TICKET CONFIG PARAMETER_SCHEMA TOKENIZER_REF \
  --store-root ARTIFACT_ROOT --worker-id WORKER_ID
```

All JSON manifests are canonical and all tensor payloads use safetensors. Pickle and Python
memory-layout serialization are forbidden. `configs/worker/smoke-ticket.json` is the deterministic
ticket vector. Its parent is the canonical all-zero FP32 safetensors state defined by the frozen
parameter schema; this avoids binding the protocol fixture to platform-specific normal-distribution
implementations while retaining one exact parent content ID.

## Formal boundary

This feature is a worker-local refinement of the accepted formal baseline
`sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
Its compatibility analyzer checks binding and absence of formal-source drift. It is not a new
claim of full semantic completeness and does not replace the feature-000 TLC, Lean, mutation,
refinement or independent human-review evidence.
