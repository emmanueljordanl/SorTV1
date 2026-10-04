#pragma once
#include <cstdint>
#include <cstddef>
#include "hardware/i2c.h"
class TwoWire {
  uint8_t address=0,tx[40]{},rx[40]{}; size_t used=0,received=0,cursor=0;
public:
  bool failed=false;
  void beginTransmission(uint8_t addr) { address=addr; used=0; }
  size_t write(uint8_t value) { if(used==sizeof tx) { failed=true; return 0; } tx[used++]=value; return 1; }
  uint8_t endTransmission(bool stop=true) {
    int n=i2c_write_timeout_us(i2c0,address,tx,used,!stop,1000);
    if(n!=int(used)) { failed=true; return 4; } return 0;
  }
  uint8_t requestFrom(uint8_t addr,uint8_t count) {
    if(count>sizeof rx) { failed=true; return 0; }
    int n=i2c_read_timeout_us(i2c0,addr,rx,count,false,1000); cursor=0; received=n>0?size_t(n):0;
    if(n!=count) failed=true;
    return uint8_t(received);
  }
  int read() { if(cursor>=received) { failed=true; return -1; } return rx[cursor++]; }
};
extern TwoWire Wire;
