#include "vote_fixture.hpp"
#include <algorithm>
#include <iostream>
#include <stdexcept>

using namespace delta;
using namespace core::consensus;
using namespace test::vote_fixture;

std::string hex(const core::canonical::Bytes& bytes) {
  constexpr char digits[] = "0123456789abcdef";
  std::string result;
  for (auto byte : bytes) {
    const auto value = std::to_integer<unsigned int>(byte);
    result.push_back(digits[value >> 4U]);
    result.push_back(digits[value & 15U]);
  }
  return result;
}

int main() {
  try {
    auto f = full(VoteAction::eligibility);
    auto& s = f.policy.snapshot;
    const auto input1 = s.input_set_certificates.front();
    auto input2 = input1;
    input2.signer_ids = {"validator-1", "validator-2", "validator-4"};
    const auto i1 = certificates::content_id(input1);
    const auto i2 = certificates::content_id(input2);
    const auto ib1 = vote_input_set_body_id(project_input_set_vote_body(input1));
    const auto ib2 = vote_input_set_body_id(project_input_set_vote_body(input2));
    if (i1 == i2 || ib1 != ib2 ||
        project_input_set_vote_body(input1) != project_input_set_vote_body(input2))
      throw std::runtime_error("bad diagnostic setup");
    auto seed2 = s.seed_transcripts.front();
    seed2.input_set_certificate_id = i2;
    auto norm2 = s.norm_evidence.front();
    norm2.input_set_certificate_id = i2;
    auto body2 = s.eligibility_bodies.front();
    body2.input_set_certificate_id = i2;
    body2.seed_transcript_id = certificates::content_id(seed2);
    body2.norm_evidence_id = certificates::content_id(norm2);
    s.input_set_certificates.push_back(input2);
    s.finalized_input_set_ids.push_back(i2);
    s.seed_transcripts.push_back(seed2);
    s.norm_evidence.push_back(norm2);
    s.eligibility_bodies.push_back(body2);
    const auto contentLess = [](const auto& a, const auto& b) {
      return certificates::content_id(a) < certificates::content_id(b);
    };
    std::sort(s.input_set_certificates.begin(), s.input_set_certificates.end(), contentLess);
    std::sort(s.finalized_input_set_ids.begin(), s.finalized_input_set_ids.end());
    std::sort(s.seed_transcripts.begin(), s.seed_transcripts.end(), contentLess);
    std::sort(s.norm_evidence.begin(), s.norm_evidence.end(), contentLess);
    std::sort(s.eligibility_bodies.begin(), s.eligibility_bodies.end(), [](const auto& a, const auto& b) {
      return vote_eligibility_body_id(a) < vote_eligibility_body_id(b);
    });
    auto candidate2 = f.candidate;
    candidate2.body_hash = vote_eligibility_body_id(body2);
    candidate2.parents.input_set_certificate_id = i2;
    candidate2.parents.seed_transcript_id = body2.seed_transcript_id;
    candidate2.parents.norm_evidence_id = body2.norm_evidence_id;
    candidate2.context_id = vote_context_id(VoteAction::eligibility, f.state.round_id,
      f.state.height, f.state.view, f.policy.validator_epoch_id, i2);
    f.policy.candidates.push_back(candidate2);
    std::sort(f.policy.candidates.begin(), f.policy.candidates.end(), [](const auto& a, const auto& b) {
      return a.context_id < b.context_id;
    });
    f.vote.durable_sequence = 2U;
    auto vote2 = f.vote;
    vote2.context_id = candidate2.context_id;
    vote2.body_hash = candidate2.body_hash;
    vote2.durable_sequence = 3U;
    vote2.signature_id = id('f');
    validate_vote_admission_policy(f.policy, f.state);
    VoteAdmissionState a{f.policy.initial_logical_tick, true, false};
    const auto admitted1 = validate_vote_admission(f.policy, f.state, a, f.vote, 2U);
    const auto admitted2 = validate_vote_admission(f.policy, f.state, a, vote2, 3U);
    VoteJournal journal;
    std::vector<core::protocol::Vote> prior;
    for (const auto& actor : validators()) {
      auto original = full(VoteAction::input_set);
      original.policy.local_validator_id = actor;
      original.vote.validator_id = actor;
      original.vote.signature_id = id(static_cast<char>('a' + prior.size()));
      if (original.vote.body_hash != ib1) throw std::runtime_error("prior ISC body changed");
      validate_vote_admission_policy(original.policy, original.state);
      const auto admitted = validate_vote_admission(original.policy, original.state, a, original.vote, 1U);
      if (admitted.action != VoteAction::input_set) throw std::runtime_error("prior action changed");
      prior.push_back(original.vote);
      if (actor == f.vote.validator_id && journal.record(original.vote) != Disposition::recorded)
        throw std::runtime_error("prior local ISC vote missing");
    }
    const auto recorded1 = journal.record(f.vote);
    const auto recorded2 = journal.record(vote2);
    if (recorded1 != Disposition::recorded || recorded2 != Disposition::recorded ||
        journal.votes().size() != 3U || admitted1.context_id == admitted2.context_id)
      throw std::runtime_error("two original votes not recorded");
    std::cout << "{\"policy\":\"ACCEPT\",\"vote1\":\"ACCEPT\",\"vote2\":\"ACCEPT\","
      << "\"journal_size\":3,\"isc_body\":\"" << ib1 << "\",\"isc_qc1\":\"" << i1
      << "\",\"isc_qc2\":\"" << i2 << "\",\"ec_context1\":\"" << f.vote.context_id
      << "\",\"ec_context2\":\"" << vote2.context_id << "\",\"ec_body1\":\"" << f.vote.body_hash
      << "\",\"ec_body2\":\"" << vote2.body_hash << "\",\"sequences\":[2,3],"
      << "\"state_hex\":\"" << hex(core::protocol::encode(f.state)) << "\","
      << "\"ec_vote_hex\":[\"" << hex(core::protocol::encode(f.vote)) << "\",\""
      << hex(core::protocol::encode(vote2)) << "\"],\"prior_isc_vote_hex\":[";
    bool first = true;
    for (const auto& vote : prior) {
      if (!first) std::cout << ',';
      first = false;
      std::cout << '\"' << hex(core::protocol::encode(vote)) << '\"';
    }
    std::cout << "]}\n";
  } catch (const std::exception& e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
