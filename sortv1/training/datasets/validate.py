import argparse
import csv
from collections import Counter
from pathlib import Path
from app.utils import sha256

FIELDS = ["object_id", "session_id", "class_id", "split", "image_path", "source", "source_dataset",
          "source_version", "source_image_id", "source_annotation_id", "original_class",
          "lighting_setup", "operator", "sha256", "excluded_reason"]
LEGACY = {"object_id", "session_id", "class_id", "split", "image_path", "source", "lighting_setup", "operator", "excluded_reason"}
SPLITS = {"train", "train_external", "validation", "test", "challenge"}

def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not LEGACY.issubset(reader.fieldnames or []): raise ValueError("Faltan columnas obligatorias del manifest")
        return list(reader)

def write_rows(path: Path, rows: list[dict]) -> None:
    import os
    path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader()
        writer.writerows({k: row.get(k, "") for k in FIELDS} for row in rows)
        handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, path)

def validate_manifest(path: Path, *, strict: bool = False, allow_empty: bool = False, require_local_eval: bool = False) -> int:
    rows = read_rows(path)
    if not rows and not allow_empty: raise ValueError("Manifest vacío: aún no existen datos reales")
    identities = {}; images = set(); hashes = set(); counts = Counter()
    for row in rows:
        split = row["split"]
        if not row["object_id"] or split not in SPLITS: raise ValueError("Objeto o partición inválidos")
        if row["class_id"] not in {"0", "1", "2", "3"} and split != "challenge": raise ValueError("Clase fuera de catálogo")
        domain = "train" if split == "train_external" else split
        for field in ("object_id", "source_image_id", "sha256"):
            value = row.get(field, "")
            if not value:
                if strict and field in {"sha256", "source_image_id"}: raise ValueError(f"Missing {field}")
                continue
            key = field, value
            if key in identities and identities[key] != domain: raise ValueError(f"Fuga de partición por {field}: {value}")
            identities[key] = domain
        label_key = "label", row["object_id"]
        if label_key in identities and identities[label_key] != row["class_id"]: raise ValueError("Fuga de etiqueta por objeto")
        identities[label_key] = row["class_id"]
        if not row["image_path"] or row["image_path"] in images: raise ValueError("Imagen vacía o duplicada")
        images.add(row["image_path"])
        if row.get("sha256"):
            if row["sha256"] in hashes: raise ValueError("Duplicate image hash")
            hashes.add(row["sha256"])
        if strict:
            from PIL import Image
            image = Path(row["image_path"]); image = image if image.is_absolute() else path.parent / image
            if not image.is_file() or sha256(image) != row["sha256"]: raise ValueError(f"Missing file or hash mismatch: {row['image_path']}")
            with Image.open(image) as decoded: decoded.verify()
            if row["source"] not in {"EXTERNAL", "LOCAL_PHYSICAL", "SYNTHETIC_TEST"}: raise ValueError("Invalid source domain")
            if split in {"validation", "test"} and require_local_eval and row["source"] != "LOCAL_PHYSICAL":
                raise ValueError("Final evaluation requires LOCAL_PHYSICAL")
        if not row.get("excluded_reason") and split != "challenge": counts[split, row["class_id"]] += 1
    if require_local_eval:
        for split in ("train", "validation", "test"):
            for label in map(str, range(4)):
                if not counts[split, label]: raise ValueError(f"Class without samples: {split}/{label}")
    return len(rows)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate provenance, leakage, files and hashes")
    parser.add_argument("manifest", type=Path); parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-empty", action="store_true"); parser.add_argument("--require-local-eval", action="store_true")
    args = parser.parse_args()
    try: print(f"Manifest válido: {validate_manifest(args.manifest, strict=args.strict, allow_empty=args.allow_empty, require_local_eval=args.require_local_eval)} imágenes")
    except (ValueError, OSError) as exc: parser.exit(1, f"ERROR: {exc}\n")
