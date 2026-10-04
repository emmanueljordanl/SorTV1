#pragma once
#include <cstdint>

namespace sortv1::timing {
constexpr std::uint32_t tick_ms = 1;
constexpr std::uint32_t heartbeat_interval_ms = 200;
constexpr std::uint32_t heartbeat_timeout_ms = 1000;
constexpr std::uint32_t decision_timeout_ms = 2000;
constexpr std::uint32_t position_timeout_ms = 3000;
constexpr std::uint32_t gate_timeout_ms = 1000;
constexpr std::uint32_t fall_timeout_ms = 2000;
constexpr std::uint32_t cycle_timeout_ms = 10000;
constexpr unsigned max_line_bytes = 512;
}  // namespace sortv1::timing
