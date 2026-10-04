#pragma once
#include <array>
#include <cstdint>

namespace physical {
enum class State { BOOT_SAFE, CHECK_HOME, READY, WAIT_STABLE, WAIT_DECISION, POSITIONING, DISPENSING, VERIFY_CLOSE, FAULT, REVIEW };
enum class Fill { UNKNOWN, AVAILABLE, FULL };
struct Inputs {
  bool calibrated=false, lid=false, service=false, power=false, reset=false;
  bool contacts_valid=true;
  bool closed=false, open=false, weight_known=false, presence=false, stable=false, overweight=false;
  std::array<bool,4> index{}, beam{};
  std::array<Fill,4> fill{};
  std::array<int32_t,4> tof_mm{{-1,-1,-1,-1}};
  int32_t weight_mg=0, hx_raw=0;
  bool hx_known=false;
  uint32_t gpio_raw=0;
};
struct Outputs { bool motor=false, gate_open=false, gate_close=false; };
struct Result { uint32_t cycle=0, request=0, seq=0; int dest=-1; bool done=false; };
class Machine {
public:
  State state=State::BOOT_SAFE;
  Outputs outputs{};
  uint32_t cycle=0, request=0, seq=0;
  int destination=-1;
  const char* reason="PHYSICAL_REARM_REQUIRED";
  bool inspect_event=false, done_event=false, fault_event=false;
  std::array<Result,8> history{};
  void heartbeat(uint32_t now) { heartbeat_ms=now; linked=true; }
  void tick(uint32_t now, const Inputs& i);
  const char* sort(uint32_t c, uint32_t r, int dest, const Inputs& i, uint32_t now);
  const Result* query(uint32_t c, uint32_t r) const;
  void fault(const char* why, uint32_t now);
  static const char* name(State state);
private:
  uint32_t entered=0, started=0, heartbeat_ms=0, index_since=0;
  bool linked=false, previous_reset=false, index_timing=false;
  bool reset_released=false;
  unsigned fall_stage=0, history_next=0;
  void enter(State s, uint32_t now) { state=s; entered=now; outputs={}; index_timing=false; }
};
}
