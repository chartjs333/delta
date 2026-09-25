#include <delta/certificates/contracts.hpp>
#include <bit>
#include <iostream>
namespace delta::core::consensus {
struct VoteInputSetBody {
  certificates::Context context;
  std::string input_root;
  std::vector<certificates::InputTuple> tuples;

  bool operator==(const VoteInputSetBody&) const = default;
};
struct VoteEligibilityBody {
  certificates::Context context;
  std::vector<certificates::EligibilityEntry> entries;
  std::string input_set_certificate_id;
  std::string norm_evidence_id;
  std::string robust_profile_id;
  std::string seed_transcript_id;

  bool operator==(const VoteEligibilityBody&) const = default;
};
struct VoteAggregationPlanBody {
  certificates::Context context;
  std::string accumulator_proof_id;
  std::vector<certificates::BucketAssignment> bucket_assignments;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::uint32_t iteration_count;
  std::string seed_transcript_id;
  std::string transcript_root;
  std::vector<certificates::Weight> weights;

  bool operator==(const VoteAggregationPlanBody&) const = default;
};
struct VoteAggregateRootBody {
  certificates::Context context;
  std::string aggregation_plan_certificate_id;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::vector<certificates::RootLeaf> leaves;
  std::string merkle_root;
  std::vector<certificates::ShardKey> required_keys;

  bool operator==(const VoteAggregateRootBody&) const = default;
};
void append_hash_text(core::canonical::Bytes& output, std::string_view value) {
  const auto length = static_cast<std::uint64_t>(value.size());
  for (std::size_t offset = sizeof(length); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((length >> shift) & 0xffU));
  }
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  output.insert(output.end(), bytes.begin(), bytes.end());
}
void append_hash_u64(core::canonical::Bytes& output, std::uint64_t value) {
  for (std::size_t offset = sizeof(value); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & 0xffU));
  }
}
void append_hash_bool(core::canonical::Bytes& output, bool value) {
  output.push_back(value ? std::byte{1U} : std::byte{0U});
}
void append_hash_context(
    core::canonical::Bytes& output,
    const certificates::Context& value) {
  append_hash_text(output, value.arithmetic_profile_id);
  append_hash_u64(output, value.height);
  append_hash_text(output, value.parameter_schema_id);
  append_hash_text(output, value.round_config_id);
  append_hash_text(output, value.round_id);
  append_hash_text(output, value.validator_epoch_id);
  append_hash_u64(output, value.view);
}
void append_hash_rational(
    core::canonical::Bytes& output,
    const certificates::Rational& value) {
  append_hash_u64(output, std::bit_cast<std::uint64_t>(value.numerator));
  append_hash_u64(output, value.denominator);
}
void append_hash_input_tuples(
    core::canonical::Bytes& output,
    const std::vector<certificates::InputTuple>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.availability_certificate_id);
    append_hash_text(output, value.commitment_id);
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.ticket_id);
  }
}
void append_hash_eligibility_entries(
    core::canonical::Bytes& output,
    const std::vector<certificates::EligibilityEntry>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_bool(output, value.accepted);
    append_hash_text(output, value.domain_id);
    append_hash_rational(output, value.gamma);
    append_hash_text(output, value.reason_code);
    append_hash_text(output, value.ticket_id);
  }
}
void append_hash_bucket_assignments(
    core::canonical::Bytes& output,
    const std::vector<certificates::BucketAssignment>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.bucket_id);
    append_hash_text(output, value.ticket_id);
  }
}
void append_hash_weights(
    core::canonical::Bytes& output,
    const std::vector<certificates::Weight>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_rational(output, value.alpha);
    append_hash_text(output, value.ticket_id);
  }
}
void append_hash_root_leaves(
    core::canonical::Bytes& output,
    const std::vector<certificates::RootLeaf>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.parameter_shard_qc_id);
    append_hash_text(output, value.shard_id);
  }
}
void append_hash_shard_keys(
    core::canonical::Bytes& output,
    const std::vector<certificates::ShardKey>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.shard_id);
  }
}
[[nodiscard]] std::string authority_content_id(
    std::string_view domain,
    const core::canonical::Bytes& body) {
  core::canonical::Bytes input;
  input.reserve(domain.size() + 1U + body.size());
  const auto domain_bytes = std::as_bytes(std::span(domain.data(), domain.size()));
  input.insert(input.end(), domain_bytes.begin(), domain_bytes.end());
  input.push_back(std::byte{0U});
  input.insert(input.end(), body.begin(), body.end());
  return "sha256:" + core::canonical::sha256_hex(input);
}
VoteInputSetBody project_input_set_vote_body(
    const certificates::InputSetCertificate& certificate) {
  return VoteInputSetBody{
      certificate.context,
      certificate.input_root,
      certificate.tuples,
  };
}
VoteEligibilityBody project_eligibility_vote_body(
    const certificates::EligibilityCertificate& certificate,
    std::string seed_transcript_id) {
  return VoteEligibilityBody{
      certificate.context,
      certificate.entries,
      certificate.input_set_certificate_id,
      certificate.norm_evidence_id,
      certificate.robust_profile_id,
      std::move(seed_transcript_id),
  };
}
VoteAggregationPlanBody project_aggregation_plan_vote_body(
    const certificates::AggregationPlanCertificate& certificate) {
  return VoteAggregationPlanBody{
      certificate.context,
      certificate.accumulator_proof_id,
      certificate.bucket_assignments,
      certificate.eligibility_certificate_id,
      certificate.input_set_certificate_id,
      certificate.iteration_count,
      certificate.seed_transcript_id,
      certificate.transcript_root,
      certificate.weights,
  };
}
VoteAggregateRootBody project_aggregate_root_vote_body(
    const certificates::AggregateRootQc& certificate) {
  return VoteAggregateRootBody{
      certificate.context,
      certificate.aggregation_plan_certificate_id,
      certificate.eligibility_certificate_id,
      certificate.input_set_certificate_id,
      certificate.leaves,
      certificate.merkle_root,
      certificate.required_keys,
  };
}
std::string vote_input_set_body_id(const VoteInputSetBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.input_root);
  append_hash_input_tuples(encoded, body.tuples);
  return authority_content_id("deltareduce.vote.input-set-body.v1", encoded);
}
std::string vote_eligibility_body_id(const VoteEligibilityBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_eligibility_entries(encoded, body.entries);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_text(encoded, body.norm_evidence_id);
  append_hash_text(encoded, body.robust_profile_id);
  append_hash_text(encoded, body.seed_transcript_id);
  return authority_content_id("deltareduce.vote.eligibility-body.v1", encoded);
}
std::string vote_aggregation_plan_body_id(const VoteAggregationPlanBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.accumulator_proof_id);
  append_hash_bucket_assignments(encoded, body.bucket_assignments);
  append_hash_text(encoded, body.eligibility_certificate_id);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_u64(encoded, body.iteration_count);
  append_hash_text(encoded, body.seed_transcript_id);
  append_hash_text(encoded, body.transcript_root);
  append_hash_weights(encoded, body.weights);
  return authority_content_id("deltareduce.vote.aggregation-plan-body.v1", encoded);
}
std::string vote_aggregate_root_body_id(const VoteAggregateRootBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.aggregation_plan_certificate_id);
  append_hash_text(encoded, body.eligibility_certificate_id);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_root_leaves(encoded, body.leaves);
  append_hash_text(encoded, body.merkle_root);
  append_hash_shard_keys(encoded, body.required_keys);
  return authority_content_id("deltareduce.vote.aggregate-root-body.v1", encoded);
}
}

using namespace delta::certificates;
using namespace delta::core::consensus;
std::string id(char c) {return "sha256:"+std::string(64,c);}
template<class T> void emit(const char* name,const T& value) {
 const auto raw=canonical_json(value);const char* hex="0123456789abcdef";
 std::cout<<"CERT\t"<<name<<'\t'<<content_id(value)<<'\t';
 for(auto x:raw){auto n=std::to_integer<unsigned>(x);std::cout<<hex[n>>4]<<hex[n&15];}
 std::cout<<'\n';
}
template<class F> void rejects(const char* name,F fn) {
 try {fn();throw std::runtime_error("expected rejection missing");}
 catch(const CertificateError&) {std::cout<<"REJECT\t"<<name<<'\n';}
}
int main() {
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const SeedTranscript seed{c,isc,id('9'),id('a'),{id('b')}};const auto sid=content_id(seed);
 const NormEvidence norm{c,{{1,"1","ticket-a"}},isc,id('c')};const auto nid=content_id(norm);
 const EligibilityCertificate ec{c,
 {{true,"domain-a",{1,1},"ACCEPTED","ticket-a"}},isc,nid,3,id('e'),signers};
 const auto eid=content_id(ec);
 const AggregationPlanCertificate plan{c,id('f'),{{"bucket-a","ticket-a"}},
 eid,isc,1,3,sid,signers,id('0'),{{{1,1},"ticket-a"}}};const auto pid=content_id(plan);
 const ParameterShardQc parameter{c,pid,1,"domain-a",eid,{id('1')},isc,3,
 {"1"},"shard-a",signers};const auto qid=content_id(parameter);
 const std::vector<RootLeaf> leaves{{"domain-a",qid,"shard-a"}};
 const AggregateRootQc root{c,pid,eid,isc,leaves,aggregate_merkle_root(leaves),3,
 {{"domain-a","shard-a"}},signers};
 emit("ISC",input);emit("SEED",seed);emit("NORM",norm);emit("EC",ec);
 emit("APC",plan);emit("PARAMETER",parameter);emit("ROOT",root);
 std::cout<<"BODY\tISC\t"<<vote_input_set_body_id(project_input_set_vote_body(input))<<'\n';
 std::cout<<"BODY\tEC\t"<<vote_eligibility_body_id(project_eligibility_vote_body(ec,sid))<<'\n';
 std::cout<<"BODY\tAPC\t"<<vote_aggregation_plan_body_id(project_aggregation_plan_vote_body(plan))<<'\n';
 std::cout<<"BODY\tROOT\t"<<vote_aggregate_root_body_id(project_aggregate_root_vote_body(root))<<'\n';
 auto altered=input;altered.signer_ids.back()="validator-4";
 std::cout<<"VARIANT\talternate_signer_qc\t"<<content_id(altered)<<'\n';
 std::cout<<"VARIANT\talternate_signer_body\t"
 <<vote_input_set_body_id(project_input_set_vote_body(altered))<<'\n';
 std::cout<<"VARIANT\talternate_seed_body\t"
 <<vote_eligibility_body_id(project_eligibility_vote_body(ec,id('9')))<<'\n';
 for(int n=1;n<=4;++n){std::vector<RootLeaf> more;
 for(int i=0;i<n;++i)more.push_back(
 {"domain-a",id(static_cast<char>('1'+i)),"shard-"+std::to_string(i)});
 std::cout<<"MERKLE\t"<<n<<'\t'<<aggregate_merkle_root(more)<<'\n';}
 rejects("empty-input",[&]{auto bad=input;bad.tuples.clear();static_cast<void>(content_id(bad));});
 rejects("duplicate-signer",[&]{auto bad=input;bad.signer_ids[1]=bad.signer_ids[0];
 static_cast<void>(content_id(bad));});
 rejects("invalid-root",[&]{auto bad=input;bad.input_root="invalid";
 static_cast<void>(content_id(bad));});
 rejects("wrong-merkle",[&]{auto bad=root;bad.merkle_root=id('0');
 static_cast<void>(content_id(bad));});
 rejects("duplicate-leaf",[&]{auto bad=root;bad.leaves.push_back(bad.leaves[0]);
 static_cast<void>(content_id(bad));});
}
