#!/usr/bin/env python3
"""Verify the frozen design-only isolated-sidecar refinement contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final

from exactness_gate import (
    EXPECTED_PROFILE_RISK_DECISION,
    FORMAL_ID,
    ExactnessError,
    canonical_bytes,
    require,
    source_identity,
)
from verify_exactness_status import validate_source

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/010-wan-benchmark-and-quality"
DESIGN_PATH: Final = FEATURE / "sidecar-refinement-design.json"
DESIGN_MARKDOWN_PATH: Final = FEATURE / "isolated-sidecar-refinement.md"
PROFILE_RISK_PATH: Final = FEATURE / "profile-risk-decision.json"
EXPECTED_DESIGN_SHA256: Final = (
    "sha256:dc031e7fb413d9ef1ed33b2d4fe1fedb170100e2782f636e7162b40cabbeb4c8"
)
EXPECTED_MARKDOWN_SHA256: Final = (
    "sha256:75f0ec2cf825db9940e2dd13f8ba81d46fd2aca40e63cbd8e424921963fbe368"
)
EXPECTED_CANONICAL_DESIGN_ID: Final = (
    "sha256:080074ff7de58d7ba025b8156ceafb0085937bb6ed74485d217af664d0ecf6ef"
)
HISTORICAL_FAIL_COMMIT: Final = "fc012861d8a1577f155abb94877102adef5cbf36"
HISTORICAL_FAIL_TREE: Final = "deeb2bda4c0a7e68015843d2ebe6fe4396edfb7b"
BASE_COMMIT: Final = "6f99ab1622aa4bb96dab29979ce11af8bd4c5f89"

EXPECTED_AUTHORITY: Final = {
    "benchmark_result_qc": None,
    "feature010_go": False,
    "feature011_authority": False,
    "gate_a_qualified": False,
    "gate_b_qualified": False,
    "gate_c_qualified": False,
    "gate_d_qualified": False,
    "pilot_execution_authorized": False,
    "primary_observation_count": 0,
    "selected_profile": None,
}
EXPECTED_FORMAL_IMPACT: Final = {
    "classification": "REFINEMENT_ONLY",
    "formal_semantics_id": FORMAL_ID,
    "new_arithmetic_preconditions": [],
    "new_availability_rules": [],
    "new_certificate_parent_edges": [],
    "new_current_transitions": [],
    "new_deadline_semantics": [],
    "new_durability_outcomes": [],
    "new_effect_categories": [],
    "new_externally_visible_action_ids": [],
    "new_failure_terminals": [],
    "new_qc_types": [],
    "new_vote_contexts": [],
    "stop_triggers": [
        "NEW_EXTERNALLY_VISIBLE_ACTION_OR_STATE",
        "NEW_FAILURE_TERMINAL_OR_DURABILITY_OUTCOME",
        "NEW_DEADLINE_OR_AVAILABILITY_RULE",
        "NEW_CERTIFICATE_PARENT_EDGE_OR_ARITHMETIC_PRECONDITION",
        "JAVA_PROTOCOL_DECISION_OR_DURABLE_STATE_OWNERSHIP",
        "EFFECT_EXPOSURE_BEFORE_DURABILITY",
        "COMMAND_ADMISSION_BEFORE_JOURNAL_RECOVERY",
        "PROFILE_SPECIFIC_CANONICAL_EFFECT_OR_FORMAL_TRACE",
    ],
}
EXPECTED_HISTORICAL_LINEAGE: Final = {
    "base_commit": BASE_COMMIT,
    "historical_fail_commit": HISTORICAL_FAIL_COMMIT,
    "historical_fail_rewritten": False,
    "historical_fail_status": "FAIL",
    "historical_fail_tree": HISTORICAL_FAIL_TREE,
    "open_tasks": ["T028", "T029", "HR010-013", "HR010-014"],
    "profile_risk_decision_status": "IMMUTABLE_HISTORICAL_INPUT_NOT_PROMOTED",
}
EXPECTED_RUNTIME_OWNERSHIP: Final = {
    "java_is_transport_and_supervision_only": True,
    "native_is_single_writer_wal_and_state_owner": True,
    "netty_event_loop_blocking_forbidden": True,
    "parallel_native_mutation_forbidden": True,
}
EXPECTED_BOUNDS: Final = {
    "control_envelope_bytes": 16_785_536,
    "header_bytes": 128,
    "in_flight_correlations": 64,
    "ingress_queue_requests": 64,
    "max_canonical_command_bytes": 16_777_216,
    "max_canonical_effect_bytes": 16_777_216,
    "max_canonical_vote_bytes": 16_769_024,
    "max_canonical_vote_policy_bytes": 4_194_304,
    "max_canonical_vote_receipt_bytes": 16_777_216,
    "max_identity_text_bytes": 256,
    "max_inline_payload_bytes": 16_785_408,
    "max_logical_payload_bytes": 16_785_408,
    "max_open_directory_utf8_bytes": 4_096,
    "max_payload_metadata_bytes": 8_192,
    "max_request_id_bytes": 256,
    "mutating_native_calls": 1,
    "shared_memory_bytes_per_region": 1_073_741_824,
    "shared_memory_control_bytes_per_region": 8_192,
    "shared_memory_control_record_bytes": 128,
    "shared_memory_reference_bytes": 64,
    "shared_memory_regions": 2,
    "shared_memory_slots_per_region": 64,
    "tracked_timers": 65_536,
}
EXPECTED_OPERATIONS: Final = [
    "DESCRIBE",
    "OPEN",
    "SUBMIT",
    "VOTE",
    "STATE",
    "SNAPSHOT",
    "CLOSE",
    "HEALTH",
    "SHARED_MEMORY_ACK",
]
EXPECTED_PERSIST_SEQUENCE: Final = [
    "VALIDATE_COMMAND",
    "COMPUTE_CANDIDATE",
    "APPEND_WAL",
    "DURABILITY_BARRIER",
    "COMMIT_STATE_ROOT",
    "RETURN_CANONICAL_EFFECTS",
    "FRAME_AND_PUBLISH_RESPONSE",
    "JAVA_MAY_SEND",
]
EXPECTED_IPC_OWNERSHIP: Final = {
    "java": [
        "PROCESS_SUPERVISION",
        "LOCAL_ENDPOINT",
        "FRAMING",
        "BOUNDED_INGRESS",
        "BACKPRESSURE",
        "HEALTH_AND_OPERATIONAL_WATCHDOG",
        "OPAQUE_TIMER_DELIVERY",
        "TELEMETRY",
    ],
    "native": [
        "EXCLUSIVE_DURABLE_DIRECTORY_LOCK",
        "SINGLE_WRITER_REACTOR",
        "WAL_AND_DURABILITY_BARRIER",
        "SNAPSHOT_AND_VOTE_JOURNAL",
        "STATE_AND_CURRENT_ROOTS",
        "RECOVERY_AND_REPLAY_IDENTITY",
        "CANONICAL_EFFECTS",
    ],
    "shared_memory_is_consensus_authority": False,
}
EXPECTED_FRAME_LAYOUT: Final = [
    {"name": "MAGIC", "offset": 0, "size": 8, "type": "ASCII_FIXED", "value": "DELTAIPC"},
    {"name": "IPC_MAJOR", "offset": 8, "size": 2, "type": "U16_BE"},
    {"name": "IPC_MINOR", "offset": 10, "size": 2, "type": "U16_BE"},
    {"name": "HEADER_LENGTH", "offset": 12, "size": 2, "type": "U16_BE", "value": 128},
    {"name": "MESSAGE_TYPE", "offset": 14, "size": 2, "type": "U16_BE"},
    {"name": "FLAGS", "offset": 16, "size": 4, "type": "U32_BE"},
    {"name": "SESSION_ID", "offset": 20, "size": 16, "type": "OPAQUE"},
    {"name": "GENERATION", "offset": 36, "size": 8, "type": "U64_BE"},
    {"name": "TRANSPORT_CORRELATION_ID", "offset": 44, "size": 16, "type": "OPAQUE"},
    {"name": "SEQUENCE", "offset": 60, "size": 8, "type": "U64_BE"},
    {"name": "PAYLOAD_LENGTH", "offset": 68, "size": 8, "type": "U64_BE"},
    {"name": "RESPONSE_CAPACITY", "offset": 76, "size": 8, "type": "U64_BE"},
    {"name": "PAYLOAD_SHA256", "offset": 84, "size": 32, "type": "OPAQUE"},
    {"name": "RESERVED_ZERO", "offset": 116, "size": 12, "type": "ZERO_BYTES"},
]
EXPECTED_FLAG_VALUES: Final = {
    "PAYLOAD_INLINE": 1,
    "PAYLOAD_SHARED_MEMORY": 2,
    "READ_ONLY": 8,
    "RESPONSE_EXPECTED": 4,
}
EXPECTED_FLAG_RULES: Final = [
    "MESSAGE_CARRIER_ELIGIBILITY_TABLE_ENFORCED_BEFORE_SHM_REFERENCE_RESOLUTION",
    "INLINE_XOR_SHARED_MEMORY_WHEN_PAYLOAD_PRESENT",
    "UNKNOWN_FLAG_BITS_REJECTED",
]
EXPECTED_OPCODE_FLAG_REQUIREMENTS: Final = {
    "CLIENT_HELLO": ["PAYLOAD_INLINE", "RESPONSE_EXPECTED"],
    "CLOSE_REQUEST": ["PAYLOAD_INLINE", "RESPONSE_EXPECTED"],
    "CLOSE_RESPONSE": ["PAYLOAD_INLINE"],
    "ERROR_RESPONSE": ["PAYLOAD_INLINE"],
    "HEALTH_REQUEST": ["PAYLOAD_INLINE", "RESPONSE_EXPECTED", "READ_ONLY"],
    "HEALTH_RESPONSE": ["PAYLOAD_INLINE"],
    "OPEN_REQUEST": ["ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY", "RESPONSE_EXPECTED"],
    "OPEN_RESPONSE": ["PAYLOAD_INLINE"],
    "SERVER_DESCRIPTOR": ["PAYLOAD_INLINE"],
    "SHARED_MEMORY_ACK": ["PAYLOAD_INLINE"],
    "SNAPSHOT_REQUEST": ["PAYLOAD_INLINE", "RESPONSE_EXPECTED"],
    "SNAPSHOT_RESPONSE": ["ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY"],
    "STATE_REQUEST": ["PAYLOAD_INLINE", "RESPONSE_EXPECTED", "READ_ONLY"],
    "STATE_RESPONSE": ["ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY"],
    "SUBMIT_REQUEST": [
        "ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY",
        "RESPONSE_EXPECTED",
    ],
    "SUBMIT_RESPONSE": ["ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY"],
    "VOTE_REQUEST": [
        "ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY",
        "RESPONSE_EXPECTED",
    ],
    "VOTE_RESPONSE": ["ONE_OF_PAYLOAD_INLINE_OR_PAYLOAD_SHARED_MEMORY"],
}
EXPECTED_RESPONSE_CAPACITY_RULE: Final = (
    "REQUEST_WITH_RESPONSE_EXPECTED_INCLUDING_CLIENT_HELLO_MUST_SET_CAPACITY_EXACTLY_TO_"
    "FROZEN_MAX_LOGICAL_PAYLOAD_BYTES_16785408; ALL_OTHER_MESSAGES_MUST_SET_ZERO"
)
EXPECTED_SEQUENCE_RULE: Final = (
    "PER_DIRECTION_PER_SESSION_U64_STARTS_AT_1_AND_STRICTLY_INCREMENTS_BY_1; ZERO_RESERVED; "
    "OVERFLOW_PERMANENTLY_FENCES_GENERATION; DISTINCT_FROM_NATIVE_ADMITTED_SEQUENCE"
)
EXPECTED_MESSAGE_TYPES: Final = {
    "CLIENT_HELLO": 1,
    "CLOSE_REQUEST": 80,
    "CLOSE_RESPONSE": 81,
    "ERROR_RESPONSE": 255,
    "HEALTH_REQUEST": 96,
    "HEALTH_RESPONSE": 97,
    "OPEN_REQUEST": 16,
    "OPEN_RESPONSE": 17,
    "SERVER_DESCRIPTOR": 2,
    "SHARED_MEMORY_ACK": 112,
    "SNAPSHOT_REQUEST": 64,
    "SNAPSHOT_RESPONSE": 65,
    "STATE_REQUEST": 48,
    "STATE_RESPONSE": 49,
    "SUBMIT_REQUEST": 32,
    "SUBMIT_RESPONSE": 33,
    "VOTE_REQUEST": 34,
    "VOTE_RESPONSE": 35,
}
EXPECTED_FRAME_LAYOUT_ID: Final = (
    "sha256:b8d8a521133d4d5b41ab5035f2cfaa82594a4789c8b83ad0c81b77a67afbcb4b"
)
EXPECTED_BOUNDS_ID: Final = (
    "sha256:12259ada8ff8a14febf167b2631768911fefd9fd26c7298b7ff0f3d103837708"
)
EXPECTED_FLAG_TABLE_ID: Final = (
    "sha256:857da723287529fe38f3f6479decb962f435e21b541b38abe71b28489933b248"
)
EXPECTED_MESSAGE_TYPE_TABLE_ID: Final = (
    "sha256:1581d40a12765ea54c1abf7f3c5434025f40d6718e639c9f9fbfcc1eb6e07950"
)
EXPECTED_PAYLOAD_SCHEMA_ID: Final = (
    "sha256:fdeb9e2607dfe2661fff8e99a9510ae1eb6658e516f1496ade6fd1dd6e7af7ce"
)
EXPECTED_SHARED_MEMORY_ID: Final = (
    "sha256:17ce8022d0075e715e8c699ba17c27d9901bf08727579ab977e74f169b205b78"
)
EXPECTED_DESCRIPTOR_HANDSHAKE: Final = {
    "bound_fields": [
        "IPC_CONTRACT_NAME_AND_VERSION",
        "CANONICAL_ENCODING_ID",
        "FRAME_LAYOUT_SHA256",
        "PAYLOAD_SCHEMA_SHA256",
        "MESSAGE_TYPE_VALUES",
        "MESSAGE_TYPE_TABLE_SHA256",
        "FLAG_VALUES_AND_RULES",
        "FLAG_TABLE_SHA256",
        "FROZEN_BOUNDS_BY_BOUNDS_SHA256",
        "BOUNDS_SHA256",
        "SHARED_MEMORY_LAYOUT_SHA256",
        "SESSION_ID",
        "GENERATION",
        "SIDECAR_EXECUTABLE_SHA256",
        "SIDECAR_BUILD_ID",
        "OUTER_DEPLOYMENT_PROFILE",
        "NESTED_C_ABI_DESCRIPTOR_FIELDS",
        "NESTED_C_ABI_DESCRIPTOR_SHA256",
    ],
    "canonical_encoding_id": (
        "sha256:393cd207a2cd3fd4da366be56095a3467e3184c2c5db1d300d1c07d49cdd7aff"
    ),
    "bounds_rule": "V1_1_EXACT_FROZEN_BOUNDS_HASH_NO_NEGOTIATION_OR_LOWERING",
    "bounds_sha256": EXPECTED_BOUNDS_ID,
    "flag_table_sha256": EXPECTED_FLAG_TABLE_ID,
    "frame_layout_sha256": EXPECTED_FRAME_LAYOUT_ID,
    "initial_state": "DESCRIBE_ONLY",
    "major_version_rule": "EXACT_MATCH",
    "minor_version_rule": "EXACT_1_1_NO_DOWNGRADE",
    "message_type_table_sha256": EXPECTED_MESSAGE_TYPE_TABLE_ID,
    "nested_c_abi_fields": [
        "STRUCT_SIZE",
        "ABI_MAJOR",
        "ABI_MINOR",
        "FEATURE_BITS",
        "SCHEMA_VERSION",
        "PROTOCOL_VERSION",
        "FORMAL_SEMANTICS_ID",
        "BUILD_ID",
        "SCHEMA_SET_ID",
        "RUNTIME_PROFILE",
    ],
    "outer_deployment_profile": "ISOLATED_SIDECAR",
    "payload_schema_sha256": EXPECTED_PAYLOAD_SCHEMA_ID,
    "ready_rule": "EXCLUSIVE_DURABLE_LOCK_AND_COMPLETE_JOURNAL_RECOVERY_BEFORE_READY",
    "required_messages": ["CLIENT_HELLO", "SERVER_DESCRIPTOR"],
    "shared_memory_layout_sha256": EXPECTED_SHARED_MEMORY_ID,
    "version_or_identity_mismatch": "FAIL_BEFORE_OPEN_NO_DOWNGRADE",
}
EXPECTED_SHARED_MEMORY: Final = {
    "ack_frame_authority": (
        "NOTIFICATION_ONLY; PRODUCER_REUSES_ONLY_AFTER_ACQUIRE_OBSERVES_MATCHING_"
        "TERMINAL_CONTROL_STATE; LOST_OR_DUPLICATE_ACK_STUTTERS"
    ),
    "ack_frame_transport": (
        "OPTIONAL_SHARED_MEMORY_ACK_INLINE_ONLY_AFTER_CONSUMER_RELEASE_STORES_ACKED_OR_"
        "REJECTED; ABSENCE_OR_DUPLICATE_STUTTERS"
    ),
    "ack_frame_validation": (
        "CURRENT_SESSION_GENERATION_CORRELATION_REFERENCE_DIGEST_REQUEST_ID_REQUEST_DIGEST_"
        "AND_DISPOSITION_EXACT; STALE_RECLAIMED_OR_DUPLICATE_NOTIFICATION_STUTTERS"
    ),
    "atomic_abi_requirement": (
        "ALIGNED_LOCK_FREE_INTERPROCESS_U32_BIG_ENDIAN_ATOMICS_OR_DISABLE_SHM_AND_USE_BOUNDED_COPY"
    ),
    "atomic_probe_rule": (
        "PRELAUNCH_ALIGNED_MAP_SHARED_CROSS_PROCESS_U32_CAS_AND_RAW_BIG_ENDIAN_STATE_BYTES_"
        "REQUIRED_BEFORE_ENABLEMENT; FAILURE_SELECTS_BOUNDED_COPY"
    ),
    "borrowed_pointer_lifetime": "SYNCHRONOUS_NATIVE_CALL_ONLY_NO_RETAIN_AFTER_RETURN",
    "bounded_copy_fallback": "MANDATORY_BYTE_AND_TRACE_IDENTICAL",
    "control_record_layout": [
        "0:4:STATE:ATOMIC_U32_BE",
        "4:4:REGION_ID:U32_BE",
        "8:8:GENERATION:U64_BE",
        "16:4:SLOT:U32_BE",
        "20:4:RESERVED_ZERO:ZERO_BYTES",
        "24:8:OFFSET:U64_BE",
        "32:8:LENGTH:U64_BE",
        "40:32:SHA256:OPAQUE",
        "72:56:RESERVED_ZERO:ZERO_BYTES",
    ],
    "control_region_rule": (
        "64_ALIGNED_128_BYTE_RECORDS_AT_SLOT_TIMES_128; DATA_OFFSETS_AT_OR_AFTER_8192; "
        "CHECKED_NONOVERLAPPING_LIVE_RANGES_WITHIN_1_GIB"
    ),
    "consumer_access": "READ_ONLY_UNTIL_ACK_OR_REJECT",
    "effect_publication_rule": (
        "ONLY_AFTER_NATIVE_POST_DURABILITY_RETURN_AND_COMPLETE_LENGTH_AND_SHA256_VALIDATION"
    ),
    "memory_order": [
        "PRODUCER_CAS_FREE_TO_WRITING_ACQUIRE_RELEASE",
        "PRODUCER_WRITES_METADATA_AND_COMPLETE_DATA_AND_DIGEST_BEFORE_RELEASE_STORE_PUBLISHED",
        "CONSUMER_ACQUIRE_LOADS_PUBLISHED_AND_CAS_PUBLISHED_TO_READING_BEFORE_READ",
        "CONSUMER_RELEASE_STORES_ACKED_OR_REJECTED_AFTER_ALL_ACCESS_ENDS",
        "PRODUCER_ACQUIRE_LOADS_ACKED_OR_REJECTED_BEFORE_CLEAR_AND_RELEASE_STORE_FREE",
    ],
    "reference_layout": [
        "0:4:REGION_ID:U32_BE",
        "4:4:SLOT:U32_BE",
        "8:8:GENERATION:U64_BE",
        "16:8:OFFSET:U64_BE",
        "24:8:LENGTH:U64_BE",
        "32:32:SHA256:OPAQUE",
    ],
    "reference_fields": ["REGION_ID", "SLOT", "GENERATION", "OFFSET", "LENGTH", "SHA256"],
    "reference_generation_rule": (
        "REFERENCE_AND_CONTROL_RECORD_GENERATION_MUST_EQUAL_FRAME_HEADER_AND_CURRENT_GENERATION"
    ),
    "region_id_values": {"JAVA_TO_NATIVE": 1, "NATIVE_TO_JAVA": 2},
    "session_loss": (
        "PERMANENTLY_FENCE_GENERATION_AND_INVALIDATE_OLD_GENERATION_REFERENCES; RECLAIM_ONLY_"
        "AFTER_PEER_DEATH_ENDPOINT_CLOSE_AND_UNMAP_CONFIRMED"
    ),
    "slot_reuse": (
        "FORBIDDEN_UNTIL_PRODUCER_ACQUIRE_OBSERVES_ACKED_OR_REJECTED_AND_CLEARS_TO_FREE"
    ),
    "slot_state_transitions": [
        "FREE_TO_WRITING",
        "WRITING_TO_PUBLISHED",
        "PUBLISHED_TO_READING",
        "READING_TO_ACKED_OR_REJECTED",
        "ACKED_OR_REJECTED_TO_FREE",
    ],
    "slot_state_values": {
        "ACKED": 4,
        "FREE": 0,
        "PUBLISHED": 2,
        "READING": 3,
        "REJECTED": 5,
        "WRITING": 1,
    },
    "transports_transient_canonical_bytes_only": True,
}
EXPECTED_PAYLOAD_BODY_RULES: Final = [
    "MESSAGE_TYPE_IS_THE_SOLE_SCHEMA_TYPE_CODE",
    (
        "LOGICAL_PAYLOAD_PREFIX_IS_16_BYTES_SCHEMA_TYPE_U16_MAJOR_U16_MINOR_U16_"
        "RESERVED_ZERO_U16_VALUE_LENGTH_U64"
    ),
    "SCHEMA_TYPE_EQUALS_HEADER_MESSAGE_TYPE_AND_SCHEMA_VERSION_IS_1_0",
    "VALUE_IS_STRICTLY_INCREASING_UNIQUE_REQUIRED_TLVS_WITH_NO_UNKNOWN_FIELDS",
    "TLV_HEADER_IS_FIELD_ID_U16_WIRE_TYPE_U8_FLAGS_ZERO_U8_LENGTH_U32",
    "CHECKED_LENGTHS_EXACT_SCALAR_WIDTHS_NO_PADDING_NO_TRAILING_BYTES",
    "INLINE_BODY_IS_LOGICAL_PAYLOAD_AND_HEADER_LENGTH_SHA256_COVER_LOGICAL_PAYLOAD",
    (
        "SHARED_MEMORY_WIRE_BODY_IS_EXACT_64_BYTE_REFERENCE_AND_HEADER_LENGTH_SHA256_"
        "EQUAL_REFERENCED_LOGICAL_LENGTH_SHA256"
    ),
    "NO_PAYLOAD_HAS_NO_PAYLOAD_FLAG_ZERO_LENGTH_NO_BODY_AND_SHA256_OF_EMPTY",
    ("RESPONSE_CAPACITY_IS_LOGICAL_RESPONSE_CAPACITY_AND_NEVER_EXCEEDS_MAX_LOGICAL_PAYLOAD_BYTES"),
    (
        "REQUEST_DIGEST_HASHES_ASCII_DELTAIPCREQUEST1_THEN_MESSAGE_TYPE_U16_BE_SCHEMA_"
        "MAJOR_U16_BE_SCHEMA_MINOR_U16_BE_THEN_EXACT_REQUEST_OPERATION_TLVS_FIELD_IDS_"
        "16_AND_ABOVE"
    ),
    ("RESPONSES_AND_ERRORS_ECHO_REQUEST_ID_AND_REQUEST_DIGEST_WITHOUT_REHASHING_RESPONSE_FIELDS"),
    (
        "CLIENT_HELLO_AND_SERVER_DESCRIPTOR_PAYLOAD_SESSION_ID_AND_GENERATION_EQUAL_FRAME_"
        "HEADER_AND_CURRENT_SESSION_GENERATION"
    ),
    "HEALTH_RESPONSE_PAYLOAD_GENERATION_EQUALS_FRAME_HEADER_AND_CURRENT_GENERATION",
]
EXPECTED_CARRIER_ELIGIBILITY: Final = {
    "CLIENT_HELLO": "INLINE_ONLY",
    "CLOSE_REQUEST": "INLINE_ONLY",
    "CLOSE_RESPONSE": "INLINE_ONLY",
    "ERROR_RESPONSE": "INLINE_ONLY",
    "HEALTH_REQUEST": "INLINE_ONLY",
    "HEALTH_RESPONSE": "INLINE_ONLY",
    "OPEN_REQUEST": "INLINE_OR_SHARED_MEMORY",
    "OPEN_RESPONSE": "INLINE_ONLY",
    "SERVER_DESCRIPTOR": "INLINE_ONLY",
    "SHARED_MEMORY_ACK": "INLINE_ONLY",
    "SNAPSHOT_REQUEST": "INLINE_ONLY",
    "SNAPSHOT_RESPONSE": "INLINE_OR_SHARED_MEMORY",
    "STATE_REQUEST": "INLINE_ONLY",
    "STATE_RESPONSE": "INLINE_OR_SHARED_MEMORY",
    "SUBMIT_REQUEST": "INLINE_OR_SHARED_MEMORY",
    "SUBMIT_RESPONSE": "INLINE_OR_SHARED_MEMORY",
    "VOTE_REQUEST": "INLINE_OR_SHARED_MEMORY",
    "VOTE_RESPONSE": "INLINE_OR_SHARED_MEMORY",
}
EXPECTED_ADMISSION_ENCODING_RULES: Final = [
    (
        "NOT_APPLICABLE_WHEN_FIELDS_PRESENT_REQUIRES_ADMITTED_SEQUENCE_ZERO_NATIVE_STATUS_"
        "ZERO_AND_NO_OPERATION_RESULT_AUTHORITY"
    ),
    (
        "NOT_ADMITTED_PROVEN_REQUIRES_ADMITTED_SEQUENCE_ZERO_NONZERO_NATIVE_STATUS_AND_"
        "ERROR_RESPONSE"
    ),
    (
        "ADMITTED_OUTCOME_AVAILABLE_REQUIRES_ADMITTED_SEQUENCE_NONZERO; SUCCESS_USES_"
        "OPERATION_RESPONSE_NATIVE_STATUS_ZERO_AND_ALL_RESULT_FIELDS_PRESENT; NONZERO_NATIVE_"
        "STATUS_USES_ERROR_RESPONSE"
    ),
    (
        "OUTCOME_UNKNOWN_REQUIRES_ADMITTED_SEQUENCE_NONZERO_NATIVE_STATUS_UNAVAILABLE_"
        "4294967295_WHEN_NO_NATIVE_STATUS_IS_RECOVERABLE_AND_ERROR_RESPONSE_WITH_NO_OPERATION_"
        "RESULT_FIELDS"
    ),
    (
        "PRESENT_EMPTY_BYTES_USE_ZERO_LENGTH_AND_SHA256_EMPTY; ABSENT_FIXED_ID_OR_HASH_USES_"
        "ALL_ZERO_ONLY_WHERE_SCHEMA_NAME_EXPLICITLY_SAYS_OR_ZERO"
    ),
    (
        "PREPARSE_ERROR_RESPONSE_ONLY_IF_SAFE_CURRENT_SESSION_GENERATION_HEADER_AND_CORRELATION_"
        "EXIST; USE_EMPTY_REQUEST_ID_SHA256_EMPTY_NOT_ADMITTED_SEQUENCE_ZERO_NATIVE_STATUS_"
        "UNAVAILABLE_4294967295; OTHERWISE_CLOSE_CHANNEL_PERMANENTLY_FENCE_GENERATION_WITHOUT_"
        "RESPONSE"
    ),
]
EXPECTED_WIRE_TYPE_VALUES: Final = {
    "BYTES": 7,
    "CANONICAL_UTF8": 8,
    "ID128": 5,
    "SHA256": 6,
    "SHM_REFERENCE_64": 9,
    "U16_BE": 2,
    "U32_BE": 3,
    "U64_BE": 4,
    "U8": 1,
}
EXPECTED_SHARED_MEMORY_DISPOSITION_VALUES: Final = {
    "ACKED": 1,
    "REJECTED_BOUNDS": 4,
    "REJECTED_DIGEST": 2,
    "REJECTED_STALE": 3,
}
EXPECTED_OPTIONAL_FIELD_RULES: Final = {
    "OPEN_REQUEST_FIELD_20": (
        "ABSENT_OR_EXACTLY_ONE_NONEMPTY_OPAQUE_CANONICAL_VOTE_POLICY_MAX_4194304_INCLUDED_"
        "IN_REQUEST_DIGEST; ABSENT_IS_SUBMIT_ONLY"
    )
}
EXPECTED_NESTED_C_ABI_DESCRIPTOR: Final = {
    "encoded_length_rule": "U32_BE_TOTAL_DESCRIPTOR_BYTES",
    "fixed_prefix_layout": [
        "0:8:MAGIC:ASCII_DELTABI1",
        "8:4:ENCODED_LENGTH:U32_BE",
        "12:4:STRUCT_SIZE:U32_BE",
        "16:2:ABI_MAJOR:U16_BE",
        "18:2:ABI_MINOR:U16_BE",
        "20:8:FEATURE_BITS:U64_BE",
    ],
    "hash_rule": "SHA256_OF_EXACT_ENCODED_DESCRIPTOR_BYTES",
    "magic_ascii": "DELTABI1",
    "text_encoding": "U32_BE_LENGTH_THEN_CANONICAL_UTF8_NFC_NO_NUL_MAX_256",
    "text_fields_after_offset_28": [
        "SCHEMA_VERSION",
        "PROTOCOL_VERSION",
        "FORMAL_SEMANTICS_ID",
        "BUILD_ID",
        "SCHEMA_SET_ID",
        "RUNTIME_PROFILE",
    ],
    "trailing_bytes_forbidden": True,
}
EXPECTED_RETRY_AND_STALE_RESPONSE: Final = {
    "accepted_response_match_fields": [
        "SESSION_ID",
        "GENERATION",
        "TRANSPORT_CORRELATION_ID",
        "OPERATION",
        "CANONICAL_REQUEST_ID",
        "REQUEST_DIGEST",
    ],
    "admitted_sequence_validation": (
        "JAVA_BINDS_THE_FIRST_VALIDATED_NATIVE_OR_RECOVERY_RESULT; ZERO_ONLY_FOR_NOT_ADMITTED_"
        "OR_POSITIVE_NATIVE_ASSIGNED_SEQUENCE_FOR_ADMITTED; RETRY_OR_RECOVERY_RESPONSE_MUST_"
        "EQUAL_PERSISTED_NATIVE_RECOVERY_PROOF"
    ),
    "conflicting_bytes_same_request_id": (
        "SAME_CANONICAL_REQUEST_ID_WITH_DIFFERENT_OPERATION_OR_BODY_FAIL_CLOSED_CONFLICT_STUTTER"
    ),
    "exact_retry": "SAME_OPERATION_CANONICAL_REQUEST_ID_AND_BODY",
    "generation_unfence_forbidden": True,
    "post_admission_timeout": (
        "OUTCOME_UNKNOWN_PERMANENTLY_FENCE_GENERATION_TERMINATE_OR_CONFIRM_DEATH_WAIT_"
        "ENDPOINT_CLOSE_AND_DURABLE_LOCK_RELEASE_RESPAWN_RECOVER_READY_THEN_RETRY_IDENTICAL"
    ),
    "session_reconnect_same_generation_forbidden": True,
    "stale_response": "DISCARD_NO_PEER_SEND_NO_STATE_CHANGE",
}
EXPECTED_VOTE_BOUNDARY: Final = {
    "java_ownership": (
        "OPAQUE_BYTES_ONLY_NO_VOTE_POLICY_OR_VOTE_OR_RECEIPT_PARSE_AND_NO_ACTION_CONTEXT_"
        "PARENT_OR_GUARD_CHOICE"
    ),
    "native_authority": (
        "NATIVE_PARSE_VALIDATE_ADMIT_JOURNAL_DURABILITY_REPLAY_AND_RECEIPT_AUTHORSHIP_ONLY"
    ),
    "open_policy_rule": (
        "OPEN_FIELD_20_ABSENT_OR_EXACTLY_ONE_NONEMPTY_OPAQUE_CANONICAL_POLICY; ABSENT_"
        "PRESERVES_SUBMIT_ONLY_RUNTIME"
    ),
    "persist_before_expose": (
        "VALIDATE_VOTE_AND_POLICY_GUARDS_THEN_APPEND_VOTE_JOURNAL_THEN_DURABILITY_BARRIER_"
        "THEN_COMMIT_NATIVE_VOTE_STATE_THEN_AUTHOR_CANONICAL_RECEIPT_THEN_FRAME_OR_PUBLISH_"
        "RESPONSE"
    ),
    "request_rule": (
        "VOTE_REQUEST_IS_REQUEST_ID_AND_REQUEST_DIGEST_PLUS_ONE_OPAQUE_CANONICAL_VOTE_AT_"
        "MOST_16769024_BYTES"
    ),
    "response_reservation_rule": (
        "RESERVE_MAX_LOGICAL_RESPONSE_CAPACITY_BEFORE_NATIVE_ADMISSION; RECEIPT_MAX_16777216_"
        "PLUS_TLV_METADATA_MUST_FIT_16785408"
    ),
    "response_rule": (
        "VOTE_RESPONSE_IS_STANDARD_ADMISSION_PROOF_PLUS_ONE_OPAQUE_NATIVE_AUTHORED_"
        "CANONICAL_RECEIPT_AND_ITS_SHA256"
    ),
    "retry_rule": (
        "EXACT_REQUEST_RETRY_DELEGATES_TO_NATIVE_DURABLE_VOTE_REPLAY; JAVA_CACHE_IS_NEVER_"
        "REPLAY_AUTHORITY"
    ),
}
EXPECTED_TIMEOUT_AND_CRASH_DETECTION: Final = {
    "alive_after_timeout_resolution": (
        "PERMANENTLY_FENCE_GENERATION_STOP_ADMISSION_REQUEST_SHUTDOWN_FORCE_TERMINATE_"
        "AFTER_10000_MS_THEN_REQUIRE_CONFIRMED_EXIT_ENDPOINT_CLOSE_AND_DURABLE_LOCK_RELEASE"
    ),
    "failure_to_confirm_exit_or_lock_release": "UNREADY_NO_ADMISSION_SELECTED_PROFILE_NULL",
    "generation_unfence_forbidden": True,
    "graceful_shutdown_timeout_ms": 10_000,
    "heartbeat_interval_ms": 1_000,
    "heartbeat_miss_limit": 5,
    "heartbeat_loss_projection": "SUSPECT_AND_FENCE_ONLY_STUTTER_UNTIL_CONFIRMED_DEATH",
    "recovery_ready_timeout_ms": 120_000,
    "request_watchdog_timeout_ms": 30_000,
    "restart_attempt_limit": 3,
    "restart_attempt_scope": "PER_INCIDENT_AFTER_CONFIRMED_EXIT_AND_DURABLE_LOCK_RELEASE",
    "restart_backoff_ms": 1_000,
    "timeout_clock": "JAVA_MONOTONIC_OPERATIONAL_ONLY_NOT_CONSENSUS_LOGICAL_TIME",
    "timeout_exhaustion": "NO_READY_NO_ADMISSION_SELECTED_PROFILE_NULL",
}
EXPECTED_TRACE_PROJECTION: Final = [
    {
        "concrete_events": [
            "INITIAL_PROCESS_START",
            "ENDPOINT_CREATE",
            "HANDSHAKE",
            "SHARED_MEMORY_MAP",
            "HEARTBEAT_BEFORE_INIT",
        ],
        "projection": "PRE_INIT_DIAGNOSTIC_ERASED_NO_FORMAL_STATE_ROOT",
    },
    {
        "concrete_events": ["FIRST_CLEAN_OPEN"],
        "projection": "INIT_BOUNDARY_WITH_OPEN_MECHANICS_STUTTER",
    },
    {
        "concrete_events": ["HEARTBEAT_AFTER_INIT"],
        "projection": "STUTTER",
    },
    {
        "concrete_events": ["REPLACEMENT_PROCESS_LOCK_ACQUIRED_AFTER_CONFIRMED_DEATH"],
        "projection": "ACT-RESTART_ONCE_PER_NEW_GENERATION",
    },
    {
        "concrete_events": ["RECOVERY_OPEN_BEGIN"],
        "projection": "STUTTER_NO_ADMISSION",
    },
    {
        "concrete_events": ["JOURNAL_RECOVERY_COMPLETE"],
        "projection": "ACT-JOURNAL-RECOVER",
    },
    {
        "concrete_events": ["STATE", "HEALTH", "DRAINED_TERMINAL_CLOSE", "SNAPSHOT"],
        "projection": "STUTTER",
    },
    {
        "concrete_events": ["ACTIVE_CLOSE_REQUEST", "KILL_REQUEST", "HEARTBEAT_SUSPICION"],
        "projection": "STUTTER_FENCE_NO_DEATH_ACTION",
    },
    {
        "concrete_events": ["CONFIRMED_NATIVE_DEATH_REMOVING_ACTIVE_FORMAL_ACTOR"],
        "projection": "ACT-CRASH_ONCE_PER_GENERATION",
    },
    {
        "concrete_events": ["SUBMIT_OR_VOTE_DISPATCH"],
        "projection": "STUTTER_TRANSPORT_MECHANICS",
    },
    {
        "concrete_events": [
            "NATIVE_TRACE_EVENT_EXCLUDING_ACT_CRASH_ACT_RESTART_ACT_JOURNAL_RECOVER_"
            "ACT_MESSAGE_REPLAY_ACT_MESSAGE_DROP"
        ],
        "projection": "SAME_EXISTING_ACTION_ID_AND_FIELDS_FROM_NATIVE_TRACE",
    },
    {
        "concrete_events": [
            "TIMER_SCHEDULE",
            "TIMER_CANCEL",
            "TIMER_WAIT",
            "TIMER_FRAME_DELIVERED",
        ],
        "projection": "STUTTER_PRESERVE_ANY_SEPARATE_NATIVE_TRACE_ACTION",
    },
    {
        "concrete_events": [
            "STALE_TIMER_REJECTED_BEFORE_NATIVE_FORMAL_EVENT",
            "DUPLICATE_ENVELOPE_DISCARDED_BEFORE_NATIVE",
        ],
        "projection": "STUTTER_NO_NATIVE_MUTATION",
    },
    {
        "concrete_events": ["LOST_RESPONSE_RETRY_OR_REEMISSION"],
        "projection": "STUTTER_IDENTICAL_EFFECT_IDENTITY_AND_DURABLE_SEQUENCE",
    },
    {
        "concrete_events": ["NATIVE_TRACE_ACT_MESSAGE_REPLAY"],
        "projection": "PRESERVE_EXISTING_ACT-MESSAGE-REPLAY_IF_FORMAL_PRECONDITIONS_HOLD",
    },
    {
        "concrete_events": ["NATIVE_TRACE_ACT_MESSAGE_DROP"],
        "projection": "PRESERVE_EXISTING_ACT-MESSAGE-DROP_IF_FORMAL_PRECONDITIONS_HOLD",
    },
    {
        "concrete_events": [
            "FRAME_REJECTED_BEFORE_FORMAL_ENQUEUE",
            "LIVE_NATIVE_CHANNEL_LOSS_BEFORE_ADMISSION",
            "RETRY_ENVELOPE_NOT_YET_ADMITTED",
        ],
        "projection": "STUTTER_NO_NATIVE_MUTATION",
    },
    {
        "concrete_events": [
            "QUEUE_REJECT",
            "BACKPRESSURE_REJECT",
            "STALE_RESPONSE_REJECT",
            "CONFLICTING_RETRY",
        ],
        "projection": "STUTTER_NO_NATIVE_MUTATION",
    },
]
EXPECTED_TRACE_PROJECTION_INVARIANTS: Final = {
    "confirmed_death_action_rule": (
        "EXACTLY_ONE_ACT-CRASH_PER_ACTIVE_GENERATION_ONLY_AFTER_CONFIRMED_DEATH_OR_REMOVAL"
    ),
    "generic_native_trace_excluded_action_ids": [
        "ACT-CRASH",
        "ACT-RESTART",
        "ACT-JOURNAL-RECOVER",
        "ACT-MESSAGE-REPLAY",
        "ACT-MESSAGE-DROP",
    ],
    "lifecycle_projection_source": (
        "SUPERVISOR_CONFIRMED_LIFECYCLE_EVIDENCE_ONLY; NATIVE_OR_DUPLICATE_PROJECTION_FOR_SAME_"
        "GENERATION_FORBIDDEN"
    ),
    "lifecycle_refinement_projector_rule": (
        "DETERMINISTIC_REFINEMENT_PROJECTOR_MAY_MAP_VERIFIED_DEATH_AND_REPLACEMENT_LOCK_EVIDENCE_"
        "TO_EXISTING_ACT_CRASH_AND_ACT_RESTART_ONLY_WHEN_ACCEPTED_FORMAL_PRECONDITIONS_HOLD"
    ),
    "lost_response_reexposure_rule": (
        "ONLY_EXACT_PREVIOUSLY_DURABLE_EFFECT_IDENTITY_STATUS_BYTES_AND_DURABLE_"
        "SEQUENCE_MAY_BE_REEXPOSED_WITH_NO_NEW_TRANSITION"
    ),
    "pre_init_diagnostic_rule": (
        "BEFORE_FIRST_CLEAN_OPEN_EVENTS_HAVE_NO_FORMAL_STATE_ROOT_AND_ARE_EXCLUDED_FROM_EXPORTED_"
        "FORMAL_TRACE; FIRST_CLEAN_OPEN_BINDS_INIT_ROOT"
    ),
    "preserved_event_fields": [
        "ACTION_ID",
        "REQUEST_ID",
        "PARENT_HASHES",
        "BODY_HASH",
        "RESULT_HASH",
        "PRIOR_STATE_ROOT",
        "NEXT_STATE_ROOT",
        "DURABLE_SEQUENCE",
        "OUTCOME",
        "ARTIFACT_REFS",
    ],
    "stutter_durable_sequence_rule": "UNCHANGED",
    "stutter_new_effect_identity_exposed": False,
    "stutter_new_protocol_outcome_exposed": False,
    "stutter_state_root_rule": "PRIOR_STATE_ROOT_EQUALS_NEXT_STATE_ROOT",
    "timer_delivery_action_synthesis": False,
    "transport_retry_action_synthesis": False,
    "runtime_consensus_action_synthesis_by_java_forbidden": True,
}
EXPECTED_SELECTION_RULE: Final = {
    "algorithm": [
        "ANY_MISSING_OR_FAILED_HARD_GATE_SELECT_NULL",
        ("SELECT_ISOLATED_SIDECAR_IF_HARD_GATES_CONTAINMENT_AND_INTEGER_PERFORMANCE_BOUNDS_PASS"),
        (
            "EMBEDDED_FFM_REQUIRES_ALL_HARD_GATES_AND_SEPARATE_IMMUTABLE_"
            "PREMEASUREMENT_RISK_ACCEPTANCE"
        ),
        "PREFER_ISOLATED_SIDECAR_IF_BOTH_QUALIFY",
        ("AMBIGUITY_POST_HOC_THRESHOLD_MISSING_RISK_ACCEPTANCE_OR_ARITHMETIC_ERROR_SELECT_NULL"),
    ],
    "fallback_copy_bytes_per_operation_max": 33_570_816,
    "selected_profile": None,
    "sidecar_p99_fixed_load_latency_ratio_bps_max": 12_500,
    "sidecar_saturation_throughput_ratio_bps_min": 9_000,
    "status": "FROZEN_BEFORE_MEASUREMENT",
    "tie_break": "ISOLATED_SIDECAR",
}
TOP_LEVEL_FIELDS: Final = {
    "authority",
    "comparison_plan",
    "formal_impact",
    "historical_lineage",
    "ipc_contract",
    "measurement_status",
    "profile_selection_rule",
    "runtime_ownership",
    "schema_version",
    "status",
    "trace_projection",
    "trace_projection_invariants",
    "type_name",
}


def sha256_id(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        require(key not in value, "SIDECAR_JSON_DUPLICATE_KEY", key)
        value[key] = item
    return value


def canonical_design_bytes(raw: bytes, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        document = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExactnessError(f"SIDECAR_JSON_INVALID:{label}") from error
    require(isinstance(document, dict), "SIDECAR_JSON_OBJECT_REQUIRED", label)
    canonical = canonical_bytes(document)
    require(raw in {canonical, canonical + b"\n"}, "SIDECAR_JSON_NOT_CANONICAL", label)
    return document, canonical


def validate_design(document: dict[str, Any]) -> None:
    require(set(document) == TOP_LEVEL_FIELDS, "SIDECAR_DESIGN_FIELDS")
    require(
        document["type_name"] == "FEATURE010_ISOLATED_SIDECAR_REFINEMENT_DESIGN",
        "SIDECAR_DESIGN_TYPE",
    )
    require(document["schema_version"] == "1.0.0", "SIDECAR_DESIGN_SCHEMA")
    require(document["status"] == "DESIGN_ONLY_NOT_IMPLEMENTED", "SIDECAR_DESIGN_STATUS")
    require(document["measurement_status"] == "NOT_RUN", "SIDECAR_MEASUREMENT_STATUS")
    require(document["authority"] == EXPECTED_AUTHORITY, "SIDECAR_AUTHORITY_BOUNDARY")
    require(document["formal_impact"] == EXPECTED_FORMAL_IMPACT, "SIDECAR_FORMAL_IMPACT")
    require(
        document["historical_lineage"] == EXPECTED_HISTORICAL_LINEAGE,
        "SIDECAR_HISTORICAL_LINEAGE",
    )
    require(
        document["runtime_ownership"] == EXPECTED_RUNTIME_OWNERSHIP,
        "SIDECAR_RUNTIME_OWNERSHIP",
    )
    require(document["trace_projection"] == EXPECTED_TRACE_PROJECTION, "SIDECAR_TRACE_PROJECTION")
    require(
        document["trace_projection_invariants"] == EXPECTED_TRACE_PROJECTION_INVARIANTS,
        "SIDECAR_TRACE_PROJECTION_INVARIANTS",
    )
    require(
        document["profile_selection_rule"] == EXPECTED_SELECTION_RULE,
        "SIDECAR_PROFILE_SELECTION_RULE",
    )

    contract = document["ipc_contract"]
    require(
        set(contract)
        == {
            "backpressure",
            "bounds",
            "canonical_framing",
            "contract_name",
            "descriptor_handshake",
            "ffi_output_sizing",
            "operations",
            "ownership",
            "payload_codec",
            "persist_before_expose",
            "retry_and_stale_response",
            "shared_memory",
            "timeout_and_crash_detection",
            "version",
            "vote_boundary",
        },
        "SIDECAR_IPC_FIELDS",
    )
    require(contract["contract_name"] == "delta-local-sidecar-ipc", "SIDECAR_IPC_NAME")
    require(contract["version"] == {"major": 1, "minor": 1}, "SIDECAR_IPC_VERSION")
    require(contract["operations"] == EXPECTED_OPERATIONS, "SIDECAR_IPC_OPERATIONS")
    require(contract["bounds"] == EXPECTED_BOUNDS, "SIDECAR_IPC_BOUNDS")
    require(
        contract["bounds"]["max_inline_payload_bytes"]
        == contract["bounds"]["max_logical_payload_bytes"]
        and contract["bounds"]["control_envelope_bytes"]
        == contract["bounds"]["header_bytes"] + contract["bounds"]["max_inline_payload_bytes"],
        "SIDECAR_BOUNDED_COPY_TOTALITY",
    )
    require(
        document["profile_selection_rule"]["fallback_copy_bytes_per_operation_max"]
        == 2 * contract["bounds"]["max_logical_payload_bytes"],
        "SIDECAR_FALLBACK_COPY_ACCOUNTING_BOUND",
    )
    require(
        sha256_id(canonical_bytes(contract["bounds"])) == EXPECTED_BOUNDS_ID,
        "SIDECAR_BOUNDS_ID",
    )
    require(
        contract["persist_before_expose"] == EXPECTED_PERSIST_SEQUENCE,
        "SIDECAR_PERSIST_BEFORE_EXPOSE",
    )
    require(contract["ownership"] == EXPECTED_IPC_OWNERSHIP, "SIDECAR_IPC_OWNERSHIP")
    require(
        contract["descriptor_handshake"] == EXPECTED_DESCRIPTOR_HANDSHAKE,
        "SIDECAR_DESCRIPTOR_HANDSHAKE",
    )
    framing = contract["canonical_framing"]
    require(
        framing["checked_length_and_offset_arithmetic"] is True
        and framing["byte_order"] == "UNSIGNED_BIG_ENDIAN"
        and framing["magic_ascii"] == "DELTAIPC"
        and framing["header_size_bytes"] == 128,
        "SIDECAR_FRAMING_BOUNDS",
    )
    require(framing["field_layout"] == EXPECTED_FRAME_LAYOUT, "SIDECAR_FRAME_LAYOUT")
    require(framing["flag_values"] == EXPECTED_FLAG_VALUES, "SIDECAR_FRAME_FLAGS")
    require(framing["flag_rules"] == EXPECTED_FLAG_RULES, "SIDECAR_FRAME_FLAG_RULES")
    require(
        framing["opcode_flag_requirements"] == EXPECTED_OPCODE_FLAG_REQUIREMENTS,
        "SIDECAR_OPCODE_FLAG_REQUIREMENTS",
    )
    require(
        framing["response_capacity_rule"] == EXPECTED_RESPONSE_CAPACITY_RULE,
        "SIDECAR_RESPONSE_CAPACITY_RULE",
    )
    require(framing["sequence_rule"] == EXPECTED_SEQUENCE_RULE, "SIDECAR_SEQUENCE_RULE")
    require(framing["message_type_values"] == EXPECTED_MESSAGE_TYPES, "SIDECAR_FRAME_OPCODES")
    require(
        sha256_id(
            canonical_bytes(
                {
                    "flag_rules": framing["flag_rules"],
                    "flag_values": framing["flag_values"],
                    "opcode_flag_requirements": framing["opcode_flag_requirements"],
                    "response_capacity_rule": framing["response_capacity_rule"],
                }
            )
        )
        == EXPECTED_FLAG_TABLE_ID,
        "SIDECAR_FLAG_TABLE_ID",
    )
    require(
        sha256_id(canonical_bytes(framing["message_type_values"]))
        == EXPECTED_MESSAGE_TYPE_TABLE_ID,
        "SIDECAR_MESSAGE_TYPE_TABLE_ID",
    )
    require(
        sha256_id(canonical_bytes(framing)) == EXPECTED_FRAME_LAYOUT_ID,
        "SIDECAR_FRAME_LAYOUT_ID",
    )
    require(
        contract["ffi_output_sizing"]
        == {
            "buffer_too_small_may_follow_durable_submit": True,
            "rule": (
                "PREALLOCATE_FROZEN_MAXIMUM_OR_RETRY_IDENTICAL_REQUEST_ID_AND_CANONICAL_"
                "BODY_WITHIN_HARD_BOUND; NEVER_TREAT_BUFFER_TOO_SMALL_AS_PROOF_OF_NON_ADMISSION"
            ),
        },
        "SIDECAR_FFI_OUTPUT_SIZING",
    )
    require(
        contract["backpressure"]
        == {
            "admission_rule": "REJECT_ONLY_BEFORE_NATIVE_ADMISSION",
            "durable_effect_drop_forbidden": True,
            "queue_full_projection": "STUTTER",
            "response_storage_rule": (
                "RESERVE_BOUNDED_CAPACITY_OR_RETRIEVABLE_REPLAY_SLOT_BEFORE_ADMISSION"
            ),
        },
        "SIDECAR_BACKPRESSURE",
    )
    require(contract["shared_memory"] == EXPECTED_SHARED_MEMORY, "SIDECAR_SHARED_MEMORY")
    require(
        sha256_id(canonical_bytes(contract["shared_memory"])) == EXPECTED_SHARED_MEMORY_ID,
        "SIDECAR_SHARED_MEMORY_ID",
    )
    payload = contract["payload_codec"]
    require(payload["body_rules"] == EXPECTED_PAYLOAD_BODY_RULES, "SIDECAR_PAYLOAD_RULES")
    require(
        payload["carrier_eligibility"] == EXPECTED_CARRIER_ELIGIBILITY,
        "SIDECAR_CARRIER_ELIGIBILITY",
    )
    require(
        payload["admission_encoding_rules"] == EXPECTED_ADMISSION_ENCODING_RULES,
        "SIDECAR_ADMISSION_ENCODING",
    )
    require(
        payload["admitted_sequence_rule"]
        == (
            "ZERO_ONLY_FOR_NOT_APPLICABLE_OR_NOT_ADMITTED_PROVEN; POSITIVE_VALUE_ASSIGNED_BY_"
            "NATIVE_ADMISSION_OR_VERIFIED_RECOVERY"
        ),
        "SIDECAR_ADMITTED_SEQUENCE_RULE",
    )
    require(
        payload["native_status_unavailable_value"] == 4_294_967_295,
        "SIDECAR_NATIVE_STATUS_SENTINEL",
    )
    require(
        payload["error_response_rule"]
        == (
            "EMIT_ONLY_FOR_TRUSTED_REQUEST_ID_DIGEST_OR_SAFE_PREPARSE_SENTINEL_WITH_TRUSTED_"
            "CURRENT_SESSION_GENERATION_HEADER_AND_CORRELATION; OTHERWISE_DROP_WITHOUT_RESPONSE_"
            "CLOSE_CHANNEL_PERMANENTLY_FENCE_GENERATION_NO_NATIVE_CALL"
        ),
        "SIDECAR_ERROR_RESPONSE_RULE",
    )
    require(payload["wire_type_values"] == EXPECTED_WIRE_TYPE_VALUES, "SIDECAR_WIRE_TYPES")
    require(
        payload["shared_memory_disposition_values"] == EXPECTED_SHARED_MEMORY_DISPOSITION_VALUES,
        "SIDECAR_SHARED_MEMORY_DISPOSITIONS",
    )
    require(
        payload["optional_field_rules"] == EXPECTED_OPTIONAL_FIELD_RULES,
        "SIDECAR_OPTIONAL_FIELDS",
    )
    require(
        payload["nested_c_abi_descriptor"] == EXPECTED_NESTED_C_ABI_DESCRIPTOR,
        "SIDECAR_NESTED_ABI_DESCRIPTOR",
    )
    require(
        set(payload["field_registry"]) == set(EXPECTED_MESSAGE_TYPES),
        "SIDECAR_PAYLOAD_MESSAGE_COVERAGE",
    )
    require(
        payload["field_registry"]["CLIENT_HELLO"] == payload["field_registry"]["SERVER_DESCRIPTOR"],
        "SIDECAR_HANDSHAKE_FIELD_SYMMETRY",
    )
    require(
        all(isinstance(fields, list) and fields for fields in payload["field_registry"].values()),
        "SIDECAR_PAYLOAD_FIELD_REGISTRY",
    )
    for message_type, fields in payload["field_registry"].items():
        field_ids: list[int] = []
        for field in fields:
            parts = field.split(":")
            require(len(parts) == 3, "SIDECAR_PAYLOAD_FIELD_TOKEN", message_type)
            require(parts[0].isdigit(), "SIDECAR_PAYLOAD_FIELD_ID", message_type)
            field_ids.append(int(parts[0]))
        require(
            field_ids == sorted(set(field_ids)) and all(0 < item <= 65_535 for item in field_ids),
            "SIDECAR_PAYLOAD_FIELD_ORDER",
            message_type,
        )
    require(
        contract["bounds"]["max_logical_payload_bytes"]
        == contract["bounds"]["max_canonical_effect_bytes"]
        + contract["bounds"]["max_payload_metadata_bytes"],
        "SIDECAR_LOGICAL_PAYLOAD_BOUND",
    )
    require(
        sha256_id(canonical_bytes(payload)) == EXPECTED_PAYLOAD_SCHEMA_ID,
        "SIDECAR_PAYLOAD_SCHEMA_ID",
    )
    require(
        contract["retry_and_stale_response"] == EXPECTED_RETRY_AND_STALE_RESPONSE,
        "SIDECAR_RETRY_STALE_RESPONSE",
    )
    require(
        contract["timeout_and_crash_detection"] == EXPECTED_TIMEOUT_AND_CRASH_DETECTION,
        "SIDECAR_TIMEOUT_CRASH_DETECTION",
    )
    require(contract["vote_boundary"] == EXPECTED_VOTE_BOUNDARY, "SIDECAR_VOTE_BOUNDARY")

    comparison = document["comparison_plan"]
    require(
        comparison["status"] == "PREREGISTERED_NOT_EXECUTED"
        and comparison["freeze_point"] == "BEFORE_ANY_MEASUREMENT",
        "SIDECAR_COMPARISON_FREEZE",
    )
    require(
        comparison["comparison_join"] == "TWO_SEPARATELY_ADMITTED_EXACT_RUNS_ONE_PROFILE_PER_RUN",
        "SIDECAR_COMPARISON_ADMISSION",
    )
    require(
        comparison["profiles"] == ["EMBEDDED_FFM", "ISOLATED_SIDECAR"],
        "SIDECAR_COMPARISON_PROFILES",
    )
    require(len(comparison["identical_pair_fields"]) == 14, "SIDECAR_COMPARISON_PAIRING")
    require(len(comparison["paired_crash_points"]) == 7, "SIDECAR_COMPARISON_CRASH_MATRIX")
    require(
        len(comparison["sidecar_supplemental_crash_points"]) == 2,
        "SIDECAR_SUPPLEMENTAL_CRASH_MATRIX",
    )
    require(len(comparison["copy_accounting"]) == 8, "SIDECAR_COPY_ACCOUNTING")
    require(len(comparison["required_measurements"]) == 11, "SIDECAR_MEASUREMENTS")
    require(
        len(comparison["exact_cross_profile_equalities"]) == 7,
        "SIDECAR_CROSS_PROFILE_EQUALITY",
    )
    require(len(comparison["hard_gates_common"]) == 12, "SIDECAR_COMMON_HARD_GATES")
    require(len(comparison["hard_gates_sidecar"]) == 2, "SIDECAR_PROFILE_HARD_GATES")
    require(
        comparison["missing_evidence_rule"] == "FAIL_CLOSED_NO_IMPUTATION_NO_SELECTION",
        "SIDECAR_MISSING_EVIDENCE",
    )
    require(
        comparison["aggregation"]
        == {
            "fixed_load_offered_operations_per_block": 6_000,
            "fixed_offered_load_ops_per_second": 100,
            "latency_percentiles": [50, 95, 99],
            "latency_population": ("ALL_60000_COMPLETED_FIXED_LOAD_OPERATIONS_POOLED_PER_PROFILE"),
            "latency_rule": "NEAREST_RANK_INTEGER_NANOSECONDS",
            "measured_blocks": 10,
            "p99_latency_ratio_bps": ("CEILING_SIDECAR_TIMES_10000_DIV_EMBEDDED_NONZERO"),
            "ratio_unit": "INTEGER_BASIS_POINTS_CHECKED_ARITHMETIC",
            "saturation_blocks": 10,
            "staging_fallback_bytes_per_operation": (
                "MAXIMUM_OF_CHECKED_SUM_STAGING_FALLBACK_INGRESS_PLUS_EGRESS_PER_OPERATION"
            ),
            "throughput_block_value": "COMPLETED_OPERATIONS_IN_EXACT_60_SECOND_WINDOW",
            "throughput_profile_statistic": "MINIMUM_ACROSS_10_BLOCKS",
            "throughput_ratio_bps": ("FLOOR_SIDECAR_TIMES_10000_DIV_EMBEDDED_NONZERO"),
            "throughput_window_seconds": 60,
            "warmup_operations": 1_000,
        },
        "SIDECAR_AGGREGATION_RULE",
    )
    require(
        sha256_id(canonical_bytes(document)) == EXPECTED_CANONICAL_DESIGN_ID,
        "SIDECAR_DESIGN_CONTENT_ID",
    )


def validate_markdown(raw: bytes) -> None:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ExactnessError("SIDECAR_MARKDOWN_UTF8") from error
    normalized = " ".join(text.split())
    required_phrases = [
        "design-only prerequisite; not implemented",
        HISTORICAL_FAIL_COMMIT,
        HISTORICAL_FAIL_TREE,
        "T028/T029 and HR010-013/014 remain open",
        "`selected_profile` remains `null`",
        "There is no Gate A, B, C, or D qualification",
        "validate command -> compute candidate -> append WAL -> durability barrier",
        "`MESSAGE_TYPE` is also the sole payload type code",
        "`DELTABI1`",
        "`FREE -> WRITING -> PUBLISHED -> READING -> ACKED|REJECTED -> FREE`",
        "`CLIENT_HELLO` and `SERVER_DESCRIPTOR` are inline-only",
        "That frame is not slot-release authority",
        "The same generation is never unfenced or reused",
        "creates no new effect identity or protocol outcome",
        "A wrapper never synthesizes `ACT-MESSAGE-DELIVER`",
        "ACT-RESTART",
        "ACT-JOURNAL-RECOVER",
        "ACT-MESSAGE-REPLAY",
        "separately admitted exact runs",
        "This design does not apply it",
    ]
    for phrase in required_phrases:
        require(phrase in normalized, "SIDECAR_MARKDOWN_BOUNDARY", phrase)


def commit_bytes(commit: str, path: Path) -> bytes:
    relative = path.relative_to(ROOT).as_posix()
    process = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, "SIDECAR_SOURCE_PATH_MISSING", relative)
    return process.stdout


def verify_repository(source_commit: str | None) -> dict[str, Any]:
    source = None
    if source_commit is not None:
        source = source_identity(source_commit)
        validate_source(source)
        design_raw = commit_bytes(source["commit"], DESIGN_PATH)
        markdown_raw = commit_bytes(source["commit"], DESIGN_MARKDOWN_PATH)
        profile_risk_raw = commit_bytes(source["commit"], PROFILE_RISK_PATH)
    else:
        design_raw = DESIGN_PATH.read_bytes()
        markdown_raw = DESIGN_MARKDOWN_PATH.read_bytes()
        profile_risk_raw = PROFILE_RISK_PATH.read_bytes()

    document, canonical = canonical_design_bytes(design_raw, DESIGN_PATH.name)
    validate_design(document)
    validate_markdown(markdown_raw)
    profile_risk, _ = canonical_design_bytes(profile_risk_raw, PROFILE_RISK_PATH.name)
    require(profile_risk == EXPECTED_PROFILE_RISK_DECISION, "HISTORICAL_RISK_DECISION_CHANGED")

    require(sha256_id(design_raw) == EXPECTED_DESIGN_SHA256, "SIDECAR_DESIGN_SHA256")
    require(sha256_id(markdown_raw) == EXPECTED_MARKDOWN_SHA256, "SIDECAR_MARKDOWN_SHA256")
    require(canonical_bytes(document) == canonical, "SIDECAR_CANONICAL_DOCUMENT")

    return {
        "authority": EXPECTED_AUTHORITY,
        "design_sha256": EXPECTED_DESIGN_SHA256,
        "formal_impact": "REFINEMENT_ONLY",
        "markdown_sha256": EXPECTED_MARKDOWN_SHA256,
        "selected_profile": None,
        "source": source,
        "status": "PASS_SIDECAR_REFINEMENT_DESIGN_ONLY",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    arguments = parser.parse_args()
    try:
        require(arguments.check_only, "CHECK_ONLY_REQUIRED")
        result = verify_repository(arguments.source_commit)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, RuntimeError) as error:
        print(canonical_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
