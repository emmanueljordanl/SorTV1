#include "bench_policy.hpp"
#include <cassert>
using K=bench::Policy::Kind;
bench::Policy ready() {bench::Policy p;p.tick(1,true,true,true);p.tick(101,true,true,true);assert(p.ping(1,101));return p;}
int main() {
  {auto p=ready();assert(p.request(K::STEP,2,32,2000,101,true,true,true));assert(!p.request(K::SERVO,3,1500,100,102,true,true,true));p.tick(165,true,true,true);assert(p.kind==K::OFF);}
  for(unsigned issue=0;issue<4;++issue) {auto p=ready();assert(p.request(K::SERVO,2,1500,500,101,true,true,true));p.tick(issue==3?402:102,issue!=0,issue!=1,issue!=2);assert(p.kind==K::OFF && p.latched);assert(!p.request(K::STEP,3,1,2000,403,true,true,true));}
  for(unsigned issue=0;issue<5;++issue) {auto p=ready();assert(!p.request(issue==0?K::SERVO:K::STEP,2,issue==0?3000:(issue==1?33:32),issue==2?100:2000,101,issue!=3,true,issue!=4));}
  {auto p=ready();assert(!p.request(K::STEP,1,1,2000,101,true,true,true));assert(p.request(K::SERVO,2,1500,20,101,true,true,true));p.tick(121,true,true,true);assert(p.kind==K::OFF);}
}
