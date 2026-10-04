import argparse
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from app.evidence import Journal
from app.utils import sha256

def record(data:dict,journal:Journal):
    required=['test_id','hardware_revision','model_sha256','firmware_version','stimulus','expected','observed','result','evidence_path','operator']
    if any(not data.get(k) for k in required):raise ValueError('All physical record fields required')
    if data['test_id'] not in {f'P{n:02}' for n in range(1,17)} or data['result'] not in {'PASS','FAIL','PENDING'}:raise ValueError('Test/result invalid')
    path=Path(data['evidence_path'])
    if not path.is_file() or data.get('source')!='PHYSICAL':raise ValueError('Existing physical evidence required; simulation cannot PASS acceptance')
    data={**data,'date':datetime.now(timezone.utc).isoformat(),'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'evidence_sha256':sha256(path)}
    journal.append('ACCEPTANCE',data)
def main():
    p=argparse.ArgumentParser(description='Recorder does not certify observed evidence; operator signs PHYSICAL observations')
    p.add_argument('--record',type=Path,required=True);p.add_argument('--journal',type=Path,default=Path('evidence/acceptance/physical.jsonl'))
    a=p.parse_args();record(json.loads(a.record.read_text()),Journal(a.journal,'PHYSICAL'))
if __name__=='__main__':main()
