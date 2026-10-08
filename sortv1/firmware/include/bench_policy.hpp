#pragma once
#include <cstdint>
namespace bench {
struct Policy {
  enum class Kind {OFF,STEP,SERVO};
  Kind kind=Kind::OFF;
  bool latched=false, heartbeat_seen=false, guards_seen=false;
  uint32_t heartbeat_ms=0,guard_since=0,deadline=0,seq=0;
  unsigned a=0,b=0;
  void safe() { kind=Kind::OFF; a=b=0; }
  void tick(uint32_t now,bool usb,bool guards,bool deadman) {
    if(guards && !guards_seen) {guards_seen=true;guard_since=now;}
    if(!guards) guards_seen=false;
    if(kind!=Kind::OFF && (!usb || !guards || !deadman || !heartbeat_seen || uint32_t(now-heartbeat_ms)>300)) {
      safe();latched=true;
    }
    if(kind!=Kind::OFF && int32_t(now-deadline)>=0) safe();
  }
  bool ping(uint32_t n,uint32_t now) {
    if(n<=seq) return false;
    seq=n;heartbeat_seen=true;heartbeat_ms=now;return true;
  }
  bool request(Kind k,uint32_t n,unsigned x,unsigned y,uint32_t now,bool usb,bool guards,bool deadman) {
    if(n<=seq) return false;
    seq=n;
    if(latched || kind!=Kind::OFF || !usb || !guards || !deadman || !guards_seen || uint32_t(now-guard_since)<100 || !heartbeat_seen || uint32_t(now-heartbeat_ms)>300) return false;
    unsigned lease=0;
    if(k==Kind::STEP) {
      if(x<1 || x>32 || y<2000 || y>10000) return false;
      lease=(x*y+999)/1000;
    } else if(k==Kind::SERVO) {
      if(x<500 || x>2500 || y<20 || y>500) return false;
      lease=y;
    } else return false;
    if(lease>500) return false;
    kind=k;a=x;b=y;deadline=now+lease;return true;
  }
};
}
