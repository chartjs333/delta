from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from campaign02_chain_fixtures import certified_plan, certified_result, contributions
from deltatorrent.benchmark.feature008_admission import (
    CertificateArtifact,
    CtypesFeature008NativeChainVerifier,
    Feature008AdmissionError,
    Feature008ChainVerifier,
)

ROOT = Path(__file__).resolve().parents[3]
CORPUS = (
    ROOT
    / "delta-protocol"
    / "fixtures"
    / "010"
    / "campaign-02"
    / "native-chain-conformance-v1.json"
)


def _native_library() -> Path:
    candidates = [
        Path(value)
        for value in [
            os.environ.get("DELTA_FFI_LIBRARY"),
            ROOT / "out" / "build" / "cpp20" / "Debug" / "delta_ffi.dll",
            ROOT / "out" / "build" / "cpp20" / "libdelta_ffi.so",
            ROOT / "out" / "build" / "cpp20" / "libdelta_ffi.dylib",
        ]
        if value is not None
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    pytest.skip("delta_ffi shared library is not available for cross-language conformance")


def test_python_native_and_c_abi_decisions_match_the_corpus() -> None:
    verifier = CtypesFeature008NativeChainVerifier(_native_library())
    corpus = json.loads(CORPUS.read_bytes())
    assert corpus["type_name"] == "CAMPAIGN02_NATIVE_CHAIN_CONFORMANCE_CORPUS"
    assert len(corpus["cases"]) == 12
    decisions: dict[str, str] = {}
    for case in corpus["cases"]:
        try:
            receipt = verifier.verify_canonical_bundle(
                bytes.fromhex(case["bundle_bytes_hex"]),
                execution_plan_id=case["execution_plan_id"],
                certified_round_policy_id=case["policy_id"],
                parent_checkpoint_id=case["parent_checkpoint_id"],
                final_checkpoint_id=case["final_checkpoint_id"],
                runtime_state_id=case["runtime_state_id"],
                effect_set_id=case["effect_set_id"],
                runtime_wal_sha256=case["runtime_wal_sha256"],
                checkpoint_wal_sha256=case["checkpoint_wal_sha256"],
            )
            assert receipt.value["status"] == "ACCEPT"
            decision = "ACCEPT"
        except Feature008AdmissionError:
            decision = "REJECT"
        decisions[case["name"]] = decision
        assert (
            decision
            == case["python_admission"]
            == case["native_chain_verifier"]
            == case["c_abi"]
            == case["expected"]
        )
    assert decisions == {
        "incomplete-shard-coverage": "REJECT",
        "invalid-nested-content-id": "REJECT",
        "noncanonical-squared-norm": "REJECT",
        "reversed-apc-weights": "REJECT",
        "unordered-norm-entries": "REJECT",
        "unordered-seed-shares": "REJECT",
        "unordered-signers": "REJECT",
        "unreduced-rational": "REJECT",
        "valid-complete-chain": "ACCEPT",
        "wrong-required-key-order": "REJECT",
        "wrong-seed-parent": "REJECT",
        "zero-denominator": "REJECT",
    }


@pytest.mark.parametrize(
    ("case_name", "artifact_name"),
    [
        ("invalid-nested-content-id", "parameter_shard_qcs"),
        ("noncanonical-squared-norm", "norm_evidence"),
        ("reversed-apc-weights", "aggregation_plan_certificate"),
        ("unordered-norm-entries", "norm_evidence"),
        ("unordered-seed-shares", "seed_transcript"),
        ("unordered-signers", "input_set_certificate"),
        ("unreduced-rational", "aggregation_plan_certificate"),
        ("wrong-required-key-order", "aggregate_root_qc"),
        ("zero-denominator", "aggregation_plan_certificate"),
    ],
)
def test_python_typed_preflight_rejects_every_canonicality_mutation(
    case_name: str, artifact_name: str
) -> None:
    corpus = json.loads(CORPUS.read_bytes())
    case = next(item for item in corpus["cases"] if item["name"] == case_name)
    bundle = json.loads(bytes.fromhex(case["bundle_bytes_hex"]))
    artifact = bundle[artifact_name]
    if artifact_name == "parameter_shard_qcs":
        artifact = artifact[0]
    with pytest.raises(Feature008AdmissionError):
        CertificateArtifact.from_value(artifact)


def test_complete_python_admission_returns_the_native_receipt() -> None:
    plan, _ = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    receipt = Feature008ChainVerifier(
        CtypesFeature008NativeChainVerifier(_native_library())
    ).verify(plan, measured, result, require_native=False)
    assert receipt.native_receipt.value["status"] == "ACCEPT"
    assert (
        receipt.native_receipt.value["native_chain_verifier_id"]
        != receipt.native_receipt.value["native_build_id"]
    )


def test_python_admission_has_no_native_fallback() -> None:
    plan, _ = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_NATIVE_VERIFIER_REQUIRED"):
        Feature008ChainVerifier().verify(plan, measured, result, require_native=True)
