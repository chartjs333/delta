# Feature Specification: Сжатый и шардированный delta protocol

**Feature Branch**: `004-compressed-delta-protocol`  
**Created**: 2026-08-21  
**Status**: Planned — ready for implementation  
**Depends on**: `003-central-round-coordinator`

## Summary

Uncompressed FP32 псевдоградиенты слишком велики для WAN. Функция вводит версионированные codecs `raw-fp32-v1`, `fp16-v1` и детерминированный blockwise `int8-v1`, безопасные shard envelopes и worker-local error feedback. Coordinator декодирует каждый принятый update в FP32 и сохраняет математический token-weighted reduce feature `003`.

Compression является transport representation, а не изменением определения локального или глобального псевдоградиента. Residual state принадлежит конкретному worker/schema/codec profile и коммитится только после однозначного принятия соответствующего encoded update.

## User Scenarios & Testing

### US1 — Сжать и восстановить локальный update (Priority: P1)

Worker кодирует FP32 delta по выбранному codec profile, разбивает payload на проверяемые shards и coordinator восстанавливает ordered FP32 tensors.

**Independent Test**: codec conformance fixtures дают байт-в-байт одинаковый encoded payload и dtype-aware bounded reconstruction error на CPU.

**Acceptance Scenarios**:

1. **Given** валидный `LocalDelta` и `int8-blockwise-v1`, **When** update кодируется, **Then** каждый block использует canonical scale/rounding, а manifest содержит codec/profile/schema и shard hashes.
2. **Given** encoded manifest и все shards, **When** decoder проверяет их, **Then** tensor names/shapes/order восстанавливаются до FP32 без unsafe deserialization.
3. **Given** отсутствующий, повторённый, повреждённый или oversized shard, **When** decode запущен, **Then** payload отвергается до выделения незаявленного объёма памяти.
4. **Given** all-zero block, **When** он кодируется, **Then** q-values равны нулю, decoder возвращает нули, и scale representation остаётся канонической.

### US2 — Сохранить потерянную при квантовании информацию (Priority: P1)

Worker применяет error feedback между последовательными принятыми раундами.

**Independent Test**: для последовательности fixture deltas выполняется `u_t=Δ_t+r_t`, `decoded_t=D(C(u_t))`, `r_{t+1}=u_t−decoded_t`; committed residual соответствует reference и не изменяется при rejected/timeout submission.

**Acceptance Scenarios**:

1. **Given** committed residual текущего profile, **When** создаётся candidate update, **Then** residual добавляется до compression.
2. **Given** coordinator принял encoded update и вернул matching receipt hash, **When** worker commit-ит результат, **Then** candidate residual атомарно становится current.
3. **Given** request потерял ответ, **When** worker retry-ит тот же update, **Then** повторно используется тот же encoded artifact/candidate residual, а residual не продвигается дважды.
4. **Given** update rejected либо round aborted до acceptance, **When** worker завершает transaction, **Then** current residual остаётся прежним.
5. **Given** parameter schema или codec profile изменился, **When** начинается следующий round, **Then** старый residual не применяется неявно; требуется explicit reset/migration policy.

### US3 — Агрегировать compressed updates без изменения reduce contract (Priority: P1)

Coordinator принимает workers с разными разрешёнными codecs, валидирует envelopes, декодирует в FP32 и выполняет тот же token-weighted reduce.

**Independent Test**: mixed-codec accepted set совпадает с direct reference, применяющим те же decoders и затем FP32 reduce; arrival/shard order не меняет результат.

**Acceptance Scenarios**:

1. **Given** raw, FP16 и INT8 updates одной schema, **When** round запечатан, **Then** каждый update декодируется независимо, а accumulator и outer optimizer остаются FP32.
2. **Given** codec/profile не входит в round allowlist, **When** update подан, **Then** coordinator отвергает его стабильной причиной.
3. **Given** manifest объявляет одно, а shard header другое profile/schema, **When** validation выполняется, **Then** update отвергается до reduce.

## Edge Cases

- NaN/Inf в source delta, scale или decoded tensor.
- Block с max absolute value 0, subnormal или близким к FP32 overflow.
- Tensor меньше block size или tensor, пересекающий shard size boundary.
- Tied/frozen/omitted parameters согласно schema feature `002`.
- Duplicate/out-of-order shards и decompression bomb metadata.
- Codec profile меняется между candidate creation и receipt.
- Worker crash между candidate write, upload, acceptance и residual commit.
- Coordinator restart во время lazy decode.
- Mixed codec versions в одном sealed set.
- Quantization metadata overhead на маленьких tensors.

## Requirements

### Functional Requirements

- **FR-001**: Codec API MUST быть versioned и включать `encode`, `decode`, `estimate_size`, conformance metadata и declared numerical contract.
- **FR-002**: Обязательные profiles MUST включать lossless `raw-fp32-v1`, `fp16-v1` и `int8-blockwise-v1`; round config задаёт allowlist.
- **FR-003**: `int8-blockwise-v1` MUST использовать фиксированный profile block size, signed values `[-127,127]`, FP32 scale `max_abs/127`, round-to-nearest-even и canonical zero-block encoding.
- **FR-004**: Decoder MUST выдавать ordered FP32 tensors и MUST проверять exact parameter schema до возврата результата.
- **FR-005**: Encoded update MUST состоять из canonical manifest и bounded-size shards с ordinal, declared byte length, SHA-256, tensor-segment table и codec metadata.
- **FR-006**: Shard parser MUST проверять limits до allocation и запрещать pickle, executable/object dtypes и незаявленные fields.
- **FR-007**: Source, quantization scale и decoded tensors MUST проходить finite checks; invalid update не публикуется и не агрегируется.
- **FR-008**: Sharding MUST детерминированно отображать parameter schema в segments; порядок доставки shards не влияет на decoded output.
- **FR-009**: Error-feedback state MUST быть keyed как минимум по worker ID, parameter-schema hash и exact codec-profile hash.
- **FR-010**: Candidate transaction MUST хранить input delta hash, prior residual version, encoded update hash и next residual hash.
- **FR-011**: Current residual MUST продвигаться только после accepted receipt, связанного с exact update hash; rejected/aborted/unknown outcome не должен автоматически продвигать state.
- **FR-012**: Idempotent retry MUST повторно использовать candidate bytes; повторное квантование одного logical update при неизвестном исходе запрещено.
- **FR-013**: Schema/profile change MUST требовать explicit `RESET`, проверенную migration или hard failure; silent residual reuse запрещён.
- **FR-014**: Coordinator intake MUST проверить codec allowlist, manifest/shard hashes, limits, schema/parent/round lineage и numerical validity.
- **FR-015**: Coordinator MUST decode accepted updates individually и выполнить canonical FP32 token-weighted reduce из feature `003`.
- **FR-016**: Global aggregate/checkpoint publication MUST записывать набор codec profiles и decoder implementation version, использованных для sealed set.
- **FR-017**: Compression metrics MUST включать raw/encoded bytes, ratio, encode/decode time, error norms, residual norm и per-shard sizes.
- **FR-018**: Codec conformance fixtures MUST быть committed и переносимы между реализациями/платформами.
- **FR-019**: API MUST позволять добавить новый codec под новым identifier без изменения существующих bytes/semantics.

### Non-Functional Requirements

- **NFR-001**: На committed large fixture `int8-blockwise-v1` SHOULD давать не менее 3.5× уменьшения полного encoded payload относительно raw FP32, включая metadata.
- **NFR-002**: Для каждого INT8 block maximum absolute reconstruction error MUST быть не больше `scale/2 + ε` при canonical input.
- **NFR-003**: Decode MUST быть streaming/bounded по declared shard limits и не требовать загрузки всех network bytes в один необ bounded buffer.
- **NFR-004**: Codec output MUST быть детерминированным внутри reproducibility class.
- **NFR-005**: Compression не должна менять token weights, round membership, outer optimizer formula или accepted-set semantics.
- **NFR-006**: CPU conformance path обязателен; accelerator kernels MAY оптимизировать, но обязаны проходить те же fixtures/tolerances.

### Key Entities

- **CodecProfile**: codec ID/version, block/shard parameters и numerical/size limits.
- **EncodedUpdateManifest**: lineage, schema/profile, shard table, raw/encoded hashes и summary.
- **EncodedShard**: bounded immutable bytes и tensor-segment descriptors.
- **ResidualState**: current committed error tensor set и version key.
- **CompressionCandidate**: two-phase relation prior residual→encoded update→next residual.
- **DecoderReceipt**: validated decoded hash/profile для coordinator evidence.

## Success Criteria

- **SC-001**: Raw/FP16/INT8 conformance fixtures кодируются детерминированно и декодируются в declared tolerances.
- **SC-002**: INT8 large-fixture payload достигает ≥3.5× ratio относительно raw FP32 с учётом metadata.
- **SC-003**: Error-feedback sequence совпадает с direct reference, а rejection/retry/crash tests не продвигают residual ошибочно.
- **SC-004**: Mixed-codec round совпадает с decode-then-FP32-reference reduce и не зависит от shard/arrival order.
- **SC-005**: Corrupted/missing/duplicate/oversized/mismatched shards и malicious metadata отвергаются bounded parser-ом.
- **SC-006**: Existing uncompressed round tests feature `003` продолжают проходить через `raw-fp32-v1` compatibility path.

## Assumptions

- Compression применяется worker-ом после построения canonical FP32 local delta.
- Первичный INT8 profile ориентирован на correctness, а не на максимальную kernel performance.
- Coordinator имеет достаточно памяти/streaming capacity для decode и FP32 accumulation на целевом prototype scale.
- Cryptographic signatures появятся в feature `008`; здесь целостность обеспечивается hashes и trusted membership.

## Out of Scope

- Top-K, PowerSGD, low-rank, 2-bit и entropy coding.
- P2P peer protocol и Merkle-piece distribution.
- Streaming overlap с продолжающимся training.
- Aggregation непосредственно в quantized domain.
- Residual migration между разными workers или parameter schemas.
