# ADR-0012 addendum — R2 domain analysis

Tasks: T053/T054/T056. Дата: 29 сентября 2026.
База: `0894e05a0135f170329fc049db7c33153f0ae369`.
Native source опыта: `60c692f6e391f839829dfc64e93380db54cd507b`.
**Только анализ источников. A/B/C не выбраны и не реализованы.**

## Контрольный вывод

**Запрошенный бинарный результат не установлен.** Есть доказательство по
исходникам, почему прежний опыт не подтверждает нарушение в допустимой
production history. Нет ни полного независимого native-domain predicate,
достаточность которого уже установлена для замороженного R2, ни допустимого
initial / production-reachable контрпримера, который обосновывал бы обязательное
изменение representation. Отсутствие первого доказательства не является вторым.

Поэтому здесь не выдаётся ни `DOMAIN RESTRICTION SUFFICIENT`, ни
`REPRESENTATION CHANGE REQUIRED`. Это незавершённый ответ на поставленную
бинарную задачу, а не новая архитектурная развилка. Ограничение области не
принято как готовое решение. Реализация остаётся остановленной.

**Единственный установленный остаток этого анализа:** независимо обосновать
происхождение исходных *непустых certificate collections* переданного native
snapshot из допустимого protocol prefix. Existing native replay проверяет
суффикс от supplied initial state/policy; допустимость самого этого исходного
среза из его успеха не следует. Это уже замороженная initial/source часть
R2.3, а не новый gate, production-exporter project или дополнительный proof layer.

R1/R2.1/R2.2 CLOSED. R2.3/R2 OPEN; R3 не начат. DoD R1–R7 неизменен.

## 1. Что именно ограничивает исходный контракт

[Candidate contract](../../specs/000-formal-tla-spec/candidate-contract.md)
требует existing `Init` или verified reachable-history relation для initial
snapshots и прямо запрещает empty-only helper как полную область утверждения.
[Refinement contract §5](../../specs/000-formal-tla-spec/refinement-contract.md)
требует `Init` для первоначального projected state и разрешённый action/stutter
между состояниями. Непустой recovery cut требует проверенного предшествующего
prefix; переименование такого среза в genesis не устраняет это условие.

Следовательно, R2 не обязан отображать **каждый произвольный ввод**, который
локальный admission API умеет разобрать/принять. Но для исключения native
snapshot нельзя предполагать, что он уже имеет корректное public-отображение.
`validate_vote_admission_policy == OK`, успешный `OPEN`, корректный QC hash,
quorum/signature authentication и читаемый WAL по отдельности не доказывают
protocol origin. Хэш и подпись удостоверяют объект, а не всю историю его
finalization. Замороженный контракт разрешает именованные primitive trust
premises; он не разрешает предполагать whole-state correctness.

Здесь различаются:

- **protocol genesis** — существующий `DeltaReduce.Init`;
- **допустимый непустой initial/recovery cut** — срез проверенной protocol history;
- **initial argument Runtime API** — supplied bytes/state/policy, которые
  Runtime валидирует локально. Само название `initial` не делает его первым
  или вторым случаем.

## 2. Независимые predicates, которые действительно уже есть

### 2.1. Нормативная protocol reachability

Для TLA state `p` определение независимо от R2:

```text
ProtocolReach(p) := exists n, p[0..n]:
    DeltaReduce.Init(p[0])
    and p[n] = p
    and every adjacent pair satisfies DeltaReduce.Next or permitted stuttering.
```

Это использует неизменённые production `Init/Next`, а не diagnostic load action
или `UngatedNext`. Оно является точным predicate **на protocol states**.
Применить его непосредственно к native bytes невозможно: native state/policy
и public full state имеют разные типы и наборы полей. Формула
`exists p: ProtocolReach(p) and R2(native,p)` как определение native domain
была бы запрещённой зависимостью от искомого R2.

Из `Init` независимо следуют следующие исходные значения:

| Existing initializer | Нужные здесь исходные значения |
|---|---|
| `QuorumInit` | votes/messages/received/finalizedCertificates пусты; durableSequence каждого actor = 0; recovery READY |
| `CertificateInit` | closed inputs, ISC/EC/APC votes/certificates, seeds, rejections/replay receipts, abortRequests пусты |
| `ReduceApplyInit` | PARAMETER/ROOT/APPLY collections и pointer receipts пусты; current = `InitialCurrentCheckpoint` |
| `TicketInit`, `AvailabilityInit` | dynamic ticket/lease/commit/availability collections пусты, counters имеют исходные значения |
| `FailureInit` | view/time = 0, phase ACTIVE, abortReason NO_ABORT, failure/QC/vote collections пусты |

Полный `Init` — точная конъюнкция этих existing initializers и
`ModelConstantsOK`; таблица не заменяет её ослабленным условием «нет EC».
Проверка пустоты наблюдаемых raw collections/нулевых sequences может быть
независимым необходимым native genesis check. Она не доказывает остальные
полные initial/configuration/alias constraints и не охватывает непустые cuts.

### 2.2. Native execution segment

Есть независимая от public representation цепочка:

```text
NativeReplayAdmission.prepare(mode, hash, policyBytes, initialBytes) succeeds
and NativeCommandReplay.initialMachine(tick, snapshot, initialBytes) succeeds
and NativeConfigReplay.History(mode, hash, policyBytes, snapshot,
                               initialMachine, originalLog, finalMachine).
```

Это существующие definitions, не новый код. `runSound` / `recoveryComputed`
выводят такую `History` из вычисления. `VoteEntry` проверяет original policy
identity, original position, admission, receipt и snapshot guard; command replay
пересчитывает переход. Эти native modules не используют R2 или `PublicState`.

Однако `prepareWhole` декодирует и проверяет **переданный** prepared snapshot;
`initialMachine` проверяет state/snapshot shape. Они не выводят, что все
предзагруженные ISC/EC/APC/... collections были получены из protocol genesis.
В `History` первоначальная machine — параметр. Индукция по суффиксу не
доказывает отсутствующую base premise.

`NativeArithmeticHistory.recover` / `recoveryComputed` также начинают с
`prepareWhole` и `initialMachine`. Они добавляют original checked arithmetic
sources и mixed history, но не восполняют origin исходных collections.
`NativeCurrentHistory.checkRow` связывает pointer-WAL запись с переданным
finalized APPLY snapshot; это не происхождение всех сертификатов того snapshot.

`PublicReachability.Reachable` для этого не подходит: он уже использует public
journal/environment, а сам модуль прямо исключает authentication и phase/QC
rules из своего утверждения. Использовать его как независимую native initial
authority означало бы подменить область или предположить нужную связь.

### 2.3. Почему нельзя объявить одну из этих областей полной областью R2

| Предложение | Причина недостаточности |
|---|---|
| Все locally accepted prepared policies | Не доказывает protocol origin; допускает прежний API-сценарий. |
| Только empty/genesis snapshots | Теряет обязательные непустые initial/recovery cuts. |
| Только текущий guarded Runtime от genesis | Не является полной областью amendment: existing arithmetic guard запрещает PARAMETER/APPLY, которые R2 обязан связать. Из отсутствия таких executions нельзя получить содержательное закрытие R2. |
| Verified native segment от произвольного supplied initial | Независим, но не устанавливает допустимость начального среза. |
| Наличие подходящего public `Init/Next` trace после R2 projection | Циклически использует искомое отображение. |
| Новый raw guard «один ISC QC на round/body» без origin proof | Исключает пример по условию; не доказывает, что это следствие существующих native histories. Его нельзя незаметно добавить как native admission rule B. |

Желаемая форма `NativeGenesis(s) or VerifiedNativeProtocolPrefix(s)` не
содержит R2 синтаксически. Но без определённого и обоснованного второго
предиката для **полных исходных collections** это только форма требования,
не точное достаточное определение. В отчёте такой незаполненный predicate
не принимается за доказанный domain.

## 3. Исходный `ISC@1 → EC@2 → EC@3`

Исходные bytes/IDs, честный actor, sequences 1/2/3 и оба finalized ISC IDs
сохранены. Q1 и Q2 имеют одно ISC body и разные signer sets. В исходном
probe Q2 добавлен не только в `input_set_certificates`, но и в
`finalized_input_set_ids`; seed/norm/EC authority требует finalized parent.
Удаление этого признака не является прежним контрпримером.

### (1) Initial membership

**Не protocol genesis:** у примера непустые durable votes, две finalized ISC
записи и зависимая certificate lineage. Это прямо противоречит пустым
collections/нулевым sequences в existing initializers. Такой вывод не требует
полного R2: faithful observation непустых оригинальных записей нельзя назвать
пустой initial journal.

**Не подтверждён как допустимый непустой initial cut:** опыт не содержит
verified producing protocol prefix. Принятие исходной prepared policy не
является его заменой. Нельзя считать его valid initial только на этом основании.

### (2) Production reachability

**Точная цепочка не достижима через один Runtime/WAL на native revision
опыта.** ISC требует AVAILABLE, EC — ELIGIBLE. Vote запись не меняет phase;
нужный committed submit занимает WAL position и инвалидирует immutable vote
authority. Replay с прежней policy сохраняет invalidation; замена policy
нарушает original policy identity. `OPEN` с ELIGIBLE state и пустым WAL
не восстанавливает первоначальную ISC@1. Это прежний source-control-flow вывод,
не новый выполненный Runtime run или Lean theorem.

Независимо, в production TLA две **finalized ISC certificate records для
одного round** не достижимы. Доказательство по длине trace:

1. В `CertificateInit` множество пусто.
2. Единственный добавляющий writer — `FinalizeISC(body)`; он требует
   `FinalizedISCBodiesFor(body.round) = {}` и добавляет одну запись.
3. После этого guard для данного round ложен. Прочие actions сохраняют
   `inputSetCertificates`; replay не добавляет signer-вариант.
4. Следовательно, для каждого round сохраняется cardinality не более одного
   **certificate record**, что сильнее body-only QC uniqueness для этой цели.

Это доказательство по исходным actions, без изменения модели. Оно не
устанавливает отсутствующую связь arbitrary native `finalized_input_set_ids`
с этими protocol finalization events. Такая связь не получается из одного
hash/signature check. Не заявляется универсальная теорема о несуществовании
всех возможных внешних native snapshot producers.

### (3) Обязан ли R2 его отображать?

**Если snapshot действительно исключён и из valid initial, и из verified
production histories — нет.** Это следует из замороженного контракта;
тотальность по произвольному admission-API input им не требовалась.

Для данного опыта доказан отказ genesis и точной pinned Runtime chain;
допустимого исходного protocol prefix не предъявлено. Поэтому опыт **не
обосновывает обязательность A/B/C для текущего Formal GO**. В то же время
отклонение одного опыта ещё не доказывает полноту независимого native-domain
predicate и применимость всей R2.3 relation. Именно это различие не позволяет
выдать положительную бинарную метку на основании одного исключения.

## 4. Границы результата и STOP

| Утверждение | Результат |
|---|---|
| Original API/journal diagnostic | Прежнее воспроизведение действительно для его input/API scope. |
| Original witness = valid protocol genesis | Исключено existing Init. |
| Exact original chain = one production Runtime/WAL history at inspected pin | Исключено existing control flow. |
| Production-reachable representation counterexample | Не установлен. |
| Complete independent native initial/origin domain sufficient for frozen R2 | Не установлен. |
| A/B/C required / selected / implemented | Ни одно из этих утверждений не установлено/не разрешено. |

Новые TLA/Lean proofs, code, schemas, fixtures, native runs и mutation tests
не создавались. Старые formal results не переименованы и не перевыпущены.
No Formal GO, no guard change, no R3. Дальнейшая реализация R2 автоматически
не продолжается. Source inventory и raw hashes сохранены в
[documentary audit](evidence/0012-r2-domain-source-audit.json); это provenance
анализа, а не machine-checked formal evidence.
