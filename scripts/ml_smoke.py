"""Technical end-to-end ML fixture; never product or physical acceptance evidence."""
from pathlib import Path
import argparse
import json
import sys
import uuid
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"sortv1"))
import numpy as np
from PIL import Image
from app.utils import sha256,write_json
from training.datasets.validate import write_rows
from training.train.train import train
from training.evaluate.evaluate import evaluate
from training.export.export_onnx import export

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=ROOT/".tools/ml-smoke"); a=p.parse_args()
    work=a.output/uuid.uuid4().hex; work.mkdir(parents=True); rng=np.random.default_rng(42); rows=[]
    for split,count in (("train",8),("validation",52)):
        for i in range(count):
            path=work/f"{split}-{i}.png"; Image.fromarray(rng.integers(0,256,(64,80,3),dtype=np.uint8)).save(path)
            rows.append(dict(object_id=f"{split}-{i}",session_id="technical",class_id=str(i%4),split=split,image_path=str(path.resolve()),
                             source="SYNTHETIC_TEST",source_dataset="TECHNICAL_FIXTURE",source_version="1",source_image_id=sha256(path),
                             lighting_setup="SYNTHETIC",operator="CI",sha256=sha256(path),excluded_reason=""))
    manifest=work/"manifest.csv"; write_rows(manifest,rows)
    config=dict(manifest=str(manifest),output=str(work/"experiment"),seed=42,device="auto",threads=2,batch_size=4,workers=0,
                head_epochs=1,finetune_epochs=1,head_learning_rate=1e-3,finetune_learning_rate=1e-4,finetune_last_blocks=2,
                early_stopping_patience=5,augmentation=dict(rotation_degrees=10,translation_fraction=0.04,brightness=[0.9,1.1],contrast=[0.95,1.05]))
    checkpoint=train(config,technical_smoke=True)
    evaluate(checkpoint,manifest,"validation",work/"evaluation",technical_smoke=True)
    record=export(checkpoint,manifest,work/"package")
    if not record["equivalence"]["passed"]: raise RuntimeError("Technical ONNX equivalence failed")
    write_json(work/"SMOKE_RESULT.json",dict(result="PASS_SOFTWARE_ONLY",source="SYNTHETIC_TEST",equivalence=record["equivalence"]))
    print(json.dumps({"source":"SYNTHETIC_TEST","result":"PASS_SOFTWARE_ONLY","path":str(work)}))
if __name__=="__main__":main()
