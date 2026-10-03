#include <delta_abi.h>

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/runtime/vote_codec.hpp>

#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] std::vector<std::uint8_t> decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  std::vector<std::uint8_t> result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U])));
  }
  return result;
}

[[nodiscard]] std::vector<std::uint8_t> golden_from(
    std::string_view path,
    std::uint16_t type_code) {
  std::ifstream input(std::string(path), std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] std::vector<std::uint8_t> golden(std::uint16_t type_code) {
  return golden_from(DELTA_GOLDEN_FIXTURE_PATH, type_code);
}

#if defined(DELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH)
[[nodiscard]] std::vector<std::uint8_t> fixedpoint_golden() {
  std::ifstream input(DELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open fixed-point golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(R"REGEX("envelope_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "fixed-point golden envelope not found");
  return decode_hex(match[1].str());
}
#endif

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& value) {
  return {value.data(), value.size()};
}

[[nodiscard]] delta_bytes_view_t view(const delta::core::canonical::Bytes& value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

[[nodiscard]] std::span<const std::byte> bytes(const std::vector<std::uint8_t>& value) {
  return std::as_bytes(std::span(value));
}

[[nodiscard]] std::vector<std::uint8_t> octets(
    std::span<const std::byte> value) {
  std::vector<std::uint8_t> result;
  result.reserve(value.size());
  for (const auto byte : value) {
    result.push_back(std::to_integer<std::uint8_t>(byte));
  }
  return result;
}

[[nodiscard]] std::string content_id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta::core::consensus::VoteAdmissionPolicy round_config_vote_policy() {
  const auto state_bytes = golden(5U);
  return delta::test::vote_fixture::full(
             delta::core::consensus::VoteAction::round_config,
             delta::core::protocol::parse_round_state(bytes(state_bytes)))
      .policy;
}

[[nodiscard]] std::vector<std::uint8_t> round_config_vote_bytes() {
  const auto state_bytes = golden(5U);
  const auto fixture = delta::test::vote_fixture::full(
      delta::core::consensus::VoteAction::round_config,
      delta::core::protocol::parse_round_state(bytes(state_bytes)));
  return octets(delta::core::protocol::encode(fixture.vote));
}

[[nodiscard]] delta_runtime_open_options_t options(
    std::string_view directory,
    const std::vector<std::uint8_t>& initial_state) {
  return delta_runtime_open_options_t{
      DELTA_ABI_OPEN_OPTIONS_SIZE,
      64U,
      view(directory),
      view(initial_state),
      DELTA_ABI_MAJOR,
      DELTA_ABI_MINOR,
      0U,
      view(DELTA_SCHEMA_VERSION),
      view(DELTA_PROTOCOL_VERSION),
      view(DELTA_FORMAL_SEMANTICS_ID),
      view(DELTA_BUILD_ID),
      view(DELTA_SCHEMA_SET_ID),
  };
}

[[nodiscard]] std::filesystem::path fresh_directory(std::string_view name) {
#if defined(_MSVC_LANG)
  constexpr auto language_mode = _MSVC_LANG;
#else
  constexpr auto language_mode = __cplusplus;
#endif
  auto result = std::filesystem::temp_directory_path() / "delta-ffi-003-tests" /
                std::to_string(language_mode) / name;
  std::error_code error;
  std::filesystem::remove_all(result, error);
  expect(!error, "cannot clean exact ABI test directory");
  std::filesystem::create_directories(result, error);
  expect(!error, "cannot create ABI test directory");
  return result;
}

void test_frozen_descriptor_and_status_taxonomy() {
  expect(sizeof(delta_runtime_descriptor_t) == 64U, "descriptor ABI size changed");
  expect(sizeof(delta_runtime_open_options_t) == 128U, "open-options ABI size changed");
  expect(sizeof(delta_output_buffer_t) == 32U, "output-buffer ABI size changed");

  delta_runtime_descriptor_t descriptor{};
  expect(
      delta_runtime_descriptor(DELTA_ABI_DESCRIPTOR_SIZE - 1U, &descriptor) ==
          DELTA_STATUS_ABI_MISMATCH,
      "descriptor size mismatch was accepted");
  expect(descriptor.struct_size == 0U, "descriptor mismatch exposed partial fields");
  expect(
      delta_runtime_descriptor(DELTA_ABI_DESCRIPTOR_SIZE, &descriptor) == DELTA_STATUS_OK,
      "descriptor query failed");
  expect(
      descriptor.struct_size == DELTA_ABI_DESCRIPTOR_SIZE &&
          descriptor.abi_major == DELTA_ABI_MAJOR && descriptor.abi_minor == DELTA_ABI_MINOR &&
          descriptor.feature_bits == DELTA_ABI_FEATURE_BITS,
      "descriptor numeric fields mismatch");
  expect(descriptor.formal_semantics_id == std::string_view(DELTA_FORMAL_SEMANTICS_ID),
         "descriptor formal semantics mismatch");
  expect(descriptor.build_id == std::string_view(DELTA_BUILD_ID), "descriptor build mismatch");
  for (int status = DELTA_STATUS_OK; status <= DELTA_STATUS_INTERNAL_ERROR; ++status) {
    expect(
        std::string_view(delta_status_message(static_cast<delta_status_t>(status))) !=
            "UNKNOWN_STATUS",
        "registered status has no stable name");
  }
}

void test_startup_mismatch_matrix() {
  const auto initial = golden(5U);
  const auto directory = fresh_directory("mismatch").string();
  auto valid = options(directory, initial);
  delta_runtime_t* output = reinterpret_cast<delta_runtime_t*>(UINTPTR_MAX);

  auto changed = valid;
  changed.expected_abi_major = 2U;
  expect(delta_runtime_open(&changed, &output) == DELTA_STATUS_ABI_MISMATCH && output == nullptr,
         "ABI mismatch did not fail closed");

  const std::string wrong_schema = "2.0.0";
  changed = valid;
  changed.expected_schema_version = view(wrong_schema);
  expect(delta_runtime_open(&changed, &output) == DELTA_STATUS_SCHEMA_MISMATCH && output == nullptr,
         "schema mismatch did not fail closed");

  const std::string wrong_protocol = "999.0.0";
  changed = valid;
  changed.expected_protocol_version = view(wrong_protocol);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_PROTOCOL_MISMATCH && output == nullptr,
      "protocol mismatch did not fail closed");

  const std::string wrong_formal =
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  changed = valid;
  changed.expected_formal_semantics_id = view(wrong_formal);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH &&
          output == nullptr,
      "formal mismatch did not fail closed");

  const std::string wrong_build =
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
  changed = valid;
  changed.expected_build_id = view(wrong_build);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_BUILD_MISMATCH && output == nullptr,
      "build mismatch did not fail closed");

  const std::string wrong_schema_set =
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
  changed = valid;
  changed.expected_schema_set_id = view(wrong_schema_set);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_SCHEMA_MISMATCH && output == nullptr,
      "schema-set mismatch did not fail closed");
}

[[nodiscard]] std::vector<std::uint8_t> retry_effect(
    delta_runtime_t* runtime,
    const std::vector<std::uint8_t>& command,
    bool copy_path) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  const auto first = copy_path ? delta_runtime_submit_copy(runtime, view(command), &sizing)
                               : delta_runtime_submit_borrowed(runtime, view(command), &sizing);
  expect(first == DELTA_STATUS_BUFFER_TOO_SMALL, "zero-capacity call did not negotiate size");
  expect(sizing.required > 0U && sizing.written == 0U, "size negotiation exposed partial bytes");
  std::vector<std::uint8_t> output(sizing.required);
  delta_output_buffer_t destination{output.data(), output.size(), 0U, 0U};
  const auto second = copy_path ? delta_runtime_submit_copy(runtime, view(command), &destination)
                                : delta_runtime_submit_borrowed(runtime, view(command), &destination);
  expect(second == DELTA_STATUS_OK, "capacity retry failed");
  expect(destination.required == output.size() && destination.written == output.size(),
         "capacity retry size fields mismatch");
  return output;
}

void test_open_submit_snapshot_release_and_memory_rules() {
  const auto initial = golden(5U);
  auto command = golden(6U);
  const auto directory = fresh_directory("lifecycle").string();
  auto open_options = options(directory, initial);
  delta_runtime_t* handle = nullptr;
  expect(delta_runtime_open(&open_options, &handle) == DELTA_STATUS_OK && handle != nullptr,
         "valid ABI open failed");

  const auto borrowed_effect = retry_effect(handle, command, false);
  const auto copy_effect = retry_effect(handle, command, true);
  expect(borrowed_effect == copy_effect, "borrowed and copy paths produced different effects");
  std::fill(command.begin(), command.end(), std::uint8_t{0U});
  expect(delta_runtime_snapshot(handle) == DELTA_STATUS_OK,
         "native retained borrowed command memory after synchronous call");

  delta_output_buffer_t state_size{nullptr, 0U, 0U, 0U};
  expect(delta_runtime_state(handle, &state_size) == DELTA_STATUS_BUFFER_TOO_SMALL,
         "state getter did not negotiate size");
  std::vector<std::uint8_t> state(state_size.required);
  delta_output_buffer_t state_output{state.data(), state.size(), 0U, 0U};
  expect(delta_runtime_state(handle, &state_output) == DELTA_STATUS_OK,
         "state getter retry failed");
  expect(state == initial, "round-config replay unexpectedly changed state bytes");

  std::vector<std::uint8_t> malformed{0U, 1U, 2U};
  std::vector<std::uint8_t> sentinel(16U, 0x5aU);
  delta_output_buffer_t rejected{sentinel.data(), sentinel.size(), 99U, 99U};
  expect(delta_runtime_submit_borrowed(handle, view(malformed), &rejected) ==
             DELTA_STATUS_INVALID_ARGUMENT,
         "malformed command escaped stable status mapping");
  expect(rejected.required == 0U && rejected.written == 0U,
         "rejected command exposed partial output metadata");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "explicit handle release failed");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "repeated null handle release was not idempotent");
}

void test_versioned_submit_receipt_abi() {
  expect(sizeof(delta_submit_receipt_v1_t) == DELTA_SUBMIT_RECEIPT_V1_SIZE,
         "submit receipt ABI size changed");
  expect(offsetof(delta_submit_receipt_v1_t, struct_size) == 0U &&
             offsetof(delta_submit_receipt_v1_t, reserved) == 4U &&
             offsetof(delta_submit_receipt_v1_t, journal_sequence) == 8U &&
             offsetof(delta_submit_receipt_v1_t, canonical_effect) == 16U,
         "submit receipt ABI offsets changed");
  expect(
      (DELTA_ABI_FEATURE_BITS & DELTA_ABI_FEATURE_SUBMIT_RECEIPT_V1) != 0U,
      "submit-receipt feature bit is absent");

  const auto initial = golden(5U);
  const auto command = golden(6U);
  const auto directory = fresh_directory("submit-receipt").string();
  auto open_options = options(directory, initial);
  delta_runtime_t* handle = nullptr;
  expect(delta_runtime_open(&open_options, &handle) == DELTA_STATUS_OK && handle != nullptr,
         "submit-receipt runtime open failed");

  struct ReceiptCanary {
    delta_submit_receipt_v1_t receipt;
    std::array<std::uint8_t, 16> guard;
  } undersized{};
  std::memset(&undersized, 0x5a, sizeof(undersized));
  undersized.receipt.struct_size = DELTA_SUBMIT_RECEIPT_V1_SIZE - 1U;
  const auto undersized_before = undersized;
  expect(
      delta_runtime_submit_receipt_borrowed_v1(handle, view(command), &undersized.receipt) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "undersized submit receipt was accepted");
  expect(
      std::memcmp(&undersized, &undersized_before, sizeof(undersized)) == 0,
      "undersized submit receipt or adjacent canary was modified");

  ReceiptCanary nonzero_reserved{};
  std::memset(&nonzero_reserved, 0x5a, sizeof(nonzero_reserved));
  nonzero_reserved.receipt.struct_size = DELTA_SUBMIT_RECEIPT_V1_SIZE;
  nonzero_reserved.receipt.reserved = 1U;
  const auto reserved_before = nonzero_reserved;
  expect(
      delta_runtime_submit_receipt_copy_v1(handle, view(command), &nonzero_reserved.receipt) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "nonzero submit receipt reserved field was accepted");
  expect(
      std::memcmp(&nonzero_reserved, &reserved_before, sizeof(nonzero_reserved)) == 0,
      "invalid submit receipt was reset before exact shape validation");

  std::array<std::uint8_t, 1> invalid_storage{0x5aU};
  delta_submit_receipt_v1_t invalid_input_receipt{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {invalid_storage.data(), invalid_storage.size(), 77U, 88U},
  };
  for (const bool copy_path : {false, true}) {
    invalid_input_receipt.journal_sequence = 99U;
    invalid_input_receipt.canonical_effect.required = 77U;
    invalid_input_receipt.canonical_effect.written = 88U;
    const auto status = copy_path
                            ? delta_runtime_submit_receipt_copy_v1(
                                  handle, {nullptr, 1U}, &invalid_input_receipt)
                            : delta_runtime_submit_receipt_borrowed_v1(
                                  handle, {nullptr, 1U}, &invalid_input_receipt);
    expect(status == DELTA_STATUS_INVALID_ARGUMENT,
           "invalid submit command view did not return INVALID_ARGUMENT");
    expect(
        invalid_input_receipt.journal_sequence == 0U &&
            invalid_input_receipt.canonical_effect.required == 0U &&
            invalid_input_receipt.canonical_effect.written == 0U && invalid_storage[0] == 0x5aU,
        "invalid submit command view exposed partial receipt metadata or bytes");
  }

  auto storage_probe = delta::core::protocol::parse_command(bytes(command));
  storage_probe.request_id = "request-invalid-submit-receipt-storage";
  const auto storage_probe_bytes = octets(delta::core::protocol::encode(storage_probe));
  delta_submit_receipt_v1_t invalid_storage_receipt{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {nullptr, 1U, 77U, 88U},
  };
  for (const bool copy_path : {false, true}) {
    invalid_storage_receipt.journal_sequence = 99U;
    invalid_storage_receipt.canonical_effect.required = 77U;
    invalid_storage_receipt.canonical_effect.written = 88U;
    const auto status = copy_path
                            ? delta_runtime_submit_receipt_copy_v1(
                                  handle, view(storage_probe_bytes), &invalid_storage_receipt)
                            : delta_runtime_submit_receipt_borrowed_v1(
                                  handle, view(storage_probe_bytes), &invalid_storage_receipt);
    expect(status == DELTA_STATUS_INVALID_ARGUMENT,
           "invalid submit receipt output storage did not fail before admission");
    expect(
        invalid_storage_receipt.journal_sequence == 0U &&
            invalid_storage_receipt.canonical_effect.required == 0U &&
            invalid_storage_receipt.canonical_effect.written == 0U,
        "invalid submit receipt output storage exposed partial metadata");
  }

  delta_submit_receipt_v1_t sizing{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {nullptr, 0U, 77U, 88U},
  };
  expect(
      delta_runtime_submit_receipt_borrowed_v1(handle, view(command), &sizing) ==
          DELTA_STATUS_BUFFER_TOO_SMALL,
      "submit receipt sizing did not request retry");
  expect(
      sizing.journal_sequence == 1U && sizing.canonical_effect.required > 0U &&
          sizing.canonical_effect.written == 0U,
      "submit receipt sizing did not atomically expose the durable sequence and exact size");

  std::vector<std::uint8_t> borrowed_effect(sizing.canonical_effect.required);
  delta_submit_receipt_v1_t borrowed{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {borrowed_effect.data(), borrowed_effect.size(), 77U, 88U},
  };
  expect(
      delta_runtime_submit_receipt_borrowed_v1(handle, view(command), &borrowed) ==
          DELTA_STATUS_OK,
      "submit receipt borrowed retry failed");
  expect(
      borrowed.journal_sequence == sizing.journal_sequence &&
          borrowed.canonical_effect.required == borrowed_effect.size() &&
          borrowed.canonical_effect.written == borrowed_effect.size(),
      "submit receipt borrowed retry fields mismatch");

  std::vector<std::uint8_t> copied_effect(borrowed_effect.size());
  delta_submit_receipt_v1_t copied{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {copied_effect.data(), copied_effect.size(), 77U, 88U},
  };
  expect(
      delta_runtime_submit_receipt_copy_v1(handle, view(command), &copied) == DELTA_STATUS_OK,
      "submit receipt copy replay failed");
  expect(
      copied.journal_sequence == borrowed.journal_sequence && copied_effect == borrowed_effect,
      "submit receipt replay changed the native sequence or canonical effect");

  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "submit-receipt runtime release failed");
  expect(delta_runtime_open(&open_options, &handle) == DELTA_STATUS_OK && handle != nullptr,
         "submit-receipt runtime reopen failed");
  std::vector<std::uint8_t> recovered_effect(borrowed_effect.size());
  delta_submit_receipt_v1_t recovered{
      DELTA_SUBMIT_RECEIPT_V1_SIZE,
      0U,
      99U,
      {recovered_effect.data(), recovered_effect.size(), 77U, 88U},
  };
  expect(
      delta_runtime_submit_receipt_copy_v1(handle, view(command), &recovered) == DELTA_STATUS_OK,
      "recovered submit receipt replay failed");
  expect(
      recovered.journal_sequence == borrowed.journal_sequence &&
          recovered_effect == borrowed_effect,
      "recovered submit receipt changed the native sequence or canonical effect");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "recovered submit-receipt runtime release failed");
}

template <typename Operation>
void expect_invalid_argument(Operation operation, std::string_view message) {
  try {
    operation();
  } catch (const std::invalid_argument&) {
    return;
  }
  fail(std::string(message));
}

void test_vote_codec_canonical_policy() {
  expect(
      delta::runtime::max_vote_receipt_v1_bytes +
              delta::runtime::vote_transport_metadata_v1_bytes ==
          delta::runtime::max_vote_response_logical_v1_bytes,
      "opaque receipt/transport bound arithmetic changed");
  expect(
      delta::runtime::vote_receipt_v1_encoded_size(
          delta::runtime::max_vote_frame_v1_bytes,
          content_id('a'),
          std::string(delta::runtime::max_vote_policy_v1_text_bytes, 'x')) <=
          delta::runtime::max_vote_receipt_v1_bytes,
      "maximum vote frame cannot produce a transportable receipt");
  expect_invalid_argument(
      [&] {
        static_cast<void>(delta::runtime::vote_receipt_v1_encoded_size(
            delta::runtime::max_vote_frame_v1_bytes + 1U,
            content_id('a'),
            "context"));
      },
      "oversized vote frame escaped the shared transport bound");

  const auto policy = round_config_vote_policy();
  const auto encoded = delta::runtime::encode_vote_policy_v1(policy);
  const auto decoded = delta::runtime::parse_vote_policy_v1(encoded);
  expect(
      delta::runtime::encode_vote_policy_v1(decoded) == encoded,
      "opaque vote policy did not round-trip canonically");
  expect(
      decoded.configured_abort_reason == policy.configured_abort_reason,
      "opaque vote policy lost the configured abort reason");

  auto nonzero_header_reserved = encoded;
  nonzero_header_reserved[15] = std::byte{1U};
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::parse_vote_policy_v1(nonzero_header_reserved)); },
      "nonzero opaque policy reserved byte was accepted");

  auto trailing = encoded;
  trailing.push_back(std::byte{0U});
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::parse_vote_policy_v1(trailing)); },
      "opaque policy trailing byte was accepted");

  delta::core::canonical::Bytes oversized_policy(
      delta::runtime::max_vote_policy_v1_bytes + 1U, std::byte{0U});
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::parse_vote_policy_v1(oversized_policy)); },
      "oversized policy was parsed before its aggregate byte bound");

  const auto encoded_text_size = [](std::string_view value) { return 4U + value.size(); };
  const auto write_u32 = [](
                             delta::core::canonical::Bytes& destination,
                             std::size_t offset,
                             std::uint32_t value) {
    for (std::size_t index = 0U; index < sizeof(value); ++index) {
      const auto shift = static_cast<unsigned>((sizeof(value) - index - 1U) * 8U);
      destination[offset + index] = static_cast<std::byte>((value >> shift) & 0xffU);
    }
  };
  const auto validator_count_offset =
      16U + encoded_text_size(policy.local_validator_id) +
      encoded_text_size(policy.validator_epoch_id);
  delta::core::canonical::Bytes truncated_validators(
      encoded.begin(),
      encoded.begin() + static_cast<std::ptrdiff_t>(validator_count_offset + 4U));
  write_u32(
      truncated_validators,
      validator_count_offset,
      static_cast<std::uint32_t>(delta::core::consensus::max_vote_validator_count));
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::parse_vote_policy_v1(truncated_validators)); },
      "truncated validator aggregate allocated from an unbacked count");

  auto candidate_count_offset = encoded.size() - 4U;
  for (const auto& candidate : policy.candidates) {
    candidate_count_offset -= 4U;  // action
    candidate_count_offset -= encoded_text_size(candidate.body_hash);
    candidate_count_offset -= encoded_text_size(candidate.context_id);
    candidate_count_offset -= 2U * sizeof(std::uint64_t);
    const std::string* parents[]{
        &candidate.parents.round_config_id,
        &candidate.parents.parent_checkpoint_id,
        &candidate.parents.input_set_certificate_id,
        &candidate.parents.seed_transcript_id,
        &candidate.parents.norm_evidence_id,
        &candidate.parents.eligibility_certificate_id,
        &candidate.parents.aggregation_plan_certificate_id,
        &candidate.parents.parameter_matrix_root,
        &candidate.parents.aggregate_root_certificate_id,
        &candidate.parents.apply_profile_id,
        &candidate.parents.apply_candidate_id,
        &candidate.parents.last_finalized_certificate_id,
        &candidate.parents.domain_id,
        &candidate.parents.shard_id,
        &candidate.parents.reason_code,
    };
    for (const auto* parent : parents) {
      candidate_count_offset -= encoded_text_size(*parent);
    }
  }
  delta::core::canonical::Bytes truncated_candidates(
      encoded.begin(),
      encoded.begin() + static_cast<std::ptrdiff_t>(candidate_count_offset + 4U));
  write_u32(
      truncated_candidates,
      candidate_count_offset,
      static_cast<std::uint32_t>(delta::core::consensus::max_vote_candidate_count));
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::parse_vote_policy_v1(truncated_candidates)); },
      "truncated candidate aggregate allocated from an unbacked count");

  auto unsorted = policy;
  std::swap(unsorted.validator_ids[0], unsorted.validator_ids[1]);
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::encode_vote_policy_v1(unsorted)); },
      "unsorted validator set was encoded as a canonical policy");

  auto duplicate_context = policy;
  auto second = duplicate_context.candidates.front();
  ++second.view;
  duplicate_context.candidates.push_back(std::move(second));
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::encode_vote_policy_v1(duplicate_context)); },
      "duplicate candidate context was encoded as a canonical policy");

  auto invalid_abort_reason = policy;
  invalid_abort_reason.configured_abort_reason = "NO_ABORT";
  expect_invalid_argument(
      [&] { static_cast<void>(delta::runtime::encode_vote_policy_v1(invalid_abort_reason)); },
      "invalid configured abort reason was encoded as a canonical policy");
}

struct VoteCallResult {
  std::vector<std::uint8_t> encoded;
  delta::runtime::DecodedVoteReceiptV1 decoded;
};

[[nodiscard]] VoteCallResult record_vote(
    delta_runtime_t* runtime,
    const std::vector<std::uint8_t>& vote,
    bool copy_path) {
  delta_vote_receipt_v1_t sizing{
      DELTA_VOTE_RECEIPT_V1_SIZE,
      0U,
      {nullptr, 0U, 99U, 99U},
  };
  const auto first = copy_path
                         ? delta_runtime_record_vote_copy_v1(runtime, view(vote), &sizing)
                         : delta_runtime_record_vote_borrowed_v1(runtime, view(vote), &sizing);
  expect(first == DELTA_STATUS_BUFFER_TOO_SMALL, "vote receipt sizing did not request retry");
  expect(
      sizing.canonical_receipt.required > 0U && sizing.canonical_receipt.written == 0U,
      "vote receipt sizing exposed partial bytes");
  std::vector<std::uint8_t> output(sizing.canonical_receipt.required);
  delta_vote_receipt_v1_t receipt{
      DELTA_VOTE_RECEIPT_V1_SIZE,
      0U,
      {output.data(), output.size(), 0U, 0U},
  };
  const auto second = copy_path
                          ? delta_runtime_record_vote_copy_v1(runtime, view(vote), &receipt)
                          : delta_runtime_record_vote_borrowed_v1(runtime, view(vote), &receipt);
  expect(second == DELTA_STATUS_OK, "vote receipt capacity retry failed");
  expect(
      receipt.canonical_receipt.required == output.size() &&
          receipt.canonical_receipt.written == output.size(),
      "vote receipt capacity retry size fields mismatch");
  auto decoded = delta::runtime::parse_vote_receipt_v1(bytes(output));
  return VoteCallResult{std::move(output), std::move(decoded)};
}

[[nodiscard]] delta_status_t record_vote_status(
    delta_runtime_t* runtime,
    const std::vector<std::uint8_t>& vote) {
  std::vector<std::uint8_t> output(64U * 1024U);
  delta_vote_receipt_v1_t receipt{
      DELTA_VOTE_RECEIPT_V1_SIZE,
      0U,
      {output.data(), output.size(), 77U, 88U},
  };
  const auto status = delta_runtime_record_vote_borrowed_v1(runtime, view(vote), &receipt);
  expect(receipt.canonical_receipt.written == 0U || status == DELTA_STATUS_OK,
         "rejected vote exposed partial receipt bytes");
  return status;
}

void test_opaque_vote_abi_and_status_mapping() {
  expect(sizeof(delta_vote_receipt_v1_t) == DELTA_VOTE_RECEIPT_V1_SIZE,
         "opaque vote receipt ABI size changed");
  expect(
      (DELTA_ABI_FEATURE_BITS & DELTA_ABI_FEATURE_RECORD_VOTE_V1) != 0U,
      "record-vote feature bit is absent");
  const auto initial = golden(5U);
  const auto vote = round_config_vote_bytes();
  const auto policy = delta::runtime::encode_vote_policy_v1(round_config_vote_policy());
  const auto directory = fresh_directory("opaque-vote-borrowed").string();
  auto open_options = options(directory, initial);
  delta_runtime_t* handle = nullptr;
  expect(
      delta_runtime_open_with_vote_policy_v1(&open_options, view(policy), &handle) ==
              DELTA_STATUS_OK &&
          handle != nullptr,
      "opaque vote-policy open failed");

  struct ReceiptCanary {
    delta_vote_receipt_v1_t receipt;
    std::array<std::uint8_t, 16> guard;
  } undersized{};
  std::memset(&undersized, 0x5a, sizeof(undersized));
  undersized.receipt.struct_size = DELTA_VOTE_RECEIPT_V1_SIZE - 1U;
  const auto undersized_before = undersized;
  expect(
      delta_runtime_record_vote_borrowed_v1(handle, view(vote), &undersized.receipt) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "undersized vote receipt was accepted");
  expect(
      std::memcmp(&undersized, &undersized_before, sizeof(undersized)) == 0,
      "undersized vote receipt or adjacent canary was modified");

  std::array<std::uint8_t, 8> invalid_storage{};
  delta_vote_receipt_v1_t nonzero_reserved{
      DELTA_VOTE_RECEIPT_V1_SIZE,
      1U,
      {invalid_storage.data(), invalid_storage.size(), 77U, 88U},
  };
  const auto reserved_before = nonzero_reserved;
  expect(
      delta_runtime_record_vote_borrowed_v1(handle, view(vote), &nonzero_reserved) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "nonzero receipt reserved field was accepted");
  expect(
      std::memcmp(&nonzero_reserved, &reserved_before, sizeof(nonzero_reserved)) == 0,
      "invalid receipt was reset before exact shape validation");

  std::array<std::uint8_t, 1> invalid_vote_storage{};
  delta_vote_receipt_v1_t invalid_input_receipt{
      DELTA_VOTE_RECEIPT_V1_SIZE,
      0U,
      {invalid_vote_storage.data(), invalid_vote_storage.size(), 77U, 88U},
  };
  const auto expect_invalid_vote_clears_receipt = [&](delta_bytes_view_t invalid_vote) {
    for (const bool copy_path : {false, true}) {
      invalid_input_receipt.canonical_receipt.required = 77U;
      invalid_input_receipt.canonical_receipt.written = 88U;
      const auto status = copy_path
                              ? delta_runtime_record_vote_copy_v1(
                                    handle, invalid_vote, &invalid_input_receipt)
                              : delta_runtime_record_vote_borrowed_v1(
                                    handle, invalid_vote, &invalid_input_receipt);
      expect(status == DELTA_STATUS_INVALID_ARGUMENT,
             "invalid vote view did not return INVALID_ARGUMENT");
      expect(
          invalid_input_receipt.canonical_receipt.required == 0U &&
              invalid_input_receipt.canonical_receipt.written == 0U,
          "valid receipt metadata was not cleared for invalid vote view");
    }
  };
  expect_invalid_vote_clears_receipt({nullptr, 1U});
  expect_invalid_vote_clears_receipt(
      {invalid_vote_storage.data(), delta::runtime::max_vote_frame_v1_bytes + 1U});

  auto wrong_binding = delta::core::protocol::parse_vote(bytes(vote));
  wrong_binding.kind = "ISC";
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(wrong_binding))) ==
          DELTA_STATUS_TRANSITION_REJECTED,
      "per-vote action selected a different binding from the startup round contract");

  const auto accepted = record_vote(handle, vote, false);
  expect(!accepted.decoded.replay, "receipt sizing call mutated the vote journal");
  expect(
      accepted.decoded.journal_sequence == 1U &&
          accepted.decoded.action == delta::core::consensus::VoteAction::round_config &&
          accepted.decoded.formal_action_id == "ACT-CONFIG-VOTE" &&
          accepted.decoded.context_id ==
              delta::core::protocol::parse_vote(bytes(vote)).context_id &&
          accepted.decoded.vote_id ==
              delta::core::canonical::content_id(
                  delta::core::canonical::Type::vote, bytes(vote)) &&
          accepted.decoded.frame.size() == vote.size() &&
          std::equal(accepted.decoded.frame.begin(), accepted.decoded.frame.end(), bytes(vote).begin()),
      "native-authored opaque vote receipt fields mismatch");

  const auto exact_replay = record_vote(handle, vote, true);
  expect(
      !exact_replay.decoded.replay && exact_replay.decoded.journal_sequence == 1U &&
          exact_replay.decoded.vote_id == accepted.decoded.vote_id &&
          exact_replay.decoded.frame == accepted.decoded.frame &&
          exact_replay.encoded == accepted.encoded,
      "copy-path exact replay changed canonical durable receipt bytes");

  const auto parsed_vote = delta::core::protocol::parse_vote(bytes(vote));
  auto conflict = parsed_vote;
  conflict.signature_id = content_id('a');
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(conflict))) ==
          DELTA_STATUS_CONFLICT,
      "same-context byte conflict did not map to CONFLICT");
  conflict = parsed_vote;
  conflict.body_hash = content_id('f');
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(conflict))) ==
          DELTA_STATUS_CONFLICT,
      "same-context body conflict did not map to CONFLICT");
  conflict = parsed_vote;
  conflict.kind = "ISC";
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(conflict))) ==
          DELTA_STATUS_CONFLICT,
      "same-context closed-kind conflict did not map to CONFLICT");
  conflict = parsed_vote;
  conflict.kind = "FREE_FORM";
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(conflict))) ==
          DELTA_STATUS_CONFLICT,
      "same-context unknown-kind conflict lost stable key precedence");

  auto outside_contract = parsed_vote;
  outside_contract.context_id = "ROUND_CONFIG:round-003-fixture:1:9";
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(outside_contract))) ==
          DELTA_STATUS_TRANSITION_REJECTED,
      "context outside the decoded immutable candidate set was admitted");
  auto unknown_action = outside_contract;
  unknown_action.context_id = "UNKNOWN:round-003-fixture:1:0";
  unknown_action.kind = "UNKNOWN";
  expect(
      record_vote_status(handle, octets(delta::core::protocol::encode(unknown_action))) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "closed vote action escaped INVALID_ARGUMENT mapping");
  expect(
      record_vote_status(handle, std::vector<std::uint8_t>{0U, 1U, 2U}) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "malformed canonical vote escaped INVALID_ARGUMENT mapping");
  const auto after_rejections = record_vote(handle, vote, false);
  expect(
      !after_rejections.decoded.replay && after_rejections.decoded.journal_sequence == 1U &&
          after_rejections.encoded == accepted.encoded,
      "rejected/conflicting vote changed the canonical replay receipt");

  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "vote runtime release failed");
  expect(
      delta_runtime_open_with_vote_policy_v1(&open_options, view(policy), &handle) ==
              DELTA_STATUS_OK &&
          handle != nullptr,
      "vote runtime recovery open failed");
  const auto recovered = record_vote(handle, vote, false);
  expect(
      !recovered.decoded.replay && recovered.decoded.journal_sequence == 1U &&
          recovered.decoded.vote_id == accepted.decoded.vote_id &&
          recovered.encoded == accepted.encoded,
      "recovered vote replay changed canonical durable receipt bytes");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK, "recovered vote runtime release failed");

  const auto copy_directory = fresh_directory("opaque-vote-copy").string();
  auto copy_options = options(copy_directory, initial);
  expect(
      delta_runtime_open_with_vote_policy_v1(&copy_options, view(policy), &handle) ==
              DELTA_STATUS_OK &&
          handle != nullptr,
      "copy-path vote runtime open failed");
  const auto copied = record_vote(handle, vote, true);
  expect(copied.encoded == accepted.encoded, "borrowed/copy vote receipts differ");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK, "copy-path vote runtime release failed");

  auto malformed_policy = policy;
  malformed_policy[15] = std::byte{1U};
  const auto malformed_directory = fresh_directory("opaque-vote-malformed").string();
  auto malformed_options = options(malformed_directory, initial);
  handle = reinterpret_cast<delta_runtime_t*>(UINTPTR_MAX);
  expect(
      delta_runtime_open_with_vote_policy_v1(
          &malformed_options, view(malformed_policy), &handle) == DELTA_STATUS_INVALID_ARGUMENT &&
          handle == nullptr,
      "malformed opaque policy did not fail closed before open");
}

#if defined(DELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH)
[[nodiscard]] std::vector<std::uint8_t> retry_fixedpoint_shard(
    const std::vector<std::uint8_t>& envelope,
    bool copy_path) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  const auto first = copy_path
                         ? delta_fixedpoint_shard_validate_copy(view(envelope), &sizing)
                         : delta_fixedpoint_shard_validate_borrowed(view(envelope), &sizing);
  expect(first == DELTA_STATUS_BUFFER_TOO_SMALL, "fixed-point sizing did not request retry");
  expect(
      sizing.required == envelope.size() && sizing.written == 0U,
      "fixed-point sizing exposed partial bytes");
  std::vector<std::uint8_t> output(sizing.required);
  delta_output_buffer_t destination{output.data(), output.size(), 0U, 0U};
  const auto second = copy_path
                          ? delta_fixedpoint_shard_validate_copy(view(envelope), &destination)
                          : delta_fixedpoint_shard_validate_borrowed(view(envelope), &destination);
  expect(second == DELTA_STATUS_OK, "fixed-point retry failed");
  expect(destination.required == output.size() && destination.written == output.size(),
         "fixed-point retry size fields mismatch");
  return output;
}

void test_fixedpoint_native_boundary() {
  const auto envelope = fixedpoint_golden();
  expect(retry_fixedpoint_shard(envelope, false) == envelope,
         "borrowed fixed-point boundary changed bytes");
  expect(retry_fixedpoint_shard(envelope, true) == envelope,
         "copy fixed-point boundary changed bytes");

  auto malformed = envelope;
  malformed.back() ^= 1U;
  std::vector<std::uint8_t> sentinel(8U, 0x5aU);
  delta_output_buffer_t rejected{sentinel.data(), sentinel.size(), 99U, 99U};
  expect(
      delta_fixedpoint_shard_validate_borrowed(view(malformed), &rejected) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "corrupt fixed-point shard escaped stable status mapping");
  expect(rejected.required == 0U && rejected.written == 0U,
         "rejected fixed-point shard exposed partial output metadata");
}
#endif

}  // namespace

int main() {
  try {
    test_frozen_descriptor_and_status_taxonomy();
    test_startup_mismatch_matrix();
    test_open_submit_snapshot_release_and_memory_rules();
    test_versioned_submit_receipt_abi();
    test_vote_codec_canonical_policy();
    test_opaque_vote_abi_and_status_mapping();
#if defined(DELTA_FIXEDPOINT_GOLDEN_FIXTURE_PATH)
    test_fixedpoint_native_boundary();
#endif
  } catch (const std::exception& error) {
    std::cerr << "delta_ffi ABI test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_ffi ABI tests passed\n";
  return 0;
}
