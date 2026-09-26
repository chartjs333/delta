
#include <delta/core/consensus.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <iostream>
#include <string>
#include <sstream>
using namespace delta::core::consensus;
namespace pr=delta::core::protocol;
using Bytes=delta::core::canonical::Bytes;
Bytes unhex(const std::string& s){Bytes b;for(std::size_t i=0;i<s.size();i+=2)
 b.push_back(static_cast<std::byte>(std::stoul(s.substr(i,2),nullptr,16)));return b;}
int main(){std::string line;while(std::getline(std::cin,line)){
 std::istringstream in(line);std::string p,s,v;std::uint64_t tick=0,seq=0;
 bool ready=false,invalid=false,recovery=false;
 in>>p>>s>>v>>tick>>seq>>ready>>invalid>>recovery;bool startup=false,admitted=false;
 try{auto policy=delta::runtime::parse_vote_policy_v1(unhex(p));
 auto state=pr::parse_round_state(unhex(s));
 validate_vote_admission_policy(policy,state);startup=true;
 auto vote=pr::parse_vote(unhex(v));
 static_cast<void>(validate_vote_admission(policy,state,VoteAdmissionState{tick,ready,invalid},vote,seq,
 recovery?VoteAdmissionMode::recovery:VoteAdmissionMode::live));admitted=true;
 }catch(const std::exception&){}
 std::cout<<"{\"startup\":"<<(startup?"true":"false")<<",\"admitted\":"<<(admitted?"true":"false")<<"}\n";
}}
