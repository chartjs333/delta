
#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
using namespace delta::test::vote_fixture;
using namespace delta::core::consensus;
namespace rt=delta::runtime;
namespace ca=delta::core::canonical;
namespace pr=delta::core::protocol;
using Bytes=ca::Bytes;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string hex(const Bytes& b){constexpr char d[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);s.push_back(d[n&15U]);}
 return s;}
Bytes file(const std::filesystem::path& p){
 if(!std::filesystem::exists(p))return {};
 std::ifstream in(p,std::ios::binary);Bytes b;char c;
 while(in.get(c))b.push_back(static_cast<std::byte>(static_cast<unsigned char>(c)));
 if(!in.eof())throw std::runtime_error("harness file read");return b;}
void bindState(Fixture& f){
 f.policy.snapshot.state_id=ca::content_id(ca::Type::round_state,pr::encode(f.state));}
void bindBody(Fixture& f){
 const auto body=vote_input_set_body_id(f.policy.snapshot.input_set_bodies[0]);
 f.policy.snapshot.closed_input_set_ids={body};f.policy.candidates[0].body_hash=body;
 f.vote.body_hash=body;}
rt::Config config(const std::filesystem::path& p,const Fixture& f){
 rt::Config c;c.directory=p;c.initial_state_bytes=pr::encode(f.state);
 // Exercise the actual operational decoder at every open.
 c.vote_policy=rt::parse_vote_policy_v1(rt::encode_vote_policy_v1(f.policy));return c;}
struct Outcome{std::string type,code,message;};
template<class F> Outcome capture(F f){
 try{f();return {"ACCEPT","",""};}
 catch(const rt::RuntimeError& e){
 return {"RUNTIME_REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
 catch(const ConsensusError& e){
 return {"ADMISSION_REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
 catch(const std::invalid_argument& e){return {"CODEC_REJECT","",e.what()};}
}
void out(const Outcome& o){std::cout<<"{\"status\":";q(o.type);std::cout<<",\"code\":";
 q(o.code);std::cout<<",\"message\":";q(o.message);std::cout<<'}';}
void emit(const std::string& name,const std::filesystem::path& dir,const Fixture& f,
 const Outcome& o,const Bytes& proof={},std::uint64_t seq=0U,
 std::size_t count=0U,bool replay=false){
 std::cout<<"{\"name\":";q(name);std::cout<<",\"outcome\":";out(o);
 std::cout<<",\"policy_hex\":";q(hex(rt::encode_vote_policy_v1(f.policy)));
 std::cout<<",\"initial_state_hex\":";q(hex(pr::encode(f.state)));
 std::cout<<",\"receipt_hex\":";q(hex(proof));std::cout<<",\"sequence\":"<<seq;
 std::cout<<",\"recovered_votes\":"<<count<<",\"replay\":"<<(replay?"true":"false");
 std::cout<<",\"wal_hex\":";q(hex(file(dir/"runtime.wal")));
 std::cout<<",\"snapshot_hex\":";q(hex(file(dir/"runtime.snapshot")));std::cout<<"}\n";
}
Bytes checkedReceipt(const rt::VoteReceipt& r){
 auto b=rt::encode_vote_receipt_v1(r);auto parsed=rt::parse_vote_receipt_v1(b);
 if(parsed.frame!=r.frame||parsed.vote_id!=r.vote_id||parsed.journal_sequence!=r.journal_sequence
 ||parsed.context_id!=r.context_id||parsed.action!=r.action||parsed.replay)
 throw std::runtime_error("receipt codec mismatch");return b;}
void codec(VoteAction action){
 auto f=full(action);auto b=rt::encode_vote_policy_v1(f.policy);
 auto p=rt::parse_vote_policy_v1(b);
 if(rt::encode_vote_policy_v1(p)!=b)throw std::runtime_error("policy reencode");
 std::size_t truncated=0U;
 if(action==VoteAction::input_set){for(std::size_t n=0;n<b.size();++n){
 auto status=capture([&]{static_cast<void>(rt::parse_vote_policy_v1(
 std::span<const std::byte>(b).first(n)));});
 if(status.type!="CODEC_REJECT")throw std::runtime_error("truncated policy accepted");++truncated;}}
 std::cout<<"{\"name\":";q("codec-"+std::string(vote_kind_name(action)));
 std::cout<<",\"policy_hex\":";q(hex(b));std::cout<<",\"sha256\":";q(ca::sha256_hex(b));
 std::cout<<",\"roundtrip\":true,\"truncated_rejections\":"<<truncated<<"}\n";
}
void malformed(){
 auto f=full(VoteAction::input_set);auto raw=rt::encode_vote_policy_v1(f.policy);
 std::vector<Bytes> cases;
 auto b=raw;b[0]=std::byte{'X'};cases.push_back(b);
 b=raw;b[9]=std::byte{2};cases.push_back(b);
 b=raw;b[15]=std::byte{1};cases.push_back(b);
 b=raw;b.push_back(std::byte{0});cases.push_back(b);
 b=Bytes(rt::max_vote_policy_v1_bytes+1U);cases.push_back(b);
 std::size_t i=0;
 for(const auto& item:cases){
 auto o=capture([&]{static_cast<void>(rt::parse_vote_policy_v1(item));});
 std::cout<<"{\"name\":";q("malformed-"+std::to_string(i++));std::cout<<",\"outcome\":";
 out(o);std::cout<<"}\n";}
}
void basic(const std::filesystem::path& dir){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 {
 auto c=config(dir,f);rt::Runtime runtime(c);
 // Caller mutation after construction cannot alter the by-value runtime policy.
 c.vote_policy->hard_deadline_tick=0U;
 rt::VoteReceipt result{};
 auto o=capture([&]{result=runtime.record_vote(vote);});
 emit("record",dir,f,o,checkedReceipt(result),runtime.journal_sequence(),
 runtime.recovered_vote_count(),result.replay);
 o=capture([&]{result=runtime.record_vote(vote);});
 emit("retry",dir,f,o,checkedReceipt(result),runtime.journal_sequence(),
 runtime.recovered_vote_count(),result.replay);
 auto conflict=f.vote;conflict.body_hash=id('f');conflict.durable_sequence=2U;
 o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(conflict)));});
 emit("conflict",dir,f,o,{},runtime.journal_sequence(),runtime.recovered_vote_count());
 runtime.snapshot();
 emit("snapshot",dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),runtime.recovered_vote_count());
 }
 {
 rt::Runtime runtime(config(dir,f));
 emit("reopen",dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),runtime.recovered_vote_count());
 auto r=runtime.record_vote(vote);
 emit("reopen-retry",dir,f,{"ACCEPT","",""},checkedReceipt(r),runtime.journal_sequence(),
 runtime.recovered_vote_count(),r.replay);
 }
 auto c=config(dir,f);c.vote_policy.reset();
 auto o=capture([&]{rt::Runtime runtime(c);});
 emit("reopen-no-policy",dir,f,o);
}
template<class F> void changed(const std::string& name,const std::filesystem::path& base,
 const std::filesystem::path& empty,F change){
 auto f=full(VoteAction::input_set);change(f);
 validate_vote_admission_policy(f.policy,f.state);
 auto o=capture([&]{rt::Runtime runtime(config(base,f));});
 emit("changed-reopen-"+name,base,f,o);
 o=capture([&]{rt::Runtime runtime(config(empty,f));});
 emit("changed-empty-"+name,empty,f,o);
}
void crash(const std::string& name,const std::filesystem::path& dir,rt::CrashPoint point){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 {
 rt::Runtime runtime(config(dir,f));
 auto o=capture([&]{static_cast<void>(runtime.record_vote(vote,point));});
 runtime.close();emit("crash-"+name,dir,f,o,{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 }
 {
 rt::Runtime runtime(config(dir,f));
 emit("recover-"+name,dir,f,{"ACCEPT","",""},{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 auto r=runtime.record_vote(vote);
 emit("retry-"+name,dir,f,{"ACCEPT","",""},checkedReceipt(r),runtime.journal_sequence(),
 runtime.recovered_vote_count(),r.replay);
 }
}
void guard(const std::filesystem::path& dir,VoteAction action){
 auto f=full(action);rt::Runtime runtime(config(dir,f));
 auto o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(f.vote)));});
 emit("guard-"+std::string(vote_kind_name(action)),dir,f,o,{},
 runtime.journal_sequence(),runtime.recovered_vote_count());
}
void advance(const std::filesystem::path& dir){
 auto f=full(VoteAction::input_set);auto vote=pr::encode(f.vote);
 auto other=full(VoteAction::round_config,f.state);
 f.policy.candidates.insert(f.policy.candidates.begin(),other.candidate);
 rt::Runtime runtime(config(dir,f));auto original=runtime.record_vote(vote);
 pr::Command command{"validator-1",id('c'),"FINALIZE_INPUT_FREEZE",1U,11U,
 "freeze-after-isc",f.state.round_id,0U};
 static_cast<void>(runtime.submit(pr::encode(command)));
 auto r=runtime.record_vote(vote);
 emit("after-state-command-retry",dir,f,{"ACCEPT","",""},checkedReceipt(r),
 runtime.journal_sequence(),runtime.recovered_vote_count(),r.replay);
 other.vote.durable_sequence=3U;
 auto o=capture([&]{static_cast<void>(runtime.record_vote(pr::encode(other.vote)));});
 emit("after-state-command-fresh",dir,f,o,{},runtime.journal_sequence(),
 runtime.recovered_vote_count());
 runtime.close();
 rt::Runtime reopened(config(dir,f));auto again=reopened.record_vote(vote);
 emit("after-state-command-reopen-retry",dir,f,{"ACCEPT","",""},checkedReceipt(again),
 reopened.journal_sequence(),reopened.recovered_vote_count(),again.replay);
}
void corrupt(const std::filesystem::path& base,const std::filesystem::path& dir,bool snap){
 auto f=full(VoteAction::input_set);
 auto write=[&](const std::filesystem::path& path,const Bytes& b){
 std::ofstream out(path,std::ios::binary);
 for(auto c:b)out.put(static_cast<char>(c));
 if(!out)throw std::runtime_error("harness corrupt fixture write");};
 auto wal=file(base/"runtime.wal");
 if(!snap)wal.back()^=std::byte{1};
 write(dir/"runtime.wal",wal);
 if(snap){auto b=file(base/"runtime.snapshot");b.back()^=std::byte{1};
 write(dir/"runtime.snapshot",b);}
 auto o=capture([&]{rt::Runtime runtime(config(dir,f));});
 emit(snap?"corrupt-snapshot":"corrupt-wal",dir,f,o);
}
int main(int argc,char** argv){
 if(argc!=2)throw std::runtime_error("isolated directory required");
 std::filesystem::path root(argv[1]);
 auto dir=[&](const std::string& name){auto p=root/name;
 if(std::filesystem::exists(p))throw std::runtime_error("directory is not fresh");
 std::filesystem::create_directories(p);return p;};
 for(auto a:{VoteAction::round_config,VoteAction::input_set,VoteAction::eligibility,
 VoteAction::aggregation_plan,VoteAction::parameter,VoteAction::aggregate_root,
 VoteAction::apply,VoteAction::view_change,VoteAction::abort})codec(a);
 malformed();auto base=dir("baseline");basic(base);
changed("soft-deadline",base,dir("soft-deadline"),[](auto& f){f.policy.soft_deadline_tick=51U;});
changed("hard-deadline",base,dir("hard-deadline"),[](auto& f){f.policy.hard_deadline_tick=101U;});
changed("initial-time",base,dir("initial-time"),[](auto& f){f.policy.initial_logical_tick=11U;});
changed("finalized-config",base,dir("finalized-config"),[](auto& f){f.policy.snapshot.finalized_round_config_ids.clear();});
changed("closed-root",base,dir("closed-root"),[](auto& f){f.policy.snapshot.input_set_bodies[0].input_root=id('f');bindBody(f);});
changed("closed-commitment",base,dir("closed-commitment"),[](auto& f){f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');bindBody(f);});
changed("closed-ac",base,dir("closed-ac"),[](auto& f){f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');bindBody(f);});
changed("state-root",base,dir("state-root"),[](auto& f){f.state.state_root=id('f');bindState(f);});
crash("before",dir("crash-before"),rt::CrashPoint::before_wal_append);
crash("partial",dir("crash-partial"),rt::CrashPoint::during_wal_append);
crash("named-before-barrier",dir("crash-named-before-barrier"),rt::CrashPoint::after_wal_append_before_durability);
crash("durable-uncommitted",dir("crash-durable-uncommitted"),rt::CrashPoint::after_durability_before_commit);
crash("committed-unreturned",dir("crash-committed-unreturned"),rt::CrashPoint::after_commit_before_effect_return);
crash("copied-unreturned",dir("crash-copied-unreturned"),rt::CrashPoint::after_effect_copy_before_return);
guard(dir("parameter"),VoteAction::parameter);
guard(dir("apply"),VoteAction::apply);
advance(dir("advance"));
corrupt(base,dir("corrupt-wal"),false);
corrupt(base,dir("corrupt-snapshot"),true);
}
