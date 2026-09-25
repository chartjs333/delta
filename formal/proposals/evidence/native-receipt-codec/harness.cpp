#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <iomanip>
#include <iostream>
using namespace delta::core::consensus;
namespace ca=delta::core::canonical;
namespace pr=delta::core::protocol;
namespace rt=delta::runtime;
using Bytes=ca::Bytes;
std::string hex(const Bytes& b){constexpr char d[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);
 s.push_back(d[n&15U]);}return s;}
int main(){
 for(unsigned action=1;action<=9;++action){
  const auto a=static_cast<VoteAction>(action);
  const auto f=delta::test::vote_fixture::full(a);
  const auto frame=pr::encode(f.vote);
  rt::VoteReceipt r{frame,ca::content_id(ca::Type::vote,frame),f.vote.durable_sequence,
   a,std::string(vote_formal_action_id(a)),f.vote.context_id,f.policy.candidates[0].parents,false};
  const auto bytes=rt::encode_vote_receipt_v1(r);
  r.replay=true;
  if(rt::encode_vote_receipt_v1(r)!=bytes)throw std::runtime_error("replay changed bytes");
  const auto decoded=rt::parse_vote_receipt_v1(bytes);
  if(decoded.frame!=frame || decoded.replay || decoded.action!=a ||
    decoded.journal_sequence!=r.journal_sequence || decoded.vote_id!=r.vote_id ||
    decoded.context_id!=r.context_id)throw std::runtime_error("native codec roundtrip");
  unsigned rejected=0;
  auto changed=bytes;changed[20]=std::byte{1};
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){++rejected;}
  changed=bytes;changed.push_back(std::byte{0});
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){++rejected;}
  // Structural receipt fields remain valid, but native ID-to-frame validation fails.
  changed=bytes;changed[36+frame.size()+4+7]=std::byte{'0'};
  if(changed==bytes)changed[36+frame.size()+4+7]=std::byte{'1'};
  bool hashRejected=false;
  try{static_cast<void>(rt::parse_vote_receipt_v1(changed));}
  catch(const std::invalid_argument&){hashRejected=true;}
  if(rejected!=2 || !hashRejected)throw std::runtime_error("native invalid receipt accepted");
  std::cout<<"{\"action\":"<<action<<",\"receipt_hex\":"<<std::quoted(hex(bytes))
    <<",\"frame_hex\":"<<std::quoted(hex(frame))<<",\"replay_equal\":true,\"rejected\":"<<rejected
    <<",\"hash_mismatch_hex\":"<<std::quoted(hex(changed))<<",\"hash_mismatch_rejected\":true}\n";
 }
}
