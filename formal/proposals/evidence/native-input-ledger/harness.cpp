
#include <delta/core/consensus.hpp>
#include <iostream>
#include <iomanip>
using namespace delta::core::consensus;
void q(const std::string& s){std::cout<<std::quoted(s);}
std::string id(char c){return "sha256:"+std::string(64,c);}
template<class T,class F> void array(const std::vector<T>& rows,F emit){
 std::cout<<'[';bool first=true;for(const auto& row:rows){if(!first)std::cout<<',';
 first=false;emit(row);}std::cout<<']';}
void strings(const std::vector<std::string>& rows){array(rows,[](const auto& s){q(s);});}
void state(const InputLedger& ledger){
 std::cout<<"{\"commitments\":";
 array(ledger.commitments(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<'}';});
 std::cout<<",\"availability\":";
 array(ledger.availabilities(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<",\"certificate_id\":";
 q(r.certificate_id);std::cout<<",\"covered_leaf_ids\":";strings(r.covered_leaf_ids);
 std::cout<<",\"attester_ids\":";strings(r.attester_ids);
 std::cout<<",\"threshold\":"<<r.threshold<<'}';});
 std::cout<<",\"frozen_inputs\":";
 array(ledger.frozen_inputs(),[](const auto& r){std::cout<<"{\"ticket_id\":";q(r.ticket_id);
 std::cout<<",\"commitment_id\":";q(r.commitment_id);std::cout<<",\"availability_certificate_id\":";
 q(r.availability_certificate_id);std::cout<<'}';});
 std::cout<<",\"frozen\":"<<(ledger.frozen()?"true":"false");
 std::cout<<",\"late_commitments\":"<<ledger.late_commitment_count();
 std::cout<<",\"late_availability\":"<<ledger.late_availability_count()<<'}';}
std::string status(Disposition d){switch(d){
 case Disposition::recorded:return "recorded";case Disposition::replay:return "replay";
 case Disposition::late:return "late";}throw std::runtime_error("unknown disposition");}
std::string error(ErrorCode code){switch(code){
 case ErrorCode::identifier_invalid:return "ERROR:identifier_invalid";
 case ErrorCode::unknown_ticket:return "ERROR:unknown_ticket";
 case ErrorCode::commitment_equivocation:return "ERROR:commitment_equivocation";
 case ErrorCode::commitment_missing:return "ERROR:commitment_missing";
 case ErrorCode::availability_commitment_mismatch:return "ERROR:availability_commitment_mismatch";
 case ErrorCode::availability_coverage_incomplete:return "ERROR:availability_coverage_incomplete";
 case ErrorCode::availability_attesters_invalid:return "ERROR:availability_attesters_invalid";
 case ErrorCode::availability_conflict:return "ERROR:availability_conflict";
 case ErrorCode::input_set_empty:return "ERROR:input_set_empty";
 default:throw std::runtime_error("unexpected error");}}
template<class F> void step(const char* name,InputLedger& ledger,F call){
 std::cout<<"{\"name\":";q(name);std::cout<<",\"before\":";state(ledger);
 std::string result;try{result=call();}catch(const ConsensusError& e){result=error(e.code());}
 std::cout<<",\"disposition\":";q(result);std::cout<<",\"after\":";state(ledger);std::cout<<"}\n";}
void emitClosure(const InputLedger& ledger){
 using namespace delta::certificates;
 const Context context{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 std::vector<InputTuple> tuples;
 for(const auto& row:ledger.frozen_inputs()){
 std::string domain;
 if(row.ticket_id=="ticket-a")domain="domain-a";
 else if(row.ticket_id=="ticket-b")domain="domain-b";
 else throw std::runtime_error("missing domain metadata");
 tuples.push_back({row.availability_certificate_id,row.commitment_id,domain,row.ticket_id});}
 const InputSetCertificate certificate{context,id('6'),3,
 {"validator-1","validator-2","validator-3"},tuples};
 const auto raw=canonical_json(certificate);
 const std::string ascii(reinterpret_cast<const char*>(raw.data()),raw.size());
 std::cout<<"{\"name\":\"complete-frozen-isc\",\"certificate_ascii\":";q(ascii);
 std::cout<<",\"certificate_id\":";q(content_id(certificate));
 std::cout<<",\"voted_body_id\":";q(vote_input_set_body_id(project_input_set_vote_body(certificate)));
 std::cout<<"}\n";}

int main(){InputLedger ledger({"ticket-a","ticket-b","ticket-c","ticket-d"});
step("empty-freeze",ledger,[&]{return (static_cast<void>(ledger.freeze()), std::string("frozen"));});
step("commit-b",ledger,[&]{return status(ledger.record_commitment({"ticket-b","sha256:9999999999999999999999999999999999999999999999999999999999999999"}));});
step("commit-a-reverse-arrival",ledger,[&]{return status(ledger.record_commitment({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888"}));});
step("commit-c-unavailable",ledger,[&]{return status(ledger.record_commitment({"ticket-c","sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}));});
step("commit-a-identical",ledger,[&]{return status(ledger.record_commitment({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888"}));});
step("commit-a-conflict",ledger,[&]{return status(ledger.record_commitment({"ticket-a","sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}));});
step("commit-unknown",ledger,[&]{return status(ledger.record_commitment({"ticket-z","sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}));});
step("commit-invalid-id",ledger,[&]{return status(ledger.record_commitment({"ticket-a","invalid"}));});
step("availability-no-commitment",ledger,[&]{return status(ledger.record_availability({"ticket-d","sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","sha256:4444444444444444444444444444444444444444444444444444444444444444",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("availability-wrong-commitment",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("coverage-missing",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("coverage-extra",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222","sha256:3333333333333333333333333333333333333333333333333333333333333333"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("coverage-duplicate",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:1111111111111111111111111111111111111111111111111111111111111111"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("coverage-reversed",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:2222222222222222222222222222222222222222222222222222222222222222","sha256:1111111111111111111111111111111111111111111111111111111111111111"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("attesters-short",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("attesters-duplicate",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-1","storage-1"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("attesters-foreign",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-z"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("attesters-reversed",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-3","storage-2","storage-1"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("threshold-mismatch",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},2U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("threshold-zero",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},0U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},0U));});
step("available-b",ledger,[&]{return status(ledger.record_availability({"ticket-b","sha256:9999999999999999999999999999999999999999999999999999999999999999","sha256:6666666666666666666666666666666666666666666666666666666666666666",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("available-a-reverse-arrival",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("available-a-identical",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("available-a-conflict",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("freeze-partial-permitted-set",ledger,[&]{return (static_cast<void>(ledger.freeze()), std::string("frozen"));});
step("freeze-identical",ledger,[&]{return (static_cast<void>(ledger.freeze()), std::string("frozen"));});
step("historical-commit-retry",ledger,[&]{return status(ledger.record_commitment({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888"}));});
step("historical-availability-retry",ledger,[&]{return status(ledger.record_availability({"ticket-a","sha256:8888888888888888888888888888888888888888888888888888888888888888","sha256:7777777777777777777777777777777777777777777777777777777777777777",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("late-commit-d",ledger,[&]{return status(ledger.record_commitment({"ticket-d","sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}));});
step("late-commit-d-identical",ledger,[&]{return status(ledger.record_commitment({"ticket-d","sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}));});
step("late-commit-d-conflict",ledger,[&]{return status(ledger.record_commitment({"ticket-d","sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}));});
step("late-availability-d-with-only-late-commitment",ledger,[&]{return status(ledger.record_availability({"ticket-d","sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","sha256:4444444444444444444444444444444444444444444444444444444444444444",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("late-availability-c",ledger,[&]{return status(ledger.record_availability({"ticket-c","sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sha256:5555555555555555555555555555555555555555555555555555555555555555",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("late-availability-c-identical",ledger,[&]{return status(ledger.record_availability({"ticket-c","sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sha256:5555555555555555555555555555555555555555555555555555555555555555",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("late-availability-c-conflict",ledger,[&]{return status(ledger.record_availability({"ticket-c","sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3"},3U},{"sha256:1111111111111111111111111111111111111111111111111111111111111111","sha256:2222222222222222222222222222222222222222222222222222222222222222"},{"storage-1","storage-2","storage-3","storage-4"},3U));});
step("freeze-remains-original",ledger,[&]{return (static_cast<void>(ledger.freeze()), std::string("frozen"));});
emitClosure(ledger);
}
