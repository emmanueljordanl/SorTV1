import argparse
from pathlib import Path
import platform
from time import perf_counter_ns
import numpy as np
import onnxruntime as ort
import psutil
from PIL import Image
from app.inference.onnx_runtime import OnnxInference
from app.inference.preprocessing import tensor_rgb
from app.utils import write_json

def benchmark(package: Path,image: Path,*,warmup=100,iterations=1000,threads=2,target="host"):
    identity=Path("/proc/device-tree/model")
    if target=="pi" and (not identity.exists() or "Raspberry Pi 5" not in identity.read_text(errors="replace")):
        raise ValueError("Pi benchmark requires actual Raspberry Pi 5")
    if warmup<0 or iterations<1: raise ValueError("Invalid sample counts")
    inference=OnnxInference(package,threads=threads)
    with Image.open(image) as rgb: tensor=tensor_rgb(rgb.convert("RGB"),inference.spec)
    for _ in range(warmup): inference.session.run(None,{inference.input_name:tensor})
    values=[]
    for _ in range(iterations):
        start=perf_counter_ns(); inference.session.run(None,{inference.input_name:tensor}); values.append((perf_counter_ns()-start)/1e6)
    temperature=None; thermal=Path("/sys/class/thermal/thermal_zone0/temp")
    if thermal.exists(): temperature=float(thermal.read_text())/1000
    return dict(source="MEASURED_HOST",model_source=inference.manifest["source"],target=target,warmup=warmup,samples=iterations,
                p50_ms=float(np.percentile(values,50)),p95_ms=float(np.percentile(values,95)),max_ms=max(values),
                ram_rss_bytes=psutil.Process().memory_info().rss,temperature_c=temperature,threads=threads,
                model_sha256=inference.model_sha256,backend="ONNX Runtime CPU",onnxruntime=ort.__version__,
                OS=platform.platform(),Python=platform.python_version(),host=platform.node(),batch=1)

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--package",type=Path,required=True); p.add_argument("--image",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("evidence/benchmarks/onnx.json")); p.add_argument("--target",choices=["host","pi"],default="host")
    p.add_argument("--target-pi",dest="target",action="store_const",const="pi")
    p.add_argument("--warmup",type=int,default=100); p.add_argument("--iterations",type=int,default=1000); p.add_argument("--threads",type=int,default=2)
    a=p.parse_args(); result=benchmark(a.package,a.image,warmup=a.warmup,iterations=a.iterations,threads=a.threads,target=a.target)
    write_json(a.output,result); print(result)
