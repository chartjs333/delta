---------------------- MODULE DeltaReduceArithmetic ----------------------
EXTENDS Integers, FiniteSets, Sequences

CONSTANT NativeArithmeticInputs

\* Concrete finite profiles, not expected-output oracles. Production profiles
\* instantiate the same operations with their independently bound input bytes.
\* This finite model has one coordinate per shard and a uniform ticket scalar;
\* it does not establish arbitrary-vector/width safety without the Lean layer.
ZeroArithmeticInputs ==
    [q |-> 0, weightN |-> 1, weightD |-> 1, denominator |-> 1,
     qN |-> 1, qD |-> 1, applyN |-> 1, applyD |-> 1,
     model |-> 0, optimizer |-> 0,
     muN |-> 1, muD |-> 2, lrN |-> 1, lrD |-> 2,
     wdN |-> 0, wdD |-> 1, limit |-> 127]

NonzeroArithmeticInputs ==
    [ZeroArithmeticInputs EXCEPT !.q = 1, !.qD = 2,
                                  !.model = 20, !.optimizer = 2]

ABRound(n, d) ==
    LET q == n \div d
        r == n % d
    IN IF r < d - r THEN q ELSE q + 1

ABInRange(value) ==
    /\ value \in Int
    /\ -NativeArithmeticInputs.limit - 1 <= value
    /\ value <= NativeArithmeticInputs.limit

ABInputsValid ==
    /\ NativeArithmeticInputs \in
        [q : Int, weightN : Nat, weightD : Nat \ {0},
         denominator : Nat \ {0}, qN : Nat \ {0}, qD : Nat \ {0},
         applyN : Nat \ {0}, applyD : Nat \ {0},
         model : Int, optimizer : Int,
         muN : Nat, muD : Nat \ {0}, lrN : Nat, lrD : Nat \ {0},
         wdN : Nat, wdD : Nat \ {0}, limit : Nat \ {0}]
    /\ NativeArithmeticInputs.denominator % NativeArithmeticInputs.weightD = 0

ABCoefficient == NativeArithmeticInputs.weightN *
    (NativeArithmeticInputs.denominator \div NativeArithmeticInputs.weightD)

ABParameter(count) == count * (ABCoefficient * NativeArithmeticInputs.q)

ABParameterChecked(count) ==
    /\ ABInRange(ABCoefficient)
    /\ ABInRange(count * ABCoefficient)
    /\ ABInRange(ABCoefficient * NativeArithmeticInputs.q)
    /\ ABInRange(ABParameter(count))

ABConversionNumerator(n) == (n * NativeArithmeticInputs.qN) * NativeArithmeticInputs.applyD
ABConversionDenominator ==
    (NativeArithmeticInputs.denominator * NativeArithmeticInputs.qD) * NativeArithmeticInputs.applyN
ABDomain(n) == ABRound(ABConversionNumerator(n), ABConversionDenominator)
ABDomainChecked(n) ==
    /\ ABInRange(n * NativeArithmeticInputs.qN)
    /\ ABInRange(ABConversionNumerator(n))
    /\ ABInRange(NativeArithmeticInputs.denominator * NativeArithmeticInputs.qD)
    /\ ABInRange(ABConversionDenominator)
    /\ ABInRange(ABDomain(n))

RECURSIVE ABSum(_, _)
ABSum(keys, values) ==
    IF keys = {} THEN 0
    ELSE LET key == CHOOSE element \in keys : TRUE
         IN values[key] + ABSum(keys \ {key}, values)

ABApply(g) ==
    LET p == NativeArithmeticInputs
        mProduct == p.optimizer * p.muN
        m == ABRound(mProduct, p.muD) + g
        directionProduct == m * p.muN
        direction == ABRound(directionProduct, p.muD) + g
        decayProduct == p.model * p.wdN
        decay == ABRound(decayProduct, p.wdD)
        stepInput == direction + decay
        stepProduct == stepInput * p.lrN
        step == ABRound(stepProduct, p.lrD)
        model == p.model - step
    IN [model |-> model, optimizer |-> m,
        intermediates |-> <<mProduct, m, directionProduct, direction,
                            decayProduct, decay, stepInput, stepProduct, step, model>>]

ABApplyChecked(g) ==
    /\ ABInRange(g)
    /\ \A i \in DOMAIN ABApply(g).intermediates :
        ABInRange(ABApply(g).intermediates[i])

=============================================================================
