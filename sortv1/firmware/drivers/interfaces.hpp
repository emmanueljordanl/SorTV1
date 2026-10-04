#pragma once
#include <cstdint>
#include "../state_machine/states.hpp"

namespace sortv1 {
// Adaptadores Pico SDK pendientes. Solo la máquina física utiliza estas interfaces.
class Sensors {
public:
    virtual ~Sensors() = default;
    virtual Inputs read_debounced(std::uint32_t now_ms) = 0;
};

class Actuators {
public:
    virtual ~Actuators() = default;
    virtual void disable() = 0;
    virtual void begin_position(unsigned destination) = 0;
    virtual void begin_open() = 0;
    virtual void begin_close() = 0;
    virtual void tick(std::uint32_t now_ms) = 0;
};
}  // namespace sortv1
