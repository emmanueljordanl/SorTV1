#pragma once
#include "state_machine.hpp"
class Actuators {
  unsigned slice=0; bool stepping=false;
public:
  void init(); void apply(const physical::Outputs& out, bool permitted); void safe();
};
