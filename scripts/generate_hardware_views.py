"""Lossless canonical CSV -> twin JSON and reviewable physical tables."""
import argparse
import csv
import io
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'sortv1/hardware/source'
TWIN=ROOT/'SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin/data'

def read(name):
    with (SOURCE/name).open(newline='',encoding='utf-8') as f: return list(csv.DictReader(f))
def csv_text(rows, fields=None):
    s=io.StringIO(newline=''); w=csv.DictWriter(s,fieldnames=fields or list(rows[0]),lineterminator='\n'); w.writeheader(); w.writerows(rows); return s.getvalue()
def views():
    out={}; bom=read('bom_master.csv'); pins=read('pinout_master.csv'); wires=read('connections_master.csv'); connectors=read('connectors_master.csv')
    def js(path,data): out[path]=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    twin=[json.loads(x['source_json']) for x in bom if x['record_kind']=='TWIN']
    js(TWIN/'bom.json',twin); js(TWIN/'bom_baseline.json',twin)
    js(TWIN/'components.json',[json.loads(x['component_json']) for x in bom if x['record_kind']=='TWIN'])
    js(TWIN/'pinout.json',[json.loads(x['source_json']) for x in pins])
    js(TWIN/'wiring.json',[json.loads(x['source_json']) for x in wires if x['record_kind']=='TWIN'])
    js(TWIN/'connectors.json',[json.loads(x['source_json']) for x in connectors])
    hw=ROOT/'sortv1/hardware'
    out[hw/'pinout/pico.csv']=csv_text([json.loads(x['plan_json']) for x in pins])
    out[hw/'bom/bom.csv']=csv_text([json.loads(x['source_json']) for x in bom if x['record_kind']=='PLAN_ALLOCATION'])
    fields=['id','component_id','item','quantity','mvp_category','planned_mxn_2026_09_15','actual_quote_mxn','vendor','part_number','purchase_status']
    out[hw/'bom/bom_mvp_minimum.csv']=csv_text([{k:x[k] for k in fields} for x in bom if x['record_kind']!='PLAN_ALLOCATION'])
    out[hw/'bom/bom_traceability.csv']=csv_text([dict(purchase_id=x['id'],twin_bom_id=x['id'] if x['record_kind']=='TWIN' else '',twin_component_id=x['component_id'],source=x['record_kind'],status='PENDING_PHYSICAL_VALIDATION') for x in bom if x['record_kind']!='PLAN_ALLOCATION'])
    fromto=[]
    for row in wires:
        x=json.loads(row['source_json'])
        fromto.append(dict(wire_id=x['id'],from_component=x['from_component'],from_pin=x['from_pin'],to_component=x['to_component'],to_pin=x['to_pin'],signal=x['signal'],
          voltage_domain=x['voltage'],wire_gauge_or_type='TBC_MEASURE'+(f" (referencia {x['awg']} AWG)" if x.get('awg') else ''),connector=x['connector'],fuse=x['fuse'],shield='TBC_MEASURE',
          notes=f"Referencia de gemelo; NO es cableado aprobado. {x['route']}. Validar pin real, polaridad y corte DC. Longitud TBC_MEASURE",status='PENDING_PHYSICAL_VALIDATION'))
    out[hw/'wiring/wire_from_to.csv']=csv_text(fromto)
    out[hw/'wiring/terminal_matrix.csv']=csv_text([dict(connector_id=x['id'],**json.loads(x['source_json']),approval='TBC_MODEL',rated_current='TBC_MEASURE',wire_range='TBC_MODEL') for x in connectors])
    out[hw/'wiring/fuse_matrix.csv']=csv_text([dict(fuse_id=fid,branch=branch,planned_reference=ref,approved_rating='TBC_MEASURE',breaking_capacity='TBC_MODEL',load_current='TBC_MEASURE',wire_gauge='TBC_MEASURE',status='PENDING_PHYSICAL_VALIDATION') for fid,branch,ref in [('F_MAIN','12V entrada','~5 A historico no aprobado'),('F_MOTOR','VMOT','~2-3 A historico no aprobado'),('F_SERVO','buck entrada/salida validar','~3-5 A historico no aprobado'),('F_AUX','LED/cadena','TBC_MODEL')]])
    out[hw/'pinout/signals.csv']=csv_text(read('signals_master.csv'))
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();errors=[]
    for path,content in views().items():
        if a.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=content: errors.append(str(path.relative_to(ROOT)))
        else: path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8',newline='\n')
    if errors: raise SystemExit('Derived views diverge: '+', '.join(errors))
    print('Canonical hardware views verified' if a.check else 'Canonical views generated without losing twin fields')
if __name__=='__main__':main()
