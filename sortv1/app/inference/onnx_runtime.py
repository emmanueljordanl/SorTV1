from pathlib import Path
from time import perf_counter_ns
from app.contracts import LABELS, Frame, Prediction
from .preprocessing import load_json, sha256, softmax, tensor_rgb

class OnnxInference:
    def __init__(self, package: Path, threads: int = 2, *, require_equivalence: bool = True, session_factory=None):
        self.package = Path(package)
        self.manifest = load_json(self.package / "model_manifest.json")
        hashes = self.manifest.get("sha256", {})
        required = {"model.onnx", "labels.json", "preprocess.json", "thresholds.json", "training.json", "dataset_manifest.csv"}
        if not required.issubset(hashes): raise ValueError("Incomplete model package hashes")
        for name, expected in hashes.items():
            path = self.package / name
            if Path(name).name != name or not path.is_file() or sha256(path) != expected:
                raise ValueError(f"Model package hash mismatch: {name}")
        if load_json(self.package / "labels.json") != list(LABELS): raise ValueError("Labels order mismatch")
        gate = self.manifest.get("equivalence", {})
        if require_equivalence and (gate.get("passed") is not True or gate.get("images", 0) < 50):
            raise ValueError("Model not cleared for deployment: equivalence gate")
        self.spec = load_json(self.package / "preprocess.json")
        self.thresholds = load_json(self.package / "thresholds.json")
        if session_factory is None:
            import onnxruntime as ort
            options = ort.SessionOptions(); options.intra_op_num_threads = threads
            self.session = ort.InferenceSession(str(self.package / "model.onnx"), options, providers=["CPUExecutionProvider"])
        else: self.session = session_factory(str(self.package / "model.onnx"))
        inputs, outputs = self.session.get_inputs(), self.session.get_outputs()
        if len(inputs) != 1 or inputs[0].shape != [1, 3, 224, 224] or inputs[0].type != "tensor(float)":
            raise ValueError("ONNX input contract mismatch")
        if len(outputs) != 1 or outputs[0].shape != [1, 4] or outputs[0].type != "tensor(float)":
            raise ValueError("ONNX output contract mismatch")
        self.input_name, self.model_sha256 = inputs[0].name, hashes["model.onnx"]

    def predict(self, frame: Frame) -> Prediction:
        tensor = tensor_rgb(frame.rgb, self.spec); start = perf_counter_ns()
        output = self.session.run(None, {self.input_name: tensor})[0]
        duration = (perf_counter_ns() - start) / 1_000_000
        values = softmax(output)
        return Prediction(frame.frame_id, tuple(float(p) for p in values), self.model_sha256, duration)
