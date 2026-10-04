#pragma once
#include <cstddef>
#include <cstdint>
namespace wire {
uint16_t crc16(const uint8_t* data,size_t size);
struct Command { char boot[49]{}, cmd[17]{}; uint32_t cycle=0,request=0; int dest=-1; bool identity=false; };
bool decode(char* line, size_t size, Command& out);
class Parser {
  char bytes[513]{}; size_t used=0; bool discard=false; uint32_t started=0;
public:
  unsigned errors=0;
  bool feed(char value,uint32_t now,Command& out);
  void expire(uint32_t now);
};
}
