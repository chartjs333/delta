# ADR-0013 — Snapshot Provenance Contract v1

29 сентября 2026. T000–T003/T047/T053–T057. **DRAFT_FOR_APPROVAL — specification only.**

Архитектурное направление принято пользователем: production использует
ApplyQC/checkpoint-rooted snapshot provenance с независимо доверенными validator
set/epoch и защитой от rollback. Ниже предложен подробный contract; он ещё требует
утверждения. Это не разрешение реализации и не существующий Formal GO.

Source inventory: candidate `16fd8b25732b471132f56ae266e9e648c48187d1`.
Дополнительные policy/WAL types исследованы отдельно на native PR50 pin
`60c692f6e391f839829dfc64e93380db54cd507b`; они не объявляются merged candidate
или работающим demo. Предыдущие основания:
[provenance audit](0012-snapshot-provenance-audit.md),
[P1/P2 memo](0012-snapshot-provenance-decision-memo.md),
[EC identity ADR](0012-ec-context-identity-options.md).

## 1. Решение и граница authority

Целевая цепочка:

```text
independently trusted validator set / epoch / protocol origin
  -> authenticated existing ApplyQC and its exact parent certificate chain
  -> certified checkpoint/model/optimizer tuple
  -> verified binding to the complete snapshot cut and original bytes
  -> verified original WAL continuation
  -> recovered current, before READY or externally sendable effects
```

**ApplyQC остаётся единственным существующим BFT certificate, разрешающим
переход current.** Не вводятся SnapshotQC, backup quorum, новый vote kind или
право оператора самостоятельно сертифицировать current. Manifest — inventory
и средство связывания bytes, не параллельный certificate. Подпись transport peer
или автора backup не заменяет ApplyQC и не доказывает законность его истории.

Trusted configuration задаётся вне импортируемого пакета. Она связывает epoch,
validator identities с ключами и ролями, quorum policy и protocol/genesis/config
origin. Значения из snapshot можно сравнить с этой authority, но нельзя принять
их за authority потому, что тот же snapshot содержит согласованные подписи.

Контракт конкретизирует существующие certificate/authentication/recovery
obligations: [constitution](../../.specify/memory/constitution.md) III, VI, VII,
IX, X, XII; [feature 008](../../specs/008-certificates-and-consensus/spec.md)
FR-001–003, FR-015, FR-032–040;
[formal obligations](../../specs/000-formal-tla-spec/proof-obligations.md)
PO-AP1/PO-AP2/PO-R2; [ADR-0010](0010-hybrid-runtime-boundary.md).
Новый production trust contract заполняет установленный пробел, а не был скрыто
выполненной частью старого GO. Frozen R1–R7 не переписывается этим draft.

## 2. Точные существующие поля для переиспользования

Названия ниже — реальные поля исходников. «Переиспользовать» не означает, что
соответствующая полная provenance verification уже реализована.

| Существующий тип / источник | Поля | Что они дают и чего не дают |
|---|---|---|
| `certificates::Context`, [contracts.hpp](../../delta-core-cpp/include/delta/certificates/contracts.hpp) | `arithmetic_profile_id`, `height`, `parameter_schema_id`, `round_config_id`, `round_id`, `validator_epoch_id`, `view` | Exact round/epoch/config/schema/profile context; не устанавливает доверие к указанному epoch |
| `certificates::ApplyQc`, тот же файл; [008 schema](../../delta-protocol/schemas/008/apply-qc-v1.json) | `context`, `aggregate_root_qc_id`, `apply_arithmetic_profile_id`, `apply_candidate_id`, `next_model_hash`, `next_optimizer_hash`, `parent_checkpoint_id`, `quorum_threshold`, `signer_ids` | Certifies existing apply tuple. Canonical JSON также содержит `schema_version`, `formal_semantics_id`, `type_name`. В типе нет полного consensus snapshot root, WAL tip или signature bytes |
| `certificates::ApplyCandidate`; [schema](../../delta-protocol/schemas/008/apply-candidate-v1.json) | `context`, `aggregate_root_qc_id`, `apply_arithmetic_profile_id`, `next_model_hash`, `next_model_values`, `next_optimizer_hash`, `next_optimizer_values`, `parent_checkpoint_id`, `parent_optimizer_hash` | Связывает точные model/optimizer values и parent optimizer с candidate ID, на который ссылается ApplyQC |
| Existing `AggregateRootQc` / `ParameterShardQc` / APC / EC / ISC | Root QC: `leaves`, `merkle_root`, `required_keys`, `aggregation_plan_certificate_id`, `eligibility_certificate_id`, `input_set_certificate_id`; shard QC: `domain_id`, `shard_id`, `input_leaf_ids`, `result_numerators`, `denominator` и те же parents; прочие certificate IDs/context/signers сохраняются | Используются исходные полные bodies и их parent graph. Нельзя заменить QC его body alias или отбросить signer variants |
| `ValidatorPolicy`, [verifier.hpp](../../delta-core-cpp/include/delta/certificates/verifier.hpp); `QuorumPolicy`, [consensus.hpp](../../delta-core-cpp/include/delta/core/consensus.hpp) | `validator_epoch_id`, `validator_ids`, `quorum_threshold` | Existing membership/quorum representation. Нет полного authenticated key/role registry в этих структурах |
| `Vote`, [protocol.hpp](../../delta-core-cpp/include/delta/core/protocol.hpp) | `body_hash`, `context_id`, `durable_sequence`, `height`, `kind`, `round_id`, `signature_id`, `validator_epoch_id`, `validator_id`, `view` | Exact original vote identity/context/sequence; `signature_id` — ссылка, а не сама проверка подписи |
| `QuorumCertificate`, тот же файл | `body_hash`, `context_id`, `height`, `kind`, `qc_id`, `quorum_threshold`, `round_id`, `signer_ids`, `validator_epoch_id`, `view`, `vote_ids` | Existing signed-vote evidence links. Связь этого generic QC с конкретным typed ApplyQC должна проверяться по исходному signing body; она не следует из совпадения signer IDs |
| `CurrentPointerCommand`; [schema](../../delta-protocol/schemas/008/current-pointer-command-v1.json) | `context`, `apply_qc_id`, `expected_parent_checkpoint_id`, `next_checkpoint_id`, `next_optimizer_hash` | Existing authorized current transition |
| `PointerState`, [certificate_runtime.hpp](../../delta-runtime-cpp/include/delta/runtime/certificate_runtime.hpp) | `checkpoint_id`, `optimizer_id`, `apply_qc_id`, `height` | Existing certified-current tuple. Не независимый rollback floor, если восстановлен из того же backup |
| `RoundState`, [protocol.hpp](../../delta-core-cpp/include/delta/core/protocol.hpp) | `available_ticket_count`, `committed_ticket_count`, `config_id`, `durable_sequence`, `height`, `parent_checkpoint_id`, `phase`, `round_id`, `state_root`, `ticket_count`, `view` | Round-state bytes; не полный certificate/candidate/environment snapshot |
| `Snapshot`, `JournalEntry`, [wal.hpp](../../delta-runtime-cpp/src/wal.hpp) | Snapshot: `journal_sequence`, `state_bytes`; entry: `sequence`, `kind`, `command_or_vote_bytes`, `next_state_bytes`, `effect_batch_bytes`, `wal_record_bytes` | Existing exact WAL/snapshot bytes и физическая последовательность записей. Не authority происхождения base |
| `WalRecord`, [protocol.hpp](../../delta-core-cpp/include/delta/core/protocol.hpp) | `command_id`, `effect_batch_id`, `next_state_root`, `prior_state_root`, `record_kind`, `round_id`, `sequence` | Existing replay edges; sequence не переименовывается в vote sequence или checkpoint height |
| `EffectBatch`, тот же файл | `effects`, `next_state_root`, `prior_state_root`, `request_id`, `round_id` | Existing effect identity; восстановление не создаёт новую identity для того же эффекта |
| PR50 `VoteAdmissionSnapshot`, `VoteAdmissionPolicy`, `Config` | `snapshot.state_id`, полные 33 policy collections/metadata; `local_validator_id`, `validator_epoch_id`, `validator_ids`, `role`, `round_id`, `round_config_id`, deadlines; `initial_state_bytes`, `vote_policy`, `expected_wal_identity` | Полная исходная inventory обязательна там, где она входит в cut. `state_id` хэширует RoundState, а не все collections. `expected_wal_identity` связывает file descriptor с локальным файлом, не сертифицирует состояние |
| [artifact-ref](../../delta-protocol/schemas/artifact-ref.schema.json) | `byte_length`, `content_id`, `locator`, `media_type`, `schema_id`, `schema_version` | Повторно используемые content refs. Locator — местоположение, не trust; hash проверяется на полученных bytes |
| [GLOBAL_ADAPTER_CHECKPOINT](../../delta-protocol/schemas/009/global-adapter-checkpoint-v1.json) | `adapter_parameter_schema_id`, `aggregate_root_qc_id`, `apply_qc_id`, `base_model_manifest_id`, `next_adapter_id`, `next_outer_optimizer_state_id`, `parent_adapter_id`, `quantized_base_profile_id`, `training_mode_id` | Существующие ссылки adapter checkpoint на ApplyQC, не новый BFT certificate и не complete runtime snapshot |

Полная PR50 inventory `VoteAdmissionSnapshot` сохранена в исходном типе на
указанном pin: `state_id`, `parameter_schema_id`, `arithmetic_profile_id`,
`required_accumulator_proof_id`, `proposed_round_config_ids`,
`finalized_round_config_ids`, `closed_input_set_ids`, `input_set_bodies`,
`input_set_certificates`, `finalized_input_set_ids`, `seed_transcripts`,
`norm_evidence`, `eligibility_bodies`, `eligibility_certificates`,
`finalized_eligibility_ids`, `aggregation_plan_bodies`,
`aggregation_plan_certificates`, `finalized_aggregation_plan_ids`,
`parameter_bodies`, `parameter_qcs`, `finalized_parameter_ids`,
`required_parameter_keys`, `aggregate_root_bodies`, `aggregate_root_qcs`,
`finalized_aggregate_root_ids`, `apply_profiles`, `apply_candidates`, `apply_qcs`,
`finalized_apply_ids`, `timeout_observations`, `view_change_bodies`,
`abort_requests`, `abort_bodies`. Source/configuration/aliases/units, если вынесены
из этого типа, входят через исходные referenced artifacts, не исчезают из cut.

Отдельно: [training checkpoint manifest](../../delta-protocol/schemas/checkpoint-manifest.schema.json)
с `checkpoint_id`, `boundary=OPTIMIZER_STEP`, `optimizer_step`, `processed_tokens`,
`run_id`, `sampler_cursor`, `step`, `artifacts` обслуживает training resume.
Его `checkpoint_id` — label. Он не становится consensus checkpoint authority
из-за общего слова checkpoint.

## 3. Какие bindings действительно отсутствуют

### 3.1. Различать model hash и полный snapshot root

В [CurrentPointerStore::advance](../../delta-runtime-cpp/src/certificate_runtime.cpp)
уже требуется `next_checkpoint_id == ApplyQc.next_model_hash`, совпадение
optimizer и exact ApplyQC/context, parent CAS или exact idempotent replay.
[ChainVerifier::verify_apply](../../delta-core-cpp/src/certificates/verifier.cpp)
проверяет candidate ID, parents, profiles, tuple и signer policy. Это не проверка
происхождения всего начального snapshot. Сам `validate_signers` проверяет
membership/threshold; проверку настоящих подписей нельзя подменить этим вызовом.

`RoundState.state_root` также нельзя объявить полным snapshot root: существующий
[FINALIZE_AGGREGATE](../../delta-core-cpp/src/transition.cpp) присваивает ему
`command.body_hash`. Хэш `state_bytes`, full policy hash и model hash — разные
объекты. Никакое из этих значений не переинтерпретируется данным contract.

`parent_checkpoint_id` также не является ссылкой на previous ApplyQC ID.
Совпадение model hash, особенно при повторении тех же model bytes на другой
высоте, не доказывает exact checkpoint ancestry. Нужна проверенная исходная
цепочка current transitions с полными checkpoint/optimizer/QC/height tuples.
Если пакет её не предоставляет, нельзя достроить ancestry только по model hash.

### 3.2. Минимальный предлагаемый binding без нового certificate protocol

Для v1 предлагается **проверяемое выведение complete cut из исходной native
истории**, а не утверждение, будто ApplyQC подписывает произвольный manifest:

1. Существующий ApplyQC удостоверяет ровно свой tuple; его полная certificate
   chain и реальные votes/signatures проверяются относительно независимой epoch
   authority. Сохраняются исходные QC IDs и варианты signer sets.
2. Данные complete cut воспроизводятся source-only проверкой исходного producing
   prefix от independently pinned protocol genesis либо ранее так же проверенного
   cut. Parent checkpoint и все current advances должны соответствовать valid
   ApplyQC. Для каждого imported field требуется исходное producing event или
   разрешённая genesis/configuration запись; нельзя просто загрузить prefilled
   policy и проверить suffix от неё.
3. Manifest связывает именно полученные полные bytes, inventory и cut boundaries.
   Сравнение производится с результатом этой проверки. Manifest hash фиксирует
   bytes, но не добавляет authority. Произвольная самосогласованная пара
   `manifest + snapshot` проверку не проходит.

Это **derived binding**, а не подпись ApplyQC под consensus snapshot root.
ApplyQC root и local producer/WAL evidence совместно обосновывают state; один QC
не удостоверяет private votes, потерянные local records или чужую durable history.
Для локальных наблюдений остаются явно названные faithful durable-observation
и authentication abstractions, не предположение «готовый public state корректен».

Полный independent producer/checker сейчас не установлен предыдущим audit.
Этот текст задаёт требуемую обязанность будущей проверки, **не доказывает её
выполнимость имеющимися actions**. Повторное исполнение arbitrary admission API
не заменяет production producing history. Если её нельзя независимо задать или
она допускает прежний EC mismatch, R2.3 остаётся OPEN и нужен отдельный STOP.

Если нужен **компактный, непосредственно quorum-certified full-state root без
этой истории**, существующего ApplyQC недостаточно. Потребуется отдельно
утвердить добавление binding в существующий signed ApplyCandidate/ApplyQC
contract с изменением соответствующих IDs/semantics и requalification. Такое
изменение, SnapshotQC или подпись нового backup quorum здесь не выбираются.

### 3.3. Минимальные дополнительные данные — пока не schema

| Conceptual данные / binding | Что переиспользуется | Что недостаёт |
|---|---|---|
| Independent epoch authority | `validator_epoch_id`, `validator_ids`, `quorum_threshold`, config/profile IDs, existing signer identities | Authenticated key/role/status binding для epoch, protocol-origin pin и его независимый канал получения. Snapshot не может быть этим каналом |
| Apply authentication evidence | Existing ApplyQc/ApplyCandidate, generic vote/QC refs, `signature_id`, original canonical bytes | Проверяемое соответствие точного signing payload/context typed ApplyQC и подписи зарегистрированного ключа. Не предполагать `Vote.body_hash == content_id(ApplyQc)`: QC включает signer set и отличается от голосуемого body |
| Versioned import manifest | Existing artifact-ref и protocol/schema/formal version identifiers; exact original certificate/config refs | Inventory complete state/policy/source/aliases/units и их byte hashes; reference на exact ApplyQC/current tuple; declared cut; producer-history evidence refs. Каноническое encoding ещё нужно утвердить |
| Cut/WAL association | Existing actor IDs, `journal_sequence`, `JournalEntry.sequence`, original vote sequences, pointer tuple | Per-actor journal identity, byte ranges/lengths/content refs, base/tip и их cut association; completeness/unknown status. Snapshot cut и WAL continuation должны быть одной историей, а не двумя подходящими хэшами |
| Independent rollback floor | Existing `PointerState` tuple и authenticated epoch/config origin | Durable monotone trusted anchor, недоступный замене из import package, и verified ancestor/descendant binding. Существующий pointer WAL сам по себе не даёт это свойство при откате всего каталога |
| Activation record | Existing exact artifact/QC IDs, WAL positions, current tuple | Crash-safe связь выбранного manifest/cut, verified anchor и active local generation. Это local durability metadata, не новый vote/certificate и не перенумерация consensus WAL |

Схемы с `additionalProperties:false` не расширяются «незаметными» полями.
Новые данные — proposed manifest/local trust metadata вокруг existing objects;
certificate bytes/domain hashes и WAL entries остаются исходными. U64 native
поля и ограниченные JSON numeric ranges нельзя молча смешивать: encoding обязан
сохранять exact integers и действующие bounds, без округления.

## 4. Процедура проверки imported snapshot

Последовательность ниже — specification будущего native import/recovery path;
ни одного нового runtime entry point в этом изменении нет.

1. **Stage, не activate.** Читать пакет в отдельное immutable staging состояние;
   ограничить размеры, проверить canonical decoding и supported exact versions.
   Не изменять active current, trust store, vote journal, keys или WAL из
   candidate paths. Не доверять executable instructions/locator как authority.
2. **Загрузить independent trust.** Получить pinned origin/config, epoch key/role
   policy и уже известный trusted anchor/floor из отдельного источника. Нет
   нужной authority — import остаётся blocked; нельзя извлечь её из пакета.
3. **Проверить original certificate graph.** Проверить полный signing context,
   authentic signatures, unique eligible signers, exact quorum policy, epoch,
   profiles и parent links до ApplyQC/candidate/root/shard/APC/EC/ISC по existing
   rules. `signer_ids` и checksum недостаточны. Не создавать coordinate-level
   shards/votes/QCs и не нормализовать разные native QC IDs в одну identity.
4. **Проверить checkpoint artifacts.** ApplyCandidate hash/values, model и
   optimizer bytes должны соответствовать ApplyQC, parent checkpoint/optimizer,
   config/profile. Current tuple должен совпасть с разрешённым pointer command.
   Hash manifest не заменяет этой проверки.
5. **Проверить ancestry и rollback floor.** Candidate checkpoint должен быть
   exact known anchor либо его проверенным потомком. Старый ancestor, fork,
   другая origin/epoch lineage или недоказанное родство отвергаются. Больший
   height сам по себе не ancestry. Переход epoch допустим только при независимо
   проверенной authority следующего epoch, не по assertion внутри snapshot.
6. **Вывести complete cut (§3.2).** Проверить native producing prefix, original
   inventory и все поля, включая nonempty downstream lineage, unfinalized
   candidates/environment и sufficient ABORT. Сопоставить exact bytes/hash с
   manifest. Legal transitions не определяются успехом R2 projection.
   Отсутствующее происхождение хотя бы required collection не лечится очисткой.
7. **Связать journals.** Проверить исходные per-actor records/cut/ranges,
   multiplicity, command/vote/effect identities, parents и последовательности.
   Imported remote journal не становится own signer journal. Сохранить всё
   собственное уже durable vote intent, включая durable-but-unexposed записи.
   Отсутствие копии не равно доказанному отсутствию записи.
8. **Проверить continuation.** Воспроизвести exact native WAL suffix от
   установленного cut, проверяя prior/next state, effects, policy binding и
   authorized current advances. Unknown, gap, incompatible bytes, bad checksum,
   missing dependent certificate или unresolved torn tail не разрешают READY.
9. **Recheck и durable activation.** На single-writer boundary повторно сверить
   current trusted floor/generation, чтобы concurrent anchor update не сделал
   staging устаревшим. Durable commit связывает selected cut/manifest, полные
   retained journals, anchor и active generation; конкретный layout ещё требует
   решения. Новый active state не публикуется раньше durability barrier.
10. **Recovered current.** Только после согласованного durable recovery record
    разрешать runtime READY/дальнейшие commands/effects. Не переиздавать старый
    vote под новым sequence, не считать replay новой delivery. Любой fail closed
    оставляет прежний безопасный active state либо RECOVERING/BLOCKED; не
    создаёт новый protocol ABORT и не меняет current по усмотрению оператора.

До атомарной активации должен проверяться тот же неизменённый набор bytes,
который станет active; нельзя проверить одни файлы, затем загрузить другие.
Весь импорт idempotent по exact identities и complete cut. Существующий
CurrentPointerStore признаёт replay по exact `apply_qc_id`; новая эквивалентность
разных QC signer variants данным contract не вводится.

## 5. Bootstrap trust и сохранение собственной identity

Новый узел предварительно получает independently authenticated enrollment:
origin/genesis/config pin, epoch membership/keys/roles/quorum и допустимый minimum
checkpoint anchor. Канал provisioning может быть offline authenticated config
или уже доверенный control-plane root; конкретный канал/issuer — решение deployment.
Transport TLS и файл из пакета могут доставлять данные, но не создавать этот root.

Только validator keys/epoch позволяют проверить подписи старого QC, но не узнать,
что он самый новый. Для bootstrap freshness нужен independently supplied anchor
или отдельно утверждённая freshness policy. V1 обещает rollback protection
**относительно уже известного trusted floor**, не знание глобально последнего
checkpoint без внешнего источника. Нельзя выдавать height самого snapshot за floor.

Для первого непустого imported snapshot требуется valid ApplyQC. Пустой protocol
genesis/Init остаётся отдельным existing starting point. Вопрос импорта непустых
pre-first-ApplyQC cuts требует отдельного решения; этот draft не объявляет их
разрешёнными. Он также не удаляет из frozen R2/R3 локальные initial/incomplete
states, полученные законным исполнением от Init, до первого ApplyQC.

Восстановление существующего validator identity требует continuity его
собственного vote journal/anchor. Копия состояния другого участника не даёт
права начать с пустым журналом под старым local signer. New-node state transfer
не импортирует чужие private keys или durable vote authority; узел должен уже
иметь полномочия по existing epoch enrollment. Protocol membership не меняется
посредством snapshot import.

## 6. Rollback protection

- Known anchor фиксирует как минимум origin/epoch и exact
  `(height, checkpoint_id, optimizer_id, apply_qc_id)` с authenticated ancestry.
  Сравнение проводится по certified chain, не только по height или lexical epoch.
- Older once-valid checkpoint не принимается как active imported base при
  известном более новом floor. Larger-height fork также отвергается. Можно
  сохранить rejected bytes для диагностики, не активировать их.
- Floor нельзя уменьшить через import/restart/config default. Missing или
  повреждённый floor у ранее enrolled validator не означает «fresh bootstrap».
- Смена epoch требует отдельно authenticated mapping/transition; snapshot не
  разрешает revocation override или self-selected quorum. До такой authority
  cross-epoch import блокируется, даже если подписи внутренне согласованы.
- Floor должен переживать replacement/rollback импортируемого storage. Один
  fsync-файл рядом со snapshot защищает от части crashes, но не от восстановления
  обоих файлов из старого backup. Нужен independently retained monotone anchor
  (например, hardware-backed store или independently trusted external pin).
  Конкретный механизм и threat boundary подлежат утверждению; ни один сейчас
  не считается реализованным.

Offline reconstruction из старого checkpoint с последующим catch-up мог бы быть
отдельной оптимизацией, но не является выбранным разрешением принять старый
import. V1 не обходит требуемый fail closed таким fallback.

## 7. Crash/recovery semantics

| Crash / observation | Обязательный результат предлагаемого contract |
|---|---|
| До завершения verification/durability | Staging не authority; прежние trusted anchor/current/journals не изменены |
| Verified staging, но trusted floor успел вырасти | Повторная ancestry проверка; stale candidate не активируется |
| Новый floor durable, active generation ещё не опубликована | Recovery завершает ту же verified activation либо остаётся RECOVERING; не возвращается к serving старого current ниже floor |
| Active bytes найдены, но durable anchor/activation association отсутствует или противоречива | Fail closed, без votes/effects; не восстанавливать trust из этих же bytes |
| Activation durable, ответ/эффект ещё не выдан | Exact idempotent recovery по сохранённой identity; новый vote/effect identity не создаётся |
| WAL durable, effect не exposed; либо exposure неизвестна | Сохраняются original entry/sequence/intent и distinction durable/exposed/sent/delivered; unknown не становится confirmed delivery |
| Partial tail, gap, missing policy/certificate/local vote evidence | Не READY до обоснованного recovery допустимого prefix; не удалять intact lineage и не фабриковать отсутствие записей |

Existing reader имеет правила локального torn-tail recovery. Это не blanket
разрешение импортёру усечь любой неудобный suffix. Для принятого prefix должны
быть согласованы declared cut, durability observations, dependencies и floor;
физические failure assumptions остаются явными. Исходные logical WAL sequences,
vote sequences и journal multiplicity сохраняются; local activation metadata
не вставляется задним числом в consensus WAL.

При разных durability domains anchor store и runtime storage atomicity нельзя
объявить одним словом «rename». Layout должен обеспечивать описанные cases
при любом crash; при неопределённости допустима недоступность, не rollback.
Это future recovery obligation R3, а не уже полученный результат.

## 8. Владельцы проверки и влияние на R2/R3

| Существующий компонент | Роль после утверждения contract; чего сегодня не следует заявлять |
|---|---|
| Native certificate verifier / `delta-core-cpp` | Pure canonical/context/parent/quorum/key-evidence validation; не читает filesystem/network и не выбирает trust root из candidate |
| `delta-runtime-cpp`, snapshot/WAL reader, durable vote journal, `CurrentPointerStore` | Единственный владелец staged import, continuity, retained own journals, trusted-floor/activation integration и recovery readiness; существующая local replay проверка не есть весь contract |
| Node enrollment/configuration и independent trust provider | Доставляют authenticated root/epoch/keys/minimum anchor; не получают право unilateral current advancement |
| Java transport / FFM / sidecar | Переносят opaque bytes и выделенные transport-auth facts; не пересобирают consensus state и не авторизуют Apply/current |
| Python training/checkpoint tools | Дают exact model/optimizer artifact bytes; training checkpoint не заменяет ApplyQC |
| Formal source witness / refinement machinery | Independent source origin проверяется до family projection; вывод public correctness и preservation остаётся R2/R3 |

**Как закрывается MISSING SNAPSHOT PROVENANCE CONTRACT:** после утверждения
появится явная спецификация authority, цепочки bindings, bootstrap, known-floor
и fail-closed recovery. Исчезнет неоднозначность, можно ли считать произвольный
hash-consistent supplied snapshot авторитетным: нельзя. Однако закрытие
архитектурной неопределённости документацией не означает реализацию verifier
или CLOSED у R2.3. Detailed binding/decisions §9 и их проверяемое исполнение
нельзя заменить этой формулировкой.

Domain будущего R2 должен выводиться из original native history, independently
authenticated ApplyQC/checkpoint/configuration и faithful durable evidence.
Ни public well-formedness, ни успешность family constructor, ни equality
recovered native/public state не входят в provenance authority. Поэтому здесь
не предполагается искомый результат R2. Но из этого ещё не доказано, что все
native states нового domain имеют нужное public отображение.

| Результат / артефакт | Статус и влияние |
|---|---|
| R1, R2.1/R2.2, scalar/family arithmetic, constructor/domain lemmas | Остаются user-accepted CLOSED/действительными в исходных statements; без конкретного контрпримера не переоткрываются |
| R2.3 full static relation | OPEN. Нужно связать источник complete cut с уже замороженной source/config/aliases/units, collections/current/environment и initial/incomplete/ABORT relation. Новый trust root не исправляет EC identity mismatch автоматически |
| R3 `nativeArithmeticRecoveryRefines` | Не начат. Будущий statement должен включать approved native base provenance, floor/activation и прежние exact replay/unknown/crash obligations; нельзя принять recovery equality как premise |
| `NativeReplayAdmission.prepareWhole`, `NativeConfigReplay`, `NativeArithmeticHistory`, `NativeCurrentHistory` | Existing conditional decode/history/replay components могут переиспользоваться; их supplied initial state не превращается в доказанную independent origin. Новая sufficiency/composition ещё не доказана |
| Public snapshot/export/certificate authentication assumptions | Требуется явное source-to-trust dependency binding. Named Boolean authentication premise не становится полным origin verifier по переименованию |
| Production TLA `Init/Next`, `CertificateVoteUniqueness`, apply/current safety | В этом docs-only изменении неизменны; не заявлено их опровержение. Если contract implementation требует новой externally visible transition, signed context или terminal, formal-first STOP и отдельное решение |
| Existing Lean/TLC/mutant/fixture/WAL evidence | Исторические результаты на pinned sources не инвалидируются этим draft. Они **не квалифицируют** будущий import/anchor/producer checker. После разрешённых изменений source-bound affected gates/report должны быть пересобраны; старый PASS не переносится на новые bytes |
| Frozen DoD / report / article claims | R1–R7 не расширяется новым самостоятельным gate. Добавляется явно согласуемый trust contract в прежний initial/recovery scope. Нельзя заявлять arbitrary-backup recovery, globally freshest bootstrap, actual antirollback либо completed R2/R3/GO до corresponding evidence |

Полного текста статьи в checkout не установлено; последняя строка задаёт
ограничения claims, а не цитирует или редактирует неизвестный текст статьи.
Blast radius после approval: source/authority witness и R2/R3 statements,
future native import/recovery/anchor integration, configuration/enrollment,
manifest binding и source-bound evidence. Это существенное уточнение production
trust boundary, не cosmetic doc fix. R4–R7 сейчас не запускаются; runtime guard
остаётся до exact merged compatible FormalVerificationReport(GO).

## 9. Отдельные решения до реализации

Это конечный список развилок данного contract, не новые residual R8+:

1. **Full-state binding:** утвердить предложенный §3.2 independently verified
   native-history route и его source/version base. Либо явно выбрать direct
   certificate commitment к full-state root с отдельным semantic impact.
   Отсутствие полного producer contract нельзя скрыть под словом «replay».
2. **Epoch/key/bootstrap authority:** определить реально используемый trusted
   issuer/config origin, mapping IDs→keys/roles/status, minimum anchor provisioning
   и разрешённый способ epoch transition. До этого unsupported epoch fail closed.
3. **Rollback threat boundary и storage:** выбрать independent monotone floor
   mechanism и crash-safe activation layout. Whole-machine/backup rollback
   защищён только в той мере, в какой не откатывается этот независимый источник.
4. **Genesis и new-node profiles:** определить допустимость nonempty
   pre-first-ApplyQC import и процедуру старта нового enrolled signer без чужой
   journal authority. Existing identity с потерянной own history не получает
   автоматического reset. Local lawful Init histories остаются formal scope.
5. **Concrete encoding/evidence delivery:** утвердить canonical manifest/cut
   encoding и точную existing signed-vote→typed ApplyQC evidence association,
   complete-source/WAL inventory и integer bounds. Не изобретать новый crypto
   primitive или parallel quorum, не менять original IDs по умолчанию.

Если нужный full-state binding невозможно обеспечить без изменения production
`Init/Next`, certificate semantics или WAL identity, отдельный архитектурный
STOP остаётся обязательным. Этот ADR не предоставляет такое разрешение.

**STOP после specification.** Код, proofs, TLA, schemas, fixtures, normative
candidate/DoD и старые evidence не изменены. R2.3/R2 OPEN; R3 не начат.
Ожидается утверждение подробного contract и отдельная scoped команда на работу.
