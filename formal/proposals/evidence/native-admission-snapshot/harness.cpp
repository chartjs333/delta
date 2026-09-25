
#include "vote_fixture.hpp"
#include <delta/core/canonical.hpp>
#include <algorithm>
#include <iomanip>
#include <iostream>
using namespace delta::core::consensus;
using namespace delta::test::vote_fixture;
namespace canonical=delta::core::canonical;
namespace protocol=delta::core::protocol;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string hex(const canonical::Bytes& b){
 constexpr char digits[]="0123456789abcdef";std::string s;
 for(auto c:b){auto n=std::to_integer<unsigned int>(c);
 s.push_back(digits[n>>4U]);s.push_back(digits[n&15U]);}
 return s;}
void strings(const std::vector<std::string>& values){
 std::cout<<'[';bool first=true;for(const auto& v:values){if(!first)std::cout<<',';
 first=false;q(v);}std::cout<<']';}
void contextFields(const delta::certificates::Context& c){
 std::cout<<"{\"arithmetic_profile_id\":";q(c.arithmetic_profile_id);
 std::cout<<",\"height\":"<<c.height<<",\"parameter_schema_id\":";q(c.parameter_schema_id);
 std::cout<<",\"round_config_id\":";q(c.round_config_id);std::cout<<",\"round_id\":";q(c.round_id);
 std::cout<<",\"validator_epoch_id\":";q(c.validator_epoch_id);
 std::cout<<",\"view\":"<<c.view<<'}';}
void bindState(Fixture& f){
 f.policy.snapshot.state_id=canonical::content_id(canonical::Type::round_state,protocol::encode(f.state));}
void bindBody(Fixture& f){
 auto idBody=vote_input_set_body_id(f.policy.snapshot.input_set_bodies[0]);
 f.policy.snapshot.closed_input_set_ids={idBody};
 f.policy.candidates[0].body_hash=idBody;f.vote.body_hash=idBody;}
struct Outcome{std::string status;std::string code;std::string message;};
template<class F> Outcome capture(F operation){
 try{operation();return {"ACCEPT","",""};}
 catch(const ConsensusError& e){
 return {"REJECT",std::to_string(static_cast<int>(e.code())),e.what()};}
}
void outcome(const Outcome& o){
 std::cout<<"{\"status\":";q(o.status);std::cout<<",\"code\":";q(o.code);
 std::cout<<",\"message\":";q(o.message);std::cout<<'}';}
template<class F> void run(const char* name,VoteAction action,bool recovery,F mutation){
 auto f=full(action);VoteAdmissionState a{f.policy.initial_logical_tick,true,false};
 std::uint64_t expected=1U;mutation(f,a,expected);
 auto policy=capture([&]{validate_vote_admission_policy(f.policy,f.state);});
 std::string formalAction,context;
 auto vote=capture([&]{auto result=validate_vote_admission(f.policy,f.state,a,f.vote,expected,
   recovery?VoteAdmissionMode::recovery:VoteAdmissionMode::live);
   formalAction=result.formal_action_id;context=result.context_id;});
 std::cout<<"{\"name\":";q(name);std::cout<<",\"policy\":";outcome(policy);
 std::cout<<",\"vote\":";outcome(vote);std::cout<<",\"formal_action\":";q(formalAction);
 std::cout<<",\"returned_context\":";q(context);
 std::cout<<",\"state_hex\":";q(hex(protocol::encode(f.state)));
 std::cout<<",\"snapshot_state_id\":";q(f.policy.snapshot.state_id);
 std::cout<<",\"closed_ids\":";strings(f.policy.snapshot.closed_input_set_ids);
 std::cout<<",\"finalized_config_ids\":";strings(f.policy.snapshot.finalized_round_config_ids);
 std::cout<<",\"input_bodies\":[";
 bool first=true;for(const auto& b:f.policy.snapshot.input_set_bodies){
  if(!first)std::cout<<',';first=false;
  std::cout<<"{\"body_id\":";q(vote_input_set_body_id(b));std::cout<<",\"input_root\":";q(b.input_root);
  std::cout<<",\"context\":";contextFields(b.context);
  std::cout<<",\"tuples\":[";
  bool tfirst=true;for(const auto& t:b.tuples){if(!tfirst)std::cout<<',';tfirst=false;
   std::cout<<"{\"ticket_id\":";q(t.ticket_id);std::cout<<",\"domain_id\":";q(t.domain_id);
   std::cout<<",\"commitment_id\":";q(t.commitment_id);
   std::cout<<",\"availability_certificate_id\":";q(t.availability_certificate_id);std::cout<<'}';}
  std::cout<<"]}";}
 std::cout<<"],\"vote_hex\":";q(hex(protocol::encode(f.vote)));std::cout<<"}\n";
}

int main(){
run("original-round_config",VoteAction::round_config,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-input_set",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-eligibility",VoteAction::eligibility,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-aggregation_plan",VoteAction::aggregation_plan,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-aggregate_root",VoteAction::aggregate_root,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-view_change",VoteAction::view_change,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("original-abort",VoteAction::abort,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("apply-guard-live",VoteAction::apply,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("apply-guard-recovery",VoteAction::apply,true,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("parameter-guard-live",VoteAction::parameter,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("parameter-guard-recovery",VoteAction::parameter,true,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;});
run("stale-state-available_ticket_count",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.available_ticket_count=0U;});
run("stale-state-committed_ticket_count",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.committed_ticket_count=0U;f.state.available_ticket_count=0U;});
run("stale-state-config_id",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.config_id=id('f');});
run("stale-state-durable_sequence",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.durable_sequence=4U;});
run("stale-state-height",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.height=2U;});
run("stale-state-parent_checkpoint_id",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.parent_checkpoint_id=id('f');});
run("stale-state-phase",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.phase=delta::core::protocol::RoundPhase::eligible;});
run("stale-state-round_id",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.round_id="different-round";});
run("stale-state-state_root",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.state_root=id('f');});
run("stale-state-ticket_count",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.ticket_count=2U;});
run("stale-state-view",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.view=1U;});
run("snapshot-state-id",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.state_id=id('f');});
run("closed-membership",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.closed_input_set_ids.clear();});
run("closed-typed-body",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies.clear();});
run("closed-duplicate",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.closed_input_set_ids.push_back(f.vote.body_hash);});
run("closed-foreign",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.closed_input_set_ids={id('f')};});
run("body-root-unrebound",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].input_root=id('f');});
run("body-commitment-unrebound",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');});
run("body-ac-unrebound",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');});
run("body-domain-unrebound",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].domain_id="other-domain";});
run("body-ticket-unrebound",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].ticket_id="other-ticket";});
run("body-context",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].context.view=1U;});
run("candidate-context",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.candidates[0].context_id=id('f');});
run("candidate-body",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.candidates[0].body_hash=id('f');});
run("config-foreign-finalized",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.finalized_round_config_ids={id('f')};});
run("config-policy",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.round_config_id=id('f');});
run("epoch-policy",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.validator_epoch_id=id('f');});
run("committee-order",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;std::swap(f.policy.validator_ids[0],f.policy.validator_ids[1]);});
run("committee-duplicate",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.validator_ids[1]=f.policy.validator_ids[0];});
run("schema-policy",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.parameter_schema_id=id('f');});
run("arithmetic-profile-policy",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.arithmetic_profile_id=id('f');});
run("deadline-policy",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.soft_deadline_tick=f.policy.hard_deadline_tick;});
run("vote-body",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.body_hash=id('f');});
run("vote-context",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.context_id=id('f');});
run("vote-actor",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.validator_id="validator-2";});
run("vote-epoch",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.validator_epoch_id=id('f');});
run("vote-sequence",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.durable_sequence=2U;});
run("expected-sequence",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;expected=2U;});
run("vote-height",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.height=2U;});
run("vote-view",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.view=1U;});
run("vote-round",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.vote.round_id="other-round";});
run("current-parent",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.candidates[0].parents.parent_checkpoint_id=id('f');});
run("not-ready-live",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.recovery_ready=false;});
run("authority-invalidated-live",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.authority_invalidated=true;});
run("at-hard-deadline",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.logical_tick=f.policy.hard_deadline_tick;});
run("abort-request",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.abort_requests={{f.state.round_id,"INCOMPLETE_INPUT"}};});
run("not-ready-recovery",VoteAction::input_set,true,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.recovery_ready=false;});
run("invalidated-recovery",VoteAction::input_set,true,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.authority_invalidated=true;});
run("before-hard-deadline",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;a.logical_tick=f.policy.hard_deadline_tick-1U;});
run("no-finalized-config-assertion",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.finalized_round_config_ids.clear();});
run("rebound-summary-root",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.state_root=id('f');bindState(f);});
run("rebound-summary-counts",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.state.ticket_count=9U;bindState(f);});
run("rebound-input-root",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].input_root=id('f');bindBody(f);});
run("rebound-input-commitment",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].commitment_id=id('f');bindBody(f);});
run("rebound-input-ac",VoteAction::input_set,false,[](auto& f,auto& a,auto& expected){(void)f;(void)a;(void)expected;f.policy.snapshot.input_set_bodies[0].tuples[0].availability_certificate_id=id('f');bindBody(f);});
}
