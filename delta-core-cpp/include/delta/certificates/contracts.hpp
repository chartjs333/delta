#pragma once

#include <delta/core/canonical.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::certificates {

inline constexpr std::string_view formal_semantics_id =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
inline constexpr std::string_view schema_version = "1.0.0";
inline constexpr std::size_t max_contract_bytes = 4U * 1024U * 1024U;
inline constexpr std::size_t max_certificate_entries = 100'000U;

enum class ErrorCode {
  identifier_invalid,
  context_mismatch,
  parent_mismatch,
  order_invalid,
  duplicate_entry,
  quorum_invalid,
  input_set_not_certified,
  membership_mutation,
  arithmetic_invalid,
  accumulator_unsafe,
  coverage_incomplete,
  coverage_duplicate,
  mixed_view_shard,
  apply_conflict,
  apply_qc_required,
  stale_timer,
  limit_exceeded,
};

class CertificateError final : public std::runtime_error {
 public:
  CertificateError(ErrorCode code, std::string message);
  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Context {
  std::string arithmetic_profile_id;
  std::uint64_t height;
  std::string parameter_schema_id;
  std::string round_config_id;
  std::string round_id;
  std::string validator_epoch_id;
  std::uint64_t view;

  bool operator==(const Context&) const = default;
};

struct Rational {
  std::int64_t numerator;
  std::uint64_t denominator;

  bool operator==(const Rational&) const = default;
};

struct InputTuple {
  std::string availability_certificate_id;
  std::string commitment_id;
  std::string domain_id;
  std::string ticket_id;

  bool operator==(const InputTuple&) const = default;
};

struct InputSetCertificate {
  Context context;
  std::string input_root;
  std::uint32_t quorum_threshold;
  std::vector<std::string> signer_ids;
  std::vector<InputTuple> tuples;

  bool operator==(const InputSetCertificate&) const = default;
};

struct SeedTranscript {
  Context context;
  std::string input_set_certificate_id;
  std::string seed_id;
  std::string seed_profile_id;
  std::vector<std::string> share_ids;

  bool operator==(const SeedTranscript&) const = default;
};

struct NormEntry {
  std::uint64_t scale_denominator;
  std::string squared_norm;
  std::string ticket_id;

  bool operator==(const NormEntry&) const = default;
};

struct NormEvidence {
  Context context;
  std::vector<NormEntry> entries;
  std::string input_set_certificate_id;
  std::string norm_root;

  bool operator==(const NormEvidence&) const = default;
};

struct EligibilityEntry {
  bool accepted;
  std::string domain_id;
  Rational gamma;
  std::string reason_code;
  std::string ticket_id;

  bool operator==(const EligibilityEntry&) const = default;
};

struct EligibilityCertificate {
  Context context;
  std::vector<EligibilityEntry> entries;
  std::string input_set_certificate_id;
  std::string norm_evidence_id;
  std::uint32_t quorum_threshold;
  std::string robust_profile_id;
  std::vector<std::string> signer_ids;

  bool operator==(const EligibilityCertificate&) const = default;
};

struct BucketAssignment {
  std::string bucket_id;
  std::string ticket_id;

  bool operator==(const BucketAssignment&) const = default;
};

struct Weight {
  Rational alpha;
  std::string ticket_id;

  bool operator==(const Weight&) const = default;
};

struct AggregationPlanCertificate {
  Context context;
  std::string accumulator_proof_id;
  std::vector<BucketAssignment> bucket_assignments;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::uint32_t iteration_count;
  std::uint32_t quorum_threshold;
  std::string seed_transcript_id;
  std::vector<std::string> signer_ids;
  std::string transcript_root;
  std::vector<Weight> weights;

  bool operator==(const AggregationPlanCertificate&) const = default;
};

struct ShardKey {
  std::string domain_id;
  std::string shard_id;

  bool operator==(const ShardKey&) const = default;
  bool operator<(const ShardKey& other) const noexcept;
};

struct ParameterShardQc {
  Context context;
  std::string aggregation_plan_certificate_id;
  std::uint64_t denominator;
  std::string domain_id;
  std::string eligibility_certificate_id;
  std::vector<std::string> input_leaf_ids;
  std::string input_set_certificate_id;
  std::uint32_t quorum_threshold;
  std::vector<std::string> result_numerators;
  std::string shard_id;
  std::vector<std::string> signer_ids;

  bool operator==(const ParameterShardQc&) const = default;
};

struct RootLeaf {
  std::string domain_id;
  std::string parameter_shard_qc_id;
  std::string shard_id;

  bool operator==(const RootLeaf&) const = default;
};

struct AggregateRootQc {
  Context context;
  std::string aggregation_plan_certificate_id;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::vector<RootLeaf> leaves;
  std::string merkle_root;
  std::uint32_t quorum_threshold;
  std::vector<ShardKey> required_keys;
  std::vector<std::string> signer_ids;

  bool operator==(const AggregateRootQc&) const = default;
};

struct DomainWeight {
  std::string domain_id;
  Rational pi;

  bool operator==(const DomainWeight&) const = default;
};

struct ApplyArithmeticProfile {
  std::string accumulator_proof_id;
  std::vector<DomainWeight> domain_weights;
  Rational learning_rate;
  Rational momentum;
  bool nesterov;
  std::string rounding;
  Rational weight_decay;

  bool operator==(const ApplyArithmeticProfile&) const = default;
};

struct ApplyCandidate {
  Context context;
  std::string aggregate_root_qc_id;
  std::string apply_arithmetic_profile_id;
  std::string next_model_hash;
  std::vector<std::string> next_model_values;
  std::string next_optimizer_hash;
  std::vector<std::string> next_optimizer_values;
  std::string parent_checkpoint_id;
  std::string parent_optimizer_hash;

  bool operator==(const ApplyCandidate&) const = default;
};

struct ApplyQc {
  Context context;
  std::string aggregate_root_qc_id;
  std::string apply_arithmetic_profile_id;
  std::string apply_candidate_id;
  std::string next_model_hash;
  std::string next_optimizer_hash;
  std::string parent_checkpoint_id;
  std::uint32_t quorum_threshold;
  std::vector<std::string> signer_ids;

  bool operator==(const ApplyQc&) const = default;
};

struct CurrentPointerCommand {
  Context context;
  std::string apply_qc_id;
  std::string expected_parent_checkpoint_id;
  std::string next_checkpoint_id;
  std::string next_optimizer_hash;

  bool operator==(const CurrentPointerCommand&) const = default;
};

[[nodiscard]] bool is_content_id(std::string_view value) noexcept;
[[nodiscard]] bool is_label(std::string_view value) noexcept;
void validate_context(const Context& actual, const Context& expected);
void validate_rational(const Rational& value, bool non_negative = false);

[[nodiscard]] core::canonical::Bytes canonical_json(const InputSetCertificate& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const SeedTranscript& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const NormEvidence& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const EligibilityCertificate& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const AggregationPlanCertificate& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const ParameterShardQc& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const AggregateRootQc& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const ApplyArithmeticProfile& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const ApplyCandidate& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const ApplyQc& value);
[[nodiscard]] core::canonical::Bytes canonical_json(const CurrentPointerCommand& value);

[[nodiscard]] std::string aggregate_merkle_root(const std::vector<RootLeaf>& leaves);

[[nodiscard]] std::string content_id(const InputSetCertificate& value);
[[nodiscard]] std::string content_id(const SeedTranscript& value);
[[nodiscard]] std::string content_id(const NormEvidence& value);
[[nodiscard]] std::string content_id(const EligibilityCertificate& value);
[[nodiscard]] std::string content_id(const AggregationPlanCertificate& value);
[[nodiscard]] std::string content_id(const ParameterShardQc& value);
[[nodiscard]] std::string content_id(const AggregateRootQc& value);
[[nodiscard]] std::string content_id(const ApplyArithmeticProfile& value);
[[nodiscard]] std::string content_id(const ApplyCandidate& value);
[[nodiscard]] std::string content_id(const ApplyQc& value);
[[nodiscard]] std::string content_id(const CurrentPointerCommand& value);

}  // namespace delta::certificates
