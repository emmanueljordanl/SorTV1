#pragma once
#include <array>
namespace calibration {
// Generated safe defaults. Use configure_firmware.py with measured evidence.
constexpr bool verified=false;
constexpr unsigned contact_debounce_ms=20,index_stable_ms=100;
constexpr std::array<bool,29> active_high{};
constexpr int hx_offset=0;
constexpr float mg_per_count=0;
constexpr int presence_mg=0, stable_span_mg=0, overweight_mg=200000;
constexpr unsigned servo_closed_us=0,servo_open_us=0,step_period_us=0;
constexpr bool direction=false;
constexpr std::array<unsigned,4> tof_full_mm{},tof_hysteresis_mm{};
}
