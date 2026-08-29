"""Preregistered physical 8 GiB QLoRA qualification harness."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id
from deltatorrent.qlora.backend import _logical_tensor_hash
from deltatorrent.qlora.contribution import encode_adapter_contribution

PROFILE_SHA256: Final = "c7319d0c14ebc9af4667b91d92faba207b6ab0ae0cd6aa8a9e5d127d5f7ccb0d"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


class QualificationError(RuntimeError):
    """Physical gate failure that cannot produce an eligible claim."""


@dataclass(frozen=True, slots=True)
class GpuObservation:
    name: str
    uuid: str
    total_memory_bytes: int
    free_memory_bytes: int
    driver_version: str
    compute_capability: str


class _Fp32StateAdamW:
    """Adapter-only AdamW with the two FP32 moments budgeted by preflight."""

    def __init__(self, parameters: list[Any], torch: Any, *, learning_rate: float) -> None:
        if not parameters or learning_rate <= 0:
            raise QualificationError("PHYSICAL_OPTIMIZER_CONFIGURATION_INVALID")
        self.parameters = parameters
        self._torch = torch
        self._learning_rate = learning_rate
        self._step = 0
        self._first_moments = [
            torch.zeros_like(parameter, dtype=torch.float32) for parameter in parameters
        ]
        self._second_moments = [
            torch.zeros_like(parameter, dtype=torch.float32) for parameter in parameters
        ]

    @property
    def state_bytes(self) -> int:
        return sum(
            value.numel() * value.element_size()
            for value in (*self._first_moments, *self._second_moments)
        )

    def zero_grad(self) -> None:
        for parameter in self.parameters:
            parameter.grad = None

    def step(self) -> None:
        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8
        self._step += 1
        bias_correction1 = 1.0 - beta1**self._step
        bias_correction2_root = math.sqrt(1.0 - beta2**self._step)
        with self._torch.no_grad():
            for parameter, first, second in zip(
                self.parameters, self._first_moments, self._second_moments, strict=True
            ):
                if parameter.grad is None:
                    raise QualificationError("PHYSICAL_ADAPTER_GRADIENT_MISSING")
                gradient = parameter.grad.float()
                if not self._torch.isfinite(gradient).all():
                    raise QualificationError("PHYSICAL_ADAPTER_GRADIENT_NONFINITE")
                first.mul_(beta1).add_(gradient, alpha=1.0 - beta1)
                second.mul_(beta2).addcmul_(gradient, gradient, value=1.0 - beta2)
                denominator = second.sqrt().div_(bias_correction2_root).add_(epsilon)
                update = first.div(denominator).mul_(self._learning_rate / bias_correction1)
                parameter.copy_((parameter.float() - update).to(parameter.dtype))
                if not self._torch.isfinite(parameter).all():
                    raise QualificationError("PHYSICAL_ADAPTER_UPDATE_NONFINITE")


def _run(*args: str) -> str:
    return subprocess.run(
        args, check=True, capture_output=True, encoding="utf-8", errors="replace"
    ).stdout.strip()


def load_profile(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROFILE_SHA256:
        raise QualificationError("FROZEN_PROFILE_HASH_MISMATCH")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != "1.0.0":
        raise QualificationError("FROZEN_PROFILE_INVALID")
    return value


def probe_gpu() -> GpuObservation:
    fields = _run(
        "nvidia-smi",
        "--query-gpu=name,uuid,memory.total,memory.free,driver_version,compute_cap",
        "--format=csv,noheader,nounits",
    ).splitlines()
    if len(fields) != 1:
        raise QualificationError("EXACTLY_ONE_PHYSICAL_GPU_REQUIRED")
    parts = [item.strip() for item in fields[0].split(",")]
    if len(parts) != 6:
        raise QualificationError("NVIDIA_SMI_OUTPUT_INVALID")
    return GpuObservation(
        name=parts[0],
        uuid=parts[1],
        total_memory_bytes=int(parts[2]) * 1024 * 1024,
        free_memory_bytes=int(parts[3]) * 1024 * 1024,
        driver_version=parts[4],
        compute_capability=parts[5],
    )


def validate_physical_readiness(profile: dict[str, Any], gpu: GpuObservation) -> None:
    expected = profile["runner"]["gpu"]
    exact = {
        "GPU_NAME": (gpu.name, expected["name"]),
        "GPU_UUID": (gpu.uuid, expected["uuid"]),
        "GPU_TOTAL_MEMORY": (gpu.total_memory_bytes, expected["total_memory_bytes"]),
        "GPU_DRIVER": (gpu.driver_version, expected["driver_version"]),
        "GPU_COMPUTE_CAPABILITY": (gpu.compute_capability, expected["compute_capability"]),
    }
    for field, (actual, wanted) in exact.items():
        if actual != wanted:
            raise QualificationError(f"PHYSICAL_{field}_MISMATCH:{actual}:{wanted}")
    minimum = int(profile["memory"]["required_minimum_available_at_start_bytes"])
    if gpu.free_memory_bytes < minimum:
        raise QualificationError(
            f"PHYSICAL_AVAILABLE_MEMORY_INSUFFICIENT:{gpu.free_memory_bytes}:{minimum}"
        )


def _software_versions(profile: dict[str, Any], torch: Any) -> dict[str, str]:
    names = {
        "accelerate": "accelerate",
        "bitsandbytes": "bitsandbytes",
        "huggingface_hub": "huggingface_hub",
        "peft": "peft",
        "transformers": "transformers",
    }
    actual = {name: importlib.metadata.version(package) for name, package in names.items()}
    actual["pytorch"] = str(torch.__version__)
    actual["cuda_runtime"] = str(torch.version.cuda)
    actual["python"] = platform.python_version()
    expected = profile["software"]
    for name, value in actual.items():
        if value != str(expected[name]):
            raise QualificationError(f"SOFTWARE_VERSION_MISMATCH:{name}:{value}:{expected[name]}")
    return actual


def _source_observation() -> dict[str, object]:
    commit = _run("git", "rev-parse", "HEAD")
    tree = _run("git", "rev-parse", "HEAD^{tree}")
    dirty_paths = _run("git", "status", "--porcelain=v1").splitlines()
    if dirty_paths:
        raise QualificationError("PHYSICAL_SOURCE_TREE_NOT_CLEAN")
    return {"commit": commit, "tree": tree, "worktree_clean": True}


def _tensor_state(model: Any, torch: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    base: dict[str, Any] = {}
    adapters: dict[str, Any] = {}
    for name, value in model.named_parameters(remove_duplicate=False):
        if "lora_" in name:
            adapters[name] = value
        else:
            base[f"parameter::{name}"] = value
    for name, value in model.named_buffers(remove_duplicate=False):
        if "lora_" not in name:
            base[f"buffer::{name}"] = value
    if not adapters or any(not value.requires_grad for value in adapters.values()):
        raise QualificationError("PHYSICAL_ADAPTER_PARAMETER_SET_INVALID")
    if any(value.requires_grad for value in base.values()):
        raise QualificationError("PHYSICAL_BASE_TENSOR_REQUIRES_GRAD")
    if any(not torch.isfinite(value.detach().float()).all() for value in adapters.values()):
        raise QualificationError("PHYSICAL_ADAPTER_NONFINITE")
    return base, adapters


def _adapter_schema(
    adapters: dict[str, Any], profile: dict[str, Any], base_id: str, tokenizer_hash: str
) -> tuple[dict[str, object], str]:
    targets = tuple(profile["adapter"]["ordered_target_modules"])
    ordered: list[dict[str, object]] = []
    for target in targets:
        matches = [
            (name, value)
            for name, value in adapters.items()
            if name.endswith(f"{target}.lora_A.default.weight")
            or name.endswith(f"{target}.lora_B.default.weight")
        ]
        if len(matches) != 2:
            raise QualificationError(f"PHYSICAL_TARGET_RESOLUTION_MISMATCH:{target}:{len(matches)}")
        for name, value in sorted(matches):
            ordered.append(
                {
                    "alias_owner": name,
                    "logical_dtype": str(value.dtype).removeprefix("torch.").upper(),
                    "lora_rank": int(profile["adapter"]["rank"]),
                    "name": name,
                    "shape": list(value.shape),
                    "target_module": target,
                }
            )
    schema: dict[str, object] = {
        "base_model_manifest_id": base_id,
        "formal_semantics_id": FORMAL_ID,
        "ordered_parameters": ordered,
        "ordered_target_modules": list(targets),
        "quantized_base_profile_id": "PENDING",
        "schema_version": "1.0.0",
        "tokenizer_hash": tokenizer_hash,
        "type_name": "ADAPTER_PARAMETER_SCHEMA",
    }
    return schema, sha256_content_id(canonical_json_bytes(schema))


def _context_id_native(library: Path, context: dict[str, str]) -> tuple[str, str]:
    class BytesView(ctypes.Structure):
        _fields_ = [("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_size_t)]

    class Output(ctypes.Structure):
        _fields_ = [
            ("data", ctypes.POINTER(ctypes.c_uint8)),
            ("capacity", ctypes.c_size_t),
            ("required", ctypes.c_size_t),
            ("written", ctypes.c_size_t),
        ]

    class QloraContext(ctypes.Structure):
        _fields_ = [
            ("struct_size", ctypes.c_uint32),
            ("reserved", ctypes.c_uint32),
            ("adapter_parameter_schema_id", BytesView),
            ("base_model_manifest_id", BytesView),
            ("parent_adapter_id", BytesView),
            ("quantized_base_profile_id", BytesView),
            ("tokenizer_hash", BytesView),
            ("training_mode_id", BytesView),
        ]

    loaded = ctypes.CDLL(str(library))
    function = loaded.delta_qlora_context_id
    function.argtypes = [ctypes.POINTER(QloraContext), ctypes.POINTER(Output)]
    function.restype = ctypes.c_int
    buffers: list[Any] = []

    def view(value: str) -> BytesView:
        buffer = (ctypes.c_uint8 * len(value))(*value.encode("ascii"))
        buffers.append(buffer)
        return BytesView(ctypes.cast(buffer, ctypes.POINTER(ctypes.c_uint8)), len(value))

    value = QloraContext(
        ctypes.sizeof(QloraContext),
        0,
        view(context["adapter_parameter_schema_id"]),
        view(context["base_model_manifest_id"]),
        view(context["parent_adapter_id"]),
        view(context["quantized_base_profile_id"]),
        view(context["tokenizer_hash"]),
        view(context["training_mode_id"]),
    )
    sizing = Output(None, 0, 0, 0)
    if function(ctypes.byref(value), ctypes.byref(sizing)) != 7 or sizing.required != 71:
        raise QualificationError("NATIVE_QLORA_CONTEXT_SIZE_NEGOTIATION_FAILED")
    output_buffer = (ctypes.c_uint8 * sizing.required)()
    output = Output(output_buffer, sizing.required, 0, 0)
    if function(ctypes.byref(value), ctypes.byref(output)) != 0 or output.written != 71:
        raise QualificationError("NATIVE_QLORA_CONTEXT_BINDING_FAILED")
    native_id = bytes(output_buffer).decode("ascii")
    canonical = {
        **context,
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "type_name": "QLORA_CONTEXT_BINDING",
    }
    document = canonical_json_bytes(canonical)
    expected = (
        "sha256:" + hashlib.sha256(b"deltareduce.009.qlora-context.v1\x00" + document).hexdigest()
    )
    if native_id != expected:
        raise QualificationError("NATIVE_PYTHON_QLORA_CONTEXT_ID_MISMATCH")
    return native_id, hashlib.sha256(library.read_bytes()).hexdigest()


def run_physical_qualification(
    profile_path: Path,
    native_library: Path,
) -> dict[str, object]:
    profile = load_profile(profile_path)
    source = _source_observation()
    gpu = probe_gpu()
    validate_physical_readiness(profile, gpu)
    cublas_workspace = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if cublas_workspace not in {None, ":4096:8"}:
        raise QualificationError("PHYSICAL_CUBLAS_WORKSPACE_CONFIG_MISMATCH")
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    started = time.monotonic()
    import torch
    from peft import (  # type: ignore[import-not-found]
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
    )
    from transformers import (  # type: ignore[import-not-found]
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )

    versions = _software_versions(profile, torch)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise QualificationError("PHYSICAL_CUDA_DEVICE_UNAVAILABLE")
    torch.manual_seed(int(profile["execution"]["seed"]))
    torch.cuda.manual_seed_all(int(profile["execution"]["seed"]))
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

    model_profile = profile["model"]
    quantization = profile["quantization"]
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=str(quantization["quantization_type"]).lower(),
        bnb_4bit_use_double_quant=bool(quantization["double_quantization"]),
        bnb_4bit_compute_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_profile["repository"],
        revision=model_profile["revision"],
        token=False,
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_profile["repository"],
        revision=model_profile["revision"],
        token=False,
        trust_remote_code=False,
        use_safetensors=True,
        quantization_config=quant_config,
        device_map={"": 0},
        attn_implementation="sdpa",
        torch_dtype=torch.float16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.gradient_checkpointing_enable()
    adapter_profile = profile["adapter"]
    model = get_peft_model(
        model,
        LoraConfig(
            r=int(adapter_profile["rank"]),
            lora_alpha=int(adapter_profile["alpha"]),
            lora_dropout=int(adapter_profile["dropout_ppm"]) / 1_000_000,
            bias="none",
            target_modules=list(adapter_profile["ordered_target_modules"]),
            task_type="CAUSAL_LM",
        ),
    )
    for name, parameter in model.named_parameters():
        if "lora_" in name:
            parameter.data = parameter.data.to(torch.float16)
    base, adapters = _tensor_state(model, torch)
    base_hash_before = _logical_tensor_hash(base)
    parent_adapters = {
        name: value.detach().cpu().clone() for name, value in sorted(adapters.items())
    }
    optimizer = _Fp32StateAdamW(list(adapters.values()), torch, learning_rate=1e-4)
    if {id(value) for value in optimizer.parameters} != {id(value) for value in adapters.values()}:
        raise QualificationError("PHYSICAL_OPTIMIZER_PARAMETER_SET_MISMATCH")
    ticket = profile["ticket"]
    sequence_length = int(ticket["sequence_length"])
    accumulation = int(ticket["gradient_accumulation_steps"])
    optimizer_steps = int(ticket["H"])
    processed_tokens = 0
    losses: list[str] = []
    model.train()
    vocabulary_size = int(model.config.vocab_size)
    for step in range(optimizer_steps):
        optimizer.zero_grad()
        for microstep in range(accumulation):
            offset = step * accumulation + microstep
            input_ids = (
                torch.arange(sequence_length, device="cuda", dtype=torch.long) + 1024 + offset
            ).remainder(vocabulary_size)[None, :]
            result = model(input_ids=input_ids, labels=input_ids, use_cache=False)
            loss = result.loss / accumulation
            if not torch.isfinite(loss):
                raise QualificationError("PHYSICAL_NONFINITE_LOSS")
            loss.backward()
            losses.append(format(float(loss.detach().cpu()), ".9g"))
            processed_tokens += sequence_length
        optimizer.step()
        if _logical_tensor_hash(base) != base_hash_before:
            raise QualificationError("PHYSICAL_BASE_MUTATION_DURING_TICKET")
    torch.cuda.synchronize()
    actual_steps = optimizer_steps
    if actual_steps != int(ticket["H"]) or processed_tokens != int(ticket["B"]):
        raise QualificationError("PHYSICAL_INCOMPLETE_FIXED_TICKET")
    base_hash_after = _logical_tensor_hash(base)
    if base_hash_after != base_hash_before:
        raise QualificationError("PHYSICAL_BASE_MUTATION")
    final_adapters = {
        name: value.detach().cpu().clone() for name, value in sorted(adapters.items())
    }
    contribution = encode_adapter_contribution(
        parent_adapters,
        final_adapters,
        actual_optimizer_steps=actual_steps,
        expected_optimizer_steps=int(ticket["H"]),
    )
    peak_allocated = int(torch.cuda.max_memory_allocated())
    peak_reserved = int(torch.cuda.max_memory_reserved())
    hard_max = int(profile["memory"]["hard_max_reserved_bytes"])
    required_headroom = int(profile["memory"]["required_headroom_bytes"])
    if peak_reserved > hard_max or gpu.total_memory_bytes - peak_reserved < required_headroom:
        raise QualificationError("PHYSICAL_RUNTIME_MEMORY_BUDGET_EXCEEDED")
    device_map = getattr(model, "hf_device_map", {})
    if any(str(value).lower() in {"cpu", "disk"} for value in device_map.values()):
        raise QualificationError("PHYSICAL_HOST_OFFLOAD_DETECTED")

    tokenizer_hash = sha256_content_id(
        canonical_json_bytes({key: value for key, value in sorted(tokenizer.get_vocab().items())})
    )
    base_manifest = {
        "access_policy": "PUBLIC_NO_TOKEN",
        "config_hash": sha256_content_id(
            json.dumps(model.config.to_dict(), sort_keys=True, default=str).encode()
        ),
        "license": model_profile["license"],
        "model_repository": model_profile["repository"],
        "model_revision": model_profile["revision"],
        "tokenizer_hash": tokenizer_hash,
        "type_name": "BASE_MODEL_MANIFEST",
    }
    base_id = sha256_content_id(canonical_json_bytes(base_manifest))
    quant_profile = {
        **quantization,
        "backend_version": versions["bitsandbytes"],
        "base_model_manifest_id": base_id,
        "type_name": "QUANTIZED_BASE_PROFILE",
    }
    quant_id = sha256_content_id(canonical_json_bytes(quant_profile))
    schema, _ = _adapter_schema(adapters, profile, base_id, tokenizer_hash)
    schema["quantized_base_profile_id"] = quant_id
    adapter_schema_id = sha256_content_id(canonical_json_bytes(schema))
    parent_adapter_id = (
        "sha256:"
        + hashlib.sha256(
            b"deltareduce.009.parent-adapter.v1\x00"
            + b"".join(
                name.encode() + value.contiguous().numpy().tobytes()
                for name, value in parent_adapters.items()
            )
        ).hexdigest()
    )
    training_mode_id = sha256_content_id(
        canonical_json_bytes(
            {
                "formal_semantics_id": FORMAL_ID,
                "mode": "QLORA_ADAPTER",
                "parallel_certificate_graph": False,
                "schema_version": "1.0.0",
                "type_name": "TRAINING_MODE",
            }
        )
    )
    context = {
        "adapter_parameter_schema_id": adapter_schema_id,
        "base_model_manifest_id": base_id,
        "parent_adapter_id": parent_adapter_id,
        "quantized_base_profile_id": quant_id,
        "tokenizer_hash": tokenizer_hash,
        "training_mode_id": training_mode_id,
    }
    native_context_id, native_library_sha256 = _context_id_native(native_library, context)
    trainable_parameters = sum(value.numel() for value in adapters.values())
    total_parameters = sum(value.numel() for value in model.parameters())
    adapter_bytes = sum(value.numel() * value.element_size() for value in adapters.values())
    report: dict[str, object] = {
        "adapter": {
            "bytes": adapter_bytes,
            "commitment_root": contribution.commitment_root,
            "parameter_count": trainable_parameters,
            "parameter_schema_id": adapter_schema_id,
            "q_envelope_bytes": sum(len(item.envelope) for item in contribution.ordered_shards),
            "shard_count": len(contribution.ordered_shards),
            "trainable_ratio_ppm": trainable_parameters * 1_000_000 // total_parameters,
        },
        "base": {
            "hash_after": base_hash_after,
            "hash_before": base_hash_before,
            "manifest_id": base_id,
            "parameter_count": total_parameters - trainable_parameters,
            "tokenizer_hash": tokenizer_hash,
        },
        "claim": {
            "eligible": True,
            "generalized": False,
            "scope": "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
        },
        "device": {
            "compute_capability": gpu.compute_capability,
            "driver_version": gpu.driver_version,
            "free_memory_at_start_bytes": gpu.free_memory_bytes,
            "name": gpu.name,
            "total_memory_bytes": gpu.total_memory_bytes,
            "uuid": gpu.uuid,
        },
        "formal_semantics_id": FORMAL_ID,
        "execution": {
            "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
            "deterministic_algorithms": True,
        },
        "memory": {
            "hard_max_reserved_bytes": hard_max,
            "headroom_bytes": gpu.total_memory_bytes - peak_reserved,
            "host_offload_peak_bytes": 0,
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "required_headroom_bytes": required_headroom,
        },
        "optimizer": {
            "adapter_only": True,
            "learning_rate": "0.0001",
            "state_bytes": optimizer.state_bytes,
            "state_dtype": "FLOAT32",
            "type": "ADAMW",
        },
        "native": {
            "certificate_path_tests": "REQUIRED_SEPARATE_EXACT_SOURCE_PASS",
            "context_id": native_context_id,
            "library_sha256": native_library_sha256,
        },
        "profile": {
            "path": profile_path.as_posix(),
            "sha256": PROFILE_SHA256,
        },
        "schema_version": "1.0.0",
        "software": versions,
        "source": source,
        "status": "PASS",
        "ticket": {
            "actual_optimizer_steps": actual_steps,
            "fixed_B": int(ticket["B"]),
            "fixed_H": int(ticket["H"]),
            "losses": losses,
            "processed_tokens": processed_tokens,
        },
        "timing": {"elapsed_milliseconds": int((time.monotonic() - started) * 1000)},
    }
    return report


def write_evidence(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )


def physical_environment_ready() -> bool:
    return os.environ.get("DELTA_QLORA_PHYSICAL") == "1"
