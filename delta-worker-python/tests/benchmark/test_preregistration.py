from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.preregistration import PreregisteredDefinition, PreregistrationStore
from deltatorrent.benchmark.review import GovernanceAttestation, GovernanceVote, ReviewError

ROOT = Path(__file__).parents[3]
FIXTURE = ROOT / "delta-protocol/fixtures/010/valid/benchmark-contract-v1.json"


def definition() -> BenchmarkDefinition:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return BenchmarkDefinition.from_dict(document["artifacts"]["definition"]["value"])


def attestation(value: BenchmarkDefinition) -> GovernanceAttestation:
    members = ("v0", "v1", "v2", "v3")
    set_id = "sha256:" + "a" * 64
    votes = tuple(
        GovernanceVote(member, set_id, value.content_id, "DEFINITION") for member in members[:3]
    )
    return GovernanceAttestation.finalize(
        body_id=value.content_id,
        validator_set_id=set_id,
        purpose="DEFINITION",
        validator_ids=members,
        f_b=1,
        votes=votes,
    )


def test_preregistration_is_create_only_and_idempotent(tmp_path: Path) -> None:
    value = definition()
    preregistration = PreregisteredDefinition(value, attestation(value))
    store = PreregistrationStore(tmp_path)

    first = store.seal(preregistration)
    second = store.seal(preregistration)

    assert first == second
    assert first.read_bytes() == second.read_bytes()


def test_post_attestation_change_gets_new_identity(tmp_path: Path) -> None:
    original = definition()
    original_path = PreregistrationStore(tmp_path).seal(
        PreregisteredDefinition(original, attestation(original))
    )
    changed = copy.deepcopy(original.raw)
    changed["seeds"] = [31, 37]
    changed_definition = BenchmarkDefinition.from_dict(changed)

    changed_path = PreregistrationStore(tmp_path).seal(
        PreregisteredDefinition(changed_definition, attestation(changed_definition))
    )

    assert changed_path != original_path
    assert original.content_id != changed_definition.content_id


def test_insufficient_or_duplicate_votes_fail() -> None:
    value = definition()
    members = ("v0", "v1", "v2", "v3")
    set_id = "sha256:" + "b" * 64

    with pytest.raises(ReviewError, match="QUORUM_INSUFFICIENT"):
        GovernanceAttestation.finalize(
            body_id=value.content_id,
            validator_set_id=set_id,
            purpose="DEFINITION",
            validator_ids=members,
            f_b=1,
            votes=tuple(
                GovernanceVote(member, set_id, value.content_id, "DEFINITION")
                for member in members[:2]
            ),
        )
    duplicate = GovernanceVote("v0", set_id, value.content_id, "DEFINITION")
    with pytest.raises(ReviewError, match="VOTE_DUPLICATE"):
        GovernanceAttestation.finalize(
            body_id=value.content_id,
            validator_set_id=set_id,
            purpose="DEFINITION",
            validator_ids=members,
            f_b=1,
            votes=(
                duplicate,
                duplicate,
                GovernanceVote("v1", set_id, value.content_id, "DEFINITION"),
            ),
        )
