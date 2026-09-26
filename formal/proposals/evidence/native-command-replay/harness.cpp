
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
 std::uint64_t view=0U){return {"validator-1",id('a'),kind,1U,tick,request,"round-vote-fixture",view};}
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
 std::uint64_t seq=0U;std::optional<rt::SubmitReceipt> receipt;};
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
 std::cout<<",\"receipt\":";if(r.receipt)receipt(*r.receipt);else std::cout<<"null";std::cout<<"}\n";}
void openCase(const std::string& name,const Fixture& f,bool policy,
 const std::vector<dt::JournalEntry>& entries,std::optional<dt::Snapshot> snap={}){
 auto p=dir(name);{dt::Wal wal(p/"runtime.wal");for(const auto& e:entries)wal.append_and_sync(e,false);
 if(snap)wal.write_snapshot(p/"runtime.snapshot",*snap);}
 auto r=capture([&](auto& o){rt::Runtime runtime(config(p,f,policy));
 o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit(name,"recover",p,f,policy,{},r);}
int main(int argc,char** argv){if(argc!=2)throw std::runtime_error("isolated directory required");
 root=argv[1];auto f=full(VoteAction::input_set);auto p=dir("live");
 auto c0=command("FINALIZE_INPUT_FREEZE",11U,"freeze");auto b0=pr::encode(c0);
 auto c1=command("ADVANCE_VIEW",12U,"view",1U);
 auto c2=command("CERTIFY_ABORT",13U,"abort",1U);
 Bytes middle;{rt::Runtime runtime(config(p,f,true));
 for(const auto& c:{c0,c1,c2}){auto b=pr::encode(c);auto r=capture([&](auto& o){
 o.receipt=runtime.submit(b);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});
 if(c.request_id=="view"){runtime.snapshot();middle=runtime.state_bytes();}
 emit("live-"+c.request_id,"live",p,f,true,b,r);}
 auto r=capture([&](auto& o){o.receipt=runtime.submit(b0);o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});
 emit("historical-retry","retry",p,f,true,b0,r);
 auto wrong=c0;wrong.body_hash=id('b');auto b=pr::encode(wrong);
 r=capture([&](auto& o){o.receipt=runtime.submit(b);});emit("request-conflict","retry",p,f,true,b,r);
 auto old=command("ADVANCE_VIEW",10U,"old",2U);b=pr::encode(old);
 r=capture([&](auto& o){o.receipt=runtime.submit(b);});emit("fresh-old-clock","fresh",p,f,true,b,r);}
 {rt::Runtime runtime(config(p,f,true));auto r=capture([&](auto& o){o.receipt=runtime.submit(b0);
 o.state=runtime.state_bytes();o.seq=runtime.journal_sequence();});emit("reopened-retry","retry",p,f,true,b0,r);}
 std::vector<dt::JournalEntry> entries;{dt::Wal wal(p/"runtime.wal");entries=wal.recover().entries;}
 openCase("no-snapshot",f,true,entries);openCase("matching-middle",f,true,entries,dt::Snapshot{2U,middle});
 openCase("wrong-middle",f,true,entries,dt::Snapshot{2U,pr::encode(f.state)});
 openCase("ahead-snapshot",f,true,entries,dt::Snapshot{4U,middle});
 openCase("zero-different-snapshot",f,true,entries,dt::Snapshot{0U,middle});
 openCase("zero-empty-journal",f,true,{},dt::Snapshot{0U,middle});
 for(int k=0;k<3;++k){auto changed=entries;if(k==0)changed[1].next_state_bytes=entries[0].next_state_bytes;
 if(k==1)changed[1].effect_batch_bytes.clear();if(k==2)changed[1].wal_record_bytes.clear();
 openCase("changed-output-"+std::to_string(k),f,true,changed);}
 auto changed=entries;std::swap(changed[0],changed[1]);openCase("reordered",f,true,changed);
 changed=entries;changed[1].sequence=3U;openCase("sequence-gap",f,true,changed);
 auto low=c0;low.logical_tick=9U;auto result=delta::core::transition::apply(pr::encode(f.state),pr::encode(low));
 std::vector<dt::JournalEntry> old{{1U,dt::JournalKind::transition,pr::encode(low),result.next_state_bytes,
 result.effect_batch_bytes,result.wal_record_bytes}};
 openCase("old-clock-policy",f,true,old);openCase("old-clock-submit-only",f,false,old);
 auto configFixture=full(VoteAction::round_config);
 auto cc=command("FINALIZE_ROUND_CONFIG",11U,"same");auto cb=pr::encode(cc);
 auto cr=delta::core::transition::apply(pr::encode(configFixture.state),cb);
 std::vector<dt::JournalEntry> dup{{1U,dt::JournalKind::transition,cb,cr.next_state_bytes,cr.effect_batch_bytes,cr.wal_record_bytes},
 {2U,dt::JournalKind::transition,cb,cr.next_state_bytes,cr.effect_batch_bytes,cr.wal_record_bytes}};
 openCase("duplicate-request",configFixture,false,dup);
 openCase("empty",f,true,{});
}
