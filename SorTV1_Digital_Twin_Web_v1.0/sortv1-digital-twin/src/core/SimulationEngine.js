import {DigitalTwin} from './DigitalTwin.js';
export function advanceUntil(twin,predicate,limit=15000){let elapsed=0;while(!predicate(twin)&&elapsed<limit){twin.tick(20);elapsed+=20;}return predicate(twin);}
export function readyTwin(data){const t=new DigitalTwin(data);advanceUntil(t,x=>x.plant.tof.bins.every(b=>b.state==='AVAILABLE'),1000);if(!t.action('rearm'))throw Error('REARM_FAILED');advanceUntil(t,x=>x.fw.state==='READY',4000);return t;}
export function runScenario(data,fault=null,kind=2){const t=readyTwin(data);if(fault)t.faults.arm(fault);t.startDemo(kind);advanceUntil(t,x=>x.result!==null||['FAULT','REVIEW','BOOT_SAFE'].includes(x.fw.state),14000);return t;}
