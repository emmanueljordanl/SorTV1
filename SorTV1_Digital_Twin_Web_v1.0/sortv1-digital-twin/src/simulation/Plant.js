import {ToFSensors} from '../sensors/ToFSensors.js';
const toward=(x,y,step)=>x<y?Math.min(y,x+step):Math.max(y,x-step);
export class Plant {
 constructor(){this.lid=true;this.door=true;this.estop=false;this.usb=true;this.piFrozen=false;this.armed=false;this.latch=false;this.power=false;this.gateAngle=0;this.rotorAngle=12;this.targetAngle=0;this.rotorCommand=false;this.gateCommand=null;this.stepRate=0;this.dir=0;this.nEN=1;this.flags={};this.reeds=[false,false,false,false];this.beams=[false,false,false,false];this.beamHistory=[];this.mass=0;this.stable=true;this.object=null;this.levels=[8,12,6,10];this.tof=new ToFSensors();this.routeClear=true;this.fallStart=null;this.motorMoves=0;this.openCommands=0;this.reedStableSince=null;this.confirmedIndex=null;this.gateClosed=true;this.gateOpen=false;this.servoSupply=6;this.binsInspected=true;this.closedAt=0;}
 cut(){this.armed=false;this.latch=true;this.power=false;this.nEN=1;this.rotorCommand=false;this.gateCommand=null;this.stepRate=0;}
 update(dt,now){
  this.power=this.armed&&!this.latch&&this.lid&&this.door&&!this.estop;
  this.servoSupply=this.flags.servoBrownout?3.5:(this.power?6:0);
  if(!this.power){this.rotorCommand=false;this.gateCommand=null;this.nEN=1;this.stepRate=0;}
  const old=this.rotorAngle;
  if(this.power&&this.rotorCommand&&this.nEN===0&&this.gateClosed&&this.routeClear){const speed=this.flags.lostSteps?0:150;this.rotorAngle=toward(this.rotorAngle,this.targetAngle,speed*dt/1000);this.stepRate=Math.abs(this.targetAngle-this.rotorAngle)>0.01?speed/1.8:0;this.dir=this.targetAngle>this.rotorAngle?1:0;if(Math.abs(old-this.rotorAngle)>0)this.motorMoves++;}
  if(this.power&&this.gateCommand!==null&&this.servoSupply>=5&&!this.flags.stall){if(!(this.gateCommand===90&&this.flags.gateNoOpen)&&!(this.gateCommand===0&&this.flags.gateNoClose))this.gateAngle=toward(this.gateAngle,this.gateCommand,120*dt/1000);}
  this.gateClosed=this.gateAngle<0.5&&!this.flags.closedSensorMissing;this.gateOpen=this.gateAngle>=85&&!this.flags.openSensorMissing;
  this.reeds=[0,1,2,3].map(i=>Math.abs(((this.rotorAngle-i*90+540)%360)-180)<1.5);
  if(this.flags.reedMissing)this.reeds.fill(false);if(this.flags.doubleReed){this.reeds[0]=true;this.reeds[1]=true;}
  this.beams.fill(false);
  if(this.object){
   if(this.object.stage==='tray'&&this.gateAngle>45){this.object.stage='falling';this.fallStart=now;this.routeClear=false;}
   if(this.object.stage==='falling'){
    this.object.progress=Math.min(1,(now-this.fallStart)/700);
    if(this.flags.jam)this.object.progress=Math.min(0.24,this.object.progress);
    const requested=this.object.dest;const physicalIndex=Math.round(((this.rotorAngle%360)+360)%360/90)%4;
    this.object.actualBin=this.flags.wrongBin?(requested+1)%4:physicalIndex;
    if(this.object.progress>=0.55&&this.object.progress<0.8&&!this.flags.beamMiss)this.beams[this.object.actualBin]=true;
    if(this.flags.beamBlocked&&this.object.progress>=0.55)this.beams[this.object.actualBin]=true;
    if(this.object.progress>=1){this.object.stage='bin';this.mass=0;}
   }
   if(this.object.stage==='bin'&&this.flags.beamBlocked)this.beams[this.object.actualBin]=true;
   if(this.object.stage==='tray')this.mass=this.flags.overweight?250:(this.flags.unstable?this.object.mass+15*Math.sin(now/35):this.object.mass);
   else if(this.object.progress>0.3)this.mass=0;
  }
  this.stable=!this.flags.unstable;
  const target=this.object?.kind??0;
  if(this.flags.binFull)this.levels[target]=99;
  this.tof.tick(now,this.levels,this.flags,target);
 }
 load(kind){if(this.lid||this.object?.stage==='tray')throw Error('Abrir tapa para depositar');if(!Number.isInteger(kind)||kind<0||kind>3)throw Error('INVALID_OBJECT');this.object={kind,mass:[30,4,18,60][kind],stage:'tray',progress:0,dest:null,actualBin:null};this.mass=this.object.mass;}
 clearManually(){this.object=null;this.mass=0;this.fallStart=null;this.routeClear=true;this.beams.fill(false);this.flags={};this.gateAngle=0;this.gateClosed=true;this.gateOpen=false;this.confirmedIndex=null;this.lid=true;this.door=true;this.estop=false;this.usb=true;this.piFrozen=false;this.tof.samples=Array.from({length:4},()=>[]);this.levels=[8,12,6,10];}
 sensors(){return {TOP_LID:this.lid?'CLOSED':'OPEN',SERVICE_DOOR:this.door?'CLOSED':'OPEN',GATE_CLOSED:this.gateClosed,GATE_OPEN:this.gateOpen,ROT:this.reeds.slice(),BREAK_BEAMS:this.beams.map(x=>x?'BLOCKED':'FREE'),LOAD_CELL_g:this.mass,STABLE:this.stable,TOF:this.tof.bins.map(b=>({...b})),ACTUATOR_POWER:this.power,source:'SIMULATION'};}
}
