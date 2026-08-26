"""Deterministic tokenizer, fixed windows and sampler cursor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from deltatorrent.domain.errors import DeltaError, ErrorCode


@dataclass(frozen=True, slots=True)
class Tokenizer:
    vocabulary: Mapping[str, int]
    pad_token: str
    unknown_token: str

    def __post_init__(self) -> None:
        vocabulary = dict(self.vocabulary)
        if (
            not vocabulary
            or len(set(vocabulary.values())) != len(vocabulary)
            or sorted(vocabulary.values()) != list(range(len(vocabulary)))
            or self.pad_token not in vocabulary
            or self.unknown_token not in vocabulary
        ):
            raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_VOCABULARY_INVALID")
        object.__setattr__(self, "vocabulary", MappingProxyType(vocabulary))

    @property
    def pad_id(self) -> int:
        return self.vocabulary[self.pad_token]

    def encode(self, text: str) -> tuple[int, ...]:
        unknown = self.vocabulary[self.unknown_token]
        return tuple(self.vocabulary.get(token, unknown) for token in text.split())

    @classmethod
    def from_json_file(cls, path: Path) -> Tokenizer:
        try:
            return cls.from_json_bytes(path.read_bytes())
        except OSError as exc:
            raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_JSON_INVALID") from exc

    @classmethod
    def from_json_bytes(cls, payload: bytes) -> Tokenizer:
        try:
            value = json.loads(payload.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_JSON_INVALID") from exc
        if not isinstance(value, dict) or set(value) != {
            "pad_token",
            "schema_version",
            "unknown_token",
            "vocabulary",
        }:
            raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_SCHEMA_INVALID")
        if value["schema_version"] != "1.0.0" or not isinstance(value["vocabulary"], dict):
            raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_SCHEMA_INVALID")
        vocabulary: dict[str, int] = {}
        for key, item in value["vocabulary"].items():
            if not isinstance(key, str) or isinstance(item, bool) or not isinstance(item, int):
                raise DeltaError(ErrorCode.SCHEMA_INVALID, "TOKENIZER_VOCABULARY_INVALID")
            vocabulary[key] = item
        return cls(vocabulary, value["pad_token"], value["unknown_token"])


@dataclass(frozen=True, slots=True)
class TokenSample:
    inputs: tuple[int, ...]
    targets: tuple[int, ...]


def load_samples(
    corpus: Path, tokenizer: Tokenizer, sequence_length: int
) -> tuple[TokenSample, ...]:
    try:
        text = corpus.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DeltaError(ErrorCode.SCHEMA_INVALID, "CORPUS_INVALID") from exc
    return load_samples_from_text(text, tokenizer, sequence_length)


def load_samples_from_text(
    text: str, tokenizer: Tokenizer, sequence_length: int
) -> tuple[TokenSample, ...]:
    tokens = tokenizer.encode(text)
    width = sequence_length + 1
    samples = tuple(
        TokenSample(window[:-1], window[1:])
        for start in range(0, len(tokens) - width + 1, sequence_length)
        if len(window := tokens[start : start + width]) == width
    )
    if not samples:
        raise DeltaError(ErrorCode.SCHEMA_INVALID, "CORPUS_TOO_SHORT")
    return samples


@dataclass(slots=True)
class DeterministicSampler:
    sample_count: int
    seed: int
    cursor: int = 0

    def __post_init__(self) -> None:
        if self.sample_count <= 0 or self.seed < 0 or self.cursor < 0:
            raise ValueError("SAMPLER_STATE_INVALID")

    def take(self, count: int) -> tuple[int, ...]:
        if count <= 0:
            raise ValueError("SAMPLER_BATCH_INVALID")
        result = tuple(self._index_at(self.cursor + offset) for offset in range(count))
        self.cursor += count
        return result

    def _index_at(self, cursor: int) -> int:
        epoch, position = divmod(cursor, self.sample_count)
        order = sorted(
            range(self.sample_count),
            key=lambda index: hashlib.sha256(
                f"deltareduce.sampler.v1:{self.seed}:{epoch}:{index}".encode()
            ).digest(),
        )
        return order[position]


def tokenizer_payload(tokenizer: Tokenizer) -> dict[str, Any]:
    return {
        "pad_token": tokenizer.pad_token,
        "schema_version": "1.0.0",
        "unknown_token": tokenizer.unknown_token,
        "vocabulary": dict(tokenizer.vocabulary),
    }
