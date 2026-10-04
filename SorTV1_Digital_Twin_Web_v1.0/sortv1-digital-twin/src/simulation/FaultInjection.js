export class FaultInjection {
 constructor(twin,definitions){this.twin=twin;this.definitions=definitions;this.selected=null;this.fired=false;}
 arm(id){this.selected=this.definitions.find(f=>f.id===id)??null;this.fired=false;this.twin.event('FAULT_ARMED',this.selected?.title??'Sin fallo');}
 tick(){const f=this.selected,t=this.twin;if(!f||this.fired||t.fw.state!==f.phase)return;if(f.phase==='POSITIONING'&&t.clock.now-t.fw.entered<120)return;this.fire(f);}
 fire(f=this.selected){if(!f)return;this.fired=true;const t=this.twin,p=t.plant;t.event('FAULT_INJECTED',`${f.id} ${f.title}`,{fault_id:f.id});
  if(f.flag==='estop'){p.estop=true;p.power=false;}
  else if(f.flag==='lid'){p.lid=false;p.power=false;}
  else if(f.flag==='door'){p.door=false;p.power=false;}
  else if(f.flag==='usb')p.usb=false;
  else if(f.flag==='piFrozen')p.piFrozen=true;
  else if(f.flag==='picoReset')t.rebootPico();
  else if(f.flag==='crashAfterFall'){t.rebootPi(true);}
  else{p.flags[f.flag]=true;if(f.flag==='tofInvalid'){p.tof.bins[p.object.kind].state='UNKNOWN';p.tof.bins[p.object.kind].level=null;}if(f.flag==='binFull'){p.levels[p.object.kind]=99;p.tof.samples[p.object.kind]=[];p.tof.bins[p.object.kind].state='FULL';}}
 }
}
