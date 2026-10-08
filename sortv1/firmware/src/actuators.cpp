#include "actuators.hpp"
#include "calibration.hpp"
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "hardware/timer.h"
namespace {
repeating_timer_t timer;
volatile bool pulse=false, permission=false;
bool step(repeating_timer_t*) { pulse=permission && !pulse; gpio_put(0,pulse); return true; }
}
void Actuators::init() {
  gpio_init(2); gpio_put(2,1); gpio_set_dir(2,GPIO_OUT); gpio_set_drive_strength(2,GPIO_DRIVE_STRENGTH_8MA);
  for(unsigned pin:{0u,1u,3u}) { gpio_init(pin); gpio_put(pin,0); gpio_set_dir(pin,GPIO_OUT); }
  slice=pwm_gpio_to_slice_num(3);
  if(calibration::verified) {
    // 1 MHz PWM count, 20 ms frame. No pulse until explicitly commanded.
    pwm_set_clkdiv(slice,float(clock_get_hz(clk_sys))/1000000.0f); pwm_set_wrap(slice,19999);
    pwm_set_gpio_level(3,0); gpio_set_function(3,GPIO_FUNC_PWM); pwm_set_enabled(slice,true);
    gpio_put(1,calibration::direction);
  }
  safe();
}
void Actuators::safe() {
  permission=false;
  if(stepping) { cancel_repeating_timer(&timer); stepping=false; }
  gpio_put(0,0); pulse=false; gpio_put(2,1); pwm_set_gpio_level(3,0);
}
void Actuators::apply(const physical::Outputs& out,bool permitted) {
  if(!permitted || !calibration::verified) { safe(); return; }
  if(out.motor) {
    pwm_set_gpio_level(3,0); gpio_put(2,0); permission=true;
    if(!stepping) stepping=add_repeating_timer_us(-int64_t(calibration::step_period_us/2),step,nullptr,&timer);
    if(!stepping) safe();
  } else {
    permission=false; if(stepping) { cancel_repeating_timer(&timer); stepping=false; }
    gpio_put(0,0); pulse=false; gpio_put(2,1);
    pwm_set_gpio_level(3,out.gate_open?calibration::servo_open_us:(out.gate_close?calibration::servo_closed_us:0));
  }
}
