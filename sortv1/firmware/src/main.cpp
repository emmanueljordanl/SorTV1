#include "pico/stdlib.h"
#include "pico/rand.h"
#include "pico/unique_id.h"
#include "hardware/watchdog.h"
#include "tusb.h"
#include "state_machine.hpp"
#include "protocol.hpp"
#include "sensors.hpp"
#include "actuators.hpp"
#include <cstdio>
#include <cstring>
#include <cstdarg>
namespace {
physical::Machine machine; Sensors sensors; Actuators actuators; wire::Parser parser;
char boot[49]{};
struct Frame { char bytes[512]{}; size_t size=0,sent=0; };
Frame tx[16]; unsigned head=0,tail=0;
uint32_t now_ms() { return to_ms_since_boot(get_absolute_time()); }
void send(const char* format,...) {
  unsigned next=(tail+1)%16;
  if(next==head) { actuators.safe(); machine.fault("TX_OVERFLOW",now_ms()); return; }
  auto& frame=tx[tail]; va_list args; va_start(args,format); int n=vsnprintf(frame.bytes,sizeof frame.bytes-6,format,args); va_end(args);
  if(n<0 || n>505) { actuators.safe(); machine.fault("TX_OVERSIZE",now_ms()); return; }
  unsigned crc=wire::crc16(reinterpret_cast<uint8_t*>(frame.bytes),size_t(n));
  snprintf(frame.bytes+n,7,"|%04X\n",crc); frame.size=size_t(n)+6; frame.sent=0; tail=next;
}
void flush() {
  if(head==tail || !tud_cdc_connected()) return;
  auto& frame=tx[head]; size_t available=tud_cdc_write_available();
  size_t remaining=frame.size-frame.sent; size_t n=remaining<available?remaining:available;
  if(n) { frame.sent+=tud_cdc_write(frame.bytes+frame.sent,uint32_t(n)); tud_cdc_write_flush(); }
  if(frame.sent==frame.size) head=(head+1)%16;
}
const char* boolean(bool v) { return v?"true":"false"; }
const char* fill(physical::Fill f) { return f==physical::Fill::AVAILABLE?"AVAILABLE":(f==physical::Fill::FULL?"FULL":"UNKNOWN"); }
void status() {
  const auto& s=sensors.data; char weight[24],raw[24];
  snprintf(weight,sizeof weight,s.weight_known?"%ld":"null",long(s.weight_mg));
  snprintf(raw,sizeof raw,s.hx_known?"%ld":"null",long(s.hx_raw));
  send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"STATUS\",\"state\":\"%s\",\"cycle\":%lu,\"request\":%lu,\"calibrated\":%s,\"lid\":%s,\"service\":%s,\"power\":%s,\"gate_closed\":%s,\"gate_open\":%s,\"presence\":%s,\"stable\":%s,\"weight_mg\":%s,\"hx_raw\":%s,\"gpio_raw\":%lu,\"fill\":[\"%s\",\"%s\",\"%s\",\"%s\"]}",
       boot,physical::Machine::name(machine.state),(unsigned long)machine.cycle,(unsigned long)machine.request,
       boolean(s.calibrated),boolean(s.lid),boolean(s.service),boolean(s.power),boolean(s.closed),boolean(s.open),boolean(s.presence),boolean(s.stable),weight,raw,(unsigned long)s.gpio_raw,
       fill(s.fill[0]),fill(s.fill[1]),fill(s.fill[2]),fill(s.fill[3]));
}
void done(const physical::Result& r) { send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"DONE\",\"cycle\":%lu,\"request\":%lu,\"seq\":%lu,\"confirmed_bin\":%d}",boot,(unsigned long)r.cycle,(unsigned long)r.request,(unsigned long)r.seq,r.dest); }
void handle(const wire::Command& c,uint32_t now) {
  if(std::strcmp(c.boot,boot)) {
    send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"NACK\",\"cycle\":%lu,\"request\":%lu,\"reason\":\"BOOT_MISMATCH\"}",boot,(unsigned long)c.cycle,(unsigned long)c.request); return;
  }
  if(!std::strcmp(c.cmd,"HEARTBEAT")) { machine.heartbeat(now); return; }
  if(!std::strcmp(c.cmd,"QUERY")) {
    if(c.identity) { if(auto* old=machine.query(c.cycle,c.request)) { if(old->done) done(*old); else send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"ACK\",\"cycle\":%lu,\"request\":%lu}",boot,(unsigned long)c.cycle,(unsigned long)c.request); return; } }
    status(); return;
  }
  const char* reply=machine.sort(c.cycle,c.request,c.dest,sensors.data,now);
  if(!std::strcmp(reply,"DONE")) done(*machine.query(c.cycle,c.request));
  else if(!std::strcmp(reply,"ACK")) send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"ACK\",\"cycle\":%lu,\"request\":%lu}",boot,(unsigned long)c.cycle,(unsigned long)c.request);
  else send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"NACK\",\"cycle\":%lu,\"request\":%lu,\"reason\":\"%s\"}",boot,(unsigned long)c.cycle,(unsigned long)c.request,reply);
}
}
int main() {
  actuators.init(); stdio_init_all();
  pico_unique_board_id_t id; pico_get_unique_board_id(&id);
  uint64_t random=get_rand_64(); // Boot identity changes after reset, not just silicon identity.
  snprintf(boot,sizeof boot,"%02x%02x%02x%02x-%08lx%08lx",id.id[0],id.id[1],id.id[2],id.id[3],(unsigned long)(random>>32),(unsigned long)random);
  sensors.init(); watchdog_enable(2000,true);
  uint32_t last_status=0,last_tick=now_ms(); bool connected=false;
  while(true) {
    uint32_t now=now_ms(); bool usb=tud_cdc_connected();
    if(usb && !connected) { head=tail=0; send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"HELLO\",\"firmware\":\"0.2.0-mvp-rc1\",\"rearm\":\"PHYSICAL_ONLY\"}",boot); }
    if(!usb && connected) { actuators.safe(); machine.fault("USB_DISCONNECTED",now); head=tail=0; parser=wire::Parser{}; }
    connected=usb; parser.expire(now);
    // Bounded parsing budget preserves the cooperative sensor/control tick.
    for(unsigned n=0;n<128 && tud_cdc_available();++n) { wire::Command command; char c=char(tud_cdc_read_char()); if(parser.feed(c,now,command)) handle(command,now); }
    if(now-last_tick>=1) {
      if(now-last_tick>100) { actuators.safe(); machine.fault("LOOP_OVERRUN",now); }
      last_tick=now; sensors.poll(now); machine.tick(now,sensors.data);
      if(machine.inspect_event) send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"INSPECT\",\"cycle\":%lu}",boot,(unsigned long)machine.cycle);
      if(machine.done_event) { if(auto* result=machine.query(machine.cycle,machine.request)) done(*result); }
      if(machine.fault_event) {
        if(machine.cycle) send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"FAULT\",\"cycle\":%lu,\"request\":%lu,\"seq\":%lu,\"reason\":\"%s\"}",boot,(unsigned long)machine.cycle,(unsigned long)machine.request,(unsigned long)machine.seq,machine.reason);
        else send("{\"v\":1,\"boot\":\"%s\",\"cmd\":\"FAULT\",\"seq\":%lu,\"reason\":\"%s\"}",boot,(unsigned long)machine.seq,machine.reason);
      }
      actuators.apply(machine.outputs,sensors.data.calibrated && sensors.data.power && sensors.data.lid && sensors.data.service && usb);
      watchdog_update();
    }
    if(usb && now-last_status>=250) { last_status=now; status(); }
    flush(); tight_loop_contents();
  }
}
