------------------------ MODULE DeltaReduceMutants ------------------------
EXTENDS Integers

CONSTANTS MutantId, RequiredKeyCount, AccumulatorBound

VARIABLES stage,
          durableVote, messageSent,
          commitmentCount,
          inputFrozen, inputVersion,
          seedExists, seedHasISC,
          apcExists, apcHasParent,
          shardQCExists, shardHasParent,
          aggregateExists, aggregateKeyCount,
          arithmeticAccepted, arithmeticChecked, accumulatorValue,
          currentChanged, applyQCExists,
          publishedKind

vars == <<stage, durableVote, messageSent, commitmentCount,
          inputFrozen, inputVersion, seedExists, seedHasISC,
          apcExists, apcHasParent, shardQCExists, shardHasParent,
          aggregateExists, aggregateKeyCount, arithmeticAccepted,
          arithmeticChecked, accumulatorValue, currentChanged,
          applyQCExists, publishedKind>>

Init ==
    /\ stage = 0
    /\ durableVote = FALSE
    /\ messageSent = FALSE
    /\ commitmentCount = 0
    /\ inputFrozen = TRUE
    /\ inputVersion = 0
    /\ seedExists = FALSE
    /\ seedHasISC = TRUE
    /\ apcExists = FALSE
    /\ apcHasParent = TRUE
    /\ shardQCExists = FALSE
    /\ shardHasParent = TRUE
    /\ aggregateExists = FALSE
    /\ aggregateKeyCount = RequiredKeyCount
    /\ arithmeticAccepted = FALSE
    /\ arithmeticChecked = TRUE
    /\ accumulatorValue = 0
    /\ currentChanged = FALSE
    /\ applyQCExists = TRUE
    /\ publishedKind = "NONE"

MutantStep ==
    /\ stage = 0
    /\ stage' = 1
    /\ durableVote' = durableVote
    /\ messageSent' =
        IF MutantId = "MUT-MISSING-DURABLE-VOTE" THEN TRUE ELSE messageSent
    /\ commitmentCount' =
        IF MutantId = "MUT-DUPLICATE-COMMITMENT" THEN 2 ELSE commitmentCount
    /\ inputFrozen' = inputFrozen
    /\ inputVersion' =
        IF MutantId = "MUT-MUTABLE-ISC" THEN 1 ELSE inputVersion
    /\ seedExists' =
        IF MutantId = "MUT-EARLY-SEED" THEN TRUE ELSE seedExists
    /\ seedHasISC' =
        IF MutantId = "MUT-EARLY-SEED" THEN FALSE ELSE seedHasISC
    /\ apcExists' =
        IF MutantId = "MUT-MISSING-APC-PARENT" THEN TRUE ELSE apcExists
    /\ apcHasParent' =
        IF MutantId = "MUT-MISSING-APC-PARENT" THEN FALSE ELSE apcHasParent
    /\ shardQCExists' =
        IF MutantId = "MUT-MISSING-SHARD-PARENT" THEN TRUE ELSE shardQCExists
    /\ shardHasParent' =
        IF MutantId = "MUT-MISSING-SHARD-PARENT" THEN FALSE ELSE shardHasParent
    /\ aggregateExists' =
        IF MutantId = "MUT-INCOMPLETE-AGGREGATE" THEN TRUE ELSE aggregateExists
    /\ aggregateKeyCount' =
        IF MutantId = "MUT-INCOMPLETE-AGGREGATE"
        THEN RequiredKeyCount - 1 ELSE aggregateKeyCount
    /\ arithmeticAccepted' =
        IF MutantId = "MUT-UNCHECKED-OVERFLOW" THEN TRUE ELSE arithmeticAccepted
    /\ arithmeticChecked' =
        IF MutantId = "MUT-UNCHECKED-OVERFLOW" THEN FALSE ELSE arithmeticChecked
    /\ accumulatorValue' =
        IF MutantId = "MUT-UNCHECKED-OVERFLOW"
        THEN AccumulatorBound + 1 ELSE accumulatorValue
    /\ currentChanged' =
        IF MutantId = "MUT-CURRENT-WITHOUT-APPLYQC" THEN TRUE ELSE currentChanged
    /\ applyQCExists' =
        IF MutantId = "MUT-CURRENT-WITHOUT-APPLYQC" THEN FALSE ELSE applyQCExists
    /\ publishedKind' =
        IF MutantId = "MUT-PARTIAL-PUBLICATION"
        THEN "PARAMETER_PARTIAL" ELSE publishedKind

Next == MutantStep
Spec == Init /\ [][Next]_vars

PersistBeforeSend == messageSent => durableVote
CommitUniqueness == commitmentCount <= 1
ISCImmutability == inputFrozen => inputVersion = 0
SeedAfterInputFreeze == seedExists => seedHasISC
APCParentage == apcExists => apcHasParent
ShardViewAtomicity == shardQCExists => shardHasParent
AggregateCompleteness == aggregateExists => aggregateKeyCount = RequiredKeyCount
NoOverflow == arithmeticAccepted =>
    arithmeticChecked /\ -AccumulatorBound <= accumulatorValue
                      /\ accumulatorValue <= AccumulatorBound
CurrentCertified == currentChanged => applyQCExists
PlaneSeparation == publishedKind \notin
    {"WORKER_COMMITMENT", "AVAILABILITY_FRAGMENT", "PARAMETER_PARTIAL"}

=============================================================================
