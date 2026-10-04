"""Human inspection record for one MCU cycle. No communication or motion command."""
import argparse
import time
from pathlib import Path
from app.utils import load_json,write_json
def main():
    p=argparse.ArgumentParser();p.add_argument('--operator',required=True);p.add_argument('--boot',required=True);p.add_argument('--cycle',type=int,required=True)
    for flag in ['single-object','dry-known-catalog','within-limits']:p.add_argument('--'+flag,action='store_true',required=True)
    a=p.parse_args();settings=load_json(Path('config/physical.json'));path=settings.get('admission_record')
    if not path or settings.get('operator')!=a.operator or a.cycle<=0:p.error('Configure admission_record and matching operator in physical.json')
    write_json(Path(path),dict(operator=a.operator,boot=a.boot,cycle=a.cycle,timestamp=time.time(),single_object=True,dry_known_catalog=True,within_size_mass_limits=True,source='PHYSICAL_OPERATOR_INSPECTION'))
if __name__=='__main__':main()
