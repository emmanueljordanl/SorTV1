// Separate bench image. Production calibration and SORT are never enabled here.
#include "bench_policy.hpp"
#include "protocol.hpp"
#include "pico/stdlib.h"
#include "pico/rand.h"
#include "hardware/watchdog.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"
#include "tusb.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cctype>
#include <initializer_list>
namespace {
bench::Policy policy;
char boot[20]{};
unsigned slice=0,remaining=0;
uint32_t next_edge=0;
bool level=false;
void safe() {gpio_put(2,1);gpio_put(0,0);pwm_set_gpio_level(3,0);remaining=0;level=false;}
bool guards() {return !gpio_get(12) && !gpio_get(27) && !gpio_get(28);}
uint32_t ms() {return to_ms_since_boot(get_absolute_time());}
void emit(const char* cmd,unsigned seq,unsigned a,unsigned b) {
  char payload[120];int n=snprintf(payload,sizeof payload,"BENCH1|%s|%s|%u|%u|%u",boot,cmd,seq,a,b);
  unsigned crc=wire::crc16(reinterpret_cast<uint8_t*>(payload),size_t(n));
  // Bounded write; no stdio blocking inside the motion loop.
  if(tud_cdc_connected() && tud_cdc_write_available()>=unsigned(n+6)) {
    char line[128];int len=snprintf(line,sizeof line,"%s|%04X\n",payload,crc);
    tud_cdc_write(line,unsigned(len));tud_cdc_write_flush();
  }
}
bool number(const char* t,unsigned& v) {
  if(!*t || strlen(t)>10) return false;
  for(const char* c=t;*c;++c) if(!isdigit(static_cast<unsigned char>(*c))) return false;
  char* end=nullptr;unsigned long n=strtoul(t,&end,10);
  if(*end || n>0xFFFFFFFFul) return false;
  v=unsigned(n);return true;
}
void handle(char* line,uint32_t now) {
  char* last=strrchr(line,'|');if(!last || strlen(last+1)!=4) return;
  for(char* c=last+1;*c;++c) if(!isxdigit(static_cast<unsigned char>(*c))) return;
  unsigned expected=unsigned(strtoul(last+1,nullptr,16));
  if(wire::crc16(reinterpret_cast<uint8_t*>(line),size_t(last-line))!=expected) return;
  *last=0;char* parts[6]{};unsigned count=0;
  char* save=nullptr;
  for(char* t=strtok_r(line,"|",&save);t;t=strtok_r(nullptr,"|",&save)) {if(count==6) return;parts[count++]=t;}
  if(count!=6 || strcmp(parts[0],"BENCH1") || strcmp(parts[1],boot)) return;
  unsigned seq,a,b;if(!number(parts[3],seq) || !number(parts[4],a) || !number(parts[5],b)) return;
  if(!strcmp(parts[2],"PING")) {if(a==0 && b==0) policy.ping(seq,now);return;}
  if(!strcmp(parts[2],"STOP")) {policy.safe();safe();emit("STOPPED",seq,0,0);return;}
  auto kind=!strcmp(parts[2],"STEP")?bench::Policy::Kind::STEP:(!strcmp(parts[2],"SERVO")?bench::Policy::Kind::SERVO:bench::Policy::Kind::OFF);
  if(!policy.request(kind,seq,a,b,now,tud_cdc_connected(),guards(),!gpio_get(15))) {emit("REJECTED",seq,0,0);return;}
  safe();
  if(kind==bench::Policy::Kind::STEP) {remaining=a*2;next_edge=time_us_32();gpio_put(2,0);}
  else pwm_set_gpio_level(3,a);
  emit("ACCEPTED",seq,a,b);
}
}
int main() {
  gpio_init(2);gpio_put(2,1);gpio_set_dir(2,GPIO_OUT);gpio_set_drive_strength(2,GPIO_DRIVE_STRENGTH_8MA);
  for(unsigned p:{0u,1u,3u}) {gpio_init(p);gpio_put(p,0);gpio_set_dir(p,GPIO_OUT);}
  for(unsigned p:{12u,15u,27u,28u}) {gpio_init(p);gpio_set_dir(p,GPIO_IN);gpio_disable_pulls(p);}
  slice=pwm_gpio_to_slice_num(3);pwm_set_clkdiv(slice,float(clock_get_hz(clk_sys))/1000000.0f);pwm_set_wrap(slice,19999);
  pwm_set_gpio_level(3,0);gpio_set_function(3,GPIO_FUNC_PWM);pwm_set_enabled(slice,true);
  safe();stdio_init_all();watchdog_enable(1000,true);
  char line[160]{};unsigned used=0;uint32_t partial_at=0,last_status=0;bool connected=false,discard=false;
  while(true) {
    uint32_t now=ms();bool usb=tud_cdc_connected();
    if(usb && !connected) {safe();policy=bench::Policy{};snprintf(boot,sizeof boot,"%08lx",static_cast<unsigned long>(get_rand_32()));emit("HELLO",0,0,0);used=0;discard=false;}
    if(!usb && connected) {policy.safe();policy.latched=true;safe();used=0;discard=false;}
    connected=usb;policy.tick(now,usb,guards(),!gpio_get(15));
    if(policy.kind==bench::Policy::Kind::OFF) safe();
    else if(policy.kind==bench::Policy::Kind::STEP && remaining && int32_t(time_us_32()-next_edge)>=0) {
      level=!level;gpio_put(0,level);--remaining;next_edge=time_us_32()+policy.b/2;
      if(!remaining) {policy.safe();safe();emit("DONE",policy.seq,0,0);}
    }
    if(used && uint32_t(now-partial_at)>200) {used=0;discard=true;}
    for(unsigned n=0;n<64 && tud_cdc_available();++n) {
      char c=char(tud_cdc_read_char());
      if(c=='\n') {if(!discard && used) {line[used]=0;handle(line,now);}used=0;discard=false;}
      else if(!discard) {if(!used) partial_at=now;if(used<sizeof line-1 && c>=32 && c<=126) line[used++]=c;else {discard=true;used=0;}}
    }
    if(usb && uint32_t(now-last_status)>=250) {last_status=now;unsigned mask=(!gpio_get(12)?1u:0u)|(!gpio_get(27)?2u:0u)|(!gpio_get(28)?4u:0u)|(!gpio_get(15)?8u:0u);emit("STATUS",policy.seq,mask,policy.latched?1u:0u);}
    watchdog_update();tight_loop_contents();
  }
}
