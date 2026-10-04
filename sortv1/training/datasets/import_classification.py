import argparse
from pathlib import Path
import yaml
from app.contracts import LABELS
from app.utils import sha256
from training.datasets.validate import write_rows

def import_folders(root: Path, mapping: dict, version: str, output: Path):
    from PIL import Image
    rows = []
    for image in sorted(root.rglob("*")):
        if image.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}: continue
        with Image.open(image) as decoded: decoded.verify()
        original = image.parent.name; rule = mapping.get("classes", {}).get(original, {})
        target = rule.get("target", "CHALLENGE_OOD")
        if target == "EXCLUDE": continue
        if target in LABELS and not rule.get("reviewed"): raise ValueError("Unreviewed class mapping")
        if target not in {*LABELS, "CHALLENGE_OOD"}: raise ValueError("Invalid class mapping")
        digest = sha256(image)
        rows.append(dict(object_id="external:"+digest, session_id="trashia:"+version,
                         class_id=str(LABELS.index(target)) if target in LABELS else "", split="train_external" if target in LABELS else "challenge",
                         image_path=str(image.resolve()), source="EXTERNAL", source_dataset="TrashIA", source_version=version,
                         source_image_id=digest, source_annotation_id="folder", original_class=original,
                         lighting_setup="EXTERNAL_UNKNOWN", operator="import", sha256=digest, excluded_reason=""))
    write_rows(output, rows); return len(rows)

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--root",type=Path,required=True); p.add_argument("--mapping",type=Path,required=True)
    p.add_argument("--version",required=True); p.add_argument("--output",type=Path,required=True)
    a=p.parse_args(); print(import_folders(a.root,yaml.safe_load(a.mapping.read_text()),a.version,a.output))
