#ifndef DELTA_ABI_H
#define DELTA_ABI_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32)
#if defined(DELTA_FFI_BUILD)
#define DELTA_API __declspec(dllexport)
#else
#define DELTA_API __declspec(dllimport)
#endif
#else
#define DELTA_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#define DELTA_NOEXCEPT noexcept
#else
#define DELTA_NOEXCEPT
#endif

#define DELTA_ABI_MAJOR UINT16_C(1)
#define DELTA_ABI_MINOR UINT16_C(0)
#define DELTA_ABI_FEATURE_BITS UINT64_C(7)
#define DELTA_ABI_DESCRIPTOR_SIZE UINT32_C(64)
#define DELTA_ABI_OPEN_OPTIONS_SIZE UINT32_C(128)
#define DELTA_ABI_OUTPUT_BUFFER_SIZE UINT32_C(32)
#define DELTA_HIERARCHY_CONTEXT_SIZE UINT32_C(168)
#define DELTA_SCHEDULING_ELIGIBILITY_CONTEXT_SIZE UINT32_C(184)
#define DELTA_CERTIFICATE_INSPECT_CONTEXT_SIZE UINT32_C(40)
#define DELTA_CERTIFICATE_CHAIN_CONTEXT_SIZE UINT32_C(168)
#define DELTA_QLORA_CONTEXT_SIZE UINT32_C(104)
#define DELTA_SCHEMA_VERSION "1.0.0"
#define DELTA_PROTOCOL_VERSION "003.1.0"
#define DELTA_RUNTIME_PROFILE "embedded-ffm"
#define DELTA_FORMAL_SEMANTICS_ID \
  "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
#define DELTA_BUILD_ID \
  "sha256:1616161616161616161616161616161616161616161616161616161616161616"
#define DELTA_SCHEMA_SET_ID \
  "sha256:1717171717171717171717171717171717171717171717171717171717171717"

typedef struct delta_runtime delta_runtime_t;

typedef enum delta_status {
  DELTA_STATUS_OK = 0,
  DELTA_STATUS_INVALID_ARGUMENT = 1,
  DELTA_STATUS_ABI_MISMATCH = 2,
  DELTA_STATUS_SCHEMA_MISMATCH = 3,
  DELTA_STATUS_PROTOCOL_MISMATCH = 4,
  DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH = 5,
  DELTA_STATUS_BUILD_MISMATCH = 6,
  DELTA_STATUS_BUFFER_TOO_SMALL = 7,
  DELTA_STATUS_CLOSED = 8,
  DELTA_STATUS_QUEUE_FULL = 9,
  DELTA_STATUS_IO_ERROR = 10,
  DELTA_STATUS_CORRUPT_DURABLE_STATE = 11,
  DELTA_STATUS_CONFLICT = 12,
  DELTA_STATUS_TRANSITION_REJECTED = 13,
  DELTA_STATUS_INTERNAL_ERROR = 14
} delta_status_t;

typedef struct delta_bytes_view {
  const uint8_t* data;
  size_t size;
} delta_bytes_view_t;

typedef struct delta_output_buffer {
  uint8_t* data;
  size_t capacity;
  size_t required;
  size_t written;
} delta_output_buffer_t;

typedef struct delta_runtime_descriptor {
  uint32_t struct_size;
  uint16_t abi_major;
  uint16_t abi_minor;
  uint64_t feature_bits;
  const char* schema_version;
  const char* protocol_version;
  const char* formal_semantics_id;
  const char* build_id;
  const char* schema_set_id;
  const char* runtime_profile;
} delta_runtime_descriptor_t;

typedef struct delta_runtime_open_options {
  uint32_t struct_size;
  uint32_t submission_capacity;
  delta_bytes_view_t directory_utf8;
  delta_bytes_view_t initial_state;
  uint16_t expected_abi_major;
  uint16_t expected_abi_minor;
  uint32_t reserved;
  delta_bytes_view_t expected_schema_version;
  delta_bytes_view_t expected_protocol_version;
  delta_bytes_view_t expected_formal_semantics_id;
  delta_bytes_view_t expected_build_id;
  delta_bytes_view_t expected_schema_set_id;
} delta_runtime_open_options_t;

typedef struct delta_hierarchy_context {
  uint32_t struct_size;
  uint32_t reserved;
  delta_bytes_view_t accumulator_proof_instance_id;
  delta_bytes_view_t coefficient_plan_root;
  delta_bytes_view_t fixedpoint_config_id;
  delta_bytes_view_t formal_semantics_id;
  delta_bytes_view_t frozen_input_root;
  delta_bytes_view_t parent_checkpoint_id;
  delta_bytes_view_t profile_id;
  delta_bytes_view_t round_config_id;
  delta_bytes_view_t scale_table_id;
  delta_bytes_view_t shard_plan_id;
} delta_hierarchy_context_t;

typedef struct delta_scheduling_eligibility_context {
  uint32_t struct_size;
  uint32_t reserved;
  delta_bytes_view_t arithmetic_profile_id;
  delta_bytes_view_t parameter_schema_id;
  delta_bytes_view_t round_config_id;
  delta_bytes_view_t eligibility_policy_id;
  delta_bytes_view_t model_mode;
  delta_bytes_view_t allowed_domain_ids_csv;
  delta_bytes_view_t allowed_region_ids_csv;
  delta_bytes_view_t allowed_software_build_ids_csv;
  delta_bytes_view_t trusted_signature_ids_csv;
  uint64_t decision_tick;
  uint64_t identity_epoch;
  uint64_t minimum_memory_bytes;
  uint64_t minimum_sample_count;
} delta_scheduling_eligibility_context_t;

typedef enum delta_certificate_kind {
  DELTA_CERTIFICATE_INPUT_SET = 1,
  DELTA_CERTIFICATE_SEED_TRANSCRIPT = 2,
  DELTA_CERTIFICATE_NORM_EVIDENCE = 3,
  DELTA_CERTIFICATE_ELIGIBILITY = 4,
  DELTA_CERTIFICATE_AGGREGATION_PLAN = 5,
  DELTA_CERTIFICATE_PARAMETER_SHARD_QC = 6,
  DELTA_CERTIFICATE_AGGREGATE_ROOT_QC = 7,
  DELTA_CERTIFICATE_APPLY_PROFILE = 8,
  DELTA_CERTIFICATE_APPLY_CANDIDATE = 9,
  DELTA_CERTIFICATE_APPLY_QC = 10,
  DELTA_CERTIFICATE_CURRENT_POINTER_COMMAND = 11
} delta_certificate_kind_t;

typedef struct delta_certificate_inspect_context {
  uint32_t struct_size;
  uint32_t kind;
  delta_bytes_view_t expected_content_id;
  delta_bytes_view_t expected_formal_semantics_id;
} delta_certificate_inspect_context_t;

typedef struct delta_certificate_chain_context {
  uint32_t struct_size;
  uint32_t reserved;
  delta_bytes_view_t expected_formal_semantics_id;
  delta_bytes_view_t expected_native_build_id;
  delta_bytes_view_t expected_execution_plan_id;
  delta_bytes_view_t expected_certified_round_policy_id;
  delta_bytes_view_t expected_parent_checkpoint_id;
  delta_bytes_view_t expected_final_checkpoint_id;
  delta_bytes_view_t expected_runtime_state_id;
  delta_bytes_view_t expected_effect_set_id;
  delta_bytes_view_t expected_runtime_wal_sha256;
  delta_bytes_view_t expected_checkpoint_wal_sha256;
} delta_certificate_chain_context_t;

typedef struct delta_qlora_context {
  uint32_t struct_size;
  uint32_t reserved;
  delta_bytes_view_t adapter_parameter_schema_id;
  delta_bytes_view_t base_model_manifest_id;
  delta_bytes_view_t parent_adapter_id;
  delta_bytes_view_t quantized_base_profile_id;
  delta_bytes_view_t tokenizer_hash;
  delta_bytes_view_t training_mode_id;
} delta_qlora_context_t;

DELTA_API delta_status_t delta_runtime_descriptor(
    uint32_t caller_struct_size,
    delta_runtime_descriptor_t* output);
DELTA_API const char* delta_status_message(delta_status_t status);
DELTA_API delta_status_t delta_runtime_open(
    const delta_runtime_open_options_t* options,
    delta_runtime_t** output);
DELTA_API delta_status_t delta_runtime_submit_borrowed(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_runtime_submit_copy(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_runtime_state(
    delta_runtime_t* runtime,
    delta_output_buffer_t* state_output);
DELTA_API delta_status_t delta_runtime_snapshot(delta_runtime_t* runtime);
DELTA_API delta_status_t delta_runtime_release(delta_runtime_t** runtime);
DELTA_API delta_status_t delta_fixedpoint_shard_validate_borrowed(
    delta_bytes_view_t envelope,
    delta_output_buffer_t* envelope_output);
DELTA_API delta_status_t delta_fixedpoint_shard_validate_copy(
    delta_bytes_view_t envelope,
    delta_output_buffer_t* envelope_output);
DELTA_API delta_status_t delta_distribution_policy_evaluate_borrowed(
    delta_bytes_view_t canonical_manifest,
    delta_bytes_view_t canonical_certificate,
    uint8_t request_make_current,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_distribution_policy_evaluate_copy(
    delta_bytes_view_t canonical_manifest,
    delta_bytes_view_t canonical_certificate,
    uint8_t request_make_current,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_hierarchy_contract_validate_borrowed(
    const delta_hierarchy_context_t* expected_context,
    delta_bytes_view_t canonical_topology,
    delta_bytes_view_t canonical_proof,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_hierarchy_contract_validate_copy(
    const delta_hierarchy_context_t* expected_context,
    delta_bytes_view_t canonical_topology,
    delta_bytes_view_t canonical_proof,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_scheduling_capability_evaluate_borrowed(
    const delta_scheduling_eligibility_context_t* policy,
    delta_bytes_view_t canonical_profile,
    delta_output_buffer_t* decision_output);
DELTA_API delta_status_t delta_scheduling_capability_evaluate_copy(
    const delta_scheduling_eligibility_context_t* policy,
    delta_bytes_view_t canonical_profile,
    delta_output_buffer_t* decision_output);
DELTA_API delta_status_t delta_certificate_inspect_borrowed(
    const delta_certificate_inspect_context_t* context,
    delta_bytes_view_t canonical_certificate,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_certificate_inspect_copy(
    const delta_certificate_inspect_context_t* context,
    delta_bytes_view_t canonical_certificate,
    delta_output_buffer_t* effect_output);
DELTA_API delta_status_t delta_certificate_chain_verify_borrowed(
    const delta_certificate_chain_context_t* context,
    delta_bytes_view_t canonical_bundle,
    delta_output_buffer_t* receipt_output) DELTA_NOEXCEPT;
DELTA_API delta_status_t delta_certificate_chain_verify_copy(
    const delta_certificate_chain_context_t* context,
    delta_bytes_view_t canonical_bundle,
    delta_output_buffer_t* receipt_output) DELTA_NOEXCEPT;
DELTA_API delta_status_t delta_qlora_context_id(
    const delta_qlora_context_t* context,
    delta_output_buffer_t* content_id_output);

#ifdef __cplusplus
}
#endif

#undef DELTA_NOEXCEPT

#endif
