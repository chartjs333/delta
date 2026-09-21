"""Generate deterministic TEST_FIXTURE vectors for the Feature 010 foundation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "delta-worker-python"
for import_root in (WORKER / "src", WORKER):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from deltatorrent.benchmark.canonical import canonical_bytes  # noqa: E402
from deltatorrent.benchmark.contracts import (  # noqa: E402
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)
from deltatorrent.benchmark.decision import (  # noqa: E402
    GateOutcome,
    build_foundation_result,
)
from deltatorrent.benchmark.profiles import (  # noqa: E402
    ATTACK_VECTORS,
    FOUNDATION_FAULT_EVENTS,
)
from tests.benchmark.conftest import (  # noqa: E402
    arm,
    cid,
    completed_run,
    definition,
    environment,
    fault_profile,
    fixture_receipts,
    network_profile,
    runtime_identity,
    scientific_profile,
)

FIXTURE_OUTPUT = (
    ROOT / "delta-protocol" / "fixtures" / "010" / "cross-language" / "foundation-v1.json"
)
CONFIG_OUTPUT = ROOT / "configs" / "benchmark" / "foundation-v1.json"


def _wrapper(contract: CanonicalContract) -> dict[str, object]:
    return {
        "bytes_hex": contract.canonical_bytes.hex(),
        "content_id": contract.content_id,
        "value": contract.to_dict(),
    }


def fixture_document() -> dict[str, Any]:
    runtime = runtime_identity()
    scientific = scientific_profile(repetitions=1, seeds=[17])
    reference = arm(
        "reference",
        kind="REFERENCE",
        topology="FLAT",
        deployment_profile="EMBEDDED_FFM",
    )
    candidate = arm(
        "candidate",
        kind="DELTAREDUCE",
        topology="HIERARCHICAL",
        deployment_profile="EMBEDDED_FFM",
    )
    network = network_profile()
    fault = fault_profile()
    benchmark_definition = definition(
        runtime,
        scientific,
        (reference, candidate),
        (network,),
        (fault,),
    )
    fixture_environment = environment(runtime)
    receipts = fixture_receipts(
        benchmark_definition.content_id,
        candidate.content_id,
        runtime,
        cid("ticket-1"),
    )
    run = completed_run(
        benchmark_definition.content_id,
        candidate.content_id,
        scientific,
        network,
        fault,
        fixture_environment,
        cid("ticket-1"),
        receipts,
    )
    node = CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "benchmark_definition_id": benchmark_definition.content_id,
            "dependencies": [],
            "evidence_class": "TEST_FIXTURE",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "kind": "RUN_MANIFEST",
            "media_type": "application/vnd.deltareduce.benchmark-run-manifest+json;version=1",
            "ordinal": 0,
            "payload_id": run.content_id,
            "primary_eligible": False,
            "run_id": run.to_dict()["run_id"],
            "schema_id": "SCHEMA-BENCHMARK-RUN-MANIFEST-010-V1",
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_EVIDENCE_NODE",
        }
    )
    manifest = CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "benchmark_definition_id": benchmark_definition.content_id,
            "definition_qc_id": None,
            "definition_reviewer_set_id": benchmark_definition.to_dict()[
                "definition_reviewer_set_id"
            ],
            "evidence_class": "TEST_FIXTURE",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "node_ids": [node.content_id],
            "primary_eligible": False,
            "required_kinds": ["RUN_MANIFEST"],
            "run_ids": [run.to_dict()["run_id"]],
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_EVIDENCE_MANIFEST",
        }
    )
    result = build_foundation_result(
        definition_id=benchmark_definition.content_id,
        evidence_manifest_id=manifest.content_id,
        result_evaluator_set_id=str(benchmark_definition.to_dict()["result_evaluator_set_id"]),
        run_ids=(str(run.to_dict()["run_id"]),),
        gates=(GateOutcome("foundation-fixture", True, "PASS"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="Cross-language TEST_FIXTURE; no qualifying gate is evaluated.",
    )
    attestation = CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "benchmark_result_id": result.content_id,
            "benchmark_result_qc_id": None,
            "definition_reviewer_set_id": benchmark_definition.to_dict()[
                "definition_reviewer_set_id"
            ],
            "evidence_class": "TEST_FIXTURE",
            "evidence_manifest_id": manifest.content_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "primary_eligible": False,
            "result_evaluator_set_id": benchmark_definition.to_dict()["result_evaluator_set_id"],
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_ATTESTATION_MANIFEST",
        }
    )
    artifacts = {
        "arm": _wrapper(candidate),
        "attestation": _wrapper(attestation),
        "definition": _wrapper(benchmark_definition),
        "evidence_manifest": _wrapper(manifest),
        "evidence_node": _wrapper(node),
        "result": _wrapper(result),
        "run_manifest": _wrapper(run),
    }
    return {
        "artifacts": artifacts,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "negative_cases": [
            {
                "expected_error": "JSON_BYTES_NOT_CANONICAL",
                "id": "definition-leading-space",
                "target": "definition",
                "transformation": "PREFIX_SPACE",
            },
            {
                "expected_error": "PRIMARY_ELIGIBILITY_FORBIDDEN",
                "id": "run-primary-promotion",
                "path": "/primary_eligible",
                "target": "run_manifest",
                "value": True,
            },
        ],
        "ordered_artifact_names": list(artifacts),
        "schema_version": SCHEMA_VERSION,
        "semantic_completeness_claimed": False,
    }


def config_document() -> dict[str, Any]:
    """Return the frozen, non-authorizing plan used by foundation tests only."""

    runtime = runtime_identity()
    scientific = scientific_profile()
    arms = (
        arm(
            "reference",
            kind="REFERENCE",
            topology="FLAT",
            deployment_profile="EMBEDDED_FFM",
        ),
        arm(
            "candidate",
            kind="DELTAREDUCE",
            topology="HIERARCHICAL",
            deployment_profile="EMBEDDED_FFM",
        ),
    )
    network = network_profile()
    fault = fault_profile(
        duration_ms=20_000,
        events=[event.to_dict() for event in FOUNDATION_FAULT_EVENTS],
    )
    benchmark_definition = definition(runtime, scientific, arms, (network,), (fault,))
    return {
        "arms": [item.to_dict() for item in arms],
        "attack_vectors": [vector.to_dict() for vector in ATTACK_VECTORS],
        "authority_scope": AUTHORITY_SCOPE,
        "benchmark_definition": benchmark_definition.to_dict(),
        "definition_qc_id": None,
        "evidence_class": "TEST_FIXTURE",
        "execution_authorized": False,
        "fault_profiles": [fault.to_dict()],
        "feature010_go": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "gate_eligible": False,
        "network_profiles": [network.to_dict()],
        "ordered_receipt_stages": [
            "WORKER_PYTHON",
            "TRANSPORT_JAVA_NETTY",
            "NATIVE_CPP_WAL",
        ],
        "primary_eligible": False,
        "primary_observation_count": 0,
        "qualifying_gate_c": False,
        "real_wan_gate_d": False,
        "required_byte_counters": [
            "duplicate_bytes",
            "global_bytes",
            "p2p_bytes",
            "regional_bytes",
            "retry_bytes",
            "storage_bytes",
            "validator_bytes",
            "worker_bytes",
        ],
        "required_metric_phases": [
            "compute",
            "upload",
            "availability",
            "certificate",
            "reduce",
            "apply",
            "p2p",
            "wait",
        ],
        "result_qc_id": None,
        "runtime_constraints": {
            "cpp_compilers": ["CLANG", "GCC"],
            "cuda_profile_status": "UNQUALIFIED",
            "fast_math": False,
            "jdk_compatibility": 26,
            "jdk_reference": 25,
            "native_checked_arithmetic": True,
            "netty_lock_required": True,
            "python_minor": "3.12",
        },
        "runtime_identity": runtime.to_dict(),
        "schema_version": SCHEMA_VERSION,
        "scientific_profile": scientific.to_dict(),
        "type_name": "FEATURE010_FOUNDATION_CONFIG",
    }


def exactness_corpus_document() -> dict[str, Any]:
    """Return the shared Python/C++/Java status corpus without execution authority."""

    fixture = fixture_document()
    artifacts = fixture["artifacts"]
    ordered = fixture["ordered_artifact_names"]
    negative_statuses = []
    definition_bytes = bytes.fromhex(artifacts["definition"]["bytes_hex"])
    try:
        CanonicalContract.from_bytes(b" " + definition_bytes)
    except ValueError as error:
        status = str(error)
    else:
        raise RuntimeError("definition-leading-space was accepted")
    if status != "JSON_BYTES_NOT_CANONICAL":
        raise RuntimeError(f"unexpected definition-leading-space status: {status}")
    negative_statuses.append({"case_id": "definition-leading-space", "status": status})

    promoted_run = dict(artifacts["run_manifest"]["value"])
    promoted_run["primary_eligible"] = True
    try:
        CanonicalContract.from_dict(promoted_run)
    except ContractError as error:
        status = str(error)
    else:
        raise RuntimeError("run-primary-promotion was accepted")
    if status != "PRIMARY_ELIGIBILITY_FORBIDDEN":
        raise RuntimeError(f"unexpected run-primary-promotion status: {status}")
    negative_statuses.append({"case_id": "run-primary-promotion", "status": status})
    return {
        "artifact_ids": [artifacts[name]["content_id"] for name in ordered],
        "execution_class": "CONFORMANCE_SAFETY_ONLY",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "negative_statuses": negative_statuses,
        "primary_observation_count": 0,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "type_name": "FEATURE010_EXACTNESS_CORPUS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--emit-corpus", action="store_true")
    arguments = parser.parse_args()
    if arguments.emit_corpus:
        print(
            json.dumps(
                exactness_corpus_document(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 0
    outputs = {
        FIXTURE_OUTPUT: canonical_bytes(fixture_document()),
        CONFIG_OUTPUT: canonical_bytes(config_document()),
    }
    if arguments.check:
        for path, encoded in outputs.items():
            if not path.is_file() or path.read_bytes() != encoded:
                print(f"FOUNDATION_FIXTURE_STALE:{path.relative_to(ROOT).as_posix()}")
                return 2
    else:
        for path, encoded in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(encoded)
    print("FOUNDATION_FIXTURE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
