"""Phenotype-to-gene classifier, metrics and DeltaReduce training adapter."""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypedDict, cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from deltatorrent.clinical.canonical_features import (
    AAO_GROUPS,
    CANONICAL_PHENOTYPE_FEATURES,
    FAMILY_HISTORY_VALUES,
    GENES,
    INHERITANCE_VALUES,
    PEDIGREE_FEATURES,
    SEX_VALUES,
    ZYGOSITY_VALUES,
)
from deltatorrent.clinical.gold_loader import ClinicalRecord
from deltatorrent.delta.builder import build_local_delta, snapshot_fp32_parameters
from deltatorrent.delta.normalization import normalize_local_delta
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import derive_parameter_schema

STRATEGIES: tuple[str, ...] = (
    "natural",
    "sqrt_sampling",
    "class_weighted_loss",
    "balanced_sampling",
    "balanced_batches",
)

LOSS_NAMES: tuple[str, ...] = ("cross_entropy", "focal")

DEFAULT_HARD_NEGATIVE_PAIRS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("LRRK2", ("SNCA",)),
    ("VPS35", ("SNCA", "LRRK2")),
    ("RAB32", ("LRRK2",)),
    ("PARK7", ("PRKN", "PINK1")),
)


class RankingRow(TypedDict):
    gene: str
    probability: float


def _validate_label_genes(label_genes: tuple[str, ...]) -> None:
    if not label_genes:
        raise ValueError("LABEL_GENES_MUST_NOT_BE_EMPTY")
    if len(set(label_genes)) != len(label_genes):
        raise ValueError("LABEL_GENES_MUST_BE_UNIQUE")
    unknown = sorted(set(label_genes) - set(GENES))
    if unknown:
        raise ValueError(f"UNKNOWN_LABEL_GENES: {unknown}")


@dataclass(frozen=True, slots=True)
class ClinicalTensorData:
    phenotype: Tensor
    pedigree: Tensor
    sex: Tensor
    aao_group: Tensor
    zygosity: Tensor
    inheritance: Tensor
    family_history: Tensor
    aao_numeric: Tensor
    aao_missing: Tensor
    labels: Tensor
    record_ids: tuple[str, ...]

    def __len__(self) -> int:
        return int(self.labels.shape[0])


@dataclass(frozen=True, slots=True)
class ClinicalEncoder:
    feature_order: tuple[str, ...]
    pedigree_feature_order: tuple[str, ...]
    label_genes: tuple[str, ...]
    aao_mean: float
    aao_std: float
    train_feature_counts: dict[str, int]
    train_records: int

    @classmethod
    def from_training_records(
        cls,
        records: tuple[ClinicalRecord, ...],
        *,
        label_genes: tuple[str, ...] = GENES,
    ) -> ClinicalEncoder:
        _validate_label_genes(label_genes)
        outside_label_set = sorted({record.gene for record in records} - set(label_genes))
        if outside_label_set:
            raise ValueError(f"RECORD_GENE_OUTSIDE_LABEL_SET: {outside_label_set}")
        aao_values = [record.aao_years for record in records if record.aao_years is not None]
        aao_mean = sum(aao_values) / len(aao_values) if aao_values else 0.0
        if len(aao_values) > 1:
            variance = sum((value - aao_mean) ** 2 for value in aao_values) / len(aao_values)
            aao_std = math.sqrt(variance) or 1.0
        else:
            aao_std = 1.0
        counts = Counter(feature for record in records for feature in record.phenotype_features)
        counts.update(feature for record in records for feature in record.pedigree_features)
        return cls(
            feature_order=CANONICAL_PHENOTYPE_FEATURES,
            pedigree_feature_order=PEDIGREE_FEATURES,
            label_genes=tuple(label_genes),
            aao_mean=aao_mean,
            aao_std=aao_std,
            train_feature_counts=dict(sorted(counts.items())),
            train_records=len(records),
        )

    def input_schema(self) -> dict[str, object]:
        return {
            "input_schema_version": "clinical-phenotype-vector-v1",
            "forbidden_input_roles": ["diagnosis", "target_gene", "gene_name", "variant_gene"],
            "phenotype_feature_order": list(self.feature_order),
            "pedigree_feature_order": list(self.pedigree_feature_order),
            "categorical_fields": {
                "sex": list(SEX_VALUES),
                "aao_group": list(AAO_GROUPS),
                "zygosity": list(ZYGOSITY_VALUES),
                "inheritance": list(INHERITANCE_VALUES),
                "family_history": list(FAMILY_HISTORY_VALUES),
            },
            "numeric_fields": {
                "aao_years_normalized": {
                    "mean_train_only": self.aao_mean,
                    "std_train_only": self.aao_std,
                },
                "aao_missing": {"values": [0.0, 1.0]},
            },
        }

    def model_input_terms(self, record: ClinicalRecord) -> tuple[str, ...]:
        return (
            *record.phenotype_features,
            *record.pedigree_features,
            record.sex,
            record.aao_group,
            record.zygosity,
            record.inheritance,
            record.family_history,
        )

    def encode_records(self, records: tuple[ClinicalRecord, ...]) -> ClinicalTensorData:
        feature_index = {feature: idx for idx, feature in enumerate(self.feature_order)}
        pedigree_index = {feature: idx for idx, feature in enumerate(self.pedigree_feature_order)}
        sex_index = {value: idx for idx, value in enumerate(SEX_VALUES)}
        aao_index = {value: idx for idx, value in enumerate(AAO_GROUPS)}
        zygosity_index = {value: idx for idx, value in enumerate(ZYGOSITY_VALUES)}
        inheritance_index = {value: idx for idx, value in enumerate(INHERITANCE_VALUES)}
        family_history_index = {value: idx for idx, value in enumerate(FAMILY_HISTORY_VALUES)}
        gene_index = {gene: idx for idx, gene in enumerate(self.label_genes)}

        phenotype_rows: list[list[float]] = []
        pedigree_rows: list[list[float]] = []
        sex_ids: list[int] = []
        aao_group_ids: list[int] = []
        zygosity_ids: list[int] = []
        inheritance_ids: list[int] = []
        family_history_ids: list[int] = []
        aao_numeric: list[list[float]] = []
        aao_missing: list[list[float]] = []
        labels: list[int] = []
        record_ids: list[str] = []

        if not records:
            return ClinicalTensorData(
                phenotype=torch.zeros((0, len(self.feature_order)), dtype=torch.float32),
                pedigree=torch.zeros((0, len(self.pedigree_feature_order)), dtype=torch.float32),
                sex=torch.zeros((0,), dtype=torch.long),
                aao_group=torch.zeros((0,), dtype=torch.long),
                zygosity=torch.zeros((0,), dtype=torch.long),
                inheritance=torch.zeros((0,), dtype=torch.long),
                family_history=torch.zeros((0,), dtype=torch.long),
                aao_numeric=torch.zeros((0, 1), dtype=torch.float32),
                aao_missing=torch.zeros((0, 1), dtype=torch.float32),
                labels=torch.zeros((0,), dtype=torch.long),
                record_ids=(),
            )

        for record in records:
            phenotype = [0.0] * len(self.feature_order)
            for feature in record.phenotype_features:
                idx = feature_index.get(feature)
                if idx is not None:
                    phenotype[idx] = 1.0
            pedigree = [0.0] * len(self.pedigree_feature_order)
            for feature in record.pedigree_features:
                idx = pedigree_index.get(feature)
                if idx is not None:
                    pedigree[idx] = 1.0
            normalized_aao = 0.0
            if record.aao_years is not None:
                normalized_aao = (record.aao_years - self.aao_mean) / self.aao_std

            phenotype_rows.append(phenotype)
            pedigree_rows.append(pedigree)
            sex_ids.append(sex_index.get(record.sex, sex_index["unknown"]))
            aao_group_ids.append(aao_index.get(record.aao_group, aao_index["AAO_MISSING"]))
            zygosity_ids.append(zygosity_index.get(record.zygosity, zygosity_index["unknown"]))
            inheritance_ids.append(
                inheritance_index.get(record.inheritance, inheritance_index["unknown"])
            )
            family_history_ids.append(
                family_history_index.get(record.family_history, family_history_index["unknown"])
            )
            aao_numeric.append([normalized_aao])
            aao_missing.append([1.0 if record.aao_missing else 0.0])
            label_idx = gene_index.get(record.gene)
            if label_idx is None:
                raise ValueError(f"RECORD_GENE_OUTSIDE_LABEL_SET: {record.gene}")
            labels.append(label_idx)
            record_ids.append(record.record_id)

        return ClinicalTensorData(
            phenotype=torch.tensor(phenotype_rows, dtype=torch.float32),
            pedigree=torch.tensor(pedigree_rows, dtype=torch.float32),
            sex=torch.tensor(sex_ids, dtype=torch.long),
            aao_group=torch.tensor(aao_group_ids, dtype=torch.long),
            zygosity=torch.tensor(zygosity_ids, dtype=torch.long),
            inheritance=torch.tensor(inheritance_ids, dtype=torch.long),
            family_history=torch.tensor(family_history_ids, dtype=torch.long),
            aao_numeric=torch.tensor(aao_numeric, dtype=torch.float32),
            aao_missing=torch.tensor(aao_missing, dtype=torch.float32),
            labels=torch.tensor(labels, dtype=torch.long),
            record_ids=tuple(record_ids),
        )


class PhenotypeGeneClassifier(nn.Module):
    def __init__(
        self,
        *,
        phenotype_dim: int,
        pedigree_dim: int,
        label_genes: tuple[str, ...] = GENES,
        hidden_sizes: tuple[int, int] = (256, 128),
        dropout: float = 0.10,
        seed: int = 42,
    ) -> None:
        super().__init__()
        _validate_label_genes(label_genes)
        self.label_genes = tuple(label_genes)
        torch.manual_seed(seed)
        emb_dim = 4
        self.sex_embedding = nn.Embedding(len(SEX_VALUES), emb_dim)
        self.aao_group_embedding = nn.Embedding(len(AAO_GROUPS), emb_dim)
        self.zygosity_embedding = nn.Embedding(len(ZYGOSITY_VALUES), emb_dim)
        self.inheritance_embedding = nn.Embedding(len(INHERITANCE_VALUES), emb_dim)
        self.family_history_embedding = nn.Embedding(len(FAMILY_HISTORY_VALUES), emb_dim)
        input_dim = phenotype_dim + pedigree_dim + 2 + (5 * emb_dim)
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_sizes[0]),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_sizes[0], hidden_sizes[1]),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_sizes[1], len(self.label_genes)),
        )

    def forward(
        self,
        phenotype: Tensor,
        pedigree: Tensor,
        sex: Tensor,
        aao_group: Tensor,
        zygosity: Tensor,
        inheritance: Tensor,
        family_history: Tensor,
        aao_numeric: Tensor,
        aao_missing: Tensor,
    ) -> Tensor:
        parts = [
            phenotype,
            pedigree,
            self.sex_embedding(sex),
            self.aao_group_embedding(aao_group),
            self.zygosity_embedding(zygosity),
            self.inheritance_embedding(inheritance),
            self.family_history_embedding(family_history),
            aao_numeric,
            aao_missing,
        ]
        return cast(Tensor, self.network(torch.cat(parts, dim=1)))


def make_model(
    encoder: ClinicalEncoder, *, seed: int = 42, dropout: float = 0.10
) -> PhenotypeGeneClassifier:
    return PhenotypeGeneClassifier(
        phenotype_dim=len(encoder.feature_order),
        pedigree_dim=len(encoder.pedigree_feature_order),
        label_genes=encoder.label_genes,
        dropout=dropout,
        seed=seed,
    )


@dataclass(frozen=True, slots=True)
class TrainingConfig:
    seed: int = 42
    epochs: int = 30
    batch_size: int = 128
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    strategy: str = "class_weighted_loss"
    label_smoothing: float = 0.0
    loss_name: str = "cross_entropy"
    focal_gamma: float = 2.0
    hard_negative_weight: float = 0.0
    hard_negative_margin: float = 0.25
    hard_negative_pairs: tuple[tuple[str, tuple[str, ...]], ...] = (
        DEFAULT_HARD_NEGATIVE_PAIRS
    )


@dataclass(frozen=True, slots=True)
class TrainingResult:
    model: PhenotypeGeneClassifier
    strategy: str
    best_epoch: int
    history: list[dict[str, float]]
    train_metrics: dict[str, object]
    validation_metrics: dict[str, object]


def _batch(data: ClinicalTensorData, indices: Tensor) -> tuple[Tensor, ...]:
    return (
        data.phenotype[indices],
        data.pedigree[indices],
        data.sex[indices],
        data.aao_group[indices],
        data.zygosity[indices],
        data.inheritance[indices],
        data.family_history[indices],
        data.aao_numeric[indices],
        data.aao_missing[indices],
    )


def _class_counts(labels: Tensor) -> Counter[int]:
    return Counter(int(value) for value in labels.tolist())


def _loss_weights(labels: Tensor, strategy: str, *, num_classes: int = len(GENES)) -> Tensor | None:
    if strategy != "class_weighted_loss":
        return None
    counts = _class_counts(labels)
    total = max(1, int(labels.shape[0]))
    weights = [total / (num_classes * max(1, counts[idx])) for idx in range(num_classes)]
    mean_weight = sum(weights) / len(weights)
    return torch.tensor([weight / mean_weight for weight in weights], dtype=torch.float32)


def _balanced_batch_epoch_indices(
    labels: Tensor,
    *,
    seed: int,
    epoch: int,
    batch_size: int,
) -> Tensor:
    by_class: dict[int, list[int]] = defaultdict(list)
    for idx, label in enumerate(labels.tolist()):
        by_class[int(label)].append(idx)
    classes = sorted(by_class)
    if not classes:
        return torch.zeros((0,), dtype=torch.long)

    rng = random.Random(seed + epoch * 1009)
    batches = max(1, math.ceil(int(labels.shape[0]) / batch_size))
    base_per_class = max(0, batch_size // len(classes))
    remainder = batch_size % len(classes)
    indices: list[int] = []
    for _ in range(batches):
        class_order = list(classes)
        rng.shuffle(class_order)
        allocations = {label: base_per_class for label in classes}
        for label in class_order[:remainder]:
            allocations[label] += 1
        for label in class_order:
            class_indices = by_class[label]
            for _ in range(allocations[label]):
                indices.append(class_indices[rng.randrange(len(class_indices))])
    return torch.tensor(indices, dtype=torch.long)


def _epoch_indices(
    labels: Tensor,
    strategy: str,
    *,
    seed: int,
    epoch: int,
    batch_size: int,
) -> Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed + epoch * 1009)
    count = int(labels.shape[0])
    if strategy in {"natural", "class_weighted_loss"}:
        return torch.randperm(count, generator=generator)
    if strategy == "balanced_batches":
        return _balanced_batch_epoch_indices(
            labels,
            seed=seed,
            epoch=epoch,
            batch_size=batch_size,
        )

    class_counts = _class_counts(labels)
    sample_weights: list[float] = []
    for label in labels.tolist():
        class_count = max(1, class_counts[int(label)])
        if strategy == "sqrt_sampling":
            sample_weights.append(1.0 / math.sqrt(class_count))
        elif strategy == "balanced_sampling":
            sample_weights.append(1.0 / class_count)
        else:
            raise ValueError(f"UNKNOWN_BALANCING_STRATEGY: {strategy}")
    weights = torch.tensor(sample_weights, dtype=torch.float32)
    return torch.multinomial(weights, count, replacement=True, generator=generator)


def _hard_negative_penalty(
    logits: Tensor,
    labels: Tensor,
    config: TrainingConfig,
    *,
    label_genes: tuple[str, ...] = GENES,
) -> Tensor:
    if config.hard_negative_weight <= 0:
        return logits.new_tensor(0.0)
    gene_index = {gene: idx for idx, gene in enumerate(label_genes)}
    penalties: list[Tensor] = []
    for target_gene, competitor_genes in config.hard_negative_pairs:
        target_idx = gene_index.get(target_gene)
        if target_idx is None:
            continue
        competitor_indices = [
            gene_index[gene] for gene in competitor_genes if gene in gene_index
        ]
        if not competitor_indices:
            continue
        mask = labels == target_idx
        if not bool(mask.any().item()):
            continue
        target_logits = logits[mask, target_idx].unsqueeze(1)
        competitor_logits = logits[mask][:, competitor_indices]
        penalties.append(
            torch.relu(config.hard_negative_margin + competitor_logits - target_logits).mean()
        )
    if not penalties:
        return logits.new_tensor(0.0)
    return torch.stack(penalties).mean()


def _classification_loss(
    logits: Tensor,
    labels: Tensor,
    *,
    config: TrainingConfig,
    loss_weights: Tensor | None,
    label_genes: tuple[str, ...] = GENES,
) -> Tensor:
    ce = F.cross_entropy(
        logits,
        labels,
        weight=loss_weights,
        label_smoothing=config.label_smoothing,
        reduction="none",
    )
    if config.loss_name == "cross_entropy":
        supervised = ce
    elif config.loss_name == "focal":
        probs = F.softmax(logits, dim=1)
        pt = probs.gather(1, labels.unsqueeze(1)).squeeze(1).clamp(min=1e-6, max=1.0)
        supervised = ((1.0 - pt) ** config.focal_gamma) * ce
    else:
        raise ValueError(f"UNKNOWN_LOSS_NAME: {config.loss_name}")
    loss = supervised.mean()
    return loss + config.hard_negative_weight * _hard_negative_penalty(
        logits,
        labels,
        config,
        label_genes=label_genes,
    )


def _validate_training_config(config: TrainingConfig) -> None:
    if config.strategy not in STRATEGIES:
        raise ValueError(f"UNKNOWN_BALANCING_STRATEGY: {config.strategy}")
    if config.loss_name not in LOSS_NAMES:
        raise ValueError(f"UNKNOWN_LOSS_NAME: {config.loss_name}")
    if config.focal_gamma < 0:
        raise ValueError("FOCAL_GAMMA_MUST_BE_NON_NEGATIVE")
    if config.hard_negative_weight < 0:
        raise ValueError("HARD_NEGATIVE_WEIGHT_MUST_BE_NON_NEGATIVE")
    if config.hard_negative_margin < 0:
        raise ValueError("HARD_NEGATIVE_MARGIN_MUST_BE_NON_NEGATIVE")


def _run_logits(model: PhenotypeGeneClassifier, data: ClinicalTensorData) -> Tensor:
    model.eval()
    with torch.no_grad():
        logits = model(
            data.phenotype,
            data.pedigree,
            data.sex,
            data.aao_group,
            data.zygosity,
            data.inheritance,
            data.family_history,
            data.aao_numeric,
            data.aao_missing,
        )
    return cast(Tensor, logits)


def _metric_float(metrics: dict[str, object], key: str) -> float:
    value = metrics[key]
    if isinstance(value, int | float):
        return float(value)
    raise TypeError(f"METRIC_NOT_NUMERIC: {key}")


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def expected_calibration_error(probs: Tensor, labels: Tensor, *, bins: int = 10) -> float:
    if int(labels.shape[0]) == 0:
        return 0.0
    confidences, predictions = probs.max(dim=1)
    total = float(labels.shape[0])
    ece = 0.0
    for bin_idx in range(bins):
        lower = bin_idx / bins
        upper = (bin_idx + 1) / bins
        if bin_idx == bins - 1:
            mask = (confidences >= lower) & (confidences <= upper)
        else:
            mask = (confidences >= lower) & (confidences < upper)
        bin_count = int(mask.sum().item())
        if bin_count == 0:
            continue
        bin_accuracy = (predictions[mask] == labels[mask]).float().mean().item()
        bin_confidence = confidences[mask].mean().item()
        ece += (bin_count / total) * abs(bin_accuracy - bin_confidence)
    return float(ece)


def confidence_distribution(probs: Tensor, *, bins: int = 10) -> list[dict[str, float]]:
    if int(probs.shape[0]) == 0:
        return []
    confidences = probs.max(dim=1).values
    rows: list[dict[str, float]] = []
    for bin_idx in range(bins):
        lower = bin_idx / bins
        upper = (bin_idx + 1) / bins
        if bin_idx == bins - 1:
            mask = (confidences >= lower) & (confidences <= upper)
        else:
            mask = (confidences >= lower) & (confidences < upper)
        rows.append(
            {
                "lower": lower,
                "upper": upper,
                "count": float(mask.sum().item()),
            }
        )
    return rows


def classification_metrics(
    logits: Tensor,
    labels: Tensor,
    *,
    temperature: float = 1.0,
    label_genes: tuple[str, ...] = GENES,
) -> dict[str, object]:
    _validate_label_genes(label_genes)
    if int(labels.shape[0]) == 0:
        return {
            "support": 0,
            "top1_accuracy": 0.0,
            "top2_accuracy": 0.0,
            "top3_accuracy": 0.0,
            "balanced_accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "micro_f1": 0.0,
            "brier_score": 0.0,
            "ece": 0.0,
            "confusion_matrix": [[0 for _ in label_genes] for _ in label_genes],
            "per_gene": {},
        }

    scaled_logits = logits / max(temperature, 1e-6)
    probs = F.softmax(scaled_logits, dim=1)
    predictions = probs.argmax(dim=1)
    top2 = torch.topk(probs, k=min(2, len(label_genes)), dim=1).indices
    top3 = torch.topk(probs, k=min(3, len(label_genes)), dim=1).indices
    confusion = [[0 for _ in label_genes] for _ in label_genes]
    for true_idx, pred_idx in zip(labels.tolist(), predictions.tolist(), strict=True):
        confusion[int(true_idx)][int(pred_idx)] += 1

    per_gene: dict[str, dict[str, float]] = {}
    precisions: list[float] = []
    recalls: list[float] = []
    f1s: list[float] = []
    supported_recalls: list[float] = []
    for idx, gene in enumerate(label_genes):
        tp = float(confusion[idx][idx])
        support = float(sum(confusion[idx]))
        predicted = float(sum(row[idx] for row in confusion))
        precision = _safe_div(tp, predicted)
        recall = _safe_div(tp, support)
        f1 = _safe_div(2.0 * precision * recall, precision + recall)
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        if support:
            supported_recalls.append(recall)
        per_gene[gene] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    one_hot = F.one_hot(labels, num_classes=len(label_genes)).float()
    brier = torch.sum((probs - one_hot) ** 2, dim=1).mean().item()
    top2_hits = (top2 == labels.unsqueeze(1)).any(dim=1).float().mean().item()
    top3_hits = (top3 == labels.unsqueeze(1)).any(dim=1).float().mean().item()
    accuracy = (predictions == labels).float().mean().item()
    return {
        "support": int(labels.shape[0]),
        "top1_accuracy": float(accuracy),
        "top2_accuracy": float(top2_hits),
        "top3_accuracy": float(top3_hits),
        "balanced_accuracy": float(sum(supported_recalls) / len(supported_recalls))
        if supported_recalls
        else 0.0,
        "macro_precision": float(sum(precisions) / len(precisions)),
        "macro_recall": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
        "micro_f1": float(accuracy),
        "brier_score": float(brier),
        "ece": expected_calibration_error(probs, labels),
        "confidence_distribution": confidence_distribution(probs),
        "confusion_matrix": confusion,
        "per_gene": per_gene,
    }


def evaluate_model(
    model: PhenotypeGeneClassifier,
    data: ClinicalTensorData,
    *,
    temperature: float = 1.0,
) -> dict[str, object]:
    label_genes = cast(tuple[str, ...], getattr(model, "label_genes", GENES))
    return classification_metrics(
        _run_logits(model, data),
        data.labels,
        temperature=temperature,
        label_genes=label_genes,
    )


def _train_optimizer_steps(
    model: PhenotypeGeneClassifier,
    data: ClinicalTensorData,
    *,
    config: TrainingConfig,
    steps: int,
    seed: int,
    loss_weights: Tensor | None,
    label_genes: tuple[str, ...] = GENES,
) -> list[float]:
    if len(data) == 0:
        raise ValueError("EMPTY_TRAINING_DATA")
    model.train()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    losses: list[float] = []
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    epoch_indices = _epoch_indices(
        data.labels,
        config.strategy,
        seed=seed,
        epoch=0,
        batch_size=config.batch_size,
    )
    offset = 0
    for step in range(steps):
        if offset + config.batch_size > int(epoch_indices.shape[0]):
            epoch_indices = _epoch_indices(
                data.labels,
                config.strategy,
                seed=seed,
                epoch=step + 1,
                batch_size=config.batch_size,
            )
            offset = 0
        indices = epoch_indices[offset : offset + config.batch_size]
        if int(indices.shape[0]) == 0:
            indices = torch.randint(0, len(data), (config.batch_size,), generator=generator)
        offset += config.batch_size
        optimizer.zero_grad(set_to_none=True)
        logits = model(*_batch(data, indices))
        loss = _classification_loss(
            logits,
            data.labels[indices],
            config=config,
            loss_weights=loss_weights,
            label_genes=label_genes,
        )
        loss.backward()  # type: ignore[no-untyped-call]
        optimizer.step()
        losses.append(float(loss.detach().item()))
    return losses


def train_centralized(
    encoder: ClinicalEncoder,
    train_records: tuple[ClinicalRecord, ...],
    validation_records: tuple[ClinicalRecord, ...],
    *,
    config: TrainingConfig,
) -> TrainingResult:
    _validate_training_config(config)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    torch.manual_seed(config.seed)
    train_data = encoder.encode_records(train_records)
    validation_data = encoder.encode_records(validation_records)
    model = make_model(encoder, seed=config.seed)
    loss_weights = _loss_weights(
        train_data.labels,
        config.strategy,
        num_classes=len(encoder.label_genes),
    )
    steps_per_epoch = max(1, math.ceil(len(train_data) / config.batch_size))
    best_macro_f1 = -1.0
    best_epoch = 0
    best_state: dict[str, Tensor] = {
        key: value.detach().cpu().clone() for key, value in model.state_dict().items()
    }
    history: list[dict[str, float]] = []

    for epoch in range(1, config.epochs + 1):
        losses = _train_optimizer_steps(
            model,
            train_data,
            config=config,
            steps=steps_per_epoch,
            seed=config.seed + epoch * 17,
            loss_weights=loss_weights,
            label_genes=encoder.label_genes,
        )
        validation_metrics = evaluate_model(model, validation_data)
        macro_f1 = _metric_float(validation_metrics, "macro_f1")
        history.append(
            {
                "epoch": float(epoch),
                "train_loss": sum(losses) / len(losses),
                "validation_macro_f1": macro_f1,
                "validation_top1_accuracy": _metric_float(
                    validation_metrics,
                    "top1_accuracy",
                ),
            }
        )
        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_epoch = epoch
            best_state = {
                key: value.detach().cpu().clone() for key, value in model.state_dict().items()
            }

    model.load_state_dict(best_state)
    return TrainingResult(
        model=model,
        strategy=config.strategy,
        best_epoch=best_epoch,
        history=history,
        train_metrics=evaluate_model(model, train_data),
        validation_metrics=evaluate_model(model, validation_data),
    )


def train_strategy_comparison(
    encoder: ClinicalEncoder,
    train_records: tuple[ClinicalRecord, ...],
    validation_records: tuple[ClinicalRecord, ...],
    *,
    base_config: TrainingConfig,
    strategies: Iterable[str] = STRATEGIES,
) -> tuple[TrainingResult, ...]:
    results: list[TrainingResult] = []
    for strategy in strategies:
        config = TrainingConfig(
            seed=base_config.seed,
            epochs=base_config.epochs,
            batch_size=base_config.batch_size,
            learning_rate=base_config.learning_rate,
            weight_decay=base_config.weight_decay,
            label_smoothing=base_config.label_smoothing,
            loss_name=base_config.loss_name,
            focal_gamma=base_config.focal_gamma,
            hard_negative_weight=base_config.hard_negative_weight,
            hard_negative_margin=base_config.hard_negative_margin,
            hard_negative_pairs=base_config.hard_negative_pairs,
            strategy=strategy,
        )
        results.append(
            train_centralized(
                encoder,
                train_records,
                validation_records,
                config=config,
            )
        )
    return tuple(results)


def select_best_by_macro_f1(results: tuple[TrainingResult, ...]) -> TrainingResult:
    if not results:
        raise ValueError("NO_TRAINING_RESULTS")
    return max(
        results,
        key=lambda result: (
            _metric_float(result.validation_metrics, "macro_f1"),
            _metric_float(result.validation_metrics, "top1_accuracy"),
        ),
    )


def partition_records_for_nodes(
    records: tuple[ClinicalRecord, ...],
    *,
    num_nodes: int,
    seed: int,
    label_genes: tuple[str, ...] = GENES,
) -> tuple[tuple[ClinicalRecord, ...], ...]:
    if num_nodes <= 0:
        raise ValueError("NUM_NODES_MUST_BE_POSITIVE")
    by_gene: dict[str, list[ClinicalRecord]] = defaultdict(list)
    for record in records:
        by_gene[record.gene].append(record)
    rng = random.Random(seed)
    nodes: list[list[ClinicalRecord]] = [[] for _ in range(num_nodes)]
    for gene in label_genes:
        gene_records = list(by_gene.get(gene, ()))
        rng.shuffle(gene_records)
        for idx, record in enumerate(gene_records):
            nodes[idx % num_nodes].append(record)
    for node in nodes:
        node.sort(key=lambda record: record.record_id)
    return tuple(tuple(node) for node in nodes)


@dataclass(frozen=True, slots=True)
class DeltaReduceTrainingResult:
    model: PhenotypeGeneClassifier
    round_history: list[dict[str, float]]
    validation_metrics: dict[str, object]


def train_deltareduce_classifier(
    encoder: ClinicalEncoder,
    train_records: tuple[ClinicalRecord, ...],
    validation_records: tuple[ClinicalRecord, ...],
    *,
    config: TrainingConfig,
    num_nodes: int = 4,
    rounds: int = 5,
    steps_per_round: int = 35,
) -> DeltaReduceTrainingResult:
    """Train the classifier through existing LocalDelta normalization semantics."""

    _validate_training_config(config)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    global_model = make_model(encoder, seed=config.seed)
    schema = derive_parameter_schema(global_model)
    current_global_params = snapshot_fp32_parameters(global_model, schema)
    node_records = partition_records_for_nodes(
        train_records,
        num_nodes=num_nodes,
        seed=config.seed,
        label_genes=encoder.label_genes,
    )
    node_data = tuple(encoder.encode_records(records) for records in node_records)
    validation_data = encoder.encode_records(validation_records)
    full_train_data = encoder.encode_records(train_records)
    loss_weights = _loss_weights(
        full_train_data.labels,
        config.strategy,
        num_classes=len(encoder.label_genes),
    )
    history: list[dict[str, float]] = []

    for round_idx in range(1, rounds + 1):
        normalized_deltas: list[dict[str, Tensor]] = []
        round_losses: list[float] = []
        for node_idx, data in enumerate(node_data):
            local_model = make_model(encoder, seed=config.seed + round_idx * 101 + node_idx)
            with torch.no_grad():
                for name, parameter in local_model.named_parameters():
                    parameter.copy_(current_global_params[name])
            losses = _train_optimizer_steps(
                local_model,
                data,
                config=config,
                steps=steps_per_round,
                seed=config.seed + round_idx * 1000 + node_idx,
                loss_weights=loss_weights,
                label_genes=encoder.label_genes,
            )
            round_losses.extend(losses)
            local_delta = build_local_delta(
                current_global_params,
                snapshot_fp32_parameters(local_model, schema),
                schema,
            )
            normalized_deltas.append(
                normalize_local_delta(
                    local_delta,
                    schema,
                    effective_steps=steps_per_round,
                    step_budget=steps_per_round,
                )
            )

        merged_delta: dict[str, Tensor] = {}
        coefficient = 1.0 / len(normalized_deltas)
        for name in current_global_params:
            accumulator = torch.zeros_like(current_global_params[name])
            for delta in normalized_deltas:
                accumulator = accumulator + (coefficient * delta[name])
            merged_delta[name] = accumulator * float(steps_per_round)
        current_global_params = reconstruct_final(current_global_params, merged_delta, schema)
        with torch.no_grad():
            for name, parameter in global_model.named_parameters():
                parameter.copy_(current_global_params[name])
        metrics = evaluate_model(global_model, validation_data)
        history.append(
            {
                "round": float(round_idx),
                "mean_local_loss": sum(round_losses) / len(round_losses),
                "validation_macro_f1": _metric_float(metrics, "macro_f1"),
                "validation_top1_accuracy": _metric_float(metrics, "top1_accuracy"),
            }
        )

    return DeltaReduceTrainingResult(
        model=global_model,
        round_history=history,
        validation_metrics=evaluate_model(global_model, validation_data),
    )


def fit_temperature(
    model: PhenotypeGeneClassifier,
    calibration_data: ClinicalTensorData,
) -> dict[str, float]:
    if len(calibration_data) == 0:
        return {"temperature": 1.0, "nll": 0.0}
    logits = _run_logits(model, calibration_data)
    candidates = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    scored: list[tuple[float, float]] = []
    for temperature in candidates:
        nll = F.cross_entropy(logits / temperature, calibration_data.labels).item()
        scored.append((float(nll), temperature))
    best_nll, best_temperature = min(scored, key=lambda item: item[0])
    return {"temperature": best_temperature, "nll": best_nll}


def ranking_for_record(
    model: PhenotypeGeneClassifier,
    encoder: ClinicalEncoder,
    record: ClinicalRecord,
    *,
    temperature: float = 1.0,
) -> list[RankingRow]:
    data = encoder.encode_records((record,))
    probs = F.softmax(_run_logits(model, data) / temperature, dim=1)[0]
    label_genes = cast(tuple[str, ...], getattr(model, "label_genes", encoder.label_genes))
    ranking: list[RankingRow] = [
        {"gene": gene, "probability": float(probs[idx].item())}
        for idx, gene in enumerate(label_genes)
    ]
    ranking.sort(key=lambda row: row["probability"], reverse=True)
    return ranking


def logits_for_record(
    model: PhenotypeGeneClassifier,
    encoder: ClinicalEncoder,
    record: ClinicalRecord,
) -> dict[str, float]:
    data = encoder.encode_records((record,))
    logits = _run_logits(model, data)[0]
    label_genes = cast(tuple[str, ...], getattr(model, "label_genes", encoder.label_genes))
    return {gene: float(logits[idx].item()) for idx, gene in enumerate(label_genes)}


def clone_record_with_features(
    record: ClinicalRecord,
    phenotype_features: tuple[str, ...],
) -> ClinicalRecord:
    digest = hashlib.sha256("|".join(phenotype_features).encode("utf-8")).hexdigest()[:12]
    return ClinicalRecord(
        record_id=f"{record.record_id}:features:{digest}",
        gene=record.gene,
        publication_id=record.publication_id,
        family_id=record.family_id,
        individual_id=record.individual_id,
        sex=record.sex,
        aao_years=record.aao_years,
        aao_group=record.aao_group,
        aao_missing=record.aao_missing,
        zygosity=record.zygosity,
        inheritance=record.inheritance,
        family_history=record.family_history,
        phenotype_features=phenotype_features,
        pedigree_features=record.pedigree_features,
        feature_statuses=record.feature_statuses,
        source_columns=record.source_columns,
        publication_missing=record.publication_missing,
    )
