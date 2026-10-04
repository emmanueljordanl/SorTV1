#include "state_machine.hpp"
#include "protocol.hpp"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
using namespace physical;
std::string frame(const char* payload) {
  char crc[8]; snprintf(crc,sizeof crc,"|%04X\n",wire::crc16(reinterpret_cast<const uint8_t*>(payload),std::strlen(payload)));
  return std::string(payload)+crc;
}
bool parse(const char* payload) { auto s=frame(payload); wire::Command c; return wire::decode(s.data(),s.size(),c); }
Inputs safe() { Inputs i; i.calibrated=i.lid=i.service=i.power=i.closed=i.weight_known=true; i.index[0]=true; i.fill.fill(Fill::AVAILABLE); return i; }
Machine waiting(Inputs& i) {
  Machine m; m.heartbeat(100); m.tick(99,i); i.reset=true; m.tick(100,i); i.reset=false; m.tick(101,i); m.tick(201,i); assert(m.state==State::READY);
  i.presence=true; i.stable=true; m.tick(202,i); m.tick(203,i); assert(m.state==State::WAIT_DECISION); assert(m.cycle==1); return m;
}
int main() {
  const char* golden[]={"123456789","","SorTV1","{\"v\":1,\"boot\":\"golden\",\"cmd\":\"HEARTBEAT\"}"};
  for(auto s:golden) printf("%04X\n",wire::crc16(reinterpret_cast<const uint8_t*>(s),std::strlen(s)));
  assert(parse("{\"v\":1,\"boot\":\"b\",\"cmd\":\"SORT\",\"cycle\":1,\"request\":1,\"dest\":0}"));
  assert(!parse("{\"v\":1,\"v\":1,\"boot\":\"b\",\"cmd\":\"HEARTBEAT\"}"));
  assert(!parse("{\"v\":true,\"boot\":\"b\",\"cmd\":\"HEARTBEAT\"}"));
  assert(!parse("{\"v\":1,\"boot\":\"b\",\"cmd\":\"SORT\",\"cycle\":-1,\"request\":1,\"dest\":0}"));
  assert(!parse("{\"v\":1,\"boot\":\"b\",\"cmd\":\"REARM\"}"));
  wire::Parser p; wire::Command c; for(int n=0;n<600;++n) assert(!p.feed('x',0,c)); assert(p.errors); p.feed('\n',1,c);
  auto hb=frame("{\"v\":1,\"boot\":\"b\",\"cmd\":\"HEARTBEAT\"}"); bool got=false;
  for(char v:hb) got=p.feed(v,2,c)||got;
  assert(got); p.feed('{',3,c); p.expire(254); assert(!p.feed('}',254,c)); p.feed('\n',255,c);
  for(int dest=0;dest<4;++dest) {
    Inputs i=safe(); Machine m=waiting(i);
    assert(!std::strcmp(m.sort(1,1,dest,i,204),"ACK")); assert(!std::strcmp(m.sort(1,1,dest,i,204),"ACK"));
    assert(!std::strcmp(m.sort(1,1,(dest+1)%4,i,204),"SORT_CONFLICT")); assert(!std::strcmp(m.sort(1,2,dest,i,204),"IDENTITY"));
    i.index.fill(false); i.index[dest]=true; m.tick(205,i); m.tick(305,i); assert(m.state==State::DISPENSING);
    m.tick(306,i); i.closed=false; i.open=true; i.beam[dest]=true; m.tick(307,i); i.beam[dest]=false; m.tick(308,i); assert(m.state==State::VERIFY_CLOSE);
    i.open=false; i.closed=true; i.presence=false; m.tick(309,i); assert(m.done_event); assert(m.state==State::READY);
    auto* result=m.query(1,1); assert(result && result->done && result->dest==dest);
    assert(!std::strcmp(m.sort(1,1,dest,i,310),"DONE")); assert(!m.outputs.motor && !m.outputs.gate_open);
  }
  { auto i=safe(); auto m=waiting(i); i.fill[0]=Fill::UNKNOWN; assert(!std::strcmp(m.sort(1,1,0,i,204),"GUARDS")); i.fill[0]=Fill::FULL; assert(!std::strcmp(m.sort(1,1,0,i,204),"GUARDS")); }
  { auto i=safe(); auto m=waiting(i); m.sort(1,1,0,i,204); i.power=false; m.tick(205,i); assert(m.state==State::FAULT && !m.outputs.motor); m.tick(206,i); assert(m.state==State::FAULT); }
  { auto i=safe(); auto m=waiting(i); m.sort(1,1,0,i,204); m.tick(205,i); m.tick(305,i); i.beam[1]=true; m.tick(306,i); assert(m.state==State::FAULT && !std::strcmp(m.reason,"WRONG_ROUTE")); }
  { auto i=safe(); auto m=waiting(i); i.open=true; m.tick(204,i); assert(m.state==State::FAULT); }
  { auto i=safe(); auto m=waiting(i); i.index[1]=true; m.tick(204,i); assert(m.state==State::FAULT); }
  { auto i=safe(); auto m=waiting(i); m.sort(1,1,0,i,204); m.tick(1201,i); assert(m.state==State::FAULT); }
  { auto i=safe(); i.calibrated=false; Machine m; m.heartbeat(1); i.reset=true; m.tick(2,i); assert(m.state==State::BOOT_SAFE); }
  { auto i=safe(); Machine m; m.heartbeat(1); i.reset=true; m.tick(2,i); assert(m.state==State::BOOT_SAFE); i.reset=false; m.tick(3,i); i.reset=true; m.tick(4,i); assert(m.state==State::CHECK_HOME); }
}
