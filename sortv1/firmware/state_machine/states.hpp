#pragma once
#include <cstdint>

namespace sortv1 {
enum class State : std::uint8_t {
    BOOT_SAFE, CHECK_HOME, READY, WAIT_STABLE, WAIT_DECISION,
    POSITIONING, DISPENSING, VERIFY_CLOSE, FAULT, REVIEW
};

// Contrato de entradas ya filtradas; estados desconocidos no habilitan movimiento.
struct Inputs {
    bool lid_closed = false;
    bool service_closed = false;
    bool actuator_power = false;
    bool gate_closed = false;
    bool gate_open = false;
    bool path_clear = false;
    bool heartbeat_fresh = false;
    bool permission_current = false;
    bool fault_latched = true;
    std::uint8_t rotor_indices = 0;
};

constexpr bool guards_ok(const Inputs& in) {
    return in.lid_closed && in.service_closed && in.actuator_power
        && in.heartbeat_fresh && in.permission_current && !in.fault_latched
        && !(in.gate_open && in.gate_closed);
}

constexpr bool may_position(const Inputs& in) {
    return guards_ok(in) && in.gate_closed && !in.gate_open && in.path_clear;
}

constexpr bool may_open(const Inputs& in, unsigned destination) {
    return destination < 4 && may_position(in)
        && in.rotor_indices == (1u << destination);
}
}  // namespace sortv1
