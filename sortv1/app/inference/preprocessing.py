"""Única transformación compartida entre entrenamiento y runtime."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

DEFAULT = dict(version=1, color="RGB", shape=[1, 3, 224, 224], dtype="float32",
               scale=255.0, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225],
               resize_policy="letterbox", fill=[128, 128, 128], roi_stage="capture")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def tensor_rgb(rgb, spec: dict) -> np.ndarray:
    if (spec.get("color") != "RGB" or spec.get("shape") != [1, 3, 224, 224]
            or spec.get("dtype") != "float32" or spec.get("resize_policy") != "letterbox"):
        raise ValueError("Unsupported preprocessing contract")
    image = rgb if isinstance(rgb, Image.Image) else Image.fromarray(np.asarray(rgb, dtype=np.uint8), "RGB")
    image = image.convert("RGB")
    if min(image.size) <= 0: raise ValueError("Empty image")
    scale = min(224 / image.width, 224 / image.height)
    size = max(1, round(image.width * scale)), max(1, round(image.height * scale))
    resized = image.resize(size, Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (224, 224), tuple(spec.get("fill", [128, 128, 128])))
    canvas.paste(resized, ((224 - size[0]) // 2, (224 - size[1]) // 2))
    array = np.asarray(canvas, dtype=np.float32) / np.float32(spec["scale"])
    mean, std = np.asarray(spec["mean"], dtype=np.float32), np.asarray(spec["std"], dtype=np.float32)
    if mean.shape != (3,) or std.shape != (3,) or not np.isfinite(mean).all() or not (std > 0).all():
        raise ValueError("Invalid normalization")
    return np.ascontiguousarray(((array - mean) / std).transpose(2, 0, 1)[None], dtype=np.float32)

def softmax(logits) -> np.ndarray:
    values = np.asarray(logits, dtype=np.float64)
    if values.shape != (1, 4) or not np.isfinite(values).all(): raise ValueError("Invalid logits")
    values = np.exp(values - values.max(axis=1, keepdims=True)); values /= values.sum(axis=1, keepdims=True)
    if not np.isfinite(values).all() or abs(float(values.sum()) - 1) > 1e-6: raise ValueError("Invalid probabilities")
    return values[0]
