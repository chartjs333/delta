# Certified QLoRA mode on the qualified 8 GiB runner

Feature 009 adds `TrainingMode=QLORA_ADAPTER` as a specialization of the existing DeltaReduce
certificate graph. Python owns model loading and local adapter training, C++ remains the only
authority for certificate validation, fixed-point aggregation, adapter apply and the current
pointer, and Java transports only policy-approved immutable base and ApplyQC-certified adapter
objects.

The recorded hardware result is deliberately narrow. It proves one exact profile on one physical
NVIDIA GeForce RTX 3070 Laptop GPU with 8 GiB nominal VRAM. It does not claim that every 8 GiB
device, model, sequence length or software version will work, and it makes no model-quality claim.

## Immutable profile

The source of truth is `configs/qlora/8gb-reference.json`, whose SHA-256 is
`c7319d0c14ebc9af4667b91d92faba207b6ab0ae0cd6aa8a9e5d127d5f7ccb0d`. It pins:

- `microsoft/Phi-3.5-mini-instruct` revision
  `2fe192450127e6a83f7441aef6e3ca586c338b77`, public access and MIT license;
- NF4, double quantization, FP16 compute, rank 8, alpha 16 and all 128 ordered target modules;
- Python 3.12.1, PyTorch 2.6.0+cu124, Transformers 5.16.1, PEFT 0.20.0,
  bitsandbytes 0.50.2, Accelerate 1.14.0 and huggingface_hub 1.29.0;
- a domain-pure ticket with `B=2048`, `H=2`, sequence length 256, microbatch 1 and gradient
  accumulation 4;
- maximum reserved CUDA memory of 5.5 GiB, at least 512 MiB headroom and no CPU/disk offload.

Changing any of these values creates another profile and invalidates this qualification. Do not
edit the frozen file after execution or reuse its PASS for a different runner.

## Repository-safe model import

Do not commit weights, access tokens, license-acceptance credentials, private signing keys or an
external cache. Import only safetensors-backed, content-addressed data beneath an operator-approved
root. Pickle and remote model code are rejected.

```powershell
uv run delta qlora import `
  --manifest path\to\base-model-import.json `
  --allowed-root D:\operator-cas
```

The command validates the request and prints a `base_model_manifest_id`. It does not make the base
current. A base, tokenizer, quantization profile, adapter schema and parent adapter must all match
the `RoundConfig` before a ticket is admissible.

## Offline and native checks

The tiny fixture is a deterministic CPU gate and carries no physical-memory claim:

```powershell
uv run delta qlora train `
  --fixture delta-worker-python\tests\fixtures\models\tiny_qlora\manifest.json

cmake --preset cpp20
cmake --build --preset cpp20 --parallel 4 `
  --target delta_qlora_certificate_chain_test delta_qlora_apply_test delta_ffi_qlora_test
ctest --preset cpp20 -R qlora --output-on-failure
```

Repeat the native build and test with preset `cpp23`. The native tests cover the existing
ISC/EC/APC/ParameterShardQC/AggregateRootQC/ApplyQC lineage, exact adapter coverage, four-validator
byte equality, WAL/CAS recovery and bounded C ABI parity. No QLoRA-specific parallel QC type exists.

## Physical preflight and qualification

Run preflight immediately before qualification. It requires the exact GPU UUID, driver, compute
capability, nominal VRAM and at least 6 GiB free VRAM:

```powershell
out\qlora-physical-env\Scripts\delta.exe qlora preflight `
  --profile configs\qlora\8gb-reference.json
```

Keep the environment and Hugging Face cache outside tracked paths. Set deterministic CuBLAS before
the first CUDA forward, build `delta_ffi.dll` from the clean source HEAD, and execute the whole
ticket once:

```powershell
$env:HF_HOME = 'D:\delta\out\hf-cache'
$env:HF_HUB_CACHE = 'D:\delta\out\hf-cache\hub'
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
$env:DELTA_QLORA_PHYSICAL = '1'
$env:TOKENIZERS_PARALLELISM = 'false'

out\qlora-physical-env\Scripts\delta.exe qlora qualify `
  --profile configs\qlora\8gb-reference.json `
  --native-library out\build\cpp20\Debug\delta_ffi.dll `
  --output specs\009-qlora-8gb-mode\evidence\physical-qualification.json

uv run python specs\009-qlora-8gb-mode\scripts\verify_physical_qualification.py `
  --check-only
```

Qualification fails closed on profile/source drift, unavailable hardware, version mismatch,
non-finite loss or gradient, incomplete `B/H`, base mutation, non-adapter optimizer membership,
memory/headroom excess, host offload or native context mismatch. No contribution is eligible on a
failed or interrupted run.

## Recorded result

The committed exact-run evidence reports:

- 2 optimizer steps and 2048 processed tokens;
- identical base hashes before and after training;
- 12,582,912 FP16 adapter parameters and 100,663,296 bytes of FP32 AdamW moment state;
- 256 canonical `int16-fixed-v1` shards and commitment root
  `sha256:8556ae7c7dcece008e089300c0ffc533172ce2b18878ebcf83e97832d3499d00`;
- peak allocated memory 3,162,420,736 bytes and peak reserved memory 3,414,163,456 bytes;
- 5,175,771,136 bytes measured headroom and zero host offload.

The base stays cached by content ID. Later adapter fetches transfer only the certified adapter and
certificate bundle; worker-local shards, commitments and partial aggregates remain forbidden
distribution objects.

## Composition, resume and rollback

`qlora compose` validates the base, tokenizer, quantized profile, adapter schema, parent lineage and
ApplyQC before returning composition metadata. A mismatched resume fails unless a separately
certified migration exists. A merged export is a new derived immutable object with its own
provenance and never replaces the authoritative base-plus-adapter lineage.

To roll back, stop issuing new `QLORA_ADAPTER` tickets and retain the last ApplyQC-certified adapter
pointer. Never rewrite a frozen input set, restore an uncertified local adapter, mutate the base or
bypass native current-pointer CAS. An existing ApplyQC may be replayed idempotently to repair the
pointer after a crash.

## Evidence and telemetry

Operational telemetry includes mode/base/schema/profile IDs, ticket steps/tokens, adapter and q
bytes, CUDA peaks/headroom/offload, cache hit and transferred bytes, native certificate/apply result
and composition lineage. It must not include tokens, keys or raw training examples.

The physical result is in `specs/009-qlora-8gb-mode/evidence/physical-qualification.json`; its
independent exact-source verdict is `physical-gate.json`. The phase-level report remains explicitly
`REFINEMENT_ONLY` with `semantic_completeness_claimed=false`; inherited Formal GO, TLC and Lean
evidence are not replaced by this runtime qualification.
