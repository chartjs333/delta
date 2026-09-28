# R2 / B — перенос family relation на исходные vector shards

Tasks T044/T047/T053–T057. Основание: прямой выбор пользователем B после
`e157e84c0e4091ec7654212085f8a5e2076a40b1`. DoD R1–R7 не меняется.
Бюджет этой задачи: максимум 12 активных часов; R3 не разрешён.

**Результат: общее lossless family representation доказано; R2 остаётся OPEN.**
Барьер `shard.length = 1` снят в новой representation relation. Полные старые
public APIs ещё используют scalar constructors: они не объявлены мигрированными
или квалифицированными этими леммами. Production `Init/Next`, certificate semantics,
WAL identities, runtime и guard не изменены. Необходимость их изменения для этой
representation не обнаружена; это не утверждение об уже доказанной общей admission.

## Минимальная relation и что теперь закрыто

Для исходных shards `s` с длинами `n(s)>0` индекс семейства — функция
`σ : ∀s, Fin n(s)`. Один view содержит ровно одно значение **каждого исходного
shard**, выбранное по `σ(s)`, и тот же общий carrier `C`:

`πσ(C, V) = (C, s ↦ V[s][σ(s)])`.

`C` хранится один раз. В него входят исходные objects/bytes/control; координаты
не несут protocol identities. Locality требует, чтобы выбор координаты другого
shard не менял значение текущего. Восстановление выбирает каждый локальный индекс
в исходном порядке. Перебор декартова произведения не нужен для доказательства.

| Закрытая часть R2 | Проверяемое основание |
|---|---|
| Разные положительные длины, полное семейство, отсутствие потери/подмены порядка | `ShardFamily.reconstruct_project`, `project_reconstruct`, `injective`, `all_views_iff`; complete rows проверяют и индекс, и значение |
| Исходные 4/8/8/8/8 без расщепления, starts 0/4/12/20/28, все 36 Q values | `ManifestFamily.originalWidths`, `originalCount`, `originalFullValues`, `originalNoNewObjects`; используется прежний `NativeManifestVectors.wholeManifest` |
| Общность за пределами примера | `ManifestFamily.bounded_layout`, `raw_identity`, `ordered_source` для любого успешного существующего manifest loader: не более 4096 исходных shards, каждая допустимая положительная длина до 524288; остальные ограничения loader сохраняются |
| Scalar PARAMETER — вычисленная coordinate projection исходного native результата | `NativeFamily.parameterCoordinate`, `parameterOriginalRows`: настоящие rows/Q references/weights и прежние INT64/INT128 checks; без narrow limit127 или supplied expected result |
| Полный PARAMETER body и original preparation восстанавливаются без coordinate votes | `completeBodyRecovered`, `originalBodyBytes`, `preparedWholeBodyRecovered`, `preparedRecordIdentity`: vector берётся из `prepared.expected.source`; envelope/record/sequence исходные |
| Полный ordered vector state через исходные shard offsets | `StateFamily.fullOrderedState`, `globalInjective`, `exactlyOnce`; исходный `ParameterFrameValid` исключает пропуски и пересечения; reconstruction возвращает `Option`, не подставляет нули |
| APPLY model/optimizer и их полные hash preimages | `StateFamily.nativeCompleteState`, `nativeNextVectors`, `nativeRebuildHashPreimages`; `NativeFamily.applyArithmeticCoordinate` использует исходные mixture/optimizer computations |
| Координаты не умножают signer power | `ShardFamily.signer_union`, `NativeFamily.certificateSignersUnchanged`: исходный signer set/порог и существующий `SignersValid` остаются теми же |

Это статическая relation данных и состояния. Здесь нет новой transition/recovery
теоремы. Сохранение record/sequence как общего объекта не доказывает append/fsync,
retry, delivery или recovery. Эти переходы принадлежат R3.

## Точный незакрытый остаток R2

1. Подключить family к существующим **полным public input/PARAMETER/aggregate/APPLY
   body constructors** и state projection. Сейчас `NativeInputProjection.Corpus`,
   `NativeScalarProjection.Layout/Parameter`, `PublicParameterBody.Narrow/Projection`
   и их join APIs ещё scalar. Новые source/vector lemmas не доказывают, что все
   public authority/context/parent/configuration fields уже совпадают.
2. Доказать общую связь допустимых native арифметических bounds с неизменёнными
   public predicates. Сохраняются раздельные coefficient/product/prefix,
   conversion/mixture/optimizer и output guards. `ModelLimit ≤ maxInput`,
   tied model/result limit и symmetric `resultFits` старого API не становятся
   общим INT64/INT128 доказательством благодаря этому переносу.
3. Согласовать source/config/alias/certificate/state correspondence во всей
   фиксированной vocabulary R2, включая достаточные ABORT lineage/context/terminal/
   current. Общий carrier сохраняет данные, но не аутентифицирует их и не доказывает
   правильность исходной привязки. Полный state-root preimage остаётся обязательным.
4. Соединить эти части в checked general R2 relation и провести её локальный
   statement/dependency/source review. Это завершение R2; полный финальный formal
   gate, clean offline reproduction и независимое ревью остаются R4–R7.

**Исходный evidence gap сохранён:** retained original004 4/8/8/8/8 corpus не содержит
совместного исходного vector PARAMETER/APPLY vote/QC/WAL capture. Original008 scalar
certificate не присоединялся к нему; новые certificate IDs, signers или sequences
не создавались. Общая `NativePrepared` теорема применима к соответствующему принятому
источнику, но такой конкретный joined capture здесь не представлен. Это ограничение
конкретных fixtures, а не новое требование построить production exporter и не
основание автоматически объявлять весь R2 BLOCKED_EXTERNAL.

Предположения прежние: корректные canonical codec/hash abstractions и независимо
связанные primitive metadata/configuration/certificate authentication. Source-load
success и полная native computation — условия существующих theorem statements,
не caller-supplied whole public body equality. Они не заменяют перечисленные
недоказанные public correspondence/conformance obligations.

Остаток конечен **по составу**: это прежние source/body/configuration/admission/state
обязательства над фиксированными types/actions. Длины больше не требуют нового
proof layer или отдельного доказательства на каждый размер. Общая синхронность
протокольных переходов и recovery по-прежнему R3, и здесь не выполнялась.

## Обновлённая оценка

Оставшийся **R2: 28–48 активных часов**, вместо 32–56 до spike/переноса.
Оценка включает подключение полных public constructors (8–14), bounds/admission
соответствие (6–10), source/config/alias/certificate/state composition (8–14),
общую relation и локальную проверку (6–10). Это прогноз, не гарантированный срок.
Если обнаружится необходимость production predicate/certificate/WAL change,
действует немедленный STOP, а не расширение scope.

R3 не начат; прежняя отдельная оценка 28–52 часа не пересматривалась. R1 CLOSED;
R2/R3 OPEN; R4–R7 не выполнялись. Новый Formal GO не выдан.

## Воспроизведение и границы проверки

Из candidate root:

```powershell
C:/Python312/python.exe -X utf8 formal/proposals/b-family-transfer/check_transfer.py
```

Runner воспроизводит оригинальные byte sources существующим read-only loader,
компилирует точные копии новых Lean sources и зависимостей, проверяет все объявленные
definitions/theorems на axioms и неизменность защищённых contracts относительно
base commit. Допустимы только `propext`, `Quot.sound`, `Classical.choice`.
`Checks.lean` проверяет исходные крайние координаты, полную длину и отказы на
missing/duplicate/reordered/changed rows; они дополняют, а не заменяют общие proofs.

Машиночитаемый результат: `../evidence/b-family-transfer/checks.json`, manifest:
`../evidence/b-family-transfer.json`. Нового TLC, полного `formal-check`, production
run, mutation campaign или native authentication здесь не заявлено. Proposal
пока вне mandatory semantic inventory; semantics/report/fixtures не переписаны
ради PASS. После этой контрольной точки автоматического перехода к R3 нет.
