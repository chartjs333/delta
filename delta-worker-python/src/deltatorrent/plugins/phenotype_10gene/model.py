"""Synthetic 10-gene phenotype centroid model plugin."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

import torch

from deltatorrent.plugins.contract import (
    DeltaPlugin,
    abstain_response,
    plugin_incompatible_response,
)
from deltatorrent.plugins.workload import ModelPlugin


class Synthetic10GeneCentroidPlugin(ModelPlugin, DeltaPlugin):
    """Nearest centroid classifier for tabular 10-gene phenotype vectors.

    Conforms to both generic ModelPlugin and DeltaPlugin structural protocols.
    """

    def __init__(self) -> None:
        self._centroids: torch.Tensor | None = None
        self._is_trained: bool = False

    @property
    def plugin_id(self) -> str:
        return "tabular-10gene-phenotype-v1"

    @property
    def sample_kind(self) -> str:
        return "tabular/genomic-10gene-vector"

    @property
    def target_kind(self) -> str:
        return "class-id/0-1"

    @property
    def supports_stage_c_real_drq1(self) -> bool:
        return True

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    def fit(self, train_data: Any, train_targets: Any) -> None:
        """Fit class centroids on training data."""
        if not isinstance(train_data, torch.Tensor) or not isinstance(train_targets, torch.Tensor):
            raise ValueError("train_data and train_targets must be torch.Tensor instances")
        if train_data.ndim != 2 or train_data.shape[1] != 10:
            raise ValueError(f"train_data must have shape (N, 10), got {tuple(train_data.shape)}")
        if train_targets.ndim != 1 or train_targets.shape[0] != train_data.shape[0]:
            raise ValueError(
                f"train_targets shape {tuple(train_targets.shape)} "
                f"does not match train_data N={train_data.shape[0]}"
            )

        c0_mask = train_targets == 0
        c1_mask = train_targets == 1

        if not torch.any(c0_mask) or not torch.any(c1_mask):
            raise ValueError("Training data must contain samples from both class 0 and class 1")

        mu_0 = train_data[c0_mask].mean(dim=0)
        mu_1 = train_data[c1_mask].mean(dim=0)

        self._centroids = torch.stack([mu_0, mu_1]).to(torch.float32)
        self._is_trained = True

    def predict(self, features: torch.Tensor) -> torch.Tensor:
        """Predict nearest centroid class ID (0 or 1) for features."""
        if not self._is_trained or self._centroids is None:
            raise RuntimeError("Model is not trained: call fit() first")
        if features.ndim != 2 or features.shape[1] != 10:
            raise ValueError(f"Features must have shape (N, 10), got {tuple(features.shape)}")

        # Distances: [N, 2]
        d0 = torch.norm(features - self._centroids[0], dim=1)
        d1 = torch.norm(features - self._centroids[1], dim=1)
        distances = torch.stack([d0, d1], dim=1)
        return torch.argmin(distances, dim=1)

    def evaluate(self, test_data: Any, test_targets: Any) -> dict[str, Any]:
        """Evaluate model accuracy and metrics on test split."""
        if not isinstance(test_data, torch.Tensor) or not isinstance(test_targets, torch.Tensor):
            raise ValueError("test_data and test_targets must be torch.Tensor instances")

        predictions = self.predict(test_data)
        correct = (predictions == test_targets).sum().item()
        total = test_targets.shape[0]
        accuracy = float(correct / total) if total > 0 else 0.0

        # Confusion metrics
        tp = int(((predictions == 1) & (test_targets == 1)).sum().item())
        fp = int(((predictions == 1) & (test_targets == 0)).sum().item())
        fn = int(((predictions == 0) & (test_targets == 1)).sum().item())
        tn = int(((predictions == 0) & (test_targets == 0)).sum().item())

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        denom = precision + recall
        f1 = float(2 * precision * recall / denom) if denom > 0 else 0.0

        return {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "macro_f1": round(f1, 4),
            "test_samples": total,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    def canonical_model_digest(self) -> str:
        """Compute canonical SHA-256 of little-endian float32 centroid parameters."""
        if not self._is_trained or self._centroids is None:
            raise RuntimeError("Cannot compute digest for untrained model")

        raw_bytes = self._centroids.cpu().numpy().astype("<f4").tobytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        return f"sha256:{digest}"

    # --- DeltaPlugin Structural Protocol Implementation ---

    def metadata(self) -> dict[str, Any]:
        """Return plugin manifest conforming to generic plugin contract."""
        model_hash = self.canonical_model_digest()[7:] if self._is_trained else ("0" * 64)
        return {
            "plugin_id": self.plugin_id,
            "version": "1.0.0",
            "entrypoint": "deltatorrent.plugins.phenotype_10gene:Synthetic10GeneCentroidPlugin",
            "contract": {
                "class": "DeltaPlugin",
                "methods": ["metadata", "health", "analyze"],
            },
            "compatible_delta_engines": [
                {
                    "repository": "chartjs333/delta",
                    "commit": "670b58f6458fe84620f4f9f46401f855d04ae05d",
                    "compatibility": "pinned",
                }
            ],
            "capabilities": [
                "tabular/genomic-10gene-vector",
                "class-id/0-1",
                "stage_c_real_drq1",
            ],
            "failure_policy": {"mode": "fail-closed"},
            "artifact_identity": {
                "components": [
                    {
                        "name": "centroid_parameters",
                        "path": "centroids.bin",
                        "sha256": model_hash,
                        "size_bytes": 80,
                    }
                ]
            },
        }

    def health(self) -> dict[str, Any]:
        """Return plugin health and readiness status."""
        return {
            "status": "READY" if self._is_trained else "UNINITIALIZED",
            "trained": self._is_trained,
            "model_digest": self.canonical_model_digest() if self._is_trained else None,
        }

    def analyze(self, request: dict[str, Any]) -> dict[str, Any]:
        """Inference endpoint conforming to DeltaPlugin protocol."""
        if not isinstance(request, Mapping):
            return plugin_incompatible_response(["INVALID_REQUEST_PAYLOAD"])

        if not self._is_trained or self._centroids is None:
            return abstain_response(["MODEL_NOT_TRAINED"])

        sample = request.get("sample")
        if not isinstance(sample, list) or len(sample) != 10:
            return plugin_incompatible_response(["INVALID_SAMPLE_DIMENSIONS"])

        try:
            sample_tensor = torch.tensor([sample], dtype=torch.float32)
        except Exception:
            return plugin_incompatible_response(["INVALID_NUMERIC_VALUES"])

        d0 = float(torch.norm(sample_tensor - self._centroids[0]).item())
        d1 = float(torch.norm(sample_tensor - self._centroids[1]).item())
        pred_class = 0 if d0 <= d1 else 1

        # Normalized softmax score over negative distances
        scores = torch.softmax(torch.tensor([-d0, -d1]), dim=0)
        confidence = float(scores[pred_class].item())

        return {
            "ranking": [
                {
                    "class_id": pred_class,
                    "score": round(confidence, 4),
                    "label": "CARRIER" if pred_class == 1 else "CONTROL",
                }
            ],
            "status": "ANALYZED",
            "reason_codes": ["CENTROID_MATCH"],
            "artifact_identity": {
                "model_digest": self.canonical_model_digest(),
            },
            "evidence": {
                "distance_c0": round(d0, 4),
                "distance_c1": round(d1, 4),
            },
        }
