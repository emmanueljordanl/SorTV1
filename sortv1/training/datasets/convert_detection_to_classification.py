"""COCO detection/segmentation crops; external originals never become independent test objects."""
import argparse
import hashlib
import math
import json
from pathlib import Path
import yaml
from PIL import Image
from app.contracts import LABELS
from app.utils import sha256
from training.datasets.validate import write_rows

def convert(annotation: Path, image_root: Path, output: Path, mapping: dict, version: str,
            *, margin: float = 0.08, min_pixels: int = 16) -> list[dict]:
    if not 0 <= margin <= 0.25: raise ValueError("Crop margin outside conservative range")
    data = json.loads(annotation.read_text()); images = {x["id"]: x for x in data["images"]}
    categories = {x["id"]: x["name"] for x in data["categories"]}; rows = []
    output.mkdir(parents=True, exist_ok=True)
    for box in data["annotations"]:
        source = images[box["image_id"]]; name = categories[box["category_id"]]
        rule = mapping.get("classes", {}).get(name, {})
        target = rule.get("target", mapping.get("default", "CHALLENGE_OOD"))
        if target not in {*LABELS, "CHALLENGE_OOD", "EXCLUDE"}: raise ValueError("Invalid class mapping")
        if target in LABELS and rule.get("reviewed") is not True: raise ValueError("Unreviewed material mapping")
        if target == "EXCLUDE": continue
        image_path = (image_root / source["file_name"]).resolve()
        if not image_path.is_relative_to(image_root.resolve()): raise ValueError("Image path outside export")
        with Image.open(image_path) as image:
            bounds = box.get("bbox")
            if bounds is None and isinstance(box.get("segmentation"), list):
                points = [p for polygon in box["segmentation"] for p in polygon]
                if not points: continue
                xs, ys = points[::2], points[1::2]; bounds = [min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)]
            if not bounds or len(bounds) != 4: continue
            x, y, width, height = map(float, bounds)
            if not all(math.isfinite(v) for v in (x, y, width, height)): continue
            if width < min_pixels or height < min_pixels or x < 0 or y < 0 or x+width > image.width+1 or y+height > image.height+1: continue
            left, top = max(0, int(x-width*margin)), max(0, int(y-height*margin))
            right, bottom = min(image.width, int(x+width*(1+margin)+0.999)), min(image.height, int(y+height*(1+margin)+0.999))
            digest = sha256(image_path)
            crop_path = output / f"{digest[:20]}-{box['id']}.png"
            image.convert("RGB").crop((left, top, right, bottom)).save(crop_path)
        rows.append(dict(object_id=f"trashia:{version}:{digest}:{box['id']}", session_id=f"trashia:{version}",
                         class_id=str(LABELS.index(target)) if target in LABELS else "", split="train_external" if target in LABELS else "challenge",
                         image_path=str(crop_path.resolve()), source="EXTERNAL", source_dataset="TrashIA", source_version=str(version),
                         source_image_id=digest, source_annotation_id=str(box["id"]), original_class=name,
                         lighting_setup="EXTERNAL_UNKNOWN", operator="converter", sha256=sha256(crop_path), excluded_reason=""))
    challenge_sources = {r["source_image_id"] for r in rows if r["split"] == "challenge"}
    for row in rows:
        if row["source_image_id"] in challenge_sources: row["split"] = "challenge"
    write_rows(output / "manifest.csv", rows)
    return rows

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--annotations", type=Path, required=True); p.add_argument("--images", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True); p.add_argument("--mapping", type=Path, default=Path("training/datasets/class_mapping.yaml"))
    p.add_argument("--version", required=True); p.add_argument("--margin", type=float, default=0.08)
    a = p.parse_args(); print(len(convert(a.annotations, a.images, a.output, yaml.safe_load(a.mapping.read_text()), a.version, margin=a.margin)))
