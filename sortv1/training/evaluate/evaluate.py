import argparse
import csv
from pathlib import Path
import numpy as np
import torch
from app.inference.preprocessing import softmax
from app.utils import load_json, write_json
from training.train.train import model, Samples
from training.datasets.validate import read_rows, validate_manifest
from .metrics import metrics

def evaluate(checkpoint: Path, manifest: Path, split: str, output: Path, *, search_thresholds=False, technical_smoke=False):
    if search_thresholds and split!="validation": raise ValueError("Threshold optimization is restricted to VALIDATION")
    validate_manifest(manifest,strict=True)
    rows=[r for r in read_rows(manifest) if r["split"]==split and not r.get("excluded_reason")]
    if not rows: raise ValueError("No evaluation samples")
    if not technical_smoke and any(r["source"]!="LOCAL_PHYSICAL" for r in rows): raise ValueError("Final evaluation requires LOCAL_PHYSICAL")
    saved=torch.load(checkpoint,map_location="cpu",weights_only=False); network=model(None)
    network.load_state_dict(saved["state_dict"]); network.eval(); samples=Samples(rows,manifest)
    truth=[]; probabilities=[]
    with torch.no_grad():
        for i,row in enumerate(rows):
            tensor,label=samples[i]; probabilities.append(softmax(network(tensor[None]).numpy())); truth.append(label)
    probabilities=np.asarray(probabilities); predicted=probabilities.argmax(1)
    report=metrics(truth,predicted,probabilities); report.update(split=split,source="SYNTHETIC_TEST" if technical_smoke else "LOCAL_PHYSICAL")
    output.mkdir(parents=True,exist_ok=True); write_json(output/"metrics.json",report)
    with (output/"confusion_matrix.csv").open("w",newline="") as h: csv.writer(h).writerows(report["confusion_matrix"])
    with (output/"predictions.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.writer(h); w.writerow(["object_id","source_image_id","truth","top1","confidence","margin","p0","p1","p2","p3"])
        for row,label,values in zip(rows,truth,probabilities):
            ordered=np.sort(values); w.writerow([row["object_id"],row["source_image_id"],label,int(values.argmax()),float(ordered[-1]),float(ordered[-1]-ordered[-2]),*map(float,values)])
    threshold_report=dict(status="BASELINE",split=split,top1=0.80,margin=0.15,consensus=2,frames=3)
    if search_thresholds:
        candidates=[]
        for threshold in (0.65,0.7,0.75,0.8,0.85,0.9,0.95):
            for difference in (0.10,0.15,0.20,0.25):
                result=metrics(truth,predicted,probabilities,top1=threshold,margin=difference)
                if all(p is not None and p>=0.95 for p in result["selective_purity"][:3]):
                    candidates.append((result["coverage"],threshold,difference))
        if candidates:
            coverage,threshold,difference=max(candidates); threshold_report.update(status="VALIDATION_SELECTED",top1=threshold,margin=difference,coverage=coverage)
        else: threshold_report["status"]="NO_CANDIDATE_MEETS_PURITY"
    write_json(output/"threshold_report.json",threshold_report); return report

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--checkpoint",type=Path,required=True); p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--split",choices=["validation","test"],default="test"); p.add_argument("--output",type=Path,default=Path("evidence/benchmarks/ml"))
    p.add_argument("--search-thresholds",action="store_true"); a=p.parse_args(); print(evaluate(a.checkpoint,a.manifest,a.split,a.output,search_thresholds=a.search_thresholds))
