"""Evidence-only Python -> Java/Netty -> native/WAL receipt chain."""

from __future__ import annotations

from typing import Protocol

from deltatorrent.benchmark.contracts import CanonicalContract, ContractError

_STAGES = ("WORKER_PYTHON", "TRANSPORT_JAVA_NETTY", "NATIVE_CPP_WAL")


class StageReceiptProducer(Protocol):
    """Future producer port; Foundation intentionally supplies no implementation."""

    def produce(self, run_manifest: CanonicalContract) -> tuple[CanonicalContract, ...]: ...


def verify_receipt_chain(
    *,
    run_manifest: CanonicalContract,
    receipts: tuple[CanonicalContract, ...],
    runtime_identity: CanonicalContract,
) -> None:
    if run_manifest.type_name != "BENCHMARK_RUN_MANIFEST":
        raise ContractError("RECEIPT_CHAIN_RUN_TYPE_INVALID")
    if runtime_identity.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("RECEIPT_CHAIN_RUNTIME_TYPE_INVALID")
    run = run_manifest.to_dict()
    runtime = runtime_identity.to_dict()
    if run["status"] == "PLANNED":
        if receipts:
            raise ContractError("PLANNED_RUN_RECEIPTS_FORBIDDEN")
        return
    if run["status"] != "FIXTURE_COMPLETE":
        raise ContractError("RECEIPT_CHAIN_RUN_STATUS_INVALID")
    if len(receipts) != len(_STAGES):
        raise ContractError("RECEIPT_CHAIN_INCOMPLETE")
    if any(receipt.type_name != "BENCHMARK_STAGE_RECEIPT" for receipt in receipts):
        raise ContractError("RECEIPT_CHAIN_TYPE_INVALID")
    expected_components = {
        "WORKER_PYTHON": runtime["python_profile_id"],
        "TRANSPORT_JAVA_NETTY": runtime["netty_profile_id"],
        "NATIVE_CPP_WAL": runtime["native_runtime_id"],
    }
    previous: CanonicalContract | None = None
    expected_ticket_id = str(run["ticket_ids"][0])
    for expected_stage, receipt in zip(_STAGES, receipts, strict=True):
        value = receipt.to_dict()
        if value["stage"] != expected_stage:
            raise ContractError("RECEIPT_CHAIN_ORDER_INVALID")
        if value["benchmark_definition_id"] != run["benchmark_definition_id"]:
            raise ContractError("RECEIPT_CHAIN_DEFINITION_MISMATCH")
        if value["run_id"] != run["run_id"]:
            raise ContractError("RECEIPT_CHAIN_RUN_MISMATCH")
        if value["arm_id"] != run["arm_id"]:
            raise ContractError("RECEIPT_CHAIN_ARM_MISMATCH")
        if value["ticket_id"] != expected_ticket_id:
            raise ContractError("RECEIPT_CHAIN_TICKET_MISMATCH")
        if value["source_commit"] != runtime["source_commit"]:
            raise ContractError("RECEIPT_CHAIN_SOURCE_MISMATCH")
        if value["component_identity_id"] != expected_components[expected_stage]:
            raise ContractError("RECEIPT_CHAIN_COMPONENT_MISMATCH")
        if previous is None:
            if value["previous_receipt_id"] is not None:
                raise ContractError("RECEIPT_CHAIN_FIRST_PREDECESSOR_INVALID")
        else:
            if value["previous_receipt_id"] != previous.content_id:
                raise ContractError("RECEIPT_CHAIN_PREDECESSOR_MISMATCH")
            prior_outputs = set(previous.to_dict()["output_ids"])
            if not prior_outputs <= set(value["input_ids"]):
                raise ContractError("RECEIPT_CHAIN_DATAFLOW_MISMATCH")
        previous = receipt
    declared = tuple(run["stage_receipt_ids"])
    actual = tuple(receipt.content_id for receipt in receipts)
    if declared != actual:
        raise ContractError("RECEIPT_CHAIN_MANIFEST_MISMATCH")
