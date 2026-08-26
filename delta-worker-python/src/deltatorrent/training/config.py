"""Strict versioned baseline configuration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from deltatorrent.domain.errors import DeltaError, ErrorCode

CONFIG_SCHEMA_VERSION = "1.0.0"


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.SCHEMA_INVALID, message, details)


@dataclass(frozen=True, slots=True)
class BaselineConfig:
    run_id: str
    corpus_path: str
    tokenizer_path: str
    output_dir: str
    seed: int
    device: str
    dtype: str
    sequence_length: int
    batch_size: int
    gradient_accumulation_steps: int
    optimizer_steps: int
    checkpoint_every_optimizer_steps: int
    vocab_size: int
    hidden_size: int
    learning_rate_nanos: int
    weight_decay_ppm: int
    beta1_ppm: int
    beta2_ppm: int
    epsilon_nanos: int
    schema_version: str = CONFIG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CONFIG_SCHEMA_VERSION:
            raise _invalid("CONFIG_VERSION_UNSUPPORTED", schema_version=self.schema_version)
        if not self.run_id or len(self.run_id) > 128:
            raise _invalid("run_id is invalid")
        if any(not item for item in (self.corpus_path, self.tokenizer_path, self.output_dir)):
            raise _invalid("config paths must be non-empty")
        if self.device != "cpu" or self.dtype != "float32":
            raise _invalid("feature 001 supports only cpu/float32 reproducibility class")
        integer_fields = {
            "batch_size": self.batch_size,
            "beta1_ppm": self.beta1_ppm,
            "beta2_ppm": self.beta2_ppm,
            "checkpoint_every_optimizer_steps": self.checkpoint_every_optimizer_steps,
            "epsilon_nanos": self.epsilon_nanos,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "hidden_size": self.hidden_size,
            "learning_rate_nanos": self.learning_rate_nanos,
            "optimizer_steps": self.optimizer_steps,
            "seed": self.seed,
            "sequence_length": self.sequence_length,
            "vocab_size": self.vocab_size,
            "weight_decay_ppm": self.weight_decay_ppm,
        }
        for name, value in integer_fields.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise _invalid("config integer must be non-negative", field=name)
        positive = (
            self.batch_size,
            self.checkpoint_every_optimizer_steps,
            self.epsilon_nanos,
            self.gradient_accumulation_steps,
            self.hidden_size,
            self.learning_rate_nanos,
            self.optimizer_steps,
            self.sequence_length,
            self.vocab_size,
        )
        if any(value == 0 for value in positive):
            raise _invalid("config dimensions and schedules must be positive")
        if not 0 <= self.beta1_ppm < self.beta2_ppm < 1_000_000:
            raise _invalid("AdamW betas must satisfy 0 <= beta1 < beta2 < 1")
        if self.weight_decay_ppm > 1_000_000:
            raise _invalid("weight_decay_ppm cannot exceed one")

    @property
    def learning_rate(self) -> float:
        return self.learning_rate_nanos / 1_000_000_000

    @property
    def weight_decay(self) -> float:
        return self.weight_decay_ppm / 1_000_000

    @property
    def beta1(self) -> float:
        return self.beta1_ppm / 1_000_000

    @property
    def beta2(self) -> float:
        return self.beta2_ppm / 1_000_000

    @property
    def epsilon(self) -> float:
        return self.epsilon_nanos / 1_000_000_000

    def to_dict(self) -> dict[str, object]:
        return {
            "batch_size": self.batch_size,
            "beta1_ppm": self.beta1_ppm,
            "beta2_ppm": self.beta2_ppm,
            "checkpoint_every_optimizer_steps": self.checkpoint_every_optimizer_steps,
            "corpus_path": self.corpus_path,
            "device": self.device,
            "dtype": self.dtype,
            "epsilon_nanos": self.epsilon_nanos,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "hidden_size": self.hidden_size,
            "learning_rate_nanos": self.learning_rate_nanos,
            "optimizer_steps": self.optimizer_steps,
            "output_dir": self.output_dir,
            "run_id": self.run_id,
            "schema_version": self.schema_version,
            "seed": self.seed,
            "sequence_length": self.sequence_length,
            "tokenizer_path": self.tokenizer_path,
            "vocab_size": self.vocab_size,
            "weight_decay_ppm": self.weight_decay_ppm,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> Self:
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise _invalid(
                "CONFIG_FIELDS_INVALID",
                missing=sorted(expected - set(value)),
                unknown=sorted(set(value) - expected),
            )
        try:
            return cls(**value)
        except TypeError as exc:
            raise _invalid("CONFIG_FIELD_TYPE_INVALID") from exc

    @classmethod
    def from_json_file(cls, path: Path) -> Self:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _invalid("CONFIG_JSON_INVALID", path=str(path)) from exc
        if not isinstance(value, dict):
            raise _invalid("CONFIG_ROOT_NOT_OBJECT")
        return cls.from_mapping(value)


def migrate_config(value: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit migration boundary; v1 has no legacy migrations."""

    if value.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise _invalid("CONFIG_MIGRATION_UNAVAILABLE")
    return dict(value)
