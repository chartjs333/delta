#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>

#include "vote_fixture.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace vote_fixture = delta::test::vote_fixture;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_consensus_error(consensus::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const consensus::ConsensusError& error) {
    expect(error.code() == expected, "unexpected stable consensus error code");
    return;
  }
  fail("invalid consensus input was accepted");
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

[[nodiscard]] canonical::Bytes decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] canonical::Bytes golden(std::uint16_t type_code) {
  std::ifstream input(DELTA_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    const auto& match = *cursor;
    if (std::stoul(match[2].str()) == type_code) {
      return decode_hex(match[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] std::string content_id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] protocol::RoundState state_for(consensus::VoteAction action) {
  return vote_fixture::full(action).state;
}

[[nodiscard]] consensus::VoteAdmissionPolicy policy_for(consensus::VoteAction action) {
  return vote_fixture::full(action).policy;
}

[[nodiscard]] consensus::VoteAdmissionState admission_state_for(
    const consensus::VoteAdmissionPolicy& policy) {
  return consensus::VoteAdmissionState{
      policy.initial_logical_tick,
      true,
      false,
  };
}

[[nodiscard]] bool requires_unavailable_arithmetic_inputs(
    consensus::VoteAction action) noexcept {
  return action == consensus::VoteAction::parameter ||
         action == consensus::VoteAction::apply;
}

[[nodiscard]] protocol::Vote vote_for(
    const consensus::VoteAdmissionPolicy& policy,
    const consensus::VoteCandidateBinding& candidate,
    std::uint64_t sequence = 1U) {
  return protocol::Vote{
      candidate.body_hash,
      std::string(consensus::frozen_vote_context(candidate)),
      sequence,
      candidate.height,
      std::string(consensus::vote_kind_name(candidate.action)),
      policy.round_id,
      content_id('f'),
      policy.validator_epoch_id,
      policy.local_validator_id,
      candidate.view,
  };
}

void test_durable_vote_uniqueness() {
  auto vote = protocol::parse_vote(golden(3U));
  consensus::VoteJournal journal;
  expect(
      journal.record(vote) == consensus::Disposition::recorded,
      "first durable vote was not recorded");
  expect(
      journal.record(vote) == consensus::Disposition::replay,
      "exact durable vote replay was not idempotent");

  auto conflicting = vote;
  conflicting.body_hash = content_id('b');
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &conflicting] {
    static_cast<void>(journal.record(conflicting));
  });
  expect(journal.votes().size() == 1U, "conflicting vote changed durable journal");

  auto changed_signature = vote;
  changed_signature.signature_id = content_id('c');
  expect_consensus_error(
      consensus::ErrorCode::conflicting_vote, [&journal, &changed_signature] {
        static_cast<void>(journal.record(changed_signature));
      });

  auto changed_sequence = vote;
  ++changed_sequence.durable_sequence;
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &changed_sequence] {
    static_cast<void>(journal.record(changed_sequence));
  });

  auto changed_kind = vote;
  changed_kind.kind = "ISC";
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &changed_kind] {
    static_cast<void>(journal.record(changed_kind));
  });
  auto unknown_kind = vote;
  unknown_kind.kind = "FREE_FORM";
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &unknown_kind] {
    static_cast<void>(journal.record(unknown_kind));
  });
  auto invalid_body = vote;
  invalid_body.body_hash = "not-a-content-id";
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &invalid_body] {
    static_cast<void>(journal.record(invalid_body));
  });
  auto changed_round = vote;
  changed_round.round_id = "round-conflict";
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &changed_round] {
    static_cast<void>(journal.record(changed_round));
  });
  auto changed_height = vote;
  ++changed_height.height;
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &changed_height] {
    static_cast<void>(journal.record(changed_height));
  });
  auto changed_view = vote;
  ++changed_view.view;
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &changed_view] {
    static_cast<void>(journal.record(changed_view));
  });

  auto next_view = vote;
  next_view.view = 1U;
  next_view.context_id = "ROUND_CONFIG:round-003-fixture:1:1";
  next_view.durable_sequence = 2U;
  expect(
      journal.record(next_view) == consensus::Disposition::recorded,
      "distinct vote context was rejected");
}

void test_closed_vote_admission_matrix() {
  const std::vector<consensus::VoteAction> actions{
      consensus::VoteAction::round_config,
      consensus::VoteAction::input_set,
      consensus::VoteAction::eligibility,
      consensus::VoteAction::aggregation_plan,
      consensus::VoteAction::parameter,
      consensus::VoteAction::aggregate_root,
      consensus::VoteAction::apply,
      consensus::VoteAction::view_change,
      consensus::VoteAction::abort,
  };
  for (const auto action : actions) {
    const auto state = state_for(action);
    const auto policy = policy_for(action);
    consensus::validate_vote_admission_policy(policy, state);
    const auto vote = vote_for(policy, policy.candidates.front());
    if (requires_unavailable_arithmetic_inputs(action)) {
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(consensus::validate_vote_admission(
            policy, state, admission_state_for(policy), vote, 1U));
      });
    } else {
      const auto admitted = consensus::validate_vote_admission(
          policy, state, admission_state_for(policy), vote, 1U);
      expect(admitted.action == action, "vote action mapping changed");
      expect(
          admitted.formal_action_id == consensus::vote_formal_action_id(action),
          "formal vote action mapping changed");
      expect(admitted.context_id == vote.context_id, "frozen vote context changed");
    }

    auto wrong_phase = state;
    wrong_phase.phase = action == consensus::VoteAction::view_change ||
                                action == consensus::VoteAction::abort
                            ? protocol::RoundPhase::aggregated
                        : state.phase == protocol::RoundPhase::available
                            ? protocol::RoundPhase::eligible
                            : protocol::RoundPhase::available;
    auto wrong_phase_policy = policy;
    wrong_phase_policy.snapshot.state_id = canonical::content_id(
        canonical::Type::round_state, protocol::encode(wrong_phase));
    expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
      static_cast<void>(consensus::validate_vote_admission(
          wrong_phase_policy,
          wrong_phase,
          admission_state_for(wrong_phase_policy),
          vote,
          1U));
    });

    auto missing_parent = policy;
    auto& parents = missing_parent.candidates.front().parents;
    switch (action) {
      case consensus::VoteAction::round_config:
        parents.round_config_id.clear();
        break;
      case consensus::VoteAction::input_set:
        parents.parent_checkpoint_id.clear();
        break;
      case consensus::VoteAction::eligibility:
        parents.input_set_certificate_id.clear();
        break;
      case consensus::VoteAction::aggregation_plan:
        parents.eligibility_certificate_id.clear();
        break;
      case consensus::VoteAction::parameter:
        parents.domain_id.clear();
        break;
      case consensus::VoteAction::aggregate_root:
        parents.parameter_matrix_root.clear();
        break;
      case consensus::VoteAction::apply:
        parents.apply_profile_id.clear();
        break;
      case consensus::VoteAction::view_change:
        parents.round_config_id.clear();
        break;
      case consensus::VoteAction::abort:
        parents.reason_code.clear();
        break;
    }
    expect_consensus_error(consensus::ErrorCode::identifier_invalid, [&] {
      consensus::validate_vote_admission_policy(missing_parent, state);
    });
  }

  const auto state = state_for(consensus::VoteAction::round_config);
  const auto policy = policy_for(consensus::VoteAction::round_config);
  const auto valid = vote_for(policy, policy.candidates.front());
  auto changed = valid;
  changed.kind = "FREE_FORM";
  expect_consensus_error(consensus::ErrorCode::vote_action_invalid, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  changed = valid;
  changed.kind = "ISC";
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  changed = valid;
  changed.validator_id = "validator-2";
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  changed = valid;
  changed.validator_epoch_id = content_id('a');
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  changed = valid;
  changed.context_id = content_id('a');
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  changed = valid;
  changed.body_hash = content_id('a');
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), changed, 1U));
  });
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), valid, 2U));
  });

  auto wrong_parent = policy;
  wrong_parent.candidates.front().parents.parent_checkpoint_id = content_id('a');
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        wrong_parent, state, admission_state_for(wrong_parent), valid, 1U));
  });
  auto wrong_role = policy;
  wrong_role.role = static_cast<consensus::ValidatorRole>(2U);
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(wrong_role, state);
  });
  auto wrong_candidate_action = policy;
  wrong_candidate_action.candidates.front().action =
      static_cast<consensus::VoteAction>(99U);
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(wrong_candidate_action, state);
  });
  auto wrong_phase = state;
  wrong_phase.phase = protocol::RoundPhase::aggregated;
  auto wrong_phase_policy = policy;
  wrong_phase_policy.snapshot.state_id = canonical::content_id(
      canonical::Type::round_state, protocol::encode(wrong_phase));
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        wrong_phase_policy,
        wrong_phase,
        admission_state_for(wrong_phase_policy),
        valid,
        1U));
  });
  auto expired = admission_state_for(policy);
  expired.logical_tick = policy.hard_deadline_tick;
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(policy, state, expired, valid, 1U));
  });

  auto recovery_state = admission_state_for(policy);
  recovery_state.recovery_ready = false;
  static_cast<void>(consensus::validate_vote_admission(
      policy,
      state,
      recovery_state,
      valid,
      1U,
      consensus::VoteAdmissionMode::recovery));
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        wrong_phase_policy,
        wrong_phase,
        recovery_state,
        valid,
        1U,
        consensus::VoteAdmissionMode::recovery));
  });
  recovery_state.logical_tick = policy.hard_deadline_tick;
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy,
        state,
        recovery_state,
        valid,
        1U,
        consensus::VoteAdmissionMode::recovery));
  });
  recovery_state = admission_state_for(policy);
  recovery_state.authority_invalidated = true;
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy,
        state,
        recovery_state,
        valid,
        1U,
        consensus::VoteAdmissionMode::recovery));
  });

  for (const auto seed_bound_action :
       {consensus::VoteAction::parameter, consensus::VoteAction::aggregate_root}) {
    const auto seed_state = state_for(seed_bound_action);
    auto missing_seed = policy_for(seed_bound_action);
    missing_seed.candidates.front().parents.seed_transcript_id.clear();
    expect_consensus_error(consensus::ErrorCode::identifier_invalid, [&] {
      consensus::validate_vote_admission_policy(missing_seed, seed_state);
    });
  }
}

void test_typed_vote_guard_adversarial_matrix() {
  const std::vector<consensus::VoteAction> actions{
      consensus::VoteAction::round_config,
      consensus::VoteAction::input_set,
      consensus::VoteAction::eligibility,
      consensus::VoteAction::aggregation_plan,
      consensus::VoteAction::parameter,
      consensus::VoteAction::aggregate_root,
      consensus::VoteAction::apply,
      consensus::VoteAction::view_change,
      consensus::VoteAction::abort,
  };
  for (const auto action : actions) {
    auto fixture = vote_fixture::full(action);

    auto arbitrary_context = fixture.policy;
    arbitrary_context.candidates.front().context_id += ":caller-selected";
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(arbitrary_context, fixture.state);
    });

    auto adversarial = fixture.policy;
    auto& candidate = adversarial.candidates.front();
    switch (action) {
      case consensus::VoteAction::round_config:
        adversarial.snapshot.proposed_round_config_ids.clear();
        break;
      case consensus::VoteAction::input_set:
        adversarial.snapshot.closed_input_set_ids.clear();
        break;
      case consensus::VoteAction::eligibility: {
        auto& body = adversarial.snapshot.eligibility_bodies.front();
        body.seed_transcript_id = content_id('f');
        candidate.body_hash = consensus::vote_eligibility_body_id(body);
        candidate.parents.seed_transcript_id = body.seed_transcript_id;
        break;
      }
      case consensus::VoteAction::aggregation_plan: {
        auto& body = adversarial.snapshot.aggregation_plan_bodies.front();
        body.accumulator_proof_id = content_id('e');
        candidate.body_hash = consensus::vote_aggregation_plan_body_id(body);
        break;
      }
      case consensus::VoteAction::parameter: {
        auto& body = adversarial.snapshot.parameter_bodies.front();
        body.shard_id = "shard-z";
        body.vote_context_id = "PARAMETER:domain-a:shard-z";
        candidate.body_hash = consensus::vote_parameter_body_id(body);
        candidate.context_id = body.vote_context_id;
        candidate.parents.shard_id = body.shard_id;
        break;
      }
      case consensus::VoteAction::aggregate_root: {
        auto& body = adversarial.snapshot.aggregate_root_bodies.front();
        body.leaves.clear();
        candidate.body_hash = consensus::vote_aggregate_root_body_id(body);
        break;
      }
      case consensus::VoteAction::apply: {
        auto& body = adversarial.snapshot.apply_candidates.front();
        body.parent_checkpoint_id = content_id('f');
        candidate.body_hash = delta::certificates::content_id(body);
        candidate.parents.apply_candidate_id = candidate.body_hash;
        break;
      }
      case consensus::VoteAction::view_change:
        adversarial.snapshot.timeout_observations.clear();
        break;
      case consensus::VoteAction::abort: {
        auto& body = adversarial.snapshot.abort_bodies.front();
        body.parent_checkpoint_id = content_id('f');
        candidate.body_hash = consensus::vote_abort_body_id(body);
        break;
      }
    }
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(adversarial, fixture.state);
    });
  }
}

void test_exact_parameter_assignment_and_abort_reason_guards() {
  {
    auto fixture = vote_fixture::full(consensus::VoteAction::parameter);
    auto aliased_assignment = fixture.policy.snapshot.parameter_bodies.front();
    aliased_assignment.result_numerators = {"2"};
    aliased_assignment.vote_context_id += ":alias";
    auto aliased_candidate = fixture.policy.candidates.front();
    aliased_candidate.body_hash = consensus::vote_parameter_body_id(aliased_assignment);
    aliased_candidate.context_id = aliased_assignment.vote_context_id;
    fixture.policy.snapshot.parameter_bodies.push_back(aliased_assignment);
    fixture.policy.candidates.push_back(std::move(aliased_candidate));
    std::sort(
        fixture.policy.snapshot.parameter_bodies.begin(),
        fixture.policy.snapshot.parameter_bodies.end(),
        [](const auto& left, const auto& right) {
          return consensus::vote_parameter_body_id(left) <
                 consensus::vote_parameter_body_id(right);
        });
    std::sort(
        fixture.policy.candidates.begin(),
        fixture.policy.candidates.end(),
        [](const auto& left, const auto& right) {
          return std::tie(left.height, left.view, left.action, left.context_id) <
                 std::tie(right.height, right.view, right.action, right.context_id);
        });
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
    });
  }

  {
    auto fixture = vote_fixture::full(consensus::VoteAction::parameter);
    auto distinct_assignment = fixture.policy.snapshot.parameter_bodies.front();
    distinct_assignment.shard_id = "shard-b";
    distinct_assignment.vote_context_id = "PARAMETER:domain-a:shard-b";
    auto distinct_candidate = fixture.policy.candidates.front();
    distinct_candidate.body_hash = consensus::vote_parameter_body_id(distinct_assignment);
    distinct_candidate.context_id = distinct_assignment.vote_context_id;
    distinct_candidate.parents.shard_id = distinct_assignment.shard_id;
    fixture.policy.snapshot.parameter_bodies.push_back(distinct_assignment);
    fixture.policy.snapshot.required_parameter_keys.push_back(
        {distinct_assignment.domain_id, distinct_assignment.shard_id});
    fixture.policy.candidates.push_back(std::move(distinct_candidate));
    std::sort(
        fixture.policy.snapshot.parameter_bodies.begin(),
        fixture.policy.snapshot.parameter_bodies.end(),
        [](const auto& left, const auto& right) {
          return consensus::vote_parameter_body_id(left) <
                 consensus::vote_parameter_body_id(right);
        });
    std::sort(
        fixture.policy.snapshot.required_parameter_keys.begin(),
        fixture.policy.snapshot.required_parameter_keys.end());
    std::sort(
        fixture.policy.candidates.begin(),
        fixture.policy.candidates.end(),
        [](const auto& left, const auto& right) {
          return std::tie(left.height, left.view, left.action, left.context_id) <
                 std::tie(right.height, right.view, right.action, right.context_id);
        });
    consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
  }

  const std::array<std::string_view, 6U> configured_reasons{
      "HARD_DEADLINE",
      "INCOMPLETE_INPUT",
      "UNSAFE_COEFFICIENTS",
      "IRRECOVERABLE_AVAILABILITY",
      "PARAMETER_FAILURE",
      "APPLY_FAILURE",
  };
  for (const auto reason : configured_reasons) {
    auto fixture = vote_fixture::full(consensus::VoteAction::abort);
    fixture.policy.configured_abort_reason = reason;
    auto& body = fixture.policy.snapshot.abort_bodies.front();
    body.reason_code = reason;
    fixture.policy.candidates.front().body_hash = consensus::vote_abort_body_id(body);
    fixture.policy.candidates.front().parents.reason_code = reason;
    consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
    const auto vote = vote_for(fixture.policy, fixture.policy.candidates.front());
    static_cast<void>(consensus::validate_vote_admission(
        fixture.policy,
        fixture.state,
        admission_state_for(fixture.policy),
        vote,
        1U));
  }

  for (const auto invalid_reason : {std::string_view("NO_ABORT"), std::string_view("UNKNOWN")}) {
    auto fixture = vote_fixture::full(consensus::VoteAction::abort);
    fixture.policy.configured_abort_reason = invalid_reason;
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
    });
  }

  {
    auto fixture = vote_fixture::full(consensus::VoteAction::abort);
    fixture.policy.configured_abort_reason = "APPLY_FAILURE";
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
    });
  }

  {
    auto fixture = vote_fixture::full(consensus::VoteAction::abort);
    fixture.policy.snapshot.abort_requests = {
        {fixture.policy.round_id, "HARD_DEADLINE"}};
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(fixture.policy, fixture.state);
    });
  }

  {
    auto fixture = vote_fixture::full(consensus::VoteAction::abort);
    fixture.policy.configured_abort_reason = "INCOMPLETE_INPUT";
    fixture.policy.initial_logical_tick = 10U;
    auto& body = fixture.policy.snapshot.abort_bodies.front();
    body.reason_code = fixture.policy.configured_abort_reason;
    fixture.policy.candidates.front().body_hash = consensus::vote_abort_body_id(body);
    fixture.policy.candidates.front().parents.reason_code = body.reason_code;
    fixture.policy.snapshot.abort_requests = {
        {fixture.policy.round_id, fixture.policy.configured_abort_reason}};
    const auto vote = vote_for(fixture.policy, fixture.policy.candidates.front());
    static_cast<void>(consensus::validate_vote_admission(
        fixture.policy,
        fixture.state,
        admission_state_for(fixture.policy),
        vote,
        1U));

    fixture.policy.snapshot.abort_requests = {
        {fixture.policy.round_id, "UNSAFE_COEFFICIENTS"}};
    expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
      static_cast<void>(consensus::validate_vote_admission(
          fixture.policy,
          fixture.state,
          admission_state_for(fixture.policy),
          vote,
          1U));
    });
  }
}

void test_exhaustive_vote_binding_and_deadline_guards() {
  using ParentField = std::string consensus::VoteParentState::*;
  const std::array<ParentField, 15> parent_fields{
      &consensus::VoteParentState::round_config_id,
      &consensus::VoteParentState::parent_checkpoint_id,
      &consensus::VoteParentState::input_set_certificate_id,
      &consensus::VoteParentState::seed_transcript_id,
      &consensus::VoteParentState::norm_evidence_id,
      &consensus::VoteParentState::eligibility_certificate_id,
      &consensus::VoteParentState::aggregation_plan_certificate_id,
      &consensus::VoteParentState::parameter_matrix_root,
      &consensus::VoteParentState::aggregate_root_certificate_id,
      &consensus::VoteParentState::apply_profile_id,
      &consensus::VoteParentState::apply_candidate_id,
      &consensus::VoteParentState::last_finalized_certificate_id,
      &consensus::VoteParentState::domain_id,
      &consensus::VoteParentState::shard_id,
      &consensus::VoteParentState::reason_code,
  };
  const std::array actions{
      consensus::VoteAction::round_config,
      consensus::VoteAction::input_set,
      consensus::VoteAction::eligibility,
      consensus::VoteAction::aggregation_plan,
      consensus::VoteAction::parameter,
      consensus::VoteAction::aggregate_root,
      consensus::VoteAction::apply,
      consensus::VoteAction::view_change,
      consensus::VoteAction::abort,
  };

  for (const auto action : actions) {
    const auto fixture = vote_fixture::full(action);
    const auto valid_vote = vote_for(fixture.policy, fixture.candidate);
    const auto valid_state = admission_state_for(fixture.policy);
    const auto expect_admission_rejected = [&](const protocol::Vote& vote) {
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(consensus::validate_vote_admission(
            fixture.policy, fixture.state, valid_state, vote, 1U));
      });
    };

    auto changed_vote = valid_vote;
    changed_vote.validator_id = "validator-2";
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    changed_vote.validator_epoch_id = content_id('0');
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    changed_vote.round_id = "round-foreign";
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    ++changed_vote.height;
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    ++changed_vote.view;
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    changed_vote.context_id += ":foreign";
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    changed_vote.body_hash = content_id('0');
    expect_admission_rejected(changed_vote);
    changed_vote = valid_vote;
    changed_vote.kind = std::string(consensus::vote_kind_name(
        action == consensus::VoteAction::round_config
            ? consensus::VoteAction::input_set
            : consensus::VoteAction::round_config));
    expect_admission_rejected(changed_vote);

    auto wrong_role = fixture.policy;
    wrong_role.role = static_cast<consensus::ValidatorRole>(2U);
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(wrong_role, fixture.state);
    });

    auto wrong_round = fixture.policy;
    wrong_round.round_id = "round-foreign";
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(wrong_round, fixture.state);
    });

    auto wrong_candidate_height = fixture.policy;
    ++wrong_candidate_height.candidates.front().height;
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(wrong_candidate_height, fixture.state);
    });
    auto wrong_candidate_view = fixture.policy;
    ++wrong_candidate_view.candidates.front().view;
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      consensus::validate_vote_admission_policy(wrong_candidate_view, fixture.state);
    });

    std::size_t required_parent_guard_count = 0U;
    std::size_t forbidden_parent_guard_count = 0U;
    for (const auto field : parent_fields) {
      auto changed_policy = fixture.policy;
      auto& value = changed_policy.candidates.front().parents.*field;
      const bool forbidden_extra = value.empty();
      value = value == content_id('0') ? content_id('1') : content_id('0');
      try {
        consensus::validate_vote_admission_policy(changed_policy, fixture.state);
        const auto vote = vote_for(changed_policy, changed_policy.candidates.front());
        static_cast<void>(consensus::validate_vote_admission(
            changed_policy, fixture.state, valid_state, vote, 1U));
        fail("wrong or forbidden typed vote parent was accepted");
      } catch (const consensus::ConsensusError& error) {
        expect(
            error.code() == consensus::ErrorCode::vote_policy_invalid ||
                error.code() == consensus::ErrorCode::vote_admission_rejected,
            "typed parent guard returned an unexpected error");
      }
      if (forbidden_extra) {
        ++forbidden_parent_guard_count;
      } else {
        ++required_parent_guard_count;
      }
    }
    expect(
        required_parent_guard_count + forbidden_parent_guard_count == parent_fields.size() &&
            required_parent_guard_count > 0U && forbidden_parent_guard_count > 0U,
        "typed required/forbidden parent guard matrix is incomplete");

    auto not_ready = valid_state;
    not_ready.recovery_ready = false;
    expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
      static_cast<void>(consensus::validate_vote_admission(
          fixture.policy, fixture.state, not_ready, valid_vote, 1U));
    });
    if (requires_unavailable_arithmetic_inputs(action)) {
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(consensus::validate_vote_admission(
            fixture.policy,
            fixture.state,
            not_ready,
            valid_vote,
            1U,
            consensus::VoteAdmissionMode::recovery));
      });
    } else {
      static_cast<void>(consensus::validate_vote_admission(
          fixture.policy,
          fixture.state,
          not_ready,
          valid_vote,
          1U,
          consensus::VoteAdmissionMode::recovery));
    }

    for (const auto mode :
         {consensus::VoteAdmissionMode::live, consensus::VoteAdmissionMode::recovery}) {
      auto invalidated = valid_state;
      invalidated.authority_invalidated = true;
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(consensus::validate_vote_admission(
            fixture.policy, fixture.state, invalidated, valid_vote, 1U, mode));
      });
    }

    const auto admit_at = [&](const consensus::VoteAdmissionPolicy& policy, std::uint64_t tick) {
      auto at_tick = admission_state_for(policy);
      at_tick.logical_tick = tick;
      return consensus::validate_vote_admission(
          policy, fixture.state, at_tick, valid_vote, 1U);
    };
    const auto reject_at = [&](const consensus::VoteAdmissionPolicy& policy, std::uint64_t tick) {
      auto at_tick = admission_state_for(policy);
      at_tick.logical_tick = tick;
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(consensus::validate_vote_admission(
            policy, fixture.state, at_tick, valid_vote, 1U));
      });
    };
    if (requires_unavailable_arithmetic_inputs(action)) {
      reject_at(fixture.policy, fixture.policy.initial_logical_tick);
      reject_at(fixture.policy, fixture.policy.soft_deadline_tick);
      reject_at(fixture.policy, fixture.policy.hard_deadline_tick - 1U);
    } else if (action == consensus::VoteAction::view_change) {
      expect(fixture.policy.soft_deadline_tick > 0U, "view soft deadline has no lower boundary");
      reject_at(fixture.policy, fixture.policy.soft_deadline_tick - 1U);
      static_cast<void>(admit_at(fixture.policy, fixture.policy.soft_deadline_tick));
      static_cast<void>(admit_at(fixture.policy, fixture.policy.hard_deadline_tick - 1U));
      reject_at(fixture.policy, fixture.policy.hard_deadline_tick);
    } else if (action == consensus::VoteAction::abort) {
      auto deadline_only = fixture.policy;
      deadline_only.snapshot.abort_requests.clear();
      reject_at(deadline_only, deadline_only.hard_deadline_tick - 1U);
      static_cast<void>(admit_at(deadline_only, deadline_only.hard_deadline_tick));
    } else {
      expect(fixture.policy.soft_deadline_tick > 0U, "ordinary soft deadline has no lower boundary");
      static_cast<void>(admit_at(fixture.policy, fixture.policy.soft_deadline_tick - 1U));
      static_cast<void>(admit_at(fixture.policy, fixture.policy.soft_deadline_tick));
      static_cast<void>(admit_at(fixture.policy, fixture.policy.hard_deadline_tick - 1U));
      reject_at(fixture.policy, fixture.policy.hard_deadline_tick);
    }
  }
}

void test_pre_qc_body_projection_excludes_quorum_material() {
  const auto isc = vote_fixture::full(consensus::VoteAction::input_set);
  const auto ec = vote_fixture::full(consensus::VoteAction::eligibility);
  auto input_qc = ec.policy.snapshot.input_set_certificates.front();
  expect(
      consensus::vote_input_set_body_id(
          consensus::project_input_set_vote_body(input_qc)) ==
          isc.candidate.body_hash,
      "ISC vote body does not project from its finalized certificate");
  expect(
      delta::certificates::content_id(input_qc) != isc.candidate.body_hash,
      "ISC vote incorrectly hashes the full signer-bearing certificate");
  input_qc.quorum_threshold = 1U;
  input_qc.signer_ids = {"untrusted-signer"};
  expect(
      consensus::vote_input_set_body_id(
          consensus::project_input_set_vote_body(input_qc)) ==
          isc.candidate.body_hash,
      "ISC proposal projection depends on quorum-only material");

  const auto apc = vote_fixture::full(consensus::VoteAction::aggregation_plan);
  const auto& finalized_ec =
      apc.policy.snapshot.eligibility_certificates.front();
  expect(
      consensus::vote_eligibility_body_id(
          consensus::project_eligibility_vote_body(
              finalized_ec.certificate,
              finalized_ec.seed_transcript_id)) == ec.candidate.body_hash,
      "EC vote body does not project from its finalized certificate");

  const auto parameter = vote_fixture::full(consensus::VoteAction::parameter);
  const auto& finalized_apc =
      parameter.policy.snapshot.aggregation_plan_certificates.front();
  expect(
      consensus::vote_aggregation_plan_body_id(
          consensus::project_aggregation_plan_vote_body(finalized_apc)) ==
          apc.candidate.body_hash,
      "APC vote body does not project from its finalized certificate");

  const auto root = vote_fixture::full(consensus::VoteAction::aggregate_root);
  const auto& parameter_qc = root.policy.snapshot.parameter_qcs.front();
  const auto parameter_a = consensus::project_parameter_vote_body(
      parameter_qc, "PARAMETER:domain-a:shard-a");
  const auto parameter_b = consensus::project_parameter_vote_body(
      parameter_qc, "another-assignment-context");
  expect(
      consensus::vote_parameter_body_id(parameter_a) ==
              parameter.candidate.body_hash &&
          consensus::vote_parameter_body_id(parameter_a) ==
              consensus::vote_parameter_body_id(parameter_b),
      "parameter body projection includes QC/context-only metadata");

  const auto apply = vote_fixture::full(consensus::VoteAction::apply);
  const auto& root_qc = apply.policy.snapshot.aggregate_root_qcs.front();
  expect(
      consensus::vote_aggregate_root_body_id(
          consensus::project_aggregate_root_vote_body(root_qc)) ==
          root.candidate.body_hash,
      "root vote body does not project from its finalized QC");
}

void test_candidate_context_order_and_multiplicity() {
  const auto state = state_for(consensus::VoteAction::parameter);
  auto policy = policy_for(consensus::VoteAction::parameter);
  auto root_fixture = vote_fixture::full(consensus::VoteAction::aggregate_root, state);
  policy.snapshot.parameter_qcs = root_fixture.policy.snapshot.parameter_qcs;
  policy.snapshot.finalized_parameter_ids =
      root_fixture.policy.snapshot.finalized_parameter_ids;
  policy.snapshot.aggregate_root_bodies =
      root_fixture.policy.snapshot.aggregate_root_bodies;
  auto second = std::move(root_fixture.candidate);
  policy.candidates.push_back(std::move(second));
  std::sort(
      policy.candidates.begin(),
      policy.candidates.end(),
      [](const auto& left, const auto& right) {
        return std::tuple{
                   left.height,
                   left.view,
                   static_cast<std::uint32_t>(left.action),
                   std::string_view(left.context_id)} <
               std::tuple{
                   right.height,
                   right.view,
                   static_cast<std::uint32_t>(right.action),
                   std::string_view(right.context_id)};
      });
  consensus::validate_vote_admission_policy(policy, state);
  const auto bound = std::find_if(
      policy.candidates.begin(), policy.candidates.end(), [](const auto& candidate) {
        return candidate.action == consensus::VoteAction::aggregate_root;
      });
  expect(bound != policy.candidates.end(), "second immutable round-contract binding is absent");
  const auto bound_vote = vote_for(policy, *bound);
  const auto admitted = consensus::validate_vote_admission(
      policy, state, admission_state_for(policy), bound_vote, 1U);
  expect(
      admitted.context_id == bound->context_id && admitted.parents == bound->parents,
      "native admission did not author context/parents from the selected frozen binding");
  auto wrong_action = bound_vote;
  wrong_action.kind = "PARAMETER";
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), wrong_action, 1U));
  });
  auto wrong_body = bound_vote;
  wrong_body.body_hash = policy.candidates.front().body_hash;
  if (wrong_body.body_hash == bound->body_hash) {
    wrong_body.body_hash = policy.candidates.back().body_hash;
  }
  expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
    static_cast<void>(consensus::validate_vote_admission(
        policy, state, admission_state_for(policy), wrong_body, 1U));
  });
  auto duplicate_context = policy;
  auto later_view = duplicate_context.candidates.front();
  ++later_view.view;
  duplicate_context.candidates.push_back(std::move(later_view));
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(duplicate_context, state);
  });
  std::reverse(policy.candidates.begin(), policy.candidates.end());
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(policy, state);
  });

  auto too_many_validators = policy_for(consensus::VoteAction::parameter);
  too_many_validators.validator_ids.resize(consensus::max_vote_validator_count + 1U);
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(too_many_validators, state);
  });
  auto too_many_candidates = policy_for(consensus::VoteAction::parameter);
  too_many_candidates.candidates.resize(consensus::max_vote_candidate_count + 1U);
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    consensus::validate_vote_admission_policy(too_many_candidates, state);
  });
}

consensus::QuorumPolicy f1_policy() {
  return consensus::QuorumPolicy{
      content_id('d'),
      {"validator-1", "validator-2", "validator-3", "validator-4"},
      3U,
  };
}

void test_exact_quorum_policy() {
  auto certificate = protocol::parse_quorum_certificate(golden(4U));
  const auto policy = f1_policy();
  consensus::validate_quorum(certificate, policy);

  auto unknown = certificate;
  unknown.signer_ids.back() = "validator-9";
  expect_consensus_error(consensus::ErrorCode::unknown_signer, [&unknown, &policy] {
    consensus::validate_quorum(unknown, policy);
  });

  auto wrong_threshold = policy;
  wrong_threshold.quorum_threshold = 2U;
  expect_consensus_error(
      consensus::ErrorCode::quorum_policy_mismatch, [&certificate, &wrong_threshold] {
        consensus::validate_quorum(certificate, wrong_threshold);
      });

  auto malformed = policy;
  malformed.validator_ids.pop_back();
  expect_consensus_error(consensus::ErrorCode::validator_set_invalid, [&certificate, &malformed] {
    consensus::validate_quorum(certificate, malformed);
  });
}

consensus::AvailabilityProof availability(
    std::string ticket_id,
    std::string commitment_id,
    char certificate_digit) {
  return consensus::AvailabilityProof{
      std::move(ticket_id),
      std::move(commitment_id),
      content_id(certificate_digit),
      {content_id('1'), content_id('2')},
      {"storage-1", "storage-2", "storage-3"},
      3U,
  };
}

void test_commitment_availability_and_freeze() {
  consensus::InputLedger ledger({"ticket-a", "ticket-b", "ticket-c"});
  const consensus::Commitment ticket_b{"ticket-b", content_id('b')};
  const consensus::Commitment ticket_a{"ticket-a", content_id('a')};
  expect(
      ledger.record_commitment(ticket_b) == consensus::Disposition::recorded,
      "ticket-b commitment rejected");
  expect(
      ledger.record_commitment(ticket_a) == consensus::Disposition::recorded,
      "ticket-a commitment rejected");
  expect(
      ledger.commitments().front().ticket_id == "ticket-a",
      "commitments are not stored in canonical ticket order");
  expect(
      ledger.record_commitment(ticket_a) == consensus::Disposition::replay,
      "exact commitment replay was not idempotent");

  auto conflicting = ticket_a;
  conflicting.commitment_id = content_id('c');
  expect_consensus_error(consensus::ErrorCode::commitment_equivocation, [&ledger, &conflicting] {
    static_cast<void>(ledger.record_commitment(conflicting));
  });
  const consensus::Commitment unknown{"ticket-z", content_id('f')};
  expect_consensus_error(consensus::ErrorCode::unknown_ticket, [&ledger, &unknown] {
    static_cast<void>(ledger.record_commitment(unknown));
  });

  const std::vector<std::string> leaves{content_id('1'), content_id('2')};
  const std::vector<std::string> attesters{"storage-1", "storage-2", "storage-3", "storage-4"};
  auto proof_a = availability("ticket-a", ticket_a.commitment_id, '3');
  expect(
      ledger.record_availability(proof_a, leaves, attesters, 3U) ==
          consensus::Disposition::recorded,
      "valid availability proof rejected");
  expect(
      ledger.record_availability(proof_a, leaves, attesters, 3U) ==
          consensus::Disposition::replay,
      "availability replay was not idempotent");

  const auto frozen = ledger.freeze();
  expect(frozen.size() == 1U && frozen.front().ticket_id == "ticket-a", "frozen input mismatch");
  expect(ledger.freeze() == frozen, "input freeze replay changed the frozen set");

  const consensus::Commitment late{"ticket-c", content_id('c')};
  expect(
      ledger.record_commitment(late) == consensus::Disposition::late,
      "late commitment was not classified as late");
  expect(ledger.late_commitment_count() == 1U, "late commitment evidence was not retained");

  auto proof_b = availability("ticket-b", ticket_b.commitment_id, '4');
  expect(
      ledger.record_availability(proof_b, leaves, attesters, 3U) ==
          consensus::Disposition::late,
      "late availability was not classified as late");
  expect(ledger.late_availability_count() == 1U, "late availability evidence was not retained");
  expect(ledger.frozen_inputs() == frozen, "late evidence changed frozen inputs");
}

void test_availability_fails_closed() {
  consensus::InputLedger ledger({"ticket-a"});
  const consensus::Commitment commitment{"ticket-a", content_id('a')};
  static_cast<void>(ledger.record_commitment(commitment));
  const std::vector<std::string> leaves{content_id('1'), content_id('2')};
  const std::vector<std::string> attesters{"storage-1", "storage-2", "storage-3"};

  auto incomplete = availability("ticket-a", commitment.commitment_id, '3');
  incomplete.covered_leaf_ids.pop_back();
  expect_consensus_error(
      consensus::ErrorCode::availability_coverage_incomplete,
      [&ledger, &incomplete, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(incomplete, leaves, attesters, 3U));
      });

  auto insufficient = availability("ticket-a", commitment.commitment_id, '3');
  insufficient.attester_ids.pop_back();
  expect_consensus_error(
      consensus::ErrorCode::availability_attesters_invalid,
      [&ledger, &insufficient, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(insufficient, leaves, attesters, 3U));
      });

  auto wrong_threshold = availability("ticket-a", commitment.commitment_id, '3');
  wrong_threshold.threshold = 1U;
  expect_consensus_error(
      consensus::ErrorCode::availability_attesters_invalid,
      [&ledger, &wrong_threshold, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(wrong_threshold, leaves, attesters, 3U));
      });

  auto wrong_parent = availability("ticket-a", content_id('b'), '3');
  expect_consensus_error(
      consensus::ErrorCode::availability_commitment_mismatch,
      [&ledger, &wrong_parent, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(wrong_parent, leaves, attesters, 3U));
      });

  consensus::InputLedger empty({"ticket-a"});
  expect_consensus_error(consensus::ErrorCode::input_set_empty, [&empty] {
    static_cast<void>(empty.freeze());
  });
}

}  // namespace

int main() {
  try {
    test_durable_vote_uniqueness();
    test_closed_vote_admission_matrix();
    test_typed_vote_guard_adversarial_matrix();
    test_exact_parameter_assignment_and_abort_reason_guards();
    test_exhaustive_vote_binding_and_deadline_guards();
    test_pre_qc_body_projection_excludes_quorum_material();
    test_candidate_context_order_and_multiplicity();
    test_exact_quorum_policy();
    test_commitment_availability_and_freeze();
    test_availability_fails_closed();
  } catch (const std::exception& error) {
    std::cerr << "delta_core consensus test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core consensus tests passed\n";
  return 0;
}
