export class EventLogger {
 constructor(){this.events=[];this.protocol=[];this.journal={pending:null,committed:[]};this.counts=[0,0,0,0];}
 append(event){const row=structuredClone({...event,source:'SIMULATION',result_kind:'SIMULATED'});this.events.push(row);return row;}
 intent(key){this.journal.pending=key;}
 commit(key,bin){if(this.journal.committed.includes(key))return false;this.journal.committed.push(key);this.journal.pending=null;this.counts[bin]++;return true;}
 export(format='jsonl'){const rows=this.events.map(e=>({...e,source:'SIMULATION',result_kind:'SIMULATED'}));if(format==='json')return JSON.stringify({source:'SIMULATION',events:rows,counts:this.counts},null,2);if(format==='csv'){const cols=['source','result_kind','t_ms','boot','cycle','type','state','detail'];return cols.join(',')+'\n'+rows.map(r=>cols.map(k=>'"'+String(typeof r[k]==='object'?JSON.stringify(r[k]):r[k]??'').replaceAll('"','""')+'"').join(',')).join('\n');}return rows.map(r=>JSON.stringify(r)).join('\n')+'\n';}
}
