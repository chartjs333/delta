"""Run the non-primary 15-plan measured Stage C cross-language conformance set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile, simulate
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]


def artifact(path: Path) -> RuntimeArtifact:
    return RuntimeArtifact(path.resolve(), sha256_content_id(path.read_bytes()))


def load_inputs() -> tuple[tuple[tuple[str, NetworkProfile], ...], FaultProfile]:
    network_document = json.loads((ROOT / "configs/benchmark/networks-v1.json").read_bytes())
    fault_document = json.loads((ROOT / "configs/benchmark/faults-v1.json").read_bytes())
    profiles = tuple(
        (sha256_content_id(canonical_json_bytes(item)), NetworkProfile.from_dict(item))
        for item in network_document["profiles"]
    )
    return profiles, FaultProfile.from_dict(fault_document["trace_profile"])


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--java-executable", type=Path, required=True)
    result.add_argument("--native-executable", type=Path, required=True)
    result.add_argument("--transport-harness", type=Path, required=True)
    result.add_argument("--netty-artifact", type=Path, action="append", required=True)
    result.add_argument("--os-counter-root", type=Path, required=True)
    result.add_argument("--working-root", type=Path, required=True)
    result.add_argument("--image-id", required=True)
    return result


def main() -> None:
    arguments = parser().parse_args()
    profiles, fault_profile = load_inputs()
    boundary = MeasuredStageCRuntimeBoundary(
        image_id=arguments.image_id,
        java_executable=artifact(arguments.java_executable),
        native_executable=artifact(arguments.native_executable),
        transport_harness=artifact(arguments.transport_harness),
        netty_artifacts=tuple(artifact(path) for path in arguments.netty_artifact),
        os_interface_counter_root=arguments.os_counter_root,
        working_root=arguments.working_root,
    )
    receipt_ids: list[str] = []
    for ordinal in range(1, 16):
        plan_id = sha256_content_id(
            b"deltareduce.010.campaign02-stage-c-non-primary-conformance-plan.v1\0"
            + canonical_json_bytes(
                {
                    "execution_authorized": False,
                    "ordinal": ordinal,
                    "type_name": "CAMPAIGN02_STAGE_C_NON_PRIMARY_CONFORMANCE_PLAN",
                }
            )
        )
        measured = boundary.execute(
            plan_id=plan_id,
            packet_count=4096,
            payload_bytes=256,
            network_profiles=profiles,
            fault_profile=fault_profile,
        )
        for counters, (_profile_id, profile) in zip(
            measured.network_counters, profiles, strict=True
        ):
            oracle = simulate(profile, 4096)
            expected_dropped = sum(item.dropped for item in oracle)
            expected_duplicates = sum(item.duplicated and not item.dropped for item in oracle)
            if (
                counters.dropped_packets != expected_dropped
                or counters.duplicate_packets != expected_duplicates
            ):
                raise SystemExit("measured counters disagree with independent simulation oracle")
        receipt_ids.append(
            sha256_content_id(
                b"deltareduce.010.campaign02-stage-c-non-primary-conformance-receipt.v1\0"
                + canonical_json_bytes(
                    {
                        "fault_trace_id": measured.native_fault_trace_id,
                        "java_transport_receipt_ids": [
                            item.java_transport_receipt_id for item in measured.network_counters
                        ],
                        "plan_id": measured.plan_id,
                    }
                )
            )
        )
    output = {
        "decision": "PASS",
        "execution_authorized": False,
        "execution_class": "NON_PRIMARY_CONFORMANCE",
        "observations": 0,
        "plan_count": len(receipt_ids),
        "receipt_set_id": sha256_content_id("\n".join(receipt_ids).encode("ascii")),
        "schema_version": "1.0.0",
        "type_name": "CAMPAIGN02_STAGE_C_MEASURED_CONFORMANCE_SUMMARY",
    }
    print(canonical_json_bytes(output).decode("utf-8"))


if __name__ == "__main__":
    main()
