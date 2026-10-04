#include "state_machine.hpp"
#include "calibration.hpp"
namespace physical {
const char* Machine::name(State s) {
  static const char* names[]={"BOOT_SAFE","CHECK_HOME","READY","WAIT_STABLE","WAIT_DECISION","POSITIONING","DISPENSING","VERIFY_CLOSE","FAULT","REVIEW"};
  return names[static_cast<int>(s)];
}
const Result* Machine::query(uint32_t c, uint32_t r) const {
  for (const auto& h:history) if(h.cycle==c && h.request==r && c!=0) return &h;
  return nullptr;
}
void Machine::fault(const char* why, uint32_t now) {
  enter(State::FAULT,now); reason=why; ++seq; fault_event=true;
}
const char* Machine::sort(uint32_t c,uint32_t r,int dest,const Inputs& i,uint32_t now) {
  if(const auto* old=query(c,r)) return old->dest==dest ? (old->done?"DONE":"ACK") : "SORT_CONFLICT";
  if(c!=cycle || !c || r!=1) return "IDENTITY";
  if(state!=State::WAIT_DECISION || request!=0) return "STATE";
  if(dest<0 || dest>3) return "DESTINATION";
  if(!linked || now-heartbeat_ms>1000 || !i.calibrated || !i.lid || !i.service || !i.power || !i.closed || i.open || !i.stable || !i.presence || i.overweight || i.fill[dest]!=Fill::AVAILABLE) return "GUARDS";
  for(bool blocked:i.beam) if(blocked) return "PATH_BLOCKED";
  request=r; destination=dest; history[history_next]={c,r,0,dest,false}; history_next=(history_next+1)%history.size();
  enter(State::POSITIONING,now); return "ACK";
}
void Machine::tick(uint32_t now,const Inputs& i) {
  inspect_event=done_event=fault_event=false;
  if(!i.contacts_valid) { outputs={}; return; }
  if(!i.reset) reset_released=true;
  const bool rising=i.reset && !previous_reset; previous_reset=i.reset;
  unsigned indices=0; for(bool v:i.index) if(v) ++indices;
  if(i.open && i.closed) { if(state!=State::FAULT) fault("GATE_CONFLICT",now); return; }
  if(indices>1) { if(state!=State::FAULT) fault("MULTIPLE_INDICES",now); return; }
  const bool idle=(state==State::BOOT_SAFE || state==State::FAULT || state==State::REVIEW);
  const bool active=(state==State::POSITIONING || state==State::DISPENSING || state==State::VERIFY_CLOSE);
  const bool guards=i.calibrated && i.lid && i.service && i.power && linked && now-heartbeat_ms<=1000;
  if(active && !guards) { fault("INTERLOCK_OR_HEARTBEAT",now); return; }
  if(active && i.fill[destination]!=Fill::AVAILABLE) { fault("BIN_UNAVAILABLE",now); return; }
  if(active && (i.overweight || !i.weight_known)) { fault("WEIGHT_UNSAFE",now); return; }
  if(!idle && state!=State::READY && now-started>10000) { fault("CYCLE_TIMEOUT",now); return; }
  if(idle) {
    outputs={};
    bool clear=true; for(bool blocked:i.beam) clear &= !blocked;
    if(rising && reset_released && guards && clear && i.weight_known && !i.presence && i.closed && !i.open && indices==1) {
      request=0; destination=-1; started=now; enter(State::CHECK_HOME,now); reason="OK";
    }
    return;
  }
  switch(state) {
  case State::CHECK_HOME:
    if(!guards) { fault("HOME_GUARDS",now); break; }
    if(indices==1 && i.closed && !i.presence) {
      if(!index_timing) { index_since=now; index_timing=true; }
      if(now-index_since>=calibration::index_stable_ms) enter(State::READY,now);
    } else index_timing=false;
    if(now-entered>3000) fault("HOME_TIMEOUT",now);
    break;
  case State::READY:
    // Opening lid for loading removes physical actuator power and is normal.
    outputs={};
    if(!linked || now-heartbeat_ms>1000 || (!i.power && i.lid && i.service)) { fault("READY_POWER_OR_LINK_LOST",now); break; }
    if(guards && i.closed && i.weight_known && i.presence) { started=now; enter(State::WAIT_STABLE,now); }
    break;
  case State::WAIT_STABLE:
    if(!guards) { fault("INSPECT_GUARDS",now); break; }
    if(i.overweight) { enter(State::REVIEW,now); reason="OVERWEIGHT"; break; }
    if(i.weight_known && i.presence && i.stable) { ++cycle; request=0; destination=-1; enter(State::WAIT_DECISION,now); inspect_event=true; }
    else if(now-entered>3000) { enter(State::REVIEW,now); reason="UNSTABLE"; }
    break;
  case State::WAIT_DECISION:
    if(!guards || !i.presence || !i.stable || !i.closed) { enter(State::REVIEW,now); reason="INSPECTION_CHANGED"; }
    else if(now-entered>2000) { enter(State::REVIEW,now); reason="DECISION_TIMEOUT"; }
    break;
  case State::POSITIONING:
    if(!i.closed || i.open) { fault("GATE_NOT_CLOSED",now); break; }
    for(bool blocked:i.beam) if(blocked) { fault("ROTOR_NOT_EMPTY",now); return; }
    if(i.fill[destination]!=Fill::AVAILABLE) { fault("BIN_UNAVAILABLE",now); break; }
    outputs.motor=!i.index[destination];
    if(i.index[destination] && indices==1) {
      if(!index_timing) { index_since=now; index_timing=true; }
      if(now-index_since>=calibration::index_stable_ms) { enter(State::DISPENSING,now); fall_stage=0; }
    } else index_timing=false;
    if(now-entered>3000) fault("POSITION_TIMEOUT",now);
    break;
  case State::DISPENSING:
    outputs.gate_open=true;
    if(!i.index[destination] || indices!=1) { fault("POSITION_LOST",now); break; }
    for(int b=0;b<4;++b) if(b!=destination && i.beam[b]) { fault("WRONG_ROUTE",now); return; }
    if(fall_stage==0 && !i.beam[destination]) fall_stage=1;
    else if(fall_stage==1 && i.beam[destination]) fall_stage=2;
    else if(fall_stage==2 && !i.beam[destination] && i.open) { enter(State::VERIFY_CLOSE,now); }
    if(!i.open && now-entered>1000) fault("OPEN_TIMEOUT",now);
    else if(now-entered>2000) fault("FALL_TIMEOUT",now);
    break;
  case State::VERIFY_CLOSE:
    outputs.gate_close=true;
    for(int b=0;b<4;++b) if(i.beam[b]) { fault("PATH_NOT_CLEAR",now); return; }
    if(!i.index[destination] || indices!=1) { fault("POSITION_LOST",now); break; }
    if(i.weight_known && i.stable && !i.presence && i.closed && !i.open) {
      ++seq;
      for(auto& h:history) if(h.cycle==cycle && h.request==request) { h.done=true; h.seq=seq; }
      enter(State::READY,now); done_event=true;
    } else if(now-entered>1000) fault("CLOSE_OR_EMPTY_TIMEOUT",now);
    break;
  default: break;
  }
}
}
