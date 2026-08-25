# ADR-0002: Freeze canonical rational reduction and rounding

**Status**: Accepted  
**Date**: 2026-08-25  
**Decision owners**: project specification authority

## Context

ADR-0001 requires deterministic fixed-point consensus arithmetic, but did not
fully specify rational normalization and the exact half-tie rule. A numerator
bound alone cannot guarantee that independent validators serialize and apply
the same rational result.

## Decision

Every consensus rational input is represented by a positive denominator and a
numerator/denominator pair reduced to coprime form. A common denominator is a
positive common multiple of every input denominator, and numerator accumulation
must pass the declared signed-width bound before semantic use.

Final integer conversion uses Euclidean quotient and nonnegative remainder.
Values strictly below half remain at the quotient; values at or above half use
the quotient plus one. Exact half ties therefore resolve toward positive
infinity. This rule applies uniformly to positive and negative numerators and is
part of the content-addressed arithmetic profile.

## Consequences

- Independent implementations have one bit-exact reduction and rounding rule.
- Denominator positivity, coprimality, common-denominator divisibility,
  numerator headroom and each rounding branch are separate proof obligations.
- Changing reduction form or the half-tie direction is a protocol semantic
  change requiring a new ADR, updated proofs/fixtures and a new Formal GO.

