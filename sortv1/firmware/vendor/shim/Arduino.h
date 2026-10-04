#pragma once
#include <cstdint>
#include "pico/stdlib.h"
using boolean=bool;
inline uint32_t millis() { return to_ms_since_boot(get_absolute_time()); }
