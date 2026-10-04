import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import random
import subprocess
import uuid
import numpy as np
from PIL import Image, ImageEnhance
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
import yaml
from app.inference.preprocessing import DEFAULT, tensor_rgb
from app.utils import sha256, write_json
from training.datasets.validate import read_rows, validate_manifest
from training.evaluate.metrics import metrics

def model(weights: str | None = "IMAGENET1K_V1"):
    network = mobilenet_v3_small(weights=None if weights is None else MobileNet_V3_Small_Weights[weights])
    network.classifier[-1] = nn.Linear(network.classifier[-1].in_features, 4)
    return network

class Samples(Dataset):
    def __init__(self, rows: list[dict], manifest: Path, *, augmentation: dict | None = None):
        self.rows, self.manifest, self.augmentation = rows, manifest, augmentation
    def __len__(self): return len(self.rows)
    def __getitem__(self, index):
        row = self.rows[index]; path = Path(row["image_path"])
        if not path.is_absolute(): path = self.manifest.parent / path
        with Image.open(path) as decoded: image = decoded.convert("RGB")
        if self.augmentation:
            spec = self.augmentation
            image = image.rotate(random.uniform(-spec["rotation_degrees"], spec["rotation_degrees"]),
                                 resample=Image.Resampling.BILINEAR, expand=True, fillcolor=(128, 128, 128))
            fraction = spec["translation_fraction"]
            pad_x, pad_y = max(1, int(image.width * 0.15)), max(1, int(image.height * 0.15))
            canvas = Image.new("RGB", (image.width + 2*pad_x, image.height + 2*pad_y), (128,128,128))
            canvas.paste(image, (pad_x + int(random.uniform(-fraction, fraction)*image.width),
                                 pad_y + int(random.uniform(-fraction, fraction)*image.height)))
            image = ImageEnhance.Brightness(canvas).enhance(random.uniform(*spec["brightness"]))
            image = ImageEnhance.Contrast(image).enhance(random.uniform(*spec["contrast"]))
        return torch.from_numpy(tensor_rgb(image, DEFAULT)[0]), int(row["class_id"])

def train(config: dict, *, technical_smoke: bool = False) -> Path:
    manifest = Path(config["manifest"])
    validate_manifest(manifest, strict=True)
    rows = [r for r in read_rows(manifest) if not r.get("excluded_reason")]
    training = [r for r in rows if r["split"] in {"train", "train_external"}]
    validation = [r for r in rows if r["split"] == "validation"]
    if not training or not validation: raise ValueError("Training and validation samples required")
    if not technical_smoke and any(r["source"] != "LOCAL_PHYSICAL" for r in validation):
        raise ValueError("Selection validation requires LOCAL_PHYSICAL")
    if not technical_smoke and any(r["source"] == "SYNTHETIC_TEST" for r in rows):
        raise ValueError("Synthetic technical fixtures cannot enter production training")
    if any(not any(r["class_id"] == str(i) for r in group) for group in (training, validation) for i in range(4)):
        raise ValueError("All four classes need training and validation samples")
    seed = config["seed"]; random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(config.get("threads", 4))
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True; torch.backends.cudnn.benchmark = False
    device = config.get("device", "auto")
    if device == "auto": device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available(): raise ValueError("CUDA unavailable")
    network = model(None if technical_smoke else config["initial_weights"]).to(device)
    train_loader = DataLoader(Samples(training, manifest, augmentation=config["augmentation"]),
                              batch_size=config["batch_size"], shuffle=True, num_workers=config.get("workers", 0))
    val_loader = DataLoader(Samples(validation, manifest), batch_size=config["batch_size"], num_workers=0)
    output = Path(config["output"]) / (("smoke-" if technical_smoke else "train-") + uuid.uuid4().hex)
    output.mkdir(parents=True, exist_ok=False)
    try: commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except subprocess.CalledProcessError: commit = "UNVERSIONED"
    record = dict(experiment_id=output.name, git_commit=commit, dataset_manifest_sha256=sha256(manifest),
                  roboflow_version=sorted({r.get("source_version", "") for r in rows if r["source"] == "EXTERNAL"}),
                  config=config, seed=seed, architecture="mobilenet_v3_small", initial_weights=None if technical_smoke else config["initial_weights"],
                  batch_size=config["batch_size"], timestamp=datetime.now(timezone.utc).isoformat(), torch_version=torch.__version__,
                  cuda_version=torch.version.cuda, GPU=torch.cuda.get_device_name(0) if device=="cuda" else None, host=platform.node(),
                  source="SYNTHETIC_TEST" if technical_smoke else "TRAINING", device=device, preprocess=DEFAULT,
                  validation_domain="SYNTHETIC_TEST" if technical_smoke else "LOCAL_PHYSICAL", history=[])
    record.update(learning_rates={"head": config["head_learning_rate"], "finetune": config["finetune_learning_rate"]},
                  epochs={"head": config["head_epochs"], "finetune": config["finetune_epochs"]}, augmentation=config["augmentation"])
    best = -1.0; bad_epochs = 0; epoch_number = 0
    for phase, epochs, lr in [("head", config["head_epochs"], config["head_learning_rate"]),
                               ("finetune", config["finetune_epochs"], config["finetune_learning_rate"])]:
        for p in network.parameters(): p.requires_grad = False
        for p in network.classifier.parameters(): p.requires_grad = True
        if phase == "finetune":
            for block in list(network.features.children())[-config.get("finetune_last_blocks",3):]:
                for p in block.parameters(): p.requires_grad = True
        bad_epochs = 0
        optimizer = torch.optim.AdamW([p for p in network.parameters() if p.requires_grad], lr=lr)
        for _ in range(epochs):
            epoch_number += 1; network.train()
            network.features.eval()  # Freeze BatchNorm state on frozen blocks.
            if phase == "finetune":
                for block in list(network.features.children())[-config.get("finetune_last_blocks",3):]: block.train()
            losses = []
            for batch, target in train_loader:
                optimizer.zero_grad(set_to_none=True); logits=network(batch.to(device)); loss=nn.functional.cross_entropy(logits,target.to(device))
                loss.backward(); optimizer.step(); losses.append(float(loss.detach().cpu()))
            truth, predicted = [], []; network.eval()
            with torch.no_grad():
                for batch, target in val_loader:
                    predicted.extend(network(batch.to(device)).argmax(1).cpu().tolist()); truth.extend(target.tolist())
            score = metrics(truth, predicted)["macro_f1"]
            record["history"].append(dict(epoch=epoch_number, phase=phase, learning_rate=lr, loss=float(np.mean(losses)), validation_macro_f1=score))
            if score > best:
                best = score; bad_epochs = 0; record.update(best_epoch=epoch_number, validation_macro_f1=score)
                torch.save({"state_dict":network.state_dict(),"training":record},output/"best.pt")
            else: bad_epochs += 1
            write_json(output/"training.json",record)
            print(f"{record['source']} epoch={epoch_number} phase={phase} validation_macro_f1={score:.4f}")
            if phase=="finetune" and bad_epochs>=config["early_stopping_patience"]: break
    return output / "best.pt"

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,default=Path("training/configs/baseline.yaml"))
    a=p.parse_args(); print(train(yaml.safe_load(a.config.read_text())))
