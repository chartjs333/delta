#pragma once

#include <delta/certificates/verifier.hpp>

#include <cstdint>
#include <string>
#include <vector>

namespace delta::qlora {

inline constexpr std::size_t max_context_bytes = 4096U;

struct Context {
  std::string adapter_parameter_schema_id;
  std::string base_model_manifest_id;
  std::string parent_adapter_id;
  std::string quantized_base_profile_id;
  std::string tokenizer_hash;
  std::string training_mode_id;

  bool operator==(const Context&) const = default;
};

struct AdapterKey {
  std::string domain_id;
  std::string parameter_name;

  bool operator==(const AdapterKey&) const = default;
  bool operator<(const AdapterKey& other) const noexcept;
};

struct AdapterVector {
  AdapterKey key;
  std::int64_t coefficient;
  std::vector<std::int64_t> q_values;
  std::string ticket_id;
};

struct ReducedAdapterVector {
  AdapterKey key;
  std::vector<std::int64_t> numerators;
};

[[nodiscard]] std::string canonical_json(const Context& value);
[[nodiscard]] std::string content_id(const Context& value);
void validate_binding(
    const Context& value,
    const certificates::Context& certificate_context);
[[nodiscard]] certificates::ChainVerifier make_chain_verifier(
    const Context& value,
    certificates::Context certificate_context,
    certificates::ValidatorPolicy validators);
[[nodiscard]] std::vector<AdapterKey> required_adapter_keys(
    const std::vector<std::string>& ordered_domains,
    const std::vector<std::string>& ordered_parameters);
void validate_exact_coverage(
    const std::vector<AdapterKey>& required,
    const std::vector<AdapterVector>& contributions);
[[nodiscard]] std::vector<ReducedAdapterVector> reduce_adapter_vectors(
    const std::vector<AdapterKey>& required,
    const std::vector<AdapterVector>& contributions);
[[nodiscard]] std::vector<certificates::ShardKey> certificate_required_keys(
    const std::vector<AdapterKey>& required);

}  // namespace delta::qlora
