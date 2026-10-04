export const LABELS=['PET','PAPEL_CARTON','METAL_LATAS','OTRO_SECO_CONOCIDO'];
export function decide(frames){if(frames.length!==3||frames.some(f=>!f.valid||f.age_ms>300||f.probabilities?.length!==4||f.probabilities.some(x=>!Number.isFinite(x)||x<0||x>1)||Math.abs(f.probabilities.reduce((a,b)=>a+b,0)-1)>1e-5))return {decision:'REVIEW',reason:'QUALITY',requested_bin:null};const candidates=frames.map(f=>{const ranked=f.probabilities.map((v,i)=>({v,i})).sort((a,b)=>b.v-a.v);return {id:ranked[0].i,pass:ranked[0].v>0.80&&ranked[0].v-ranked[1].v>0.15,score:ranked[0].v};});for(let i=0;i<4;i++){const votes=candidates.filter(c=>c.id===i&&c.pass);if(votes.length>=2)return {decision:'ACCEPT',predicted_class:LABELS[i],requested_bin:i,score:Math.min(...votes.map(v=>v.score))};}return {decision:'REVIEW',reason:'LOW_CONFIDENCE',requested_bin:null};}
export class InspectionSimulation {
 constructor(twin){this.twin=twin;this.frames=[];this.stage='IDLE';this.started=null;this.done=false;this.modules=Object.fromEntries(['capture','quality','inference','decision','transport','controller','evidence','operator_ui'].map(k=>[k,'WAITING']));}
 start(now){this.started=now;this.frames=[];this.done=false;this.stage='CAPTURE';this.modules.capture='ACTIVE';}
 tick(now){if(this.started===null||this.done||this.twin.plant.piFrozen||!this.twin.plant.usb)return;const t=this.twin,p=t.plant;const age=now-this.started;
  while(this.frames.length<3&&age>=80+100*this.frames.length){const k=p.object.kind;const probabilities=[0.03,0.03,0.03,0.03];probabilities[k]=0.91;const frame={frame_id:`${t.fw.boot}:${t.fw.cycle}:F${this.frames.length}`,cycle_id:t.fw.cycle,timestamp:now,age_ms:p.flags.stale?500:60,valid:!p.flags.cameraCovered&&!p.flags.blur,probabilities,source:'SIMULATION',exposure:'SIMULATED',gain:'SIMULATED',WB:'SIMULATED'};this.frames.push(frame);t.event('CAMERA',`Frame ${'ABC'[this.frames.length-1]} nuevo`,{frame});}
  if(age>=320&&this.stage==='CAPTURE'){this.stage='QUALITY';this.modules.capture='DONE';this.modules.quality='ACTIVE';t.event('QUALITY',p.flags.cameraCovered||p.flags.blur||p.flags.stale?'FAIL':'PASS SIMULATED');}
  if(age>=360&&this.stage==='QUALITY'){this.stage='INFERENCE';this.modules.quality='DONE';this.modules.inference='ACTIVE';t.event('PREPROCESS','ROI → RGB → 224×224 float32 → /255 → ImageNet');}
  if(age>=540&&this.stage==='INFERENCE'){this.stage='DECISION';this.modules.inference='DONE';this.modules.decision='ACTIVE';t.event('INFERENCE','MobileNetV3 Small: probabilidades SIMULADAS; no ONNX ejecutado',{frames:this.frames});}
  if(age>=600&&!this.done){this.done=true;this.modules.decision='DONE';if(p.flags.modelMissing){t.fw.review('MODEL_MISSING');return;}if(p.flags.diskFull){t.fw.review('STORAGE_FULL');return;}
   t.decision=decide(this.frames);t.event('DECISION',JSON.stringify(t.decision));if(t.decision.decision!=='ACCEPT'){t.fw.review(t.decision.reason);return;}
   t.logger.intent(`${t.fw.boot}:${t.fw.cycle}`);t.event('INTENT_PERSISTED','Journal SIMULATED antes de SORT');
   const msg={v:1,boot:t.fw.boot,cycle:t.fw.cycle,request:1,cmd:'SORT',dest:p.flags.invalidDest?4:t.decision.requested_bin};t.sendSort(msg,{corrupt:p.flags.crc});if(p.flags.duplicate)t.sendSort(msg);if(p.flags.ackLost){t.event('ACK_LOST','Consulta y reenvío misma clave');t.sendSort(msg);}
  }
 }
}
