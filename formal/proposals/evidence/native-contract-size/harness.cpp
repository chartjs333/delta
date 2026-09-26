#include <delta/certificates/contracts.hpp>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>
using namespace delta::certificates;
std::string id(char c){return "sha256:"+std::string(64,c);}
int main(){
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const std::vector<std::pair<unsigned,unsigned>> cases{{1U,0U},{65523U,49U},{65523U,50U},{65523U,51U}};
 for(const auto& [count,padding]:cases){
  NormEvidence norm{c,{},isc,id('c')};
  for(unsigned i=0;i<count;++i){std::ostringstream name;
   name<<'t'<<std::setw(5)<<std::setfill('0')<<i;
   norm.entries.push_back({1,"0",name.str()});}
  norm.entries.back().ticket_id+=std::string(padding,'z');
  const auto bytes=canonical_json(norm);
  std::cout<<count<<'\t'<<padding<<'\t'<<bytes.size()<<'\t'
   <<delta::core::canonical::sha256_hex(bytes)<<'\t';
  try{const auto key=content_id(norm);std::cout<<"ACCEPT\t"<<key<<'\n';}
  catch(const CertificateError& e){std::cout<<"REJECT\t"<<static_cast<int>(e.code())<<'\n';}
 }
}
