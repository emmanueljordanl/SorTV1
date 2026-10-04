#pragma once
#include "state_machine.hpp"
#include "VL53L0X.h"
#include <array>
class Sensors {
  struct Debounce { bool candidate=false, value=false; uint32_t changed=0; };
  std::array<Debounce,29> contacts{};
  std::array<VL53L0X,4> tof;
  std::array<bool,4> tof_ok{};
  std::array<uint32_t,4> tof_last{};
  std::array<std::array<unsigned,3>,4> ranges{};
  std::array<unsigned,4> range_count{},range_next{};
  std::array<int32_t,8> weights{};
  unsigned weight_count=0,weight_next=0;
  uint32_t hx_last=0,tof_poll=0;
  uint32_t contact_start=0;
  bool input(unsigned pin,uint32_t now);
public:
  physical::Inputs data{};
  void init(); void poll(uint32_t now);
};
