# ADR-0011 / B — impact estimate без реализации

**Дата:** 28 сентября 2026. **Статус:** ESTIMATE ONLY / IMPLEMENTATION NOT AUTHORIZED.
Пользователь принял ADR-0011 как архитектурную развилку, запросил оценку B,
но не разрешил реализацию. Проверяемая исходная точка:
`076d6cddd5ad67b53d267847f1fbdc2eb278d791`; proof checkpoint:
`c666f62b4989fb1fd0306a2af7e02ccc6e649427`.
Tasks T044/T047/T053–T057. R1 CLOSED; R2/R3 OPEN. DoD R1–R7 неизменен.

## Решение, для которого дана оценка

B сохраняет один исходный vector shard/vote/certificate и его полные bytes,
context, parents и положение в manifest. `πₖ` — чтение координаты этого объекта,
а не создание нового объекта протокола. Исходные пять shards 4/8/8/8/8 остаются
пятью shards. Семейство связано с одним исходным событием, одним durable slot,
одним signer set и общим control state. Принятие всего вектора атомарно.

Для отдельного shard индекс удовлетворяет `k < length`. Для полного scalar state
с shards разной длины требуется согласованный выбор координаты **для каждого**
shard, например селектор `σ(s) ∈ Fin(length(s))`, либо эквивалентная композиция
через общий carrier. Одна глобальная `k` не покрывает этот случай без дополнительных
условий. Padding, новые shard IDs и независимый `Next` по координатам исключены.
Это деталь реализации прежнего полного отображения R2, не новое обязательство.

План оценки: старые width-one APIs и доказательства сохраняются; общий bridge
использует family-aware входы и композицию. Сначала полное покрытие/совместная
инъективность и source/body/state correspondence (R2), затем preservation через
существующие действия (R3). Полнота каждой отдельной scalar view не предполагается.

## Четыре ответа

1. **B допускает сохранение protocol semantics и certificate/QC/WAL identity.**
   В описанном плане native wire/runtime не меняются. Исходные signatures, body
   hashes, sequence и effect identity принадлежат целому объекту; projected
   body/root — только formal representation. Однако целостность такого lifting
   ещё не доказана: это план, а не уже полученный результат R2/R3.
   Это сохранение **исходных объектов при отображении**, не обещание одинаковых
   hashes после будущего переписывания version/semantics metadata внутри объекта.
   Например, существующие JSON schemas PARAMETER/APPLY QC фиксируют старый
   `formal_semantics_id`; их будущая migration к новой authority не входит в B/R2.
   Исходные certificates не пересоздаются с новым полем под прежним hash.
2. **Для устранения `length = 1` менять production `DeltaReduce.Init/Next`
   не требуется.** Сохраняем существующие scalar actions как leaf specification;
   меняем refinement/projection layer и формально определяем синхронное lifting.
   Одной правки Python checker недостаточно. Гарантии «весь R2 закроется без
   изменения каких-либо TLA guards» пока нет: прежние ограничения диапазонов
   `ModelLimit`, `ABInRange`, `CheckedParameterValue` требуют отдельного обоснования
   в том же R2. Если его нельзя получить над прежними predicates, это отдельная
   архитектурная контрольная точка, а не разрешение молча поменять production TLA.
3. **Старые теоремы не становятся ложными.** Сохраняется их прежняя область,
   включая width-one и ограниченные модели. После включения B в обязательные
   artifacts старые hashes/aggregate evidence не квалифицируют новый source tree;
   обновляются semantics ID и совместимые R4–R7 evidence. Общего vector/recovery
   результата сейчас нет, поэтому «отменять» уже закрытый R2/R3 нечего.
4. **Остаток R2: 32–56 активных часов. R3 дополнительно: 28–52 часа.**
   Это оценка при успешном representation-only пути B, с детализацией ниже;
   не срок полного GO и не гарантированная верхняя граница.

## Значение статусов

| Статус | Что именно означает |
|---|---|
| `UNCHANGED` | План не требует изменения указанного исходного контракта/bytes. |
| `PROOF REUSE` | Утверждение и доказательство сохраняются с прежними предпосылками; применение в новом bridge ещё нужно связать. |
| `MODIFICATION` | Требуется family-aware контракт/композиция или изменение вызывающего checker. Старый API может остаться legacy; имя нового файла здесь не навязывается. |
| `RE-RUN ONLY` | Исходный сценарий/алгоритм сохраняется; нужна квалификация для нового candidate с точными source/config/tool hashes. Полный gate остаётся R4, не начинается этим отчётом. |
| `INVALIDATED` | Старое evidence нельзя использовать как evidence **для изменённой цели**. Оно остаётся историческим результатом для своих источников. |

В таблицах отдельно указаны исходники и квалификация. `UNCHANGED` для текста
модуля не означает автоматического переноса старого aggregate PASS на новый GO.
Имена ниже — существующие точки изменения/переиспользования; новый обязательный
список модулей, fixtures или R8 этим документом не вводится.

## TLA: точные модули и actions

Все пути этой таблицы относительно `formal/tla/`. Колонка B различает
неизменный production action и изменяемое отображение этого action.

| Существующий модуль / определения | Статус и работа для B |
|---|---|
| `DeltaReduce.tla`: `Init`, `OrdinaryNext`, `EnabledFailureNext`, `Next`, `Spec`, `TypeOK` | `UNCHANGED` в минимальном плане. Новый family carrier обязан соответствовать одному существующему action либо разрешённому stutter; доказательство lifting — `MODIFICATION`, R2/R3. |
| `DeltaReduceTypes.tla`: `ParameterKeys`, `VoteEnvelope`, `VoteRecord`, `ProtocolVariables`, `VoteContexts`, `ModelConstantsOK` | `UNCHANGED` как scalar leaf contract. `ParameterValues ⊆ Int` остаётся; coordinate index не добавляется в vote context или key `(domain, shard)`. |
| `DeltaReduceArithmetic.tla`: `ABInputsValid`, `ABParameter`, `ABParameterChecked`, `ABDomain`, `ABDomainChecked`, `ABMixture`, `ABMixtureChecked`, `ABApplyEvaluated`, `ABApply`, `ABApplyChecked`, `ABInRange` | `PROOF REUSE` формул и checked coordinate interpretation. Связь полного native profile с параметрами/bounds всех views — `MODIFICATION` в R2; пока не утверждается эквивалентность старых guards общей native admission. |
| `DeltaReduceReduceApply.tla`: `NativeArithmeticAuthority`, `NativeParameterValue`, `NativeDomainValue`, `NativeGradient`, `NativeModelHash`, `NativeOptimizerHash`, `NativeApplyChecked`, `CheckedParameterValue`, `ValidParameterArithmetic`, `ValidParameterResultBody`, `ValidApplyArithmetic`, `ValidApplyBody`, `ExactAggregateCoverage` | `UNCHANGED` leaf definitions; `MODIFICATION` их family interpretation/source binding. Structured `NativeModelHash` не становится native crypto ID; complete source и общий checkpoint остаются отдельно связанными. Числовая совместимость — открытая часть R2. |
| Тот же модуль: `ProposeParameterResultAction`, `VoteParameterAction`, `FinalizeParameterQCAction`, `AssembleAggregateRootAction`, `VoteAggregateRootAction`, `FinalizeAggregateRootQCAction`, `ComputeApplyCandidateAction`, `VoteApplyAction`, `FinalizeApplyQCAction`, `AdvanceCurrentCheckpointAction`, `ReplayCurrentAdvanceAction` | `UNCHANGED` production actions; `MODIFICATION` синхронного projection/lifting. PARAMETER/ROOT/APPLY и current остаются одним целым действием, не набором independently admissible coordinate votes. Статическое соответствие — R2, сохранение по шагу — R3. |
| Тот же модуль: `ProposeSubstitutedParameterAuthorityAction`, `ComputeSubstitutedApplyAuthorityAction`, `ComputeWrongApplyResultAction`, `RejectParameterWrongParentAction`, `RejectParameterUncheckedAction`, `RejectParameterOverflowAction`, `RejectConflictingParameterAction`, `RejectIncompleteAggregateAction`, `RejectDuplicateAggregateAction`, `RejectMixedAggregateAction`, `RejectConflictingAggregateAction`, `RejectWrongApplyParentAction`, `RejectUnsafeApplyAction`, `RejectConflictingApplyAction`, `RejectCurrentConflictAction` | `UNCHANGED`; `RE-RUN ONLY` существующих rejection/mutant сценариев. Family checker дополнительно обязан отвергать несогласованные views как нарушение прежнего body/source correspondence, не вводя новую protocol rejection action. |
| Тот же модуль: `CrashAfterApplyQCBeforePointerAction`, `PublishCertifiedObjectAction`, `RejectForbiddenPublicationAction`, `ReduceApplyNext` | `UNCHANGED`; `MODIFICATION` соответствующего общего state/current projection в R3. Нельзя публиковать часть координат. |
| `DeltaReduceQuorums.tla`: `CanPersistVoteEnvelope`, `PersistVoteEnvelopeChanges`, `HasDeliveredVote`, `HasDurableVote`, `HasConflictingDurableVote`, `PersistConfigVoteAction`, `FinalizeRoundConfigAction`, `SendVoteEnvelopeAction`, `DeliverVoteEnvelopeAction`, `VoteTransportNext` | `UNCHANGED`; `PROOF REUSE` правил uniqueness/quorum. Обоснование одного original vote/slot/signer set для семейства — `MODIFICATION` в R2/R3; views не увеличивают quorum power. |
| `DeltaReduceCertificates.tla`: `VoteISCAction`, `FinalizeISCAction`, `GenerateSeedAction`, `VoteECAction`, `FinalizeECAction`, `VoteAPCAction`, `FinalizeAPCAction`, `ReplayMessageAction` | `UNCHANGED`; `PROOF REUSE` certificate/parent facts. General family-to-one certificate correspondence — `MODIFICATION` композиции, не изменение edges или ID. |
| `DeltaReduceFailures.tla`: `CrashBeforePersistAction`, `CrashAfterPersistAction`, `CrashAfterSendAction`, `RestartAction`, `RecoverJournalAction`, `EnqueueMessageAction`, `DeliverMessageAction`, `DropMessageAction`, `DuplicateMessageAction`, `EnablePartitionAction`, `HealPartitionAction`, `SoftTimeoutAction`, `VoteViewChangeAction`, `ViewChangeAction`, `VoteHardAbortAction`, `HardAbortAction`, `FailureNext` | `UNCHANGED` transition semantics; `MODIFICATION` lifting в R3. VIEW/ABORT/current и original journal общие; missing response не превращается в evidence of absence. |
| `DeltaReducePublicState.tla`: `PublicStateFields`, `ProjectedPublicState`, `CompletePublicState`, `MatchesPublicState` | `UNCHANGED` single-view export из 64 полей; `MODIFICATION` внешнего family/export/replay контракта. Старый single-view document не переименовывается в полный vector state. |
| `DeltaReduceRefinement.tla`: `FormalActionIds`, `ActionModule`, `ProjectedAction` | `UNCHANGED` существующие action IDs/dispatch; `MODIFICATION` family replay/lifting, использующего этот dispatch один раз для исходного события. |
| `DeltaReduceAvailability.tla`, `DeltaReduceTickets.tla` | `UNCHANGED` actions и rules; `PROOF REUSE` прежних availability/ticket assumptions. Их наблюдаемое состояние всё равно входит в general relation; B не разрешает считать availability всегда истинной. |

**Существующие harnesses/configurations — `RE-RUN ONLY` для квалификации,
текст сохраняется:** `DeltaReduceConfigHarness`, `DeltaReduceCurrentBindingHarness`
(`BindingInit`, `BindingNext`, `CurrentBindingSpec`, `NoStaleArithmeticVotes`),
`DeltaReduceF1Harness`, `DeltaReduceFixtureInputs`, `DeltaReduceHeterogeneousHarness`,
`DeltaReduceLivenessHarness`, `DeltaReducePartitionHarness`,
`DeltaReducePersistenceHarness` (`PersistenceInit`, `PersistenceNext`,
`PersistenceSpec`, `PersistAdmit`, `PersistAppend`, `PersistBarrier`, `PersistCommit`,
`PersistExpose`, `PersistReplay`, `PersistCrashBefore`, `PersistCrashAfterDurable`,
`PersistCrashAfterCommit`, `PersistCrashAfterExpose`, `PersistAppendLost`,
`PersistAppendSurvived`, `PersistBarrierFailedAbsent`, `PersistBarrierFailedPresent`,
`PersistStopOnError`, `PersistTornAppend`, `PersistRestart`, `PersistRecover`,
`PersistCorruptRecovery`), `DeltaReducePhase6Harness`, `DeltaReduceVoteLifecycleHarness`.

Затронутые квалификацией families в `formal/tla/cfg/`:
`native-arithmetic-binding.cfg`, `native-arithmetic-liveness.cfg`,
`arithmetic-boundary.cfg`, `heterogeneous-{positive,prefix,product,conversion}.cfg`,
`current-binding.cfg`, `current-binding-recovery.cfg`,
`persistence-{parameter,apply}.cfg`, `apply-recovery.cfg`, `vote-crash-recovery.cfg`,
`vote-lifecycle-{config,isc,ec,apc,parameter,aggregate,apply,view,abort}.cfg`.
Остальной существующий manifest safety/liveness также сохраняется, без требования
добавлять конфигурации. Старые bounded TLC результаты не доказывают новый family lifting.

Повторно квалифицируемые существующие assertions включают `ArithmeticBindingSound`,
`NoOverflow`, `ShardViewAtomicity`, `AggregateCompleteness`, `ApplyUniqueness`,
`CurrentCertified`, `RecoveryIdempotence`, `ReduceApplyVoteUniqueness`,
`ReduceApplyQCUniqueness`, `ValidReduceApplyQuorums`, `VoteUniqueness`, `QCUniqueness`,
`RecoveryOrdering`, `AllQCVotesPersisted`, `PersistenceRecordSound`,
`PersistenceRecoverySound`. Их область не расширяется одним перезапуском TLC.

## Lean: существующие definitions/theorems

Пути относительно `formal/proofs/DeltaReduce/`. Указаны конкретные затрагиваемые
entry points и результаты; транзитивный rebuild зависимости не означает переделку
её доказательства. Сохранённые scalar APIs имеют прежний scope.

| Файл и существующие имена | Статус / граница работы |
|---|---|
| `Quorum.lean`: `quorumIntersection`, `quorumIntersectionContainsHonest`, `conflictingQCImpossible`; `FixedPoint.lean`: `everyCanonicalPrefixFits`, `intermediateProductFits`, `commonDenominatorNumeratorSafe`, `canonicalRoundDeterministic`; `Hierarchy.lean`: `exactDomainShardPartition`, `hierarchicalEqualsFlat`, `hierarchicalCoefficientMetadata`, `hierarchicalDenominatorMetadata` | `PROOF REUSE`. Математика и hypotheses прежние; family не создаёт дополнительных validators/tickets. |
| `ParameterKernel.lean`: `checkedParameter`, `checkedParameterSound`, `checkedParameterRowsComplete`, `checkedParameterCoordinateRefines`, `checkedConvertRows`, `checkedConvertRowsSound`, `checkedDomainVector`, `checkedDomainVectorSound`; `ApplyKernel.lean`: `checkedMix`, `checkedMixSound`, `checkedOptimizer`, `checkedOptimizerSound`, `deriveWeightPlan`, `weightPlanLeast`, `deriveApply`, `applyComputationUnique`, `applyComputationShapeAndBounds` | `PROOF REUSE` vector/scalar kernels при исходных bounds, order и shapes. Это основа B, не новый arithmetic algorithm. |
| `ArithmeticBinding.lean` (namespace `NativeBinding`): `deriveParameter`, `DerivedParameter.body`, `derivedParameterBodySound`, `derivedParameterCoordinateRefines`, `nativeParameterConversionSound`, `nativePlacementSound`, `nativeApplyBodyAndBytesUnique`, `nativeApplyOutputBounds`, `nativeApplyResultUnique`, `encodeParameterBody`, `encodeApplyBody`, `encodeVoteContext`, `encodeVoteEnvelope`, `NativePrepared`, `prepareNativeFirst`, `nativePreparedIdentity`, `nativePreparedRecordUnique`, `nativePreparedHashPreimages` | `PROOF REUSE`; native canonical bytes и identity contracts `UNCHANGED`. Новая family должна ссылаться на эти полные original sources. |
| `NativeVectorArithmetic.lean`: `compute`, `reduce`, `reducedFromSources`, `exactOutput`, `coordinateRefines`, `sourceAligned`, `originalCoordinateTerms`, `originalCoordinateRefines`, `noCoordinateFallback` | `PROOF REUSE`. Полный source computation уже содержит координаты. |
| `formal/proposals/vector-shard-representation.lean`: `Source`, `Image`, `Represents`, `represent`, `represents`, `projectExact`, `noCoordinateDefault`, `identityObservablesPreserved`, `noCollapse`, `globalCoordinateExact`, `scalarParameterIsCoordinate`, `scalarConversionIsCoordinate`, `scalarMixtureIsCoordinate`, `scalarOptimizerIsCoordinate`, `applyCoordinateFromSameVector`, `originalResultCoordinate`, `originalScalarResultUnchanged`, `originalWidths`, `originalObjectsRetained`, `originalManifestEntries`, `originalFiveNotThirtySix` | `PROOF REUSE` в доказанной области. Предложение пока вне mandatory inventory; подключение к общему bridge — `MODIFICATION`, а не признание его уже готовым refinement. |
| `NativeScalarProjection.lean`: `Layout`, `layout`, `Projected`, `project`, `projectionRetainsEveryCoordinate`, `projectionInjective`, `Parameter`, `parameter`, `parameterScalarComputedFromNativeRows`, `vectorParameterHasNoScalarProjection`, `Apply`, `applyResult`, `applyRetainsNativeHashPreimages` | `PROOF REUSE` старого width-one API. `MODIFICATION` общего пути вызова: заменить его requirement на полный indexed family, не удалить истинную теорему `vectorParameterHasNoScalarProjection` ради зелёной сборки. |
| `NativeInputProjection.lean`: `ScalarRows`, `scalarRows`, `Block`, `loadBlock`, `Corpus`, `loadCorpus`, `qAt`, `deriveTicket`, `deriveDomain`, `ModelLimit`, `modelLimit`, `Projected`, `projectInputs`, `projectedQHasCanonicalArtifact`, `projectedTicketWeightFromAllShards`, `projectedQuantumFromAssignment`, `projectedDenominatorFromAllAssignments`, `projectedMixtureIsLeastCommonMultiple` | `MODIFICATION` general input contract/callers: actual source row + coordinate, вместо `LoadedRow … 1` / `[value]`; единые weights/Q/quantum/parents; разделить source accumulator/output/input bounds и scalar fixture limit. Source/order facts переиспользуются. |
| `PublicArithmeticInputs.lean`: `Image`, `image`, `Vocabulary`, `qTable`, `currentTable`, `vectorTable`, `Components`, `loadComponents`, `Encoded`, `encodeImage`, `encodeProjected`, `checkProjected`, `checkedWholeInputs`, `encodedRetainsEveryField` | `MODIFICATION` family construction и whole-input binding. `sortEntriesPerm`, `functionPreservesAllPairs` — `PROOF REUSE`. Нельзя оставить finite fixture aliases в качестве общей identity relation. |
| `PublicAuthority.lean`: `Header`, `loadHeader`, `loadEntries`, `Projection`, `project`, `Checked`, `check`, `checkedWholeAuthority`, `exactConstructedParentChain`, `currentTablesFromBoundVectors`, `structuredCurrentValuesShareSchema` | `MODIFICATION` projected tables/authority composition; `headerUsesOriginalAuthority`, `coefficientUsesBothAPCAndPlan`, `allNativeCommitmentsRetained`, `nativeParentEdgesChecked`, `completeNativeParentPayloads` — `PROOF REUSE`. Именованная независимая `MetadataTrust` boundary не заменяется assumed whole-body equality. |
| `PublicParameterBody.lean`: `Narrow`, `narrow`, `resultFits`, `Projection`, `project`, `Projection.fields`, `check`, `fullBodyWasComputed`, `bodyNumberHasBothNativeAndProjectedChecks`, `fullPublicInputsAndNativeRowsShareFrame`, `narrowChecksEveryCoefficientProductAndPrefix` | `MODIFICATION` полного PARAMETER family bridge. Старый body остаётся scalar lemma. `checkedWidthsAgree` — `PROOF REUSE`. Все coordinates и промежуточные checks входят в общий admission result. |
| `PublicApplyArithmetic.lean`: `conversion`, `Converted`, `checkConversion`, `Conversions`, `checkConversions`, `Checked`, `check`; `conversionWidthsAgree`, `optimizerWidthsAgree`, `applyWidthsAgree`, `outputIdentity`, `noCertifiedConversionOmitted` | `MODIFICATION` binding общего profile/bounds; перечисленные cross-width equality/source lemmas — `PROOF REUSE` при их hypotheses. Проверка PARAMETER не подменяет conversion/mix/optimizer checks. |
| `PublicApplyBody.lean`: `Leaves`, `projectLeaves`, `Projection`, `project`, `check`, `wholeApplyWasComputed`, `completeLeafCount`, `fullNativeCertifiedBodies`, `everyPublicLeafHasOriginalSource`, `aggregatePreservesLeafSet`, `nextValuesFromActualNativeOutputs` | `MODIFICATION` общего leaf/aggregate/APPLY представления; без размножения certificate leaves по координатам. `Checkpoint`, `checkCheckpoint`, `checkpointUsesComputedModelHash`, `noAssumedCheckpointName` — `PROOF REUSE` прежней условной native identity boundary, не доказательство нового frozen checkpoint contract. |
| `PublicRootBody.lean`: `Projection`, `project`, `check`, `wholeBody`, `nativeLeafCount`, `nativeLeafAt`, `originalScalarAt`; `PublicRootParents.lean`: `Checked`, `check`, `completeBodyParents`, `actualCommitmentAt`; `PublicRootHistory.lean`: `Checked`, `check`, `completeVote`, `completeContext`, `fromHistory` | `MODIFICATION` family body/parents/history composition. `PublicRootBody.originalVoteIdentity` и `PublicRootHistory.nativeIdentity` / `originalSequences` — `PROOF REUSE` original-source facts. |
| `PublicRootEnvelope.lean`: `envelope`, `value`, `Checked`, `check`, `entireVote`, `fullApcContext`, `contextFromBody`, `actorSource`, `nativeIdentity`, `wholeCanonical`; `PublicParentNames.lean`: `entriesAgree`, `completeEntries`, `membersAgree`, `completeMembers` | `MODIFICATION` family consumers полного ROOT body; `PROOF REUSE` original actor/context/identity и primitive parent-name agreement при согласованном общем vocabulary. Generic envelope не меняет число votes. |
| `PublicParameterJoin.lean`, `PublicApplyJoin.lean`: `Body`, `loadBody`, `SourceBody`, `loadSourceBody`, `Joined`, `bindVote`, `joinedOriginalPreparation`, `joinedCompleteAfterFootprint`, `joinedOriginalSequence` | `MODIFICATION` R2 общего body-to-one-vote join. `Executed`, `executeKnown`, `checkedBodyPersistencePreservesReachability`, `unknownHasNoCompleteState` сохраняют legacy scope; family preservation — `MODIFICATION` R3. |
| `PublicScalarNumbers.lean`: `VectorValue`, `checkVectorValue`, `ApplyNumbers`, `checkApplyNumbers`, `checkedApplyAllNativeCoordinates`, `checkedOptimizerAllNativeCoordinates`, `ParameterNumber`, `checkParameterNumber`, `SourceNumbers`, `checkSourceNumbers`, `bindCheckedNumbers`, `bindVoteNumbers`, `executeKnownNumbers`, `numericExecutionPreservesReachability` | `PROOF REUSE` numeric-only/legacy checks; `MODIFICATION` потребителя общего family bridge. Numeric-only результат не становится достаточным full body gate. |
| `PublicEarlyBody.lean`: `project`, `check`; `PublicPlanningBody.lean`: `loadEcBody`, `loadApcBody`, `project`, `check`, `nativeParentsRetained`, `differentPlanParentsReject`; `PublicEarlyHistory.lean`, `PublicPlanningHistory.lean`, `PublicFailureHistory.lean`: `Checked`, `check`, `exactNativeSource`, `exactOriginalBytes`, `completePublicVote`, `wrongPriorRejects` | `PROOF REUSE` в существующих named-metadata/parent scopes. `MODIFICATION` общей all-kind/state композиции R2: согласовать источники/aliases и убрать необоснованное сужение общего domain, не переписывать native non-arithmetic payloads. |
| `PublicFailureBody.lean`: `EmptyLineage`, `loadAbortBody`, `nonemptyLineageRejects`; `NativeAbortLineage.lean`: `exactSevenLists`, `exactCurrentLineage`, `acceptedApplyAbsence`, `originalConfigIds`; `PublicAbortAncestors.lean`: `project`, `originalSevenLists`, `arithmeticPayloadsRetained`, `applyAbsenceDerived` | `PROOF REUSE` ровно доказанного scope; empty-lineage API не используется для nonempty ancestors. `MODIFICATION` достаточного certificate/context/terminal/current correspondence в общей R2 relation. **Универсальный full ABORT body остаётся FUTURE WORK**, не дополнительным gate. |
| `PublicState.lean`: `State`, `fieldNames`, `profile`, `Identity`, `documentBytes`, `preimage`, `admissible`, `load`, `loadedCompletePreimage`, `Vote`, `voteEntries`, `readVote`, `Frame`, `extract`, `expectedContext`, `extractFirst`, `projectFirst`, `IdentityMap`, `nativeMatches`, `bindNativeFrame` | `MODIFICATION` family carrier/common preimage binding и consumers; старый 64-field view/profile остаётся прежним. Generic `Value`/encoding/ordering/canonicality — `PROOF REUSE`. View root не заменяет полный original state root. |
| `PublicDurablePrefix.lean`: `Historical`, `checkHistorical`, `Pairs`, `checkPairs`, `Prefix`, `checkPrefix`, `alignment`, `prefixNoMissingVote`, `prefixNoExtraRecord`, `prefixNoDuplicates`, `opaqueSlotBlocksCompletePrefix` | `MODIFICATION` R2 exact all-kind/all-actor prior contents, связанного с family original bytes; текущая arithmetic-only `SourceBody` недостаточна. `executedMatchesEveryPreviousPublicVote`, `unknownCannotSupplyCompletePrefix` — legacy results / новая композиция R3. |
| `PublicVoteEffects.lean`: `Inputs`, `readInputs`, `expected`, `check`, `Checked`, `project`, `exactFourAssigned`, `checkedSequenceAllocatedFromPrior`, `checkedDurableMembership`, `checkedNoMessageExposure`, `checkedNoCurrentAdvance` | `PROOF REUSE` single-view footprint; `MODIFICATION` R3 общего эффекта/sequence. Generic `insertMembership`, `updateKeys` — `PROOF REUSE`. |
| `PublicSnapshot.lean`: `Header`, `encode`, `preimage`, `Exported`, `load`, `FirstBound`, `bindFirst`, `executeFirst`, `originalContextAndCommand`, `knownEventKeepsOriginalSequence`, `boundNativePreparation`, `executionPreservesReachability`, `executionUnknownRetainsPrefix` | Native snapshot bytes/IDs — `UNCHANGED`; факты original context/sequence — `PROOF REUSE`; common family binding — `MODIFICATION` R2, preservation — R3. |
| `PublicJournal.lean`: `Envelope`, `Slot`, `Journal`, `checkNativeSlot`, `checkSlot`, `journalPreimage`, `journalRoot`, `step`, `replay`, `nativeSequenceCountsAllSlots`, `replayExactSlots`, `replayComputedRoot`, `observedAppendExact`, `unknownTipCannotClaimAppend` | `PROOF REUSE` original journal machine/bytes. `MODIFICATION` correspondence с полным public family, не нового WAL формата. |
| `PublicRecovery.lean`: `persist`, `otherVote`, `advance`, `retry`, `exposeRetry`, `restore`, `recover`, `historicalRetryExact`, `unknownPersistPreservesKnownPrefix`, `absenceRequiresExactPrior`, `restoreRequiresExactRoot`, `readyRecoveryDerivesAllVoteHistory`, `exposedStagesRequireBarrierAndCommit`; `PublicReachability.lean`: `Invariant`, `Transition`, `Reachable`, `transitionPreservesInvariant`, `reachableInvariant`, `reachableJournalHistory`, `reachableSlotProvenance`, `reachableArithmeticPreparation` | `PROOF REUSE` существующей абстрактной машины. `MODIFICATION` R3 полного relation-preservation theorem; эти component results не закрывали его раньше. |
| `RecoveryKernel.lean`: `replayExactRecords`, `originalRecordRecovered`, `verifiedPresenceReplays`, `verifiedAbsenceReplays`, `incompleteRetainsUnknownSequence`, `corruptAndAmbiguousStayBlocked`, `unauthenticatedScanBlocked`; `NativeReplay.lean`: `checkApply`, `acceptedVoteHasPreparation`, `acceptedApplyHasDerivation`, `preparedRecordRecovered`, `staleFirstVoteRejected`, `unknownNativePresence`, `unknownNativeAbsence`, `unknownNativeCannotInferAbsence` | `PROOF REUSE` original-record/replay facts с существующими source/trust hypotheses. Интеграция с full family — R3, без ослабления UNKNOWN. |
| `NativeWholeReplay.lean`: `historyRun`, `observedWhole`, `incompleteRejected`, `retryWholeOrigin`, `arithmeticScanRejected`; `NativeVoteCache.lean`: `capture`, `lookup`, `lookupExact`, `rowOriginal`, `arithmeticOriginalSource`, `ambiguousLookup` | `PROOF REUSE` фактов об исходной истории/lookup. Ограниченный whole-replay API не объявляется общим recovery theorem; общая композиция — `MODIFICATION` R3. |
| `Apply.lean`: `applyVoteUniqueness`, `currentStateUniqueFromQCIntersection`, `abortPreservesCurrent`, `fullRecoveryObservationalEquivalence`, `restartRecoveryIdempotent` | `PROOF REUSE` абстрактных theorem statements. `fullRecoveryObservationalEquivalence` не является уже доказанным native full-state refinement. |
| `formal/proofs/DeltaReduce.lean`, `AxiomAudit.lean` | `MODIFICATION` imports/audit inventory при включении family proof в обязательный bundle; `RE-RUN ONLY` прежних доказательств. Это wiring существующего gate, не новый safety obligation. |

## Schemas и executable checkers

| Существующий путь / интерфейс | Статус / точное последствие |
|---|---|
| `formal/schemas/formal-trace.schema.json`: `roundContract`, `parameterAssignment`, `coordinateRange`, `nativeSnapshot`, `event` | `UNCHANGED` outer event/native witness contract в минимальном B. Один исходный event, исходные assignment/context IDs. `MODIFICATION` совокупного public-evidence контракта через отдельный versioned, digest-bound family witness и его validator; имя нового artifact пока не выбирается. |
| Там же `nativeSnapshot.projection_id`; `formal/scripts/native_trace_witness.py`: `NativeEvidence.check`, `snapshot_id`, `check_native_trace` | `UNCHANGED`. `projection_id` уже связывает PARAMETER с APC, APPLY с aggregate ID; **его нельзя занять ID семейства**. Native witness container/version и его original hashes сохраняются. Family companion отдельно связывает exact event/snapshot/full source. |
| `delta-protocol/schemas/parameter-schema-v1.json`, `008/parameter-shard-qc-v1.json`, `008/apply-candidate-v1.json`, `008/apply-qc-v1.json`, `008/apply-arithmetic-profile-v1.json`, `checkpoint-manifest.schema.json` | `UNCHANGED` для B/R2. Production wire/schema/QC/manifest IDs не меняются; B не добавляет coordinate certificate. Имеющиеся `formal_semantics_id` pins остаются pins исходного протокола; будущее runtime adoption новой authority — отдельная совместимость после GO, не автоматическое переписывание старых объектов. |
| `formal/scripts/coordinate_projection.py`: `native_schema_projection` | `PROOF REUSE`/`RE-RUN ONLY` исходной проверки exact coordinates/offsets/ranges. Никакого rename/split shard. |
| `formal/proposals/native_binding.py`: `Witness`, `NativeAnchor`, decoding/canonical source derivation | `UNCHANGED` native vector oracle. `RE-RUN ONLY` совместимого evidence; нет нового native admission rule. |
| `formal/scripts/public_native_projection.py`: `PinnedFixtureSources`, `_parents`, `_authority`, `_parameter`, `_apply`, `bind_first`, `projection_id`, `verify_projection` | `MODIFICATION` family adapter/validator. Старые fixture pins сохраняются как fixtures, не используются как finite approval table общего R2. |
| `formal/scripts/public_state_projection.py`: `PROFILE`, `MODEL_VALUES`, `inventory`, `model_identity`, `canonical_value`, `state_preimage`, `state_root`, `check_observation`, `tla_value`, `replay_sources` | `MODIFICATION` family profile, shared source/aliases, reconstruction и replay consumer. Старые tagged scalar values/64-variable inventory можно оставить legacy. Нельзя выдавать family за прежний `deltareduce.full-public-state.v1-candidate` с прежним digest. |
| `formal/scripts/public_state_storage.py`: `pack`, `unpack`; `formal/scripts/check_public_state_replay.py` | Generic legacy storage — `UNCHANGED`/`PROOF REUSE`; family dispatcher/replay integration — `MODIFICATION`. Дополнительные family поля не подмешиваются в прежние 64 protocol variables. |
| `formal/scripts/native_durability_witness.py`: `vote_exposed`, `observation_id`, `journal_root`, `envelope`, `persisted_bytes`, `check_durability_trace` | `UNCHANGED` original journal/effect/sequence semantics; `RE-RUN ONLY`. `MODIFICATION` вызывающего family composition: одна durability observation на один source event, не по записи на coordinate. |
| `formal/scripts/check-refinement.py`: `verify_round_contract`, `verify_quorum`, `check_trace`, `check_all_fixtures` | `MODIFICATION` family-witness dispatch/checking. Существующие shape/quorum проверки — `PROOF REUSE`; голос/доставка/QC учитываются однократно. |
| `formal/scripts/formal_artifacts.py`: `discover_semantic_artifacts` | `MODIFICATION` регистрации обязательного family contract. Сейчас функция включает один hard-coded trace schema; отдельный новый schema автоматически в semantic inventory не попадёт. Нельзя оставить обязательный family contract вне source binding. |
| Там же `derive_formal_semantics_id`, `validate_trace_document`, `validate_contract_registry`, `determine_report_decision`, `verify_report_document`; `formal/scripts/verify_phase0.py`: `verify` | Hash/decision/legacy-validation алгоритмы — `UNCHANGED`; применение — `RE-RUN ONLY`. Inventory/registry/compatibility bindings — `MODIFICATION` при будущем включении B. Frozen statements R1–R7 не меняются. Новый report/GO сейчас не выпускается. |
| `formal/scripts/run_formal_gate.py`: `run_proofs`, `dispatch`; `formal/scripts/check_lean_evidence.py`: `main`; `formal/scripts/audit_public_prefix_sources.py`: `audit` | Gate dispatch/Lean checker — `RE-RUN ONLY` после подключения в существующие imports/refinement entry points. Prefix audit — `RE-RUN ONLY` прежних exact-source cases; его family consumer/fixture contract — `MODIFICATION`, если используется в общем R2. Финальная R4 квалификация отложена. |

## Fixture families и generators

Изменяемые fixtures подтверждают ровно существующие source/coverage/atomicity
obligations. Не требуется расширять их количество или создавать ещё один большой
native corpus. Старые записи не перезаписываются новыми identities.

| Существующая family | Статус |
|---|---|
| `formal/fixtures/traces/native/` и `manifest.json`, исходные canonical PARAMETER/APPLY/WAL/UNKNOWN records, исходный coordinate/schema corpus 4/8/8/8/8; `formal/scripts/native_trace_fixture.py`, `native_durability_fixture.py` | `UNCHANGED` original bytes/IDs; `RE-RUN ONLY` validators. Дополнительный family evidence ссылается на эти оригиналы. |
| `formal/fixtures/traces/legal/`, `formal/fixtures/traces/illegal/`; `formal/scripts/generate_trace_fixtures.py`, `generate_native_trace_mutations.py` | Существующие protocol event сценарии — `RE-RUN ONLY`; family-bearing public projection companions/generation — `MODIFICATION`. Обновлённые candidate bindings не превращают старую запись в новый production run. |
| `formal/proposals/public-arithmetic-inputs.json`, `public-arithmetic-vectors.json`, `public-native-projection.json`, `public-state-vectors.json`, `public-state-lean-vectors.json`, `public-state-replay.cfg`, `public-arithmetic-replay.cfg` | Старые scalar golden results сохраняются как legacy; общий family fixture/replay путь — `MODIFICATION`. Новые projected roots только для новой representation, не замена native body/current IDs. |
| `formal/proposals/public-journal-vectors.json`, `public-recovery-vectors.json`, `public-snapshot-vectors.json` | Original journal/snapshot cases — `RE-RUN ONLY`; их соединение с family state/transition — `MODIFICATION` R2/R3. |
| `generate_public_arithmetic_inputs_lean.py`, `derive_public_arithmetic_inputs.py`, `generate_public_arithmetic_vectors.py`, `generate_public_native_projection.py`, `generate_public_state_vectors.py`, `generate_public_state_lean.py`, `generate_public_vote_effects.py` в `formal/scripts/` | `MODIFICATION` family generation/consumer, legacy entry points могут сохраняться. |
| `generate_public_journal_vectors.py`, `generate_public_recovery_vectors.py`, `generate_public_snapshot_vectors.py` в `formal/scripts/` | `RE-RUN ONLY` исходной native/legacy части; family join examples — `MODIFICATION`, не переопределение original journal bytes. |
| Lean `NativeScalarProjectionVectors`, `NativeInputProjectionVectors`, `PublicArithmeticInputsVectors`, `PublicAuthorityVectors`, `PublicParameterBodyVectors`, `PublicApplyBodyVectors`, `PublicRootBodyVectors`, `PublicRootParentsVectors`, `PublicRootHistoryVectors`, `PublicStateVectors`, `PublicDurablePrefixVectors` | `RE-RUN ONLY` сохранённых scalar claims; `MODIFICATION` family/source integration cases для общего R2. |
| Lean `PublicEarlyBodyVectors`, `PublicPlanningBodyVectors`, `PublicFailureBodyVectors`, `PublicAbortLineageVectors`, `NativeAbortLineage` source evidence | `RE-RUN ONLY` прежних source/lineage результатов; `MODIFICATION` только общего all-kind family correspondence. Не новый full ABORT constructor. |
| Lean `PublicSnapshotVectors`, `PublicJournalVectors`, `PublicRecoveryVectors`, `NativeReplayVectors`, `NativeWholeReplayVectors`, `NativeVoteCacheVectors`, `RecoveryKernelVectors`, `NativeWalVectors`, `NativeWalScanVectors` | `RE-RUN ONLY` прежних scoped results; `MODIFICATION` family-preservation/recovery integration, преимущественно R3. |
| Lean `ParameterKernelVectors`, `ApplyKernelVectors`, `NativeVectorArithmeticVectors`, `NativeVectorSourceVectors`, `NativeVectorCorpusVectors`, `NativeManifestVectors`, `NativeSchemaVectors`, `NativeParameterVectors`, `NativeApplyResultVectors` | `RE-RUN ONLY`; arithmetic/native source golden bytes не меняются. |
| `formal/fixtures/counterexamples/`: `mut-parameter-arithmetic-binding`, `mut-parameter-model-binding`, `mut-apply-arithmetic-binding`, `mut-apply-optimizer-binding`, `mut-arithmetic-{product,prefix,conversion}-guard`, `mut-domain-{rounding,mixture-weights}`, `mut-incomplete-aggregate`, `mut-unchecked-overflow`, `mut-{parameter,apply}-persistence-{sequence,recovery}`, `mut-{parameter,apply}-stale-current`, `mut-{parameter,apply}-stale-current-recovery`, `mut-missing-durable-vote`, `mut-current-without-applyqc`, `mut-partial-publication` | `RE-RUN ONLY` существующих production-mutant families. Их обнаружение не заменяет proof общей family relation. Остальные зарегистрированные counterexamples сохраняются в R4 manifest. |

Затронутые существующие tooling-test consumers: `test_coordinate_projection.py`,
`test_public_arithmetic_inputs.py`, `test_public_arithmetic_projection.py`,
`test_public_state_projection.py`, `test_public_state_lean.py`,
`test_public_native_projection.py`, `test_public_authority.py`,
`test_public_parameter_body.py`, `test_public_apply_body.py`,
`test_public_root_body.py`, `test_public_root_parents.py`, `test_public_root_history.py`,
`test_public_durable_prefix.py`, `test_public_vote_effects.py`,
`test_public_snapshot_vectors.py`, `test_public_journal_vectors.py`,
`test_public_recovery_vectors.py`, `test_public_abort_lineage.py`,
`test_refinement.py` — `MODIFICATION` family cases/changed contracts,
`RE-RUN ONLY` сохранённых legacy cases.
`test_native_trace_witness.py`, `test_persistence_witness.py`,
`test_uncertain_witness.py` — `RE-RUN ONLY` native semantics, с проверкой отсутствия
умножения source records при family integration. Это перечень consumers,
не новая квота на тесты.

## Что именно теряет квалификацию после реализации B

**Этот отчёт ничего из перечисленного не инвалидирует сегодня:** code/proof/schema
и candidate semantics не изменены. При будущем подключении B:

| Результат | Классификация |
|---|---|
| Доказанные kernel theorems, scalar-only constructors, original coordinate/identity lemma, bounded TLC statements на прежних inputs | `PROOF REUSE` или `RE-RUN ONLY`. Их математические утверждения сохраняются; расширенное применение требует новых hypotheses/composition. |
| Предположение, что прежний single scalar complete-body API представляет vector shards 4/8/8/8/8 | `INVALIDATED` **уже диагностикой**, не новым изменением. Это не было закрытым formal result; его нельзя включать в оценку как готовую часть R2. |
| Старые scalar full-public-state roots/whole-body checks как свидетельство **полного vector family state** | `INVALIDATED` для такого применения. Как legacy scalar observations они остаются корректными. |
| `formal/reports/formal-semantics.json`, `formal-id-registry.json`, `source-tree-manifest.json`, `baseline-inputs.json` для нового mandatory artifact set | `MODIFICATION` bindings/derived identities. R1 DoD и accepted contract остаются прежними; смена semantics ID не является утверждением, что изменён native wire protocol. |
| `lean-proof-report.json`, `tlc-evidence.json`, `refinement-evidence.json`, `mutant-evidence.json` как aggregate qualification нового candidate | `INVALIDATED` как перенос старого evidence без проверки compatibility. Неизменные отдельные результаты могут переиспользоваться только по существующим gate rules; необходимая повторная квалификация — R4. |
| `formal-verification-report.json`, `reproducibility-evidence.json`, `clean-offline-reproduction.json`, прежние независимые review attestations как authority для новых sources | `INVALIDATED` для новой цели; R5–R7 по прежнему плану. Старый report уже исторический NO_GO; существующего candidate GO здесь не отзываем. |
| `nativeArithmeticRecoveryRefines` | Пока отсутствует содержательное закрытие; `MODIFICATION`/завершение R3, а не потеря готовой теоремы. |

## Оценка активного времени

Оценка **оставшегося** труда после прежних результатов. Время уже сделанных proofs
и этого анализа не начисляется повторно. Ожидание пользователя/heartbeat/reviewers
не является активной работой. Это экспертная оценка с ограниченной уверенностью,
не измеренная скорость завершения ещё не построенного general proof.

| До закрытия всего R2, при representation-only B | Активные часы |
|---|---:|
| Family domain/coverage/joint injectivity, общий source/preimage и heterogeneous coordinate selection | 6–10 |
| PARAMETER/ROOT/APPLY inputs/authority/body composition, исходные bounds и configuration/aliases | 8–14 |
| Полное static state/certificate/all-kind durable correspondence, достаточное ABORT отображение | 8–14 |
| Family evidence contract, checkers и focused fixture integration | 4–8 |
| Общий R2 statement/composition, kernel/dependency review и адресная проверка rejection cases | 6–10 |
| **R2 итого** | **32–56** |

| R3 после закрытого R2, без повторной оплаты R2 | Активные часы |
|---|---:|
| Admissible initial snapshots / verified reachable histories и base relation | 6–10 |
| Admission/persistence/exposure/send/delivery/QC/current lifting | 8–14 |
| Crash/restart/UNKNOWN, exact presence/absence/corrupt scan и original replay | 8–16 |
| Общая induction/composition `nativeArithmeticRecoveryRefines`, statement audit и focused verification | 6–12 |
| **R3 дополнительно** | **28–52** |

**R2 + R3: 60–108 активных часов. Это не оценка до Formal GO.** Здесь нет финального
полного R4 gate, чистого offline R5, итогового R6, независимого R7, runtime/FFM,
демо, WAN, benchmark или training. R7 остаётся BLOCKED_EXTERNAL; R2/R3 по известным
условиям локально выполнимы, с неустранённым архитектурным риском.

Прежняя оценка R2 12–24 часа предполагала преимущественно соединение уже имеющихся
конструкторов. Диагностика опровергла эту предпосылку для native vectors. Новая
оценка меняет прогноз трудозатрат, **не критерии закрытия и не перечень R1–R7**.
R3 также требует дополнительной композиции семейства; старые component proofs
уже учтены как reuse, а не как необходимость переписать всё.

Два главных риска для диапазона: доказательство синхронности без лишних состояний/
голосов и соответствие разрешённым native widths без усиленных ограничений.
`ModelLimit ≤ maxInput` и symmetric `resultFits` в текущем Lean bridge сами по себе
не являются такими доказательствами. Известное исключение `INT64_MIN` этим guard
не доказывает достижимость именно такого PARAMETER результата из int16-Q; нельзя
выдумывать counterexample или ослаблять договорённый FULL_SIGNED_INT64 domain.
При доказанной необходимости поменять production predicate оценка B пересматривается
на контрольной точке до реализации такого изменения. Верхняя граница не обещана.

Остаток конечен **по составу obligations**: R2 связывает фиксированную существующую
data/action vocabulary и допустимый domain; R3 доказывает base/step/recovery для
этой relation. Параметрическая длина vectors не означает конечный fixture proof.
Новые самостоятельные proof-layer gates, универсальный ABORT constructor и
production exporter project в эту оценку не добавлены.

## STOP и основания

Реализация B, новые Lean/TLA proofs, изменения schemas/fixtures и R4–R7 **не начаты**.
Следующий шаг требует прямого выбора/разрешения пользователя. Automation остаётся
на месте; её heartbeat не снимает STOP. Residual delta: R1 CLOSED; R2/R3 OPEN.

Основания: [ADR-0011](0011-r2-shard-representation-options.md),
[замороженный DoD](../../specs/000-formal-tla-spec/accepted-residual-20260928.md),
[candidate contract](../../specs/000-formal-tla-spec/candidate-contract.md),
[PO-AB1 / PO-R1 / PO-R2](../../specs/000-formal-tla-spec/proof-obligations.md),
[refinement contract](../../specs/000-formal-tla-spec/refinement-contract.md),
[arithmetic amendment](../../specs/000-formal-tla-spec/amendments/0001-arithmetic-input-binding.md),
[scalar-domain diagnostic](../../formal/proposals/r2-domain-audit.md),
[minimal vector relation](../../formal/proposals/vector-shard-representation.md).
