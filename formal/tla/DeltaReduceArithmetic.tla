---------------------- MODULE DeltaReduceArithmetic ----------------------
EXTENDS Integers, FiniteSets, Sequences, TLC

CONSTANTS NativeArithmeticInputs, Tickets, Domains, Shards

\* One coordinate per shard. Immutable inputs differ by ticket/domain/shard.
\* Explicit orders abstract the canonical ordering; byte decoding is unproved.
ABOrder(keys) == CHOOSE order \in [1..Cardinality(keys) -> keys] :
    {order[i] : i \in 1..Cardinality(keys)} = keys
ABSequenceSet(order) == {order[i] : i \in DOMAIN order}
ABIsOrder(order, keys) ==
    /\ order \in Seq(keys)
    /\ Len(order) = Cardinality(keys)
    /\ ABSequenceSet(order) = keys

ZeroArithmeticInputs ==
    [ticketOrder |-> ABOrder(Tickets), domainOrder |-> ABOrder(Domains),
     ticketDomain |-> [ticket \in Tickets |-> CHOOSE domain \in Domains : TRUE],
     q |-> [ticket \in Tickets |-> [shard \in Shards |-> 0]],
     weightN |-> [ticket \in Tickets |-> 1], weightD |-> [ticket \in Tickets |-> 1],
     denominator |-> [domain \in Domains |-> 1],
     qN |-> [domain \in Domains |-> [shard \in Shards |-> 1]],
     qD |-> [domain \in Domains |-> [shard \in Shards |-> 1]],
     piN |-> [domain \in Domains |-> 1],
     piD |-> [domain \in Domains |-> Cardinality(Domains)],
     mixtureD |-> Cardinality(Domains), applyN |-> 1, applyD |-> 1,
     model |-> [shard \in Shards |-> 0], optimizer |-> [shard \in Shards |-> 0],
     muN |-> 1, muD |-> 2, lrN |-> 1, lrD |-> 2,
     wdN |-> 0, wdD |-> 1, limit |-> 127]

NonzeroArithmeticInputs ==
    [ZeroArithmeticInputs EXCEPT
        !.q = [ticket \in Tickets |-> [shard \in Shards |-> 1]],
        !.qD = [domain \in Domains |-> [shard \in Shards |-> 2]],
        !.model = [shard \in Shards |-> 20],
        !.optimizer = [shard \in Shards |-> 2]]

ABRound(n, d) ==
    LET q == n \div d
        r == n % d
    IN IF r < d - r THEN q ELSE q + 1

ABInRange(value) ==
    /\ value \in Int
    /\ -NativeArithmeticInputs.limit - 1 <= value
    /\ value <= NativeArithmeticInputs.limit

RECURSIVE ABPrefix(_, _)
ABPrefix(values, count) ==
    IF count = 0 THEN 0 ELSE ABPrefix(values, count - 1) + values[count]
ABTotal(values) == ABPrefix(TLCEval(values), Len(values))
ABCheckedSequence(values) ==
    /\ \A index \in DOMAIN values : ABInRange(values[index])
    /\ \A count \in 0..Len(values) : ABInRange(ABPrefix(TLCEval(values), count))

RECURSIVE ABGcd(_, _), ABLcmPrefix(_, _)
ABGcd(a, b) == IF b = 0 THEN a ELSE ABGcd(b, a % b)
ABLcmPrefix(values, count) ==
    IF count = 0 THEN 1
    ELSE LET previous == ABLcmPrefix(values, count - 1)
         IN (previous \div ABGcd(previous, values[count])) * values[count]

ABInputsValid ==
    LET p == NativeArithmeticInputs
    IN /\ p \in
        [ticketOrder : Seq(Tickets), domainOrder : Seq(Domains),
         ticketDomain : [Tickets -> Domains], q : [Tickets -> [Shards -> Int]],
         weightN : [Tickets -> Nat], weightD : [Tickets -> Nat \ {0}],
         denominator : [Domains -> Nat \ {0}],
         qN : [Domains -> [Shards -> Nat \ {0}]],
         qD : [Domains -> [Shards -> Nat \ {0}]],
         piN : [Domains -> Nat], piD : [Domains -> Nat \ {0}],
         mixtureD : Nat \ {0}, applyN : Nat \ {0}, applyD : Nat \ {0},
         model : [Shards -> Int], optimizer : [Shards -> Int],
         muN : Nat, muD : Nat \ {0}, lrN : Nat, lrD : Nat \ {0},
         wdN : Nat, wdD : Nat \ {0}, limit : Nat \ {0}]
       /\ ABIsOrder(p.ticketOrder, Tickets)
       /\ ABIsOrder(p.domainOrder, Domains)
       /\ \A ticket \in Tickets :
            /\ ABGcd(p.weightN[ticket], p.weightD[ticket]) = 1
            /\ \A shard \in Shards : ABInRange(p.q[ticket][shard])
       /\ \A ticket \in Tickets : p.denominator[p.ticketDomain[ticket]] % p.weightD[ticket] = 0
       /\ \A domain \in Domains :
            /\ p.mixtureD % p.piD[domain] = 0
            /\ ABGcd(p.piN[domain], p.piD[domain]) = 1
            /\ \A shard \in Shards : ABGcd(p.qN[domain][shard], p.qD[domain][shard]) = 1
       /\ p.mixtureD = ABLcmPrefix([i \in DOMAIN p.domainOrder |-> p.piD[p.domainOrder[i]]], Len(p.domainOrder))
       /\ ABGcd(p.applyN, p.applyD) = 1
       /\ ABGcd(p.muN, p.muD) = 1
       /\ ABGcd(p.lrN, p.lrD) = 1
       /\ ABGcd(p.wdN, p.wdD) = 1
       /\ ABTotal([i \in DOMAIN p.domainOrder |->
            p.piN[p.domainOrder[i]] * (p.mixtureD \div p.piD[p.domainOrder[i]])]) = p.mixtureD
       /\ \A shard \in Shards : ABInRange(p.model[shard]) /\ ABInRange(p.optimizer[shard])

ABMembers(members) == SelectSeq(NativeArithmeticInputs.ticketOrder, LAMBDA ticket : ticket \in members)
ABCoefficients(members, domain) ==
    LET p == NativeArithmeticInputs
        order == ABMembers(members)
    IN TLCEval([i \in DOMAIN order |-> p.weightN[order[i]] * (p.denominator[domain] \div p.weightD[order[i]])])
ABProducts(members, domain, shard) ==
    LET order == ABMembers(members)
        coefficients == ABCoefficients(members, domain)
    IN TLCEval([i \in DOMAIN order |-> coefficients[i] * NativeArithmeticInputs.q[order[i]][shard]])
ABParameter(members, domain, shard) == ABTotal(ABProducts(members, domain, shard))
ABParameterChecked(members, domain, shard) ==
    /\ members \subseteq Tickets
    /\ \A ticket \in members : NativeArithmeticInputs.ticketDomain[ticket] = domain
    /\ ABCheckedSequence(ABCoefficients(members, domain))
    /\ ABCheckedSequence(ABProducts(members, domain, shard))

ABConversionNumerator(n, domain, shard) ==
    (n * NativeArithmeticInputs.qN[domain][shard]) * NativeArithmeticInputs.applyD
ABConversionDenominator(domain, shard) ==
    (NativeArithmeticInputs.denominator[domain] * NativeArithmeticInputs.qD[domain][shard]) * NativeArithmeticInputs.applyN
ABDomain(n, domain, shard) ==
    ABRound(ABConversionNumerator(n, domain, shard), ABConversionDenominator(domain, shard))
ABDomainChecked(n, domain, shard) ==
    /\ ABInRange(n * NativeArithmeticInputs.qN[domain][shard])
    /\ ABInRange(ABConversionNumerator(n, domain, shard))
    /\ ABInRange(NativeArithmeticInputs.denominator[domain] * NativeArithmeticInputs.qD[domain][shard])
    /\ ABInRange(ABConversionDenominator(domain, shard))
    /\ ABInRange(ABDomain(n, domain, shard))

ABMixtureFirstProducts(values) ==
    LET p == NativeArithmeticInputs
    IN TLCEval([i \in DOMAIN p.domainOrder |-> p.piN[p.domainOrder[i]] * values[p.domainOrder[i]]])
ABMixtureProducts(values) ==
    LET p == NativeArithmeticInputs
        first == ABMixtureFirstProducts(values)
    IN TLCEval([i \in DOMAIN p.domainOrder |-> first[i] * (p.mixtureD \div p.piD[p.domainOrder[i]])])
ABMixture(values) == ABRound(ABTotal(ABMixtureProducts(values)), NativeArithmeticInputs.mixtureD)
ABMixtureChecked(values) ==
    /\ \A i \in DOMAIN ABMixtureFirstProducts(values) : ABInRange(ABMixtureFirstProducts(values)[i])
    /\ ABCheckedSequence(ABMixtureProducts(values))
    /\ ABInRange(NativeArithmeticInputs.mixtureD)
    /\ ABInRange(ABMixture(values))

ABApplyEvaluated(g, shard) ==
    LET p == NativeArithmeticInputs
        mProduct == p.optimizer[shard] * p.muN
        m == ABRound(mProduct, p.muD) + g
        directionProduct == m * p.muN
        direction == ABRound(directionProduct, p.muD) + g
        decayProduct == p.model[shard] * p.wdN
        decay == ABRound(decayProduct, p.wdD)
        stepInput == direction + decay
        stepProduct == stepInput * p.lrN
        step == ABRound(stepProduct, p.lrD)
        model == p.model[shard] - step
    IN [model |-> model, optimizer |-> m,
        intermediates |-> <<mProduct, m, directionProduct, direction,
                            decayProduct, decay, stepInput, stepProduct, step, model>>]

\* Singleton function application binds the already evaluated integer gradient.
\* TLA identity: [value \in {g} |-> F(value)][g] = F(g). TLC's ENABLED
\* expansion otherwise repeatedly evaluates the complete arithmetic lineage.
ABApply(g, shard) ==
    [value \in {g} |-> ABApplyEvaluated(value, shard)][g]

\* The sole record is checked coordinate by coordinate exactly as before;
\* binding it once avoids recalculating all intermediates for each index.
ABApplyChecked(g, shard) ==
    /\ ABInRange(g)
    /\ \A result \in {ABApply(g, shard)} :
        \A i \in DOMAIN result.intermediates : ABInRange(result.intermediates[i])

=============================================================================
