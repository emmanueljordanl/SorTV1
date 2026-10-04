"""Measured CPU vs CPU laptop comparison on identical inputs; never attributed to Pi."""
import argparse
from pathlib import Path
import platform
from time import perf_counter_ns
import numpy as np
import torch
from PIL import Image
from training.train.train import model
from app.inference.onnx_runtime import OnnxInference
from app.inference.preprocessing import tensor_rgb
from app.utils import write_json,sha256

def run(checkpoint,package,image,*,warmup=100,iterations=1000,threads=4):
    torch.set_num_threads(threads);saved=torch.load(checkpoint,map_location='cpu',weights_only=False);network=model(None)
    network.load_state_dict(saved['state_dict']);network.eval();runtime=OnnxInference(package,threads=threads)
    with Image.open(image) as decoded:data=tensor_rgb(decoded.convert('RGB'),runtime.spec)
    tensor=torch.from_numpy(data);values={}
    with torch.no_grad():
        for name,function in [('PyTorch CPU',lambda:network(tensor)),('ONNX Runtime CPU',lambda:runtime.session.run(None,{runtime.input_name:data}))]:
            for _ in range(warmup):function()
            times=[]
            for _ in range(iterations):start=perf_counter_ns();function();times.append((perf_counter_ns()-start)/1e6)
            values[name]=dict(p50_ms=float(np.percentile(times,50)),p95_ms=float(np.percentile(times,95)),max_ms=max(times))
    return dict(source='MEASURED_HOST',target='LAPTOP',host=platform.node(),OS=platform.platform(),Python=platform.python_version(),
        model_source=runtime.manifest['source'],checkpoint_sha256=sha256(checkpoint),model_sha256=runtime.model_sha256,batch=1,threads=threads,
        warmup=warmup,iterations=iterations,torch=torch.__version__,backends=values,physical_acceptance='PENDING')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ['checkpoint','package','image']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('evidence/benchmarks/laptop.json'));p.add_argument('--iterations',type=int,default=1000)
    a=p.parse_args();result=run(a.checkpoint,a.package,a.image,iterations=a.iterations);write_json(a.output,result);print(result)
