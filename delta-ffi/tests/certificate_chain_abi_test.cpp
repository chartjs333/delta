#include <delta_abi.h>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

struct CorpusCase final {
  std::vector<std::uint8_t> bundle;
  bool c_abi_accepted;
  std::string checkpoint_wal_sha256;
  std::string effect_set_id;
  std::string execution_plan_id;
  bool accepted;
  std::string final_checkpoint_id;
  std::string name;
  bool native_accepted;
  std::string parent_checkpoint_id;
  std::string policy_id;
  bool python_accepted;
  std::string runtime_state_id;
  std::string runtime_wal_sha256;
};

void expect(bool condition, const char* message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

[[nodiscard]] std::uint8_t nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  return static_cast<std::uint8_t>(10 + value - 'a');
}

[[nodiscard]] std::vector<std::uint8_t> decode_hex(std::string_view value) {
  expect(value.size() % 2U == 0U, "corpus hex length is odd");
  std::vector<std::uint8_t> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>((nibble(value[index]) << 4U) |
                                               nibble(value[index + 1U])));
  }
  return result;
}

[[nodiscard]] std::vector<CorpusCase> load_corpus() {
  std::ifstream input(DELTA_CERTIFICATE_CHAIN_CORPUS_PATH, std::ios::binary);
  expect(input.good(), "cannot open native chain conformance corpus");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX(\{"bundle_bytes_hex":"([0-9a-f]+)","c_abi":"(ACCEPT|REJECT)","checkpoint_wal_sha256":"([0-9a-f]{64})","effect_set_id":"(sha256:[0-9a-f]{64})","execution_plan_id":"(sha256:[0-9a-f]{64})","expected":"(ACCEPT|REJECT)","final_checkpoint_id":"(sha256:[0-9a-f]{64})","name":"([a-z0-9-]+)","native_chain_verifier":"(ACCEPT|REJECT)","parent_checkpoint_id":"(sha256:[0-9a-f]{64})","policy_id":"(sha256:[0-9a-f]{64})","python_admission":"(ACCEPT|REJECT)","runtime_state_id":"(sha256:[0-9a-f]{64})","runtime_wal_sha256":"([0-9a-f]{64})"\})REGEX");
  std::vector<CorpusCase> result;
  for (auto iterator = std::sregex_iterator(document.begin(), document.end(), pattern);
       iterator != std::sregex_iterator();
       ++iterator) {
    const auto& match = *iterator;
    result.push_back({
        decode_hex(match[1].str()),
        match[2].str() == "ACCEPT",
        match[3].str(),
        match[4].str(),
        match[5].str(),
        match[6].str() == "ACCEPT",
        match[7].str(),
        match[8].str(),
        match[9].str() == "ACCEPT",
        match[10].str(),
        match[11].str(),
        match[12].str() == "ACCEPT",
        match[13].str(),
        match[14].str(),
    });
  }
  expect(result.size() >= 12U, "native chain conformance corpus is incomplete");
  return result;
}

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {
      reinterpret_cast<const std::uint8_t*>(value.data()),
      value.size(),
  };
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& value) {
  return {value.data(), value.size()};
}

using Verify = delta_status_t (*)(
    const delta_certificate_chain_context_t*,
    delta_bytes_view_t,
    delta_output_buffer_t*);

struct Invocation final {
  delta_status_t status;
  std::string receipt;
};

[[nodiscard]] Invocation invoke(
    Verify function,
    const delta_certificate_chain_context_t& context,
    const CorpusCase& test_case) {
  delta_output_buffer_t sizing{};
  const auto first = function(&context, view(test_case.bundle), &sizing);
  if (first != DELTA_STATUS_BUFFER_TOO_SMALL) {
    expect(sizing.required == 0U && sizing.written == 0U, "rejection exposed partial output");
    return {first, {}};
  }
  expect(sizing.required > 0U && sizing.written == 0U, "receipt size negotiation failed");
  std::vector<std::uint8_t> bytes(sizing.required);
  delta_output_buffer_t output{bytes.data(), bytes.size(), 0U, 0U};
  const auto second = function(&context, view(test_case.bundle), &output);
  expect(
      second == DELTA_STATUS_OK && output.required == bytes.size() &&
          output.written == bytes.size(),
      "native chain receipt retry failed");
  return {second, {reinterpret_cast<const char*>(bytes.data()), bytes.size()}};
}

[[nodiscard]] delta_certificate_chain_context_t context(const CorpusCase& test_case) {
  const auto formal = std::string_view{DELTA_FORMAL_SEMANTICS_ID};
  const auto build = std::string_view{DELTA_BUILD_ID};
  return {
      DELTA_CERTIFICATE_CHAIN_CONTEXT_SIZE,
      0U,
      view(formal),
      view(build),
      view(test_case.execution_plan_id),
      view(test_case.policy_id),
      view(test_case.parent_checkpoint_id),
      view(test_case.final_checkpoint_id),
      view(test_case.runtime_state_id),
      view(test_case.effect_set_id),
      view(test_case.runtime_wal_sha256),
      view(test_case.checkpoint_wal_sha256),
  };
}

void run() {
  const auto corpus = load_corpus();
  std::size_t accepted = 0U;
  std::size_t rejected = 0U;
  for (const auto& test_case : corpus) {
    expect(
        test_case.accepted == test_case.c_abi_accepted &&
            test_case.accepted == test_case.native_accepted &&
            test_case.accepted == test_case.python_accepted,
        "cross-verifier corpus expectations diverge");
    const auto expected_status =
        test_case.accepted ? DELTA_STATUS_OK : DELTA_STATUS_TRANSITION_REJECTED;
    const auto expected_context = context(test_case);
    const auto borrowed = invoke(
        delta_certificate_chain_verify_borrowed, expected_context, test_case);
    const auto copied = invoke(
        delta_certificate_chain_verify_copy, expected_context, test_case);
    expect(borrowed.status == expected_status, "borrowed native chain result differs from corpus");
    expect(copied.status == expected_status, "copy native chain result differs from corpus");
    expect(borrowed.receipt == copied.receipt, "borrowed/copy chain receipts differ");
    if (test_case.accepted) {
      ++accepted;
      expect(
          borrowed.receipt.find("\"status\":\"ACCEPT\"") != std::string::npos &&
              borrowed.receipt.find(test_case.execution_plan_id) != std::string::npos &&
              borrowed.receipt.find(test_case.final_checkpoint_id) != std::string::npos,
          "native receipt lacks the run binding");
    } else {
      ++rejected;
    }
  }
  expect(accepted == 1U && rejected + accepted == corpus.size(), "corpus decision counts differ");

  auto invalid = context(corpus.front());
  const std::string wrong_build = "sha256:" + std::string(64U, 'f');
  invalid.expected_native_build_id = view(wrong_build);
  delta_output_buffer_t output{};
  expect(
      delta_certificate_chain_verify_copy(&invalid, view(corpus.front().bundle), &output) ==
          DELTA_STATUS_BUILD_MISMATCH,
      "native chain ABI accepted the wrong build identity");

  invalid = context(corpus.front());
  invalid.struct_size = DELTA_CERTIFICATE_CHAIN_CONTEXT_SIZE - 1U;
  expect(
      delta_certificate_chain_verify_borrowed(&invalid, view(corpus.front().bundle), &output) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "native chain ABI accepted an incompatible context layout");

  invalid = context(corpus.front());
  const std::string wrong_formal = "sha256:" + std::string(64U, 'f');
  invalid.expected_formal_semantics_id = view(wrong_formal);
  expect(
      delta_certificate_chain_verify_copy(&invalid, view(corpus.front().bundle), &output) ==
          DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH,
      "native chain ABI accepted the wrong formal semantics identity");
}

}  // namespace

int main() {
  try {
    run();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
