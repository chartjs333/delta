#include <delta_abi.h>

#include <delta/qlora/context.hpp>

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

[[nodiscard]] std::string id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

void test_bounded_context_id_parity() {
  static_assert(sizeof(delta_qlora_context_t) == DELTA_QLORA_CONTEXT_SIZE);
  const auto native = delta::qlora::Context{id('1'), id('2'), id('3'), id('4'), id('5'), id('6')};
  const auto context = delta_qlora_context_t{
      DELTA_QLORA_CONTEXT_SIZE,
      0U,
      view(native.adapter_parameter_schema_id),
      view(native.base_model_manifest_id),
      view(native.parent_adapter_id),
      view(native.quantized_base_profile_id),
      view(native.tokenizer_hash),
      view(native.training_mode_id),
  };
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  expect(
      delta_qlora_context_id(&context, &sizing) == DELTA_STATUS_BUFFER_TOO_SMALL &&
          sizing.required == 71U,
      "QLoRA ABI did not negotiate its bounded output");
  std::vector<std::uint8_t> output(sizing.required);
  delta_output_buffer_t target{output.data(), output.size(), 0U, 0U};
  expect(
      delta_qlora_context_id(&context, &target) == DELTA_STATUS_OK &&
          target.written == target.required,
      "QLoRA ABI context ID failed");
  const std::string actual(output.begin(), output.end());
  expect(actual == delta::qlora::content_id(native), "C ABI and native QLoRA IDs differ");

  auto malformed = context;
  malformed.base_model_manifest_id.size = 72U;
  expect(
      delta_qlora_context_id(&malformed, &target) == DELTA_STATUS_INVALID_ARGUMENT,
      "QLoRA ABI accepted an overlong content ID");
}

}  // namespace

int main() {
  try {
    test_bounded_context_id_parity();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
