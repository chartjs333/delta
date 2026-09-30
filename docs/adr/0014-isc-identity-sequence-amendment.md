# ISC identity / sequence mapping — decision memo

**30 сентября 2026. I-B и S-RANK APPROVED как архитектурные решения.
Реализация не разрешена.**
Existing tasks T053/T016, HR008-001/002/018. Только amendment к
[WAL Capsule v1](0014-isc-finalization-wal-capsule-v1.md), которая утверждена как local byte/storage contract.
[Commitment Profile A](0014-isc-commitment-profile-v1.md) утверждён только для FR-004.
Пользователь утвердил I-B и S-RANK; альтернативы ниже сохраняются как rationale,
не открытые варианты. Изменения действуют только в будущей независимо закреплённой
и квалифицированной semantics version `σ_next`, не в существующих accepted/candidate
IDs. σ_next — обозначение, новый version/hash не назначен. Код, schemas, proofs,
R2.3/R3 и frozen DoD/Profile не меняются. Документальные amendments внесены в
WAL Capsule и Producer Integration; W1 теперь утверждён как local byte/storage contract.

## 1. ISC consensus identity: утверждённый I-B

Обозначения: `B` — существующий `VoteInputSetBody`; `b=vote_input_set_body_id(B)`;
`C` — полный typed ISC с quorum/signers; `c=content_id(C)`.
Существующий `b` хэширует context, input_root и полный ordered tuple list под
`deltareduce.vote.input-set-body.v1`. `c` хэширует canonical ISC, включая signer set,
под `deltareduce.008.input-set-certificate.v1`. Это **разные существующие IDs** [N1].

**Нормативное решение I-B: единая consensus identity ISC — `b`; `C/c` — неизменяемый
certificate witness / identity его bytes, удостоверяющий B.** Body ID сам по себе
не является authority: нужен проверенный quorum witness для того же полного B,
независимо допущенные context/configuration и durable finalization.
Ни C, ни signer identities, ни исходные vote envelopes при этом не удаляются.

| Потребитель | Предлагаемое точное значение и правило |
|---|---|
| Seed / assignment | Parent/context ISC = `b`. Seed разрешён только после durable finalization B с проверенным C; его consensus identity/выбор не зависят от выбора witness c/signers. Все решения о допустимости assignment используют тот же B/seed context. Existing bucket function использует `seed_id,ticket_id`, а не C напрямую; новый randomness algorithm здесь не предлагается |
| EC/APC/PARAMETER/ROOT lineage | Каждая ссылка **на ISC** разрешается в `b`; проверка witness C отдельно подтверждает `body(C)=B` и quorum. Остальные certificate edges не переопределяются этим memo |
| Finalized index | Логически `(independently admitted round context) → b`, не `round → c`. Witness storage сохраняет `c → exact C`. Другой B в том же finalized context — conflict; другой валидный C для того же B — не новый consensus ISC |
| Replay | Идентичность finalized результата — `(round context,b)`. Точная повторная команда возвращает исходные local receipt/C/effect/physical slot. Другой request/C того же B не создаёт вторую finalization, vote или slot и не переписывает первый witness. Проверка новых входных bytes не заменяется сравнением одного b |

Таким образом, C в receipt или publish payload остаётся исходным **артефактом
доказательства**, но не ключом выбора consensus результата. Поздний quorum cut
не меняет ни локально зафиксированные bytes первого witness, ни общую identity B.
Исходная delivery inventory сохраняется; message/vote multiplicity не стирается.
Это не разрешение свести все public certificate records с разными signers к одному
непроверяемому объекту: соответствие полных collections ещё требует qualification.

**Почему недостаточно оставить C.** TLA `FinalizedISCBodies`, `SeedRecord`, EC/APC
и ROOT edges уже используют **body**, тогда как native `finalized_input_set_ids`,
seed и downstream `input_set_certificate_id` сейчас разрешаются через **c** [T1,N2].
Это фактическое расхождение контрактов, а не новое требование к multiplicity.

Минимальный arrival-cut пример: f=1, honest h1/h2/h3 и Byzantine z подписали один B.
Доставленные sets `{h1,h2,z}` и `{h2,h3,z}` оба имеют quorum 3/4, но дают разные C/c.
При фиксации первого C на каждом узле и последующем молчании z honest узлы могут
остаться на разных descendant contexts. Общего C текущая quorum validity не
гарантирует. Это source-derived сценарий для проектируемого producer, **не**
исполненный native trace или новый TLC counterexample. Sorting signers делает
canonical один set, но не делает разные sets одинаковыми.

| Альтернатива | Certificate semantics / bytes / Init/Next | Liveness при разных cuts |
|---|---|---|
| **I-B, утверждён** | Меняет native смысл ISC parent-reference/index; ISC C encoding/hash formula остаются. Downstream signed references/IDs меняются. Existing production TLA Init/Next менять для выбора B не требуется: они уже body-based | Устраняет именно split из-за ISC witnesses при одном B; не требует ожидания конкретного signer subset. Полная liveness по-прежнему зависит от существующих seed/network/quorum предпосылок и ещё не доказана |
| I-C: полный C | Сохраняет нынешние native ссылки/bytes. Прямой перевод public identity на C меняет seed/parent predicates и семантику соответствующих Next actions; простая подстановка в refinement этого не доказывает | Текущий контракт не обеспечивает общий C. First-q и minimum-seen зависят от cut; ожидание фиксированных signers/all validators может ждать Byzantine бесконечно |
| I-W: protocol-unique witness | В существующем контракте нет правила, делающего witness глобально уникальным. Дополнительное agreement/selection либо другой certificate profile — отдельное семантическое решение; последствия Init/Next/bytes нельзя определить без этого решения | Из существующих producer/quorum rules такая liveness не следует. Новый механизм здесь не проектируется |

**Compatibility I-B.** Нельзя под старой версией silently заменить значение поля
`input_set_certificate_id` с c на b. Native checks, parent contexts и downstream
signed bodies изменятся; их EC/APC/ROOT и последующие dependent QC IDs потребуется
получить заново в квалифицированном новом semantics profile. Existing ISC vote body
hash и ISC C bytes/hash для *тех же* B/signers/context сохраняются; смена
`formal_semantics_id` в context сама изменит связанные bytes/IDs. Старые подписи/QC
не мигрируют путём relabel. No-double-vote не разрешает пересигнировать старый
защищённый context. Сейчас никакой ID/version не изменён и не назначен.

[W1](0014-isc-finalization-wal-capsule-v1.md) теперь нормативно различает:
consensus parent/finalized lookup = b; original witness/receipt/publish artifact = c;
native physical slot = s; public vote ordinal/count = V_a(s). Его IFQ1 command body hash
уже содержит b; IFR1 и PUBLISH_CERTIFICATE сохраняют artifact c. Дополнительные wire
identity fields не добавлены. Старое обещание неизменности смысла downstream
parent-reference заменено явной σ_next-only compatibility boundary. Старые C/QC/WAL
не relabel или мигрируют; parent.qcId в old source остаётся фактом о старой версии.

Это решение **не закрывает explicit parent/context completeness**: существующий B
не дополняется parent field, transitive configuration binding не объявляется
достаточным. Также не решается уникальность witnesses остальных certificate видов.

## 2. Sequence mapping: утверждённый S-RANK

Область: один actor/фиксированный epoch approved profile, полный независимо
проверенный original WAL prefix `L_a[1..p]`. Physical slot — порядковый номер frame,
**не byte offset**. Все local kind-2 records принадлежат этому actor; remote vote
envelopes внутри kind 3 — witness evidence, не новые local vote records [N3,L2].

Нормативная relation использует существующие счётчики раздельно:

```text
physicalSequence(L_a) = p = length(L_a)
native Vote.durable_sequence(L_a[s]) = s               (kind = 2)
public durableSequence[a] = V_a(p)
V_a(p) = number of original kind-2 records in L_a[1..p]
public ordinal of original vote at s = V_a(s)
s = V_a(s) + count(kind 1 in L_a[1..s]) + count(kind 3 in L_a[1..s])
```

Последнее равенство для v1 с kinds 1/2/3; unknown kind — fail closed, не vote и не
stutter по умолчанию. Учитываются **все** исходные votes, не только ISC/arithmetic.
Нужны сохранение порядка, actor identity и взаимно однозначная проекция original
votes на public vote envelopes: public TLA хранит set, его cardinality должна
равняться V. Если два original votes схлопываются в один public envelope, rank это
не исправляет; такой history нельзя молча дедуплицировать [T2,L2].

| Original frame | Physical slot p | Public counter V | Сохраняемый signed native sequence |
|---|---:|---:|---:|
| kind 1 command | 1 | 0 | — |
| kind 2 ISC vote | 2 | 1 | 2 |
| kind 3 ISC finalization | 3 | 1 | — |
| kind 2 EC vote | 4 | 2 | 4 |

Public VoteEnvelope не содержит native slot: logical ordinal не заменяет ни
signed Vote.durable_sequence, ни original DVREC receipt. Coarse
`RoundState.durable_sequence` — ещё отдельный command-state счётчик, не p/V;
kind 3 по W1 его сохраняет. При checkpoint prefix counts берутся из проверенной
original history, не обнуляются по границе snapshot и не берутся на веру из metadata.

| Crash / replay cut | Требуемое поведение mapping |
|---|---|
| До append / отклонение команды | p/V и исходные receipts не меняются |
| Failed/unknown append или barrier | Новый durable tip неизвестен; нет exposed effect и READY. Нельзя объявить p+1 подтверждённым или освободить тот же slot для другого vote |
| Recovery: целый surviving frame | После проверки prefix/source/floor и durability принять original frame ровно один раз: kind 2 увеличивает p/V, kind 1/3 — только p. Kind 3 также восстанавливает проверенное finalized state, не новую подпись |
| Torn/corrupt/ambiguous frame | Fail closed по approved provenance profile; не переписывать tail/sequence ради relation |
| После barrier до commit/expose; повтор после restart | Восстановить тот же frame/receipt/effect и physical slot. Replay ничего не добавляет; ранняя недоставка effect не создаёт новую finalization |

**Compatibility S-RANK.** Certificate semantics, existing signed bytes/QC IDs и
native sequence interpretation не меняются. Но новый vote после вставленного kind 3
имеет следующий **physical** slot, поэтому его новые signed bytes/vote ID (и generic
QC с этими vote IDs) отличаются от гипотетического запуска *без* kind 3. Это не
перенумерация существующих records. Typed ISC C не содержит native vote sequence:
один B/signers/context по-прежнему определяет те же C bytes.

Production TLA Init/Next менять для S-RANK не требуется: `PersistVoteEnvelopeChanges`
увеличивает public counter для vote; `FinalizeISC` оставляет его unchanged;
`DurableSequenceExact` уже считает votes [T2]. Kind 3 может представлять FinalizeISC,
а не whole-state stutter; crash/replay refinement этого соответствия пока не доказан.
Rank не добавляет ожидания quorum/cut и сам не ухудшает liveness при исправном
durable storage и существующих bounds; overflow/capacity checks сохраняются.

Альтернативы отклонены: `public sequence = physical slot` нарушает existing
DurableSequenceExact уже при kind 1, а kind 3 усиливает расхождение; замена signed
native slot на vote ordinal меняет подписанные bytes/receipt contract и не нужна.

## 3. Что потребуется переквалифицировать после approval

Никакие старые теоремы сегодня не стали ложными: они остаются результатами о своих
прежних definitions/inputs. Их нельзя переносить на изменённые contracts как GO.

| Решение | Existing proofs / evidence и точная граница reuse |
|---|---|
| I-B | `NativeIscCertificate.checkedBody`, `bodyIgnoresSigners`, `checkedQuorum` — reuse своих утверждений; они не доказывают равенство c. `NativeSeedTranscript.linked/linkedSources`, `NativeSeedSection.finalizedParent`, `NativeEligibilityLineage`, `NativePlanLineage`, `NativeRootParents.sameIsc/crossParents/iscSource`, `PublicRootHistory.cachedOriginalParents` — новая qualification parent links: seed сейчас явно ссылается на `parent.qcId`. Source-bound loaders `FamilyRelation.loadObservedState` и source/alias checks затронуты. Evidence families `native-isc-certificate`, `native-seed-transcript`, `public-root-parents`, `public-root-history`, `b-family-constructors` не покрывают новую семантику |
| S-RANK | `NativeWalBytes.Shape/decode`, `NativeWalScan.checkedSequenceUnique`, `NativeConfigReplay.step/historySequence` — kind-3 coverage и original positions. `NativeArithmeticHistory.historyCounts/historyVotePosition/recoveryCounts/retryPosition`, `NativeCacheHistory.positionMapping/recoveredCache`, `NativeCacheProjection` — прежний член «число commands» не включает kind 3; нужна qualification non-vote count. `NativeReplayAdmission.originalSequence`, `NativeIscAdmission.sequencePreserved` сохраняют смысл original slot, но новые mixed histories не покрыты. `FamilyRelation.loadJournalRows/journalRowsEntireOriginals` сейчас используют ветку `kind != 1`: новый reader обязан validate kind 3 отдельно и считать votes только при kind 2; `durableLogicalSequenceFromOriginalVotes` и обе no-missing/no-extra стороны также переквалифицируются |
| Совместно | Native vote-policy/seed/EC/APC/ROOT fixtures, exact bytes/admission/replay and cross-language conformance; evidence `native-wal-codec`, `native-wal-scan`, `native-config-replay`, `native-vote-cache`, `native-whole-replay`, `b-family-constructors`. TLA `ISCImmutability`, `CertificateQCUniqueness`, `CertificateVoteUniqueness`, `SeedAfterInputFreeze`, `DurableSequenceExact` и public certificate lineage gates повторно квалифицируются с новым refinement input. Pure arithmetic/R2.1/R2.2 не открываются заново без конкретного контрпримера. Candidate semantics hash/report не могут переиспользовать старые pins как GO |

Это impact inventory двух решений, не новый список обязательств DoD и не начало R3.
Полная state/signers correspondence и liveness остаются задачами последующей
разрешённой qualification; этот source audit не является независимой аттестацией.

## 4. Evidence path и STOP

Исходники прочитаны без выполнения новых native/formal tests. Exact pinned blobs
и documentary checks исходной редакции:
[historical source audit](evidence/0014-isc-identity-sequence-source-audit.json).
Его report hash относится к pre-approval редакции, не к этому amendment.
Нормативные documentary vectors с positive controls и rejected mutations находятся
в [WAL Capsule §10](0014-isc-finalization-wal-capsule-v1.md#нормативные-documentary-vectors-i-b--s-rank).
Они не являются production fixtures, native evidence, новыми schemas или proofs.

- **N1:** native pin `60c692f6`: `consensus.cpp:419–434`; `certificates/contracts.cpp` canonical ISC/content_id.
- **N2:** тот же pin: `certificates/vote_admission.cpp` input_qc_id/finalized/seed/EC bindings; `certificates/verifier.cpp` verify_seed/eligibility/plan; `robust/plan.cpp` seed_number/build_plan.
- **N3:** тот же pin: `protocol.hpp:98–113`; `runtime.cpp` physical allocation/recovery/retry; `wal.hpp` kinds 1/2; `vote_codec.cpp` original receipt sequence.
- **T1:** candidate `559100e7`: `DeltaReduceCertificates.tla` FinalizedISCBodies/FinalizeISC/SeedRecord; `DeltaReduceReduceApply.tla` ISC parent edges.
- **T2:** тот же candidate: `DeltaReduceQuorums.tla` PersistVoteEnvelopeChanges; `DeltaReduceFailures.tla` DurableSequenceExact; `refinement-contract.md:85–94` already distinguishes abstract vote sequence from WAL offsets.
- **L1/L2:** тот же candidate: Lean files из §3; `NativeCacheHistory.positionMapping`; `FamilyRelation.lean` complete original rows / public durable vote counter.

**STOP после разрешённого documentary amendment.** I-B/S-RANK утверждены;
W1 утверждён как local byte/storage contract. Код, schemas, proofs, production recovery,
R2.3/R3 не разрешены; approval не является exact compatible merged Formal GO.
R1/R2.1/R2.2 CLOSED; R2.3/R2 OPEN; R3 не начат. Новых решений о profile/DoD нет.
