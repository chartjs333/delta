# Delta ISC Sprint 16 — lane tasks

## Общий formal-first guard

База: `codex/feature000-binding-candidate@ea5a70d8c5fd3516de243632f2c5681b0e5a6292`.
Manifest branch: `agent/isc-s16-pipelined-sprint`.

Для всех lane запрещены production integration, снятие native guard, назначение `formal_semantics_id`/`σ_next`, миграция старых objects/signatures/QC/WAL, R2.3/R3 и незаявленное расширение scope. Любая необходимость выйти за ownership означает `STOP`.

## ISC-S16-A01 — contract freeze

**Branch:** `agent/isc-s16-contract-freeze`

Разрешено только:

- `docs/adr/0014-*.md`;
- `docs/adr/evidence/0014-isc-contract-freeze-v1.json`.

Задача:

1. Зафиксировать non-circular DAG `source profile → σ → E/e → R/r → V/v → M/sig/G/g → C/c/W1/evidence`.
2. Исключить concrete deployment E/R/V/G bytes и IDs из входа вычисления `σ`.
3. Согласовать статусы Commitment A, I-B, S-RANK, W1, P-EXPLICIT, SIG-ISC-ED25519-v1, ISC-EVIDENCE-BUDGET-v1 и Producer Integration.
4. Создать machine-readable checklist с base commit, решениями, открытыми obligations и запретами.
5. Не менять code, schemas, TLA, Lean, fixtures и build files.

## ISC-S16-B01 — W1 reference storage

**Branch:** `agent/isc-s16-w1-reference-engine`

Создать только quarantined `formal/reference/isc_w1/**`:

- encode/decode approved DRW1 kind-3 и четырёх W1 sections;
- checked lengths/counts/caps;
- fail-closed unknown kind/version, reserved bits, overflow, truncation, checksum, trailing bytes и section mismatch;
- opaque payload model без quorum/parent/signature/seed authority;
- file-backed append/barrier/reopen/scan/replay harness;
- fault injection: before append, partial append, complete append before barrier, barrier failure, surviving frame, corrupt/torn tail;
- round-trip, boundary ±1, mixed `1→2→3→2`, replay identity, physical-slot preservation и no silent tail repair;
- явный marker `REFERENCE_ONLY_NOT_PRODUCTION`.

Запрещено менять `delta-runtime-cpp/**`, `delta-core-cpp/**`, `delta-ffi/**`, `delta-node-java/**`, top-level build graph и approved W1 fields.

## ISC-S16-C01 — crypto reference/conformance

**Branch:** `agent/isc-s16-ed25519-reference`

Создать только quarantined `formal/reference/isc_crypto/**`:

- exact canonical K/E/R/V/M/G bytes;
- domain separation и identity-role separation b/c/v/g/r/e;
- detached Ed25519 conformance через уже доступную и явно проверенную библиотеку;
- deterministic synthetic vectors без deployment secrets;
- negative tests: wrong domain/V/r/key/epoch/validator, malformed lengths/encoding, role substitutions и bad signature forms;
- cross-language vector manifest, если две реализации уже доступны.

Запрещены production key custody, runtime/WAL integration, consensus invocation, vendoring/download fallback и новый trust root. При отсутствии нужной библиотеки — `STOP` по crypto execution.

## ISC-S16-D01 — formal linkage

**Branch:** `agent/isc-s16-formal-linkage`

Разрешены только TLA+/Lean и относящиеся formal fixtures/evidence:

- explicit parent binding;
- admission budget counters и conditional liveness;
- identity separation B/C/V/G/R/K/E;
- checked size equations;
- V→G relation и сохранение original physical slot без нового vote;
- mixed WAL mapping;
- mutants/negative fixtures для parent mismatch, budget ±1, ID-role swap, missing G и pre-barrier exposure;
- source-bound formal report со статусом GO либо честным NO_GO для ограниченного contract scope.

Запрещены production C++/Java/ABI, R2.3/R3, ослабление invariants и назначение `σ` до завершения dependency closure.

## Final branch check

Каждая lane обязана подтвердить:

- каталог `orchestration/sprints/isc-s16-pipelined/` полностью присутствует;
- sprint-файлы не изменены и не удалены;
- source baseline находится в ancestry;
- outcome содержит exact commit/provenance/tests/blockers.
