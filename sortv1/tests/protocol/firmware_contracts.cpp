#include <cassert>
#include <cstdint>
#include "../../firmware/state_machine/states.hpp"
#include "../../firmware/drivers/interfaces.hpp"
#include "../../firmware/protocol/crc16.hpp"
#include "../../firmware/config/timing.hpp"

int main() {
    const std::uint8_t vector[] = {'1','2','3','4','5','6','7','8','9'};
    assert(sortv1::crc16(vector, sizeof(vector)) == 0x29B1);
    sortv1::Inputs in;
    assert(!sortv1::may_position(in));
    assert(!sortv1::may_open(in, 0));
    in.lid_closed = in.service_closed = in.actuator_power = true;
    in.gate_closed = in.path_clear = in.heartbeat_fresh = in.permission_current = true;
    in.fault_latched = false;
    in.rotor_indices = 1;
    assert(sortv1::may_position(in));
    assert(sortv1::may_open(in, 0));
    assert(!sortv1::may_open(in, 1));
    assert(!sortv1::may_open(in, 4));
    in.rotor_indices = 3;
    assert(!sortv1::may_open(in, 0));
    in.rotor_indices = 1;
    in.gate_open = true;
    assert(!sortv1::may_position(in));
    in.gate_open = false;
    in.service_closed = false;
    assert(!sortv1::may_open(in, 0));
    in.service_closed = true;
    in.heartbeat_fresh = false;
    assert(!sortv1::may_position(in));
    static_assert(sortv1::timing::max_line_bytes == 512);
}
