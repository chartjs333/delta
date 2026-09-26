
#include "vote_fixture.hpp"
#include "wal.hpp"
#include <delta/core/transition.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
using namespace delta::test::vote_fixture;
using namespace delta::core::consensus;
namespace rt=delta::runtime; namespace dt=rt::detail;
namespace ca=delta::core::canonical; namespace pr=delta::core::protocol;
using Bytes=ca::Bytes;
std::filesystem::path root;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string hex(const Bytes& b){constexpr char d[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned>(c);s.push_back(d[n>>4U]);s.push_back(d[n&15U]);}
 return s;}
Bytes file(const std::filesystem::path& p){if(!std::filesystem::exists(p))return {};
 std::ifstream in(p,std::ios::binary);Bytes b;char c;
 while(in.get(c))b.push_back(static_cast<std::byte>(static_cast<unsigned char>(c)));
 if(!in.eof())throw std::runtime_error("harness read");return b;}
std::filesystem::path dir(const std::string& n){auto p=root/n;
 if(std::filesystem::exists(p))throw std::runtime_error("not fresh");
 std::filesystem::create_directories(p);return p;}
pr::Command command(const std::string& kind,std::uint64_t tick,const std::string& request,
 std::uint64_t view=0U){return {"validator-1",id('c'),kind,1U,tick,request,"round-vote-fixture",view};}
rt::Config config(const std::filesystem::path& p,const Fixture& f,bool policy){
 rt::Config c;c.directory=p;c.initial_state_bytes=pr::encode(f.state);
 if(policy)c.vote_policy=rt::parse_vote_policy_v1(rt::encode_vote_policy_v1(f.policy));return c;}
void receipt(const rt::SubmitReceipt& r){
 std::cout<<"{\"state_hex\":";q(hex(r.next_state_bytes));std::cout<<",\"effects_hex\":";
 q(hex(r.effect_batch_bytes));std::cout<<",\"record_hex\":";q(hex(r.wal_record_bytes));
 std::cout<<",\"next_id\":";q(r.next_state_id);std::cout<<",\"effects_id\":";q(r.effect_batch_id);
 std::cout<<",\"record_id\":";q(r.wal_record_id);std::cout<<",\"sequence\":"<<r.journal_sequence;
 std::cout<<",\"replay\":"<<(r.replay?"true":"false")<<'}';}
struct Result {std::string status="ACCEPT",code="",message="";Bytes state;
 std::uint64_t seq=0U;std::optional<rt::SubmitReceipt> receipt;std::optional<rt::VoteReceipt> vote;};
template<class F> Result capture(F f){Result r;try{f(r);}
 catch(const rt::RuntimeError& e){r.status="REJECT";r.code=std::to_string(static_cast<int>(e.code()));r.message=e.what();}
 catch(const std::exception& e){r.status="REJECT";r.code="core";r.message=e.what();}return r;}
void emit(const std::string& name,const std::string& operation,const std::filesystem::path& p,
 const Fixture& f,bool policy,const Bytes& input,const Result& r){
 std::cout<<"{\"name\":";q(name);std::cout<<",\"operation\":";q(operation);
 std::cout<<",\"status\":";q(r.status);std::cout<<",\"code\":";q(r.code);
 std::cout<<",\"message\":";q(r.message);std::cout<<",\"initial_hex\":";q(hex(pr::encode(f.state)));
 std::cout<<",\"policy_hex\":";q(policy?hex(rt::encode_vote_policy_v1(f.policy)):"");
 std::cout<<",\"clock\":";if(policy)std::cout<<f.policy.initial_logical_tick;else std::cout<<"null";
 std::cout<<",\"command_hex\":";q(hex(input));std::cout<<",\"wal_hex\":";q(hex(file(p/"runtime.wal")));
 std::cout<<",\"snapshot_hex\":";q(hex(file(p/"runtime.snapshot")));
 std::cout<<",\"state_hex\":";q(hex(r.state));std::cout<<",\"sequence\":"<<r.seq;
 std::cout<<",\"receipt\":";if(r.receipt)receipt(*r.receipt);else std::cout<<"null";std::cout<<",\"vote_receipt_hex\":";q(r.vote?hex(rt::encode_vote_receipt_v1(*r.vote)):"");std::cout<<",\"vote_replay\":"<<(r.vote&&r.vote->replay?"true":"false");std::cout<<"}\n";}
void openCase(const std::string& name,const Fixture& f,bool policy,
 const std::vector<dt::JournalEntry>& entries,std::optional<dt::Snapshot> snap={}){
 auto p=dir(name);{dt::Wal wal(p/"runtime.wal");for(const auto& e:entries)wal.append_and_sync(e,false);
 if(snap)wal.write_snapshot(p/"runtime.snapshot",*snap);}
 auto r=capture([&](auto& o){rt::Runtime runtime(config(p,f,policy));
 o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit(name,"recover",p,f,policy,{},r);}

int main(int argc,char** argv){if(argc!=2)throw std::runtime_error("isolated directory required");
 root=argv[1];auto f=full(VoteAction::input_set);auto other=full(VoteAction::round_config,f.state);f.policy.candidates.insert(f.policy.candidates.begin(),other.candidate);auto p=dir("live");
 auto vote=pr::encode(f.vote);auto c0=command("FINALIZE_INPUT_FREEZE",11U,"freeze-after-isc");
 auto b0=pr::encode(c0);auto c1=command("ADVANCE_VIEW",12U,"view",1U);
 auto c2=command("CERTIFY_ABORT",13U,"abort",1U);Bytes mid;
 {rt::Runtime runtime(config(p,f,true));
 auto r=capture([&](auto& o){o.vote=runtime.record_vote(vote);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});
 runtime.snapshot();emit("live-vote","vote",p,f,true,vote,r);
 for(const auto& c:{c0,c1,c2}){auto b=pr::encode(c);r=capture([&](auto& o){o.receipt=runtime.submit(b);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});
 if(c.request_id=="view")mid=runtime.state_bytes();emit("live-"+c.request_id,"live",p,f,true,b,r);}
 r=capture([&](auto& o){o.vote=runtime.record_vote(vote);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit("historical-vote","vote-retry",p,f,true,vote,r);
 r=capture([&](auto& o){o.receipt=runtime.submit(b0);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit("historical-command","retry",p,f,true,b0,r);
 auto altered=f.vote;altered.signature_id=id('a');auto vb=pr::encode(altered);
 r=capture([&](auto& o){o.vote=runtime.record_vote(vb);});emit("vote-conflict","vote-retry",p,f,true,vb,r);
 auto wrong=c0;wrong.body_hash=id('b');auto cb=pr::encode(wrong);
 r=capture([&](auto& o){o.receipt=runtime.submit(cb);});emit("command-conflict","retry",p,f,true,cb,r);
 auto fresh=f.vote;fresh.context_id=id('a');fresh.durable_sequence=5U;vb=pr::encode(fresh);
 r=capture([&](auto& o){o.vote=runtime.record_vote(vb);});emit("fresh-after-command","fresh-vote",p,f,true,vb,r);
 }
 {rt::Runtime runtime(config(p,f,true));auto r=capture([&](auto& o){o.vote=runtime.record_vote(vote);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit("reopened-vote","vote-retry",p,f,true,vote,r);
 r=capture([&](auto& o){o.receipt=runtime.submit(b0);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit("reopened-command","retry",p,f,true,b0,r);}
 std::vector<dt::JournalEntry> entries;{dt::Wal wal(p/"runtime.wal");entries=wal.recover().entries;}
 openCase("no-snapshot",f,true,entries);openCase("snapshot-at-vote",f,true,entries,dt::Snapshot{1U,pr::encode(f.state)});
 openCase("snapshot-at-command",f,true,entries,dt::Snapshot{3U,mid});
 openCase("wrong-vote-snapshot",f,true,entries,dt::Snapshot{1U,mid});
 openCase("wrong-command-snapshot",f,true,entries,dt::Snapshot{3U,pr::encode(f.state)});
 openCase("zero-different-snapshot",f,true,entries,dt::Snapshot{0U,mid});
 openCase("ahead-snapshot",f,true,entries,dt::Snapshot{5U,mid});
 openCase("vote-only",f,true,{entries[0]},dt::Snapshot{1U,pr::encode(f.state)});
 openCase("empty",f,true,{});
 auto changed=entries;changed[0].wal_record_bytes[0]=std::byte{'0'};openCase("wrong-policy-id",f,true,changed);
 changed=entries;changed[0].sequence=2U;openCase("outer-gap",f,true,changed);
 auto vv=f.vote;vv.durable_sequence=2U;changed=entries;changed[0].command_or_vote_bytes=pr::encode(vv);openCase("vote-sequence",f,true,changed);
 changed=entries;std::swap(changed[0],changed[1]);openCase("reordered",f,true,changed);
 auto dup=entries[0];dup.sequence=2U;dup.command_or_vote_bytes=pr::encode(vv);openCase("duplicate-vote",f,true,{entries[0],dup});
 dup=entries[1];dup.sequence=3U;openCase("duplicate-command",f,true,{entries[0],entries[1],dup});
 vv.durable_sequence=3U;dup=entries[0];dup.sequence=3U;dup.command_or_vote_bytes=pr::encode(vv);openCase("vote-after-command",f,true,{entries[0],entries[1],dup});
 changed=entries;changed[2].next_state_bytes=entries[1].next_state_bytes;openCase("changed-state",f,true,changed);
 changed=entries;changed[2].effect_batch_bytes=entries[1].effect_batch_bytes;openCase("changed-effects",f,true,changed);
 changed=entries;changed[2].wal_record_bytes=entries[1].wal_record_bytes;openCase("changed-record",f,true,changed);
 auto alteredPolicy=f;alteredPolicy.policy.initial_logical_tick=9U;openCase("changed-startup-policy",alteredPolicy,true,entries);
 auto low=c0;low.logical_tick=9U;auto lr=delta::core::transition::apply(pr::encode(f.state),pr::encode(low));
 auto lowEntry=entries[1];lowEntry.command_or_vote_bytes=pr::encode(low);lowEntry.next_state_bytes=lr.next_state_bytes;lowEntry.effect_batch_bytes=lr.effect_batch_bytes;lowEntry.wal_record_bytes=lr.wal_record_bytes;
 openCase("backwards-clock",f,true,{entries[0],lowEntry});
}
