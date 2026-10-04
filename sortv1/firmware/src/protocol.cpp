#include "protocol.hpp"
#include <cstring>
#include <cstdlib>
#include <cstdio>
namespace wire {
uint16_t crc16(const uint8_t* data,size_t size) {
  uint16_t c=0xffff;
  for(size_t i=0;i<size;++i) { c^=uint16_t(data[i])<<8; for(int j=0;j<8;++j) c=(c&0x8000)?uint16_t((c<<1)^0x1021):uint16_t(c<<1); }
  return c;
}
namespace {
void ws(char*& p) { while(*p==' ' || *p=='\t') ++p; }
bool string(char*& p,char* out,size_t capacity) {
  if(*p++!='"') return false;
  size_t n=0;
  while(*p && *p!='"') { unsigned char c=*p++; if(c<32 || c>126 || c=='\\' || n+1>=capacity) return false; out[n++]=char(c); }
  if(*p++!='"') return false;
  out[n]=0; return true;
}
bool integer(char*& p,uint32_t& out) {
  if(*p<'0'||*p>'9') return false;
  if(*p=='0' && p[1]>='0' && p[1]<='9') return false;
  uint64_t value=0;
  while(*p>='0' && *p<='9') { value=value*10+unsigned(*p++-'0'); if(value>0xffffffffULL) return false; }
  out=uint32_t(value); return true;
}
}
bool decode(char* line,size_t size,Command& out) {
  if(size<7 || size>512 || line[size-1]!='\n') return false;
  const size_t pipe=size-6;
  if(line[pipe]!='|') return false;
  unsigned checksum=0;
  for(size_t k=pipe+1;k<size-1;++k) { const char c=line[k]; unsigned v;
    if(c>='0'&&c<='9') v=unsigned(c-'0'); else if(c>='a'&&c<='f') v=unsigned(c-'a'+10); else if(c>='A'&&c<='F') v=unsigned(c-'A'+10); else return false;
    checksum=(checksum<<4)|v;
  }
  if(crc16(reinterpret_cast<uint8_t*>(line),pipe)!=checksum) return false;
  line[pipe]=0; char* p=line; ws(p); if(*p++!='{') return false;
  unsigned fields=0; out={}; uint32_t version=0;
  while(true) {
    ws(p); char key[24]{}; if(!string(p,key,sizeof key)) return false;
    ws(p); if(*p++!=':') return false; ws(p);
    unsigned bit=0; uint32_t value=0;
    if(!std::strcmp(key,"v")) { bit=1; if(!integer(p,version)) return false; }
    else if(!std::strcmp(key,"boot")) { bit=2; if(!string(p,out.boot,sizeof out.boot)) return false; }
    else if(!std::strcmp(key,"cmd")) { bit=4; if(!string(p,out.cmd,sizeof out.cmd)) return false; }
    else if(!std::strcmp(key,"cycle")) { bit=8; if(!integer(p,out.cycle)) return false; }
    else if(!std::strcmp(key,"request")) { bit=16; if(!integer(p,out.request)) return false; }
    else if(!std::strcmp(key,"dest")) { bit=32; if(!integer(p,value) || value>3) return false; out.dest=int(value); }
    else return false;
    if(fields&bit) return false;
    fields|=bit; ws(p); if(*p=='}') { ++p; break; } if(*p++!=',') return false;
  }
  ws(p); if(*p || (fields&7)!=7 || version!=1 || !out.boot[0]) return false;
  out.identity=(fields&24)==24;
  if(!std::strcmp(out.cmd,"SORT")) return fields==63 && out.request!=0 && out.cycle!=0;
  if(!std::strcmp(out.cmd,"HEARTBEAT")) return fields==7;
  if(!std::strcmp(out.cmd,"QUERY")) return fields==7 || fields==31;
  return false;
}
void Parser::expire(uint32_t now) { if(used && now-started>=250) { used=0; discard=true; ++errors; } }
bool Parser::feed(char value,uint32_t now,Command& out) {
  expire(now);
  if(discard) { if(value=='\n') discard=false; return false; }
  if(!used) started=now;
  if(used==512) { used=0; discard=value!='\n'; ++errors; return false; }
  bytes[used++]=value;
  if(value!='\n') return false;
  const bool ok=decode(bytes,used,out); used=0; if(!ok) ++errors; return ok;
}
}
