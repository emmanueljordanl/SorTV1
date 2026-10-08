import argparse
from pathlib import Path
import shutil
import numpy as np
import torch
import onnx
import onnxruntime as ort
from app.contracts import LABELS
from app.inference.preprocessing import DEFAULT, softmax
from app.utils import sha256, write_json, load_json
from training.datasets.validate import read_rows, validate_manifest
from training.train.train import model, Samples
from training.thresholds import load_selection, copy_selected

def export(checkpoint: Path, manifest: Path, output: Path, *, logits_atol=1e-4, probabilities_atol=1e-5, thresholds=None, test_report=None, technical_smoke=False):
    if thresholds is None: raise ValueError("Export requires frozen --thresholds from VALIDATION")
    selected=load_selection(thresholds,checkpoint,manifest,technical_smoke=technical_smoke)
    if test_report is None: raise ValueError("Export requires frozen TEST --test-report")
    tested=load_json(test_report)
    if tested.get("split") != "test" or tested.get("threshold_selection_sha256") != sha256(thresholds) or tested.get("checkpoint_sha256") != sha256(checkpoint) or tested.get("dataset_manifest_sha256") != sha256(manifest):
        raise ValueError("TEST report does not match frozen thresholds/checkpoint/dataset")
    if not technical_smoke and tested.get("source") != "LOCAL_PHYSICAL": raise ValueError("Production TEST requires LOCAL_PHYSICAL")
    validate_manifest(manifest,strict=True)
    if output.exists(): raise ValueError("Refusing to overwrite a versioned model package")
    output.mkdir(parents=True)
    saved=torch.load(checkpoint,map_location="cpu",weights_only=False); network=model(None)
    network.load_state_dict(saved["state_dict"]); network.eval()
    torch.onnx.export(network,torch.zeros(1,3,224,224),str(output/"model.onnx"),input_names=["images"],
                      output_names=["logits"],opset_version=17,dynamo=False,external_data=False)
    onnx.checker.check_model(onnx.load(output/"model.onnx"))
    session=ort.InferenceSession(str(output/"model.onnx"),providers=["CPUExecutionProvider"])
    rows=[r for r in read_rows(manifest) if r["split"]=="validation" and not r.get("excluded_reason")]
    samples=Samples(rows,manifest); max_logit=0.0; max_probability=0.0; matches=True
    with torch.no_grad():
        for i in range(len(samples)):
            tensor,_=samples[i]; pytorch=network(tensor[None]).numpy()
            runtime=session.run(None,{"images":tensor[None].numpy()})[0]
            max_logit=max(max_logit,float(np.abs(pytorch-runtime).max()))
            max_probability=max(max_probability,float(np.abs(softmax(pytorch)-softmax(runtime)).max()))
            matches=matches and int(pytorch.argmax())==int(runtime.argmax())
    equivalence=dict(images=len(samples),logits_atol=logits_atol,probabilities_atol=probabilities_atol,
                     max_logit_abs_diff=max_logit,max_probability_abs_diff=max_probability,top1_equal=matches,
                     passed=len(samples)>=50 and max_logit<=logits_atol and max_probability<=probabilities_atol and matches)
    write_json(output/"labels.json",list(LABELS)); write_json(output/"preprocess.json",DEFAULT)
    copy_selected(thresholds,checkpoint,manifest,output,technical_smoke=technical_smoke)
    write_json(output/"training.json",saved["training"]); shutil.copyfile(manifest,output/"dataset_manifest.csv")
    shutil.copyfile(test_report,output/"test_metrics.json")
    files=["model.onnx","labels.json","preprocess.json","thresholds.json","training.json","dataset_manifest.csv","threshold_selection.json","test_metrics.json"]
    record=dict(version="0.2.0-mvp-rc1",architecture="mobilenet_v3_small",shape=[1,3,224,224],dtype="float32",
                sha256={name:sha256(output/name) for name in files},equivalence=equivalence,
                source=saved["training"]["source"],validation_domain=saved["training"]["validation_domain"],
                threshold_selection_status=selected["status"],physical_acceptance="PENDING_PHYSICAL_VALIDATION",status="NUMERICALLY_VERIFIED" if equivalence["passed"] else "DO_NOT_DEPLOY")
    write_json(output/"model_manifest.json",record)
    return record

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--checkpoint",type=Path,required=True); p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--thresholds",type=Path,required=True); p.add_argument("--test-report",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); result=export(a.checkpoint,a.manifest,a.output,thresholds=a.thresholds,test_report=a.test_report)
    print(result); raise SystemExit(0 if result["equivalence"]["passed"] else 2)
