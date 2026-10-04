#include "sensors.hpp"
#include "calibration.hpp"
#include "pico/stdlib.h"
#include "hardware/sync.h"
#include <algorithm>
#include <cmath>
TwoWire Wire;
bool Sensors::input(unsigned pin,uint32_t now) {
  auto& d=contacts[pin]; bool v=gpio_get(pin)==calibration::active_high[pin];
  if(v!=d.candidate) { d.candidate=v; d.changed=now; }
  if(now-d.changed>=20) d.value=d.candidate;
  return d.value;
}
void Sensors::init() {
  for(unsigned pin=10;pin<=28;++pin) {
    if(pin==11 || pin==23 || pin==24 || pin==25) continue;
    gpio_init(pin); gpio_set_dir(pin,GPIO_IN);
    // External electrical pulls are mandatory; do not hide open circuits with guesses.
  }
  gpio_init(11); gpio_put(11,0); gpio_set_dir(11,GPIO_OUT);
  i2c_init(i2c0,100000); gpio_set_function(4,GPIO_FUNC_I2C); gpio_set_function(5,GPIO_FUNC_I2C);
  for(unsigned pin=6;pin<10;++pin) { gpio_init(pin); gpio_put(pin,0); gpio_set_dir(pin,GPIO_OUT); }
  // Only BOOT initialization is bounded/blocking. Motors are disabled; watchdog starts later.
  sleep_ms(2);
  for(unsigned b=0;b<4;++b) {
    gpio_set_dir(6+b,GPIO_IN); // XSHUT released to module's verified pull-up; no forced 3V3/5V.
    sleep_ms(2); Wire.failed=false; tof[b].setTimeout(50);
    tof_ok[b]=tof[b].init() && !Wire.failed;
    if(tof_ok[b]) { tof[b].setAddress(uint8_t(0x30+b)); tof[b].startContinuous(200); tof[b].setTimeout(1); }
    else { gpio_set_dir(6+b,GPIO_OUT); gpio_put(6+b,0); }
  }
  data.calibrated=calibration::verified;
  contact_start=to_ms_since_boot(get_absolute_time()); data.contacts_valid=false;
}
void Sensors::poll(uint32_t now) {
  data.gpio_raw=gpio_get_all();
  data.lid=input(12,now); data.closed=input(13,now); data.open=input(14,now); data.reset=input(15,now);
  data.service=input(27,now); data.power=input(28,now);
  constexpr unsigned fallpins[]={20,21,22,26};
  for(unsigned b=0;b<4;++b) { data.index[b]=input(16+b,now); data.beam[b]=input(fallpins[b],now); }
  data.contacts_valid=now-contact_start>=20;
  if(!gpio_get(10)) {
    // HX711 bit transfer is bounded (<100 us). SCK high remains below power-down threshold.
    uint32_t irq=save_and_disable_interrupts(); uint32_t raw=0;
    for(unsigned b=0;b<24;++b) { gpio_put(11,1); busy_wait_us_32(1); raw=(raw<<1)|unsigned(gpio_get(10)); gpio_put(11,0); busy_wait_us_32(1); }
    gpio_put(11,1); busy_wait_us_32(1); gpio_put(11,0); restore_interrupts(irq);
    int32_t signed_raw=int32_t(raw | ((raw&0x800000)?0xff000000:0)); data.hx_raw=signed_raw; data.hx_known=true; hx_last=now;
    if(calibration::verified) {
      double mg=(double(signed_raw)-calibration::hx_offset)*calibration::mg_per_count;
      if(std::isfinite(mg) && std::abs(mg)<2147483647) {
        data.weight_mg=int32_t(mg); weights[weight_next]=data.weight_mg; weight_next=(weight_next+1)%weights.size();
        if(weight_count<weights.size()) ++weight_count;
        data.weight_known=weight_count==weights.size();
        auto mm=std::minmax_element(weights.begin(),weights.end());
        data.stable=data.weight_known && int64_t(*mm.second)-*mm.first<=calibration::stable_span_mg;
        data.presence=data.weight_mg>calibration::presence_mg; data.overweight=data.weight_mg>calibration::overweight_mg;
      } else data.weight_known=false;
    }
  }
  if(now-hx_last>500) { data.hx_known=false; data.weight_known=false; data.stable=false; }
  if(now-tof_poll>=50) {
    tof_poll=now; unsigned b=(now/50)%4;
    if(tof_ok[b]) {
      Wire.failed=false;
      if(tof[b].readReg(VL53L0X::RESULT_INTERRUPT_STATUS)&7) {
        unsigned mm=tof[b].readRangeContinuousMillimeters();
        // Reject sensor error statuses as well as bus failures, never map them to empty.
        const unsigned status=(tof[b].readReg(VL53L0X::RESULT_RANGE_STATUS)>>3)&15;
        if(!Wire.failed && !tof[b].timeoutOccurred() && status==11 && mm>0 && mm<8190) {
          ranges[b][range_next[b]]=mm; range_next[b]=(range_next[b]+1)%3; if(range_count[b]<3) ++range_count[b];
          tof_last[b]=now;
          data.tof_mm[b]=int32_t(mm);
          if(calibration::verified && range_count[b]==3) {
            auto sorted=ranges[b]; std::sort(sorted.begin(),sorted.end()); const unsigned median=sorted[1];
            if(median<=calibration::tof_full_mm[b]) data.fill[b]=physical::Fill::FULL;
            else if(median>=calibration::tof_full_mm[b]+calibration::tof_hysteresis_mm[b]) data.fill[b]=physical::Fill::AVAILABLE;
          }
        } else { data.fill[b]=physical::Fill::UNKNOWN; data.tof_mm[b]=-1; }
      }
    }
    for(unsigned n=0;n<4;++n) if(!tof_ok[n] || now-tof_last[n]>1000) { data.fill[n]=physical::Fill::UNKNOWN; data.tof_mm[n]=-1; }
  }
}
