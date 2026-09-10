"""Publication-disjoint split utilities for clinical classifier runs."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass

from deltatorrent.clinical.canonical_features import GENES
from deltatorrent.clinical.gold_loader import ClinicalRecord

SPLIT_NAMES: tuple[str, ...] = ("train", "validation", "calibration", "test")


@dataclass(frozen=True, slots=True)
class SplitResult:
    train: tuple[ClinicalRecord, ...]
    validation: tuple[ClinicalRecord, ...]
    calibration: tuple[ClinicalRecord, ...]
    test: tuple[ClinicalRecord, ...]
    split_by_record_id: dict[str, str]
    split_by_publication_id: dict[str, str]

    def records_for(self, split_name: str) -> tuple[ClinicalRecord, ...]:
        if split_name == "train":
            return self.train
        if split_name == "validation":
            return self.validation
        if split_name == "calibration":
            return self.calibration
        if split_name == "test":
            return self.test
        raise ValueError(f"UNKNOWN_SPLIT: {split_name}")


def publication_disjoint_split(
    records: tuple[ClinicalRecord, ...],
    *,
    seed: int = 42,
    ratios: Mapping[str, float] | None = None,
) -> SplitResult:
    """Create a deterministic split where each publication appears in one split only."""

    split_ratios = dict(
        ratios
        or {
            "train": 0.65,
            "validation": 0.15,
            "calibration": 0.10,
            "test": 0.10,
        }
    )
    if tuple(split_ratios) != SPLIT_NAMES:
        raise ValueError(f"SPLIT_RATIOS_MUST_USE_ORDERED_KEYS: {SPLIT_NAMES}")
    total_ratio = sum(split_ratios.values())
    if abs(total_ratio - 1.0) > 1e-9:
        raise ValueError("SPLIT_RATIOS_MUST_SUM_TO_ONE")

    groups: dict[str, list[ClinicalRecord]] = defaultdict(list)
    for record in records:
        groups[record.publication_id].append(record)

    total_by_gene = Counter(record.gene for record in records)
    target_total = {name: len(records) * split_ratios[name] for name in SPLIT_NAMES}
    target_by_gene = {
        name: {gene: total_by_gene[gene] * split_ratios[name] for gene in GENES}
        for name in SPLIT_NAMES
    }

    rng = random.Random(seed)
    assigned: dict[str, list[ClinicalRecord]] = {name: [] for name in SPLIT_NAMES}
    assigned_by_gene: dict[str, Counter[str]] = {name: Counter() for name in SPLIT_NAMES}
    assigned_total: Counter[str] = Counter()
    split_by_publication_id: dict[str, str] = {}

    publications_by_gene: dict[str, set[str]] = defaultdict(set)
    for publication_id, group_records in groups.items():
        for gene in {record.gene for record in group_records}:
            publications_by_gene[gene].add(publication_id)

    gene_order = sorted(GENES, key=lambda gene: (total_by_gene[gene], gene))

    def assign_publication(
        publication_id: str,
        *,
        focus_gene: str | None,
    ) -> None:
        if publication_id in split_by_publication_id:
            return
        group_records = groups[publication_id]
        group_counts = Counter(record.gene for record in group_records)
        group_size = len(group_records)

        def split_score(
            split_name: str,
        ) -> float:
            current_total = assigned_total[split_name]
            next_total = assigned_total[split_name] + group_size
            current_total_score = (
                (current_total - target_total[split_name]) / max(1.0, target_total[split_name])
            ) ** 2
            next_total_score = (
                (next_total - target_total[split_name]) / max(1.0, target_total[split_name])
            ) ** 2
            total_score = next_total_score - current_total_score
            gene_delta_score = 0.0
            for gene, count in group_counts.items():
                target = max(1.0, target_by_gene[split_name][gene])
                current_gene_total = assigned_by_gene[split_name][gene]
                next_gene_total = assigned_by_gene[split_name][gene] + count
                rarity_weight = 1.0 / math.sqrt(max(1, total_by_gene[gene]))
                focus_weight = 4.0 if gene == focus_gene else 1.0
                current_gene_score = ((current_gene_total - target) / target) ** 2
                next_gene_score = ((next_gene_total - target) / target) ** 2
                gene_delta_score += (
                    focus_weight * rarity_weight * (next_gene_score - current_gene_score)
                )
            return (0.05 * total_score) + gene_delta_score

        chosen_split = min(SPLIT_NAMES, key=lambda name: (split_score(name), name))
        assigned[chosen_split].extend(group_records)
        assigned_total[chosen_split] += len(group_records)
        assigned_by_gene[chosen_split].update(group_counts)
        split_by_publication_id[publication_id] = chosen_split

    for gene in gene_order:
        publications = list(publications_by_gene.get(gene, ()))
        rng.shuffle(publications)
        publications.sort(key=lambda pub: (-len([r for r in groups[pub] if r.gene == gene]), pub))
        for publication_id in publications:
            assign_publication(publication_id, focus_gene=gene)

    for publication_id in sorted(groups):
        assign_publication(publication_id, focus_gene=None)

    split_by_record_id = {
        record.record_id: split_name
        for split_name in SPLIT_NAMES
        for record in assigned[split_name]
    }
    result = SplitResult(
        train=tuple(assigned["train"]),
        validation=tuple(assigned["validation"]),
        calibration=tuple(assigned["calibration"]),
        test=tuple(assigned["test"]),
        split_by_record_id=split_by_record_id,
        split_by_publication_id=split_by_publication_id,
    )
    assert_publication_isolation(result)
    return result


def assert_publication_isolation(split: SplitResult) -> None:
    seen: dict[str, str] = {}
    for split_name in SPLIT_NAMES:
        for record in split.records_for(split_name):
            existing = seen.setdefault(record.publication_id, split_name)
            if existing != split_name:
                raise ValueError(
                    "PUBLICATION_SPLIT_LEAKAGE",
                    record.publication_id,
                    existing,
                    split_name,
                )


def split_hash(split: SplitResult) -> str:
    payload = {
        "schema": "clinical-publication-split-v1",
        "splits": {
            name: sorted(record.record_id for record in split.records_for(name))
            for name in SPLIT_NAMES
        },
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def split_summary(split: SplitResult) -> dict[str, object]:
    summary: dict[str, object] = {
        "split_hash": split_hash(split),
        "publication_disjoint": True,
        "splits": {},
    }
    split_payload: dict[str, object] = {}
    for split_name in SPLIT_NAMES:
        records = split.records_for(split_name)
        split_payload[split_name] = {
            "records": len(records),
            "records_per_gene": dict(sorted(Counter(record.gene for record in records).items())),
            "unique_publications": len({record.publication_id for record in records}),
            "unique_families": len(
                {(record.publication_id, record.family_id) for record in records}
            ),
        }
    summary["splits"] = split_payload
    return summary
