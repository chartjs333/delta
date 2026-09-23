# Arithmetic binding proposal: no formal authority

These files make amendment `0001-arithmetic-input-binding.md` reviewable as
concrete arithmetic and negative design vectors. They are not a production
artifact parser, TLA refinement, theorem proof, runtime implementation or new
FormalVerificationReport. `DRAFT_NOT_AUTHORITY` and `formal_go=false` are explicit
in the generated vector document.

```text
python -m unittest discover -s formal/proposals -v
python formal/proposals/arithmetic_binding.py
```

The first candidate has 13 tests for positive/negative half ties, non-ties,
weighted accumulation, conversion quantum, overflow before cancellation, unsafe
prefixes, missing/reordered tickets, noncanonical fractions, substituted parent
model/optimizer/schema and domain-separated value bytes. The matched candidate is
`model=[16,-18]`, `optimizer=[5,-4]` for the checked-in vector.

The native authority arguments in this mathematical reference must ultimately be
resolved from native durable state. Passing both a candidate and its claimed
authority from one untrusted command would not establish binding. This proposal
does not implement that resolver.

Self-review found two material migration issues:

- Per-domain rounding before mixture changes results relative to mixing exact
  rationals first. The tested counterexample is `1/2` and `-1/2` with equal
  weights. The chosen operation order needs a new formal authority.
- The reference accepts the full signed minimum when the exact result fits.
  The current C++ `round_half_toward_positive` rejects `INT64_MIN / 1` because it
  first bounds the unsigned quotient by `INT64_MAX`. The output-range contract
  must be settled in the formal profile before any native modification.

The accepted semantic input set is unchanged by this proposal. Its independently
recomputed ID remains `sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6`.
That fact is **not** evidence that this proposed arithmetic binding has GO. No
accepted TLA/schema/proof was changed, no accepted report was regenerated and no
independent review was fabricated.

Next work remains the production model/schema/refinement integration, arithmetic
proof instantiations, production mutants, cross-language vectors, full pinned
gate/reproduction and a newly reviewed merged authority. PR50's PARAMETER/APPLY
guard must remain until those obligations pass.
