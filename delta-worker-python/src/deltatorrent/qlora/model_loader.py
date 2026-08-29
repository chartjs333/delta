"""Offline reference loading and production adapter construction."""

from __future__ import annotations

import json
from pathlib import Path

import torch

from deltatorrent.qlora.backend import BitsAndBytesAdapter, TinyOfflineBackend
from deltatorrent.qlora.manifests import ImportRequest, load_import_request


def load_tiny_backend(path: Path) -> tuple[ImportRequest, TinyOfflineBackend]:
    request = load_import_request(path / "import.json", allowed_root=path.parent)
    state = json.loads(request.weight_paths[0].read_text(encoding="utf-8"))
    adapter = json.loads((path / "adapter.json").read_text(encoding="utf-8"))
    base = {
        name: torch.tensor(value, dtype=torch.float32, requires_grad=False)
        for name, value in state.items()
        if name in request.manifest.persistent_base_parameters
    }
    buffers = {
        name: torch.tensor(value, dtype=torch.float32, requires_grad=False)
        for name, value in state.items()
        if name in request.manifest.persistent_protocol_buffers
    }
    adapters = {
        name: torch.nn.Parameter(torch.tensor(value, dtype=torch.float32))
        for name, value in adapter.items()
    }
    return request, TinyOfflineBackend(base, buffers, adapters)


def production_adapter(profile: dict[str, object]) -> BitsAndBytesAdapter:
    quantization = profile.get("quantization")
    software = profile.get("software")
    if not isinstance(quantization, dict) or not isinstance(software, dict):
        raise ValueError("PRODUCTION_PROFILE_FIELDS_INVALID")
    if quantization.get("backend") != "BITSANDBYTES":
        raise ValueError("PRODUCTION_BACKEND_INVALID")
    return BitsAndBytesAdapter(
        backend_version=str(software.get("bitsandbytes")),
        compute_dtype=str(quantization.get("compute_dtype")),
        quantization_type=str(quantization.get("quantization_type")),
        double_quantization=quantization.get("double_quantization") is True,
    )
