#include <delta/certificates/verifier.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace delta::core::consensus {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ConsensusError(code, message);
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

void require_id(std::string_view value) {
  require(!value.empty(), ErrorCode::identifier_invalid, "identifier is empty");
}

void require_content_id(std::string_view value) {
  constexpr std::string_view prefix = "sha256:";
  require(
      value.size() == prefix.size() + 64U && value.starts_with(prefix),
      ErrorCode::identifier_invalid,
      "content ID shape");
  for (const char digit : value.substr(prefix.size())) {
    require(
        (digit >= '0' && digit <= '9') || (digit >= 'a' && digit <= 'f'),
        ErrorCode::identifier_invalid,
        "content ID hexadecimal digit");
  }
}

void require_vote(const protocol::Vote& vote) {
  require_id(vote.validator_id);
  require_content_id(vote.validator_epoch_id);
  require_id(vote.kind);
  require_id(vote.round_id);
  require_id(vote.context_id);
  require_content_id(vote.body_hash);
  require_content_id(vote.signature_id);
  require(vote.durable_sequence > 0U, ErrorCode::vote_invalid, "durable vote sequence is zero");
}

[[nodiscard]] bool is_abort_request_reason(std::string_view reason) noexcept {
  return reason == "INCOMPLETE_INPUT" || reason == "UNSAFE_COEFFICIENTS";
}

void require_parent(
    std::string_view value,
    bool required,
    bool content_id,
    const char* message) {
  if (!required) {
    require(value.empty(), ErrorCode::vote_policy_invalid, message);
  } else if (content_id) {
    require_content_id(value);
  } else {
    require_id(value);
  }
}

void require_sorted_ids(const std::vector<std::string>& values, bool content_ids = true) {
  require(
      std::is_sorted(values.begin(), values.end()) &&
          std::adjacent_find(values.begin(), values.end()) == values.end(),
      ErrorCode::vote_policy_invalid,
      "vote authority set is not canonically ordered");
  for (const auto& value : values) {
    if (content_ids) {
      require_content_id(value);
    } else {
      require_id(value);
    }
  }
}

template <typename Value>
[[nodiscard]] bool contains(const std::vector<Value>& values, const Value& value) {
  return std::binary_search(values.begin(), values.end(), value);
}

template <typename Values, typename Identifier>
[[nodiscard]] const typename Values::value_type* find_by_id(
    const Values& values,
    std::string_view id,
    Identifier identifier) {
  for (const auto& value : values) {
    if (identifier(value) == id) {
      return &value;
    }
  }
  return nullptr;
}

template <typename Values, typename Identifier>
void require_ordered(const Values& values, Identifier identifier, const char* message) {
  std::string previous;
  bool first = true;
  for (const auto& value : values) {
    const auto current = identifier(value);
    require_content_id(current);
    require(first || previous < current, ErrorCode::vote_policy_invalid, message);
    previous = current;
    first = false;
  }
}

[[nodiscard]] std::string input_body_id(const VoteInputSetBody& value) {
  return vote_input_set_body_id(value);
}

[[nodiscard]] std::string input_qc_id(const certificates::InputSetCertificate& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string seed_id(const certificates::SeedTranscript& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string norm_id(const certificates::NormEvidence& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string ec_body_id(const VoteEligibilityBody& value) {
  return vote_eligibility_body_id(value);
}

[[nodiscard]] std::string ec_qc_id(const VoteFinalizedEligibility& value) {
  return certificates::content_id(value.certificate);
}

[[nodiscard]] std::string plan_body_id(const VoteAggregationPlanBody& value) {
  return vote_aggregation_plan_body_id(value);
}

[[nodiscard]] std::string plan_qc_id(
    const certificates::AggregationPlanCertificate& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string parameter_body_id(const VoteParameterBody& value) {
  return vote_parameter_body_id(value);
}

[[nodiscard]] std::string parameter_qc_id(
    const certificates::ParameterShardQc& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string root_body_id(const VoteAggregateRootBody& value) {
  return vote_aggregate_root_body_id(value);
}

[[nodiscard]] std::string root_qc_id(const certificates::AggregateRootQc& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string profile_id(
    const certificates::ApplyArithmeticProfile& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string apply_body_id(const certificates::ApplyCandidate& value) {
  return certificates::content_id(value);
}

[[nodiscard]] std::string apply_qc_id(const VoteFinalizedApply& value) {
  return certificates::content_id(value.certificate);
}

template <typename Artifacts, typename Identifier>
void require_subset(
    const std::vector<std::string>& ids,
    const Artifacts& artifacts,
    Identifier identifier,
    const char* message) {
  for (const auto& id : ids) {
    require(
        find_by_id(artifacts, id, identifier) != nullptr,
        ErrorCode::vote_policy_invalid,
        message);
  }
}

[[nodiscard]] bool phase_allows(VoteAction action, protocol::RoundPhase phase) noexcept {
  switch (action) {
    case VoteAction::round_config:
      return phase == protocol::RoundPhase::ticketing_open;
    case VoteAction::input_set:
      return phase == protocol::RoundPhase::available;
    case VoteAction::eligibility:
    case VoteAction::aggregation_plan:
    case VoteAction::parameter:
    case VoteAction::aggregate_root:
    case VoteAction::apply:
      return phase == protocol::RoundPhase::eligible;
    case VoteAction::view_change:
    case VoteAction::abort:
      return phase != protocol::RoundPhase::aggregated &&
             phase != protocol::RoundPhase::aborted;
  }
  return false;
}

void validate_candidate_shape(
    const VoteAdmissionPolicy& policy,
    const VoteCandidateBinding& candidate) {
  require_content_id(candidate.body_hash);
  require_id(candidate.context_id);
  const auto value = static_cast<std::uint32_t>(candidate.action);
  require(
      value >= static_cast<std::uint32_t>(VoteAction::round_config) &&
          value <= static_cast<std::uint32_t>(VoteAction::abort),
      ErrorCode::vote_policy_invalid,
      "candidate action is outside the closed vote vocabulary");
  const auto& parent = candidate.parents;
  require_parent(parent.round_config_id, true, true, "round-config parent is absent");
  require_parent(parent.parent_checkpoint_id, true, true, "parent checkpoint is absent");
  require(
      parent.round_config_id == policy.round_config_id,
      ErrorCode::vote_policy_invalid,
      "candidate does not bind the runtime round config");
  const bool ec = candidate.action == VoteAction::eligibility;
  const bool apc = candidate.action == VoteAction::aggregation_plan;
  const bool parameter = candidate.action == VoteAction::parameter;
  const bool root = candidate.action == VoteAction::aggregate_root;
  const bool apply = candidate.action == VoteAction::apply;
  const bool abort = candidate.action == VoteAction::abort;
  require_parent(
      parent.input_set_certificate_id,
      ec || apc || parameter || root,
      true,
      "input-set parent presence is invalid");
  require_parent(
      parent.seed_transcript_id,
      ec || apc || parameter || root,
      true,
      "seed parent presence is invalid");
  require_parent(
      parent.norm_evidence_id,
      ec || apc,
      true,
      "norm parent presence is invalid");
  require_parent(
      parent.eligibility_certificate_id,
      apc || parameter || root,
      true,
      "eligibility parent presence is invalid");
  require_parent(
      parent.aggregation_plan_certificate_id,
      parameter || root,
      true,
      "aggregation-plan parent presence is invalid");
  require_parent(
      parent.parameter_matrix_root,
      root,
      true,
      "parameter matrix presence is invalid");
  require_parent(
      parent.aggregate_root_certificate_id,
      apply,
      true,
      "aggregate-root parent presence is invalid");
  require_parent(parent.apply_profile_id, apply, true, "apply profile presence is invalid");
  require_parent(parent.apply_candidate_id, apply, true, "apply candidate presence is invalid");
  require_parent(
      parent.last_finalized_certificate_id,
      false,
      true,
      "synthetic last-finalized parent is forbidden");
  require_parent(parent.domain_id, parameter, false, "parameter domain presence is invalid");
  require_parent(parent.shard_id, parameter, false, "parameter shard presence is invalid");
  require_parent(parent.reason_code, abort, false, "abort reason presence is invalid");
  if (candidate.action == VoteAction::round_config) {
    require(
        candidate.body_hash == parent.round_config_id,
        ErrorCode::vote_policy_invalid,
        "round-config body differs from configured proposal");
  }
}

void validate_snapshot_sets(
    const VoteAdmissionPolicy& policy,
    const VoteAdmissionSnapshot& snapshot) {
  const auto config_set = [&](const std::vector<std::string>& ids) {
    require_sorted_ids(ids);
    require(
        std::all_of(ids.begin(), ids.end(), [&](const auto& id) {
          return id == policy.round_config_id;
        }),
        ErrorCode::vote_policy_invalid,
        "vote authority contains a foreign round config");
  };
  config_set(snapshot.proposed_round_config_ids);
  config_set(snapshot.finalized_round_config_ids);
  require_sorted_ids(snapshot.closed_input_set_ids);
  require_sorted_ids(snapshot.finalized_input_set_ids);
  require_sorted_ids(snapshot.finalized_eligibility_ids);
  require_sorted_ids(snapshot.finalized_aggregation_plan_ids);
  require_sorted_ids(snapshot.finalized_parameter_ids);
  require_sorted_ids(snapshot.finalized_aggregate_root_ids);
  require_sorted_ids(snapshot.finalized_apply_ids);
}

[[nodiscard]] std::uint32_t quorum_threshold(const VoteAdmissionPolicy& policy) {
  const auto f = (policy.validator_ids.size() - 1U) / 3U;
  return static_cast<std::uint32_t>(2U * f + 1U);
}

[[nodiscard]] certificates::InputSetCertificate as_input_certificate(
    const VoteInputSetBody& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::InputSetCertificate{
      body.context,
      body.input_root,
      quorum_threshold(policy),
      policy.validator_ids,
      body.tuples,
  };
}

[[nodiscard]] certificates::EligibilityCertificate as_eligibility_certificate(
    const VoteEligibilityBody& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::EligibilityCertificate{
      body.context,
      body.entries,
      body.input_set_certificate_id,
      body.norm_evidence_id,
      quorum_threshold(policy),
      body.robust_profile_id,
      policy.validator_ids,
  };
}

[[nodiscard]] certificates::AggregationPlanCertificate as_plan_certificate(
    const VoteAggregationPlanBody& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::AggregationPlanCertificate{
      body.context,
      body.accumulator_proof_id,
      body.bucket_assignments,
      body.eligibility_certificate_id,
      body.input_set_certificate_id,
      body.iteration_count,
      quorum_threshold(policy),
      body.seed_transcript_id,
      policy.validator_ids,
      body.transcript_root,
      body.weights,
  };
}

[[nodiscard]] certificates::ParameterShardQc as_parameter_certificate(
    const VoteParameterBody& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::ParameterShardQc{
      body.context,
      body.aggregation_plan_certificate_id,
      body.denominator,
      body.domain_id,
      body.eligibility_certificate_id,
      body.input_leaf_ids,
      body.input_set_certificate_id,
      quorum_threshold(policy),
      body.result_numerators,
      body.shard_id,
      policy.validator_ids,
  };
}

[[nodiscard]] certificates::AggregateRootQc as_root_certificate(
    const VoteAggregateRootBody& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::AggregateRootQc{
      body.context,
      body.aggregation_plan_certificate_id,
      body.eligibility_certificate_id,
      body.input_set_certificate_id,
      body.leaves,
      body.merkle_root,
      quorum_threshold(policy),
      body.required_keys,
      policy.validator_ids,
  };
}

[[nodiscard]] certificates::ApplyQc as_apply_certificate(
    const certificates::ApplyCandidate& body,
    const VoteAdmissionPolicy& policy) {
  return certificates::ApplyQc{
      body.context,
      body.aggregate_root_qc_id,
      body.apply_arithmetic_profile_id,
      certificates::content_id(body),
      body.next_model_hash,
      body.next_optimizer_hash,
      body.parent_checkpoint_id,
      quorum_threshold(policy),
      policy.validator_ids,
  };
}

void validate_typed_snapshot(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state) {
  const auto& snapshot = policy.snapshot;
  require_content_id(snapshot.state_id);
  const auto state_bytes = protocol::encode(state);
  require(
      snapshot.state_id ==
          canonical::content_id(canonical::Type::round_state, state_bytes),
      ErrorCode::vote_policy_invalid,
      "vote authority does not bind exact canonical state bytes");
  require_content_id(snapshot.parameter_schema_id);
  require_content_id(snapshot.arithmetic_profile_id);
  if (!snapshot.required_accumulator_proof_id.empty()) {
    require_content_id(snapshot.required_accumulator_proof_id);
  }
  validate_snapshot_sets(policy, snapshot);

  const certificates::Context expected{
      snapshot.arithmetic_profile_id,
      state.height,
      snapshot.parameter_schema_id,
      policy.round_config_id,
      policy.round_id,
      policy.validator_epoch_id,
      state.view,
  };
  const certificates::ChainVerifier verifier(
      expected,
      certificates::ValidatorPolicy{
          policy.validator_epoch_id,
          policy.validator_ids,
          quorum_threshold(policy),
      });

  require_ordered(
      snapshot.input_set_bodies,
      input_body_id,
      "input-set proposal bodies are not canonical");
  for (const auto& input : snapshot.input_set_bodies) {
    static_cast<void>(verifier.verify_input_set(as_input_certificate(input, policy)));
  }
  require_subset(
      snapshot.closed_input_set_ids,
      snapshot.input_set_bodies,
      input_body_id,
      "closed input body lacks typed proposal authority");

  require_ordered(
      snapshot.input_set_certificates,
      input_qc_id,
      "finalized input-set certificates are not canonical");
  for (const auto& input : snapshot.input_set_certificates) {
    require(
        verifier.verify_input_set(input) == input_qc_id(input),
        ErrorCode::vote_policy_invalid,
        "input-set certificate identity changed during native validation");
  }
  require_subset(
      snapshot.finalized_input_set_ids,
      snapshot.input_set_certificates,
      input_qc_id,
      "finalized ISC lacks a typed quorum certificate");

  require_ordered(snapshot.seed_transcripts, seed_id, "seeds are not canonical");
  for (const auto& seed : snapshot.seed_transcripts) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        seed.input_set_certificate_id,
        input_qc_id);
    require(
        input != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            verifier.verify_seed(seed, input_qc_id(*input)) == seed_id(seed),
        ErrorCode::vote_policy_invalid,
        "seed lacks an exact finalized ISC parent");
  }

  require_ordered(snapshot.norm_evidence, norm_id, "norm evidence is not canonical");
  for (const auto& norm : snapshot.norm_evidence) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        norm.input_set_certificate_id,
        input_qc_id);
    require(
        input != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            verifier.verify_norms(norm, input_qc_id(*input)) == norm_id(norm),
        ErrorCode::vote_policy_invalid,
        "norm evidence lacks an exact finalized ISC parent");
  }

  require_ordered(
      snapshot.eligibility_bodies,
      ec_body_id,
      "EC proposal bodies are not canonical");
  for (const auto& ec : snapshot.eligibility_bodies) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        ec.input_set_certificate_id,
        input_qc_id);
    const auto* norm = find_by_id(snapshot.norm_evidence, ec.norm_evidence_id, norm_id);
    const auto* seed =
        find_by_id(snapshot.seed_transcripts, ec.seed_transcript_id, seed_id);
    require(
        input != nullptr && norm != nullptr && seed != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            norm->input_set_certificate_id == input_qc_id(*input) &&
            seed->input_set_certificate_id == input_qc_id(*input),
        ErrorCode::vote_policy_invalid,
        "EC proposal has missing or mixed ISC/seed/norm parents");
    static_cast<void>(verifier.verify_eligibility(
        as_eligibility_certificate(ec, policy), *input, norm_id(*norm)));
  }

  require_ordered(
      snapshot.eligibility_certificates,
      ec_qc_id,
      "finalized EC certificates are not canonical");
  for (const auto& ec : snapshot.eligibility_certificates) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        ec.certificate.input_set_certificate_id,
        input_qc_id);
    const auto* norm =
        find_by_id(snapshot.norm_evidence, ec.certificate.norm_evidence_id, norm_id);
    const auto* seed =
        find_by_id(snapshot.seed_transcripts, ec.seed_transcript_id, seed_id);
    require(
        input != nullptr && norm != nullptr && seed != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            seed->input_set_certificate_id == input_qc_id(*input) &&
            verifier.verify_eligibility(ec.certificate, *input, norm_id(*norm)) ==
                ec_qc_id(ec),
        ErrorCode::vote_policy_invalid,
        "finalized EC lacks exact ISC/seed/norm/quorum authority");
  }
  require_subset(
      snapshot.finalized_eligibility_ids,
      snapshot.eligibility_certificates,
      ec_qc_id,
      "finalized EC lacks a typed quorum certificate");

  require_ordered(
      snapshot.aggregation_plan_bodies,
      plan_body_id,
      "APC proposal bodies are not canonical");
  require_ordered(
      snapshot.aggregation_plan_certificates,
      plan_qc_id,
      "finalized APC certificates are not canonical");
  if (!snapshot.aggregation_plan_bodies.empty() ||
      !snapshot.aggregation_plan_certificates.empty()) {
    require_content_id(snapshot.required_accumulator_proof_id);
  }
  const auto validate_plan = [&](const auto& plan, bool finalized) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        plan.input_set_certificate_id,
        input_qc_id);
    const auto* ec = find_by_id(
        snapshot.eligibility_certificates,
        plan.eligibility_certificate_id,
        ec_qc_id);
    const auto* seed =
        find_by_id(snapshot.seed_transcripts, plan.seed_transcript_id, seed_id);
    require(
        input != nullptr && ec != nullptr && seed != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            contains(snapshot.finalized_eligibility_ids, ec_qc_id(*ec)) &&
            ec->seed_transcript_id == seed_id(*seed),
        ErrorCode::vote_policy_invalid,
        finalized ? "finalized APC lacks exact finalized lineage"
                  : "APC proposal lacks exact finalized lineage");
    return std::tuple{input, ec, seed};
  };
  for (const auto& plan : snapshot.aggregation_plan_bodies) {
    const auto [input, ec, seed] = validate_plan(plan, false);
    static_cast<void>(verifier.verify_plan(
        as_plan_certificate(plan, policy),
        *input,
        ec->certificate,
        seed_id(*seed),
        snapshot.required_accumulator_proof_id));
  }
  for (const auto& plan : snapshot.aggregation_plan_certificates) {
    const auto [input, ec, seed] = validate_plan(plan, true);
    require(
        verifier.verify_plan(
            plan,
            *input,
            ec->certificate,
            seed_id(*seed),
            snapshot.required_accumulator_proof_id) == plan_qc_id(plan),
        ErrorCode::vote_policy_invalid,
        "finalized APC identity changed during native validation");
  }
  require_subset(
      snapshot.finalized_aggregation_plan_ids,
      snapshot.aggregation_plan_certificates,
      plan_qc_id,
      "finalized APC lacks a typed quorum certificate");

  require_ordered(
      snapshot.parameter_bodies,
      parameter_body_id,
      "parameter proposal bodies are not canonical");
  require_ordered(
      snapshot.parameter_qcs,
      parameter_qc_id,
      "finalized parameter QCs are not canonical");
  std::set<std::string_view> assignment_contexts;
  std::map<
      std::tuple<std::string_view, std::string_view, std::string_view>,
      std::string_view>
      assignment_context_by_key;
  for (const auto& parameter : snapshot.parameter_bodies) {
    require_id(parameter.vote_context_id);
    const auto assignment_key = std::tuple{
        std::string_view(parameter.aggregation_plan_certificate_id),
        std::string_view(parameter.domain_id),
        std::string_view(parameter.shard_id)};
    const auto [assignment, inserted] =
        assignment_context_by_key.try_emplace(assignment_key, parameter.vote_context_id);
    require(
        inserted || assignment->second == parameter.vote_context_id,
        ErrorCode::vote_policy_invalid,
        "formal parameter assignment key has conflicting vote contexts");
    require(
        assignment_contexts.insert(parameter.vote_context_id).second,
        ErrorCode::vote_policy_invalid,
        "parameter assignment context is duplicated");
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        parameter.input_set_certificate_id,
        input_qc_id);
    const auto* ec = find_by_id(
        snapshot.eligibility_certificates,
        parameter.eligibility_certificate_id,
        ec_qc_id);
    const auto* plan = find_by_id(
        snapshot.aggregation_plan_certificates,
        parameter.aggregation_plan_certificate_id,
        plan_qc_id);
    require(
        input != nullptr && ec != nullptr && plan != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            contains(snapshot.finalized_eligibility_ids, ec_qc_id(*ec)) &&
            contains(snapshot.finalized_aggregation_plan_ids, plan_qc_id(*plan)) &&
            plan->input_set_certificate_id == input_qc_id(*input) &&
            plan->eligibility_certificate_id == ec_qc_id(*ec) &&
            std::binary_search(
                snapshot.required_parameter_keys.begin(),
                snapshot.required_parameter_keys.end(),
                certificates::ShardKey{parameter.domain_id, parameter.shard_id}) &&
            std::any_of(
                ec->certificate.entries.begin(),
                ec->certificate.entries.end(),
                [&](const auto& entry) {
                  return entry.accepted && entry.domain_id == parameter.domain_id;
                }),
        ErrorCode::vote_policy_invalid,
        "parameter proposal lacks exact assignment/finalized lineage");
    static_cast<void>(verifier.verify_shard(
        as_parameter_certificate(parameter, policy),
        input_qc_id(*input),
        ec_qc_id(*ec),
        plan_qc_id(*plan)));
  }
  for (const auto& parameter : snapshot.parameter_qcs) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        parameter.input_set_certificate_id,
        input_qc_id);
    const auto* ec = find_by_id(
        snapshot.eligibility_certificates,
        parameter.eligibility_certificate_id,
        ec_qc_id);
    const auto* plan = find_by_id(
        snapshot.aggregation_plan_certificates,
        parameter.aggregation_plan_certificate_id,
        plan_qc_id);
    require(
        input != nullptr && ec != nullptr && plan != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            contains(snapshot.finalized_eligibility_ids, ec_qc_id(*ec)) &&
            contains(snapshot.finalized_aggregation_plan_ids, plan_qc_id(*plan)) &&
            verifier.verify_shard(
                parameter,
                input_qc_id(*input),
                ec_qc_id(*ec),
                plan_qc_id(*plan)) == parameter_qc_id(parameter),
        ErrorCode::vote_policy_invalid,
        "finalized parameter QC lacks exact lineage/quorum authority");
  }
  require_subset(
      snapshot.finalized_parameter_ids,
      snapshot.parameter_qcs,
      parameter_qc_id,
      "finalized parameter result lacks a typed QC");

  require(
      std::is_sorted(
          snapshot.required_parameter_keys.begin(), snapshot.required_parameter_keys.end()) &&
          std::adjacent_find(
              snapshot.required_parameter_keys.begin(), snapshot.required_parameter_keys.end()) ==
              snapshot.required_parameter_keys.end(),
      ErrorCode::vote_policy_invalid,
      "required parameter matrix is not canonical");
  const auto finalized_root_inputs = [&](const auto& root) {
    const auto* input = find_by_id(
        snapshot.input_set_certificates,
        root.input_set_certificate_id,
        input_qc_id);
    const auto* ec = find_by_id(
        snapshot.eligibility_certificates,
        root.eligibility_certificate_id,
        ec_qc_id);
    const auto* plan = find_by_id(
        snapshot.aggregation_plan_certificates,
        root.aggregation_plan_certificate_id,
        plan_qc_id);
    require(
        input != nullptr && ec != nullptr && plan != nullptr &&
            contains(snapshot.finalized_input_set_ids, input_qc_id(*input)) &&
            contains(snapshot.finalized_eligibility_ids, ec_qc_id(*ec)) &&
            contains(snapshot.finalized_aggregation_plan_ids, plan_qc_id(*plan)),
        ErrorCode::vote_policy_invalid,
        "aggregate root lacks exact finalized parents");
    std::vector<certificates::ParameterShardQc> shards;
    shards.reserve(root.leaves.size());
    for (const auto& leaf : root.leaves) {
      const auto* parameter =
          find_by_id(snapshot.parameter_qcs, leaf.parameter_shard_qc_id, parameter_qc_id);
      require(
          parameter != nullptr &&
              contains(snapshot.finalized_parameter_ids, parameter_qc_id(*parameter)) &&
              parameter->domain_id == leaf.domain_id &&
              parameter->shard_id == leaf.shard_id,
          ErrorCode::vote_policy_invalid,
          "aggregate root has missing, duplicate, or mixed parameter coverage");
      shards.push_back(*parameter);
    }
    return std::tuple{input, ec, plan, shards};
  };

  require_ordered(
      snapshot.aggregate_root_bodies,
      root_body_id,
      "aggregate-root proposal bodies are not canonical");
  for (const auto& root : snapshot.aggregate_root_bodies) {
    const auto [input, ec, plan, shards] = finalized_root_inputs(root);
    static_cast<void>(verifier.verify_root(
        as_root_certificate(root, policy),
        input_qc_id(*input),
        ec_qc_id(*ec),
        plan_qc_id(*plan),
        snapshot.required_parameter_keys,
        shards));
  }
  require_ordered(
      snapshot.aggregate_root_qcs,
      root_qc_id,
      "finalized aggregate-root QCs are not canonical");
  for (const auto& root : snapshot.aggregate_root_qcs) {
    const auto [input, ec, plan, shards] = finalized_root_inputs(root);
    require(
        verifier.verify_root(
            root,
            input_qc_id(*input),
            ec_qc_id(*ec),
            plan_qc_id(*plan),
            snapshot.required_parameter_keys,
            shards) == root_qc_id(root),
        ErrorCode::vote_policy_invalid,
        "finalized aggregate-root identity changed during native validation");
  }
  require_subset(
      snapshot.finalized_aggregate_root_ids,
      snapshot.aggregate_root_qcs,
      root_qc_id,
      "finalized root lacks a typed QC");

  require_ordered(snapshot.apply_profiles, profile_id, "apply profiles are not canonical");
  require_ordered(
      snapshot.apply_candidates,
      apply_body_id,
      "apply proposal bodies are not canonical");
  for (const auto& apply : snapshot.apply_candidates) {
    const auto* root = find_by_id(
        snapshot.aggregate_root_qcs,
        apply.aggregate_root_qc_id,
        root_qc_id);
    const auto* profile = find_by_id(
        snapshot.apply_profiles,
        apply.apply_arithmetic_profile_id,
        profile_id);
    require(
        root != nullptr && profile != nullptr &&
            contains(snapshot.finalized_aggregate_root_ids, root_qc_id(*root)) &&
            apply.parent_checkpoint_id == state.parent_checkpoint_id,
        ErrorCode::vote_policy_invalid,
        "apply proposal lacks exact root/profile/current authority");
    static_cast<void>(verifier.verify_apply(
        as_apply_certificate(apply, policy),
        apply,
        root_qc_id(*root),
        profile_id(*profile)));
  }
  require_ordered(
      snapshot.apply_qcs,
      apply_qc_id,
      "finalized ApplyQCs are not canonical");
  for (const auto& apply : snapshot.apply_qcs) {
    const auto* root = find_by_id(
        snapshot.aggregate_root_qcs,
        apply.certificate.aggregate_root_qc_id,
        root_qc_id);
    const auto* profile = find_by_id(
        snapshot.apply_profiles,
        apply.certificate.apply_arithmetic_profile_id,
        profile_id);
    require(
        root != nullptr && profile != nullptr &&
            contains(snapshot.finalized_aggregate_root_ids, root_qc_id(*root)) &&
            apply.candidate.parent_checkpoint_id == state.parent_checkpoint_id &&
            verifier.verify_apply(
                apply.certificate,
                apply.candidate,
                root_qc_id(*root),
                profile_id(*profile)) == apply_qc_id(apply),
        ErrorCode::vote_policy_invalid,
        "finalized ApplyQC lacks exact root/profile/current/quorum authority");
  }
  require_subset(
      snapshot.finalized_apply_ids,
      snapshot.apply_qcs,
      apply_qc_id,
      "finalized apply body lacks a typed QC");

  std::tuple<std::string_view, std::uint64_t, std::uint64_t> previous_observation{};
  bool first = true;
  for (const auto& observation : snapshot.timeout_observations) {
    require_id(observation.round_id);
    const auto key = std::tuple<std::string_view, std::uint64_t, std::uint64_t>{
        observation.round_id, observation.height, observation.view};
    require(
        first || previous_observation < key,
        ErrorCode::vote_policy_invalid,
        "timeout observations are not canonical");
    previous_observation = key;
    first = false;
  }
  require_ordered(
      snapshot.view_change_bodies,
      vote_view_change_body_id,
      "view-change bodies are not canonical");
  std::pair<std::string_view, std::string_view> previous_request{};
  first = true;
  for (const auto& request : snapshot.abort_requests) {
    require_id(request.round_id);
    require(
        is_abort_request_reason(request.reason_code),
        ErrorCode::vote_policy_invalid,
        "abort request reason is outside the closed formal vocabulary");
    const auto key = std::pair<std::string_view, std::string_view>{
        request.round_id, request.reason_code};
    require(
        first || previous_request < key,
        ErrorCode::vote_policy_invalid,
        "abort requests are not canonical");
    previous_request = key;
    first = false;
  }
  require_ordered(snapshot.abort_bodies, vote_abort_body_id, "abort bodies are not canonical");
  for (const auto& abort : snapshot.abort_bodies) {
    require(
        abort.round_id == policy.round_id &&
            abort.validator_epoch_id == policy.validator_epoch_id &&
            abort.height == state.height && abort.view == state.view &&
            abort.hard_deadline_tick == policy.hard_deadline_tick &&
            abort.parent_checkpoint_id == state.parent_checkpoint_id &&
            abort.reason_code == policy.configured_abort_reason &&
            abort.round_config_ids == snapshot.finalized_round_config_ids &&
            abort.input_set_ids == snapshot.finalized_input_set_ids &&
            abort.eligibility_ids == snapshot.finalized_eligibility_ids &&
            abort.aggregation_plan_ids == snapshot.finalized_aggregation_plan_ids &&
            abort.parameter_ids == snapshot.finalized_parameter_ids &&
            abort.aggregate_root_ids == snapshot.finalized_aggregate_root_ids &&
            abort.apply_ids == snapshot.finalized_apply_ids,
        ErrorCode::vote_policy_invalid,
        "abort body is not the exact current lineage");
  }
}

[[nodiscard]] bool has_abort_request(
    const VoteAdmissionSnapshot& snapshot,
    std::string_view round,
    std::string_view reason) {
  return std::any_of(
      snapshot.abort_requests.begin(),
      snapshot.abort_requests.end(),
      [&](const auto& request) {
        return request.round_id == round && request.reason_code == reason;
      });
}

void validate_candidate_authority(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state,
    const VoteCandidateBinding& candidate) {
  const auto& snapshot = policy.snapshot;
  const auto& parent = candidate.parents;
  require(
      candidate.height == state.height && candidate.view == state.view,
      ErrorCode::vote_policy_invalid,
      "candidate coordinates differ from current native state");
  switch (candidate.action) {
    case VoteAction::round_config:
      require(
          contains(snapshot.proposed_round_config_ids, candidate.body_hash) &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id),
          ErrorCode::vote_policy_invalid,
          "config vote body/context differs from the typed proposal");
      return;
    case VoteAction::input_set:
      require(
          contains(snapshot.closed_input_set_ids, candidate.body_hash) &&
              find_by_id(
                  snapshot.input_set_bodies,
                  candidate.body_hash,
                  input_body_id) != nullptr &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id),
          ErrorCode::vote_policy_invalid,
          "ISC vote body/context is absent from closed inputs");
      return;
    case VoteAction::eligibility: {
      const auto* body =
          find_by_id(snapshot.eligibility_bodies, candidate.body_hash, ec_body_id);
      require(
          body != nullptr &&
              contains(snapshot.finalized_input_set_ids, body->input_set_certificate_id) &&
              parent.input_set_certificate_id == body->input_set_certificate_id &&
              parent.seed_transcript_id == body->seed_transcript_id &&
              parent.norm_evidence_id == body->norm_evidence_id &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id,
                  body->input_set_certificate_id),
          ErrorCode::vote_policy_invalid,
          "EC vote differs from typed finalized lineage");
      return;
    }
    case VoteAction::aggregation_plan: {
      const auto* body = find_by_id(
          snapshot.aggregation_plan_bodies,
          candidate.body_hash,
          plan_body_id);
      require(
          body != nullptr &&
              contains(snapshot.finalized_input_set_ids, body->input_set_certificate_id) &&
              contains(snapshot.finalized_eligibility_ids, body->eligibility_certificate_id) &&
              parent.input_set_certificate_id == body->input_set_certificate_id &&
              parent.seed_transcript_id == body->seed_transcript_id &&
              parent.eligibility_certificate_id == body->eligibility_certificate_id &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id,
                  body->eligibility_certificate_id),
          ErrorCode::vote_policy_invalid,
          "APC vote differs from typed finalized lineage");
      const auto* ec = find_by_id(
          snapshot.eligibility_certificates,
          body->eligibility_certificate_id,
          ec_qc_id);
      require(
          ec != nullptr &&
              parent.norm_evidence_id == ec->certificate.norm_evidence_id,
          ErrorCode::vote_policy_invalid,
          "APC vote differs from exact norm lineage");
      return;
    }
    case VoteAction::parameter: {
      const auto* body = find_by_id(
          snapshot.parameter_bodies,
          candidate.body_hash,
          parameter_body_id);
      require(
          body != nullptr && body->vote_context_id == candidate.context_id &&
              contains(
                  snapshot.finalized_aggregation_plan_ids,
                  body->aggregation_plan_certificate_id) &&
              parent.input_set_certificate_id == body->input_set_certificate_id &&
              parent.eligibility_certificate_id == body->eligibility_certificate_id &&
              parent.aggregation_plan_certificate_id ==
                  body->aggregation_plan_certificate_id &&
              parent.domain_id == body->domain_id &&
              parent.shard_id == body->shard_id &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id,
                  body->vote_context_id),
          ErrorCode::vote_policy_invalid,
          "parameter vote is outside exact prepared assignment");
      const auto* plan = find_by_id(
          snapshot.aggregation_plan_certificates,
          body->aggregation_plan_certificate_id,
          plan_qc_id);
      require(
          plan != nullptr && parent.seed_transcript_id == plan->seed_transcript_id,
          ErrorCode::vote_policy_invalid,
          "parameter vote has wrong seed lineage");
      return;
    }
    case VoteAction::aggregate_root: {
      const auto* body = find_by_id(
          snapshot.aggregate_root_bodies,
          candidate.body_hash,
          root_body_id);
      require(
          body != nullptr &&
              contains(
                  snapshot.finalized_aggregation_plan_ids,
                  body->aggregation_plan_certificate_id) &&
              parent.input_set_certificate_id == body->input_set_certificate_id &&
              parent.eligibility_certificate_id == body->eligibility_certificate_id &&
              parent.aggregation_plan_certificate_id ==
                  body->aggregation_plan_certificate_id &&
              parent.parameter_matrix_root == body->merkle_root &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id,
                  body->aggregation_plan_certificate_id),
          ErrorCode::vote_policy_invalid,
          "root vote is outside exact prepared matrix");
      const auto* plan = find_by_id(
          snapshot.aggregation_plan_certificates,
          body->aggregation_plan_certificate_id,
          plan_qc_id);
      require(
          plan != nullptr && parent.seed_transcript_id == plan->seed_transcript_id,
          ErrorCode::vote_policy_invalid,
          "root vote has wrong seed lineage");
      return;
    }
    case VoteAction::apply: {
      const auto* body = find_by_id(
          snapshot.apply_candidates,
          candidate.body_hash,
          apply_body_id);
      require(
          body != nullptr &&
              contains(snapshot.finalized_aggregate_root_ids, body->aggregate_root_qc_id) &&
              parent.aggregate_root_certificate_id == body->aggregate_root_qc_id &&
              parent.apply_profile_id == body->apply_arithmetic_profile_id &&
              parent.apply_candidate_id == apply_body_id(*body) &&
              body->parent_checkpoint_id == state.parent_checkpoint_id &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id,
                  body->aggregate_root_qc_id),
          ErrorCode::vote_policy_invalid,
          "apply vote is outside exact checked candidate/current parent");
      return;
    }
    case VoteAction::view_change: {
      const auto* body = find_by_id(
          snapshot.view_change_bodies, candidate.body_hash, vote_view_change_body_id);
      require(
          body != nullptr && body->round_id == policy.round_id &&
              body->height == state.height && body->from_view == state.view &&
              state.view != std::numeric_limits<std::uint64_t>::max() &&
              body->to_view == state.view + 1U &&
              body->soft_deadline_tick == policy.soft_deadline_tick &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  body->from_view,
                  policy.validator_epoch_id) &&
              std::any_of(
                  snapshot.timeout_observations.begin(),
                  snapshot.timeout_observations.end(),
                  [&](const auto& observation) {
                    return observation.round_id == body->round_id &&
                           observation.height == body->height &&
                           observation.view == body->from_view;
                  }),
          ErrorCode::vote_policy_invalid,
          "view vote lacks exact timeout observation/body");
      return;
    }
    case VoteAction::abort: {
      const auto* body = find_by_id(snapshot.abort_bodies, candidate.body_hash, vote_abort_body_id);
      require(
          body != nullptr && body->reason_code == parent.reason_code &&
              body->parent_checkpoint_id == state.parent_checkpoint_id &&
              snapshot.finalized_apply_ids.empty() &&
              candidate.context_id == vote_context_id(
                  candidate.action,
                  policy.round_id,
                  state.height,
                  state.view,
                  policy.validator_epoch_id),
          ErrorCode::vote_policy_invalid,
          "abort vote is not exact lineage or follows finalized apply");
      return;
    }
  }
}

void validate_policy_impl(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state) {
  require_id(policy.local_validator_id);
  require_content_id(policy.validator_epoch_id);
  require(
      !policy.validator_ids.empty() && policy.validator_ids.size() <= max_vote_validator_count,
      ErrorCode::vote_policy_invalid,
      "validator set is empty or exceeds frozen bound");
  require_sorted_ids(policy.validator_ids, false);
  require(
      (policy.validator_ids.size() % 3U) == 1U &&
          contains(policy.validator_ids, policy.local_validator_id),
      ErrorCode::vote_policy_invalid,
      "local validator is not in a canonical 3f+1 set");
  require(
      policy.role == ValidatorRole::validator,
      ErrorCode::vote_policy_invalid,
      "consensus identity lacks validator role");
  require_id(policy.round_id);
  require_content_id(policy.round_config_id);
  require(
      is_configured_abort_reason(policy.configured_abort_reason),
      ErrorCode::vote_policy_invalid,
      "configured abort reason is outside the closed formal vocabulary");
  require(
      policy.soft_deadline_tick < policy.hard_deadline_tick,
      ErrorCode::vote_policy_invalid,
      "vote deadlines are not strictly ordered");
  require(
      state.round_id == policy.round_id && state.config_id == policy.round_config_id,
      ErrorCode::vote_policy_invalid,
      "vote policy does not bind native round/config");
  require(
      !policy.candidates.empty() && policy.candidates.size() <= max_vote_candidate_count,
      ErrorCode::vote_policy_invalid,
      "candidate set is empty or exceeds frozen bound");
  validate_typed_snapshot(policy, state);
  std::tuple<std::uint64_t, std::uint64_t, std::uint32_t, std::string_view> previous{};
  std::set<std::string_view> contexts;
  bool first = true;
  for (const auto& candidate : policy.candidates) {
    validate_candidate_shape(policy, candidate);
    validate_candidate_authority(policy, state, candidate);
    const auto key = std::tuple{
        candidate.height,
        candidate.view,
        static_cast<std::uint32_t>(candidate.action),
        std::string_view(candidate.context_id)};
    require(
        first || previous < key,
        ErrorCode::vote_policy_invalid,
        "candidate order is invalid");
    require(
        contexts.insert(candidate.context_id).second,
        ErrorCode::vote_policy_invalid,
        "candidate context is not globally unique");
    previous = key;
    first = false;
  }
}

}  // namespace

void validate_vote_admission_policy(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state) {
  try {
    validate_policy_impl(policy, state);
  } catch (const certificates::CertificateError&) {
    reject(
        ErrorCode::vote_policy_invalid,
        "typed vote authority failed native certificate validation");
  }
}

VoteAdmission validate_vote_admission(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state,
    const VoteAdmissionState& admission_state,
    const protocol::Vote& vote,
    std::uint64_t expected_durable_sequence,
    VoteAdmissionMode mode) {
  validate_vote_admission_policy(policy, state);
  require_vote(vote);
  const auto action = parse_vote_action(vote.kind);
#if !defined(DELTA_RECORD_VOTE_MUTANT_SKIP_ARITHMETIC_INPUT_GUARD)
  // The current immutable vote policy binds PARAMETER/APPLY result bodies, but
  // it does not carry the authoritative q-shard bytes or parent model,
  // optimizer, and domain-aggregate values required to recompute those bodies.
  // Treating a self-consistent caller-supplied result as that authority would
  // permit arbitrary arithmetic to become durable. Until those already-frozen
  // inputs have a native binding, both live admission and recovery fail closed.
  require(
      action != VoteAction::parameter && action != VoteAction::apply,
      ErrorCode::vote_admission_rejected,
      "arithmetic vote lacks authoritative native recomputation inputs");
#endif
  require(
      vote.validator_id == policy.local_validator_id &&
          vote.validator_epoch_id == policy.validator_epoch_id &&
          vote.round_id == state.round_id && vote.height == state.height &&
          vote.view == state.view,
      ErrorCode::vote_admission_rejected,
      "vote identity/current coordinates differ from native state");
  const VoteCandidateBinding* binding = nullptr;
  for (const auto& candidate : policy.candidates) {
    const auto context_matches =
#if defined(DELTA_RECORD_VOTE_MUTANT_SKIP_CONTEXT_GUARD)
        true;
#else
        candidate.context_id == vote.context_id;
#endif
    if (candidate.action == action && candidate.height == state.height &&
        candidate.view == state.view && context_matches) {
      binding = &candidate;
      break;
    }
  }
  require(
      binding != nullptr,
      ErrorCode::vote_admission_rejected,
      "vote context is outside immutable typed candidate set");
  require(
      vote.body_hash == binding->body_hash &&
          binding->parents.parent_checkpoint_id == state.parent_checkpoint_id,
      ErrorCode::vote_admission_rejected,
      "vote body/current checkpoint differs from typed candidate");
  require(
      vote.durable_sequence == expected_durable_sequence,
      ErrorCode::vote_admission_rejected,
      "vote sequence differs from native WAL admission");
  if (mode == VoteAdmissionMode::live) {
    require(
        admission_state.recovery_ready,
        ErrorCode::vote_admission_rejected,
        "vote admission precedes native journal recovery");
  }
  require(
      !admission_state.authority_invalidated,
      ErrorCode::vote_admission_rejected,
      "vote authority was invalidated by committed transition");
  require(
      phase_allows(action, state.phase),
      ErrorCode::vote_admission_rejected,
      "vote action is illegal in current native phase");
  if (action == VoteAction::view_change) {
    require(
        policy.snapshot.abort_requests.empty() &&
            admission_state.logical_tick >= policy.soft_deadline_tick &&
            admission_state.logical_tick < policy.hard_deadline_tick,
        ErrorCode::vote_admission_rejected,
        "view vote is outside exact deadline window");
  } else if (action == VoteAction::abort) {
    const auto* body =
        find_by_id(policy.snapshot.abort_bodies, vote.body_hash, vote_abort_body_id);
    require(
        body != nullptr &&
            body->reason_code == policy.configured_abort_reason &&
            (has_abort_request(
                 policy.snapshot, policy.round_id, policy.configured_abort_reason) ||
             admission_state.logical_tick >= policy.hard_deadline_tick),
        ErrorCode::vote_admission_rejected,
        "abort vote is not enabled by exact request/deadline state");
  } else {
    require(
        policy.snapshot.abort_requests.empty() &&
            admission_state.logical_tick < policy.hard_deadline_tick,
        ErrorCode::vote_admission_rejected,
        "ordinary vote is closed by abort/deadline state");
  }
  return VoteAdmission{
      action,
      std::string(vote_formal_action_id(action)),
      binding->context_id,
      binding->parents,
  };
}

}  // namespace delta::core::consensus
