"""Build immutable ZIP with commit identity; generated assets never become source."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'artifacts');a=p.parse_args()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    twin=ROOT/'SorTV1_Digital_Twin_Web_v1.0/sortv1-digital-twin';subprocess.run(['npm.cmd' if __import__('os').name=='nt' else 'npm','run','build'],cwd=twin,check=True)
    a.output.mkdir(parents=True,exist_ok=True);target=a.output/f'SorTV1-0.2.0-mvp-rc1-{commit[:12]}-twin.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted((twin/'dist').rglob('*')):
            if file.is_file():z.write(file,file.relative_to(twin))
        for name in ['scripts/serve-dist.mjs','LICENSE','README.md']:
            if (twin/name).is_file():z.write(twin/name,name)
        if not (twin/'LICENSE').is_file(): z.write(ROOT/'LICENSE','LICENSE')
        z.writestr('BUILD.json',json.dumps({'git_commit':commit,'version':'0.2.0-mvp-rc1','source':'SOFTWARE_BUILD','physical_acceptance':'PENDING'}))
    target.with_suffix('.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
    print(target)
