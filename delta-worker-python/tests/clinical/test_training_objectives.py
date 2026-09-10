from __future__ import annotations

import torch
from deltatorrent.clinical.canonical_features import GENES
from deltatorrent.clinical.classifier import (
    TrainingConfig,
    _classification_loss,
    _epoch_indices,
)


def test_balanced_batches_mix_supported_classes_per_batch() -> None:
    labels = torch.tensor([idx for idx in range(len(GENES)) for _ in range(3)])

    indices = _epoch_indices(
        labels,
        "balanced_batches",
        seed=7,
        epoch=1,
        batch_size=20,
    )

    first_batch_labels = {int(labels[idx]) for idx in indices[:20]}
    assert first_batch_labels == set(range(len(GENES)))


def test_focal_loss_and_hard_negative_penalty_are_finite() -> None:
    labels = torch.tensor([GENES.index("LRRK2"), GENES.index("VPS35")])
    logits = torch.zeros((2, len(GENES)), dtype=torch.float32)
    logits[0, GENES.index("SNCA")] = 2.0
    logits[1, GENES.index("SNCA")] = 2.0
    logits.requires_grad_(True)

    base = _classification_loss(
        logits,
        labels,
        config=TrainingConfig(loss_name="focal"),
        loss_weights=None,
    )
    hard_negative = _classification_loss(
        logits,
        labels,
        config=TrainingConfig(loss_name="focal", hard_negative_weight=1.0),
        loss_weights=None,
    )

    assert torch.isfinite(base)
    assert torch.isfinite(hard_negative)
    assert float(hard_negative.item()) > float(base.item())
