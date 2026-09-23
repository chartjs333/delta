#pragma once

#include <delta/certificates/contracts.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace delta::test::vote_fixture {

inline std::string id(char digit) { return "sha256:" + std::string(64U, digit); }

inline std::vector<std::string> validators() {
  return {"validator-1", "validator-2", "validator-3", "validator-4"};
}

inline std::vector<std::string> signers() {
  return {"validator-1", "validator-2", "validator-3"};
}

inline core::protocol::RoundPhase phase_for(core::consensus::VoteAction action) {
  switch (action) {
    case core::consensus::VoteAction::round_config:
      return core::protocol::RoundPhase::ticketing_open;
    case core::consensus::VoteAction::input_set:
      return core::protocol::RoundPhase::available;
    case core::consensus::VoteAction::eligibility:
    case core::consensus::VoteAction::aggregation_plan:
    case core::consensus::VoteAction::parameter:
    case core::consensus::VoteAction::aggregate_root:
    case core::consensus::VoteAction::apply:
    case core::consensus::VoteAction::view_change:
    case core::consensus::VoteAction::abort:
      return core::protocol::RoundPhase::eligible;
  }
  return core::protocol::RoundPhase::aborted;
}

inline core::protocol::RoundState state_for(core::consensus::VoteAction action) {
  return core::protocol::RoundState{
      .available_ticket_count = 1U,
      .committed_ticket_count = 1U,
      .config_id = id('1'),
      .durable_sequence = 0U,
      .height = 1U,
      .parent_checkpoint_id = id('2'),
      .phase = phase_for(action),
      .round_id = "round-vote-fixture",
      .state_root = id('3'),
      .ticket_count = 1U,
      .view = 0U,
  };
}

struct Fixture {
  core::protocol::RoundState state;
  core::consensus::VoteAdmissionPolicy policy;
  core::consensus::VoteCandidateBinding candidate;
  core::protocol::Vote vote;
};

Fixture full(
    core::consensus::VoteAction action,
    core::protocol::RoundState state);


inline Fixture full(core::consensus::VoteAction action) {
  return full(action, state_for(action));
}

core::consensus::VoteAdmissionPolicy round_config_policy(
    const core::protocol::RoundState& state,
    const core::protocol::Vote& vote);

}  // namespace delta::test::vote_fixture
