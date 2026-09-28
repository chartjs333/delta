# ADR-0011 — Представление vector shard в R2

**Статус:** B SELECTED FOR R2 BY USER; не formal authority.
**Дата:** 28 сентября 2026. **Основание:** `c666f62b4989fb1fd0306a2af7e02ccc6e649427`.
**Scope:** выбор представления внутри замороженного R2. Production-код,
mandatory schemas/proofs и DoD R1–R7 не меняются.

**Текущее ограниченное разрешение:** после spike пользователь выбрал B для R2,
не меняя DoD R1–R7. Разрешён перенос relation на исходные 4/8/8/8/8 с бюджетом
12 активных часов, без R3 и без изменения production Init/Next, certificate
semantics или WAL identity. [Контрольная точка переноса](../../formal/proposals/b-family-transfer/README.md)
фиксирует общее lossless representation и точный остаток R2.

**Предыдущий этап:** пользователь условно выбрал B только для feasibility spike
с бюджетом восемь активных часов. Изолированный
[spike](../../formal/proposals/b-feasibility/README.md) дал **FEASIBLE** для
центральной композиции на одном исходном диагностическом vector shard.
Mandatory artifacts и protocol semantics не изменены. На том этапе окончательного
принятия B и разрешения полной реализации не было; последующий выбор описан выше.
R2/R3 не закрыты. Исходное сравнение A/B ниже сохранено.

## Граница решения

Исходные shards имеют длины **4/8/8/8/8**. Lossless representation и checked scalar
coordinate projection уже доказаны при **тех же bounds**. Но complete public API
зависят от `NativeScalarProjection.Parameter` / `Layout`, требующих `length = 1`.

В обоих вариантах сохраняются native bytes/IDs/context/parents/offsets/order.
Один vote — одна WAL sequence и один элемент кворума; приём всего вектора атомарен.
Это прежние PO-AB1/R2 и one-event → one-action. Hash координаты не заменяет
native body/model ID или полный preimage.

## A — vector-aware public shard representation

Один public shard хранит индексированный вектор; PARAMETER — один vector body;
APPLY — полные model/optimizer vectors.

| Контракт | Необходимое изменение |
|---|---|
| **TLA** | `DeltaReduceArithmetic`: `q/model/optimizer[shard]` становятся векторами. `DeltaReduceTypes`: заменить `ParameterValues ⊆ Int`. `DeltaReduceReduceApply`: vector body/leaves, model/optimizer values, guards/equality. Согласовать `DeltaReducePublicState` export и TLC inputs. Ключ `(domain, shard)` прежний. |
| **Lean** | Обобщить `NativeScalarProjection`, `NativeInputProjection`, `PublicArithmeticInputs`; адаптировать `PublicAuthority`, `PublicParameterBody/Join`, `PublicApplyBody/Join` и whole-state bindings. |
| **Public schema** | Integer → index→integer function внутри body/state; generic `PublicState.Value.function` подходит. Изменить validators, projected preimages и compatibility/version. Внешний `formal-trace.schema.json` с IDs/witness refs может сохраниться; содержимое witness и его проверка меняются. Native wire schemas прежние. |
| **Fixtures** | Обновить затронутые public arithmetic/full-state traces, golden bytes/roots и generated Lean vectors. Native artifacts/manifest сохраняются; scalar cases остаются legacy либо становятся singleton-vector cases с новыми projected hashes. |

**Переделать доказательства:** scalar body/authority equality, input encoding,
coverage/injectivity, model/optimizer serialization и затронутые body-dependent
invariant/transition instantiations.

**Semantics:** публичная TLA-модель меняется. Native protocol предполагается прежним;
эквивалентность наблюдаемого поведения ещё требуется доказать. Перенос нового
encoding в native wire был бы отдельным изменением протокола вне этого ADR.

## B — scalar projection family над одним исходным объектом

Общий original object хранит identity/vector/control state; `πₖ` читает координату
при `0 ≤ k < shard.length`. Нет padding для коротких shards.
`k` — индекс представления, **не часть shard/vote/certificate ID**.

| Контракт | Необходимое изменение |
|---|---|
| **TLA** | Сохранить scalar arithmetic как подмодель; добавить синхронную композицию/lifting к существующим действиям. Один control transition, без независимых persist/send/QC/current по `k`. `DeltaReducePublicState`/replay interface различают общий объект и views. Старый одиночный scalar `Spec` не является моделью всего vector vote. |
| **Lean** | Сохранить scalar API для width-one scope. В общем bridge заменить `Parameter.scalar` / `Layout.scalar` на `k < length` и полную family relation. Адаптировать `NativeInputProjection`, `PublicArithmeticInputs`, композицию `PublicAuthority` и PARAMETER/APPLY joins. Несколько старых whole-body checks недостаточны. |
| **Public schema** | Scalar view grammar прежняя; добавить versioned family witness: общий identity/context/full-vector preimage/layout, все views, одна связь с event/state root. Outer trace event может сохраниться. Старый `full-public-state.v1-candidate` не обозначает family. View body/root не являются подписываемыми bodies/QC. |
| **Fixtures** | Сохранить scalar leaf fixtures/native artifacts. Адаптировать relation/full-state traces к family witness: 4/8/8/8/8, потеря/перестановка координат, частичное принятие. Никаких дублированных votes/QC. |

**Переделать доказательства:** scalar-only whole-body bridge → family-to-one;
доказать покрытие, совместную инъективность, полный preimage и атомарное поднятие
действия. Корректности каждой `πₖ` недостаточно для единого vote/QC/WAL.

**Semantics:** только refinement representation/proof architecture по замыслу;
эквивалентность ещё не доказана. Независимое голосование по координатам было бы
изменением protocol semantics и не является B.

## Что сохраняется в обоих вариантах

Без изменения сохраняются теоремы `Quorum`/`FixedPoint`/`Hierarchy`,
`ParameterKernel`/`ApplyKernel`, native vector derivations, доказанные
identity/coordinate свойства, generic tagged encoding/ordering/set/update lemmas.
Их применение к новому whole-state bridge требуется обосновать.

B дополнительно сохраняет scalar body/input proofs **в прежнем scope**; A требует
vector-обобщений. Оба не решают автоматически прежнее расхождение native INT64/INT128
и public `ModelLimit`/symmetric result guard: wide success не означает limit127
acceptance. Полный recovery ещё не доказан; он остаётся прежним R3, не новым residual.

Включение A или B в mandatory Lean/TLA/schema изменит `formal_semantics_id` и
потребует совместимого evidence по прежним R4–R7. Это не обязательно изменение
native protocol. Принятие архитектурной развилки не меняет mandatory artifacts и не выдаёт GO.

## Рекомендация, не принятое решение

**B — минимальный по замене существующих scalar контрактов способ убрать
`shard.length = 1` из общего bridge без новых identities.** Исходный vector остаётся
целым; вместо length-one используется полный coordinate domain. Это минимум
изменений контрактов, не установленный минимум трудозатрат: синхронизация в B
нетривиальна. A прямее представляет whole body, но затрагивает больше schemas.

**Развилка принята пользователем; полная реализация A/B не разрешена.**
Для B отдельно подготовлен [impact estimate](0011-r2-b-impact-estimate.md).
Запрос этой оценки не являлся выбором B для реализации. После отдельно разрешённого
ограниченного spike новые proof layers снова остановлены.

Основания: [замороженный контракт](../../specs/000-formal-tla-spec/candidate-contract.md),
[refinement contract](../../specs/000-formal-tla-spec/refinement-contract.md),
[диагностика scalar API](../../formal/proposals/r2-domain-audit.md),
[проверенная minimal relation](../../formal/proposals/vector-shard-representation.md).
