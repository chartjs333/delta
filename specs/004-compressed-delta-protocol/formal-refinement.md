# Formal Proof/Refinement Obligations: 004 Fixed-Point Delta Protocol

This file is normative for `004-compressed-delta-protocol`.

## Formal baseline dependency

The branch MUST bind the compatible `formal_semantics_id` and the theorem artifacts PO-A1, PO-A2 and PO-A3 from `000-formal-tla-spec`. A profile is not safe merely because boundary tests pass.

## Concrete proof instantiation

For every accepted `FixedPointProfile`, configuration validation MUST generate content-addressed evidence establishing:

- signed q range `Q` and coefficient range/headroom `A`;
- maximum eligible term count `Nmax`;
- intermediate multiplication width;
- incremental/final accumulator width `M`;
- common denominator and canonical reduction/rounding rules;
- inequality/preconditions required by the machine-checked accumulator theorem;
- profile/schema/config hashes covered by the proof instance.

A change to scale table, q range, coefficient envelope, shard coverage or count invalidates the instance.

## Trace refinement

Implementation traces must project profile validation, q-shard verification, checked add/multiply, unsafe-config rejection and runtime-overflow abort. The checker must reject any trace that converts accepted q values to floating point for consensus, silently saturates/wraps or finalizes a result after a failed bound.

## Exit evidence

1. theorem project/build hash and exact theorem IDs;
2. accepted maximum-safe and rejected first-unsafe concrete instances;
3. direct q-stream implementation traces accepted by the formal checker;
4. unchecked-overflow mutant still produces its expected counterexample;
5. no float consensus codec path exists.

Any arithmetic semantic change returns to branch 000 before implementation.
