#include <delta/certificates/contracts.hpp>
#include <iostream>
#include <string>
#include <vector>
using namespace delta::certificates;
std::string id(char c){return "sha256:"+std::string(64,c);}
std::string hex(const delta::core::canonical::Bytes& bs){
 const char* digits="0123456789abcdef";std::string out;
 for(auto byte:bs){const auto b=std::to_integer<unsigned>(byte);
 out.push_back(digits[b>>4]);out.push_back(digits[b&15]);}return out;}
std::string unhex(const std::string& raw){std::string out;
 for(std::size_t i=0;i<raw.size();i+=2){
 out.push_back(static_cast<char>(std::stoul(raw.substr(i,2),nullptr,16)));}return out;}
template<typename T> void emit(const char* kind,std::size_t i,const std::string& input,const T& v){
 try{const auto bytes=canonical_json(v);const auto key=content_id(v);
 std::cout<<kind<<'\t'<<i<<'\t'<<input<<"\tACCEPT\t"<<hex(bytes)<<'\t'<<key<<'\n';}
 catch(const CertificateError& e){std::cout<<kind<<'\t'<<i<<'\t'<<input
 <<"\tREJECT\t"<<static_cast<int>(e.code())<<"\t-\n";}}
int main(){
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const SeedTranscript seed{c,isc,id('9'),id('a'),{id('b')}};const auto sid=content_id(seed);
 const NormEvidence norm{c,{{1,"1","ticket-a"}},isc,id('c')};const auto nid=content_id(norm);
 const EligibilityCertificate ec{c,{{true,"domain-a",{1,1},"ACCEPTED","ticket-a"}},
 isc,nid,3,id('e'),signers};const auto eid=content_id(ec);
 const AggregationPlanCertificate plan{c,id('f'),{{"bucket-a","ticket-a"}},
 eid,isc,1,3,sid,signers,id('0'),{{{1,1},"ticket-a"}}};const auto pid=content_id(plan);
 const ParameterShardQc parameter{c,pid,1,"domain-a",eid,{id('1')},isc,3,
 {"1"},"shard-a",signers};
 const std::vector<std::string> cases{"30","31","2d31","2d30","2d3030","2d303030","2d30303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030","3030","3031","2d3031","2d30303031","39323233333732303336383534373735383037","39323233333732303336383534373735383038","2d39323233333732303336383534373735383038","2d39323233333732303336383534373735383039","2d3039323233333732303336383534373735383038","2d3039323233333732303336383534373735383039","","2d","2b30","2b31","2030","3020","310a","3100","2d303000","312e30","316530","307831","2d2d31","ff"};
 for(std::size_t i=0;i<cases.size();++i){auto n=norm;n.entries[0].squared_norm=unhex(cases[i]);
 emit("NORM",i,cases[i],n);}
 for(std::size_t i=0;i<cases.size();++i){auto p=parameter;p.result_numerators={unhex(cases[i])};
 emit("PARAMETER",i,cases[i],p);}
}
