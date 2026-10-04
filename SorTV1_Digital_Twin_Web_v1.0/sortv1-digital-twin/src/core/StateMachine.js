let bootCounter=0;
export const ACTIVE=['CHECK_HOME','POSITIONING','DISPENSING','VERIFY_CLOSE'];
export class StateMachine {
 constructor(twin){this.twin=twin;this.boot=`sim-b${++bootCounter}`;this.cycle=0;this.state='BOOT_SAFE';this.entered=0;this.cache=new Map();this.operation=null;this.lastHeartbeat=0;this.lastIndex=null;this.indexSince=0;this.seenBlocked=false;this.seenFree=false;this.openSeen=false;this.doneKeys=new Set();this.reason=null;this.cycleStarted=null;this.lastBeam=[false,false,false,false];this.twin.plant.cut();}
 transition(next,detail){const old=this.state;this.state=next;this.entered=this.twin.clock.now;this.twin.event('STATE',`${old} → ${next}: ${detail}`,{from:old,to:next});}
 safeStop(){this.twin.plant.cut();}
 fault(reason){if(this.state==='FAULT')return;this.reason=reason;this.safeStop();this.transition('FAULT',reason);this.twin.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,cmd:'FAULT',reason});}
 review(reason){if(['FAULT','REVIEW'].includes(this.state))return;this.reason=reason;this.safeStop();this.transition('REVIEW',reason);this.twin.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,cmd:'STATUS',state:'REVIEW',reason});}
 rearm(){const p=this.twin.plant;if(!['BOOT_SAFE','FAULT','REVIEW'].includes(this.state)||p.estop||!p.lid||!p.door||!p.routeClear||p.mass>1||!p.gateClosed||p.gateOpen||!p.binsInspected||!p.usb||p.piFrozen)return false;if(p.tof.addresses.some(x=>x===null))return false;p.latch=false;p.armed=true;p.power=true;p.nEN=0;p.targetAngle=Math.round(p.rotorAngle/360)*360;p.rotorCommand=true;this.operation=null;this.cache.clear();this.reason=null;this.lastIndex=null;this.indexSince=this.twin.clock.now;this.cycleStarted=null;this.lastHeartbeat=this.twin.clock.now;this.transition('CHECK_HOME','Rearme físico simulado + inspección manual de recorrido vacío');return true;}
 receive(m){const t=this.twin,p=t.plant;const nack=reason=>{t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,request:m.request??null,cmd:'NACK',reason});return {accepted:false,reason};};
  if(m.cmd==='HEARTBEAT'){if(m.boot!==this.boot)return nack('BOOT');this.lastHeartbeat=t.clock.now;return {accepted:true};}
  if(m.cmd==='QUERY'){t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,cmd:'STATUS',state:this.state,result:this.operation?.result??null});return {accepted:true};}
  if(m.cmd!=='SORT')return nack('COMMAND');
  if(m.boot!==this.boot)return nack('BOOT');if(!Number.isInteger(m.cycle)||m.cycle!==this.cycle||m.cycle<1)return nack('CYCLE');if(!Number.isInteger(m.request)||m.request<0)return nack('REQUEST');if(!Number.isInteger(m.dest)||m.dest<0||m.dest>3)return nack('DEST');
  const key=`${m.boot}:${m.cycle}:${m.request}`;const prior=this.cache.get(key);if(prior){if(prior.dest!==m.dest)return nack('ID_CONFLICT');t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,request:m.request,cmd:'ACK',duplicate:true,status:prior.result??this.state});return {accepted:true,duplicate:true};}
  if(this.operation)return nack('CYCLE_ALREADY_CLAIMED');if(this.state!=='WAIT_DECISION')return nack('STATE');if(t.clock.now-this.entered>2000)return nack('EXPIRED');
  if(!p.power||!p.lid||!p.door||p.estop||!p.gateClosed||p.gateOpen||!p.routeClear||!p.stable||p.mass>200||!p.object||p.object.stage!=='tray')return nack('GUARD');
  if(p.tof.bins[m.dest].state!=='AVAILABLE'){this.review(`BIN_${m.dest}_${p.tof.bins[m.dest].state}`);return nack('CAPACITY');}
  this.operation={key,dest:m.dest,request:m.request,result:null};this.cache.set(key,this.operation);p.object.dest=m.dest;this.lastIndex=null;this.indexSince=t.clock.now;this.seenBlocked=false;this.seenFree=false;this.openSeen=false;this.lastBeam=p.beams.slice();p.confirmedIndex=null;p.targetAngle=m.dest*90;while(p.targetAngle-p.rotorAngle>180)p.targetAngle-=360;while(p.targetAngle-p.rotorAngle< -180)p.targetAngle+=360;p.nEN=0;p.rotorCommand=true;this.transition('POSITIONING',`SORT destination=${m.dest}, guardas válidas`);t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,request:m.request,cmd:'ACK'});return {accepted:true};
 }
 tick(){const t=this.twin,p=t.plant,now=t.clock.now,elapsed=now-this.entered;
  if(['FAULT','REVIEW','BOOT_SAFE'].includes(this.state))return;
  if(p.estop){this.fault('E_STOP');return;}
  if(ACTIVE.includes(this.state)&&(!p.lid||!p.door||!p.power)){this.fault(!p.lid?'TOP_LID':!p.door?'SERVICE_DOOR':'ACTUATOR_POWER_LOST');return;}
  if(!p.door){this.fault('SERVICE_DOOR');return;}
  if(now-this.lastHeartbeat>=1000){this.fault('HEARTBEAT_LOST');return;}
  if(p.gateClosed&&p.gateOpen){this.fault('CONTRADICTORY_LIMITS');return;}
  if(p.reeds.filter(Boolean).length>1){this.fault('MULTIPLE_REEDS');return;}
  if(this.cycleStarted!==null&&now-this.cycleStarted>10000){this.fault('CYCLE_DEADLINE');return;}
  if(this.state==='CHECK_HOME'||this.state==='POSITIONING'){
   if(!p.gateClosed||p.gateOpen||!p.routeClear){this.fault('ROTOR_GUARD');return;}
   const target=this.state==='CHECK_HOME'?0:this.operation.dest;const detected=p.reeds[target]&&p.reeds.filter(Boolean).length===1;
   if(detected){if(this.lastIndex!==target){this.lastIndex=target;this.indexSince=now;p.rotorCommand=false;p.stepRate=0;t.event('REED',`ROT${target} detectado`);}if(now-this.indexSince>=100){p.confirmedIndex=target;p.rotorCommand=false;p.stepRate=0;t.event('INDEX_CONFIRMED',`ROT${target} exclusivo estable 100 ms`);if(this.state==='CHECK_HOME'){p.nEN=1;this.transition('READY','Homing confirmado');}else{this.transition('DISPENSING','Índice confirma posición real');p.gateCommand=90;p.openCommands++;t.event('GATE_OPEN_COMMAND','PWM autorizado una sola vez');}return;}}
   else if(this.lastIndex!==null){this.fault('REED_UNSTABLE');return;}
   if(elapsed>=3000)this.fault('POSITION_TIMEOUT');return;
  }
  if(this.state==='READY'){
   p.nEN=1;p.rotorCommand=false;p.gateCommand=null;
   if(!p.gateClosed){this.fault('GATE_NOT_CLOSED_READY');return;}
   if(p.lid&&p.object?.stage==='tray'){this.transition('WAIT_STABLE','Tapa cerrada con presencia');}return;
  }
  if(this.state==='WAIT_STABLE'){
   if(!p.lid){this.transition('READY','Carga no finalizada');return;}
   if(p.mass>200){this.review('OVERWEIGHT');return;}if(elapsed>2000&&!p.stable){this.review('UNSTABLE_WEIGHT');return;}
   if(p.stable&&elapsed>=400&&p.object?.stage==='tray'){this.cycle++;this.cycleStarted=now;this.operation=null;this.transition('WAIT_DECISION','Presencia estable; ciclo nuevo');t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,cmd:'INSPECT'});t.pi.start(now);}return;
  }
  if(this.state==='WAIT_DECISION'){
   if(!p.lid){this.review('LID_OPEN_DURING_INSPECTION');return;}if(p.mass>200){this.review('OVERWEIGHT');return;}
   if(elapsed>=2000)this.review('DECISION_TIMEOUT');return;
  }
  if(this.state==='DISPENSING'||this.state==='VERIFY_CLOSE'){
   if(p.confirmedIndex!==this.operation.dest||!p.reeds[this.operation.dest]){this.fault('INDEX_LOST');return;}
   for(let i=0;i<4;i++){if(p.beams[i]&&!this.lastBeam[i]){t.event('BEAM_BLOCKED',`BIN${i}`);if(i!==this.operation.dest){this.fault('WRONG_BIN');return;}this.seenBlocked=true;}if(!p.beams[i]&&this.lastBeam[i]){t.event('BEAM_FREE',`BIN${i}`);if(i===this.operation.dest&&this.seenBlocked)this.seenFree=true;}}
   this.lastBeam=p.beams.slice();
  }
  if(this.state==='DISPENSING'){
   if(p.gateOpen&&!this.openSeen){this.openSeen=true;this.openAt=now;t.event('OPEN_CONFIRMED','Final OPEN físico simulado');}
   if(!this.openSeen&&elapsed>=1000){this.fault('OPEN_TIMEOUT');return;}
   if(this.openSeen&&this.seenFree&&p.mass<=1&&!p.beams.some(Boolean)){
    p.routeClear=true;t.event('FALL_CONFIRMED',`BIN${this.operation.dest}; haz completo y bandeja vacía`);p.gateCommand=0;this.transition('VERIFY_CLOSE','Cerrar después de caída confirmada');t.event('GATE_CLOSE_COMMAND','PWM cierre');return;}
   if(this.openSeen&&now-this.openAt>=2000)this.fault(p.beams.some(Boolean)?'BEAM_STUCK':p.mass>1?'OBJECT_JAM':'FALL_UNCONFIRMED');return;
  }
  if(this.state==='VERIFY_CLOSE'){
   if(p.gateClosed&&!p.gateOpen&&this.openSeen&&this.seenFree&&p.mass<=1&&!p.beams.some(Boolean)){
    const key=`${this.boot}:${this.cycle}`;if(this.doneKeys.has(key))return;
    this.doneKeys.add(key);this.operation.result='DONE';p.gateCommand=null;p.nEN=1;
    t.event('CLOSED_CONFIRMED','Final CLOSED físico simulado');t.protocol('PICO',{v:1,boot:this.boot,cycle:this.cycle,request:this.operation.request,cmd:'DONE',confirmed_bin:this.operation.dest});
    t.result={cycle_id:key,predicted_class:t.decision.predicted_class,decision:t.decision.decision,score:t.decision.score,requested_bin:this.operation.dest,confirmed_bin:this.operation.dest,physical_result:'DONE',source:'SIMULATION',result_kind:'SIMULATED',cycle_ms:now-this.cycleStarted,model_sha256:null,model_status:'SIMULATED_NO_MODEL',firmware:'conceptual-js-1.0',config_sha256:t.configHash??null,error_code:null};
    if(t.logger.commit(key,this.operation.dest)){t.event('PERSISTED','JSONL y contador consolidados una vez',{result:t.result});p.levels[this.operation.dest]+=2;t.event('TOF_UPDATE','Lectura secuencial de nivel después del ciclo');}
    this.cycleStarted=null;this.transition('READY','DONE confirmado');return;
   }
   if(elapsed>=1000)this.fault('CLOSE_TIMEOUT');
  }
 }
}
